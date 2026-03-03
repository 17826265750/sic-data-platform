"""
Stress Curve Endpoint - 应力数据曲线分析
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
import uuid

from app.models.schemas import StressCurveRequest, StressCurveResult, UploadResponse
from app.services.file_service import FileService
from app.services.job_service import JobService

router = APIRouter()
file_service = FileService()
job_service = JobService()


@router.post("/upload", response_model=UploadResponse)
async def upload_stress_data(file: UploadFile = File(...)):
    """
    上传应力数据Excel文件

    文件要求:
    - 格式: .xlsx
    - 必须包含: 时间(h), 环境温度(℃), I1-I80 漏电流列
    """
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="仅支持Excel文件 (.xlsx, .xls)")

    file_id = str(uuid.uuid4())
    saved_path = await file_service.save_upload(file, file_id)

    return UploadResponse(
        file_id=file_id,
        filename=file.filename,
        size=file.size or 0,
        message="应力数据文件上传成功"
    )


@router.post("/analyze", response_model=dict)
async def analyze_stress_curve(request: StressCurveRequest):
    """
    分析应力数据并生成漏电流趋势曲线

    处理流程:
    1. 读取Excel数据
    2. 按温度条件筛选 (0-100h全保留, 100-1000h温度174.5-175.5℃)
    3. 可选Savitzky-Golay平滑
    4. 绘制80通道漏电流曲线

    参数:
    - file_id: 上传的文件ID
    - time_start/time_end: 绘图时间范围
    - leakage_columns: 'all' 或指定列如 'I1,I2,I5'
    - show_legend: 是否显示图例
    - smooth_data: 是否平滑处理
    - smooth_window: 平滑窗口大小
    """
    job_id = await job_service.create_job(
        job_type="stress_curve",
        params=request.model_dump()
    )

    from app.workers.tasks.processing_tasks import process_stress_curve_task
    process_stress_curve_task.delay(job_id, request.model_dump())

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "应力曲线分析任务已创建"
    }


@router.get("/preview/{file_id}")
async def preview_stress_data(file_id: str):
    """
    预览应力数据文件

    返回:
    - 可用漏电流列列表
    - 时间范围
    - 温度范围
    """
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    import pandas as pd
    df = pd.read_excel(file_info["path"])

    # 识别漏电流列
    leakage_cols = [col for col in df.columns if col.startswith('I')]
    leakage_cols = sorted(leakage_cols, key=lambda x: int(x[1:]) if x[1:].isdigit() else 0)

    # 获取时间和温度范围
    time_col = [col for col in df.columns if '时间' in col]
    temp_col = [col for col in df.columns if '温度' in col]

    time_range = {}
    temp_range = {}

    if time_col:
        time_range = {
            "min": float(df[time_col[0]].min()),
            "max": float(df[time_col[0]].max())
        }

    if temp_col:
        temp_range = {
            "min": float(df[temp_col[0]].min()),
            "max": float(df[temp_col[0]].max())
        }

    return {
        "file_id": file_id,
        "filename": file_info["filename"],
        "total_rows": len(df),
        "leakage_columns": leakage_cols,
        "channels_count": len(leakage_cols),
        "time_range": time_range,
        "temperature_range": temp_range
    }