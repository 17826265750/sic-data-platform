"""Tasks package"""
from workers.tasks.processing_tasks import (
    process_parameter_check_task,
    process_trend_chart_task,
    process_stress_curve_task,
    process_normal_distribution_task,
    process_report_generation_task,
)

__all__ = [
    "process_parameter_check_task",
    "process_trend_chart_task",
    "process_stress_curve_task",
    "process_normal_distribution_task",
    "process_report_generation_task",
]