"""
Jobs Endpoint - 任务管理
"""
from fastapi import APIRouter, HTTPException
from typing import Optional
import os

from app.models.schemas import JobInfo, JobListResponse, JobStatus
from app.services.job_service import JobService
from app.config import settings

router = APIRouter()
job_service = JobService()


@router.get("/{job_id}", response_model=JobInfo)
async def get_job_status(job_id: str):
    """
    获取任务状态

    返回:
    - 任务ID
    - 当前状态 (pending/running/completed/failed)
    - 进度百分比
    - 结果数据 (如果完成)
    - 错误信息 (如果失败)
    """
    job_info = await job_service.get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    return JobInfo(**job_info)


@router.get("/{job_id}/download")
async def download_job_result(job_id: str):
    """
    下载任务结果文件

    支持下载:
    - 生成的图表 (PNG/PDF)
    - 处理后的Excel文件
    - 生成的Word报告
    """
    job_info = await job_service.get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    if job_info["status"] != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"任务状态为 {job_info['status']}，无法下载结果"
        )

    result = job_info.get("result", {})
    output_files = result.get("output_files", [])

    if not output_files:
        raise HTTPException(status_code=404, detail="没有可下载的结果文件")

    # Return file download info
    from fastapi.responses import FileResponse

    # Get the first output file
    output_path = output_files[0]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="结果文件不存在")

    return FileResponse(
        path=output_path,
        filename=os.path.basename(output_path),
        media_type="application/octet-stream"
    )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    status: Optional[JobStatus] = None,
    job_type: Optional[str] = None,
    limit: int = 20,
    offset: int = 0
):
    """
    获取任务列表

    参数:
    - status: 按状态筛选
    - job_type: 按类型筛选
    - limit: 返回数量限制
    - offset: 分页偏移
    """
    jobs = await job_service.list_jobs(
        status=status,
        job_type=job_type,
        limit=limit,
        offset=offset
    )

    total = await job_service.count_jobs(status=status, job_type=job_type)

    return JobListResponse(
        jobs=[JobInfo(**job) for job in jobs],
        total=total
    )


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    """
    取消/删除任务
    """
    job_info = await job_service.get_job(job_id)
    if not job_info:
        raise HTTPException(status_code=404, detail="任务不存在")

    if job_info["status"] == JobStatus.RUNNING:
        # Revoke Celery task
        from workers.celery_app import celery_app
        celery_app.control.revoke(job_id, terminate=True)

    await job_service.update_job(job_id, {"status": JobStatus.CANCELLED})

    return {"message": "任务已取消", "job_id": job_id}