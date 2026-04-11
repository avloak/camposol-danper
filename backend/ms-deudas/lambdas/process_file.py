"""
Map iterator: invoca al Agente IA Prontobus por archivo y persiste en DynamoDB.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import json
import uuid
from datetime import datetime
from decimal import Decimal

import boto3

from agente_ia import handler as agente_handler

dynamo = boto3.resource("dynamodb")
TABLE = os.environ["TABLE_DEUDAS"]
table = dynamo.Table(TABLE)


def _to_decimal(obj):
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, list):
        return [_to_decimal(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    return obj


def handler(event, context):
    file_uri = event["file"]
    instrucciones = event["instrucciones_s3"]
    execution_id = event["execution_id"]
    email = event["email"]

    api_event = {
        "body": json.dumps({
            "instrucciones_s3": instrucciones,
            "contenido_s3": file_uri,
        })
    }
    api_resp = agente_handler(api_event, None)

    try:
        api_body = json.loads(api_resp["body"])
    except Exception:
        api_body = {"error": "respuesta invalida del agente"}

    if api_resp.get("statusCode") != 200:
        raise RuntimeError(f"Agente IA falló [{api_resp.get('statusCode')}]: {api_body.get('error', api_body)}")

    item_id = str(uuid.uuid4())
    item = {
        "id": item_id,
        "execution_id": execution_id,
        "archivo": file_uri,
        "instrucciones_s3": instrucciones,
        "email": email,
        "resultado": _to_decimal(api_body.get("resultado", {})),
        "modelo": api_body.get("modelo", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    table.put_item(Item=item)

    return {
        "id": item_id,
        "archivo": file_uri,
        "resultado": api_body.get("resultado", {}),
    }
