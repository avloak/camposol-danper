"""
Recibe un PDF codificado en base64 y lo guarda directamente en S3.
POST /deudas/upload-url  { "filename": "papeleta.pdf", "content": "<base64>" }
→ { "s3_uri": "s3://bucket/pdfs/papeleta.pdf", "key": "...", "size": 12345 }
"""
import os
import json
import base64
import re

import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_DEUDAS"]
PREFIX = "pdfs/"
MAX_SIZE = 8 * 1024 * 1024  # 8 MB decoded limit

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def respond(s, b):
    return {
        "statusCode": s,
        "headers": {**CORS, "Content-Type": "application/json"},
        "body": json.dumps(b, ensure_ascii=False),
    }


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return respond(400, {"error": "JSON inválido"})

    filename = body.get("filename", "").strip()
    content_b64 = body.get("content", "")

    if not filename:
        return respond(400, {"error": "Campo 'filename' es obligatorio"})
    if not content_b64:
        return respond(400, {"error": "Campo 'content' es obligatorio"})
    if not filename.lower().endswith(".pdf"):
        return respond(400, {"error": "Solo se permiten archivos PDF"})

    try:
        raw = base64.b64decode(content_b64)
    except Exception:
        return respond(400, {"error": "Contenido base64 inválido"})

    if len(raw) > MAX_SIZE:
        return respond(413, {"error": f"Archivo demasiado grande (máx {MAX_SIZE // 1024 // 1024} MB)"})

    safe_name = re.sub(r"[^\w.\-]", "_", filename)
    key = f"{PREFIX}{safe_name}"

    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=raw,
        ContentType="application/pdf",
    )

    return respond(200, {
        "s3_uri": f"s3://{BUCKET}/{key}",
        "key": key,
        "size": len(raw),
    })
