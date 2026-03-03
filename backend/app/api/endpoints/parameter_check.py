"""
Parameter Check Endpoint - 参数检查数据处理
"""
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from typing import List, Optional
import uuid
from pathlib import Path

from app.models.schemas import ParameterCheckRequest, ParameterCheckResult, UploadResponse
from app.services.file_service import FileService
from app.services.job_service import JobService

router = APIRouter()
file_service = FileService()
job_service = JobService()


@router.post("/upload", response_model=UploadResponse)
async def upload_parameter_check_files(
    files: List[UploadFile] = File(..., description="Excel files to upload")
):
    """
    上传参数检查相关文件

    支持上传:
    - 模板文件 (包含"数据处理"的文件)
    - 源数据文件 (H3TRB/HTRB时间点数据)
    - 应力数据文件 (_P数字_ 格式)
    """
    uploaded_files = []

    for file in files:
        if not file.filename.endswith(('.xlsx', '.xls')):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件格式: {file.filename}"
            )

        file_id = str(uuid.uuid4())
        saved_path = await file_service.save_upload(file, file_id)

        uploaded_files.append({
            "file_id": file_id,
            "filename": file.filename,
            "path": str(saved_path)
        })

    return UploadResponse(
        file_id=uploaded_files[0]["file_id"] if len(uploaded_files) == 1 else "",
        filename=f"{len(uploaded_files)} files uploaded",
        size=sum(f["size"] for f in uploaded_files),
        message=f"成功上传 {len(uploaded_files)} 个文件"
    )


@router.post("/process", response_model=dict)
async def process_parameter_check(request: ParameterCheckRequest):
    """
    执行参数检查数据处理

    处理流程:
    1. 扫描上传的文件
    2. 自动匹配模板与源数据
    3. 提取VF/IR/BVR参数数据
    4. 填充到模板对应位置
    5. 清理缺失时间点数据
    """
    job_id = await job_service.create_job(
        job_type="parameter_check",
        params=request.model_dump()
    )

    # Start async processing
    from app.workers.tasks.processing_tasks import process_parameter_check_task
    process_parameter_check_task.delay(job_id, request.model_dump())

    return {
        "job_id": job_id,
        "status": "pending",
        "message": "参数检查处理任务已创建"
    }


@router.get("/preview/{file_id}")
async def preview_file_structure(file_id: str):
    """
    预览文件结构

    返回:
    - 表头行索引
    - 可用列信息
    - 数据行数
    """
    file_info = await file_service.get_file_info(file_id)
    if not file_info:
        raise HTTPException(status_code=404, detail="文件不存在")

    # Parse Excel structure
    import pandas as pd
    df = pd.read_excel(file_info["path"], header=None)

    # Find header row
    header_row = -1
    for idx, row in df.head(50).iterrows():
        row_str = " ".join([str(x) for x in row.values if pd.notna(x)])
        if "Serial#" in row_str:
            header_row = idx
            break

    return {
        "file_id": file_id,
        "filename": file_info["filename"],
        "total_rows": len(df),
        "total_columns": len(df.columns),
        "header_row": header_row,
        "columns": df.iloc[header_row].tolist() if header_row >= 0 else []
    }