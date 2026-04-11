"""
Envía el CSV generado al correo configurado vía SendGrid (urllib).
Utiliza una plantilla HTML responsiva con branding ProntoBus.
"""
import os
import json
import base64
import urllib.request
import urllib.error
from datetime import datetime

import boto3

s3 = boto3.client("s3")

SENDGRID_API_KEY = os.environ["SENDGRID_API_KEY"]
SENDGRID_FROM_EMAIL = os.environ["SENDGRID_FROM_EMAIL"]
SENDGRID_URL = "https://api.sendgrid.com/v3/mail/send"


def _build_html(execution_id: str, ranking_rows: int, vencer_rows: int) -> str:
    ahora = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Reporte Deudas e Infracciones</title>
</head>
<body style="margin:0;padding:0;background-color:#f4f6fa;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;">
  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background-color:#f4f6fa;padding:24px 12px;">
    <tr>
      <td align="center">
        <table role="presentation" width="600" cellpadding="0" cellspacing="0" border="0" style="max-width:600px;width:100%;background-color:#ffffff;border-radius:12px;overflow:hidden;box-shadow:0 4px 16px rgba(0,0,0,0.08);">
          <!-- Header gradiente (tonos rojo/naranja para deudas) -->
          <tr>
            <td style="background:linear-gradient(135deg,#dc3545 0%,#fd7e14 100%);padding:32px 32px 28px 32px;text-align:center;">
              <div style="font-size:44px;line-height:1;">💰</div>
              <h1 style="margin:12px 0 4px 0;color:#ffffff;font-size:24px;font-weight:700;letter-spacing:-0.3px;">ProntoBus</h1>
              <p style="margin:0;color:rgba(255,255,255,0.92);font-size:14px;">Reporte de Deudas e Infracciones</p>
            </td>
          </tr>

          <!-- Título sección -->
          <tr>
            <td style="padding:32px 32px 8px 32px;">
              <h2 style="margin:0 0 8px 0;color:#212529;font-size:20px;font-weight:600;">📊 Procesamiento completado</h2>
              <p style="margin:0;color:#6c757d;font-size:14px;line-height:1.6;">
                El workflow de IA finalizó exitosamente. Adjunto encontrarás dos archivos CSV con el
                detalle extraído por el modelo <strong>Llama 3.3 70B</strong>:
                el ranking de infractores y las deudas próximas a vencer.
              </p>
            </td>
          </tr>

          <!-- Stat cards -->
          <tr>
            <td style="padding:20px 32px 8px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0">
                <tr>
                  <td width="33%" style="padding:4px;">
                    <div style="background:#fff3cd;border-left:4px solid #ffc107;border-radius:8px;padding:14px;">
                      <div style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Ranking</div>
                      <div style="font-size:22px;color:#664d03;font-weight:700;margin-top:4px;">{ranking_rows} filas</div>
                    </div>
                  </td>
                  <td width="33%" style="padding:4px;">
                    <div style="background:#f8d7da;border-left:4px solid #dc3545;border-radius:8px;padding:14px;">
                      <div style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Por Vencer</div>
                      <div style="font-size:22px;color:#842029;font-weight:700;margin-top:4px;">{vencer_rows} filas</div>
                    </div>
                  </td>
                  <td width="33%" style="padding:4px;">
                    <div style="background:#d1e7dd;border-left:4px solid #198754;border-radius:8px;padding:14px;">
                      <div style="font-size:11px;color:#6c757d;text-transform:uppercase;letter-spacing:0.5px;font-weight:600;">Estado</div>
                      <div style="font-size:14px;color:#0f5132;font-weight:700;margin-top:4px;">✓ Éxito</div>
                    </div>
                  </td>
                </tr>
              </table>
            </td>
          </tr>

          <!-- Metadatos -->
          <tr>
            <td style="padding:20px 32px;">
              <table role="presentation" width="100%" cellpadding="0" cellspacing="0" border="0" style="background:#f8f9fa;border-radius:8px;">
                <tr><td style="padding:12px 16px;border-bottom:1px solid #e9ecef;font-size:13px;color:#495057;"><strong>📋 Ejecución:</strong> <span style="color:#6c757d;font-family:monospace;">{execution_id}</span></td></tr>
                <tr><td style="padding:12px 16px;font-size:13px;color:#495057;"><strong>🕐 Fecha:</strong> <span style="color:#6c757d;">{ahora}</span></td></tr>
              </table>
            </td>
          </tr>

          <!-- Aviso importante -->
          <tr>
            <td style="padding:0 32px 20px 32px;">
              <div style="background:#fff3cd;border-radius:8px;padding:16px;border-left:4px solid #ffc107;">
                <p style="margin:0;color:#664d03;font-size:13px;line-height:1.5;">
                  <strong>⚠️ Importante:</strong> Revisa las fechas límite de descuento para aplicar
                  los beneficios a tiempo y evitar recargos en las multas de tránsito.
                </p>
              </div>
            </td>
          </tr>

          <!-- Aviso adjuntos -->
          <tr>
            <td style="padding:0 32px 24px 32px;">
              <div style="background:#cfe2ff;border-radius:8px;padding:16px;text-align:center;">
                <div style="font-size:24px;margin-bottom:4px;">📎</div>
                <p style="margin:0;color:#084298;font-size:14px;font-weight:600;">
                  Se adjuntan <strong>2 archivos CSV</strong>: ranking de infractores y deudas por vencer.
                </p>
              </div>
            </td>
          </tr>

          <!-- Footer -->
          <tr>
            <td style="background:#212529;padding:24px 32px;text-align:center;">
              <p style="margin:0 0 6px 0;color:#ffffff;font-size:13px;font-weight:600;">ProntoBus Cloud Platform</p>
              <p style="margin:0;color:#adb5bd;font-size:11px;">
                Mensaje automático del sistema. Por favor no responder a este correo.
              </p>
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>"""


def handler(event, context):
    csv_meta = event["csv"]
    email = event["email"]
    execution_id = event["execution_id"]

    ranking_meta = csv_meta["ranking_infracciones"]
    vencer_meta  = csv_meta["deudas_por_vencer"]

    def _encode(meta):
        obj = s3.get_object(Bucket=meta["bucket"], Key=meta["key"])
        return base64.b64encode(obj["Body"].read()).decode("utf-8")

    html = _build_html(
        execution_id=execution_id,
        ranking_rows=ranking_meta.get("rows", 0),
        vencer_rows=vencer_meta.get("rows", 0),
    )

    payload = {
        "personalizations": [{
            "to": [{"email": email}],
            "subject": f"💰 [ProntoBus] Reporte Deudas / Infracciones - {execution_id}",
        }],
        "from": {"email": SENDGRID_FROM_EMAIL, "name": "ProntoBus"},
        "content": [{"type": "text/html", "value": html}],
        "attachments": [
            {
                "content": _encode(ranking_meta),
                "filename": ranking_meta["filename"],
                "type": "text/csv",
                "disposition": "attachment",
            },
            {
                "content": _encode(vencer_meta),
                "filename": vencer_meta["filename"],
                "type": "text/csv",
                "disposition": "attachment",
            },
        ],
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
        with urllib.request.urlopen(req, timeout=30) as resp:
            return {
                "status": "OK",
                "http": resp.status,
                "to": email,
                "ranking_csv": ranking_meta["s3_uri"],
                "vencer_csv": vencer_meta["s3_uri"],
            }
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "ignore")
        raise RuntimeError(f"SendGrid HTTP {e.code}: {detail}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"SendGrid connection error: {e.reason}")
