"""
Stress Curve Processor - 应力数据曲线处理

重构自 YLSJ.py
核心功能：漏电流趋势可视化(80通道)
"""
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy.signal import savgol_filter

from app.core.processor_base import ProcessorBase
from app.core.plot_base import PlotBase


class StressCurveProcessor(ProcessorBase):
    """应力数据曲线处理器"""

    def __init__(self, job_id: str, params: Dict[str, Any]):
        super().__init__(job_id, params)
        self.file_id = params.get("file_id")

    async def process(self) -> Dict[str, Any]:
        """执行应力曲线分析"""
        await self.update_progress(10, "读取数据文件...")

        if not self.file_id:
            raise ValueError("未提供文件ID")

        # 获取文件路径
        file_info = await self.file_service.get_file_info(self.file_id)
        if not file_info:
            raise ValueError(f"文件不存在: {self.file_id}")

        file_path = Path(file_info["path"])

        # 读取Excel数据
        df = pd.read_excel(file_path)
        print(f"成功读取数据，共 {len(df)} 行")

        await self.update_progress(20, "识别数据列...")

        # 识别漏电流列
        leakage_cols = self._identify_leakage_columns(df)

        await self.update_progress(30, "筛选数据...")

        # 筛选数据
        filtered_df = self._filter_data(df)

        await self.update_progress(40, "应用时间范围...")

        # 应用时间范围
        time_start = self.params.get("time_start", 0)
        time_end = self.params.get("time_end", 1000)
        time_col = self._find_time_column(df)

        if time_col:
            plot_df = filtered_df[
                (filtered_df[time_col] >= time_start) &
                (filtered_df[time_col] <= time_end)
            ].copy()
        else:
            plot_df = filtered_df.copy()

        await self.update_progress(50, "处理选定的列...")

        # 处理漏电流列选择
        selected_cols = self._get_selected_columns(leakage_cols)

        # 数据平滑
        smooth_data = self.params.get("smooth_data", False)
        smooth_window = self.params.get("smooth_window", 5)

        if smooth_data:
            await self.update_progress(60, "应用平滑处理...")
            for col in selected_cols:
                if col in plot_df.columns and len(plot_df) > smooth_window:
                    plot_df[col] = savgol_filter(plot_df[col], smooth_window, 3)

        await self.update_progress(70, "保存筛选数据...")

        # 保存筛选后的数据
        filtered_output = self.generate_output_path("筛选后_应力数据.xlsx")
        plot_df.to_excel(filtered_output, index=False)

        await self.update_progress(80, "绘制曲线...")

        # 绘制曲线
        chart_path = self._plot_curves(plot_df, selected_cols, time_col, time_start, time_end)

        await self.update_progress(100, "完成")

        return {
            "chart_path": str(chart_path),
            "filtered_data_path": str(filtered_output),
            "channels_count": len(selected_cols),
            "data_points": len(plot_df),
            "output_files": [str(chart_path), str(filtered_output)]
        }

    def _identify_leakage_columns(self, df: pd.DataFrame) -> List[str]:
        """识别漏电流列 (I1-I80)"""
        leakage_cols = [col for col in df.columns if col.startswith('I')]
        leakage_cols = sorted(
            leakage_cols,
            key=lambda x: int(x[1:]) if x[1:].isdigit() else 0
        )
        return leakage_cols

    def _find_time_column(self, df: pd.DataFrame) -> Optional[str]:
        """查找时间列"""
        for col in df.columns:
            if '时间' in col:
                return col
        return None

    def _find_temp_column(self, df: pd.DataFrame) -> Optional[str]:
        """查找温度列"""
        for col in df.columns:
            if '温度' in col:
                return col
        return None

    def _filter_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """按规则筛选数据"""
        time_col = self._find_time_column(df)
        temp_col = self._find_temp_column(df)

        if not time_col:
            return df.copy()

        if not temp_col:
            # 如果没有温度列，返回时间范围内的数据
            return df[(df[time_col] >= 0) & (df[time_col] <= 1000)].copy()

        # 核心筛选条件
        cond1 = (df[time_col] >= 0) & (df[time_col] <= 100)
        cond2 = (
            (df[time_col] > 100) &
            (df[time_col] <= 1000) &
            (df[temp_col] >= 174.5) &
            (df[temp_col] <= 175.5)
        )

        return df[cond1 | cond2].copy()

    def _get_selected_columns(self, all_cols: List[str]) -> List[str]:
        """获取用户选择的列"""
        cols_param = self.params.get("leakage_columns", "all")

        if cols_param == "all":
            return all_cols

        # 解析逗号分隔的列名
        selected = [col.strip() for col in cols_param.split(',') if col.strip() in all_cols]
        return selected if selected else all_cols

    def _plot_curves(
        self, df: pd.DataFrame, cols: List[str],
        time_col: Optional[str], time_start: float, time_end: float
    ) -> Path:
        """绘制漏电流曲线"""
        import matplotlib.pyplot as plt

        plotter = PlotBase()
        fig, ax = plotter.create_figure((20, 12))

        time_data = df[time_col] if time_col else range(len(df))

        show_legend = self.params.get("show_legend", False)

        for col in cols:
            if col in df.columns:
                ax.plot(
                    time_data, df[col],
                    marker='.',
                    markersize=1,
                    linewidth=1.5,
                    alpha=0.7,
                    label=col
                )

        # 设置标签和标题
        ax.set_title(
            f'漏电流随时间变化趋势\n（时间范围：{time_start}-{time_end}h）',
            fontsize=12, pad=10
        )
        ax.set_xlabel('时间（h）', fontsize=14)
        ax.set_ylabel('漏电流值（uA）', fontsize=14)
        ax.grid(True, alpha=0.2)

        # 图例（可选）
        if show_legend:
            ax.legend(
                fontsize=7,
                ncol=10,
                loc='upper center',
                bbox_to_anchor=(0.5, -0.08),
                frameon=False
            )

        plt.tight_layout()

        # 保存
        chart_path = self.generate_output_path("漏电流趋势图.png")
        plotter.save_plot(str(chart_path), 300)

        return chart_path