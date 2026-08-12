#!/usr/bin/env python3
"""Browser GUI for flow cytometry histograms with interactive gating.

Runs a small local web server and opens the interface in your browser.
Only needs the packages the plotting itself needs (numpy, matplotlib,
seaborn, scipy, readfcs) - no GUI toolkit, so it behaves the same on
macOS, Windows and Linux.

Run:   python3 flower.py
Stop:  Ctrl+C in the terminal
"""

import base64
import io
import json
import threading
import webbrowser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import matplotlib.pyplot as plt
import numpy as np

import flow_core as fc
from gui_page import PAGE_HTML

_RENDER_LOCK = threading.Lock()

PALETTE = ["#4C72B0", "#55A868", "#C44E52", "#8172B2", "#CCB974",
           "#64B5CD", "#DA8BC3", "#8C8C8C"]

STATE = {
    "samples": [],   # {path, label, color, active, df}
    "scatter_gates": {},   # {sample_index: gate_dict}  – gating scatter (FSC/SSC)
    "hist_gates": {},      # {sample_index: gate_dict}  – histogram interval
    "analysis_gates": {},  # {sample_index: gate_dict}  – analysis scatter
}


# ------------------------------------------------------------------ state --
def add_sample(path, label=None, color=None):
    path = Path(path).expanduser()
    df = fc.read_fcs(path)
    STATE["samples"].append({
        "path": str(path),
        "label": label or path.stem,
        "color": color or PALETTE[len(STATE["samples"]) % len(PALETTE)],
        "active": True,
        "df": df,
    })


def autoload_defaults():
    for path in sorted(fc.DATA_DIR.glob("*.fcs")):
        try:
            add_sample(path)
        except Exception as exc:  # noqa: BLE001
            print(f"Could not load {path.name}: {exc}")


def channels():
    return STATE["samples"][0]["df"].columns.tolist() if STATE["samples"] else []


def scatter_gate_for(index):
    return STATE["scatter_gates"].get(str(index))


def hist_gate_for(index):
    return STATE["hist_gates"].get(str(index))


def analysis_gate_for(index):
    return STATE["analysis_gates"].get(str(index))


_ALL_GATE_DICTS = ("scatter_gates", "hist_gates", "analysis_gates")


def series_for(s):
    out = []
    for i, sample in enumerate(STATE["samples"]):
        if not sample.get("active", True):
            continue
        values = fc.channel_values(sample["df"], s,
                                    scatter_gate_for(i), hist_gate_for(i),
                                    analysis_gate_for(i))
        out.append({"label": sample["label"], "color": sample["color"], "values": values,
                    "hist_gate": hist_gate_for(i)})
    return out


def gate_stats(s):
    stats = []
    for i, sample in enumerate(STATE["samples"]):
        sg = scatter_gate_for(i)
        hg = hist_gate_for(i)
        ag = analysis_gate_for(i)
        total = len(sample["df"])
        scatter_kept = len(fc.apply_gate(sample["df"], sg)) if sg else total
        plotted = int(fc.channel_values(sample["df"], s, sg, hg, ag).size)
        stats.append({
            "label": sample["label"], "total": total,
            "scatter_kept": scatter_kept,
            "scatter_percent": round(100 * scatter_kept / total, 1) if total else 0,
            "plotted": plotted,
            "has_scatter_gate": sg is not None,
            "has_hist_gate": hg is not None,
            "has_analysis_gate": ag is not None,
            "active": sample.get("active", True),
        })
    return stats


# --------------------------------------------------------------- rendering --
def _png(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=fig.dpi)
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def render_scatter(index, s):
    with _RENDER_LOCK:
        sample = STATE["samples"][index]
        df = sample["df"]
        x_ch, y_ch = s["scatter_x"], s["scatter_y"]

        fc.apply_style(s)
        preview_dpi = 120
        width = int(s["fig_w"] * preview_dpi)
        height = int(s["fig_h"] * preview_dpi)
        bbox = [0.15, 0.14, 0.80, 0.80]
        fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
        ax = fig.add_axes(bbox)

        # Determine limits
        pooled_x = df[x_ch].to_numpy(float)
        pooled_y = df[y_ch].to_numpy(float)
        if s.get("scatter_xlim_auto"):
            xlim = fc._percentile_limits(pooled_x)
        else:
            xlim = (s["scatter_xlim_lo"], s["scatter_xlim_hi"])
        if s.get("scatter_ylim_auto"):
            ylim = fc._percentile_limits(pooled_y)
        else:
            ylim = (s["scatter_ylim_lo"], s["scatter_ylim_hi"])

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

        g = scatter_gate_for(index)
        fc.draw_scatter(ax, df, sample["color"], g, s)

        meta = {"width": width, "height": height, "bbox": bbox,
                "xlim": list(xlim), "ylim": list(ylim),
                "scale": s.get("scatter_scale", "log")}
        return _png(fig), meta


def render_analysis_scatter(index, s):
    with _RENDER_LOCK:
        sample = STATE["samples"][index]
        sg = scatter_gate_for(index)
        df = fc.apply_gate(sample["df"], sg) if sg else sample["df"]
        x_ch, y_ch = s["analysis_x"], s["analysis_y"]

        fc.apply_style(s)
        preview_dpi = 120
        width = int(s["fig_w"] * preview_dpi)
        height = int(s["fig_h"] * preview_dpi)
        bbox = [0.15, 0.14, 0.80, 0.80]
        fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
        ax = fig.add_axes(bbox)

        pooled_x = df[x_ch].to_numpy(float)
        pooled_y = df[y_ch].to_numpy(float)
        if s.get("analysis_xlim_auto"):
            xlim = fc._percentile_limits(pooled_x)
        else:
            xlim = (s["analysis_xlim_lo"], s["analysis_xlim_hi"])
        if s.get("analysis_ylim_auto"):
            ylim = fc._percentile_limits(pooled_y)
        else:
            ylim = (s["analysis_ylim_lo"], s["analysis_ylim_hi"])

        ax.set_xlim(*xlim)
        ax.set_ylim(*ylim)

        g = analysis_gate_for(index)
        fc.draw_scatter(ax, df, sample["color"], g, s,
                        x_ch=x_ch, y_ch=y_ch,
                        scale_key="analysis_scale",
                        xlim_auto_key="analysis_xlim_auto",
                        xlim_lo_key="analysis_xlim_lo",
                        xlim_hi_key="analysis_xlim_hi",
                        ylim_auto_key="analysis_ylim_auto",
                        ylim_lo_key="analysis_ylim_lo",
                        ylim_hi_key="analysis_ylim_hi",
                        xlabel_key="analysis_xlabel",
                        ylabel_key="analysis_ylabel")

        meta = {"width": width, "height": height, "bbox": bbox,
                "xlim": list(xlim), "ylim": list(ylim),
                "scale": s.get("analysis_scale", "log")}
        return _png(fig), meta


def render_histogram(s):
    with _RENDER_LOCK:
        fc.apply_style(s)
        preview_dpi = 120
        width = int(s["fig_w"] * preview_dpi)
        height = int(s["fig_h"] * preview_dpi)
        fig = plt.figure(figsize=(width / 100, height / 100), dpi=100)
        ax = fig.add_axes([0.15, 0.14, 0.80, 0.80])
        fc.draw_histogram(ax, series_for(s), s)
        meta = {"width": width, "height": height}
        return _png(fig), meta


# ------------------------------------------------------------------ server --
class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def _send(self, payload, ctype="application/json", code=200):
        body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        self._send(PAGE_HTML.encode(), "text/html; charset=utf-8")

    def do_POST(self):
        try:
            req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            self._send(self.route(self.path, req))
        except Exception as exc:  # noqa: BLE001 - surface errors in the UI
            self._send({"error": f"{type(exc).__name__}: {exc}"})

    # ------------------------------------------------------------ routing --
    def route(self, path, req):
        if path == "/api/init":
            groups = [{"name": name,
                       "fields": [{"key": f[0], "label": f[1], "type": f[2], "help": f[3],
                                   "options": f[4] if len(f) > 4 else None} for f in fields]}
                      for name, fields in fc.SCHEMA]
            return {"schema": groups, "defaults": fc.DEFAULTS, "samples": self.sample_list(),
                    "channels": channels(),
                    "scatter_gates": STATE["scatter_gates"],
                    "hist_gates": STATE["hist_gates"],
                    "analysis_gates": STATE["analysis_gates"],
                    "data_dir": str(fc.DATA_DIR)}

        if path == "/api/browse":
            folder = Path(req.get("dir") or fc.DATA_DIR).expanduser()
            if not folder.is_dir():
                raise NotADirectoryError(f"{folder} is not a folder")
            folders = sorted([p.name for p in folder.iterdir() if p.is_dir() and not p.name.startswith(".")])
            files = sorted([p.name for p in folder.glob("*.fcs")])
            loaded = {sm["path"] for sm in STATE["samples"]}
            return {"dir": str(folder), "parent": str(folder.parent),
                    "folders": folders,
                    "files": [{"name": n, "loaded": str(folder / n) in loaded} for n in files]}

        if path == "/api/samples/add":
            for item in req["paths"]:
                add_sample(item)
            return {"samples": self.sample_list(), "channels": channels()}

        if path == "/api/samples/upload":
            target = fc.DATA_DIR / "uploads"
            target.mkdir(exist_ok=True)
            for item in req["files"]:
                dest = target / item["name"]
                dest.write_bytes(base64.b64decode(item["data"]))
                add_sample(dest)
            return {"samples": self.sample_list(), "channels": channels()}

        if path == "/api/samples/remove":
            idx = req["index"]
            STATE["samples"].pop(idx)
            # Reindex gates after removal
            for gate_dict in _ALL_GATE_DICTS:
                old = dict(STATE[gate_dict])
                STATE[gate_dict] = {}
                for k, v in old.items():
                    ki = int(k)
                    if ki < idx:
                        STATE[gate_dict][str(ki)] = v
                    elif ki > idx:
                        STATE[gate_dict][str(ki - 1)] = v
            return {"samples": self.sample_list(), "channels": channels(),
                    "scatter_gates": STATE["scatter_gates"],
                    "hist_gates": STATE["hist_gates"],
                    "analysis_gates": STATE["analysis_gates"]}

        if path == "/api/samples/update":
            sample = STATE["samples"][req["index"]]
            sample["label"] = req.get("label", sample["label"])
            sample["color"] = req.get("color", sample["color"])
            if "active" in req:
                sample["active"] = bool(req["active"])
            return {"samples": self.sample_list()}

        if path == "/api/samples/move":
            samples = STATE["samples"]
            i, j = req["index"], req["index"] + req["delta"]
            if 0 <= j < len(samples):
                samples[i], samples[j] = samples[j], samples[i]
                for gate_dict in _ALL_GATE_DICTS:
                    gi, gj = STATE[gate_dict].get(str(i)), STATE[gate_dict].get(str(j))
                    if gi: STATE[gate_dict][str(j)] = gi
                    else: STATE[gate_dict].pop(str(j), None)
                    if gj: STATE[gate_dict][str(i)] = gj
                    else: STATE[gate_dict].pop(str(i), None)
            return {"samples": self.sample_list(),
                    "scatter_gates": STATE["scatter_gates"],
                    "hist_gates": STATE["hist_gates"],
                    "analysis_gates": STATE["analysis_gates"]}

        if path == "/api/gate/set":
            gate_type = req.get("gate_type", "scatter")
            gate_dict = {"scatter": "scatter_gates",
                         "histogram": "hist_gates",
                         "analysis": "analysis_gates"}.get(gate_type, "scatter_gates")
            if gate_type == "analysis":
                for i in range(len(STATE["samples"])):
                    STATE[gate_dict][str(i)] = req["gate"]
            else:
                STATE[gate_dict][str(req["index"])] = req["gate"]
            return {"scatter_gates": STATE["scatter_gates"],
                    "hist_gates": STATE["hist_gates"],
                    "analysis_gates": STATE["analysis_gates"]}

        if path == "/api/gate/clear":
            gate_type = req.get("gate_type", "scatter")
            gate_dict = {"scatter": "scatter_gates",
                         "histogram": "hist_gates",
                         "analysis": "analysis_gates"}.get(gate_type, "scatter_gates")
            if gate_type == "analysis":
                STATE[gate_dict].clear()
            else:
                STATE[gate_dict].pop(str(req.get("index", -1)), None)
            return {"scatter_gates": STATE["scatter_gates"],
                    "hist_gates": STATE["hist_gates"],
                    "analysis_gates": STATE["analysis_gates"]}

        if path == "/api/scatter":
            s = fc.merge_settings(req.get("settings"))
            img, meta = render_scatter(req["index"], s)
            return {"img": img, "meta": meta, "stats": gate_stats(s)}

        if path == "/api/analysis_scatter":
            s = fc.merge_settings(req.get("settings"))
            img, meta = render_analysis_scatter(req["index"], s)
            return {"img": img, "meta": meta, "stats": gate_stats(s)}

        if path == "/api/histogram":
            s = fc.merge_settings(req.get("settings"))
            img, meta = render_histogram(s)
            return {"img": img, "meta": meta, "stats": gate_stats(s)}

        if path == "/api/save":
            s = fc.merge_settings(req.get("settings"))
            idx = req.get("scatter_index", 0)
            with _RENDER_LOCK:
                pdf, png = fc.save_figure(series_for(s), s)
                active_sample = STATE["samples"][idx]
                spdf, spng = fc.save_scatter_figure(
                    active_sample, scatter_gate_for(idx), s)
                apdf, apng = fc.save_analysis_scatter_figure(
                    active_sample, analysis_gate_for(idx), s,
                    scatter_gate=scatter_gate_for(idx))
                samples_info = [
                    {"label": sm["label"], "color": sm["color"], "df": sm["df"],
                     "scatter_gate": scatter_gate_for(i),
                     "hist_gate": hist_gate_for(i),
                     "analysis_gate": analysis_gate_for(i)}
                    for i, sm in enumerate(STATE["samples"])
                    if sm.get("active", True)
                ]
                xlsx = fc.save_statistics(samples_info, s)
            result = {"pdf": str(pdf), "png": str(png),
                      "scatter_pdf": str(spdf), "scatter_png": str(spng),
                      "analysis_pdf": str(apdf), "analysis_png": str(apng),
                      "scatter_gates": STATE["scatter_gates"],
                      "hist_gates": STATE["hist_gates"],
                      "analysis_gates": STATE["analysis_gates"],
                      "snippet": self.snippet(s)}
            if xlsx:
                result["xlsx"] = str(xlsx)
            return result

        raise ValueError(f"unknown route {path}")

    def sample_list(self):
        return [{"label": sm["label"], "color": sm["color"], "path": sm["path"],
                 "n": len(sm["df"]), "active": sm.get("active", True)}
                for sm in STATE["samples"]]

    def snippet(self, s):
        """Python snippet reproducing the current GUI state in the CLI script."""
        samples = ",\n".join(
            f'    ("{sm["label"]}", Path(r"{sm["path"]}"), "{sm["color"]}")'
            for sm in STATE["samples"])
        changed = {k: v for k, v in s.items() if fc.DEFAULTS.get(k) != v}
        settings = ",\n".join(f"    {k!r}: {v!r}" for k, v in sorted(changed.items()))

        def _gates_str(gate_dict_name):
            lines = []
            for i, sm in enumerate(STATE["samples"]):
                g = STATE[gate_dict_name].get(str(i))
                if g:
                    lines.append(f'    {i}: {json.dumps(g)},  # {sm["label"]}')
            return "{" + "\n".join(lines) + "\n}" if lines else "{}"

        return (f"SAMPLES = [\n{samples}\n]\n\n"
                f"SCATTER_GATES = {_gates_str('scatter_gates')}\n\n"
                f"HIST_GATES = {_gates_str('hist_gates')}\n\n"
                f"ANALYSIS_GATES = {_gates_str('analysis_gates')}\n\n"
                f"SETTINGS = merge_settings({{\n{settings}\n}})")


def main():
    autoload_defaults()
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    port = server.server_address[1]
    url = f"http://127.0.0.1:{port}"
    print(f"Flower ready at {url}")
    print(f"Loaded {len(STATE['samples'])} file(s) from {fc.DATA_DIR}")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.5, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
