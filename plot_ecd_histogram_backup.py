#!/usr/bin/env python3
"""Overlay ECD-A channel histograms from three .fcs files (publication quality)."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import readfcs
from matplotlib.ticker import LogLocator, NullFormatter
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
    "n_bins": 300,             # log-spaced bins across xlim
    "smooth_sigma": 1.5,       # gaussian smoothing width in bins (0 = off)
    "xlim": (1e-1, 1e6),
    # colors (one per entry in FILES, in order)
    "colors": ["#4C72B0", "#55A868", "#C44E52"],
    "fill_alpha": 0.25,
    "line_width": 1.2,
    # figure
    "figsize": (3.5, 2.8),     # inches (single-column width)
    "dpi": 300,                # png resolution
    # fonts
    "font_family": ["Arial", "Helvetica", "DejaVu Sans"],
    "font_size": 9,
    # axes
    "axes_linewidth": 1.0,
    "tick_size": 4,
    "tick_width": 1.0,
    "xlabel": "ECD-A fluorescence intensity",
    "ylabel": "Density",
    # output
    "out_pdf": "ECD-A_histogram.pdf",
    "out_png": "ECD-A_histogram.png",
}
# ---------------------------------------------------------------------------


def load_channel(path: Path, channel: str) -> np.ndarray:
    adata = readfcs.read(path)
    df = adata.to_df()
    if channel not in df.columns:
        raise KeyError(f"Channel '{channel}' not found in {path.name}. Available: {df.columns.tolist()}")
    return df[channel].to_numpy(dtype=float)


def main() -> None:
    s = SETTINGS

    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": s["font_family"],
        "font.size": s["font_size"],
        "axes.linewidth": s["axes_linewidth"],
        "axes.spines.top": False,
        "axes.spines.right": False,
        "xtick.direction": "out",
        "ytick.direction": "out",
        "xtick.major.size": s["tick_size"],
        "ytick.major.size": s["tick_size"],
        "xtick.minor.size": s["tick_size"] * 0.7,
        "xtick.major.width": s["tick_width"],
        "ytick.major.width": s["tick_width"],
        "xtick.minor.width": s["tick_width"] * 0.8,
        "xtick.minor.visible": True,
        "pdf.fonttype": 42,
        "ps.fonttype": 42,
    })

    data = {}
    for label, path in FILES.items():
        values = load_channel(path, s["channel"])
        values = values[values > s["min_value"]]  # log display: drop non-positive events
        data[label] = values

    log_bins = np.linspace(np.log10(s["xlim"][0]), np.log10(s["xlim"][1]), s["n_bins"] + 1)

    fig, ax = plt.subplots(figsize=s["figsize"])

    y_max = 0.0
    for (label, values), color in zip(data.items(), s["colors"]):
        counts, edges = np.histogram(np.log10(values), bins=log_bins, density=True)
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
    ax.set_ylabel(s["ylabel"])
    ax.margins(x=0)

    n_decades = int(np.log10(s["xlim"][1]) - np.log10(s["xlim"][0])) + 1
    ax.xaxis.set_major_locator(LogLocator(base=10.0, subs=(1.0,), numticks=n_decades + 2))
    ax.xaxis.set_minor_locator(LogLocator(base=10.0, subs=np.arange(2, 10) * 0.1, numticks=10 * n_decades))
    ax.xaxis.set_minor_formatter(NullFormatter())

    ax.legend(frameon=False, loc="upper left", handlelength=1.4)

    fig.tight_layout()
    fig.savefig(DATA_DIR / s["out_pdf"])
    fig.savefig(DATA_DIR / s["out_png"], dpi=s["dpi"])
    print(f"Saved {DATA_DIR / s['out_pdf']} and {s['out_png']}")


if __name__ == "__main__":
    main()
