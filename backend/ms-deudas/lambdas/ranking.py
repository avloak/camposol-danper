"""
Endpoints adicionales:
  GET /deudas/ranking      - Ranking de conductores con más infracciones.
  GET /deudas/por-vencer   - Listado de deudas con fecha límite próxima.
Lee directamente de DynamoDB.
"""
import os
import json
from datetime import datetime, date, timedelta
from decimal import Decimal

import boto3

dynamo = boto3.resource("dynamodb")
TABLE = os.environ["TABLE_DEUDAS"]
table = dynamo.Table(TABLE)

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "GET,OPTIONS",
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


def _walk(d, results=None):
    """Devuelve flat list de cualquier dict que parezca una infracción/deuda."""
    results = results if results is not None else []
    if isinstance(d, dict):
        if any(k in d for k in ("conductor", "conductor_id", "infractor")):
            results.append(d)
        for v in d.values():
            _walk(v, results)
    elif isinstance(d, list):
        for v in d:
            _walk(v, results)
    return results


def handler(event, context):
    """Ranking simple por número de infracciones agrupado por conductor."""
    res = table.scan()
    counts = {}
    for it in res.get("Items", []):
        infracciones = _walk(it.get("resultado", {}))
        for inf in infracciones:
            key = inf.get("conductor") or inf.get("conductor_id") or inf.get("infractor") or "DESCONOCIDO"
            counts[key] = counts.get(key, 0) + 1

    ranking = sorted(
        [{"conductor": k, "infracciones": v} for k, v in counts.items()],
        key=lambda x: x["infracciones"],
        reverse=True,
    )
    return respond(200, {"ranking": ranking, "total": len(ranking)})


def por_vencer(event, context):
    """Lista deudas con fecha_limite o fecha_vencimiento próxima."""
    qs = event.get("queryStringParameters") or {}
    dias = int(qs.get("dias", 7))
    hoy = date.today()
    limite = hoy + timedelta(days=dias)

    res = table.scan()
    pendientes = []
    for it in res.get("Items", []):
        infs = _walk(it.get("resultado", {}))
        for inf in infs:
            f_str = inf.get("fecha_limite") or inf.get("fecha_vencimiento") or inf.get("fecha_descuento")
            if not f_str:
                continue
            try:
                f = datetime.strptime(str(f_str)[:10], "%Y-%m-%d").date()
            except ValueError:
                continue
            if f <= limite:
                pendientes.append({
                    **inf,
                    "fecha_limite": str(f),
                    "dias_restantes": (f - hoy).days,
                    "archivo": it.get("archivo", ""),
                })

    pendientes.sort(key=lambda x: x.get("dias_restantes", 0))
    return respond(200, {"items": pendientes, "total": len(pendientes)})
