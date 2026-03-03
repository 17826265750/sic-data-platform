"""Core package"""
from app.core.plot_base import PlotBase, setup_chinese_fonts, get_color_palette, get_marker_styles
from app.core.processor_base import ProcessorBase

__all__ = [
    "PlotBase",
    "setup_chinese_fonts",
    "get_color_palette",
    "get_marker_styles",
    "ProcessorBase"
]