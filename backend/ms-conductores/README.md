# ms-conductores

Microservicio REST para la gestión de **conductores** de ProntoBus.

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

## Funcionalidades

- CRUD de conductores con datos personales, licencia, legajo y disponibilidad.
- Endpoint para listar conductores disponibles (motor de asignación).

## Stack

- AWS API Gateway + Lambda (Python 3.13) + DynamoDB
- Serverless Framework v4
- IAM Role: **LabRole** (existente)

## Tabla DynamoDB `ms-conductores-{stage}-conductores`

| Campo                            | Tipo    | Descripción                              |
|----------------------------------|---------|------------------------------------------|
| id (PK)                          | string  | UUID                                     |
| dni                              | string  |                                          |
| nombre, apellidos                | string  |                                          |
| fecha_nacimiento                 | string  | YYYY-MM-DD                               |
| telefono, email, direccion       | string  |                                          |
| licencia_numero                  | string  |                                          |
| licencia_categoria               | string  | A-I, A-IIa, A-IIb, A-IIIa, A-IIIb, A-IIIc|
| licencia_emision, licencia_vencimiento | string | YYYY-MM-DD                          |
| fecha_ingreso                    | string  |                                          |
| cargo                            | string  |                                          |
| salario                          | number  |                                          |
| contacto_emergencia              | string  |                                          |
| contacto_emergencia_telefono     | string  |                                          |
| disponibilidad                   | string  | DISPONIBLE / ASIGNADO / DESCANSO / VACACIONES |
| observaciones                    | string  |                                          |
| created_at, updated_at           | string  | ISO-8601                                 |

## Endpoints

| Método | Ruta                       | Descripción              |
|--------|----------------------------|--------------------------|
| GET    | /conductores               | Listar todos             |
| POST   | /conductores               | Crear conductor          |
| GET    | /conductores/{id}          | Obtener uno              |
| PUT    | /conductores/{id}          | Actualizar               |
| DELETE | /conductores/{id}          | Eliminar                 |
| GET    | /conductores/disponibles   | Solo disponibles         |

## Despliegue automático

```bash
cd backend/ms-conductores
serverless deploy --stage dev
serverless info --stage dev
```

## Eliminar despliegue

```bash
serverless remove --stage dev
```

## Variables de entorno

- `TABLE_CONDUCTORES` – nombre de la tabla DynamoDB

## Ejemplos curl

```bash
BASE=https://xxxx.execute-api.us-east-1.amazonaws.com/dev
curl -X POST $BASE/conductores -H "Content-Type: application/json" \
  -d '{"dni":"45678901","nombre":"Juan","apellidos":"Pérez","licencia_numero":"Q12345678","licencia_categoria":"A-IIb","licencia_vencimiento":"2027-01-15","disponibilidad":"DISPONIBLE"}'
```

---

## Prompt utilizado para la generación

> **Rol/Persona:** Actúa como un programador Full Stack y experto en crear Agentes de IA con servicios de AWS.
>
> **Contexto:** Una empresa de transportes llamada ProntoBus, requiere implementar una plataforma web que le permita gestionar planillas de conductores, flotas de buses, rutas de servicio, asignacion de unidades a conductores y horarios de trabajo, asi como de procesar manualmente pdfs que contienen deudas para generar envio de reportes sobre deudas, conductores con mayores infracciones y un listado de deudas por vencer.
>
> **Tarea:** Crea una web responsiva con estas funcionalidades… Gestión de Conductores: Perfiles de conductores, licencias, disponibilidad y legajo personal… Para el BackEnd crea 3 microservicios o apis rest (flota, conductores, horarios). Utiliza estos servicios de AWS (Api Gateway, Lambda y DynamoDB) para cada microservicio. Utiliza lenguaje de programación python. Automatiza el despliegue de cada microservicio con el framework serverless considerando el uso del rol de IAM LabRole existente. Genera un README.md… indica explícitamente que ha sido creado con GitHub Copilot y la fecha de creación e incluye como referencia todo el texto del prompt utilizado.
