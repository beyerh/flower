#!/usr/bin/env python3
"""Overlay flow cytometry histograms from several .fcs files (publication quality).

Batch/reproducible entry point. Every option lives in the two blocks below;
the rendering itself is shared with the GUI (see flow_core.py).
Interactive alternative:  python3 flower.py
"""

from flow_core import (DATA_DIR, channel_values, merge_settings, read_fcs,
                        save_figure, save_statistics)

# --------------------------------------------------------------- samples --
# label -> (file, colour). Order defines the drawing and legend order.
SAMPLES = [
    ("HeLa WT", DATA_DIR / "03-HeLA WT-C1.fcs", "#4C72B0"),
    ("pMLM049 clone 6 Dark", DATA_DIR / "03-HeLa pMLM049 clone 6 Dark-B4.fcs", "#55A868"),
    ("pMLM049 clone 6 Light", DATA_DIR / "03-HeLa pMLM049 clone 6 Light-B3.fcs", "#C44E52"),
]

# Per-sample scatter gates: {sample_index: gate_dict}.
# Per-sample histogram gates: {sample_index: gate_dict}.
# Per-sample analysis gates: {sample_index: gate_dict}.
# Copy the dicts printed by the GUI's save button here to reproduce gates.
SCATTER_GATES = {}
HIST_GATES = {}
ANALYSIS_GATES = {}
# SCATTER_GATES = {0: {"type": "polygon", "x": "FSC-A", "y": "SSC-A",
#         "verts": [[5e4, 3e4], [6e5, 3e4], [6e5, 5e5], [5e4, 5e5]]}}

# -------------------------------------------------------------- settings --
# Only list what differs from flow_core.DEFAULTS; see that file for all keys
# and an explanation of each one.
SETTINGS = merge_settings({
    "channel": "ECD-A",
    "y_axis": "counts",          # density | counts | percent_of_max
    "n_bins": 500,
    "smooth_sigma": 1.5,
    "xlim_lo": 1e-1,
    "xlim_hi": 1e6,
    "fig_w": 3.0,
    "fig_h": 3.0,
    "dpi": 600,
})
# --------------------------------------------------------------------------


def main():
    series = []
    samples_info = []
    for i, (label, path, color) in enumerate(SAMPLES):
        df = read_fcs(path)
        sg = SCATTER_GATES.get(i)
        hg = HIST_GATES.get(i)
        ag = ANALYSIS_GATES.get(i)
        values = channel_values(df, SETTINGS, sg, hg, ag)
        if sg or hg or ag:
            print(f"{label}: {values.size}/{len(df)} events kept "
                  f"({100 * values.size / len(df):.1f}%)")
        series.append({"label": label, "color": color, "values": values,
                       "hist_gate": hg})
        samples_info.append({"label": label, "color": color, "df": df,
                             "scatter_gate": sg, "hist_gate": hg,
                             "analysis_gate": ag})

    pdf, png = save_figure(series, SETTINGS)
    print(f"Saved {pdf} and {png}")
    xlsx = save_statistics(samples_info, SETTINGS)
    if xlsx:
        print(f"Saved {xlsx}")


if __name__ == "__main__":
    main()
