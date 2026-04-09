"""
Endpoint POST /descansos/workflow
Body:
  {
    "instrucciones_s3": "s3://bucket/instrucciones.md",
    "contenido_s3":     "s3://bucket/folder/",
    "email":            "destinatario@dominio.com"
  }

Inicia una ejecución asíncrona del Step Function.
"""
import os
import json
import uuid
from datetime import datetime

import boto3

sfn = boto3.client("stepfunctions")
STATE_MACHINE_ARN = os.environ["STATE_MACHINE_ARN"]

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}


def respond(s, b):
    return {"statusCode": s,
            "headers": {**CORS, "Content-Type": "application/json"},
            "body": json.dumps(b, ensure_ascii=False)}


def handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return respond(400, {"error": "JSON inválido"})

    for f in ("instrucciones_s3", "contenido_s3", "email"):
        if not body.get(f):
            return respond(400, {"error": f"Campo '{f}' es obligatorio"})

    execution_id = f"descansos-{uuid.uuid4()}"
    payload = {
        "execution_id": execution_id,
        "instrucciones_s3": body["instrucciones_s3"],
        "contenido_s3": body["contenido_s3"],
        "email": body["email"],
        "started_at": datetime.utcnow().isoformat() + "Z",
    }

    res = sfn.start_execution(
        stateMachineArn=STATE_MACHINE_ARN,
        name=execution_id,
        input=json.dumps(payload),
    )

    return respond(202, {
        "message": "Workflow iniciado",
        "execution_id": execution_id,
        "execution_arn": res["executionArn"],
        "started_at": payload["started_at"],
    })


def status(event, context):
    arn = event["pathParameters"]["executionArn"]
    res = sfn.describe_execution(executionArn=arn)
    return respond(200, {
        "status": res.get("status"),
        "startDate": str(res.get("startDate")),
        "stopDate": str(res.get("stopDate")) if res.get("stopDate") else None,
    })
