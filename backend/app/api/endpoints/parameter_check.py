"""
Parameter Check Endpoint - 参数检查数据处理
"""
import asyncio
import logging
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
logger = logging.getLogger(__name__)


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

    最大文件大小: 50MB
    支持格式: .xlsx, .xls
    """
    if not files:
        raise HTTPException(status_code=400, detail="没有上传文件")

    if len(files) > 20:
        raise HTTPException(status_code=400, detail="一次最多上传20个文件")

    uploaded_files = []
    total_size = 0

    for file in files:
        try:
            file_id = str(uuid.uuid4())
            saved_path = await file_service.save_upload(file, file_id)

            file_size = saved_path.stat().st_size
            total_size += file_size

            uploaded_files.append({
                "file_id": file_id,
                "filename": file.filename,
                "path": str(saved_path),
                "size": file_size
            })
            logger.info(f"File uploaded: {file.filename} ({file_size} bytes)")

        except ValueError as e:
            logger.warning(f"File validation failed: {file.filename} - {e}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"File upload error: {file.filename} - {e}")
            raise HTTPException(status_code=500, detail=f"文件上传失败: {file.filename}")

    return UploadResponse(
        file_id=uploaded_files[0]["file_id"] if len(uploaded_files) == 1 else "",
        filename=f"{len(uploaded_files)} files uploaded",
        size=total_size,
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

    异步任务，返回 job_id 用于查询进度
    """
    # Validate input directory exists
    if not request.input_directory:
        raise HTTPException(status_code=400, detail="请指定输入目录")

    try:
        job_id = await job_service.create_job(
            job_type="parameter_check",
            params=request.model_dump()
        )

        # Start async processing
        from app.workers.tasks.processing_tasks import process_parameter_check_task
        process_parameter_check_task.delay(job_id, request.model_dump())

        logger.info(f"Parameter check job created: {job_id}")

        return {
            "job_id": job_id,
            "status": "pending",
            "message": "参数检查处理任务已创建"
        }
    except Exception as e:
        logger.error(f"Failed to create parameter check job: {e}")
        raise HTTPException(status_code=500, detail=f"创建任务失败: {str(e)}")


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

    try:
        # Parse Excel structure asynchronously
        import pandas as pd

        def parse_excel(path: str):
            return pd.read_excel(path, header=None)

        df = await asyncio.to_thread(parse_excel, file_info["path"])

        # Find header row
        header_row = -1
        for idx, row in df.head(50).iterrows():
            row_str = " ".join([str(x) for x in row.values if pd.notna(x)])
            if "Serial#" in row_str or "序号" in row_str:
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
    except Exception as e:
        logger.error(f"Failed to preview file {file_id}: {e}")
        raise HTTPException(status_code=500, detail=f"文件解析失败: {str(e)}")