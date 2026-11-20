"""
FileStorageService — S3-compatible object storage abstraction.
Supports:
  1. "local" (default) — stores files in data/notes/ and data/submissions/.
  2. "s3" — stores files in MinIO / AWS S3 buckets with signed URLs.
"""
import hashlib
from pathlib import Path
from typing import Optional, Tuple
from config import settings


class FileStorageService:
    def __init__(self):
        self.backend = settings.STORAGE_BACKEND
        self.local_base = settings.BASE_DIR / "data"

    def compute_sha256(self, data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    async def save_file(
        self,
        category: str,  # "notes" or "submissions"
        folder_id: int,  # course_id or assignment_id
        filename: str,
        data: bytes,
    ) -> Tuple[str, str]:
        """
        Saves file data and returns (storage_path_or_key, sha256_checksum).
        Preserves backward compatibility with existing local paths.
        """
        checksum = self.compute_sha256(data)

        if self.backend == "s3" and settings.S3_ENDPOINT_URL:
            # S3 / MinIO backend
            try:
                import boto3
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                )
                bucket = (
                    settings.S3_BUCKET_NOTES
                    if category == "notes"
                    else settings.S3_BUCKET_SUBMISSIONS
                )
                key = f"{folder_id}/{filename}"
                s3.put_object(Bucket=bucket, Key=key, Body=data)
                return f"s3://{bucket}/{key}", checksum
            except Exception as e:
                # Graceful fallback to local
                pass

        # Local filesystem backend (default)
        dest_dir = self.local_base / category / str(folder_id)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / filename
        dest_path.write_bytes(data)
        return str(dest_path), checksum

    async def read_file(self, storage_path_or_key: str) -> bytes:
        """Reads file data from either S3 or local path."""
        if storage_path_or_key.startswith("s3://") and settings.S3_ENDPOINT_URL:
            try:
                import boto3
                parts = storage_path_or_key[5:].split("/", 1)
                bucket, key = parts[0], parts[1]
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                )
                response = s3.get_object(Bucket=bucket, Key=key)
                return response["Body"].read()
            except Exception:
                pass

        # Fallback to local file read
        p = Path(storage_path_or_key)
        if not p.exists():
            raise FileNotFoundError(f"File not found: {storage_path_or_key}")
        return p.read_bytes()

    def generate_access_url(self, storage_path_or_key: str, expires_in_seconds: int = 3600) -> str:
        """Generates pre-signed URL for S3 or local API download URL."""
        if storage_path_or_key.startswith("s3://") and settings.S3_ENDPOINT_URL:
            try:
                import boto3
                parts = storage_path_or_key[5:].split("/", 1)
                bucket, key = parts[0], parts[1]
                s3 = boto3.client(
                    "s3",
                    endpoint_url=settings.S3_ENDPOINT_URL,
                    aws_access_key_id=settings.S3_ACCESS_KEY,
                    aws_secret_access_key=settings.S3_SECRET_KEY,
                )
                return s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": bucket, "Key": key},
                    ExpiresIn=expires_in_seconds,
                )
            except Exception:
                pass
        return f"/api/files/download?path={storage_path_or_key}"
