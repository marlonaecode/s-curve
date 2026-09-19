"""
charts.py
All matplotlib chart generation logic for S-curve analysis.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from matplotlib.figure import Figure

# ─── Style constants ─────────────────────────────────────────────────────────
COLOR_PLANNED = "#4A90D9"
COLOR_ACTUAL  = "#E8834A"
COLOR_FILL_POS = "#C8E6C9"   # ahead of plan (green tint)
COLOR_FILL_NEG = "#FFCDD2"   # behind plan (red tint)
COLOR_BAR_PLAN = "#90CAF9"
COLOR_BAR_REAL = "#FFAB76"
BG_COLOR       = "#0E1117"   # matches Streamlit dark theme
TEXT_COLOR      = "#FAFAFA"
GRID_COLOR      = "#2A2D3A"
FONT_FAMILY     = "DejaVu Sans"

STYLE = {
    "figure.facecolor":  BG_COLOR,
    "axes.facecolor":    "#161B27",
    "axes.edgecolor":    GRID_COLOR,
    "axes.labelcolor":   TEXT_COLOR,
    "axes.titlecolor":   TEXT_COLOR,
    "xtick.color":       TEXT_COLOR,
    "ytick.color":       TEXT_COLOR,
    "grid.color":        GRID_COLOR,
    "grid.alpha":        0.5,
    "text.color":        TEXT_COLOR,
    "legend.facecolor":  "#1E2433",
    "legend.edgecolor":  GRID_COLOR,
    "font.family":       FONT_FAMILY,
}


def _apply_style() -> None:
    plt.rcParams.update(STYLE)


# ─── Chart 1: S-Curve (cumulative) ───────────────────────────────────────────

def plot_scurve(df: pd.DataFrame, title: str = "Curva S – Avance Acumulado") -> Figure:
    """
    Classic S-curve: cumulative planned vs actual progress over time.
    Fills the gap between curves to highlight advance or delay.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 5))

    weeks = df["semana"].values
    planned = df["avance_planificado"].values
    actual  = df["avance_real"].values

    # Shaded area between curves
    ax.fill_between(
        weeks, planned, actual,
        where=(actual >= planned), interpolate=True,
        color=COLOR_FILL_POS, alpha=0.4, label="Adelanto"
    )
    ax.fill_between(
        weeks, planned, actual,
        where=(actual < planned), interpolate=True,
        color=COLOR_FILL_NEG, alpha=0.4, label="Retraso"
    )

    # Main curves
    ax.plot(weeks, planned, color=COLOR_PLANNED, linewidth=2.5,
            marker="o", markersize=3.5, label="Planificado", zorder=3)
    ax.plot(weeks, actual, color=COLOR_ACTUAL, linewidth=2.5,
            marker="s", markersize=3.5, label="Real", zorder=3)

    # Highlight last real data point
    last_idx = np.where(actual > 0)[0]
    if len(last_idx):
        lx, ly = weeks[last_idx[-1]], actual[last_idx[-1]]
        ax.annotate(
            f"{ly:.1f}%",
            xy=(lx, ly), xytext=(lx + 0.6, ly + 3),
            color=COLOR_ACTUAL, fontsize=9, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=COLOR_ACTUAL, lw=1.2),
        )

    ax.set_title(title, fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Semana", fontsize=11)
    ax.set_ylabel("Avance Acumulado (%)", fontsize=11)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=100))
    ax.set_xlim(weeks[0] - 0.5, weeks[-1] + 0.5)
    ax.set_ylim(-2, 105)
    ax.grid(True, linestyle="--", linewidth=0.6)
    ax.legend(fontsize=10, loc="upper left")

    fig.tight_layout()
    return fig


# ─── Chart 2: Weekly incremental bar chart ────────────────────────────────────

def plot_weekly_increments(df_inc: pd.DataFrame,
                            title: str = "Avance Semanal (Incremental)") -> Figure:
    """
    Grouped bar chart showing weekly incremental planned vs actual progress.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 4))

    weeks = df_inc["semana"].values
    inc_plan = df_inc["inc_planificado"].values
    inc_real = df_inc["inc_real"].values

    x = np.arange(len(weeks))
    width = 0.4

    bars_plan = ax.bar(x - width / 2, inc_plan, width, color=COLOR_BAR_PLAN,
                        label="Planificado", alpha=0.9, zorder=3)
    bars_real = ax.bar(x + width / 2, inc_real, width, color=COLOR_BAR_REAL,
                        label="Real", alpha=0.9, zorder=3)

    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Semana", fontsize=10)
    ax.set_ylabel("Incremento (%)", fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(weeks, fontsize=8, rotation=45)
    ax.grid(axis="y", linestyle="--", linewidth=0.6)
    ax.legend(fontsize=10)

    fig.tight_layout()
    return fig


# ─── Chart 3: Variance bar chart ─────────────────────────────────────────────

def plot_variance(df: pd.DataFrame,
                  title: str = "Variación Semanal (Real – Planificado)") -> Figure:
    """
    Bar chart of the weekly variance (actual minus planned, cumulative).
    Bars are colored green when ahead, red when behind.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 4))

    weeks    = df["semana"].values
    variance = df["avance_real"].values - df["avance_planificado"].values
    colors   = [COLOR_FILL_POS.replace("C8", "66").replace("E6", "BB").replace("C9", "88")
                if v >= 0 else "#EF9A9A" for v in variance]
    colors_solid = ["#66BB6A" if v >= 0 else "#EF5350" for v in variance]

    ax.bar(weeks, variance, color=colors_solid, alpha=0.85, zorder=3, edgecolor=GRID_COLOR)
    ax.axhline(0, color=TEXT_COLOR, linewidth=1.0, linestyle="-")

    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Semana", fontsize=10)
    ax.set_ylabel("Variación (%)", fontsize=10)
    ax.grid(axis="y", linestyle="--", linewidth=0.6)

    # Legend patches
    ahead_patch  = mpatches.Patch(color="#66BB6A", label="Adelanto")
    behind_patch = mpatches.Patch(color="#EF5350", label="Retraso")
    ax.legend(handles=[ahead_patch, behind_patch], fontsize=10)

    fig.tight_layout()
    return fig


# ─── Chart 4: SPI trend ──────────────────────────────────────────────────────

def plot_spi_trend(df: pd.DataFrame,
                   title: str = "Tendencia del SPI (Schedule Performance Index)") -> Figure:
    """
    Line chart of the weekly Schedule Performance Index (actual / planned).
    SPI = 1.0 is the baseline; above = ahead, below = behind.
    """
    _apply_style()
    fig, ax = plt.subplots(figsize=(10, 4))

    weeks   = df["semana"].values
    planned = df["avance_planificado"].values
    actual  = df["avance_real"].values

    with np.errstate(divide="ignore", invalid="ignore"):
        spi = np.where(planned > 0, actual / planned, np.nan)

    ax.plot(weeks, spi, color="#CE93D8", linewidth=2.5,
            marker="D", markersize=4, label="SPI", zorder=3)
    ax.axhline(1.0, color="#80DEEA", linewidth=1.5,
               linestyle="--", label="SPI = 1.0 (en plan)")
    ax.fill_between(weeks, spi, 1.0,
                    where=(spi >= 1.0), interpolate=True,
                    color="#66BB6A", alpha=0.25, label="Adelanto")
    ax.fill_between(weeks, spi, 1.0,
                    where=(spi < 1.0), interpolate=True,
                    color="#EF5350", alpha=0.2, label="Retraso")

    ax.set_title(title, fontsize=13, fontweight="bold", pad=10)
    ax.set_xlabel("Semana", fontsize=10)
    ax.set_ylabel("SPI", fontsize=10)
    ax.set_ylim(0, max(2.0, float(np.nanmax(spi)) + 0.2))
    ax.grid(True, linestyle="--", linewidth=0.6)
    ax.legend(fontsize=10, loc="lower right")

    fig.tight_layout()
    return fig
