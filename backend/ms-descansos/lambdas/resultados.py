"""
Endpoints de resultados del workflow IA de descansos:
  GET /descansos/resultados                → lista CSVs en s3://<bucket>/resultados/
  GET /descansos/resultados/{key+}/download → presigned URL para descargar el CSV

La URL presigned tiene validez de 5 minutos y permite que el navegador
descargue directamente el archivo sin exponer credenciales de AWS.
"""
import os
import json

import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_DESCANSOS"]

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
}


def respond(s, b):
    return {
        "statusCode": s,
        "headers": {**CORS, "Content-Type": "application/json"},
        "body": json.dumps(b, ensure_ascii=False, default=str),
    }


def listar(event, context):
    """Lista los CSVs disponibles en la carpeta /resultados/ del bucket."""
    paginator = s3.get_paginator("list_objects_v2")
    items = []
    for page in paginator.paginate(Bucket=BUCKET, Prefix="resultados/"):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            if not key.endswith(".csv"):
                continue
            items.append({
                "key": key,
                "filename": key.split("/")[-1],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
            })

    items.sort(key=lambda x: x["last_modified"], reverse=True)
    return respond(200, {"items": items, "count": len(items), "bucket": BUCKET})


def descargar(event, context):
    """Devuelve una presigned URL (GET) para descargar el CSV desde el navegador."""
    params = event.get("pathParameters") or {}
    key = params.get("key")
    if not key:
        return respond(400, {"error": "Se requiere la key del archivo"})

    # API Gateway puede pasar el '+' como path, normalizamos:
    if not key.startswith("resultados/"):
        key = f"resultados/{key}"

    try:
        s3.head_object(Bucket=BUCKET, Key=key)
    except Exception:
        return respond(404, {"error": f"Archivo no encontrado: {key}"})

    filename = key.split("/")[-1]
    url = s3.generate_presigned_url(
        "get_object",
        Params={
            "Bucket": BUCKET,
            "Key": key,
            "ResponseContentDisposition": f'attachment; filename="{filename}"',
            "ResponseContentType": "text/csv; charset=utf-8",
        },
        ExpiresIn=300,  # 5 minutos
    )
    return respond(200, {
        "url": url,
        "filename": filename,
        "key": key,
        "expires_in": 300,
    })
