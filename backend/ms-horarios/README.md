# ms-horarios

Microservicio REST para la **gestión de horarios, asignaciones y rutas** de ProntoBus.

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

## Funcionalidades

- CRUD de asignaciones (turnos) conductor↔bus↔ruta.
- Motor de asignación masiva por fecha.
- CRUD básico de rutas (catálogo).

## Stack

- AWS API Gateway + Lambda (Python 3.13) + DynamoDB
- Serverless Framework v4
- IAM Role: **LabRole** (existente)

## Tablas DynamoDB

### `ms-horarios-{stage}-horarios`

| Campo               | Tipo    | Descripción                          |
|---------------------|---------|--------------------------------------|
| id (PK)             | string  | UUID                                 |
| conductor_id        | string  | Referencia conductor                 |
| bus_id              | string  | Referencia bus                       |
| ruta                | string  |                                      |
| fecha               | string  | YYYY-MM-DD                           |
| hora_inicio         | string  | HH:MM                                |
| hora_fin            | string  | HH:MM                                |
| estado              | string  | PROGRAMADO / EN_CURSO / COMPLETADO / CANCELADO |
| created_at, updated_at | string | ISO-8601                          |

### `ms-horarios-{stage}-rutas`

| Campo         | Tipo    | Descripción                |
|---------------|---------|----------------------------|
| id (PK)       | string  | UUID                       |
| nombre        | string  |                            |
| origen        | string  |                            |
| destino       | string  |                            |
| paradas       | list    |                            |
| distancia_km  | number  |                            |
| duracion_min  | number  |                            |

## Endpoints

| Método | Ruta                  | Descripción                                    |
|--------|-----------------------|------------------------------------------------|
| GET    | /horarios             | Listar asignaciones                            |
| POST   | /horarios             | Crear asignación                               |
| GET    | /horarios/{id}        | Obtener asignación                             |
| PUT    | /horarios/{id}        | Actualizar                                     |
| DELETE | /horarios/{id}        | Eliminar                                       |
| POST   | /horarios/asignar     | Asignación masiva conductor↔bus↔ruta por fecha |
| GET    | /rutas                | Listar rutas                                   |
| POST   | /rutas                | Crear ruta                                     |

## Despliegue automático

```bash
cd backend/ms-horarios
serverless deploy --stage dev
serverless info --stage dev
```

## Eliminar

```bash
serverless remove --stage dev
```

## Variables de entorno

- `TABLE_HORARIOS`
- `TABLE_RUTAS`

## Ejemplos curl

```bash
BASE=https://xxxx.execute-api.us-east-1.amazonaws.com/dev

# Crear ruta
curl -X POST $BASE/rutas -H "Content-Type: application/json" \
  -d '{"nombre":"Línea 12","origen":"Callao","destino":"La Molina","distancia_km":24.5,"duracion_min":75}'

# Asignación masiva
curl -X POST $BASE/horarios/asignar -H "Content-Type: application/json" \
  -d '{"fecha":"2026-04-09","asignaciones":[{"conductor_id":"u1","bus_id":"b1","ruta":"Línea 12","hora_inicio":"06:00","hora_fin":"14:00"}]}'
```

---

## Prompt utilizado para la generación

> **Rol/Persona:** Actúa como un programador Full Stack y experto en crear Agentes de IA con servicios de AWS.
>
> **Contexto:** Una empresa de transportes llamada ProntoBus, requiere implementar una plataforma web que le permita gestionar planillas de conductores, flotas de buses, rutas de servicio, asignacion de unidades a conductores y horarios de trabajo, asi como de procesar manualmente pdfs que contienen deudas para generar envio de reportes sobre deudas, conductores con mayores infracciones y un listado de deudas por vencer.
>
> **Tarea:** Crea una web responsiva con estas funcionalidades… Planificación y Turnos: Motor de asignación de buses a conductores y gestión de rutas/horarios… Para el BackEnd crea 3 microservicios o apis rest (flota, conductores, horarios). Utiliza estos servicios de AWS (Api Gateway, Lambda y DynamoDB) para cada microservicio. Utiliza lenguaje de programación python. Automatiza el despliegue de cada microservicio con el framework serverless considerando el uso del rol de IAM LabRole existente. Genera un README.md… indica explícitamente que ha sido creado con GitHub Copilot y la fecha de creación e incluye como referencia todo el texto del prompt utilizado.
