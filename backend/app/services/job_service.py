"""
Job Service - 任务管理服务
"""
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional
from redis.asyncio import from_url as async_from_url
import uuid

from app.config import settings
from app.models.schemas import JobStatus

logger = logging.getLogger(__name__)


class JobService:
    """任务管理服务 - 使用Redis存储任务状态"""

    def __init__(self):
        self._redis = None
        self.key_prefix = "job:"

    async def _get_redis(self):
        """获取异步Redis连接"""
        if self._redis is None:
            self._redis = await async_from_url(
                settings.REDIS_URL,
                decode_responses=True,
                encoding="utf-8"
            )
        return self._redis

    async def close(self):
        """关闭Redis连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    async def create_job(self, job_type: str, params: Dict) -> str:
        """
        创建新任务

        Args:
            job_type: 任务类型
            params: 任务参数

        Returns:
            任务ID
        """
        redis = await self._get_redis()
        job_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        job_data = {
            "job_id": job_id,
            "job_type": job_type,
            "status": JobStatus.PENDING.value,
            "progress": 0,
            "message": "任务已创建，等待处理",
            "params": json.dumps(params, ensure_ascii=False),
            "result": "",
            "error": "",
            "created_at": now,
            "updated_at": now
        }

        await redis.hset(f"{self.key_prefix}{job_id}", mapping=job_data)
        logger.info(f"Job created: {job_id} (type: {job_type})")
        return job_id

    async def get_job(self, job_id: str) -> Optional[Dict]:
        """
        获取任务信息

        Args:
            job_id: 任务ID

        Returns:
            任务信息字典
        """
        redis = await self._get_redis()
        data = await redis.hgetall(f"{self.key_prefix}{job_id}")
        if not data:
            return None

        # 转换数据类型
        result = {
            "job_id": data.get("job_id"),
            "job_type": data.get("job_type"),
            "status": JobStatus(data.get("status", "pending")),
            "progress": int(data.get("progress", 0)),
            "message": data.get("message"),
            "result": json.loads(data.get("result")) if data.get("result") else None,
            "error": data.get("error") or None,
            "created_at": data.get("created_at"),
            "updated_at": data.get("updated_at")
        }
        return result

    async def update_job(self, job_id: str, updates: Dict) -> bool:
        """
        更新任务状态

        Args:
            job_id: 任务ID
            updates: 更新内容

        Returns:
            是否成功
        """
        redis = await self._get_redis()
        key = f"{self.key_prefix}{job_id}"
        if not await redis.exists(key):
            return False

        updates["updated_at"] = datetime.utcnow().isoformat()

        # 处理特殊字段
        if "result" in updates and isinstance(updates["result"], dict):
            updates["result"] = json.dumps(updates["result"], ensure_ascii=False)
        if "status" in updates and isinstance(updates["status"], JobStatus):
            updates["status"] = updates["status"].value

        await redis.hset(key, mapping=updates)
        return True

    async def update_progress(self, job_id: str, progress: int, message: str = None):
        """
        更新任务进度

        Args:
            job_id: 任务ID
            progress: 进度百分比 (0-100)
            message: 状态消息
        """
        updates = {"progress": min(100, max(0, progress))}
        if message:
            updates["message"] = message
        await self.update_job(job_id, updates)

    async def set_running(self, job_id: str):
        """设置任务为运行中"""
        await self.update_job(job_id, {
            "status": JobStatus.RUNNING,
            "message": "任务正在处理中"
        })

    async def set_completed(self, job_id: str, result: Dict):
        """设置任务为已完成"""
        await self.update_job(job_id, {
            "status": JobStatus.COMPLETED,
            "progress": 100,
            "result": result,
            "message": "任务处理完成"
        })
        logger.info(f"Job completed: {job_id}")

    async def set_failed(self, job_id: str, error: str):
        """设置任务为失败"""
        await self.update_job(job_id, {
            "status": JobStatus.FAILED,
            "error": error,
            "message": f"任务失败: {error}"
        })
        logger.error(f"Job failed: {job_id} - {error}")

    async def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None,
        limit: int = 20,
        offset: int = 0
    ) -> List[Dict]:
        """
        获取任务列表

        Args:
            status: 按状态筛选
            job_type: 按类型筛选
            limit: 返回数量
            offset: 偏移量

        Returns:
            任务列表
        """
        redis = await self._get_redis()
        # 获取所有job keys
        keys = await redis.keys(f"{self.key_prefix}*")
        jobs = []

        for key in keys:
            data = await redis.hgetall(key)
            if not data:
                continue

            # 筛选条件
            if status and data.get("status") != status.value:
                continue
            if job_type and data.get("job_type") != job_type:
                continue

            job_info = await self.get_job(data.get("job_id"))
            if job_info:
                jobs.append(job_info)

        # 按创建时间倒序
        jobs.sort(key=lambda x: x.get("created_at", ""), reverse=True)

        return jobs[offset:offset + limit]

    async def count_jobs(
        self,
        status: Optional[JobStatus] = None,
        job_type: Optional[str] = None
    ) -> int:
        """统计任务数量"""
        jobs = await self.list_jobs(status=status, job_type=job_type, limit=10000)
        return len(jobs)

    async def delete_job(self, job_id: str) -> bool:
        """删除任务"""
        redis = await self._get_redis()
        key = f"{self.key_prefix}{job_id}"
        result = await redis.delete(key)
        return result > 0