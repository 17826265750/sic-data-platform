"""
Processing Tasks - Celery异步任务定义
"""
import asyncio
from typing import Dict, Any

from workers.celery_app import celery_app
from app.services.job_service import JobService
from app.core.processors import (
    ParameterCheckProcessor,
    TrendChartProcessor,
    StressCurveProcessor,
    NormalDistributionProcessor,
    ReportGenerationProcessor,
)
from app.models.schemas import JobStatus


# 创建同步版本的异步服务调用
def run_async(coro):
    """在同步环境中运行异步函数"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


async def update_job_progress(job_id: str, progress: int, message: str = None):
    """更新任务进度的异步函数"""
    job_service = JobService()
    await job_service.update_progress(job_id, progress, message)


@celery_app.task(bind=True, name="process_parameter_check")
def process_parameter_check_task(self, job_id: str, params: Dict[str, Any]):
    """参数检查数据处理任务"""
    job_service = JobService()

    async def run():
        await job_service.set_running(job_id)

        processor = ParameterCheckProcessor(job_id, params)
        processor.set_progress_callback(
            lambda p, m: update_job_progress(job_id, p, m)
        )

        result = await processor.run()

        if result.get("success"):
            await job_service.set_completed(job_id, result)
        else:
            await job_service.set_failed(job_id, result.get("error", "Unknown error"))

        return result

    return run_async(run())


@celery_app.task(bind=True, name="process_trend_chart")
def process_trend_chart_task(self, job_id: str, params: Dict[str, Any]):
    """趋势图生成任务"""
    job_service = JobService()

    async def run():
        await job_service.set_running(job_id)

        processor = TrendChartProcessor(job_id, params)
        processor.set_progress_callback(
            lambda p, m: update_job_progress(job_id, p, m)
        )

        result = await processor.run()

        if result.get("success"):
            await job_service.set_completed(job_id, result)
        else:
            await job_service.set_failed(job_id, result.get("error", "Unknown error"))

        return result

    return run_async(run())


@celery_app.task(bind=True, name="process_stress_curve")
def process_stress_curve_task(self, job_id: str, params: Dict[str, Any]):
    """应力曲线分析任务"""
    job_service = JobService()

    async def run():
        await job_service.set_running(job_id)

        processor = StressCurveProcessor(job_id, params)
        processor.set_progress_callback(
            lambda p, m: update_job_progress(job_id, p, m)
        )

        result = await processor.run()

        if result.get("success"):
            await job_service.set_completed(job_id, result)
        else:
            await job_service.set_failed(job_id, result.get("error", "Unknown error"))

        return result

    return run_async(run())


@celery_app.task(bind=True, name="process_normal_distribution")
def process_normal_distribution_task(self, job_id: str, params: Dict[str, Any]):
    """正态分布分析任务"""
    job_service = JobService()

    async def run():
        await job_service.set_running(job_id)

        processor = NormalDistributionProcessor(job_id, params)
        processor.set_progress_callback(
            lambda p, m: update_job_progress(job_id, p, m)
        )

        result = await processor.run()

        if result.get("success"):
            await job_service.set_completed(job_id, result)
        else:
            await job_service.set_failed(job_id, result.get("error", "Unknown error"))

        return result

    return run_async(run())


@celery_app.task(bind=True, name="process_report_generation")
def process_report_generation_task(self, job_id: str, params: Dict[str, Any]):
    """报告生成任务"""
    job_service = JobService()

    async def run():
        await job_service.set_running(job_id)

        processor = ReportGenerationProcessor(job_id, params)
        processor.set_progress_callback(
            lambda p, m: update_job_progress(job_id, p, m)
        )

        result = await processor.run()

        if result.get("success"):
            await job_service.set_completed(job_id, result)
        else:
            await job_service.set_failed(job_id, result.get("error", "Unknown error"))

        return result

    return run_async(run())