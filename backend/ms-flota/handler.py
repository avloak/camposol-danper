"""
ms-flota - Microservicio CRUD de buses + alertas de vencimiento.
Tabla DynamoDB:
  buses
    id (PK)             string
    placa               string
    marca               string
    modelo              string
    anio                number
    capacidad           number
    soat_vencimiento    string (YYYY-MM-DD)
    revision_tecnica_vencimiento string (YYYY-MM-DD)
    estado              string  (OPERATIVO | MANTENIMIENTO | INACTIVO)
    created_at          string
    updated_at          string
"""

import os
import json
import uuid
from datetime import datetime, date, timedelta
from decimal import Decimal

import boto3
from boto3.dynamodb.conditions import Attr

TABLE = os.environ["TABLE_BUSES"]
dynamo = boto3.resource("dynamodb")
table = dynamo.Table(TABLE)

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


class DecimalEnc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


def respond(status, body):
    return {
        "statusCode": status,
        "headers": {**CORS_HEADERS, "Content-Type": "application/json"},
        "body": json.dumps(body, cls=DecimalEnc, ensure_ascii=False),
    }


def parse_body(event):
    try:
        return json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {}


def now_iso():
    return datetime.utcnow().isoformat() + "Z"


# ---------- Handlers ----------

def listar(event, context):
    res = table.scan()
    return respond(200, {"items": res.get("Items", []), "count": res.get("Count", 0)})


def obtener(event, context):
    bus_id = event["pathParameters"]["id"]
    res = table.get_item(Key={"id": bus_id})
    if "Item" not in res:
        return respond(404, {"error": "Bus no encontrado"})
    return respond(200, res["Item"])


def crear(event, context):
    data = parse_body(event)
    if not data.get("placa"):
        return respond(400, {"error": "El campo 'placa' es obligatorio"})

    item = {
        "id": str(uuid.uuid4()),
        "placa": data.get("placa"),
        "marca": data.get("marca", ""),
        "modelo": data.get("modelo", ""),
        "anio": int(data.get("anio") or 0),
        "capacidad": int(data.get("capacidad") or 0),
        "soat_vencimiento": data.get("soat_vencimiento", ""),
        "revision_tecnica_vencimiento": data.get("revision_tecnica_vencimiento", ""),
        "estado": data.get("estado", "OPERATIVO"),
        "created_at": now_iso(),
        "updated_at": now_iso(),
    }
    table.put_item(Item=item)
    return respond(201, item)


def actualizar(event, context):
    bus_id = event["pathParameters"]["id"]
    data = parse_body(event)

    res = table.get_item(Key={"id": bus_id})
    if "Item" not in res:
        return respond(404, {"error": "Bus no encontrado"})

    item = res["Item"]
    for k in ("placa", "marca", "modelo", "estado",
              "soat_vencimiento", "revision_tecnica_vencimiento"):
        if k in data:
            item[k] = data[k]
    if "anio" in data:
        item["anio"] = int(data["anio"] or 0)
    if "capacidad" in data:
        item["capacidad"] = int(data["capacidad"] or 0)

    item["updated_at"] = now_iso()
    table.put_item(Item=item)
    return respond(200, item)


def eliminar(event, context):
    bus_id = event["pathParameters"]["id"]
    table.delete_item(Key={"id": bus_id})
    return respond(200, {"message": "Bus eliminado", "id": bus_id})


def alertas(event, context):
    """Devuelve buses con SOAT/RT vencidos o por vencer en <= 30 días."""
    qs = event.get("queryStringParameters") or {}
    dias = int(qs.get("dias", 30))
    hoy = date.today()
    limite = hoy + timedelta(days=dias)

    res = table.scan()
    alertas_list = []
    for it in res.get("Items", []):
        for campo, label in (
            ("soat_vencimiento", "SOAT"),
            ("revision_tecnica_vencimiento", "Revisión Técnica"),
        ):
            valor = it.get(campo)
            if not valor:
                continue
            try:
                f = datetime.strptime(valor, "%Y-%m-%d").date()
            except ValueError:
                continue
            if f <= limite:
                alertas_list.append({
                    "bus_id": it.get("id"),
                    "placa": it.get("placa"),
                    "tipo": label,
                    "fecha_vencimiento": valor,
                    "dias_restantes": (f - hoy).days,
                    "estado": "VENCIDO" if f < hoy else "POR_VENCER",
                })

    return respond(200, {"alertas": alertas_list, "count": len(alertas_list)})
