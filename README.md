# Flower

Interactive flow cytometry analysis in the browser. Overlay histograms, gate live cells on FSC/SSC scatter plots, draw additional gates on analysis scatter plots, and export publication-quality figures and statistics — all without installing a native GUI toolkit.

## Quick start

```bash
pip install numpy matplotlib seaborn scipy readfcs openpyxl
```

Drop your `.fcs` files into the project folder (or browse/upload via the GUI), then:

```bash
python3 flower.py
```

Flower opens automatically in your browser. Press `Ctrl+C` in the terminal to stop.

## Requirements

| Package    | Purpose                                      |
|------------|----------------------------------------------|
| numpy      | Numerical operations, histogram binning      |
| matplotlib | Publication-quality figure rendering (PDF/PNG)|
| seaborn    | Plot styling and despine                     |
| scipy      | Gaussian smoothing of histogram curves       |
| readfcs    | Reading `.fcs` flow cytometry files          |
| openpyxl   | Writing XLSX statistics files                |

Install all at once:

```bash
pip install numpy matplotlib seaborn scipy readfcs openpyxl
```

## Features

- **Three linked plots**: gating scatter (FSC/SSC), histogram, and analysis scatter
- **Interactive gating**: polygon and quadrant gates on scatter plots, interval gates on histograms
- **Gate chain**: gating scatter → histogram interval → analysis scatter (applied sequentially)
- **Per-sample gates**: each sample remembers its own gates independently
- **Channel selection by clicking axis labels**: click the X or Y axis label below/beside any plot to pick a channel from a dropdown
- **Publication-quality output**: Arial font, mathtext superscripts, 600 dpi PNG, vector PDF
- **XLSX statistics**: per-sample counts, mean, median, std, percentiles, geometric mean for ungated and each gating stage
- **Reproducible snippets**: the GUI generates a Python snippet to paste into the CLI script

## CLI usage (batch / reproducible)

```bash
python3 plot_ecd_histogram.py
```

Edit `SAMPLES`, `SCATTER_GATES`, `HIST_GATES`, `ANALYSIS_GATES`, and `SETTINGS` at the top of `plot_ecd_histogram.py` to reproduce figures without the GUI.

## File overview

| File                    | Role                                              |
|-------------------------|---------------------------------------------------|
| `flower.py`             | Browser GUI server (start here)                   |
| `gui_page.py`           | HTML/CSS/JS frontend served by `flower.py`        |
| `flow_core.py`          | Core engine: schema, FCS loader, gating, rendering|
| `plot_ecd_histogram.py` | CLI script for batch/reproducible plotting        |
