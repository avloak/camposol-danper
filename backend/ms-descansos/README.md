# ms-descansos

Microservicio para el **procesamiento automatizado de descansos médicos** mediante un workflow asíncrono de **Step Functions** que utiliza IA (Groq + Llama 3.3 70B), más un flujo de **aprobación / rechazo manual** por parte del administrador con notificación por correo.

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08
>
> Caso de uso: empresas agroindustriales (Camposol, Dunper – Trujillo) que mueven ~200 buses con ~50 personas cada uno (≈10 000 personas/día). El alto volumen de descansos médicos requiere una bandeja centralizada de aprobación para RRHH.

## Funcionalidades

- Endpoint REST asíncrono que dispara un Step Function.
- Endpoint REST "Agente IA Prontobus" que llama a la API de Groq.
- Workflow Step Functions:
  1. **ListFiles** – enumera los archivos `.md` de la carpeta S3 indicada.
  2. **Map / ProcessFile** – por cada archivo invoca al *Agente IA Prontobus*, guarda el resultado JSON en DynamoDB y crea automáticamente una **Solicitud de Descanso Médico** en estado `PENDIENTE` con los datos extraídos por la IA.
  3. **GenerateCsv** – genera un CSV (separador `;`) con la tabla comparativa y lo almacena en `s3://<bucket>/resultados/`.
  4. **SendEmail** – envía el CSV adjunto al correo configurado mediante el API de SendGrid.
- **Bandeja de Solicitudes (nuevo)**:
  - CRUD de Solicitudes de Descanso Médico.
  - Registro manual desde el frontend (independiente del workflow IA).
  - Botones **Aprobar / Rechazar** que actualizan el estado y disparan automáticamente un correo al remitente vía SendGrid (HTML con todo el detalle del descanso y las observaciones del administrador).

## Stack

- AWS API Gateway + Step Functions + Lambda (Python **3.14**, urllib) + DynamoDB + S3
- API IA: **Groq** modelo `llama-3.3-70b-versatile`
- API Email: **SendGrid**
- Serverless Framework v4 + plugin `serverless-step-functions`
- IAM Role: **LabRole** (existente)

## Tabla DynamoDB `ms-descansos-{stage}-descansos`

| Campo            | Tipo   | Descripción                            |
|------------------|--------|----------------------------------------|
| id (PK)          | string | UUID del registro                      |
| execution_id     | string | ID de la ejecución del Step Function (GSI) |
| archivo          | string | URI S3 del archivo procesado           |
| instrucciones_s3 | string | URI S3 del archivo de instrucciones    |
| email            | string | Correo destinatario                    |
| resultado        | map    | JSON devuelto por la IA                |
| modelo           | string | Modelo Groq utilizado                  |
| created_at       | string | ISO-8601                               |

## Tabla DynamoDB `ms-descansos-{stage}-solicitudes` (nuevo)

| Campo             | Tipo   | Descripción                                       |
|-------------------|--------|---------------------------------------------------|
| id (PK)           | string | UUID                                              |
| paciente_nombre   | string | Nombre completo del paciente                      |
| paciente_dni      | string | DNI del paciente                                  |
| medico_nombre     | string | Nombre del médico tratante                        |
| medico_cmp        | string | Código CMP (Colegio Médico del Perú)              |
| diagnostico       | string | Diagnóstico                                       |
| fecha_inicio      | string | YYYY-MM-DD                                        |
| fecha_fin         | string | YYYY-MM-DD                                        |
| dias_descanso     | number | Calculado automáticamente                         |
| remitente_email   | string | Correo a notificar al aprobar/rechazar            |
| remitente_nombre  | string |                                                   |
| conductor_id      | string | Opcional – referencia al ms-conductores           |
| origen            | string | `MANUAL` o `IA_WORKFLOW`                          |
| archivo_origen    | string | Solo cuando origen = `IA_WORKFLOW`                |
| estado            | string | `PENDIENTE` / `APROBADO` / `RECHAZADO` (GSI)      |
| observaciones     | string | Texto del admin que se incluye en el correo       |
| revisado_por      | string |                                                   |
| revisado_at       | string | ISO-8601                                          |
| created_at        | string | ISO-8601                                          |
| updated_at        | string | ISO-8601                                          |

## Bucket S3

`ms-descansos-{stage}-bucket-{accountId}` con la estructura:

```
instrucciones/
   extraer.md
certificados/
   cert001.md
   cert002.md
   ...
resultados/                ← se crean automáticamente
   descansos-<exec>-<ts>.csv
```

## Endpoints

| Método | Ruta                                              | Descripción                                       |
|--------|---------------------------------------------------|---------------------------------------------------|
| POST   | /descansos/workflow                               | Inicia ejecución asíncrona del Step Function      |
| GET    | /descansos/workflow/{executionArn+}               | Estado de la ejecución                            |
| POST   | /agente-ia/descansos                              | API Agente IA Prontobus (Groq)                    |
| GET    | /descansos/solicitudes?estado=PENDIENTE           | Listar solicitudes (filtro opcional por estado)   |
| POST   | /descansos/solicitudes                            | Crear solicitud manual                            |
| GET    | /descansos/solicitudes/{id}                       | Obtener solicitud                                 |
| PUT    | /descansos/solicitudes/{id}/aprobar               | Aprobar y enviar email HTML al remitente          |
| PUT    | /descansos/solicitudes/{id}/rechazar              | Rechazar y enviar email HTML al remitente         |
| GET    | /descansos/solicitudes/exportar?estado=PENDIENTE  | **Exportar listado a CSV (descarga directa)**     |
| GET    | /descansos/resultados                             | **Listar CSVs generados por el workflow IA**      |
| GET    | /descansos/resultados/{key+}/download             | **Descargar un CSV (presigned URL 5 min)**        |

## Mejoras de correo (HTML)

Todos los correos (workflow + aprobación/rechazo) usan una **plantilla HTML responsiva**
con:
- Header con gradiente y branding ProntoBus
- Stat cards con totales y estado
- Tabla de detalle con filas alternadas
- Badge de estado destacado
- Callouts para observaciones del administrador
- Footer profesional
- Estilos inline 100% compatibles con Gmail y Outlook

### POST /descansos/workflow

Body:

```json
{
  "instrucciones_s3": "s3://ms-descansos-dev-bucket-123/instrucciones/extraer.md",
  "contenido_s3":     "s3://ms-descansos-dev-bucket-123/certificados/",
  "email":            "supervisor@prontobus.com"
}
```

Respuesta `202 Accepted`:

```json
{
  "message": "Workflow iniciado",
  "execution_id": "descansos-abcd-1234...",
  "execution_arn": "arn:aws:states:..."
}
```

### POST /agente-ia/descansos

Body:

```json
{
  "instrucciones_s3": "s3://bucket/instrucciones.md",
  "contenido_s3":     "s3://bucket/cert/cert001.md"
}
```

### POST /descansos/solicitudes (manual)

```json
{
  "paciente_nombre": "Juan Pérez Quispe",
  "paciente_dni":    "45678901",
  "medico_nombre":   "Dra. María Salas",
  "medico_cmp":      "56789",
  "diagnostico":     "Lumbalgia aguda - reposo absoluto",
  "fecha_inicio":    "2026-04-09",
  "fecha_fin":       "2026-04-12",
  "conductor_id":    "u-001",
  "remitente_nombre": "RRHH Camposol",
  "remitente_email":  "rrhh@camposol.com.pe"
}
```

### PUT /descansos/solicitudes/{id}/aprobar  ·  /rechazar

```json
{
  "observaciones": "Validado por médico ocupacional, procede el descanso.",
  "revisado_por":  "admin@prontobus.com"
}
```

Respuesta:

```json
{
  "solicitud": { "id": "...", "estado": "APROBADO", ... },
  "email":     { "status": "OK", "http": 202, "to": "rrhh@camposol.com.pe" }
}
```

El correo se envía con plantilla HTML que incluye paciente, DNI, médico, CMP, diagnóstico, fechas y observaciones del administrador.

## Variables de entorno globales (no .env)

Definir antes de hacer `serverless deploy`:

```bash
export GROQ_API_KEY="..."
export SENDGRID_API_KEY="..."
export SENDGRID_FROM_EMAIL="noreply@prontobus.com"
```

PowerShell (Windows):

```powershell
$env:GROQ_API_KEY="..."
$env:SENDGRID_API_KEY="..."
$env:SENDGRID_FROM_EMAIL="noreply@prontobus.com"
```

## Despliegue automático

```bash
# 1. Pre-requisitos
npm i -g serverless

# 2. Instalar plugin de Step Functions
cd backend/ms-descansos
npm install

# 3. Verificar variables de entorno (ver sección anterior)

# 4. Desplegar
serverless deploy --stage dev

# 5. Ver endpoints
serverless info --stage dev

# 6. Eliminar despliegue
serverless remove --stage dev
```

## Postman

Ver `backend/postman/ms-descansos.postman_collection.json`.

---

## Prompt utilizado para la generación

> **Rol/Persona:** Actúa como un programador Full Stack y experto en crear Agentes de IA con servicios de AWS.
>
> **Contexto:** Una empresa de transportes llamada ProntoBus, requiere implementar una plataforma web que le permita gestionar planillas de conductores, flotas de buses, rutas de servicio, asignacion de unidades a conductores y horarios de trabajo, asi como de procesar manualmente pdfs que contienen deudas para generar envio de reportes sobre deudas, conductores con mayores infracciones y un listado de deudas por vencer.
>
> **Tarea:** Procesamiento de Descansos Medicos: Ingesta de PDFs para extraer texto estructurado de certificados médicos y modificar el horario del conductor afectado automaticamente. Crea workflows que usen IA con esas funcionalidades:
> 1. Recibe como entrada estos datos: Ruta a archivo en bucket S3 en formato markdown con instrucciones para IA, Ruta a carpeta en bucket S3 que contenga archivos en formato markdown para evaluar con las instrucciones, Correo donde enviar el archivo con los resultados.
> 2. Por cada archivo debe llamar al Api Agente IA prontobus y enviarle como parametro la ruta del archivo de instrucciones y la ruta del archivo de contenido. El procesamiento lo realizara el Api IA de Groq.
> 3. El resultado del Api Agente IA prontobus (formato json) debe guardarlo en una tabla dynamodb.
> 4. Debe generar un archivo en formato CSV con campos separados por punto y coma (;) y una tabla comparativa con el resultado del Api de todos los archivos evaluados, almacenarlo en el bucket en una carpeta "resultados".
> 5. Debe enviar un correo utilizando el Api de SendGrid adjuntando el archivo CSV anterior.
>
> **Requisitos:** Para el BackEnd crea 2 microservicios (descansos, deudas). Utiliza estos servicios de AWS (Api Gateway, Step Functions, DynamoDB, Lambda). Genera endpoints en Api Gateway para poder ejecutar el workflow Step Functions de forma asincrona. En caso se necesite crear lambdas utiliza lenguaje de programacion python version 3.14 con libreria urllib en vez de requests. Api IA de Groq con el modelo "llama-3.3-70b-versatile". Para la IaC utiliza el framework serverless versión 4 con rol de IAM LabRole existente. Considera que usaremos variables de entorno globales y no archivos .env. Genera un readme.md… indica explícitamente que ha sido creado con GitHub Copilot y la fecha de creación e incluye como referencia todo el texto del prompt utilizado. Genera colecciones postman para poder probar los nuevos apis workflow creados.
