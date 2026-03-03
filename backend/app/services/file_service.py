"""
File Service - 文件存储服务
"""
import os
import uuid
import aiofiles
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from app.config import settings


class FileService:
    """文件上传和管理服务"""

    def __init__(self):
        self.upload_dir = settings.upload_path
        self.result_dir = settings.result_path

    async def init_directories(self):
        """初始化存储目录"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload(self, file, file_id: str) -> Path:
        """
        保存上传的文件

        Args:
            file: UploadFile对象
            file_id: 文件唯一ID

        Returns:
            保存的文件路径
        """
        # 创建以file_id为名的子目录
        file_dir = self.upload_dir / file_id
        file_dir.mkdir(parents=True, exist_ok=True)

        # 保存文件
        file_path = file_dir / file.filename
        async with aiofiles.open(file_path, 'wb') as f:
            content = await file.read()
            await f.write(content)

        return file_path

    async def get_file_info(self, file_id: str) -> Optional[Dict]:
        """
        获取文件信息

        Args:
            file_id: 文件ID

        Returns:
            文件信息字典，如果不存在返回None
        """
        file_dir = self.upload_dir / file_id
        if not file_dir.exists():
            return None

        # 查找目录中的文件
        files = list(file_dir.glob('*'))
        if not files:
            return None

        file_path = files[0]
        stat = file_path.stat()

        return {
            "file_id": file_id,
            "filename": file_path.name,
            "path": str(file_path),
            "size": stat.st_size,
            "uploaded_at": datetime.fromtimestamp(stat.st_ctime)
        }

    async def save_result(self, job_id: str, filename: str, content: bytes) -> Path:
        """
        保存处理结果文件

        Args:
            job_id: 任务ID
            filename: 文件名
            content: 文件内容

        Returns:
            保存的文件路径
        """
        result_dir = self.result_dir / job_id
        result_dir.mkdir(parents=True, exist_ok=True)

        file_path = result_dir / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        return file_path

    async def get_result_path(self, job_id: str) -> Path:
        """获取结果目录路径"""
        result_dir = self.result_dir / job_id
        result_dir.mkdir(parents=True, exist_ok=True)
        return result_dir

    async def cleanup_old_files(self, days: int = 7):
        """
        清理旧文件

        Args:
            days: 保留天数
        """
        cutoff = datetime.now().timestamp() - (days * 24 * 60 * 60)

        for directory in [self.upload_dir, self.result_dir]:
            for item in directory.iterdir():
                if item.is_dir() and item.stat().st_ctime < cutoff:
                    # 删除整个目录
                    import shutil
                    shutil.rmtree(item)