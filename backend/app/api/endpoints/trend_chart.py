"""
Trend Chart Endpoint - 变化率作图 (VF/BV/IR)
"""
from fastapi import APIRouter, HTTPException
from typing import Dict, List
import uuid

from app.models.schemas import (
    TrendChartRequest,
    TrendChartResult,
    TrendChartType,
    UploadResponse
)
from app.services.job_service import JobService

router = APIRouter()
job_service = JobService()


@router.post("/vf", response_model=dict)
async def generate_vf_trend_chart(request: TrendChartRequest):
    """
    生成VF变化率趋势图

    VF (正向电压) 参数:
    - 产品型号列表
    - 各时间点均值和标准差
    - 自动计算变化率并标注
    """
    request.chart_type = TrendChartType.VF
    job_id = await job_service.create_job(
        job_type="trend_chart_vf",
        params=request.model_dump()
    )

    from app.workers.tasks.processing_tasks import process_trend_chart_task
    process_trend_chart_task.delay(job_id, request.model_dump())

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "VF趋势图生成任务已创建"
    }


@router.post("/bv", response_model=dict)
async def generate_bv_trend_chart(request: TrendChartRequest):
    """
    生成BV变化率趋势图

    BV (反向击穿电压) 参数:
    - 测试条件: 1mA
    - 产品型号列表
    - 各时间点均值和标准差
    """
    request.chart_type = TrendChartType.BV
    job_id = await job_service.create_job(
        job_type="trend_chart_bv",
        params=request.model_dump()
    )

    from app.workers.tasks.processing_tasks import process_trend_chart_task
    process_trend_chart_task.delay(job_id, request.model_dump())

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "BV趋势图生成任务已创建"
    }


@router.post("/ir", response_model=dict)
async def generate_ir_trend_chart(request: TrendChartRequest):
    """
    生成IR变化率趋势图

    IR (反向漏电流) 参数:
    - 测试条件: 1200V
    - 产品型号列表
    - 各时间点均值和标准差
    """
    request.chart_type = TrendChartType.IR
    job_id = await job_service.create_job(
        job_type="trend_chart_ir",
        params=request.model_dump()
    )

    from app.workers.tasks.processing_tasks import process_trend_chart_task
    process_trend_chart_task.delay(job_id, request.model_dump())

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "IR趋势图生成任务已创建"
    }


@router.post("/data-template", response_model=Dict)
async def get_trend_chart_data_template():
    """
    获取趋势图数据模板

    返回标准的数据输入格式示例
    """
    return {
        "template": {
            "product_list": ["HX1D40120H", "HX2D60120H"],
            "time_labels": ["初始值(T0)", "168小时", "500小时", "1000小时"],
            "means": {
                "HX1D40120H": [1.3683, 1.3753, 1.3662, 1.3696],
                "HX2D60120H": [1.4156, 1.4157, 1.4243, 1.4183]
            },
            "stds": {
                "HX1D40120H": [0.0045, 0.0059, 0.0092, 0.0045],
                "HX2D60120H": [0.0052, 0.0054, 0.0052, 0.0049]
            }
        },
        "description": "VF/BV/IR趋势图数据格式模板，means和stds为各产品在各时间点的统计数据"
    }