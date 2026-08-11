#!/usr/bin/env python3
"""Overlay ECD-A channel histograms from three .fcs files (publication quality)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import readfcs
import seaborn as sns
from matplotlib.ticker import AutoMinorLocator, LogLocator, NullFormatter
from scipy.ndimage import gaussian_filter1d

# ---------------------------------------------------------------- settings --
DATA_DIR = Path(__file__).parent

FILES = {
    "HeLa WT": DATA_DIR / "03-HeLA WT-C1.fcs",
    "pMLM049 clone 6 Dark": DATA_DIR / "03-HeLa pMLM049 clone 6 Dark-B4.fcs",
    "pMLM049 clone 6 Light": DATA_DIR / "03-HeLa pMLM049 clone 6 Light-B3.fcs",
}

SETTINGS = {
    # data
    "channel": "ECD-A",
    "min_value": 1e-1,         # events <= this are excluded (log display)
    # optional rectangular scatter gate: {channel: (low, high)}, or None
    # e.g. {"FSC-A": (5e4, 6e5), "SSC-A": (3e4, 5e5)}
    "gate": None,
    "n_bins": 500,             # log-spaced bins across xlim
    "smooth_sigma": 1.5,       # gaussian smoothing width in bins (0 = off)
    "xlim": (1e-1, 1e6),
    # y axis: "density" (area-normalized) | "counts" | "percent_of_max"
    "y_axis": "density",
    # colors (one per entry in FILES, in order)
    "colors": ["#4C72B0", "#55A868", "#C44E52"],
    "fill_alpha": 0.25,
    "line_width": 1.2,
    # figure
    "figsize": (3.0, 2.8),     # inches (single-column width)
    "dpi": 600,                # output resolution
    # fonts
    "font_family": "Arial",
    "font_size": 10,
    # axes / ticks (matches companion figure style)
    "axes_linewidth": 1.0,
    "tick_direction": "in",
    "tick_length": 4,
    "tick_minor_length": 2.5,
    "tick_width": 1.0,
    "xlabel": "ECD-A fluorescence intensity",
    "ylabel": None,            # None = derived from y_axis mode
    # output
    "out_pdf": "ECD-A_histogram.pdf",
    "out_png": "ECD-A_histogram.png",
}
# ---------------------------------------------------------------------------


def load_channel(path: Path, channel: str, gate: dict | None) -> np.ndarray:
    adata = readfcs.read(path)
    df = adata.to_df()
    for ch in [channel, *(gate or {})]:
        if ch not in df.columns:
            raise KeyError(f"Channel '{ch}' not found in {path.name}. Available: {df.columns.tolist()}")
    if gate:
        mask = np.ones(len(df), dtype=bool)
        for ch, (low, high) in gate.items():
            mask &= df[ch].between(low, high).to_numpy()
        print(f"{path.name}: gate kept {mask.sum()}/{len(df)} events ({100 * mask.mean():.1f}%)")
        df = df[mask]
    return df[channel].to_numpy(dtype=float)


def main() -> None:
    s = SETTINGS

    sns.reset_orig()
    sns.set_style("ticks")
    plt.rcParams.update({
        "font.family": s["font_family"],
        "font.size": s["font_size"],
        "axes.labelsize": s["font_size"],
        "xtick.labelsize": s["font_size"],
        "ytick.labelsize": s["font_size"],
        "legend.fontsize": s["font_size"],
        "axes.linewidth": s["axes_linewidth"],
        "xtick.direction": s["tick_direction"],
        "ytick.direction": s["tick_direction"],
        "xtick.major.size": s["tick_length"],
        "ytick.major.size": s["tick_length"],
        "xtick.minor.size": s["tick_minor_length"],
        "ytick.minor.size": s["tick_minor_length"],
        "xtick.major.width": s["tick_width"],
        "ytick.major.width": s["tick_width"],
        "xtick.minor.width": s["tick_width"],
        "ytick.minor.width": s["tick_width"],
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    data = {}
    for label, path in FILES.items():
        values = load_channel(path, s["channel"], s["gate"])
        values = values[values > s["min_value"]]  # log display: drop non-positive events
        data[label] = values

    log_bins = np.linspace(np.log10(s["xlim"][0]), np.log10(s["xlim"][1]), s["n_bins"] + 1)

    fig, ax = plt.subplots(figsize=s["figsize"])

    ylabels = {"density": "Density", "counts": "Events", "percent_of_max": "% of max"}
    if s["y_axis"] not in ylabels:
        raise ValueError(f"y_axis must be one of {list(ylabels)}, got {s['y_axis']!r}")

    y_max = 0.0
    for (label, values), color in zip(data.items(), s["colors"]):
        if s["y_axis"] == "density":
            counts, edges = np.histogram(np.log10(values), bins=log_bins, density=True)
        else:
            counts, edges = np.histogram(np.log10(values), bins=log_bins)
            counts = counts.astype(float)
            if s["y_axis"] == "percent_of_max":
                counts = 100 * counts / counts.max()
        if s["smooth_sigma"] > 0:
            counts = gaussian_filter1d(counts, sigma=s["smooth_sigma"], mode="nearest")
        y_max = max(y_max, float(counts.max()))
        centers = 10 ** (0.5 * (edges[:-1] + edges[1:]))
        ax.fill_between(centers, counts, step="mid", alpha=s["fill_alpha"], color=color, lw=0)
        ax.step(centers, counts, where="mid", color=color, lw=s["line_width"], label=label)

    ax.set_xscale("log")
    ax.set_xlim(*s["xlim"])
    ax.set_ylim(0, y_max * 1.45)  # headroom for the legend
    ax.set_xlabel(s["xlabel"])
    ax.set_ylabel(s["ylabel"] or ylabels[s["y_axis"]])
    ax.margins(x=0)

    n_decades = int(np.log10(s["xlim"][1]) - np.log10(s["xlim"][0])) + 1
    ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,), numticks=n_decades + 2))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10 * n_decades))
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.yaxis.set_minor_locator(AutoMinorLocator())

    ax.legend(frameon=False, loc="upper left", handlelength=1.4)
    sns.despine(ax=ax)

    fig.tight_layout()
    fig.savefig(DATA_DIR / s["out_pdf"])
    fig.savefig(DATA_DIR / s["out_png"], dpi=s["dpi"])
    print(f"Saved {DATA_DIR / s['out_pdf']} and {s['out_png']}")


if __name__ == "__main__":
    main()
