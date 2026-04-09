"""Step 1 - enumerar archivos .md de la carpeta S3 indicada."""
import boto3

s3 = boto3.client("s3")


def parse_s3_uri(uri: str):
    if not uri.startswith("s3://"):
        raise ValueError(f"URI S3 inválida: {uri}")
    rest = uri[5:]
    bucket, _, key = rest.partition("/")
    return bucket, key


def handler(event, context):
    folder_uri = event["contenido_s3"]
    bucket, prefix = parse_s3_uri(folder_uri)
    if prefix and not prefix.endswith("/"):
        prefix += "/"

    paginator = s3.get_paginator("list_objects_v2")
    files = []
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []) or []:
            key = obj["Key"]
            if key.endswith(".md"):
                files.append(f"s3://{bucket}/{key}")

    return {"files": files, "count": len(files), "bucket": bucket, "prefix": prefix}
