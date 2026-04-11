"""
Genera dos CSVs (separador ;) a partir de los resultados del workflow IA de deudas:
  - resultados/ranking_infracciones-<execution_id>-<ts>.csv
  - resultados/deudas_por_vencer-<execution_id>-<ts>.csv

Cada resultado procesado por el agente IA debe tener la estructura:
  {
    "ranking_infracciones": [ { "dni", "cantidad_infracciones", "deuda_total_soles", "ranking" }, ... ],
    "deudas_por_vencer":    [ { "numero_documento", "dni", "fecha_infraccion", "codigo_infraccion", "deuda_actual_soles" }, ... ]
  }

Las listas de todos los archivos procesados se agregan en un único CSV por sección.
"""
import os
import io
import csv
from datetime import datetime

import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["BUCKET_DEUDAS"]

RANKING_FIELDS = ["ranking", "dni", "cantidad_infracciones", "deuda_total_soles"]
VENCER_FIELDS  = ["numero_documento", "dni", "fecha_infraccion", "codigo_infraccion", "deuda_actual_soles"]


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

    ranking_rows: list[dict] = []
    vencer_rows:  list[dict] = []

    for r in results:
        resultado = r.get("resultado", {})
        archivo   = r.get("archivo", "")

        for item in resultado.get("ranking_infracciones", []):
            ranking_rows.append({**item, "_archivo": archivo})

        for item in resultado.get("deudas_por_vencer", []):
            vencer_rows.append({**item, "_archivo": archivo})

    # Re-sort ranking by deuda_total_soles descending and reassign positions
    try:
        ranking_rows.sort(key=lambda x: float(str(x.get("deuda_total_soles", 0)).replace(",", ".")), reverse=True)
        for i, row in enumerate(ranking_rows, start=1):
            row["ranking"] = i
    except (ValueError, TypeError):
        pass

    ranking_fieldnames = RANKING_FIELDS + ["_archivo"]
    vencer_fieldnames  = VENCER_FIELDS  + ["_archivo"]

    ranking_key = f"resultados/ranking_infracciones-{execution_id}-{ts}.csv"
    vencer_key  = f"resultados/deudas_por_vencer-{execution_id}-{ts}.csv"

    ranking_info = _upload(ranking_key, _make_csv(ranking_rows, ranking_fieldnames))
    vencer_info  = _upload(vencer_key,  _make_csv(vencer_rows,  vencer_fieldnames))

    return {
        "ranking_infracciones": {**ranking_info, "rows": len(ranking_rows)},
        "deudas_por_vencer":    {**vencer_info,  "rows": len(vencer_rows)},
    }
