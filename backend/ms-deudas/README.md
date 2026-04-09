# ms-deudas

Microservicio para el **procesamiento automatizado de deudas por infracciones de tránsito** mediante un workflow asíncrono de **Step Functions** que utiliza IA (Groq + Llama 3.3 70B).

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

## Funcionalidades

- Endpoint REST asíncrono para iniciar el workflow.
- Endpoint REST "Agente IA Prontobus" para deudas (Groq).
- Workflow Step Functions:
  1. **ListFiles** – enumera los archivos `.md` de la carpeta S3.
  2. **Map / ProcessFile** – por cada archivo invoca al agente IA y guarda el resultado en DynamoDB. La IA además calcula la fecha límite de descuento.
  3. **GenerateCsv** – genera un CSV (separador `;`) con la tabla comparativa.
  4. **SendEmail** – envía el CSV adjunto al correo configurado vía SendGrid.
- Endpoints adicionales:
  - **GET /deudas/ranking** – ranking de conductores con más infracciones.
  - **GET /deudas/por-vencer?dias=7** – deudas con fecha límite próxima.

## Stack

- AWS API Gateway + Step Functions + Lambda (Python **3.14**, urllib) + DynamoDB + S3
- API IA: **Groq** modelo `llama-3.3-70b-versatile`
- API Email: **SendGrid**
- Serverless Framework v4 + plugin `serverless-step-functions`
- IAM Role: **LabRole** (existente)

## Tabla DynamoDB `ms-deudas-{stage}-deudas`

| Campo            | Tipo   | Descripción                                         |
|------------------|--------|-----------------------------------------------------|
| id (PK)          | string | UUID                                                |
| execution_id     | string | ID de la ejecución del Step Function (GSI)          |
| archivo          | string | URI S3 del archivo procesado                        |
| instrucciones_s3 | string |                                                     |
| email            | string |                                                     |
| resultado        | map    | JSON devuelto por la IA (lista de deudas, fechas, montos) |
| modelo           | string |                                                     |
| created_at       | string | ISO-8601                                            |

## Bucket S3

`ms-deudas-{stage}-bucket-{accountId}`:

```
instrucciones/
   extraer.md
infracciones/
   doc001.md
   doc002.md
   ...
resultados/                ← se crean automáticamente
   deudas-<exec>-<ts>.csv
```

## Endpoints

| Método | Ruta                                  | Descripción                              |
|--------|---------------------------------------|------------------------------------------|
| POST   | /deudas/workflow                      | Iniciar ejecución asíncrona              |
| GET    | /deudas/workflow/{executionArn+}      | Estado de ejecución                      |
| POST   | /agente-ia/deudas                     | API Agente IA Prontobus                  |
| GET    | /deudas/ranking                       | Ranking de infractores                   |
| GET    | /deudas/por-vencer?dias=7             | Deudas con fecha límite próxima          |
| GET    | /deudas/resultados                    | **Listar CSVs generados por el workflow IA** |
| GET    | /deudas/resultados/{key+}/download    | **Descargar un CSV (presigned URL 5 min)**   |

## Mejoras de correo (HTML)

El correo del workflow usa una **plantilla HTML responsiva** con branding ProntoBus:
header con gradiente rojo/naranja, stat cards (filas, estado, modelo IA), metadatos
de la ejecución, callout de advertencia sobre fechas de descuento y footer
profesional. Estilos inline compatibles con Gmail / Outlook.

### POST /deudas/workflow

```json
{
  "instrucciones_s3": "s3://ms-deudas-dev-bucket-123/instrucciones/extraer.md",
  "contenido_s3":     "s3://ms-deudas-dev-bucket-123/infracciones/",
  "email":            "finanzas@prontobus.com"
}
```

## Variables de entorno globales (no .env)

```bash
export GROQ_API_KEY="..."
export SENDGRID_API_KEY="..."
export SENDGRID_FROM_EMAIL="noreply@prontobus.com"
```

## Despliegue automático

```bash
cd backend/ms-deudas
npm install
serverless deploy --stage dev
serverless info --stage dev
```

## Eliminar despliegue

```bash
serverless remove --stage dev
```

## Postman

Ver `backend/postman/ms-deudas.postman_collection.json`.

---

## Prompt utilizado para la generación

> **Rol/Persona:** Actúa como un programador Full Stack y experto en crear Agentes de IA con servicios de AWS.
>
> **Contexto:** Una empresa de transportes llamada ProntoBus, requiere implementar una plataforma web que le permita gestionar planillas de conductores, flotas de buses, rutas de servicio, asignacion de unidades a conductores y horarios de trabajo, asi como de procesar manualmente pdfs que contienen deudas para generar envio de reportes sobre deudas, conductores con mayores infracciones y un listado de deudas por vencer.
>
> **Tarea:** Procesamiento de Documentos de Deudas por Infracciones: Ingesta de PDFs para almacenar las deudas extraídas, calcula fechas límite de descuento y genera el ranking de infractores. Comunicaciones: Envío de correos electrónicos para reportes de deudas y alertas de vencimientos. Crea workflows que usen IA con esas funcionalidades:
> 1. Recibe como entrada estos datos: Ruta a archivo en bucket S3 en formato markdown con instrucciones para IA, Ruta a carpeta en bucket S3 que contenga archivos en formato markdown para evaluar con las instrucciones, Correo donde enviar el archivo con los resultados.
> 2. Por cada archivo debe llamar al Api Agente IA prontobus y enviarle como parametro la ruta del archivo de instrucciones y la ruta del archivo de contenido. El procesamiento lo realizara el Api IA de Groq.
> 3. El resultado del Api Agente IA prontobus (formato json) debe guardarlo en una tabla dynamodb.
> 4. Debe generar un archivo en formato CSV con campos separados por punto y coma (;) y una tabla comparativa con el resultado del Api de todos los archivos evaluados, almacenarlo en el bucket en una carpeta "resultados".
> 5. Debe enviar un correo utilizando el Api de SendGrid adjuntando el archivo CSV anterior.
>
> **Requisitos:** Para el BackEnd crea 2 microservicios (descansos, deudas). Utiliza estos servicios de AWS (Api Gateway, Step Functions, DynamoDB, Lambda). Genera endpoints en Api Gateway para poder ejecutar el workflow Step Functions de forma asincrona. En caso se necesite crear lambdas utiliza lenguaje de programacion python version 3.14 con libreria urllib en vez de requests. Api IA de Groq con el modelo "llama-3.3-70b-versatile". Para la IaC utiliza el framework serverless versión 4 con rol de IAM LabRole existente. Considera que usaremos variables de entorno globales y no archivos .env. Genera un readme.md… indica explícitamente que ha sido creado con GitHub Copilot y la fecha de creación e incluye como referencia todo el texto del prompt utilizado. Genera colecciones postman para poder probar los nuevos apis workflow creados.
