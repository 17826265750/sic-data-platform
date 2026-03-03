"""
Plot Base - 统一绘图配置基类
"""
import matplotlib
matplotlib.use('Agg')  # 非交互式后端，适合服务器环境

import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
from typing import Optional, List, Tuple

from app.config import settings


class PlotBase:
    """统一绘图配置，消除重复的中文字体设置"""

    def __init__(self):
        self.fig = None
        self.ax = None
        self._setup_fonts()

    def _setup_fonts(self):
        """设置中文字体"""
        plt.rcParams['axes.unicode_minus'] = False

        # Docker环境中的字体路径
        if os.path.exists(settings.CHINESE_FONT_PATH):
            font_manager.fontManager.addfont(settings.CHINESE_FONT_PATH)
            plt.rcParams['font.family'] = 'WenQuanYi Micro Hei'
        else:
            # 尝试系统自带字体
            chinese_fonts = [
                'Microsoft YaHei', 'SimHei', 'SimSun',
                'WenQuanYi Micro Hei', 'Noto Sans CJK SC',
                'DejaVu Sans'
            ]

            for font_name in chinese_fonts:
                try:
                    plt.rcParams['font.family'] = font_name
                    # 测试字体是否可用
                    fig, ax = plt.subplots(figsize=(1, 1))
                    ax.text(0.5, 0.5, '中文测试')
                    plt.close(fig)
                    break
                except Exception:
                    continue

    def create_figure(self, figsize: Tuple[int, int] = (14, 8)):
        """创建图表"""
        self.fig, self.ax = plt.subplots(figsize=figsize)
        return self.fig, self.ax

    def save_plot(self, output_path: str, dpi: int = 300):
        """保存图表"""
        if self.fig:
            self.fig.savefig(output_path, dpi=dpi, bbox_inches='tight')
            plt.close(self.fig)

    def set_chinese_labels(self, ax, title: str = None, xlabel: str = None, ylabel: str = None):
        """设置中文标签"""
        if title:
            ax.set_title(title, fontsize=16, pad=20)
        if xlabel:
            ax.set_xlabel(xlabel, fontsize=14)
        if ylabel:
            ax.set_ylabel(ylabel, fontsize=14)


def setup_chinese_fonts():
    """
    全局配置中文字体 (应用启动时调用)
    """
    PlotBase()  # 初始化会自动设置字体
    print("中文字体配置完成")


def get_color_palette(n: int) -> List:
    """获取n种颜色"""
    import numpy as np
    return plt.cm.tab10(np.linspace(0, 1, n))


def get_marker_styles(n: int) -> List[str]:
    """获取n种标记样式"""
    markers = ['o', 's', '^', 'D', 'v', '<', '>', 'p', 'h', '*']
    return markers[:n] if n <= len(markers) else markers * (n // len(markers) + 1)