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


def handler(event, context):
    execution_id = event["execution_id"]
    results = event.get("results", [])

    rows = []
    keys = set()
    for r in results:
        flat = _flat_keys(r.get("resultado", {}))
        flat["archivo"] = r.get("archivo", "")
        flat["id"] = r.get("id", "")
        rows.append(flat)
        keys.update(flat.keys())

    fieldnames = ["id", "archivo"] + sorted(k for k in keys if k not in ("id", "archivo"))

    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, delimiter=";")
    writer.writeheader()
    for r in rows:
        writer.writerow({k: r.get(k, "") for k in fieldnames})

    csv_text = buf.getvalue()
    ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    key = f"resultados/descansos-{execution_id}-{ts}.csv"
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
        "rows": len(rows),
        "csv_b64_len": len(csv_text),
    }
