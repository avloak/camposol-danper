# ProntoBus - Plataforma de Gestión de Transportes

Plataforma web para la empresa de transportes **ProntoBus** que permite gestionar planillas de conductores, flotas de buses, rutas de servicio, asignación de unidades, horarios de trabajo y procesamiento automatizado de PDFs (descansos médicos y deudas por infracciones) usando Inteligencia Artificial.

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

---

## Arquitectura

```
┌─────────────────────────────────────────────────────────┐
│                  FRONTEND (React + S3)                  │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        │   API Gateway      │
        └─────────┬──────────┘
                  │
   ┌──────┬───────┼────────┬──────────┐
   ▼      ▼       ▼        ▼          ▼
ms-flota ms-cond ms-hora ms-desc   ms-deudas
   │      │       │        │          │
   ▼      ▼       ▼        ▼          ▼
DynamoDB DynDB  DynDB  StepFunctions StepFunctions
                          │              │
                          ▼              ▼
                       Groq IA        Groq IA
                       SendGrid       SendGrid
                       S3             S3
```

## Estructura del proyecto

```
Trabajo Final Cloud/
├── frontend/                   # App React responsiva
├── backend/
│   ├── ms-flota/               # CRUD buses + alertas SOAT/RT
│   ├── ms-conductores/         # CRUD conductores
│   ├── ms-horarios/            # Rutas, turnos, asignaciones
│   ├── ms-descansos/           # Workflow descansos médicos (IA)
│   └── ms-deudas/              # Workflow deudas infracciones (IA)
└── postman/                    # Colecciones Postman
```

## Microservicios

| Microservicio   | Tecnología                                   | Descripción                                   |
|-----------------|----------------------------------------------|-----------------------------------------------|
| ms-flota        | API Gateway + Lambda (Python) + DynamoDB     | CRUD de buses, alertas vencimientos           |
| ms-conductores  | API Gateway + Lambda (Python) + DynamoDB     | Perfiles, licencias, legajos                  |
| ms-horarios     | API Gateway + Lambda (Python) + DynamoDB     | Rutas, turnos, asignaciones                   |
| ms-descansos    | API Gateway + StepFunctions + Lambda + DynamoDB | Workflow IA descansos médicos              |
| ms-deudas       | API Gateway + StepFunctions + Lambda + DynamoDB | Workflow IA deudas e infracciones          |

## Despliegue rápido

Cada microservicio y el frontend tienen su propio `README.md` con instrucciones detalladas.

```bash
# 1. Backend - desplegar microservicios
cd backend/ms-flota         && serverless deploy --stage dev
cd ../ms-conductores        && serverless deploy --stage dev
cd ../ms-horarios           && serverless deploy --stage dev
cd ../ms-descansos          && serverless deploy --stage dev
cd ../ms-deudas             && serverless deploy --stage dev

# 2. Frontend - build y deploy
cd ../../frontend
npm install
npm run build
serverless deploy --stage dev
```

## Variables de entorno globales requeridas

Estas variables deben estar definidas en el entorno (no en archivos `.env`):

```bash
export GROQ_API_KEY="tu_groq_api_key"
export SENDGRID_API_KEY="tu_sendgrid_api_key"
export SENDGRID_FROM_EMAIL="noreply@prontobus.com"
```

En Windows (PowerShell):

```powershell
$env:GROQ_API_KEY="tu_groq_api_key"
$env:SENDGRID_API_KEY="tu_sendgrid_api_key"
$env:SENDGRID_FROM_EMAIL="noreply@prontobus.com"
```

## Requisitos

- Node.js 20+
- Python 3.13/3.14
- Serverless Framework v4
- AWS CLI configurado con credenciales (LabRole)
- Cuenta Groq (https://console.groq.com)
- Cuenta SendGrid (https://sendgrid.com)
