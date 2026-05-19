# ============================================================
# 01_generate_data.py
# Generación de dataset clínico simulado — IPS Colombia
# Autor: Juan David Atará Delgado
# Fecha: Mayo 2026
# ============================================================

import pandas as pd
import numpy as np
from faker import Faker
import random
import os

fake = Faker('es_CO')
np.random.seed(42)
random.seed(42)

N_PATIENTS    = 500
N_ADMISSIONS  = 1200
N_LABS        = 3500

# ── Tabla 1: Pacientes ───────────────────────────────────────
print("Generando tabla de pacientes...")

diagnosticos = [
    'Hipertensión arterial', 'Diabetes mellitus tipo 2',
    'Insuficiencia cardíaca', 'EPOC', 'Neumonía',
    'Infección urinaria', 'Fractura de cadera',
    'ACV isquémico', 'Sepsis', 'Cáncer de mama'
]

eps_list = ['Sura', 'Sanitas', 'Compensar', 'Nueva EPS', 'Famisanar']
regimen  = ['Contributivo', 'Subsidiado']

patients = pd.DataFrame({
    'patient_id'  : [f'PAC{str(i).zfill(4)}' for i in range(1, N_PATIENTS+1)],
    'nombre'      : [fake.first_name() for _ in range(N_PATIENTS)],
    'apellido'    : [fake.last_name()  for _ in range(N_PATIENTS)],
    'edad'        : np.random.randint(18, 90, N_PATIENTS),
    'sexo'        : np.random.choice(['M', 'F'], N_PATIENTS),
    'ciudad'      : np.random.choice(['Bogotá','Medellín','Cali','Barranquilla','Bucaramanga'], N_PATIENTS),
    'eps'         : np.random.choice(eps_list, N_PATIENTS),
    'regimen'     : np.random.choice(regimen, N_PATIENTS, p=[0.65, 0.35]),
    'diagnostico_principal': np.random.choice(diagnosticos, N_PATIENTS),
})

# ── Tabla 2: Admisiones ──────────────────────────────────────
print("Generando tabla de admisiones...")

servicios = ['Urgencias', 'Hospitalización', 'UCI', 'Cirugía', 'Consulta externa']
estados   = ['Alta', 'Traslado', 'Fallecido', 'En curso']

admissions = []
for i in range(N_ADMISSIONS):
    pid          = random.choice(patients['patient_id'].tolist())
    fecha_ingreso = fake.date_between(start_date='-2y', end_date='today')
    estancia      = np.random.randint(1, 30)
    fecha_egreso  = pd.Timestamp(fecha_ingreso) + pd.Timedelta(days=int(estancia))
    servicio      = random.choice(servicios)
    costo_base    = {'Urgencias':500000, 'Hospitalización':1200000,
                     'UCI':4500000, 'Cirugía':3200000, 'Consulta externa':150000}
    costo         = costo_base[servicio] * estancia * np.random.uniform(0.8, 1.4)

    admissions.append({
        'admission_id' : f'ADM{str(i+1).zfill(5)}',
        'patient_id'   : pid,
        'fecha_ingreso': fecha_ingreso,
        'fecha_egreso' : fecha_egreso.date(),
        'dias_estancia': estancia,
        'servicio'     : servicio,
        'estado_egreso': np.random.choice(estados, p=[0.75, 0.12, 0.05, 0.08]),
        'costo_cop'    : round(costo, 0),
        'readmision'   : np.random.choice([0, 1], p=[0.85, 0.15]),
    })

admissions_df = pd.DataFrame(admissions)

# ── Tabla 3: Resultados de laboratorio ──────────────────────
print("Generando tabla de laboratorios...")

examenes = {
    'Hemoglobina'    : (12.0, 17.5, 'g/dL'),
    'Glucosa'        : (70,   200,  'mg/dL'),
    'Creatinina'     : (0.5,  3.5,  'mg/dL'),
    'Sodio'          : (130,  150,  'mEq/L'),
    'Potasio'        : (3.0,  6.0,  'mEq/L'),
    'PCR'            : (0,    150,  'mg/L'),
    'Leucocitos'     : (3000, 20000,'cel/µL'),
}

labs = []
for i in range(N_LABS):
    adm      = random.choice(admissions_df['admission_id'].tolist())
    examen   = random.choice(list(examenes.keys()))
    rng      = examenes[examen]
    valor    = round(np.random.uniform(rng[0], rng[1]), 2)
    # Valores de referencia
    ref_min  = rng[0] + (rng[1]-rng[0])*0.15
    ref_max  = rng[1] - (rng[1]-rng[0])*0.15
    anormal  = 1 if (valor < ref_min or valor > ref_max) else 0

    labs.append({
        'lab_id'      : f'LAB{str(i+1).zfill(6)}',
        'admission_id': adm,
        'examen'      : examen,
        'valor'       : valor,
        'unidad'      : rng[2],
        'anormal'     : anormal,
        'fecha'       : fake.date_between(start_date='-2y', end_date='today'),
    })

labs_df = pd.DataFrame(labs)

# ── Guardar CSV ──────────────────────────────────────────────
os.makedirs('data/raw', exist_ok=True)
patients.to_csv('data/raw/patients.csv',    index=False)
admissions_df.to_csv('data/raw/admissions.csv', index=False)
labs_df.to_csv('data/raw/labs.csv',         index=False)

print(f"✅ Dataset generado:")
print(f"   Pacientes:   {len(patients):,}")
print(f"   Admisiones:  {len(admissions_df):,}")
print(f"   Laboratorios:{len(labs_df):,}")
print(f"   Guardado en data/raw/")