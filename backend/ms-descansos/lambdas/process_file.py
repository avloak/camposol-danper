"""
Map iterator: invoca al Agente IA Prontobus por archivo y persiste en DynamoDB.

Adicionalmente, si la IA logra extraer los campos de un certificado médico
(paciente, dni, médico, cmp, diagnóstico, fechas), crea automáticamente
una entrada en la tabla de SOLICITUDES con estado PENDIENTE para que
el administrador pueda aprobarla o rechazarla desde el frontend.
"""
import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

import json
import uuid
from datetime import datetime
from decimal import Decimal

import boto3

from agente_ia import handler as agente_handler  # invoca directamente

dynamo = boto3.resource("dynamodb")
TABLE = os.environ["TABLE_DESCANSOS"]
TABLE_SOL = os.environ.get("TABLE_SOLICITUDES", "")
table = dynamo.Table(TABLE)
table_sol = dynamo.Table(TABLE_SOL) if TABLE_SOL else None


def _to_decimal(obj):
    """Convierte floats a Decimal para DynamoDB."""
    if isinstance(obj, float):
        return Decimal(str(obj))
    if isinstance(obj, list):
        return [_to_decimal(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_decimal(v) for k, v in obj.items()}
    return obj


def _pick(d: dict, *keys, default=""):
    """Devuelve el primer valor no vacío entre las posibles claves."""
    for k in keys:
        v = d.get(k)
        if v not in (None, ""):
            return v
    return default


def _dias(fi, ff):
    try:
        a = datetime.strptime(str(fi)[:10], "%Y-%m-%d")
        b = datetime.strptime(str(ff)[:10], "%Y-%m-%d")
        return (b - a).days + 1
    except Exception:
        return 0


def crear_solicitud_desde_ia(resultado: dict, archivo: str, email: str) -> str:
    """
    Si el JSON devuelto por la IA contiene los datos de un certificado médico,
    crea una solicitud en estado PENDIENTE. Devuelve el id creado o "" si no aplica.
    """
    if not table_sol or not isinstance(resultado, dict):
        return ""

    paciente = _pick(resultado, "paciente_nombre", "paciente", "nombre_paciente", "nombre")
    dni = _pick(resultado, "paciente_dni", "dni", "dni_paciente")
    medico = _pick(resultado, "medico_nombre", "medico", "nombre_medico", "doctor")
    cmp = _pick(resultado, "medico_cmp", "cmp", "colegio_medico")
    diagnostico = _pick(resultado, "diagnostico", "diagnosis", "motivo")
    fi = _pick(resultado, "fecha_inicio", "fecha_descanso_inicio", "desde", "fecha")
    ff = _pick(resultado, "fecha_fin", "fecha_descanso_fin", "hasta", "fecha_termino")
    remitente = _pick(resultado, "remitente_email", "email_remitente", default=email)
    remitente_nombre = _pick(resultado, "remitente_nombre", "enviado_por")

    # Si no logramos extraer lo mínimo, no creamos solicitud
    if not (paciente and dni and (fi or ff)):
        return ""

    sid = str(uuid.uuid4())
    item = {
        "id": sid,
        "paciente_nombre": str(paciente),
        "paciente_dni": str(dni),
        "medico_nombre": str(medico),
        "medico_cmp": str(cmp),
        "diagnostico": str(diagnostico),
        "fecha_inicio": str(fi),
        "fecha_fin": str(ff or fi),
        "dias_descanso": _dias(fi, ff or fi),
        "remitente_email": str(remitente),
        "remitente_nombre": str(remitente_nombre),
        "conductor_id": str(_pick(resultado, "conductor_id", "id_conductor")),
        "origen": "IA_WORKFLOW",
        "archivo_origen": archivo,
        "estado": "PENDIENTE",
        "observaciones": "",
        "revisado_por": "",
        "revisado_at": "",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "updated_at": datetime.utcnow().isoformat() + "Z",
    }
    table_sol.put_item(Item=item)
    return sid


def handler(event, context):
    file_uri = event["file"]
    instrucciones = event["instrucciones_s3"]
    execution_id = event["execution_id"]
    email = event["email"]

    # Llamamos al "Api Agente IA prontobus" (lambda local agente_ia)
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

    resultado = api_body.get("resultado", {}) or {}

    item_id = str(uuid.uuid4())
    item = {
        "id": item_id,
        "execution_id": execution_id,
        "archivo": file_uri,
        "instrucciones_s3": instrucciones,
        "email": email,
        "resultado": _to_decimal(resultado),
        "modelo": api_body.get("modelo", ""),
        "created_at": datetime.utcnow().isoformat() + "Z",
    }
    table.put_item(Item=item)

    # Crea automáticamente una solicitud PENDIENTE para revisión del admin
    solicitud_id = ""
    try:
        solicitud_id = crear_solicitud_desde_ia(resultado, file_uri, email)
    except Exception as e:
        print(f"[process_file] error creando solicitud: {e}")

    return {
        "id": item_id,
        "solicitud_id": solicitud_id,
        "archivo": file_uri,
        "resultado": resultado,
    }
