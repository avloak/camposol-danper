"""
API Agente IA Prontobus (especialización: descansos médicos).
Recibe la ruta de un archivo de instrucciones y la ruta de un archivo de contenido,
ambos en S3 y formato Markdown. Llama al API de Groq (llama-3.3-70b-versatile)
y devuelve el resultado estructurado en JSON.

POST /agente-ia/descansos
Body:
  {
    "instrucciones_s3": "s3://bucket/instrucciones.md",
    "contenido_s3":     "s3://bucket/cert/cert001.md"
  }
"""
import os
import json
import urllib.request
import urllib.error

import boto3

s3 = boto3.client("s3")

GROQ_API_KEY = os.environ["GROQ_API_KEY"]
GROQ_MODEL = os.environ.get("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

CORS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,Authorization",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}


def respond(s, b):
    return {"statusCode": s,
            "headers": {**CORS, "Content-Type": "application/json"},
            "body": json.dumps(b, ensure_ascii=False)}


def parse_s3_uri(uri: str):
    if not uri.startswith("s3://"):
        raise ValueError(f"URI S3 inválida: {uri}")
    rest = uri[5:]
    bucket, _, key = rest.partition("/")
    return bucket, key


def read_s3_text(uri: str) -> str:
    bucket, key = parse_s3_uri(uri)
    obj = s3.get_object(Bucket=bucket, Key=key)
    return obj["Body"].read().decode("utf-8")


def call_groq(system_prompt: str, user_content: str) -> dict:
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.1,
        "response_format": {"type": "json_object"},
    }
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        GROQ_URL,
        data=data,
        method="POST",
        headers={
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=45) as resp:
            body = resp.read().decode("utf-8")
            parsed = json.loads(body)
            content = parsed["choices"][0]["message"]["content"]
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                return {"raw": content}
    except urllib.error.HTTPError as e:
        return {"error": f"Groq HTTP {e.code}", "detail": e.read().decode("utf-8", "ignore")}
    except urllib.error.URLError as e:
        return {"error": f"Groq URL error: {e.reason}"}


def handler(event, context):
    # Permite invocación HTTP o invocación directa desde Step Functions / otra Lambda
    if isinstance(event, dict) and event.get("body"):
        try:
            body = json.loads(event["body"])
        except json.JSONDecodeError:
            return respond(400, {"error": "JSON inválido"})
    else:
        body = event or {}

    instr = body.get("instrucciones_s3")
    cont = body.get("contenido_s3")
    if not instr or not cont:
        return respond(400, {"error": "Faltan 'instrucciones_s3' o 'contenido_s3'"})

    try:
        instrucciones = read_s3_text(instr)
        contenido = read_s3_text(cont)
    except Exception as e:
        return respond(500, {"error": f"Error leyendo S3: {e}"})

    system_prompt = (
        "Eres un asistente experto en interpretar certificados médicos de descanso "
        "para conductores de transporte público. Tu única salida debe ser JSON válido. "
        "Sigue al pie de la letra las instrucciones del usuario.\n\n"
        "INSTRUCCIONES:\n" + instrucciones
    )

    result = call_groq(system_prompt, contenido)

    return respond(200, {
        "instrucciones_s3": instr,
        "contenido_s3": cont,
        "modelo": GROQ_MODEL,
        "resultado": result,
    })
