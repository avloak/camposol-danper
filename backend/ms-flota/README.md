# ms-flota

Microservicio REST para la gestión de la **flota de buses** de ProntoBus.

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

## Funcionalidades

- CRUD de buses (placa, marca, modelo, año, capacidad, estado).
- Registro de fechas de vencimiento de SOAT y revisión técnica.
- Endpoint de alertas para detectar vencimientos próximos / vencidos.

## Stack

- AWS API Gateway + Lambda (Python 3.13) + DynamoDB
- Serverless Framework v4
- IAM Role: **LabRole** (existente)

## Tabla DynamoDB `ms-flota-{stage}-buses`

| Campo                          | Tipo    | Descripción                          |
|--------------------------------|---------|--------------------------------------|
| id (PK)                        | string  | UUID                                 |
| placa                          | string  | Placa del bus                        |
| marca                          | string  |                                      |
| modelo                         | string  |                                      |
| anio                           | number  |                                      |
| capacidad                      | number  | Capacidad de pasajeros               |
| soat_vencimiento               | string  | YYYY-MM-DD                           |
| revision_tecnica_vencimiento   | string  | YYYY-MM-DD                           |
| estado                         | string  | OPERATIVO / MANTENIMIENTO / INACTIVO |
| created_at, updated_at         | string  | ISO-8601                             |

## Endpoints

| Método | Ruta                              | Descripción                          |
|--------|-----------------------------------|--------------------------------------|
| GET    | /buses                            | Listar todos                         |
| POST   | /buses                            | Crear bus                            |
| GET    | /buses/{id}                       | Obtener un bus                       |
| PUT    | /buses/{id}                       | Actualizar bus                       |
| DELETE | /buses/{id}                       | Eliminar bus                         |
| GET    | /buses/alertas/vencimientos?dias=30 | Alertas vencimiento SOAT/RT       |

## Despliegue automático

```bash
# 1. Pre-requisitos
npm i -g serverless

# 2. Desplegar
cd backend/ms-flota
serverless deploy --stage dev

# 3. Ver endpoints
serverless info --stage dev

# 4. Eliminar
serverless remove --stage dev
```

## Variables de entorno

Las variables son inyectadas por el `serverless.yml`:

- `TABLE_BUSES` – nombre de la tabla DynamoDB

## Ejemplos curl

```bash
BASE=https://xxxx.execute-api.us-east-1.amazonaws.com/dev

# Crear
curl -X POST $BASE/buses \
  -H "Content-Type: application/json" \
  -d '{"placa":"ABC-123","marca":"Mercedes","modelo":"Sprinter","anio":2022,"capacidad":20,"soat_vencimiento":"2026-10-15","revision_tecnica_vencimiento":"2026-09-30"}'

# Listar
curl $BASE/buses

# Alertas (próximos 60 días)
curl "$BASE/buses/alertas/vencimientos?dias=60"
```

---

## Prompt utilizado para la generación

> **Rol/Persona:** Actúa como un programador Full Stack y experto en crear Agentes de IA con servicios de AWS.
>
> **Contexto:** Una empresa de transportes llamada ProntoBus, requiere implementar una plataforma web que le permita gestionar planillas de conductores, flotas de buses, rutas de servicio, asignacion de unidades a conductores y horarios de trabajo, asi como de procesar manualmente pdfs que contienen deudas para generar envio de reportes sobre deudas, conductores con mayores infracciones y un listado de deudas por vencer.
>
> **Tarea:** Crea una web responsiva con estas funcionalidades… Gestión de Flotas: CRUD de buses, alertas de vencimiento de SOAT/Revisiones técnicas… Para el BackEnd crea 3 microservicios o apis rest (flota, conductores, horarios). Utiliza estos servicios de AWS (Api Gateway, Lambda y DynamoDB) para cada microservicio. Utiliza lenguaje de programación python. Automatiza el despliegue de cada microservicio con el framework serverless considerando el uso del rol de IAM LabRole existente. Genera un README.md para cada microservicio… indica explícitamente que ha sido creado con GitHub Copilot y la fecha de creación e incluye como referencia todo el texto del prompt utilizado.
