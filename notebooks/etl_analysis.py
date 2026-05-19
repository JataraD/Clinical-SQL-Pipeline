# ============================================================
# 03_etl_analysis.py
# Pipeline ETL + Análisis de KPIs clínicos
# Autor: Juan David Atará Delgado
# Fecha: Mayo 2026
# ============================================================

import pandas as pd
import sqlite3
import os

conn = sqlite3.connect('data/processed/clinical_db.sqlite')
os.makedirs('data/processed', exist_ok=True)

print("=== PIPELINE ETL — CLINICAL DATA ===\n")

# ── KPI 1: Ocupación y eficiencia por servicio ───────────────
kpi_servicio = pd.read_sql("""
    SELECT
        servicio,
        COUNT(*)                               AS total_admisiones,
        ROUND(AVG(dias_estancia), 2)           AS estancia_promedio,
        ROUND(AVG(costo_cop), 0)               AS costo_promedio,
        SUM(CASE WHEN estado_egreso = 'Fallecido' 
            THEN 1 ELSE 0 END)                 AS fallecidos,
        ROUND(SUM(CASE WHEN estado_egreso = 'Fallecido'
            THEN 1 ELSE 0 END) * 100.0 
            / COUNT(*), 2)                     AS mortalidad_pct,
        ROUND(SUM(costo_cop) / 1000000, 1)     AS costo_total_MM
    FROM admissions
    GROUP BY servicio
    ORDER BY total_admisiones DESC
""", conn)

kpi_servicio.to_csv('data/processed/kpi_servicio.csv', index=False)
print("✅ KPI 1 — Eficiencia por servicio")
print(kpi_servicio.to_string(index=False))

# ── KPI 2: Perfil de pacientes por diagnóstico ───────────────
kpi_diagnostico = pd.read_sql("""
    SELECT
        p.diagnostico_principal,
        COUNT(DISTINCT p.patient_id)           AS pacientes_unicos,
        COUNT(a.admission_id)                  AS total_admisiones,
        ROUND(AVG(p.edad), 1)                  AS edad_promedio,
        ROUND(AVG(a.dias_estancia), 1)         AS estancia_promedio,
        ROUND(SUM(a.readmision) * 100.0 
            / COUNT(*), 1)                     AS tasa_readmision_pct,
        ROUND(SUM(a.costo_cop) / 1000000, 1)   AS costo_total_MM
    FROM patients p
    JOIN admissions a ON p.patient_id = a.patient_id
    GROUP BY p.diagnostico_principal
    ORDER BY costo_total_MM DESC
""", conn)

kpi_diagnostico.to_csv('data/processed/kpi_diagnostico.csv', index=False)
print("\n✅ KPI 2 — Perfil por diagnóstico")
print(kpi_diagnostico.to_string(index=False))

# ── KPI 3: Calidad de datos ──────────────────────────────────
print("\n✅ KPI 3 — Calidad de datos")

calidad = pd.read_sql("""
    SELECT
        'patients'   AS tabla,
        COUNT(*)     AS total_registros,
        SUM(CASE WHEN patient_id IS NULL THEN 1 ELSE 0 END) AS nulos_id,
        SUM(CASE WHEN edad < 0 OR edad > 120 THEN 1 ELSE 0 END) AS edad_invalida
    FROM patients
    UNION ALL
    SELECT
        'admissions',
        COUNT(*),
        SUM(CASE WHEN admission_id IS NULL THEN 1 ELSE 0 END),
        SUM(CASE WHEN dias_estancia < 0 THEN 1 ELSE 0 END)
    FROM admissions
    UNION ALL
    SELECT
        'labs',
        COUNT(*),
        SUM(CASE WHEN lab_id IS NULL THEN 1 ELSE 0 END),
        SUM(CASE WHEN valor < 0 THEN 1 ELSE 0 END)
    FROM labs
""", conn)

calidad['completitud_pct'] = 100 - (calidad['nulos_id'] / calidad['total_registros'] * 100)
print(calidad.to_string(index=False))

calidad.to_csv('data/processed/kpi_calidad.csv', index=False)

# ── KPI 4: Tendencia mensual de admisiones ───────────────────
kpi_tendencia = pd.read_sql("""
    SELECT
        SUBSTR(fecha_ingreso, 1, 7)            AS mes,
        COUNT(*)                               AS admisiones,
        ROUND(AVG(costo_cop) / 1000000, 2)     AS costo_promedio_MM,
        SUM(readmision)                        AS readmisiones,
        ROUND(AVG(dias_estancia), 1)           AS estancia_promedio
    FROM admissions
    GROUP BY SUBSTR(fecha_ingreso, 1, 7)
    ORDER BY mes
""", conn)

kpi_tendencia.to_csv('data/processed/kpi_tendencia.csv', index=False)
print(f"\n✅ KPI 4 — Tendencia mensual ({len(kpi_tendencia)} meses de datos)")

# ── KPI 5: Score de riesgo por paciente ─────────────────────
kpi_riesgo = pd.read_sql("""
    SELECT
        p.patient_id,
        p.edad,
        p.diagnostico_principal,
        p.eps,
        COUNT(a.admission_id)                  AS total_admisiones,
        SUM(a.readmision)                      AS total_readmisiones,
        ROUND(AVG(a.dias_estancia), 1)         AS estancia_promedio,
        ROUND(SUM(a.costo_cop) / 1000000, 2)   AS costo_total_MM,
        -- Score de riesgo simple
        ROUND(
            (SUM(a.readmision) * 3) +
            (AVG(a.dias_estancia) * 0.5) +
            (p.edad * 0.1)
        , 1)                                   AS risk_score
    FROM patients p
    JOIN admissions a ON p.patient_id = a.patient_id
    GROUP BY p.patient_id
    ORDER BY risk_score DESC
    LIMIT 20
""", conn)

kpi_riesgo.to_csv('data/processed/kpi_riesgo_pacientes.csv', index=False)
print(f"\n✅ KPI 5 — Top 20 pacientes por risk score")
print(kpi_riesgo[['patient_id','edad','diagnostico_principal',
                   'total_readmisiones','risk_score']].to_string(index=False))

conn.close()
print("\n✅ ETL completado — todos los KPIs guardados en data/processed/")