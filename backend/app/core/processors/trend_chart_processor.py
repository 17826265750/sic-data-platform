"""
Trend Chart Processor - 变化率作图处理

重构自 VF.py, BV.py, IR.PY
核心功能：VF/BV/IR参数趋势图生成
"""
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

from app.core.processor_base import ProcessorBase
from app.core.plot_base import PlotBase, get_color_palette, get_marker_styles


class TrendChartProcessor(ProcessorBase):
    """变化率趋势图处理器"""

    # 配置常量
    CONFIG = {
        "figure_size": (14, 8),
        "offset_step": 0.05,
        "errorbar_capsize": 5,
        "line_width": 2,
        "marker_size": 8,
        "annotation_font_size": 9,
        "axis_label_font_size": 14,
        "title_font_size": 16,
        "legend_font_size": 12,
        "tick_label_font_size": 12,
        "dpi": 300,
    }

    # Y轴标签映射
    Y_LABELS = {
        "VF": "VF (V)",
        "BV": "BV@1mA (V)",
        "IR": "IR (uA)"
    }

    # 标题映射
    TITLES = {
        "VF": "SiC JBS二极管HTRB测试VF值变化趋势",
        "BV": "SiC JBS二极管HTRB测试BV@1mA值变化趋势",
        "IR": "SiC JBS二极管HTRB测试IR值变化趋势"
    }

    def __init__(self, job_id: str, params: Dict[str, Any]):
        super().__init__(job_id, params)
        self.chart_type = params.get("chart_type", "VF")

    async def process(self) -> Dict[str, Any]:
        """生成趋势图"""
        await self.update_progress(10, "准备数据...")

        # 获取参数
        product_list = self.params.get("product_list", [])
        time_labels = self.params.get("time_labels", ["初始值(T0)", "168小时", "500小时", "1000小时"])
        means = self.params.get("means", {})
        stds = self.params.get("stds", {})

        if not product_list or not means:
            raise ValueError("缺少必要参数: product_list 或 means")

        await self.update_progress(30, "计算变化率...")

        # 计算变化率
        change_rates_detail, change_rates_final = self._calculate_change_rates(
            product_list, means
        )

        await self.update_progress(50, "生成报表...")

        # 生成CSV报表
        report_path = self._generate_report(
            product_list, means, stds, change_rates_detail, time_labels
        )

        await self.update_progress(70, "绘制图表...")

        # 绘制趋势图
        chart_path = self._plot_trend_chart(
            product_list, time_labels, means, stds, change_rates_final
        )

        await self.update_progress(100, "完成")

        return {
            "chart_path": str(chart_path),
            "report_path": str(report_path),
            "change_rates": change_rates_final,
            "output_files": [str(chart_path), str(report_path)]
        }

    def _calculate_change_rates(
        self, product_list: List[str], means: Dict[str, List[float]]
    ) -> tuple:
        """计算变化率"""
        change_rates_detail = {}
        change_rates_final = {}

        for product in product_list:
            if product not in means:
                continue

            initial = means[product][0] if means[product] else 0

            if initial == 0:
                change_rates_final[product] = 0.0
                change_rates_detail[product] = [0.0] * len(means[product])
            else:
                change_rates_detail[product] = [
                    (v - initial) / initial * 100 for v in means[product]
                ]
                change_rates_final[product] = change_rates_detail[product][-1]

        return change_rates_detail, change_rates_final

    def _generate_report(
        self, product_list: List[str], means: Dict, stds: Dict,
        change_rates_detail: Dict, time_labels: List[str]
    ) -> Path:
        """生成CSV报表"""
        n_times = len(time_labels)

        report_data = {
            '产品型号': product_list,
        }

        # 添加各时间点数据
        for i, label in enumerate(time_labels):
            report_data[f'{label} {self.chart_type}'] = [
                means[p][i] if p in means and i < len(means[p]) else None
                for p in product_list
            ]

        # 添加变化率
        for i, label in enumerate(time_labels[1:], 1):
            report_data[f'{label}变化率(%)'] = [
                change_rates_detail[p][i] if p in change_rates_detail and i < len(change_rates_detail[p]) else None
                for p in product_list
            ]

        df = pd.DataFrame(report_data)
        df = df.round(4)

        report_path = self.generate_output_path(f"{self.chart_type}_变化率报表.csv")
        df.to_csv(report_path, index=False, encoding='utf-8-sig')

        return report_path

    def _plot_trend_chart(
        self, product_list: List[str], time_labels: List[str],
        means: Dict, stds: Dict, change_rates_final: Dict
    ) -> Path:
        """绘制趋势图"""
        import matplotlib.pyplot as plt

        plotter = PlotBase()
        fig, ax = plotter.create_figure(self.CONFIG["figure_size"])

        time_indices = np.arange(len(time_labels))
        n_products = len(product_list)

        # 获取颜色和标记样式
        colors = get_color_palette(n_products)
        markers = get_marker_styles(n_products)

        product_styles = {
            p: {'color': colors[i], 'marker': markers[i]}
            for i, p in enumerate(product_list)
        }

        # 计算产品偏移
        offsets = np.linspace(
            -self.CONFIG["offset_step"] * (n_products - 1) / 2,
            self.CONFIG["offset_step"] * (n_products - 1) / 2,
            n_products
        )
        product_offset_map = dict(zip(product_list, offsets))

        # 绘制每个产品的折线
        for product in product_list:
            if product not in means:
                continue

            x_pos = time_indices + product_offset_map[product]
            y_mean = means[product]
            y_std = stds.get(product, [0] * len(y_mean))
            style = product_styles[product]

            # 折线
            ax.plot(
                x_pos, y_mean,
                color=style['color'],
                marker=style['marker'],
                label=product,
                linewidth=self.CONFIG["line_width"],
                markersize=self.CONFIG["marker_size"]
            )

            # 误差棒
            ax.errorbar(
                x_pos, y_mean, yerr=y_std,
                color=style['color'],
                capsize=self.CONFIG["errorbar_capsize"],
                linewidth=self.CONFIG["line_width"] * 0.7,
                linestyle=''
            )

            # 变化率标注
            if product in change_rates_final:
                y_final = y_mean[-1]
                rate_text = f'{change_rates_final[product]:+.2f}%'
                ax.annotate(
                    rate_text,
                    xy=(x_pos[-1], y_final),
                    xytext=(0, 8),
                    textcoords='offset points',
                    ha='center', va='bottom',
                    fontsize=self.CONFIG["annotation_font_size"],
                    color=style['color'],
                    fontweight='bold',
                    bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.9),
                    zorder=10
                )

        # 设置轴标签
        ax.set_xticks(time_indices)
        ax.set_xticklabels(time_labels, fontsize=self.CONFIG["tick_label_font_size"])
        ax.set_xlabel('测试阶段', fontsize=self.CONFIG["axis_label_font_size"])
        ax.set_ylabel(
            self.Y_LABELS.get(self.chart_type, self.chart_type),
            fontsize=self.CONFIG["axis_label_font_size"]
        )

        # 设置Y轴范围
        all_means = [v for p in product_list for v in means.get(p, [])]
        all_stds = [v for p in product_list for v in stds.get(p, [])]

        if all_means:
            y_min = min(all_means) - max(all_stds) * 1.1 if all_stds else min(all_means) * 0.9
            y_max = max(all_means) + max(all_stds) * 1.1 if all_stds else max(all_means) * 1.1
            ax.set_ylim(y_min, y_max)

        # 其他样式
        ax.legend(loc='best', fontsize=self.CONFIG["legend_font_size"], title='产品型号')
        ax.grid(True, axis='y', linestyle='--', alpha=0.6)
        ax.set_title(
            self.TITLES.get(self.chart_type, f'{self.chart_type}变化趋势'),
            fontsize=self.CONFIG["title_font_size"],
            pad=20
        )

        # 保存
        chart_path = self.generate_output_path(f"{self.chart_type}_HTRB_plot.png")
        plotter.save_plot(str(chart_path), self.CONFIG["dpi"])

        return chart_path