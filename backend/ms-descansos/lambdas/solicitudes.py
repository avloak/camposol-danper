"""
CRUD + flujo de aprobación de Solicitudes de Descanso Médico.

Tabla: ms-descansos-{stage}-solicitudes
  id (PK)             string  UUID
  paciente_nombre     string
  paciente_dni        string
  medico_nombre       string
  medico_cmp          string  (Colegio Médico del Perú)
  diagnostico         string
  fecha_inicio        string  YYYY-MM-DD
  fecha_fin           string  YYYY-MM-DD
  dias_descanso       number
  remitente_email     string  (correo de la persona que envió el descanso)
  remitente_nombre    string
  conductor_id        string  (opcional)
  origen              string  (MANUAL | IA_WORKFLOW)
  archivo_origen      string  (opcional - URI S3 si vino del workflow)
  estado              string  PENDIENTE | APROBADO | RECHAZADO
  observaciones       string
  revisado_por        string
  revisado_at         string ISO-8601
  created_at          string ISO-8601
  updated_at          string ISO-8601
"""
import os
import io
import csv
import json
import uuid
import urllib.request
import urllib.error
from datetime import datetime
from decimal import Decimal

import boto3

TABLE = os.environ["TABLE_SOLICITUDES"]
SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
SENDGRID_FROM_EMAIL = os.environ["SENDGRID_FROM_EMAIL"]
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"

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
    return {
        "statusCode": s,
        "headers": {**CORS, "Content-Type": "application/json"},
        "body": json.dumps(b, cls=DecEnc, ensure_ascii=False),
    }


def parse(e):
    try:
        return json.loads(e.get("body") or "{}")
    except json.JSONDecodeError:
        return {}


def now():
    return datetime.utcnow().isoformat() + "Z"


# ---------- SendGrid helper (urllib) ----------

def _row(label: str, value: str) -> str:
    """Fila HTML de la tabla de detalle."""
    return (
        '<tr>'
        '<td style="padding:12px 16px;border-bottom:1px solid #e9ecef;'
        'background:#f8f9fa;font-size:13px;color:#495057;font-weight:600;width:40%;">'
        f'{label}</td>'
        '<td style="padding:12px 16px;border-bottom:1px solid #e9ecef;'
        f'font-size:14px;color:#212529;">{value or "—"}</td>'
        '</tr>'
    )


def send_notification_email(to_email: str, to_name: str, solicitud: dict, accion: str, observaciones: str = ""):
    """
    Envía un correo al remitente del descanso notificando aprobación o rechazo.
    accion = 'APROBADO' | 'RECHAZADO'
    Plantilla HTML responsiva con estilos inline (Gmail/Outlook friendly).
    """
    if not to_email:
        return {"status": "SKIPPED", "reason": "sin email destinatario"}

    if accion == "APROBADO":
        subject = f"✅ [ProntoBus] Descanso médico APROBADO - {solicitud.get('paciente_nombre', '')}"
        grad_from = "#198754"
        grad_to = "#20c997"
        icono = "✅"
        titulo = "Descanso médico APROBADO"
        subtitulo = "Su solicitud ha sido aprobada correctamente"
        mensaje = (
            "Nos complace informarle que el descanso médico solicitado ha sido "
            "<strong>APROBADO</strong> por el área de recursos humanos. "
            "El conductor queda oficialmente relevado de sus turnos durante el periodo indicado."
        )
        badge_color = "#d1e7dd"
        badge_text = "#0f5132"
    else:
        subject = f"❌ [ProntoBus] Descanso médico RECHAZADO - {solicitud.get('paciente_nombre', '')}"
        grad_from = "#dc3545"
        grad_to = "#e35d6a"
        icono = "❌"
        titulo = "Descanso médico RECHAZADO"
        subtitulo = "Su solicitud no ha sido aprobada"
        mensaje = (
            "Lamentamos informarle que el descanso médico solicitado ha sido "
            "<strong>RECHAZADO</strong>. Revise las observaciones del administrador "
            "para más detalle y, de ser necesario, vuelva a presentar la solicitud "
            "adjuntando la documentación adicional requerida."
        )
        badge_color = "#f8d7da"
        badge_text = "#842029"

    obs_block = ""
    if observaciones:
        obs_block = f"""
          <tr>
            <td style="padding:0 32px 20px 32px;">
              <div style="background:#fff3cd;border-left:4px solid #ffc107;border-radius:8px;padding:16px;">
                <div style="font-size:12px;color:#664d03;text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:6px;">
                  📝 Observaciones del administrador
                </div>
                <div style="font-size:14px;color:#664d03;line-height:1.5;">
                  {observaciones}
                </div>
              </div>
            </td>
          </tr>"""

    filas = (
        _row("👤 Paciente", solicitud.get("paciente_nombre", "")) +
        _row("🆔 DNI", solicitud.get("paciente_dni", "")) +
        _row("👨‍⚕️ Médico", solicitud.get("medico_nombre", "")) +
        _row("🏥 CMP", solicitud.get("medico_cmp", "")) +
        _row("📋 Diagnóstico", solicitud.get("diagnostico", "")) +
        _row("📅 Fecha inicio", solicitud.get("fecha_inicio", "")) +
        _row("📅 Fecha fin", solicitud.get("fecha_fin", "")) +
        _row("🔢 Días de descanso", str(solicitud.get("dias_descanso", "")))
    )

    fecha_rev = solicitud.get("revisado_at", "")[:19].replace("T", " ") if solicitud.get("revisado_at") else ""

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{titulo}</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f6fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6fa;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
          <!-- Header con gradiente -->
          <tr>
            <td style="background:linear-gradient(135deg,{grad_from} 0%,{grad_to} 100%);padding:36px 32px 32px 32px;text-align:center;">
              <div style="font-size:56px;line-height:1;margin-bottom:8px;">{icono}</div>
              <h1 style="margin:0 0 6px 0;color:#ffffff;font-size:22px;font-weight:700;letter-spacing:-0.3px;">{titulo}</h1>
              <p style="margin:0;color:rgba(255,255,255,0.92);font-size:14px;">{subtitulo}</p>
            </td>
          </tr>

          <!-- Saludo -->
          <tr>
            <td style="padding:28px 32px 8px 32px;">
              <p style="margin:0 0 12px 0;color:#212529;font-size:15px;">
                Estimado(a) <strong>{to_name or 'usuario'}</strong>,
              </p>
              <p style="margin:0;color:#495057;font-size:14px;line-height:1.6;">
                {mensaje}
              </p>
            </td>
          </tr>

          <!-- Badge de estado -->
          <tr>
            <td style="padding:16px 32px 8px 32px;text-align:center;">
              <div style="display:inline-block;background:{badge_color};color:{badge_text};padding:8px 20px;border-radius:20px;font-size:13px;font-weight:700;letter-spacing:0.5px;">
                ESTADO: {accion}
              </div>
            </td>
          </tr>

          <!-- Tabla de detalle -->
          <tr>
            <td style="padding:20px 32px 8px 32px;">
              <div style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;font-weight:700;margin-bottom:10px;">
                📄 Detalle del certificado
              </div>
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="border:1px solid #e9ecef;border-radius:8px;overflow:hidden;">
                {filas}
              </table>
            </td>
          </tr>
          {obs_block}

          <!-- Info revisión -->
          <tr>
            <td style="padding:8px 32px 24px 32px;">
              <p style="margin:0;color:#adb5bd;font-size:12px;text-align:center;">
                Revisado por <strong>{solicitud.get('revisado_por','admin')}</strong>{f' · {fecha_rev} UTC' if fecha_rev else ''}
              </p>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#212529;padding:24px 32px;text-align:center;">
              <p style="margin:0 0 6px 0;color:#ffffff;font-size:13px;font-weight:600;">🚌 ProntoBus Cloud Platform</p>
              <p style="margin:0;color:#adb5bd;font-size:11px;line-height:1.5;">
                Este es un mensaje automático del sistema.<br>
                Por favor no responder a este correo.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""

    payload = {
        "personalizations": [{
            "to": [{"email": to_email, "name": to_name or to_email}],
            "subject": subject,
        }],
        "from": {"email": SENDGRID_FROM_EMAIL, "name": "ProntoBus"},
        "content": [{"type": "text/html", "value": html}],
    }

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        SENDGRID_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            return {"status": "OK", "http": resp.status, "to": to_email}
    except urllib.error.HTTPError as e:
        return {"status": "ERROR", "http": e.code,
                "detail": e.read().decode("utf-8", "ignore"), "to": to_email}
    except urllib.error.URLError as e:
        return {"status": "ERROR", "detail": str(e.reason), "to": to_email}


# ---------- CRUD ----------

CAMPOS = [
    "paciente_nombre", "paciente_dni",
    "medico_nombre", "medico_cmp",
    "diagnostico",
    "fecha_inicio", "fecha_fin",
    "remitente_email", "remitente_nombre",
    "conductor_id", "archivo_origen", "origen", "observaciones",
]


def _dias(fi: str, ff: str) -> int:
    try:
        a = datetime.strptime(fi, "%Y-%m-%d")
        b = datetime.strptime(ff, "%Y-%m-%d")
        return (b - a).days + 1
    except Exception:
        return 0


def listar(event, context):
    qs = event.get("queryStringParameters") or {}
    estado = qs.get("estado")
    if estado:
        from boto3.dynamodb.conditions import Key
        res = table.query(
            IndexName="estado-index",
            KeyConditionExpression=Key("estado").eq(estado),
        )
    else:
        res = table.scan()
    items = sorted(res.get("Items", []),
                   key=lambda x: x.get("created_at", ""), reverse=True)
    return respond(200, {"items": items, "count": len(items)})


def obtener(event, context):
    sid = event["pathParameters"]["id"]
    res = table.get_item(Key={"id": sid})
    if "Item" not in res:
        return respond(404, {"error": "Solicitud no encontrada"})
    return respond(200, res["Item"])


def crear(event, context):
    data = parse(event)
    for f in ("paciente_nombre", "paciente_dni", "medico_nombre",
              "medico_cmp", "diagnostico", "fecha_inicio", "fecha_fin"):
        if not data.get(f):
            return respond(400, {"error": f"Campo '{f}' es obligatorio"})

    item = {"id": str(uuid.uuid4())}
    for f in CAMPOS:
        item[f] = data.get(f, "")
    item["dias_descanso"] = _dias(item["fecha_inicio"], item["fecha_fin"])
    item["origen"] = data.get("origen", "MANUAL")
    item["estado"] = "PENDIENTE"
    item["revisado_por"] = ""
    item["revisado_at"] = ""
    item["created_at"] = now()
    item["updated_at"] = now()

    table.put_item(Item=item)
    return respond(201, item)


def _actualizar_estado(sid: str, accion: str, data: dict):
    res = table.get_item(Key={"id": sid})
    if "Item" not in res:
        return None, respond(404, {"error": "Solicitud no encontrada"})
    item = res["Item"]
    if item.get("estado") != "PENDIENTE":
        return None, respond(400, {
            "error": f"La solicitud ya fue {item.get('estado')}, no se puede modificar"
        })

    item["estado"] = accion
    item["observaciones"] = data.get("observaciones", item.get("observaciones", ""))
    item["revisado_por"] = data.get("revisado_por", "admin")
    item["revisado_at"] = now()
    item["updated_at"] = now()
    table.put_item(Item=item)
    return item, None


def aprobar(event, context):
    sid = event["pathParameters"]["id"]
    data = parse(event)
    item, err = _actualizar_estado(sid, "APROBADO", data)
    if err:
        return err
    email_result = send_notification_email(
        to_email=item.get("remitente_email", ""),
        to_name=item.get("remitente_nombre", ""),
        solicitud=item,
        accion="APROBADO",
        observaciones=item.get("observaciones", ""),
    )
    return respond(200, {"solicitud": item, "email": email_result})


def rechazar(event, context):
    sid = event["pathParameters"]["id"]
    data = parse(event)
    item, err = _actualizar_estado(sid, "RECHAZADO", data)
    if err:
        return err
    email_result = send_notification_email(
        to_email=item.get("remitente_email", ""),
        to_name=item.get("remitente_nombre", ""),
        solicitud=item,
        accion="RECHAZADO",
        observaciones=item.get("observaciones", ""),
    )
    return respond(200, {"solicitud": item, "email": email_result})


# ---------- Exportar a CSV ----------

CSV_FIELDS = [
    "id", "estado", "origen",
    "paciente_nombre", "paciente_dni",
    "medico_nombre", "medico_cmp",
    "diagnostico",
    "fecha_inicio", "fecha_fin", "dias_descanso",
    "remitente_nombre", "remitente_email",
    "conductor_id", "archivo_origen",
    "observaciones", "revisado_por", "revisado_at",
    "created_at", "updated_at",
]


def exportar_csv(event, context):
    """
    GET /descansos/solicitudes/exportar[?estado=PENDIENTE]
    Devuelve el listado (filtrado opcionalmente) como archivo CSV con
    separador ';' listo para descarga directa desde el navegador.
    """
    qs = event.get("queryStringParameters") or {}
    estado = qs.get("estado")

    if estado:
        from boto3.dynamodb.conditions import Key
        res = table.query(
            IndexName="estado-index",
            KeyConditionExpression=Key("estado").eq(estado),
        )
    else:
        res = table.scan()

    items = sorted(res.get("Items", []),
                   key=lambda x: x.get("created_at", ""), reverse=True)

    buf = io.StringIO()
    buf.write("\ufeff")  # BOM UTF-8 para que Excel lo reconozca
    writer = csv.DictWriter(buf, fieldnames=CSV_FIELDS, delimiter=";",
                            extrasaction="ignore", quoting=csv.QUOTE_MINIMAL)
    writer.writeheader()
    for it in items:
        row = {k: (str(it.get(k, "")) if it.get(k) is not None else "") for k in CSV_FIELDS}
        writer.writerow(row)

    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    sufijo = f"-{estado.lower()}" if estado else ""
    filename = f"solicitudes-descansos{sufijo}-{ts}.csv"

    return {
        "statusCode": 200,
        "headers": {
            **CORS,
            "Content-Type": "text/csv; charset=utf-8",
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
        "body": buf.getvalue(),
    }
