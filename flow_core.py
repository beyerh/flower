#!/usr/bin/env python3
"""Core plotting engine for flow cytometry histograms.

Holds the settings schema, the FCS loader with polygon gating, and the
publication-quality renderer. Both the command line script
(`plot_ecd_histogram.py`) and the GUI (`flower.py`) build on this module,
so figures look identical no matter how they were produced.
"""

import re
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import readfcs
import seaborn as sns
from matplotlib.path import Path as MplPath
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, LogLocator, NullFormatter
from scipy.ndimage import gaussian_filter1d

if getattr(sys, "frozen", False):
    # Running as a PyInstaller bundle — bundled FCS files are extracted
    # to sys._MEIPASS; results go to a writable folder in the user's home.
    BUNDLED_DIR = Path(sys._MEIPASS)
    DATA_DIR = Path.home()
    RESULTS_DIR = Path.home() / "Flower_results"
else:
    BUNDLED_DIR = Path(__file__).parent
    DATA_DIR = BUNDLED_DIR
    RESULTS_DIR = DATA_DIR / "results"

_Y_AXIS_MODES = {
    "density": "Density",
    "counts": "Events",
    "percent_of_max": "% of max",
}
Y_AXIS_MODES = _Y_AXIS_MODES  # kept for external access

_LEGEND_LOCS = [
    "best", "upper left", "upper right", "lower left", "lower right",
    "center left", "center right", "upper center", "lower center",
]
LEGEND_LOCS = _LEGEND_LOCS


def _log_tick_label(x, pos):
    """Mathtext log tick labels: 10^{-1}, 10^{0}, 10^{1}, …"""
    if x <= 0:
        return ""
    exp = np.log10(x)
    if exp == int(exp):
        return r"$10^{%d}$" % int(exp)
    return ""

# --------------------------------------------------------------------------
# Settings schema: drives both the defaults below and the GUI form.
# Each field: key, label, type, help, and optional options/step/group.
# --------------------------------------------------------------------------
SCHEMA = [
    ("Histogram", [
        ("channel", "Channel", "channel",
         "Fluorescence parameter shown on the x axis (area channels '-A' are standard)."),
        ("x_scale", "X axis scale", "choice",
         "Logarithmic decades (standard for fluorescence) or linear.",
         ["log", "linear"]),
        ("min_value", "Minimum value", "float",
         "Events at or below this value are discarded. A log axis cannot display zero or "
         "negative values, which flow cytometers do produce for dim events."),
        ("y_axis", "Y axis mode", "choice",
         "density = area under each curve is 1 (compares shapes, independent of event count). "
         "counts = raw events per bin. percent of max = each curve scaled to its own peak.",
         list(Y_AXIS_MODES)),
        ("n_bins", "Number of bins", "int",
         "Bins are spaced evenly on the log axis. More bins resolve finer structure but add noise."),
        ("smooth_sigma", "Smoothing", "float",
         "Width of the Gaussian smoothing kernel in bins. 0 disables smoothing. "
         "Smoothing spreads events over neighbouring bins, so sharp peaks get lower "
         "while the total event count is preserved; use '% of max' for a fixed peak height. "
         "Too much smoothing hides real shoulders."),
        ("xlim_lo", "X min", "float", "Left end of the x axis (a power of ten looks tidiest)."),
        ("xlim_hi", "X max", "float", "Right end of the x axis."),
        ("ylim_auto", "Auto Y range", "bool",
         "Scale the y axis to the data and leave room for the legend."),
        ("y_headroom", "Y headroom", "float",
         "With auto range: multiplier applied to the tallest peak, e.g. 1.45 leaves 45% free space."),
        ("ylim_lo", "Y min", "float", "Only used when auto Y range is off."),
        ("ylim_hi", "Y max", "float", "Only used when auto Y range is off."),
        ("xlabel", "X label", "text", "Leave empty to derive it from the selected channel."),
        ("ylabel", "Y label", "text", "Leave empty to derive it from the y axis mode."),
        ("title", "Title", "text", "Optional plot title; usually omitted in composite figures."),
        ("line_width", "Curve line width", "float", "Thickness of the histogram outlines."),
        ("fill_alpha", "Fill opacity", "float",
         "Transparency of the area under each curve. 0 draws outlines only."),
    ]),
    ("Gating scatter", [
        ("scatter_x", "X channel", "channel",
         "Parameter on the gating scatter x axis (typically FSC-A)."),
        ("scatter_y", "Y channel", "channel",
         "Parameter on the gating scatter y axis (typically SSC-A)."),
        ("scatter_scale", "Axis scale", "choice",
         "Logarithmic or linear axes for the gating scatter.",
         ["log", "linear"]),
        ("scatter_xlim_auto", "Auto X range", "bool",
         "Use percentile-based limits that ignore extreme outliers."),
        ("scatter_xlim_lo", "X min", "float", "Left end of the scatter x axis (used when auto is off)."),
        ("scatter_xlim_hi", "X max", "float", "Right end of the scatter x axis."),
        ("scatter_ylim_auto", "Auto Y range", "bool",
         "Use percentile-based limits that ignore extreme outliers."),
        ("scatter_ylim_lo", "Y min", "float", "Bottom end of the scatter y axis (used when auto is off)."),
        ("scatter_ylim_hi", "Y max", "float", "Top end of the scatter y axis."),
        ("scatter_xlabel", "X label", "text", "Leave empty to derive from the x channel."),
        ("scatter_ylabel", "Y label", "text", "Leave empty to derive from the y channel."),
        ("scatter_point_size", "Point size", "float", "Size of scatter dots in points (shared by both scatters)."),
        ("scatter_point_alpha", "Point opacity", "float", "Transparency of scatter dots 0-1 (shared by both scatters)."),
    ]),
    ("Singlets scatter", [
        ("singlets_x", "X channel", "channel",
         "Parameter on the singlets scatter x axis (typically FSC-A)."),
        ("singlets_y", "Y channel", "channel",
         "Parameter on the singlets scatter y axis (typically FSC-H for singlet discrimination)."),
        ("singlets_scale", "Axis scale", "choice",
         "Logarithmic or linear axes for the singlets scatter.",
         ["log", "linear"]),
        ("singlets_xlim_auto", "Auto X range", "bool",
         "Use percentile-based limits that ignore extreme outliers."),
        ("singlets_xlim_lo", "X min", "float", "Left end of the singlets scatter x axis (used when auto is off)."),
        ("singlets_xlim_hi", "X max", "float", "Right end of the singlets scatter x axis."),
        ("singlets_ylim_auto", "Auto Y range", "bool",
         "Use percentile-based limits that ignore extreme outliers."),
        ("singlets_ylim_lo", "Y min", "float", "Bottom end of the singlets scatter y axis (used when auto is off)."),
        ("singlets_ylim_hi", "Y max", "float", "Top end of the singlets scatter y axis."),
        ("singlets_xlabel", "X label", "text", "Leave empty to derive from the x channel."),
        ("singlets_ylabel", "Y label", "text", "Leave empty to derive from the y channel."),
    ]),
    ("Analysis scatter", [
        ("analysis_x", "X channel", "channel",
         "Fluorescence parameter on the analysis scatter x axis."),
        ("analysis_y", "Y channel", "channel",
         "Fluorescence parameter on the analysis scatter y axis."),
        ("analysis_scale", "Axis scale", "choice",
         "Logarithmic or linear axes for the analysis scatter.",
         ["log", "linear"]),
        ("analysis_xlim_auto", "Auto X range", "bool",
         "Use percentile-based limits that ignore extreme outliers."),
        ("analysis_xlim_lo", "X min", "float", "Left end of the analysis scatter x axis (used when auto is off)."),
        ("analysis_xlim_hi", "X max", "float", "Right end of the analysis scatter x axis."),
        ("analysis_ylim_auto", "Auto Y range", "bool",
         "Use percentile-based limits that ignore extreme outliers."),
        ("analysis_ylim_lo", "Y min", "float", "Bottom end of the analysis scatter y axis (used when auto is off)."),
        ("analysis_ylim_hi", "Y max", "float", "Top end of the analysis scatter y axis."),
        ("analysis_xlabel", "X label", "text", "Leave empty to derive from the x channel."),
        ("analysis_ylabel", "Y label", "text", "Leave empty to derive from the y channel."),
    ]),
    ("Shared style", [
        ("font_family", "Font", "text", "Font family, e.g. Arial or Helvetica. Applied to both graphs."),
        ("font_size", "Base font size", "float", "Applies to axis labels and the legend."),
        ("axes_linewidth", "Axis line width", "float", "Thickness of the axis spines."),
        ("tick_direction", "Direction", "choice",
         "Where tick marks point relative to the axis.", ["in", "out", "inout"]),
        ("tick_length", "Major length", "float", "Length of labelled ticks in points."),
        ("tick_minor_length", "Minor length", "float", "Length of unlabelled ticks in points."),
        ("tick_width", "Major width", "float", "Line width of labelled ticks."),
        ("tick_minor_width", "Minor width", "float", "Line width of unlabelled ticks."),
        ("minor_x", "Minor ticks X", "bool", "Show the 2-9 subdivisions inside each decade."),
        ("minor_y", "Minor ticks Y", "bool", "Show intermediate ticks on the y axis."),
        ("y_minor_per_major", "Y minor per major", "int",
         "Subdivisions between two labelled y ticks. 0 lets matplotlib decide."),
        ("tick_label_size", "Label size", "float", "Font size of the tick numbers in points."),
        ("spine_top", "Top frame line", "bool", "Show the axis line along the top edge."),
        ("spine_right", "Right frame line", "bool", "Show the axis line along the right edge."),
        ("grid", "Grid", "bool", "Draw faint grid lines at the major ticks."),
        ("grid_alpha", "Grid opacity", "float", "Opacity of the grid lines."),
        ("legend_show", "Legend", "bool", "Show the sample legend."),
        ("legend_loc", "Legend position", "choice", "Where to place the legend.", LEGEND_LOCS),
        ("legend_frame", "Legend box", "bool", "Draw a frame around the legend."),
    ]),
    ("Output", [
        ("fig_w", "Width (inch)", "float", "Figure width; 3.0-3.5 in suits a single journal column. Set width = height for a square plot area."),
        ("fig_h", "Height (inch)", "float", "Figure height. Set width = height for a square plot area."),
        ("dpi", "Resolution (dpi)", "int", "Raster resolution of the PNG; the PDF stays vector."),
        ("out_pdf", "Histogram PDF", "text", "Histogram PDF file name."),
        ("out_png", "Histogram PNG", "text", "Histogram PNG file name."),
        ("out_scatter_pdf", "Gating scatter PDF", "text", "Gating scatter PDF file name."),
        ("out_scatter_png", "Gating scatter PNG", "text", "Gating scatter PNG file name."),
        ("out_singlets_pdf", "Singlets scatter PDF", "text", "Singlets scatter PDF file name."),
        ("out_singlets_png", "Singlets scatter PNG", "text", "Singlets scatter PNG file name."),
        ("out_analysis_pdf", "Analysis scatter PDF", "text", "Analysis scatter PDF file name."),
        ("out_analysis_png", "Analysis scatter PNG", "text", "Analysis scatter PNG file name."),
        ("out_xlsx", "XLSX statistics file", "text", "Excel file with per-sample statistics. Sample names are appended automatically."),
    ]),
]

DEFAULTS = {
    # histogram
    "channel": "ECD-A",
    "x_scale": "log",
    "min_value": 1e-1,
    "y_axis": "counts",
    "n_bins": 500,
    "smooth_sigma": 1.5,
    "xlim_lo": 1e-1,
    "xlim_hi": 1e6,
    "ylim_auto": True,
    "y_headroom": 1.2,
    "ylim_lo": 0.0,
    "ylim_hi": 1.0,
    "xlabel": "",
    "ylabel": "",
    "title": "",
    "line_width": 1.2,
    "fill_alpha": 0.25,
    # gating scatter
    "scatter_x": "FSC-A",
    "scatter_y": "SSC-A",
    "scatter_scale": "log",
    "scatter_xlim_auto": True,
    "scatter_xlim_lo": 1e3,
    "scatter_xlim_hi": 1e6,
    "scatter_ylim_auto": True,
    "scatter_ylim_lo": 1e3,
    "scatter_ylim_hi": 1e6,
    "scatter_xlabel": "",
    "scatter_ylabel": "",
    "scatter_point_size": 2.0,
    "scatter_point_alpha": 0.45,
    # singlets scatter
    "singlets_x": "FSC-A",
    "singlets_y": "FSC-H",
    "singlets_scale": "log",
    "singlets_xlim_auto": True,
    "singlets_xlim_lo": 1e3,
    "singlets_xlim_hi": 1e6,
    "singlets_ylim_auto": True,
    "singlets_ylim_lo": 1e3,
    "singlets_ylim_hi": 1e6,
    "singlets_xlabel": "",
    "singlets_ylabel": "",
    # analysis scatter
    "analysis_x": "ECD-A",
    "analysis_y": "FSC-A",
    "analysis_scale": "log",
    "analysis_xlim_auto": True,
    "analysis_xlim_lo": 1e-1,
    "analysis_xlim_hi": 1e6,
    "analysis_ylim_auto": True,
    "analysis_ylim_lo": 1e3,
    "analysis_ylim_hi": 1e6,
    "analysis_xlabel": "",
    "analysis_ylabel": "",
    # shared style
    "font_family": "Arial",
    "font_size": 10.0,
    "axes_linewidth": 1.0,
    "tick_direction": "in",
    "tick_length": 4.0,
    "tick_minor_length": 2.5,
    "tick_width": 1.0,
    "tick_minor_width": 1.0,
    "minor_x": True,
    "minor_y": True,
    "y_minor_per_major": 0,
    "tick_label_size": 10.0,
    "spine_top": False,
    "spine_right": False,
    "grid": False,
    "grid_alpha": 0.3,
    "legend_show": True,
    "legend_loc": "upper left",
    "legend_frame": False,
    # output
    "fig_w": 3.0,
    "fig_h": 3.0,
    "dpi": 600,
    "out_pdf": "ECD-A_histogram.pdf",
    "out_png": "ECD-A_histogram.png",
    "out_scatter_pdf": "gating_scatter.pdf",
    "out_scatter_png": "gating_scatter.png",
    "out_singlets_pdf": "singlets_scatter.pdf",
    "out_singlets_png": "singlets_scatter.png",
    "out_analysis_pdf": "analysis_scatter.pdf",
    "out_analysis_png": "analysis_scatter.png",
    "out_xlsx": "statistics",
}

FIELD_TYPES = {key: spec[2] for _group, fields in SCHEMA for spec in fields for key in [spec[0]]}


def coerce(key, value):
    """Convert one raw GUI value to the type declared in the schema."""
    kind = FIELD_TYPES.get(key)
    if kind == "int":
        return int(float(value))
    if kind == "float":
        return float(value)
    if kind == "bool":
        return bool(value) if isinstance(value, bool) else str(value).lower() in ("1", "true", "yes", "on")
    return str(value)


def merge_settings(overrides=None):
    """Defaults updated with (possibly string-typed) overrides."""
    s = dict(DEFAULTS)
    for key, value in (overrides or {}).items():
        if key not in FIELD_TYPES:
            continue
        if value is None or value == "":
            if FIELD_TYPES[key] == "text":
                s[key] = ""
            continue
        try:
            s[key] = coerce(key, value)
        except (TypeError, ValueError):
            pass  # keep the default when a field is mid-edit
    return s


# ------------------------------------------------------------------- data --
def read_fcs(path):
    """Read an FCS file into a DataFrame of events x channels."""
    return readfcs.read(str(path)).to_df()


def apply_gate(df, gate):
    """Keep events inside a gate. Supports polygon, quadrant, and interval types."""
    if not gate:
        return df
    gtype = gate.get("type", "polygon")
    if gtype == "polygon":
        if len(gate.get("verts", [])) < 3:
            return df
        points = np.column_stack([df[gate["x"]].to_numpy(float),
                                   df[gate["y"]].to_numpy(float)])
        return df[MplPath(np.asarray(gate["verts"], dtype=float)).contains_points(points)]
    if gtype == "quadrant":
        x_thr, y_thr = gate["x_threshold"], gate["y_threshold"]
        x_vals = df[gate["x"]].to_numpy(float)
        y_vals = df[gate["y"]].to_numpy(float)
        mask = np.zeros(len(df), dtype=bool)
        for q in gate.get("quadrants", []):
            if q == "UR":
                mask |= (x_vals > x_thr) & (y_vals > y_thr)
            elif q == "UL":
                mask |= (x_vals <= x_thr) & (y_vals > y_thr)
            elif q == "LL":
                mask |= (x_vals <= x_thr) & (y_vals <= y_thr)
            elif q == "LR":
                mask |= (x_vals > x_thr) & (y_vals <= y_thr)
        return df[mask]
    if gtype == "interval":
        ch, lo, hi = gate["channel"], gate["lo"], gate["hi"]
        vals = df[ch].to_numpy(float)
        return df[(vals >= lo) & (vals <= hi)]
    return df


def channel_values(df, s, scatter_gate=None, singlets_gate=None,
                    hist_gate=None, analysis_gate=None):
    """Gated values of the selected channel (positive-only on log axes).

    Gate chain: scatter_gate -> singlets_gate -> hist_gate -> analysis_gate.
    """
    gated = df
    if scatter_gate:
        gated = apply_gate(gated, scatter_gate)
    if singlets_gate:
        gated = apply_gate(gated, singlets_gate)
    if hist_gate:
        gated = apply_gate(gated, hist_gate)
    if analysis_gate:
        gated = apply_gate(gated, analysis_gate)
    values = gated[s["channel"]].to_numpy(dtype=float)
    if s.get("x_scale", "log") == "log":
        values = values[values > s["min_value"]]
    else:
        values = values[values >= s["min_value"]]
    return values


# ------------------------------------------------------------------ style --
def apply_style(s):
    sns.reset_orig()
    sns.set_style("ticks")
    ff = s["font_family"]
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": [ff, "DejaVu Sans"],
        "font.size": s["font_size"],
        "axes.labelsize": s["font_size"],
        "legend.fontsize": s["font_size"],
        "xtick.labelsize": s["tick_label_size"],
        "ytick.labelsize": s["tick_label_size"],
        "axes.linewidth": s["axes_linewidth"],
        "xtick.direction": s["tick_direction"],
        "ytick.direction": s["tick_direction"],
        "xtick.major.size": s["tick_length"],
        "ytick.major.size": s["tick_length"],
        "xtick.minor.size": s["tick_minor_length"],
        "ytick.minor.size": s["tick_minor_length"],
        "xtick.major.width": s["tick_width"],
        "ytick.major.width": s["tick_width"],
        "xtick.minor.width": s["tick_minor_width"],
        "ytick.minor.width": s["tick_minor_width"],
        "xtick.minor.visible": s["minor_x"],
        "ytick.minor.visible": s["minor_y"],
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
        "text.usetex": False,
        "mathtext.fontset": "custom",
        "mathtext.rm": ff,
        "mathtext.it": f"{ff}:italic",
        "mathtext.bf": f"{ff}:bold",
        "mathtext.cal": "cursive",
        "mathtext.tt": "monospace",
        "mathtext.sf": ff,
    })


# --------------------------------------------------------------- renderer --
def histogram_curve(values, s):
    """Binned (and optionally smoothed) curve: (bin centres, heights)."""
    n_bins = max(int(s["n_bins"]), 2)
    sigma = max(float(s["smooth_sigma"]), 0.0)
    density = s["y_axis"] == "density"
    if s["x_scale"] == "linear":
        bins = np.linspace(s["xlim_lo"], s["xlim_hi"], n_bins + 1)
        centers = 0.5 * (bins[:-1] + bins[1:])
        if values.size == 0:
            return centers, np.zeros(len(centers))
        counts, _ = np.histogram(values, bins=bins, density=density)
    else:
        log_bins = np.linspace(np.log10(s["xlim_lo"]), np.log10(s["xlim_hi"]), n_bins + 1)
        centers = 10 ** (0.5 * (log_bins[:-1] + log_bins[1:]))
        if values.size == 0:
            return centers, np.zeros(len(centers))
        counts, _ = np.histogram(np.log10(values), bins=log_bins, density=density)
    counts = counts.astype(float)
    if sigma > 0:
        counts = gaussian_filter1d(counts, sigma=sigma, mode="constant", cval=0.0)
    if s["y_axis"] == "percent_of_max" and counts.max() > 0:
        counts = 100 * counts / counts.max()
    return centers, counts


def draw_histogram(ax, series, s):
    """Draw overlaid histograms. series = [{label, color, values, hist_gate?}, ...]."""
    y_max = 0.0
    smoothed = s["smooth_sigma"] > 0
    for item in series:
        centers, counts = histogram_curve(item["values"], s)
        y_max = max(y_max, float(counts.max()))
        if s["fill_alpha"] > 0:
            ax.fill_between(centers, counts, step=None if smoothed else "mid",
                            color=item["color"], alpha=s["fill_alpha"], lw=0)
        if smoothed:
            ax.plot(centers, counts, color=item["color"],
                    lw=s["line_width"], label=item["label"])
        else:
            ax.step(centers, counts, where="mid", color=item["color"],
                    lw=s["line_width"], label=item["label"])

    if s["x_scale"] == "linear":
        ax.set_xscale("linear")
    else:
        ax.set_xscale("log")
    ax.set_xlim(s["xlim_lo"], s["xlim_hi"])
    if s["ylim_auto"]:
        ax.set_ylim(0, max(y_max, 1e-9) * s["y_headroom"])
    else:
        ax.set_ylim(s["ylim_lo"], s["ylim_hi"])

    ax.set_xlabel(s["xlabel"] or f"{s['channel']} fluorescence intensity")
    ax.set_ylabel(s["ylabel"] or Y_AXIS_MODES[s["y_axis"]])
    if s["title"]:
        ax.set_title(s["title"])
    ax.margins(x=0)

    if s["x_scale"] == "log":
        decades = max(int(np.log10(s["xlim_hi"]) - np.log10(s["xlim_lo"])), 1) + 1
        ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,), numticks=decades + 2))
        ax.xaxis.set_major_formatter(FuncFormatter(_log_tick_label))
        if s["minor_x"]:
            ax.xaxis.set_minor_locator(
                LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10 * decades))
            ax.xaxis.set_minor_formatter(NullFormatter())
    else:
        if s["minor_x"]:
            ax.xaxis.set_minor_locator(AutoMinorLocator())
    if s["minor_y"]:
        n = s["y_minor_per_major"]
        ax.yaxis.set_minor_locator(AutoMinorLocator(n if n > 0 else None))

    ax.tick_params(which="minor", top=False, right=False)
    if s["grid"]:
        ax.grid(True, which="major", alpha=s["grid_alpha"], lw=s["axes_linewidth"] * 0.6)
        ax.set_axisbelow(True)

    # Draw interval gate lines per sample
    for item in series:
        hg = item.get("hist_gate")
        if hg and hg.get("type") == "interval":
            ax.axvline(hg["lo"], color=item["color"], lw=1.0, ls="--", alpha=0.7, zorder=5)
            ax.axvline(hg["hi"], color=item["color"], lw=1.0, ls="--", alpha=0.7, zorder=5)

    if s["legend_show"] and series:
        ax.legend(frameon=s["legend_frame"], loc=s["legend_loc"], handlelength=1.4)

    sns.despine(ax=ax, top=not s["spine_top"], right=not s["spine_right"])


def _percentile_limits(values, low_pct=0.2, high_pct=99.8):
    """Decade-aligned limits that ignore extreme outliers."""
    positive = values[values > 0]
    if not positive.size:
        return 1.0, 1e6
    lo, hi = np.percentile(positive, [low_pct, high_pct])
    lo = 10 ** np.floor(np.log10(lo))
    hi = 10 ** np.ceil(np.log10(hi))
    if hi <= lo * 10:
        hi = lo * 100
    return float(lo), float(hi)


def draw_scatter(ax, df, color, gate, s, x_ch=None, y_ch=None,
                 xlabel=None, ylabel=None, scale_key="scatter_scale",
                 xlim_auto_key="scatter_xlim_auto", xlim_lo_key="scatter_xlim_lo",
                 xlim_hi_key="scatter_xlim_hi", ylim_auto_key="scatter_ylim_auto",
                 ylim_lo_key="scatter_ylim_lo", ylim_hi_key="scatter_ylim_hi",
                 xlabel_key="scatter_xlabel", ylabel_key="scatter_ylabel"):
    """Draw a scatter plot for one sample with optional gate overlay.

    Defaults to gating-scatter channels; pass x_ch/y_ch and the *_key args
    to render the analysis scatter instead.
    """
    if x_ch is None:
        x_ch = s["scatter_x"]
    if y_ch is None:
        y_ch = s["scatter_y"]
    ps = s["scatter_point_size"]
    pa = s["scatter_point_alpha"]

    inside = apply_gate(df, gate) if gate else None
    ax.scatter(df[x_ch], df[y_ch], s=ps, c="#b9bfc9", alpha=pa,
               linewidths=0, rasterized=True)
    if inside is not None and len(inside):
        ax.scatter(inside[x_ch], inside[y_ch], s=ps, c=color, alpha=min(pa + 0.1, 1),
                   linewidths=0, rasterized=True)

    scale = s.get(scale_key, "log")
    if scale == "log":
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.xaxis.set_major_formatter(FuncFormatter(_log_tick_label))
        ax.yaxis.set_major_formatter(FuncFormatter(_log_tick_label))
        if s["minor_x"]:
            decades_x = max(int(np.log10(ax.get_xlim()[1]) - np.log10(ax.get_xlim()[0])), 1) + 1
            ax.xaxis.set_minor_locator(
                LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10 * decades_x))
            ax.xaxis.set_minor_formatter(NullFormatter())
        if s["minor_y"]:
            decades_y = max(int(np.log10(ax.get_ylim()[1]) - np.log10(ax.get_ylim()[0])), 1) + 1
            ax.yaxis.set_minor_locator(
                LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10 * decades_y))
            ax.yaxis.set_minor_formatter(NullFormatter())
    else:
        ax.set_xscale("linear")
        ax.set_yscale("linear")
        if s["minor_x"]:
            ax.xaxis.set_minor_locator(AutoMinorLocator())
        if s["minor_y"]:
            ax.yaxis.set_minor_locator(AutoMinorLocator())

    ax.set_xlabel(s.get(xlabel_key, "") or x_ch)
    ax.set_ylabel(s.get(ylabel_key, "") or y_ch)
    ax.tick_params(which="minor", top=False, right=False)
    if s["grid"]:
        ax.grid(True, which="major", alpha=s["grid_alpha"], lw=s["axes_linewidth"] * 0.6)
        ax.set_axisbelow(True)
    sns.despine(ax=ax, top=not s["spine_top"], right=not s["spine_right"])

    # Draw gate boundary overlay
    if gate:
        gtype = gate.get("type", "polygon")
        if gtype == "polygon" and len(gate.get("verts", [])) >= 3:
            verts = gate["verts"] + [gate["verts"][0]]
            ax.plot([v[0] for v in verts], [v[1] for v in verts],
                    color="#333333", lw=1.2, ls="--", zorder=5)
        elif gtype == "quadrant":
            ax.axvline(gate["x_threshold"], color="#333333", lw=1.0, ls="--", zorder=5)
            ax.axhline(gate["y_threshold"], color="#333333", lw=1.0, ls="--", zorder=5)


def _gate_label(gate):
    """Human-readable label for a gate."""
    if not gate:
        return "None"
    gtype = gate.get("type", "polygon")
    if gtype == "polygon":
        return f"Polygon ({gate.get('x','?')}/{gate.get('y','?')})"
    if gtype == "quadrant":
        qs = "+".join(gate.get("quadrants", [])) or "none"
        return f"Quadrant {qs} ({gate.get('x','?')}/{gate.get('y','?')})"
    if gtype == "interval":
        return f"Interval {gate.get('channel','?')} [{gate.get('lo','?')}, {gate.get('hi','?')}]"
    return gtype


def _stats(vals):
    """Compute statistics for a 1D array of values."""
    if vals.size == 0:
        return {"count": 0, "mean": None, "median": None, "std": None,
                "min": None, "max": None, "p5": None, "p25": None,
                "p75": None, "p95": None, "geo_mean": None}
    positive = vals[vals > 0]
    geo = float(np.exp(np.mean(np.log(positive)))) if positive.size else None
    return {
        "count": int(vals.size),
        "mean": float(np.mean(vals)),
        "median": float(np.median(vals)),
        "std": float(np.std(vals, ddof=1)) if vals.size > 1 else 0.0,
        "min": float(np.min(vals)),
        "max": float(np.max(vals)),
        "p5": float(np.percentile(vals, 5)),
        "p25": float(np.percentile(vals, 25)),
        "p75": float(np.percentile(vals, 75)),
        "p95": float(np.percentile(vals, 95)),
        "geo_mean": geo,
    }


def _quadrant_mask(df, gate, quadrant):
    """Return boolean mask for one quadrant of a quadrant gate."""
    x_thr, y_thr = gate["x_threshold"], gate["y_threshold"]
    x_vals = df[gate["x"]].to_numpy(float)
    y_vals = df[gate["y"]].to_numpy(float)
    if quadrant == "UR":
        return (x_vals > x_thr) & (y_vals > y_thr)
    if quadrant == "UL":
        return (x_vals <= x_thr) & (y_vals > y_thr)
    if quadrant == "LL":
        return (x_vals <= x_thr) & (y_vals <= y_thr)
    if quadrant == "LR":
        return (x_vals > x_thr) & (y_vals <= y_thr)
    return np.zeros(len(df), dtype=bool)


def _sanitize(name):
    """Make a string safe for filenames."""
    return re.sub(r'[^A-Za-z0-9_\-]+', '_', name).strip('_') or "sample"


def save_statistics(samples_info, s, out_dir=RESULTS_DIR):
    """Write an XLSX file with per-sample statistics.

    For each sample, produces rows for the histogram and analysis scatter
    (excluding the gating scatter) at each gating stage:
    ungated -> live cell gated -> singlets gated -> histogram gated -> analysis gated
    (with per-quadrant breakdown for quadrant analysis gates).

    samples_info = [{label, color, df, scatter_gate, singlets_gate, hist_gate, analysis_gate}, ...]
    """
    try:
        import openpyxl
    except ImportError:
        return None

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Statistics"

    headers = [
        "Sample", "Plot", "Channel", "Condition", "Quadrant",
        "Count", "Mean", "Median", "Std", "Min", "Max",
        "P5", "P25", "P75", "P95", "Geo. mean",
    ]
    ws.append(headers)

    hist_ch = s["channel"]
    analysis_channels = [s["analysis_x"], s["analysis_y"]]

    for info in samples_info:
        df = info["df"]
        sg = info.get("scatter_gate")
        sig = info.get("singlets_gate")
        hg = info.get("hist_gate")
        ag = info.get("analysis_gate")
        label = info["label"]

        # Build gating stages: list of (condition, df_at_stage)
        stages = [("ungated", df)]

        live_cell = apply_gate(df, sg) if sg else df
        stages.append(("live cell gated", live_cell))

        singlets_cell = apply_gate(live_cell, sig) if sig else live_cell
        if sig:
            stages.append(("singlets gated", singlets_cell))

        if hg:
            hist_gated_df = apply_gate(singlets_cell, hg)
            stages.append(("histogram gated", hist_gated_df))
        else:
            hist_gated_df = singlets_cell

        has_quadrant_analysis = ag and ag.get("type") == "quadrant"
        if ag and not has_quadrant_analysis:
            all_gated = apply_gate(hist_gated_df, ag)
            stages.append(("analysis gated", all_gated))

        # Write rows for each plot and channel at each stage
        for plot_name, channels in [("Histogram", [hist_ch]),
                                     ("Analysis scatter", analysis_channels)]:
            for condition, df_stage in stages:
                for ch in channels:
                    vals = df_stage[ch].to_numpy(dtype=float)
                    st = _stats(vals)
                    ws.append([label, plot_name, ch, condition, "",
                               st["count"], st["mean"], st["median"], st["std"],
                               st["min"], st["max"], st["p5"], st["p25"],
                               st["p75"], st["p95"], st["geo_mean"]])

        # Per-quadrant rows for quadrant analysis gates
        if has_quadrant_analysis:
            for q in ag.get("quadrants", []):
                mask = _quadrant_mask(hist_gated_df, ag, q)
                df_q = hist_gated_df[mask]
                for plot_name, channels in [("Histogram", [hist_ch]),
                                             ("Analysis scatter", analysis_channels)]:
                    for ch in channels:
                        vals = df_q[ch].to_numpy(dtype=float)
                        st = _stats(vals)
                        ws.append([label, plot_name, ch, "analysis gated", q,
                                   st["count"], st["mean"], st["median"], st["std"],
                                   st["min"], st["max"], st["p5"], st["p25"],
                                   st["p75"], st["p95"], st["geo_mean"]])

    # Auto-size columns
    for col in ws.columns:
        max_len = max(len(str(c.value)) if c.value else 0 for c in col)
        ws.column_dimensions[col[0].column_letter].width = max_len + 2

    # Build filename from sample names to avoid overwriting
    base_name = s.get("out_xlsx", "statistics")
    labels = [_sanitize(info["label"]) for info in samples_info]
    if labels:
        suffix = "_" + "_".join(labels[:3])
        if len(labels) > 3:
            suffix += f"_+{len(labels) - 3}"
    else:
        suffix = ""
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    xlsx_path = Path(out_dir) / f"{base_name}{suffix}.xlsx"
    wb.save(xlsx_path)
    return xlsx_path


def make_figure(series, s):
    apply_style(s)
    fig, ax = plt.subplots(figsize=(s["fig_w"], s["fig_h"]))
    draw_histogram(ax, series, s)
    fig.tight_layout()
    return fig


def save_figure(series, s, out_dir=RESULTS_DIR):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fig = make_figure(series, s)
    pdf, png = Path(out_dir) / s["out_pdf"], Path(out_dir) / s["out_png"]
    fig.savefig(pdf)
    fig.savefig(png, dpi=s["dpi"])
    plt.close(fig)
    return pdf, png


def make_scatter_figure(sample, gate, s):
    """Create a publication-quality gating scatter figure for one sample."""
    apply_style(s)
    fig, ax = plt.subplots(figsize=(s["fig_w"], s["fig_h"]))

    x_ch, y_ch = s["scatter_x"], s["scatter_y"]
    pooled_x = sample["df"][x_ch].to_numpy(float)
    pooled_y = sample["df"][y_ch].to_numpy(float)
    if s.get("scatter_xlim_auto"):
        ax.set_xlim(*_percentile_limits(pooled_x))
    else:
        ax.set_xlim(s["scatter_xlim_lo"], s["scatter_xlim_hi"])
    if s.get("scatter_ylim_auto"):
        ax.set_ylim(*_percentile_limits(pooled_y))
    else:
        ax.set_ylim(s["scatter_ylim_lo"], s["scatter_ylim_hi"])

    draw_scatter(ax, sample["df"], sample["color"], gate, s)
    fig.tight_layout()
    return fig


def save_scatter_figure(sample, gate, s, out_dir=RESULTS_DIR):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fig = make_scatter_figure(sample, gate, s)
    pdf = Path(out_dir) / s["out_scatter_pdf"]
    png = Path(out_dir) / s["out_scatter_png"]
    fig.savefig(pdf)
    fig.savefig(png, dpi=s["dpi"])
    plt.close(fig)
    return pdf, png


def make_analysis_scatter_figure(sample, gate, s, scatter_gate=None, singlets_gate=None):
    """Create a publication-quality analysis scatter figure for one sample.

    The data is pre-filtered by the scatter (gating) gate and the singlets
    gate so the analysis scatter shows only live single cells, then the
    analysis gate is applied on top.
    """
    apply_style(s)
    fig, ax = plt.subplots(figsize=(s["fig_w"], s["fig_h"]))

    x_ch, y_ch = s["analysis_x"], s["analysis_y"]
    df = sample["df"]
    if scatter_gate:
        df = apply_gate(df, scatter_gate)
    if singlets_gate:
        df = apply_gate(df, singlets_gate)
    pooled_x = df[x_ch].to_numpy(float)
    pooled_y = df[y_ch].to_numpy(float)
    if s.get("analysis_xlim_auto"):
        ax.set_xlim(*_percentile_limits(pooled_x))
    else:
        ax.set_xlim(s["analysis_xlim_lo"], s["analysis_xlim_hi"])
    if s.get("analysis_ylim_auto"):
        ax.set_ylim(*_percentile_limits(pooled_y))
    else:
        ax.set_ylim(s["analysis_ylim_lo"], s["analysis_ylim_hi"])

    draw_scatter(ax, df, sample["color"], gate, s,
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
    fig.tight_layout()
    return fig


def save_analysis_scatter_figure(sample, gate, s, scatter_gate=None,
                                 singlets_gate=None, out_dir=RESULTS_DIR):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fig = make_analysis_scatter_figure(sample, gate, s,
                                       scatter_gate=scatter_gate,
                                       singlets_gate=singlets_gate)
    pdf = Path(out_dir) / s["out_analysis_pdf"]
    png = Path(out_dir) / s["out_analysis_png"]
    fig.savefig(pdf)
    fig.savefig(png, dpi=s["dpi"])
    plt.close(fig)
    return pdf, png


def make_singlets_scatter_figure(sample, gate, s, scatter_gate=None):
    """Create a publication-quality singlets scatter figure for one sample.

    The data is pre-filtered by the scatter (gating) gate so the singlets
    scatter shows only live cells, then the singlets gate is applied on top.
    """
    apply_style(s)
    fig, ax = plt.subplots(figsize=(s["fig_w"], s["fig_h"]))

    x_ch, y_ch = s["singlets_x"], s["singlets_y"]
    df = apply_gate(sample["df"], scatter_gate) if scatter_gate else sample["df"]
    pooled_x = df[x_ch].to_numpy(float)
    pooled_y = df[y_ch].to_numpy(float)
    if s.get("singlets_xlim_auto"):
        ax.set_xlim(*_percentile_limits(pooled_x))
    else:
        ax.set_xlim(s["singlets_xlim_lo"], s["singlets_xlim_hi"])
    if s.get("singlets_ylim_auto"):
        ax.set_ylim(*_percentile_limits(pooled_y))
    else:
        ax.set_ylim(s["singlets_ylim_lo"], s["singlets_ylim_hi"])

    draw_scatter(ax, df, sample["color"], gate, s,
                 x_ch=x_ch, y_ch=y_ch,
                 scale_key="singlets_scale",
                 xlim_auto_key="singlets_xlim_auto",
                 xlim_lo_key="singlets_xlim_lo",
                 xlim_hi_key="singlets_xlim_hi",
                 ylim_auto_key="singlets_ylim_auto",
                 ylim_lo_key="singlets_ylim_lo",
                 ylim_hi_key="singlets_ylim_hi",
                 xlabel_key="singlets_xlabel",
                 ylabel_key="singlets_ylabel")
    fig.tight_layout()
    return fig


def save_singlets_scatter_figure(sample, gate, s, scatter_gate=None,
                                 out_dir=RESULTS_DIR):
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    fig = make_singlets_scatter_figure(sample, gate, s, scatter_gate=scatter_gate)
    pdf = Path(out_dir) / s["out_singlets_pdf"]
    png = Path(out_dir) / s["out_singlets_png"]
    fig.savefig(pdf)
    fig.savefig(png, dpi=s["dpi"])
    plt.close(fig)
    return pdf, png
