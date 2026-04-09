# Postman Collections - ProntoBus Workflows

> **Generado con GitHub Copilot**
> **Fecha de creación:** 2026-04-08

Colecciones para probar los APIs de los workflow Step Functions:

- `ms-descansos.postman_collection.json` - Workflow de descansos médicos
- `ms-deudas.postman_collection.json` - Workflow de deudas / infracciones

## Cómo usar

1. Abrir Postman → **Import** → seleccionar el `.json`.
2. En la colección, ir a **Variables** y reemplazar:
   - `baseUrl` con la URL de API Gateway impresa por `serverless info --stage dev`
   - `bucket` con el nombre real del bucket creado (`ms-descansos-dev-bucket-<accountId>`)
3. Antes de probar el workflow, sube a S3:
   - El archivo de instrucciones (`instrucciones/extraer.md`)
   - Los archivos a procesar (`certificados/*.md` o `infracciones/*.md`)
4. Ejecutar el request **1. Iniciar Workflow** → copiar `execution_arn` → pegarlo en la variable `executionArn` para consultar el estado.

## Variables globales (no .env)

Antes del despliegue:

```bash
export GROQ_API_KEY="..."
export SENDGRID_API_KEY="..."
export SENDGRID_FROM_EMAIL="noreply@prontobus.com"
```
