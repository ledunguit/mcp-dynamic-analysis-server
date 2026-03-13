from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .exceptions import ValidationError


@dataclass(frozen=True)
class R2Config:
    endpoint: str
    access_key_id: str
    secret_access_key: str
    bucket: str
    region: str = "auto"
    use_ssl: bool = True
    presign_expires_sec: int = 900
    upload_prefix: str = "uploads"
    request_timeout_sec: int = 5


class R2Client:
    def __init__(self, config: R2Config) -> None:
        try:
            import boto3
            from botocore.config import Config
            from botocore.exceptions import ClientError
        except Exception as exc:  # pragma: no cover - runtime guard
            raise ValidationError("boto3 is required for R2 integration") from exc

        self._client_error = ClientError
        self._config = config
        self._client = boto3.client(
            "s3",
            endpoint_url=config.endpoint,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name=config.region,
            use_ssl=config.use_ssl,
            config=Config(
                signature_version="s3v4",
                s3={"addressing_style": "path"},
                connect_timeout=config.request_timeout_sec,
                read_timeout=config.request_timeout_sec,
                retries={"max_attempts": 2},
            ),
        )

    def build_key(self, artifact_id: str, filename: str) -> str:
        safe_name = filename.replace("/", "_")
        return f"{self._config.upload_prefix}/{artifact_id}/{safe_name}"

    def presign_put(self, key: str, content_type: Optional[str]) -> str:
        params = {"Bucket": self._config.bucket, "Key": key}
        if content_type:
            params["ContentType"] = content_type
        return self._client.generate_presigned_url(
            "put_object",
            Params=params,
            ExpiresIn=self._config.presign_expires_sec,
        )

    def presign_get(self, key: str) -> str:
        return self._client.generate_presigned_url(
            "get_object",
            Params={"Bucket": self._config.bucket, "Key": key},
            ExpiresIn=self._config.presign_expires_sec,
        )

    def health_check(self) -> tuple[bool, str | None]:
        try:
            self._client.head_bucket(Bucket=self._config.bucket)
            return True, None
        except self._client_error as exc:
            return False, str(exc)
        except Exception as exc:  # pragma: no cover - defensive
            return False, str(exc)
