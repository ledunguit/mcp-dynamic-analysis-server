from __future__ import annotations

from typing import Any, Dict
import uuid
import logging

from pydantic import ValidationError as PydanticValidationError

from ..config import load_settings
from ..core.artifact_registry import ArtifactRegistry
from ..core.exceptions import ValidationError
from ..core.r2_client import R2Client, R2Config
from ..models.requests import CreateUploadUrlRequest
from ..models.responses import UploadUrlResponse


def create_upload_url(params: Dict[str, Any]) -> Dict[str, Any]:
    settings = load_settings()
    logger = logging.getLogger("mcp_dynamic_analysis_server")
    try:
        request = CreateUploadUrlRequest.model_validate(params)
    except PydanticValidationError as exc:
        raise ValidationError(str(exc)) from exc

    if request.size_bytes and request.size_bytes > settings.r2_max_upload_bytes:
        raise ValidationError("Requested upload exceeds configured max size")

    if not all(
        [
            settings.r2_endpoint,
            settings.r2_access_key_id,
            settings.r2_secret_access_key,
            settings.r2_bucket,
        ]
    ):
        raise ValidationError("R2 credentials are not configured")

    r2 = R2Client(
        R2Config(
            endpoint=settings.r2_endpoint or "",
            access_key_id=settings.r2_access_key_id or "",
            secret_access_key=settings.r2_secret_access_key or "",
            bucket=settings.r2_bucket or "",
            region=settings.r2_region,
            use_ssl=settings.r2_use_ssl,
            presign_expires_sec=request.expires_sec or settings.r2_presign_expires_sec,
            upload_prefix=settings.r2_upload_prefix,
            request_timeout_sec=settings.r2_healthcheck_timeout_sec,
        )
    )

    registry = ArtifactRegistry(settings.artifacts_dir)
    artifact_id = uuid.uuid4().hex
    key = r2.build_key(artifact_id, request.filename)
    upload_url = r2.presign_put(key=key, content_type=request.content_type)
    download_url = r2.presign_get(key=key)

    record = registry.create_record(
        key=key,
        filename=request.filename,
        content_type=request.content_type,
        size_bytes=request.size_bytes,
        sha256=request.sha256,
        artifact_id=artifact_id,
    )

    logger.info(
        "R2 presign created artifact_id=%s filename=%s size_bytes=%s content_type=%s key=%s expires_in_sec=%s",
        record.artifact_id,
        record.filename,
        record.size_bytes,
        record.content_type,
        record.key,
        request.expires_sec or settings.r2_presign_expires_sec,
    )

    response = UploadUrlResponse(
        artifact_id=record.artifact_id,
        upload_url=upload_url,
        download_url=download_url,
        expires_in_sec=request.expires_sec or settings.r2_presign_expires_sec,
        key=key,
    )
    return response.model_dump()
