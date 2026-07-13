"""文件存储，支持本地目录和 S3 兼容服务。"""
import asyncio
import hashlib
from functools import partial
from pathlib import Path

from app.core.config import settings


class ArtifactStorage:
    def __init__(self) -> None:
        self.provider = settings.OBJECT_STORAGE_PROVIDER.lower()
        if self.provider not in {"local", "s3", "minio"}:
            raise RuntimeError(f"不支持的对象存储类型: {self.provider}")

    def put(self, key: str, content: bytes) -> str:
        if self.provider == "local":
            path = Path(settings.LOCAL_STORAGE_DIR).resolve() / key
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
            return key
        client, bucket = self._s3()
        client.put_object(Bucket=bucket, Key=key, Body=content)
        return key

    def get(self, key: str) -> bytes:
        if self.provider == "local":
            path = Path(settings.LOCAL_STORAGE_DIR).resolve() / key
            if not path.is_file():
                raise FileNotFoundError(key)
            return path.read_bytes()
        client, bucket = self._s3()
        return client.get_object(Bucket=bucket, Key=key)["Body"].read()

    def delete(self, key: str) -> None:
        if self.provider == "local":
            path = Path(settings.LOCAL_STORAGE_DIR).resolve() / key
            path.unlink(missing_ok=True)
            return
        client, bucket = self._s3()
        client.delete_object(Bucket=bucket, Key=key)

    def _s3(self):
        try:
            import boto3
        except ImportError as exc:
            raise RuntimeError("使用 S3/MinIO 需要安装 boto3") from exc

        if self.provider == "minio":
            endpoint = settings.S3_ENDPOINT_URL or f"{'https' if settings.MINIO_SECURE else 'http'}://{settings.MINIO_ENDPOINT}"
            access_key = settings.S3_ACCESS_KEY_ID or settings.MINIO_ACCESS_KEY
            secret_key = settings.S3_SECRET_ACCESS_KEY or settings.MINIO_SECRET_KEY
            bucket = settings.MINIO_BUCKET
        else:
            endpoint = settings.S3_ENDPOINT_URL or None
            access_key = settings.S3_ACCESS_KEY_ID
            secret_key = settings.S3_SECRET_ACCESS_KEY
            bucket = settings.S3_BUCKET
        client = boto3.client(
            "s3",
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=settings.S3_REGION,
        )
        try:
            client.head_bucket(Bucket=bucket)
        except Exception:
            create_args = {"Bucket": bucket}
            if self.provider == "s3" and not endpoint and settings.S3_REGION != "us-east-1":
                create_args["CreateBucketConfiguration"] = {"LocationConstraint": settings.S3_REGION}
            client.create_bucket(**create_args)
        return client, bucket


storage = ArtifactStorage()


class MinIOStorage:
    """兼容旧接口的存储适配器，实际提供方由 OBJECT_STORAGE_PROVIDER 决定。"""

    def __init__(self) -> None:
        self.backend = storage
        self.bucket = settings.MINIO_BUCKET if storage.provider == "minio" else settings.S3_BUCKET if storage.provider == "s3" else "local"

    def _key(self, object_name: str) -> str:
        prefix = f"{self.bucket}/"
        return object_name[len(prefix):] if object_name.startswith(prefix) else object_name

    def upload_file(self, file_data: bytes, object_name: str, content_type: str = "application/octet-stream") -> tuple[str, str, str]:
        key = self._key(object_name)
        self.backend.put(key, file_data)
        return f"{self.bucket}/{key}", hashlib.md5(file_data).hexdigest(), hashlib.sha256(file_data).hexdigest()

    def download_file(self, object_name: str) -> bytes:
        return self.backend.get(self._key(object_name))

    def delete_file(self, object_name: str) -> bool:
        self.backend.delete(self._key(object_name))
        return True

    async def upload_bytes(self, object_name: str, file_data: bytes, content_type: str = "application/octet-stream") -> tuple[str, str, str]:
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(None, partial(self.upload_file, file_data, object_name, content_type))

    async def download_file_async(self, object_name: str) -> bytes:
        return await asyncio.get_running_loop().run_in_executor(None, self.download_file, object_name)

    async def delete_file_async(self, object_name: str) -> bool:
        return await asyncio.get_running_loop().run_in_executor(None, self.delete_file, object_name)


_compat_storage: MinIOStorage | None = None


def get_storage() -> MinIOStorage:
    global _compat_storage
    if _compat_storage is None:
        _compat_storage = MinIOStorage()
    return _compat_storage
