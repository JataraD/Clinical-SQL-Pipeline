# ============================================================
# 02_create_database.py
# Creación de base de datos SQLite + carga de datos
# Autor: Juan David Atará Delgado
# Fecha: Mayo 2026
# ============================================================

import pandas as pd
import sqlite3
import os

# ── Cargar CSVs ──────────────────────────────────────────────
print("Cargando datos crudos...")
patients   = pd.read_csv('data/raw/patients.csv')
admissions = pd.read_csv('data/raw/admissions.csv')
labs       = pd.read_csv('data/raw/labs.csv')

# ── Crear base de datos ──────────────────────────────────────
os.makedirs('data/processed', exist_ok=True)
conn = sqlite3.connect('data/processed/clinical_db.sqlite')

# ── Cargar tablas ────────────────────────────────────────────
print("Cargando tablas en SQLite...")
patients.to_sql('patients',   conn, if_exists='replace', index=False)
admissions.to_sql('admissions', conn, if_exists='replace', index=False)
labs.to_sql('labs',           conn, if_exists='replace', index=False)

# ── Crear índices para performance ───────────────────────────
cursor = conn.cursor()

cursor.executescript("""
    CREATE INDEX IF NOT EXISTS idx_admissions_patient 
        ON admissions(patient_id);
    CREATE INDEX IF NOT EXISTS idx_labs_admission 
        ON labs(admission_id);
    CREATE INDEX IF NOT EXISTS idx_admissions_servicio 
        ON admissions(servicio);
    CREATE INDEX IF NOT EXISTS idx_admissions_fecha 
        ON admissions(fecha_ingreso);
""")

# ── Verificar carga ──────────────────────────────────────────
print("\n=== VERIFICACIÓN DE BASE DE DATOS ===")
for tabla in ['patients', 'admissions', 'labs']:
    n = pd.read_sql(f"SELECT COUNT(*) as n FROM {tabla}", conn).iloc[0,0]
    print(f"  {tabla:15s}: {n:,} registros")

# ── Queries de validación ────────────────────────────────────
print("\n=== QUERIES DE VALIDACIÓN ===")

# Query 1: Distribución por servicio
q1 = pd.read_sql("""
    SELECT 
        servicio,
        COUNT(*)              AS total_admisiones,
        ROUND(AVG(dias_estancia), 1) AS estancia_promedio,
        ROUND(AVG(costo_cop)/1000000, 2) AS costo_promedio_MM
    FROM admissions
    GROUP BY servicio
    ORDER BY total_admisiones DESC
""", conn)
print("\nDistribución por servicio:")
print(q1.to_string(index=False))

# Query 2: Tasa de readmisión por EPS
q2 = pd.read_sql("""
    SELECT 
        p.eps,
        COUNT(a.admission_id)                    AS total_admisiones,
        SUM(a.readmision)                        AS readmisiones,
        ROUND(SUM(a.readmision)*100.0/COUNT(*),1) AS tasa_readmision_pct
    FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
    GROUP BY p.eps
    ORDER BY tasa_readmision_pct DESC
""", conn)
print("\nTasa de readmisión por EPS:")
print(q2.to_string(index=False))

# Query 3: Top diagnósticos con mayor costo
q3 = pd.read_sql("""
    SELECT 
        p.diagnostico_principal,
        COUNT(a.admission_id)              AS admisiones,
        ROUND(AVG(a.dias_estancia), 1)     AS estancia_promedio,
        ROUND(SUM(a.costo_cop)/1000000, 1) AS costo_total_MM
    FROM admissions a
    JOIN patients p ON a.patient_id = p.patient_id
    GROUP BY p.diagnostico_principal
    ORDER BY costo_total_MM DESC
    LIMIT 5
""", conn)
print("\nTop 5 diagnósticos por costo total:")
print(q3.to_string(index=False))

# Query 4: Resultados anormales por examen
q4 = pd.read_sql("""
    SELECT 
        examen,
        COUNT(*)                              AS total_resultados,
        SUM(anormal)                          AS resultados_anormales,
        ROUND(SUM(anormal)*100.0/COUNT(*), 1) AS pct_anormal
    FROM labs
    GROUP BY examen
    ORDER BY pct_anormal DESC
""", conn)
print("\nTasa de resultados anormales por examen:")
print(q4.to_string(index=False))

conn.close()
print("\n✅ Base de datos creada: data/processed/clinical_db.sqlite")