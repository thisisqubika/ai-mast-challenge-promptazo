"""S3 media storage backend.

Used when settings.media_storage_backend == "s3". Objects are written to the
configured bucket and served publicly via CloudFront (settings.media_base_url).
Credentials come from the ambient AWS chain (App Runner instance role in prod),
so no static keys are needed.
"""

from __future__ import annotations

from pathlib import Path

import boto3

from app.core.config import settings

_client = None


def _s3():
    global _client
    if _client is None:
        _client = boto3.client("s3", region_name=settings.aws_region)
    return _client


def _public_url(key: str) -> str:
    return f"{settings.media_base_url.rstrip('/')}/{key}"


def upload_bytes(key: str, content_type: str, data: bytes) -> str:
    """Upload raw bytes, return the public (CloudFront) URL."""
    _s3().put_object(
        Bucket=settings.s3_bucket, Key=key, Body=data, ContentType=content_type
    )
    return _public_url(key)


def upload_file(key: str, content_type: str, path: Path) -> str:
    """Upload a local file, return the public (CloudFront) URL."""
    _s3().upload_file(
        str(path), settings.s3_bucket, key, ExtraArgs={"ContentType": content_type}
    )
    return _public_url(key)


def download_to(key: str, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    _s3().download_file(settings.s3_bucket, key, str(dest))


def key_from_url(url: str) -> str | None:
    """Reverse of _public_url: CloudFront URL → S3 key, or None if not ours."""
    base = settings.media_base_url.rstrip("/")
    if base and url.startswith(base + "/"):
        return url[len(base) + 1:]
    return None
