# ProntoBus - Frontend Web

Aplicación web responsiva en React para la gestión de la plataforma **ProntoBus**.

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

## Funcionalidades

- **Dashboard** con accesos rápidos a todas las secciones.
- **Gestión de Flotas**: CRUD de buses, alertas visuales de vencimiento de SOAT y revisión técnica.
- **Gestión de Conductores**: listado y registro multi-paso (responsivo en mobile) de perfiles, licencias, legajo y disponibilidad.
- **Planificación y Turnos**: asignación de buses a conductores, rutas y horarios.
- **Procesamiento de Descansos Médicos**: formulario para iniciar workflow asíncrono de Step Functions.
- **Procesamiento de Deudas / Infracciones**: formulario para iniciar workflow asíncrono de Step Functions.
- Diseño 100% responsivo (sidebar colapsable en mobile).

## Stack

- React 18 + Vite
- React Router DOM
- Axios
- Hosting estático en S3 (bucket público)

## Despliegue automático con Serverless Framework v4

### 1. Pre-requisitos

- Node.js 20+
- Serverless Framework v4: `npm i -g serverless`
- Plugin: `npm i -D serverless-s3-sync`
- AWS CLI configurado con credenciales de **LabRole**

### 2. Variables de entorno (opcional, para apuntar a tus APIs)

Defínelas como variables de entorno globales del sistema (no archivo .env):

```bash
export VITE_API_FLOTA="https://xxxx.execute-api.us-east-1.amazonaws.com/dev"
export VITE_API_CONDUCTORES="https://xxxx.execute-api.us-east-1.amazonaws.com/dev"
export VITE_API_HORARIOS="https://xxxx.execute-api.us-east-1.amazonaws.com/dev"
export VITE_API_DESCANSOS="https://xxxx.execute-api.us-east-1.amazonaws.com/dev"
export VITE_API_DEUDAS="https://xxxx.execute-api.us-east-1.amazonaws.com/dev"
```

En Windows (PowerShell):

```powershell
$env:VITE_API_FLOTA="https://..."
$env:VITE_API_CONDUCTORES="https://..."
$env:VITE_API_HORARIOS="https://..."
$env:VITE_API_DESCANSOS="https://..."
$env:VITE_API_DEUDAS="https://..."
```

### 3. Instalar dependencias

```bash
npm install
npm install -D serverless-s3-sync
```

### 4. Build de la app

```bash
npm run build
```

Esto genera la carpeta `dist/` que será sincronizada con S3.

### 5. Desplegar a AWS

```bash
serverless deploy --stage dev
```

El despliegue:

1. Crea el bucket S3 público `prontobus-web-dev-<accountId>`.
2. Configura el bucket como sitio web estático.
3. Aplica la política pública de lectura.
4. Sincroniza la carpeta `dist/` al bucket.

### 6. Obtener la URL del sitio

```bash
serverless info --stage dev
```

La URL aparece como `WebsiteURL`. Suele tener el formato:

```
http://prontobus-web-dev-<accountId>.s3-website-us-east-1.amazonaws.com
```

### 7. Eliminar despliegue

```bash
serverless remove --stage dev
```

## Desarrollo local

```bash
npm run dev
```

Abre http://localhost:5173

## Estructura

```
frontend/
├── public/
├── src/
│   ├── components/    # Layout, navegación
│   ├── pages/         # Páginas de cada módulo
│   ├── services/      # api.js (Axios)
│   ├── styles/        # CSS global
│   ├── App.jsx
│   └── main.jsx
├── index.html
├── vite.config.js
├── package.json
├── serverless.yml
└── README.md
```

---

## Prompt utilizado para la generación

> **Rol/Persona:** Actúa como un programador Full Stack y experto en crear Agentes de IA con servicios de AWS.
>
> **Contexto:** Una empresa de transportes llamada ProntoBus, requiere implementar una plataforma web que le permita gestionar planillas de conductores, flotas de buses, rutas de servicio, asignacion de unidades a conductores y horarios de trabajo, asi como de procesar manualmente pdfs que contienen deudas para generar envio de reportes sobre deudas, conductores con mayores infracciones y un listado de deudas por vencer.
>
> **Tarea/Objetivo:** Crea una web responsiva con estas funcionalidades, considera crear las tablas y columnas necesarias para cumplir con las funcionalidades:
> - Gestión de Flotas: CRUD de buses, alertas de vencimiento de SOAT/Revisiones técnicas.
> - Gestión de Conductores: Perfiles de conductores, licencias, disponibilidad y legajo personal.
> - Planificación y Turnos: Motor de asignación de buses a conductores y gestión de rutas/horarios.
> - Procesamiento de Descansos Medicos: Ingesta de PDFs para extraer texto estructurado de certificados médicos y modificar el horario del conductor afectado automaticamente.
> - Procesamiento de Documentos de Deudas por Infracciones: Ingesta de PDFs para almacenar las deudas extraídas, calcula fechas límite de descuento y genera el ranking de infractores.
> - Comunicaciones: Envío de correos electrónicos para reportes de deudas y alertas de vencimientos.
>
> Además, para las funcionalidades cuarta y quinta crea workflows que usen IA con esas funcionalidades:
> 1. Recibe como entrada estos datos: Ruta a archivo en bucket S3 en formato markdown con instrucciones para IA, Ruta a carpeta en bucket S3 que contenga archivos en formato markdown para evaluar con las instrucciones, Correo donde enviar el archivo con los resultados.
> 2. Por cada archivo debe llamar al Api Agente IA prontobus y enviarle como parametro la ruta del archivo de instrucciones y la ruta del archivo de contenido. El procesamiento lo realizara el Api IA de Groq.
> 3. El resultado del Api Agente IA prontobus (formato json) debe guardarlo en una tabla dynamodb.
> 4. Debe generar un archivo en formato CSV con campos separados por punto y coma (;) y una tabla comparativa con el resultado del Api de todos los archivos evaluados, almacenarlo en el bucket en una carpeta "resultados".
> 5. Debe enviar un correo utilizando el Api de SendGrid adjuntando el archivo CSV anterior.
>
> **Requisitos de la respuesta:**
> - Para la IaC utiliza el framework serverless versión 4 con rol de IAM LabRole existente.
> - Considera que usaremos variables de entorno globales y no archivos .env.
> - Para la web responsiva utiliza React. Utiliza S3 para alojar la web. Automatiza la creación de un bucket S3 público y el despliegue de la web con serverless considerando LabRole.
> - Para el BackEnd crea 3 microservicios (flota, conductores, horarios) usando API Gateway, Lambda y DynamoDB con Python.
> - Para el BackEnd crea 2 microservicios (descansos, deudas) usando API Gateway, Step Functions, DynamoDB, Lambda. Endpoints en API Gateway para ejecutar el workflow de Step Functions de forma asincrona. Lambdas en Python 3.14 con urllib en vez de requests. API IA de Groq con modelo "llama-3.3-70b-versatile".
> - Genera un README.md para la web y para cada microservicio con todas las instrucciones de despliegue automático.
> - Genera colecciones postman para los APIs workflow.
> - Si es mucha información en pantalla de celular para el registro de un nuevo paciente, considera partirlo en pasos.
