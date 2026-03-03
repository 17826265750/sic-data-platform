"""
Processor Base - 处理器基类
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, Optional
import traceback

from app.config import settings
from app.services.file_service import FileService


class ProcessorBase(ABC):
    """
    数据处理器基类

    所有具体处理器继承此类，实现process方法
    """

    def __init__(self, job_id: str, params: Dict[str, Any]):
        self.job_id = job_id
        self.params = params
        self.file_service = FileService()
        self.output_dir: Optional[Path] = None
        self.progress_callback = None

    async def init_output_dir(self):
        """初始化输出目录"""
        self.output_dir = await self.file_service.get_result_path(self.job_id)

    def set_progress_callback(self, callback):
        """设置进度回调函数"""
        self.progress_callback = callback

    async def update_progress(self, progress: int, message: str = None):
        """更新进度"""
        if self.progress_callback:
            await self.progress_callback(progress, message)

    @abstractmethod
    async def process(self) -> Dict[str, Any]:
        """
        执行处理逻辑

        Returns:
            处理结果字典，包含输出文件路径等信息
        """
        pass

    async def run(self) -> Dict[str, Any]:
        """
        运行处理器的完整流程

        Returns:
            处理结果
        """
        try:
            await self.init_output_dir()
            result = await self.process()
            return {
                "success": True,
                "output_dir": str(self.output_dir),
                **result
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "traceback": traceback.format_exc()
            }

    def get_input_path(self, file_id: str) -> Optional[Path]:
        """获取输入文件路径"""
        file_info = self.file_service.get_file_info(file_id)
        if file_info:
            return Path(file_info["path"])
        return None

    def generate_output_path(self, filename: str) -> Path:
        """生成输出文件路径"""
        return self.output_dir / filename