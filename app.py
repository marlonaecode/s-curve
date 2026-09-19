"""
app.py
Streamlit entry point for the S-Curve Progress Dashboard.

Run with:
    streamlit run app.py
"""

import streamlit as st
import pandas as pd
from pathlib import Path

import data_utils as du
import charts

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="S-Curve Dashboard",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Top gradient banner */
    [data-testid="stAppViewContainer"] > .main::before {
        content: "";
        display: block;
        height: 4px;
        background: linear-gradient(90deg, #4A90D9, #CE93D8, #E8834A);
        margin-bottom: 0;
    }

    /* Metric cards */
    div[data-testid="metric-container"] {
        background: #1E2433;
        border: 1px solid #2A2D3A;
        border-radius: 10px;
        padding: 14px 18px;
    }
    div[data-testid="metric-container"] label {
        font-size: 0.78rem !important;
        color: #9AA5B4 !important;
        text-transform: uppercase;
        letter-spacing: 0.06em;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: #0D1117;
        border-right: 1px solid #21262D;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

DEFAULT_CSV = Path(__file__).parent / "data" / "avance_muestra.csv"

# ─── SIDEBAR ─────────────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/fluency/96/combo-chart.png",
        width=72,
    )
    st.title("S-Curve Dashboard")
    st.caption("Análisis de avance de proyectos")
    st.divider()

    # Data source
    st.subheader("📂 Fuente de datos")
    data_mode = st.radio(
        "Seleccionar fuente",
        options=["Datos de muestra", "Cargar CSV propio"],
        index=0,
    )

    uploaded_file = None
    if data_mode == "Cargar CSV propio":
        uploaded_file = st.file_uploader(
            "Sube tu archivo CSV",
            type=["csv"],
            help="El CSV debe tener columnas: semana, avance_planificado, avance_real",
        )
        with st.expander("ℹ️ Formato esperado del CSV"):
            st.code(
                "semana,avance_planificado,avance_real\n"
                "1,0.5,0.3\n"
                "2,1.2,0.8\n"
                "...",
                language="text",
            )

    st.divider()

    # Chart visibility toggles
    st.subheader("📊 Gráficos a mostrar")
    show_scurve    = st.checkbox("Curva S Acumulada",    value=True)
    show_weekly    = st.checkbox("Avance Semanal",       value=True)
    show_variance  = st.checkbox("Variación vs Plan",    value=True)
    show_spi       = st.checkbox("Tendencia SPI",        value=True)

    st.divider()

    # Week filter
    st.subheader("🔎 Filtrar semanas")
    filter_weeks = st.checkbox("Aplicar filtro de rango", value=False)

    st.divider()
    st.caption("💡 El SPI (Schedule Performance Index) mide la eficiencia del cronograma. SPI > 1 indica adelanto.")

# ─── DATA LOADING ─────────────────────────────────────────────────────────────
try:
    if data_mode == "Datos de muestra":
        df_raw = du.load_csv(DEFAULT_CSV)
        st.sidebar.success("Datos de muestra cargados ✔")
    else:
        if uploaded_file is None:
            st.info("👈 Sube un archivo CSV en el panel lateral para comenzar.")
            st.stop()
        df_raw = du.load_csv(uploaded_file)
        st.sidebar.success("Archivo cargado correctamente ✔")
except ValueError as exc:
    st.sidebar.error(f"Error en el archivo: {exc}")
    st.stop()

# Week range filter
if filter_weeks:
    min_w = int(df_raw["semana"].min())
    max_w = int(df_raw["semana"].max())
    with st.sidebar:
        week_range = st.slider(
            "Rango de semanas",
            min_value=min_w,
            max_value=max_w,
            value=(min_w, max_w),
        )
    df = df_raw[
        (df_raw["semana"] >= week_range[0]) &
        (df_raw["semana"] <= week_range[1])
    ].copy()
else:
    df = df_raw.copy()

df_inc = du.compute_weekly_increments(df)
metrics = du.compute_metrics(df)

# ─── HEADER ───────────────────────────────────────────────────────────────────
st.markdown("## 📈 Dashboard de Curva S — Avance de Proyecto")
st.markdown(
    "Visualización del progreso planificado vs real, análisis de variación "
    "y tendencia del índice de desempeño del cronograma."
)

# ─── KPI METRICS ──────────────────────────────────────────────────────────────
st.markdown("### 🎯 Indicadores Clave")
col1, col2, col3, col4, col5 = st.columns(5)

var_color = "normal" if metrics["variacion"] >= 0 else "inverse"

col1.metric(
    "Semana actual",
    f"S{metrics['semana_actual']} / S{metrics['total_semanas']}",
)
col2.metric(
    "Avance planificado",
    f"{metrics['avance_planificado_actual']:.1f}%",
)
col3.metric(
    "Avance real",
    f"{metrics['avance_real_actual']:.1f}%",
    delta=f"{metrics['variacion']:+.1f}%",
    delta_color=var_color,
)
col4.metric(
    "SPI",
    f"{metrics['spi']:.2f}",
    delta="Adelanto" if metrics["spi"] >= 1 else "Retraso",
    delta_color="normal" if metrics["spi"] >= 1 else "inverse",
)
if metrics["proyeccion_fin"]:
    col5.metric(
        "Fin proyectado",
        f"Semana {metrics['proyeccion_fin']}",
        delta=f"{'−' if metrics['proyeccion_fin'] <= metrics['total_semanas'] else '+'}"
              f"{abs(metrics['proyeccion_fin'] - metrics['total_semanas'])} sem",
        delta_color=(
            "normal" if metrics["proyeccion_fin"] <= metrics["total_semanas"] else "inverse"
        ),
    )
else:
    col5.metric("Fin proyectado", "N/D")

st.divider()

# ─── CHARTS ───────────────────────────────────────────────────────────────────
st.markdown("### 📊 Análisis Gráfico")

if show_scurve:
    st.subheader("Curva S – Avance Acumulado")
    fig_s = charts.plot_scurve(df)
    st.pyplot(fig_s, use_container_width=True)
    st.caption(
        "La **Curva S** muestra el avance acumulado planificado vs real. "
        "La zona verde indica adelanto; la roja, retraso."
    )

col_left, col_right = st.columns(2) if (show_weekly or show_variance) else (None, None)

if show_weekly and col_left:
    with col_left:
        st.subheader("Avance Semanal Incremental")
        fig_w = charts.plot_weekly_increments(df_inc)
        st.pyplot(fig_w, use_container_width=True)
        st.caption("Avance semanal (no acumulado) planificado vs real.")

if show_variance and col_right:
    with col_right:
        st.subheader("Variación Acumulada vs Plan")
        fig_v = charts.plot_variance(df)
        st.pyplot(fig_v, use_container_width=True)
        st.caption("Diferencia entre avance real y planificado acumulado por semana.")

if show_spi:
    st.subheader("Tendencia del SPI")
    fig_spi = charts.plot_spi_trend(df)
    st.pyplot(fig_spi, use_container_width=True)
    st.caption(
        "**SPI = Avance Real / Avance Planificado**. "
        "SPI = 1.0 → en plan | SPI > 1.0 → adelantado | SPI < 1.0 → retrasado."
    )

# ─── RAW DATA TABLE ───────────────────────────────────────────────────────────
with st.expander("📋 Ver tabla de datos cargados"):
    st.dataframe(
        df.style.format(
            {
                "avance_planificado": "{:.1f}%",
                "avance_real": "{:.1f}%",
            }
        ),
        use_container_width=True,
        height=320,
    )
    csv_download = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Descargar datos actuales como CSV",
        data=csv_download,
        file_name="avance_filtrado.csv",
        mime="text/csv",
    )

# ─── FOOTER ───────────────────────────────────────────────────────────────────
st.divider()
st.caption("S-Curve Dashboard · Construido con Streamlit + Matplotlib · AECODE")
