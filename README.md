# 🏥 Sistema de Registro y Control de Vacunas
**Arquitectura Serverless: IaaS + FaaS + SaaS**

## Requisitos
- Docker Desktop instalado y corriendo
- Puerto 8000 y 5432 libres

## ▶️ Cómo levantar el sistema

```bash
# 1. Clonar o descomprimir la carpeta del proyecto
cd sistema_vacunas

# 2. Levantar todos los contenedores
docker-compose up --build

# 3. Abrir el portal web
#    Doble clic en index.html o abrir en el navegador

# 4. Ver documentación automática de la API
#    http://localhost:8000/docs
```

## 🏗 Arquitectura

| Capa | Tecnología | Descripción |
|------|-----------|-------------|
| IaaS | Docker Desktop + PostgreSQL | Infraestructura en contenedores |
| FaaS | Python + FastAPI | Microservicios / funciones serverless |
| SaaS | HTML + Bootstrap + JS | Portal web de acceso al sistema |

## 📡 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|---------|-------------|
| POST | /pacientes/registro | Registrar paciente por CURP |
| GET | /pacientes/{curp} | Consultar datos de un paciente |
| POST | /vacunas/aplicar | Registrar vacuna aplicada |
| GET | /historial/{curp} | Ver historial completo por CURP |
| GET | /proximas/{curp} | Ver próximas dosis pendientes |
| POST | /alertas/enviar | Disparar sistema de alertas |
| GET | /vacunas/catalogo | Ver catálogo de vacunas |
