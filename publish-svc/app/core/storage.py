"""
MinIO 文件存储服务
"""
import io
import hashlib
import asyncio
from typing import BinaryIO, Optional
from functools import partial
from fastapi import HTTPException, status
from app.core.config import settings

try:
    from minio import Minio
    from minio.error import S3Error
except ImportError:  # pragma: no cover - depends on optional deployment package
    Minio = None
    S3Error = Exception


class MinIOStorage:
    """MinIO 存储客户端"""
    
    def __init__(self):
        if Minio is None:
            raise RuntimeError("缺少 minio 依赖，请安装 requirements.txt 中的 minio 包")

        self.client = Minio(
            settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_SECURE
        )
        self.bucket = settings.MINIO_BUCKET
        self._ensure_bucket()
    
    def _ensure_bucket(self):
        """确保 bucket 存在"""
        try:
            if not self.client.bucket_exists(self.bucket):
                self.client.make_bucket(self.bucket)
        except S3Error as e:
            print(f"创建 bucket 失败: {e}")
    
    def upload_file(
        self,
        file_data: bytes,
        object_name: str,
        content_type: str = "application/octet-stream"
    ) -> tuple[str, str, str]:
        """
        上传文件到 MinIO
        
        Args:
            file_data: 文件二进制数据
            object_name: 对象名称（路径）
            content_type: 文件类型
            
        Returns:
            tuple: (file_path, md5, sha256)
        """
        # 计算文件哈希
        md5 = hashlib.md5(file_data).hexdigest()
        sha256 = hashlib.sha256(file_data).hexdigest()
        
        # 上传到 MinIO
        file_stream = io.BytesIO(file_data)
        file_size = len(file_data)
        
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                file_stream,
                file_size,
                content_type=content_type
            )
            
            # 返回文件路径（MinIO格式）
            file_path = f"{self.bucket}/{object_name}"
            return file_path, md5, sha256
            
        except S3Error as e:
            raise Exception(f"文件上传失败: {e}")
    
    def download_file(self, object_name: str) -> bytes:
        """
        从 MinIO 下载文件
        
        Args:
            object_name: 对象名称（路径）
            
        Returns:
            bytes: 文件二进制数据
        """
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            return data
        except S3Error as e:
            raise Exception(f"文件下载失败: {e}")
    
    def delete_file(self, object_name: str) -> bool:
        """
        从 MinIO 删除文件
        
        Args:
            object_name: 对象名称（路径）
            
        Returns:
            bool: 是否成功
        """
        try:
            self.client.remove_object(self.bucket, object_name)
            return True
        except S3Error as e:
            print(f"文件删除失败: {e}")
            return False
    
    # 异步方法包装
    async def upload_bytes(
        self,
        object_name: str,
        file_data: bytes,
        content_type: str = "application/octet-stream"
    ) -> tuple[str, str, str]:
        """
        异步上传文件到 MinIO
        
        Args:
            object_name: 对象名称（路径）
            file_data: 文件二进制数据
            content_type: 文件类型
            
        Returns:
            tuple: (file_path, md5, sha256)
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.upload_file, file_data, object_name, content_type)
        )
    
    async def download_file_async(self, object_name: str) -> bytes:
        """
        异步从 MinIO 下载文件
        
        Args:
            object_name: 对象名称（路径）
            
        Returns:
            bytes: 文件二进制数据
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.download_file,
            object_name
        )
    
    async def delete_file_async(self, object_name: str) -> bool:
        """
        异步从 MinIO 删除文件
        
        Args:
            object_name: 对象名称（路径）
            
        Returns:
            bool: 是否成功
        """
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            self.delete_file,
            object_name
        )
    
    def get_file_url(self, object_name: str, expires: int = 3600) -> str:
        """
        获取文件的预签名URL
        
        Args:
            object_name: 对象名称（路径）
            expires: 过期时间（秒）
            
        Returns:
            str: 预签名URL
        """
        try:
            from datetime import timedelta
            url = self.client.presigned_get_object(
                self.bucket,
                object_name,
                expires=timedelta(seconds=expires)
            )
            return url
        except S3Error as e:
            raise Exception(f"获取文件URL失败: {e}")


storage: Optional[MinIOStorage] = None


def get_storage() -> MinIOStorage:
    """获取存储实例依赖"""
    global storage
    if storage is None:
        try:
            storage = MinIOStorage()
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc
    return storage
