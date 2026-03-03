"""
File Service - 文件存储服务
"""
import os
import re
import uuid
import aiofiles
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional, Set

from app.config import settings

logger = logging.getLogger(__name__)

# Allowed MIME types for file uploads
ALLOWED_MIME_TYPES: Set[str] = {
    # Excel files
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",  # .xlsx
    "application/vnd.ms-excel",  # .xls
    "application/octet-stream",  # Sometimes returned for Excel
    # Word files
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",  # .docx
    "application/msword",  # .doc
    # Images
    "image/png",
    "image/jpeg",
    "image/jpg",
    # PDF
    "application/pdf",
}

# Dangerous file patterns
DANGEROUS_PATTERNS = re.compile(r'[<>:"/\\|?*\x00-\x1f]|\.\.\/|\.\.\\')


class FileService:
    """文件上传和管理服务"""

    def __init__(self):
        self.upload_dir = settings.upload_path
        self.result_dir = settings.result_path
        self.max_upload_size = settings.MAX_UPLOAD_SIZE
        self.allowed_extensions = settings.allowed_extensions_list

    async def init_directories(self):
        """初始化存储目录"""
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self.result_dir.mkdir(parents=True, exist_ok=True)

    def _secure_filename(self, filename: str) -> str:
        """
        安全化文件名，防止路径遍历攻击

        Args:
            filename: 原始文件名

        Returns:
            安全的文件名
        """
        # 移除危险字符
        safe_name = DANGEROUS_PATTERNS.sub('_', filename)

        # 仅保留文件名部分（移除路径）
        safe_name = os.path.basename(safe_name)

        # 限制文件名长度
        name, ext = os.path.splitext(safe_name)
        if len(name) > 200:
            name = name[:200]

        return name + ext

    def _validate_extension(self, filename: str) -> bool:
        """验证文件扩展名"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.allowed_extensions

    async def save_upload(self, file, file_id: str) -> Path:
        """
        保存上传的文件

        Args:
            file: UploadFile对象
            file_id: 文件唯一ID

        Returns:
            保存的文件路径

        Raises:
            ValueError: 文件验证失败
        """
        # 验证文件名
        if not file.filename:
            raise ValueError("文件名为空")

        # 验证扩展名
        if not self._validate_extension(file.filename):
            raise ValueError(
                f"不支持的文件类型。允许的类型: {', '.join(self.allowed_extensions)}"
            )

        # 安全化文件名
        safe_filename = self._secure_filename(file.filename)

        # 创建以file_id为名的子目录
        file_dir = self.upload_dir / file_id
        file_dir.mkdir(parents=True, exist_ok=True)

        file_path = file_dir / safe_filename

        # 分块写入，避免内存溢出
        chunk_size = 64 * 1024  # 64KB chunks
        total_size = 0

        async with aiofiles.open(file_path, 'wb') as f:
            while True:
                chunk = await file.read(chunk_size)
                if not chunk:
                    break

                total_size += len(chunk)

                # 检查文件大小
                if total_size > self.max_upload_size:
                    # 清理已写入的文件
                    await file.close()
                    file_path.unlink(missing_ok=True)
                    raise ValueError(
                        f"文件大小超过限制 ({self.max_upload_size // (1024*1024)}MB)"
                    )

                await f.write(chunk)

        logger.info(f"File saved: {file_path} ({total_size} bytes)")
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

        # 安全化文件名
        safe_filename = self._secure_filename(filename)
        file_path = result_dir / safe_filename

        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(content)

        logger.info(f"Result saved: {file_path}")
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

        cleaned_count = 0
        for directory in [self.upload_dir, self.result_dir]:
            if not directory.exists():
                continue
            for item in directory.iterdir():
                if item.is_dir() and item.stat().st_ctime < cutoff:
                    # 删除整个目录
                    import shutil
                    shutil.rmtree(item)
                    cleaned_count += 1

        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} old file directories")