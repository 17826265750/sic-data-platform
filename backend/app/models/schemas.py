"""
Pydantic Models for API Request/Response Schemas
"""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ==================== Enums ====================

class JobStatus(str, Enum):
    """Job status enumeration"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TrendChartType(str, Enum):
    """Trend chart type enumeration"""
    VF = "VF"
    BV = "BV"
    IR = "IR"


# ==================== Base Models ====================

class BaseResponse(BaseModel):
    """Base response model"""
    success: bool = True
    message: str = "操作成功"


class ErrorDetail(BaseModel):
    """Error detail model"""
    code: str
    message: str
    details: Optional[str] = None


# ==================== Job Models ====================

class JobCreate(BaseModel):
    """Job creation request"""
    job_type: str = Field(..., description="Job type identifier")
    params: Dict[str, Any] = Field(default_factory=dict, description="Job parameters")
    files: List[str] = Field(default_factory=list, description="Uploaded file IDs")


class JobInfo(BaseModel):
    """Job information response"""
    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Job type")
    status: JobStatus = Field(..., description="Current status")
    progress: int = Field(0, ge=0, le=100, description="Progress percentage")
    message: Optional[str] = Field(None, description="Status message")
    result: Optional[Dict[str, Any]] = Field(None, description="Job result data")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class JobListResponse(BaseModel):
    """Job list response"""
    jobs: List[JobInfo]
    total: int


# ==================== Parameter Check Models ====================

class ParameterCheckRequest(BaseModel):
    """Parameter check processing request"""
    folder_path: Optional[str] = Field(None, description="Source folder path")
    file_ids: List[str] = Field(..., description="Uploaded file IDs to process")
    column_mapping: Optional[Dict[str, int]] = Field(None, description="Custom column mapping")


class ParameterCheckResult(BaseModel):
    """Parameter check processing result"""
    processed_files: int
    output_files: List[str]
    summary: Dict[str, Any]


# ==================== Trend Chart Models ====================

class TrendChartRequest(BaseModel):
    """Trend chart generation request"""
    chart_type: TrendChartType = Field(..., description="Chart type: VF, BV, or IR")
    product_list: List[str] = Field(..., description="Product names")
    time_labels: List[str] = Field(
        default=["初始值(T0)", "168小时", "500小时", "1000小时"],
        description="Time point labels"
    )
    means: Dict[str, List[float]] = Field(..., description="Mean values per product")
    stds: Dict[str, List[float]] = Field(..., description="Standard deviations per product")
    output_format: str = Field("png", description="Output format: png, pdf")


class TrendChartResult(BaseModel):
    """Trend chart generation result"""
    chart_path: str
    report_path: Optional[str] = None
    change_rates: Dict[str, float]


# ==================== Stress Curve Models ====================

class StressCurveRequest(BaseModel):
    """Stress curve analysis request"""
    file_id: str = Field(..., description="Uploaded Excel file ID")
    time_start: float = Field(0, ge=0, description="Plot time range start")
    time_end: float = Field(1000, ge=0, description="Plot time range end")
    leakage_columns: str = Field("all", description="Columns to plot: 'all' or comma-separated")
    show_legend: bool = Field(False, description="Show legend in plot")
    smooth_data: bool = Field(False, description="Apply smoothing filter")
    smooth_window: int = Field(5, ge=3, description="Smoothing window size (odd number)")


class StressCurveResult(BaseModel):
    """Stress curve analysis result"""
    chart_path: str
    filtered_data_path: str
    channels_count: int
    data_points: int


# ==================== Normal Distribution Models ====================

class NormalDistributionRequest(BaseModel):
    """Normal distribution analysis request"""
    file_id: str = Field(..., description="Uploaded Excel file ID")
    params: List[str] = Field(
        default=["VF", "IR", "BV"],
        description="Parameters to analyze"
    )
    times: List[str] = Field(
        default=["T0", "168h", "500h", "1000h"],
        description="Time points to compare"
    )
    sheets: Optional[List[str]] = Field(None, description="Product sheets to analyze")
    enable_outlier_removal: bool = Field(True, description="Enable 3-sigma outlier removal")
    outlier_sigma: float = Field(3.0, ge=1.0, le=5.0, description="Sigma threshold for outliers")


class NormalDistributionResult(BaseModel):
    """Normal distribution analysis result"""
    chart_path: str
    product_count: int
    analysis_results: List[Dict[str, Any]]
    statistics: Dict[str, Dict[str, float]]


# ==================== Report Generation Models ====================

class ReportGenerationRequest(BaseModel):
    """Report generation request"""
    template_id: str = Field(..., description="Word template file ID")
    data_file_id: str = Field(..., description="Excel data file ID")
    report_type: str = Field(..., description="Report type: HTRB, H3TRB, HTGB, TC, etc.")
    output_name: Optional[str] = Field(None, description="Custom output filename")


class ReportGenerationResult(BaseModel):
    """Report generation result"""
    report_path: str
    tables_updated: int
    fields_updated: int


# ==================== File Upload Models ====================

class FileInfo(BaseModel):
    """File information"""
    file_id: str
    filename: str
    size: int
    content_type: str
    uploaded_at: datetime


class UploadResponse(BaseModel):
    """File upload response"""
    file_id: str
    filename: str
    size: int
    message: str = "文件上传成功"