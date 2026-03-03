"""
SiC Data Processing Platform - Main FastAPI Application
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError

from app.config import settings
from app.api.router import api_router
from app.services.file_service import FileService
from app.services.job_service import JobService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    # Startup
    logger.info(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    logger.info(f"Debug mode: {settings.DEBUG}")

    # Initialize storage directories
    file_service = FileService()
    await file_service.init_directories()
    logger.info(f"Storage initialized: upload={settings.UPLOAD_DIR}, result={settings.RESULT_DIR}")

    # Setup matplotlib for Chinese fonts
    from app.core.plot_base import setup_chinese_fonts
    setup_chinese_fonts()

    # Initialize job service connection
    job_service = JobService()
    try:
        # Test Redis connection
        redis = await job_service._get_redis()
        await redis.ping()
        logger.info("Redis connection established")
    except Exception as e:
        logger.warning(f"Redis connection failed: {e}. Job tracking may not work.")

    yield

    # Shutdown
    await job_service.close()
    logger.info(f"Shutting down {settings.APP_NAME}")


def create_application() -> FastAPI:
    """Create and configure the FastAPI application"""
    app = FastAPI(
        title="SiC Data Processing Platform",
        description="""
碳化硅数据处理平台 - 整合参数检查、变化率作图、应力曲线、正态分布分析、测试报告生成

## 功能模块

| 模块 | 描述 |
|-----|------|
| 参数检查数据处理 | Excel模板数据合并与智能匹配 |
| 变化率作图 | VF/BV/IR参数趋势图生成 |
| 应力数据曲线 | 漏电流趋势可视化(80通道) |
| 正态分布分析 | 统计分析与正态分布图 |
| 测试报告生成 | Word报告自动生成 |

## 异步处理

所有长时间运行的任务都通过 Celery 异步处理，返回 job_id 供查询进度。
        """,
        version=settings.APP_VERSION,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
        lifespan=lifespan,
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API router
    app.include_router(api_router, prefix="/api/v1")

    # Health check endpoint
    @app.get("/health", tags=["Health"])
    async def health_check():
        """
        健康检查端点

        返回服务状态和各依赖项的连接状态
        """
        health_status = {
            "status": "healthy",
            "app": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "dependencies": {}
        }

        # Check Redis
        try:
            job_service = JobService()
            redis = await job_service._get_redis()
            await redis.ping()
            health_status["dependencies"]["redis"] = "connected"
        except Exception as e:
            health_status["dependencies"]["redis"] = f"error: {str(e)}"
            health_status["status"] = "degraded"

        # Check storage
        try:
            upload_path = settings.upload_path
            result_path = settings.result_path
            health_status["dependencies"]["storage"] = {
                "upload_dir": str(upload_path),
                "result_dir": str(result_path),
                "writable": upload_path.exists() and result_path.exists()
            }
        except Exception as e:
            health_status["dependencies"]["storage"] = f"error: {str(e)}"

        return health_status

    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint - API information"""
        return {
            "message": "SiC Data Processing Platform API",
            "version": settings.APP_VERSION,
            "docs": "/api/docs",
            "health": "/health",
            "endpoints": {
                "parameter_check": "/api/v1/parameter-check",
                "trend_chart": "/api/v1/trend-chart",
                "stress_curve": "/api/v1/stress-curve",
                "normal_distribution": "/api/v1/normal-distribution",
                "report": "/api/v1/report",
                "jobs": "/api/v1/jobs"
            }
        }

    # Validation error handler
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors with user-friendly messages"""
        errors = []
        for error in exc.errors():
            field = ".".join(str(loc) for loc in error["loc"])
            errors.append({
                "field": field,
                "message": error["msg"],
                "type": error["type"]
            })

        logger.warning(f"Validation error: {errors}")
        return JSONResponse(
            status_code=422,
            content={
                "error": "Validation Error",
                "detail": errors,
            },
        )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Global exception handler"""
        # Log the full error
        logger.exception(f"Unhandled exception: {exc}")

        # Return safe error response
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc) if settings.DEBUG else "An unexpected error occurred. Please try again later.",
            },
        )

    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )