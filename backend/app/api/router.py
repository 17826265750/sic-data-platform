"""
API Router - Aggregates all endpoint routers
"""
from fastapi import APIRouter

from app.api.endpoints import (
    parameter_check,
    trend_chart,
    stress_curve,
    normal_distribution,
    report_generation,
    jobs,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(
    parameter_check.router,
    prefix="/parameter-check",
    tags=["Parameter Check"],
)

api_router.include_router(
    trend_chart.router,
    prefix="/trend-chart",
    tags=["Trend Chart"],
)

api_router.include_router(
    stress_curve.router,
    prefix="/stress-curve",
    tags=["Stress Curve"],
)

api_router.include_router(
    normal_distribution.router,
    prefix="/normal-distribution",
    tags=["Normal Distribution"],
)

api_router.include_router(
    report_generation.router,
    prefix="/report",
    tags=["Report Generation"],
)

api_router.include_router(
    jobs.router,
    prefix="/jobs",
    tags=["Jobs"],
)