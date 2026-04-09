"""
ms-horarios - Microservicio de horarios, asignaciones y rutas.

Tabla horarios
  id (PK)        string
  conductor_id   string
  bus_id         string
  ruta           string
  fecha          string YYYY-MM-DD
  hora_inicio    string HH:MM
  hora_fin       string HH:MM
  estado         string  PROGRAMADO | EN_CURSO | COMPLETADO | CANCELADO
  created_at, updated_at

Tabla rutas
  id (PK)        string
  nombre         string
  origen         string
  destino        string
  paradas        list<string>
  distancia_km   number
  duracion_min   number
"""

import os
import json
import uuid
from datetime import datetime
from decimal import Decimal

import boto3

TABLE_HORARIOS = os.environ["TABLE_HORARIOS"]
TABLE_RUTAS = os.environ["TABLE_RUTAS"]
dynamo = boto3.resource("dynamodb")
horarios = dynamo.Table(TABLE_HORARIOS)
rutas = dynamo.Table(TABLE_RUTAS)

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


# ---------- Horarios ----------

def listar(event, context):
    res = horarios.scan()
    items = sorted(res.get("Items", []),
                   key=lambda x: (x.get("fecha", ""), x.get("hora_inicio", "")))
    return respond(200, {"items": items, "count": len(items)})


def obtener(event, context):
    hid = event["pathParameters"]["id"]
    res = horarios.get_item(Key={"id": hid})
    if "Item" not in res:
        return respond(404, {"error": "Horario no encontrado"})
    return respond(200, res["Item"])


def crear(event, context):
    data = parse(event)
    for f in ("conductor_id", "bus_id", "fecha"):
        if not data.get(f):
            return respond(400, {"error": f"Campo '{f}' obligatorio"})

    item = {
        "id": str(uuid.uuid4()),
        "conductor_id": data.get("conductor_id"),
        "bus_id": data.get("bus_id"),
        "ruta": data.get("ruta", ""),
        "fecha": data.get("fecha"),
        "hora_inicio": data.get("hora_inicio", ""),
        "hora_fin": data.get("hora_fin", ""),
        "estado": data.get("estado", "PROGRAMADO"),
        "created_at": now(),
        "updated_at": now(),
    }
    horarios.put_item(Item=item)
    return respond(201, item)


def actualizar(event, context):
    hid = event["pathParameters"]["id"]
    data = parse(event)
    res = horarios.get_item(Key={"id": hid})
    if "Item" not in res:
        return respond(404, {"error": "Horario no encontrado"})
    item = res["Item"]
    for f in ("conductor_id", "bus_id", "ruta", "fecha",
              "hora_inicio", "hora_fin", "estado"):
        if f in data:
            item[f] = data[f]
    item["updated_at"] = now()
    horarios.put_item(Item=item)
    return respond(200, item)


def eliminar(event, context):
    hid = event["pathParameters"]["id"]
    horarios.delete_item(Key={"id": hid})
    return respond(200, {"message": "Horario eliminado", "id": hid})


def asignar_automatico(event, context):
    """
    Motor simple de asignación: dado un set de buses + conductores disponibles
    y una lista de rutas, crea las asignaciones del día.
    Body:
      {
        "fecha": "2026-04-09",
        "asignaciones": [
          {"conductor_id": "...", "bus_id": "...", "ruta": "...",
           "hora_inicio": "06:00", "hora_fin": "14:00"},
          ...
        ]
      }
    """
    data = parse(event)
    fecha = data.get("fecha")
    asigns = data.get("asignaciones", [])
    if not fecha or not asigns:
        return respond(400, {"error": "Se requiere 'fecha' y 'asignaciones'"})

    creados = []
    for a in asigns:
        item = {
            "id": str(uuid.uuid4()),
            "conductor_id": a.get("conductor_id"),
            "bus_id": a.get("bus_id"),
            "ruta": a.get("ruta", ""),
            "fecha": fecha,
            "hora_inicio": a.get("hora_inicio", ""),
            "hora_fin": a.get("hora_fin", ""),
            "estado": "PROGRAMADO",
            "created_at": now(),
            "updated_at": now(),
        }
        horarios.put_item(Item=item)
        creados.append(item)

    return respond(201, {"creados": creados, "count": len(creados)})


# ---------- Rutas ----------

def rutas_listar(event, context):
    res = rutas.scan()
    return respond(200, {"items": res.get("Items", []), "count": res.get("Count", 0)})


def rutas_crear(event, context):
    data = parse(event)
    if not data.get("nombre"):
        return respond(400, {"error": "Campo 'nombre' obligatorio"})
    item = {
        "id": str(uuid.uuid4()),
        "nombre": data.get("nombre"),
        "origen": data.get("origen", ""),
        "destino": data.get("destino", ""),
        "paradas": data.get("paradas", []),
        "distancia_km": Decimal(str(data.get("distancia_km") or 0)),
        "duracion_min": int(data.get("duracion_min") or 0),
        "created_at": now(),
    }
    rutas.put_item(Item=item)
    return respond(201, item)
