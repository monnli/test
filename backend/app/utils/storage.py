"""统一文件存储抽象层。

支持两种后端：
- local：本地磁盘（默认，无需任何依赖）
- minio：MinIO 对象存储（仅当 STORAGE_BACKEND=minio 时启用）

使用：
    from app.utils.storage import get_storage
    storage = get_storage()
    storage.save("videos/abc.mp4", file_bytes)
    url = storage.get_url("videos/abc.mp4")
"""

from __future__ import annotations

import os
import shutil
from abc import ABC, abstractmethod
from pathlib import Path
from typing import BinaryIO

from flask import current_app


class StorageBackend(ABC):
    @abstractmethod
    def save(self, key: str, data: bytes | BinaryIO) -> str:
        """保存文件，返回访问 URL/相对路径。"""

    @abstractmethod
    def open(self, key: str) -> bytes:
        """读取文件原始字节。"""

    @abstractmethod
    def delete(self, key: str) -> None:
        """删除文件。"""

    @abstractmethod
    def exists(self, key: str) -> bool:
        """判断文件是否存在。"""

    @abstractmethod
    def get_url(self, key: str) -> str:
        """获取访问 URL。"""

    @abstractmethod
    def get_path(self, key: str) -> str | None:
        """对于本地存储返回绝对路径；对象存储返回 None。"""


class LocalStorage(StorageBackend):
    def __init__(self, root: Path):
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, key: str) -> Path:
        return self.root / key.lstrip("/")

    def save(self, key: str, data: bytes | BinaryIO) -> str:
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(data, (bytes, bytearray)):
            path.write_bytes(bytes(data))
        else:
            with path.open("wb") as fout:
                shutil.copyfileobj(data, fout)
        return self.get_url(key)

    def open(self, key: str) -> bytes:
        return self._path(key).read_bytes()

    def delete(self, key: str) -> None:
        try:
            self._path(key).unlink()
        except FileNotFoundError:
            pass

    def exists(self, key: str) -> bool:
        return self._path(key).exists()

    def get_url(self, key: str) -> str:
        return f"/storage/{key.lstrip('/')}"

    def get_path(self, key: str) -> str | None:
        return str(self._path(key))


class MinioStorage(StorageBackend):
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool, bucket: str):
        from minio import Minio  # 延迟导入

        self.client = Minio(endpoint, access_key=access_key, secret_key=secret_key, secure=secure)
        self.bucket = bucket
        if not self.client.bucket_exists(bucket):
            self.client.make_bucket(bucket)

    def save(self, key: str, data: bytes | BinaryIO) -> str:
        from io import BytesIO

        if isinstance(data, (bytes, bytearray)):
            stream = BytesIO(bytes(data))
            length = len(data)
        else:
            stream = data
            stream.seek(0, os.SEEK_END)
            length = stream.tell()
            stream.seek(0)
        self.client.put_object(self.bucket, key, stream, length)
        return self.get_url(key)

    def open(self, key: str) -> bytes:
        resp = self.client.get_object(self.bucket, key)
        try:
            return resp.read()
        finally:
            resp.close()
            resp.release_conn()

    def delete(self, key: str) -> None:
        self.client.remove_object(self.bucket, key)

    def exists(self, key: str) -> bool:
        try:
            self.client.stat_object(self.bucket, key)
            return True
        except Exception:  # noqa: BLE001
            return False

    def get_url(self, key: str) -> str:
        # 简化：返回 minio 路径占位；实际可生成预签名 URL
        return f"minio://{self.bucket}/{key}"

    def get_path(self, key: str) -> str | None:
        return None


_storage_instance: StorageBackend | None = None


def get_storage() -> StorageBackend:
    """获取单例存储实例，根据 STORAGE_BACKEND 配置切换。"""
    global _storage_instance
    if _storage_instance is not None:
        return _storage_instance

    backend = current_app.config.get("STORAGE_BACKEND", "local")
    if backend == "minio":
        _storage_instance = MinioStorage(
            endpoint=current_app.config["MINIO_ENDPOINT"],
            access_key=current_app.config["MINIO_ACCESS_KEY"],
            secret_key=current_app.config["MINIO_SECRET_KEY"],
            secure=current_app.config["MINIO_SECURE"],
            bucket=current_app.config["MINIO_BUCKET_VIDEOS"],
        )
    else:
        _storage_instance = LocalStorage(current_app.config["LOCAL_STORAGE_DIR"])
    return _storage_instance


def reset_storage() -> None:
    """测试时重置实例。"""
    global _storage_instance
    _storage_instance = None
