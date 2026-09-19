"""
data_utils.py
Handles CSV loading, validation, and derived metric calculations.
"""

import pandas as pd
import numpy as np
from pathlib import Path


REQUIRED_COLUMNS = {"semana", "avance_planificado", "avance_real"}


def load_csv(file_source) -> pd.DataFrame:
    """
    Load a CSV from a file path (str/Path) or a file-like object (Streamlit UploadedFile).
    Returns a cleaned, validated DataFrame.
    """
    if isinstance(file_source, (str, Path)):
        df = pd.read_csv(file_source)
    else:
        df = pd.read_csv(file_source)

    df.columns = df.columns.str.strip().str.lower()
    _validate(df)
    df = df.sort_values("semana").reset_index(drop=True)
    return df


def _validate(df: pd.DataFrame) -> None:
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            f"El CSV no contiene las columnas requeridas: {missing}. "
            f"Columnas encontradas: {list(df.columns)}"
        )
    if df["semana"].duplicated().any():
        raise ValueError("Existen semanas duplicadas en el archivo CSV.")
    if not pd.api.types.is_numeric_dtype(df["avance_planificado"]):
        raise ValueError("La columna 'avance_planificado' debe ser numérica.")
    if not pd.api.types.is_numeric_dtype(df["avance_real"]):
        raise ValueError("La columna 'avance_real' debe ser numérica.")


def compute_metrics(df: pd.DataFrame) -> dict:
    """
    Returns a dict of summary KPIs derived from the progress data.
    """
    last = df.iloc[-1]
    current = df[df["avance_real"] > 0].iloc[-1] if (df["avance_real"] > 0).any() else df.iloc[0]

    planned_at_current_week = df.loc[
        df["semana"] == current["semana"], "avance_planificado"
    ].values[0]

    variance = float(current["avance_real"]) - float(planned_at_current_week)
    spi = float(current["avance_real"]) / float(planned_at_current_week) if planned_at_current_week else 0

    total_weeks = int(df["semana"].max())
    reported_weeks = int((df["avance_real"] > 0).sum())

    # Simple linear projection of completion week
    if spi > 0:
        projected_completion_week = int(np.ceil(total_weeks / spi))
    else:
        projected_completion_week = None

    return {
        "avance_planificado_actual": float(planned_at_current_week),
        "avance_real_actual": float(current["avance_real"]),
        "variacion": variance,
        "spi": spi,
        "semana_actual": int(current["semana"]),
        "total_semanas": total_weeks,
        "semanas_reportadas": reported_weeks,
        "proyeccion_fin": projected_completion_week,
    }


def compute_weekly_increments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes weekly incremental progress (delta) for both planned and actual.
    """
    out = df.copy()
    out["inc_planificado"] = out["avance_planificado"].diff().fillna(out["avance_planificado"].iloc[0])
    out["inc_real"] = out["avance_real"].diff().fillna(out["avance_real"].iloc[0])
    return out
