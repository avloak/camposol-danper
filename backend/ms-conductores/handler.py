"""
ms-conductores - Microservicio CRUD de conductores.
Tabla: conductores
  id (PK)              string
  dni                  string
  nombre, apellidos    string
  fecha_nacimiento     string YYYY-MM-DD
  telefono, email      string
  direccion            string
  licencia_numero      string
  licencia_categoria   string  (A-I, A-IIa, A-IIb, A-IIIa, A-IIIb, A-IIIc)
  licencia_emision     string YYYY-MM-DD
  licencia_vencimiento string YYYY-MM-DD
  fecha_ingreso        string
  cargo                string
  salario              number
  contacto_emergencia  string
  contacto_emergencia_telefono string
  disponibilidad       string  (DISPONIBLE | ASIGNADO | DESCANSO | VACACIONES)
  observaciones        string
  created_at, updated_at
"""

import os
import json
import uuid
from datetime import datetime
from decimal import Decimal

import boto3

TABLE = os.environ["TABLE_CONDUCTORES"]
dynamo = boto3.resource("dynamodb")
table = dynamo.Table(TABLE)

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
}


class DecEnc(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return int(o) if o == o.to_integral_value() else float(o)
        return super().default(o)


def respond(s, b):
    return {"statusCode": s,
            "headers": {**CORS, "Content-Type": "application/json"},
            "body": json.dumps(b, cls=DecEnc, ensure_ascii=False)}


def parse(e):
    try:
        return json.loads(e.get("body") or "{}")
    except json.JSONDecodeError:
        return {}


def now():
    return datetime.utcnow().isoformat() + "Z"


CAMPOS = [
    "dni", "nombre", "apellidos", "fecha_nacimiento", "telefono", "email",
    "direccion", "licencia_numero", "licencia_categoria", "licencia_emision",
    "licencia_vencimiento", "fecha_ingreso", "cargo", "contacto_emergencia",
    "contacto_emergencia_telefono", "disponibilidad", "observaciones",
]


def listar(event, context):
    res = table.scan()
    return respond(200, {"items": res.get("Items", []), "count": res.get("Count", 0)})


def obtener(event, context):
    cid = event["pathParameters"]["id"]
    res = table.get_item(Key={"id": cid})
    if "Item" not in res:
        return respond(404, {"error": "Conductor no encontrado"})
    return respond(200, res["Item"])


def crear(event, context):
    data = parse(event)
    if not data.get("dni") or not data.get("nombre"):
        return respond(400, {"error": "Los campos 'dni' y 'nombre' son obligatorios"})

    item = {"id": str(uuid.uuid4())}
    for f in CAMPOS:
        item[f] = data.get(f, "")
    item["salario"] = Decimal(str(data.get("salario") or 0))
    item["disponibilidad"] = data.get("disponibilidad", "DISPONIBLE")
    item["created_at"] = now()
    item["updated_at"] = now()

    table.put_item(Item=item)
    return respond(201, item)


def actualizar(event, context):
    cid = event["pathParameters"]["id"]
    data = parse(event)
    res = table.get_item(Key={"id": cid})
    if "Item" not in res:
        return respond(404, {"error": "Conductor no encontrado"})
    item = res["Item"]
    for f in CAMPOS:
        if f in data:
            item[f] = data[f]
    if "salario" in data:
        item["salario"] = Decimal(str(data["salario"] or 0))
    item["updated_at"] = now()
    table.put_item(Item=item)
    return respond(200, item)


def eliminar(event, context):
    cid = event["pathParameters"]["id"]
    table.delete_item(Key={"id": cid})
    return respond(200, {"message": "Conductor eliminado", "id": cid})


def disponibles(event, context):
    res = table.scan()
    libres = [c for c in res.get("Items", []) if c.get("disponibilidad") == "DISPONIBLE"]
    return respond(200, {"items": libres, "count": len(libres)})
