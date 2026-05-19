# ============================================================
# app.py
# Clinical Data Dashboard — IPS Colombia
# Autor: Juan David Atará Delgado
# Fecha: Mayo 2026
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px
import plotly.graph_objects as go

# ── Configuración ────────────────────────────────────────────
st.set_page_config(
    page_title = "Clinical Data Dashboard",
    page_icon  = "🏥",
    layout     = "wide"
)

# ── Conexión DB ──────────────────────────────────────────────
@st.cache_data
def load_data():
    conn = sqlite3.connect('data/processed/clinical_db.sqlite')
    kpi_servicio    = pd.read_csv('data/processed/kpi_servicio.csv')
    kpi_diagnostico = pd.read_csv('data/processed/kpi_diagnostico.csv')
    kpi_tendencia   = pd.read_csv('data/processed/kpi_tendencia.csv')
    kpi_riesgo      = pd.read_csv('data/processed/kpi_riesgo_pacientes.csv')

    admissions = pd.read_sql("SELECT * FROM admissions", conn)
    patients   = pd.read_sql("SELECT * FROM patients",   conn)
    conn.close()
    return kpi_servicio, kpi_diagnostico, kpi_tendencia, kpi_riesgo, admissions, patients

kpi_srv, kpi_dx, kpi_trend, kpi_risk, adm, pat = load_data()

# ── Header ───────────────────────────────────────────────────
st.title("🏥 Clinical Data Dashboard")
st.markdown("**IPS Colombia — Análisis de KPIs Clínicos y Operativos** | Pipeline SQL + ETL + Python")
st.divider()

# ── KPIs principales ─────────────────────────────────────────
col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Admisiones",  f"{len(adm):,}")
col2.metric("Pacientes Únicos",  f"{adm['patient_id'].nunique():,}")
col3.metric("Estancia Promedio", f"{adm['dias_estancia'].mean():.1f} días")
col4.metric("Costo Promedio",    f"${adm['costo_cop'].mean()/1e6:.1f}M COP")
col5.metric("Tasa Readmisión",   f"{adm['readmision'].mean()*100:.1f}%")

st.divider()

# ── Tabs ─────────────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "📊 Servicios", "🔬 Diagnósticos", "📈 Tendencia", "⚠️ Riesgo"
])

# ── Tab 1: Servicios ─────────────────────────────────────────
with tab1:
    st.subheader("Eficiencia Operativa por Servicio")
    c1, c2 = st.columns(2)

    with c1:
        fig = px.bar(kpi_srv, x='servicio', y='total_admisiones',
                     color='mortalidad_pct',
                     color_continuous_scale='RdYlGn_r',
                     title='Admisiones y Mortalidad por Servicio',
                     labels={'total_admisiones':'Admisiones',
                             'mortalidad_pct':'Mortalidad %'})
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    with c2:
        fig2 = px.scatter(kpi_srv,
                          x='estancia_promedio', y='costo_promedio',
                          size='total_admisiones', color='servicio',
                          title='Estancia vs. Costo Promedio',
                          labels={'estancia_promedio':'Estancia (días)',
                                  'costo_promedio':'Costo Promedio (COP)'})
        st.plotly_chart(fig2, use_container_width=True)

    st.dataframe(kpi_srv.style.format({
        'costo_promedio'  : '${:,.0f}',
        'costo_total_MM'  : '${:.1f}M',
        'mortalidad_pct'  : '{:.1f}%',
        'estancia_promedio': '{:.1f}'
    }), use_container_width=True)

# ── Tab 2: Diagnósticos ──────────────────────────────────────
with tab2:
    st.subheader("Perfil Clínico por Diagnóstico")
    c1, c2 = st.columns(2)

    with c1:
        fig3 = px.bar(kpi_dx.sort_values('costo_total_MM', ascending=True),
                      x='costo_total_MM', y='diagnostico_principal',
                      orientation='h', color='tasa_readmision_pct',
                      color_continuous_scale='Reds',
                      title='Costo Total por Diagnóstico (MM COP)',
                      labels={'costo_total_MM':'Costo Total (MM COP)',
                              'tasa_readmision_pct':'Readmisión %'})
        st.plotly_chart(fig3, use_container_width=True)

    with c2:
        fig4 = px.scatter(kpi_dx,
                          x='edad_promedio', y='tasa_readmision_pct',
                          size='total_admisiones', color='diagnostico_principal',
                          title='Edad Promedio vs. Tasa de Readmisión',
                          labels={'edad_promedio':'Edad Promedio',
                                  'tasa_readmision_pct':'Readmisión %'})
        fig4.update_layout(showlegend=False)
        st.plotly_chart(fig4, use_container_width=True)

# ── Tab 3: Tendencia ─────────────────────────────────────────
with tab3:
    st.subheader("Tendencia Mensual de Admisiones")

    fig5 = px.line(kpi_trend, x='mes', y='admisiones',
                   title='Admisiones Mensuales',
                   markers=True,
                   labels={'mes':'Mes', 'admisiones':'Admisiones'})
    fig5.update_traces(line_color='#2196F3', line_width=2)
    st.plotly_chart(fig5, use_container_width=True)

    c1, c2 = st.columns(2)
    with c1:
        fig6 = px.bar(kpi_trend, x='mes', y='readmisiones',
                      title='Readmisiones Mensuales',
                      color='readmisiones',
                      color_continuous_scale='Reds')
        st.plotly_chart(fig6, use_container_width=True)

    with c2:
        fig7 = px.line(kpi_trend, x='mes', y='costo_promedio_MM',
                       title='Costo Promedio Mensual (MM COP)',
                       markers=True)
        fig7.update_traces(line_color='#4CAF50', line_width=2)
        st.plotly_chart(fig7, use_container_width=True)

# ── Tab 4: Riesgo ────────────────────────────────────────────
with tab4:
    st.subheader("⚠️ Pacientes de Alto Riesgo")
    st.markdown("Risk score calculado con base en readmisiones, estancia y edad.")

    fig8 = px.bar(kpi_risk.sort_values('risk_score', ascending=True),
                  x='risk_score', y='patient_id',
                  orientation='h', color='risk_score',
                  color_continuous_scale='RdYlGn_r',
                  title='Top 20 Pacientes por Risk Score',
                  hover_data=['edad', 'diagnostico_principal',
                              'total_readmisiones'],
                  labels={'risk_score':'Risk Score', 'patient_id':'Paciente'})
    fig8.update_layout(height=600)
    st.plotly_chart(fig8, use_container_width=True)

    st.dataframe(kpi_risk[[
        'patient_id','edad','diagnostico_principal',
        'total_admisiones','total_readmisiones',
        'estancia_promedio','costo_total_MM','risk_score'
    ]].style.background_gradient(subset=['risk_score'], cmap='RdYlGn_r'),
    use_container_width=True)

# ── Footer ───────────────────────────────────────────────────
st.divider()
st.caption("Pipeline: SQL (SQLite) + Python (Pandas) + Streamlit + Plotly | "
           "Datos clínicos simulados | Juan David Atará Delgado — 2026")