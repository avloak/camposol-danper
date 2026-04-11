"""
Genera un CSV (separador ;) con la tabla comparativa de los resultados
de todos los archivos evaluados, lo sube al bucket S3 en /resultados/
y devuelve la ruta.
"""
import os
import io
import csv
import json
from datetime import datetime

import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_DESCANSOS"]


def _flat_keys(d, parent="", out=None):
    out = out if out is not None else {}
    if isinstance(d, dict):
        for k, v in d.items():
            kk = f"{parent}.{k}" if parent else k
            _flat_keys(v, kk, out)
    elif isinstance(d, list):
        out[parent] = json.dumps(d, ensure_ascii=False)
    else:
        out[parent] = d
    return out


def _make_csv(rows: list[dict], fieldnames: list[str]) -> str:
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter=";", extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({k: row.get(k, "") for k in fieldnames})
    return buf.getvalue()


def _upload(key: str, csv_text: str) -> dict:
    s3.put_object(
        Bucket=BUCKET,
        Key=key,
        Body=csv_text.encode("utf-8"),
        ContentType="text/csv; charset=utf-8",
    )
    return {
        "bucket": BUCKET,
        "key": key,
        "s3_uri": f"s3://{BUCKET}/{key}",
        "filename": key.split("/")[-1],
    }


def handler(event, context):
    execution_id = event["execution_id"]
    results = event.get("results", [])
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")

    rows = []
    keys = set()
    for r in results:
        flat = _flat_keys(r.get("resultado", {}))
        flat["archivo"] = r.get("archivo", "")
        flat["id"] = r.get("id", "")
        rows.append(flat)
        keys.update(flat.keys())

    fieldnames = ["id", "archivo"] + sorted(k for k in keys if k not in ("id", "archivo"))

    key = f"resultados/descansos-{execution_id}-{ts}.csv"
    info = _upload(key, _make_csv(rows, fieldnames))

    return {**info, "rows": len(rows)}
