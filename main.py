from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import date, timedelta
from typing import Optional
import psycopg2
import psycopg2.extras
import os

app = FastAPI(
    title="Sistema de Registro y Control de Vacunas",
    description="API Serverless para gestión de vacunas en centros de salud",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    return psycopg2.connect(
        "postgresql://postgres:IzvxQgTnKurUdcKzJcZheSEByXKsfPGT@centerbeam.proxy.rlwy.net:22486/railway",
        cursor_factory=psycopg2.extras.RealDictCursor
    )

# ── Modelos ──────────────────────────────────────────────
class Paciente(BaseModel):
    curp: str
    nombre: str
    apellidos: str
    fecha_nacimiento: date
    email: Optional[str] = None
    telefono: Optional[str] = None

class AplicacionVacuna(BaseModel):
    curp: str
    vacuna_id: int
    numero_dosis: int
    centro_salud: str
    lote: Optional[str] = None

# ── Endpoints ────────────────────────────────────────────
@app.get("/")
def root():
    return {"mensaje": "Sistema de Vacunas API activo", "version": "1.0.0"}

@app.post("/pacientes/registro", summary="Registrar nuevo paciente")
def registrar_paciente(paciente: Paciente):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO pacientes (curp, nombre, apellidos, fecha_nacimiento, email, telefono)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (curp) DO UPDATE SET
            nombre=EXCLUDED.nombre, apellidos=EXCLUDED.apellidos,
            email=EXCLUDED.email, telefono=EXCLUDED.telefono
    """, (paciente.curp.upper(), paciente.nombre, paciente.apellidos,
          paciente.fecha_nacimiento, paciente.email, paciente.telefono))
    conn.commit()
    conn.close()
    return {"mensaje": "Paciente registrado exitosamente", "curp": paciente.curp.upper()}

@app.get("/pacientes/{curp}", summary="Consultar datos de un paciente")
def consultar_paciente(curp: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM pacientes WHERE curp = %s", (curp.upper(),))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Paciente no encontrado")
    return dict(row)

@app.post("/vacunas/aplicar", summary="Registrar aplicación de vacuna")
def aplicar_vacuna(aplicacion: AplicacionVacuna):
    conn = get_db()
    cur = conn.cursor()
    # Verificar que el paciente existe
    cur.execute("SELECT curp FROM pacientes WHERE curp = %s", (aplicacion.curp.upper(),))
    if not cur.fetchone():
        raise HTTPException(status_code=404, detail="Paciente no registrado, registre primero")
    # Obtener datos de la vacuna
    cur.execute("SELECT * FROM vacunas WHERE id = %s", (aplicacion.vacuna_id,))
    vacuna = cur.fetchone()
    if not vacuna:
        raise HTTPException(status_code=404, detail="Vacuna no encontrada en el catálogo")
    # Registrar aplicación
    cur.execute("""
        INSERT INTO aplicaciones (curp, vacuna_id, numero_dosis, centro_salud, lote)
        VALUES (%s, %s, %s, %s, %s)
    """, (aplicacion.curp.upper(), aplicacion.vacuna_id, aplicacion.numero_dosis,
          aplicacion.centro_salud, aplicacion.lote))
    # Programar alerta para siguiente dosis si aplica
    if aplicacion.numero_dosis < vacuna["dosis_total"] and vacuna["intervalo_dias"] > 0:
        fecha_siguiente = date.today() + timedelta(days=vacuna["intervalo_dias"])
        cur.execute("""
            INSERT INTO alertas (curp, vacuna_id, fecha_programada)
            VALUES (%s, %s, %s)
        """, (aplicacion.curp.upper(), aplicacion.vacuna_id, fecha_siguiente))
    conn.commit()
    conn.close()
    return {
        "mensaje": "Vacuna registrada exitosamente",
        "vacuna": vacuna["nombre"],
        "dosis": aplicacion.numero_dosis
    }

@app.get("/historial/{curp}", summary="Consultar historial de vacunación por CURP")
def consultar_historial(curp: str):
    conn = get_db()
    cur = conn.cursor()
    # Verificar paciente
    cur.execute("SELECT nombre, apellidos FROM pacientes WHERE curp = %s", (curp.upper(),))
    paciente = cur.fetchone()
    if not paciente:
        raise HTTPException(status_code=404, detail="CURP no encontrada en el sistema")
    # Obtener historial
    cur.execute("""
        SELECT v.nombre as vacuna, a.numero_dosis, a.fecha_aplicacion,
               a.centro_salud, a.lote, v.dosis_total
        FROM aplicaciones a
        JOIN vacunas v ON a.vacuna_id = v.id
        WHERE a.curp = %s
        ORDER BY a.fecha_aplicacion DESC
    """, (curp.upper(),))
    historial = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {
        "curp": curp.upper(),
        "paciente": f"{paciente['nombre']} {paciente['apellidos']}",
        "total_vacunas": len(historial),
        "historial": historial
    }

@app.get("/proximas/{curp}", summary="Consultar próximas vacunas pendientes")
def proximas_vacunas(curp: str):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT v.nombre as vacuna, a.fecha_programada,
               EXTRACT(DAY FROM a.fecha_programada - CURRENT_DATE)::int as dias_restantes
        FROM alertas a
        JOIN vacunas v ON a.vacuna_id = v.id
        WHERE a.curp = %s AND a.enviada = false
        ORDER BY a.fecha_programada ASC
    """, (curp.upper(),))
    proximas = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"curp": curp.upper(), "proximas_dosis": proximas}

@app.post("/alertas/enviar", summary="Enviar alertas de vacunas próximas")
def enviar_alertas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT a.id, p.email, p.nombre, p.apellidos, v.nombre as vacuna, a.fecha_programada
        FROM alertas a
        JOIN pacientes p ON a.curp = p.curp
        JOIN vacunas v ON a.vacuna_id = v.id
        WHERE a.enviada = false
        AND a.fecha_programada <= CURRENT_DATE + INTERVAL '7 days'
    """)
    alertas = cur.fetchall()
    enviadas = 0
    for alerta in alertas:
        # En producción aquí se integraría SMTP o SendGrid
        print(f"[ALERTA] Para: {alerta['email']} | "
              f"Paciente: {alerta['nombre']} {alerta['apellidos']} | "
              f"Vacuna: {alerta['vacuna']} | "
              f"Fecha: {alerta['fecha_programada']}")
        cur.execute("UPDATE alertas SET enviada=true WHERE id=%s", (alerta["id"],))
        enviadas += 1
    conn.commit()
    conn.close()
    return {"mensaje": f"Proceso completado", "alertas_enviadas": enviadas}

@app.get("/vacunas/catalogo", summary="Ver catálogo de vacunas disponibles")
def catalogo_vacunas():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM vacunas ORDER BY id")
    vacunas = [dict(r) for r in cur.fetchall()]
    conn.close()
    return {"total": len(vacunas), "vacunas": vacunas}
