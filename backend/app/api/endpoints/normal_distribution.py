"""
Normal Distribution Endpoint - 正态分布分析
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid

from app.models.schemas import (
    NormalDistributionRequest,
    NormalDistributionResult,
    UploadResponse
)
from app.services.file_service import FileService
from app.services.job_service import JobService

router = APIRouter()
file_service = FileService()
job_service = JobService()


@router.post("/upload", response_model=UploadResponse)
async def upload_normal_dist_data(file: UploadFile = File(...)):
    """
    上传正态分布分析数据文件

    文件要求:
    - 格式: .xlsx
    - 多个Sheet，每个Sheet代表一个产品
    - 每个Sheet包含各时间点的VF/IR/BV参数数据
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持Excel文件 (.xlsx, .xls)")

    file_id = str(uuid.uuid4())
    saved_path = await file_service.save_upload(file, file_id)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=file.size or 0,
        message="正态分布分析文件上传成功"
    )


@router.post("/analyze", response_model=dict)
async def analyze_normal_distribution(request: NormalDistributionRequest):
    """
    执行正态分布分析

    处理流程:
    1. 读取Excel各产品Sheet
    2. 提取指定参数和时间点数据
    3. 3-sigma异常值处理
    4. 计算统计量 (均值、标准差)
    5. 绘制正态分布直方图和拟合曲线

    参数:
    - file_id: 上传的文件ID
    - params: 要分析的参数列表 (VF, IR, BV)
    - times: 要对比的时间点 (T0, 168h, 500h, 1000h)
    - sheets: 指定产品Sheet，为空则分析全部
    - enable_outlier_removal: 是否启用3-sigma异常值移除
    - outlier_sigma: sigma阈值 (默认3.0)
    """
    job_id = await job_service.create_job(
        job_type="normal_distribution",
        params=request.model_dump()
    )

    from workers.tasks.processing_tasks import process_normal_distribution_task
    process_normal_distribution_task.delay(job_id, request.model_dump())

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "正态分布分析任务已创建"
    }


@router.get("/preview/{file_id}")
async def preview_normal_dist_data(file_id: str):
    """
    预览正态分布分析数据

    返回:
    - 可用产品Sheet列表
    - 可用参数
    - 可用时间点
    """
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    import pandas as pd

    # 获取所有Sheet名称
    xl = pd.ExcelFile(file_info["path"])
    sheet_names = xl.sheet_names

    # 读取第一个Sheet获取参数信息
    if sheet_names:
        df = xl.parse(sheet_names[0], header=None)

        # 默认时间配置
        default_time_config = {
            'T0': {'VF': 2, 'IR': 3, 'BV': 4},
            '168h': {'VF': 6, 'IR': 7, 'BV': 8},
            '500h': {'VF': 10, 'IR': 11, 'BV': 12},
            '1000h': {'VF': 14, 'IR': 15, 'BV': 16}
        }

        return {
            "file_id": file_id,
            "filename": file_info["filename"],
            "sheets": sheet_names,
            "sheet_count": len(sheet_names),
            "available_params": ["VF", "IR", "BV"],
            "available_times": list(default_time_config.keys()),
            "default_time_config": default_time_config
        }

    return {
        "file_id": file_id,
        "filename": file_info["filename"],
        "sheets": [],
        "sheet_count": 0
    }