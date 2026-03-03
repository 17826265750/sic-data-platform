"""
Normal Distribution Processor - 正态分布分析处理

重构自 JTCS.py
核心功能：统计分析与正态分布图
"""
import os
import re
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, List, Optional
from scipy import stats

from app.core.processor_base import ProcessorBase
from app.core.plot_base import PlotBase


class NormalDistributionProcessor(ProcessorBase):
    """正态分布分析处理器"""

    def __init__(self, job_id: str, params: Dict[str, Any]):
        super().__init__(job_id, params)
        self.file_id = params.get("file_id")
        self.enable_outlier_removal = params.get("enable_outlier_removal", True)
        self.outlier_sigma = params.get("outlier_sigma", 3.0)

    async def process(self) -> Dict[str, Any]:
        """执行正态分布分析"""
        await self.update_progress(10, "读取数据文件...")

        if not self.file_id:
            raise ValueError("未提供文件ID")

        file_info = await self.file_service.get_file_info(self.file_id)
        if not file_info:
            raise ValueError(f"文件不存在: {self.file_id}")

        file_path = Path(file_info["path"])

        # 获取参数
        selected_params = self.params.get("params", ["VF", "IR", "BV"])
        selected_times = self.params.get("times", ["T0", "168h", "500h", "1000h"])
        selected_sheets = self.params.get("sheets")

        await self.update_progress(20, "加载Excel文件...")

        # 读取Excel
        xl = pd.ExcelFile(file_path)
        all_sheets = xl.sheet_names

        if selected_sheets:
            sheets_to_process = [s for s in all_sheets if s in selected_sheets]
        else:
            sheets_to_process = all_sheets

        await self.update_progress(30, f"分析 {len(sheets_to_process)} 个产品...")

        # 时间配置
        time_configs = self._get_time_configs()

        # 分析数据
        all_product_data = {}
        analysis_results = []

        for idx, sheet_name in enumerate(sheets_to_process):
            progress = 30 + int((idx / len(sheets_to_process)) * 50)
            await self.update_progress(progress, f"处理: {sheet_name}")

            try:
                df = xl.parse(sheet_name, header=None)
                product_data = self._extract_parameter_data(
                    df, sheet_name, time_configs, selected_params, selected_times
                )
                all_product_data[sheet_name] = product_data

                # 生成分析结果
                analysis_results.append(self._generate_analysis_result(
                    sheet_name, product_data, selected_params, selected_times
                ))
            except Exception as e:
                print(f"Error processing sheet {sheet_name}: {e}")

        await self.update_progress(85, "绘制分布图...")

        # 绘制分布图
        chart_path = self._plot_distributions(
            all_product_data, selected_params, selected_times
        )

        await self.update_progress(100, "完成")

        # 统计汇总
        statistics = self._calculate_statistics(all_product_data, selected_params, selected_times)

        return {
            "chart_path": str(chart_path),
            "product_count": len(all_product_data),
            "analysis_results": analysis_results,
            "statistics": statistics,
            "output_files": [str(chart_path)]
        }

    def _get_time_configs(self) -> Dict:
        """获取时间配置"""
        return {
            'T0': {'VF': 2, 'IR': 3, 'BV': 4},
            '168h': {'VF': 6, 'IR': 7, 'BV': 8},
            '500h': {'VF': 10, 'IR': 11, 'BV': 12},
            '1000h': {'VF': 14, 'IR': 15, 'BV': 16}
        }

    def _extract_parameter_data(
        self, df: pd.DataFrame, sheet_name: str,
        time_configs: Dict, selected_params: List[str], selected_times: List[str]
    ) -> Dict:
        """提取参数数据"""
        data = {param: {} for param in selected_params}

        for time_label in selected_times:
            if time_label not in time_configs:
                continue

            col_indices = time_configs[time_label]

            for param in selected_params:
                col_idx = col_indices.get(param)
                if col_idx is None or col_idx >= df.shape[1]:
                    continue

                column_data = df.iloc[:, col_idx]
                raw_values = []

                for value in column_data:
                    num = self._parse_number(value)
                    if num is not None:
                        raw_values.append(num)

                raw_data = np.array(raw_values, dtype=float)
                raw_data = raw_data[~np.isnan(raw_data)]

                # 异常值处理
                clean_data = self._remove_outliers(raw_data) if self.enable_outlier_removal else raw_data

                # 计算统计量
                if clean_data.size > 0:
                    stats_dict = {
                        'mean': float(np.mean(clean_data)),
                        'std': float(np.std(clean_data)),
                        'count': int(clean_data.size),
                        'min': float(np.min(clean_data)),
                        'max': float(np.max(clean_data))
                    }
                else:
                    stats_dict = {'mean': 0, 'std': 0, 'count': 0, 'min': 0, 'max': 0}

                data[param][time_label] = {
                    'data': clean_data,
                    'stats': stats_dict
                }

        return data

    def _parse_number(self, val) -> Optional[float]:
        """解析数值"""
        if val is None:
            return None

        try:
            if isinstance(val, (int, float, np.floating, np.integer)) and not pd.isna(val):
                return float(val)
        except (TypeError, ValueError):
            pass

        s = str(val).strip()
        if s == '' or s.lower() in {'nan', 'none'}:
            return None

        # 清理
        s = s.replace('\u00A0', '').replace('\u3000', '')
        s = s.replace(',', '').replace('，', '').replace(' ', '')

        if re.search(r"[A-Za-z\u4e00-\u9fff]", s):
            return None

        match = re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d+)?", s)
        if match:
            try:
                return float(match.group(0))
            except (ValueError, TypeError):
                return None

        return None

    def _remove_outliers(self, data: np.ndarray) -> np.ndarray:
        """3-sigma异常值移除"""
        if data.size == 0:
            return data

        mean_val = np.mean(data)
        std_val = np.std(data)

        lower_bound = mean_val - self.outlier_sigma * std_val
        upper_bound = mean_val + self.outlier_sigma * std_val

        mask = (data >= lower_bound) & (data <= upper_bound)
        return data[mask]

    def _generate_analysis_result(
        self, sheet_name: str, product_data: Dict,
        selected_params: List[str], selected_times: List[str]
    ) -> Dict:
        """生成分析结果"""
        result = {
            "product_name": sheet_name,
            "parameters": {}
        }

        for param in selected_params:
            if param not in product_data:
                continue

            param_result = {}

            for time_label in selected_times:
                if time_label not in product_data[param]:
                    continue

                stats = product_data[param][time_label]['stats']
                param_result[time_label] = {
                    "mean": round(stats['mean'], 4),
                    "std": round(stats['std'], 4),
                    "count": stats['count']
                }

            # 计算变化率
            if len(selected_times) >= 2:
                first = selected_times[0]
                last = selected_times[-1]

                if first in param_result and last in param_result:
                    first_mean = param_result[first]['mean']
                    last_mean = param_result[last]['mean']

                    if first_mean != 0:
                        change_rate = ((last_mean - first_mean) / first_mean) * 100
                        param_result['change_rate'] = round(change_rate, 4)

            result["parameters"][param] = param_result

        return result

    def _plot_distributions(
        self, all_product_data: Dict, selected_params: List[str], selected_times: List[str]
    ) -> Path:
        """绘制正态分布图"""
        import matplotlib.pyplot as plt

        # 计算子图布局
        n_products = len(all_product_data)
        n_params = len(selected_params)
        total_subplots = n_products * n_params

        if total_subplots <= 3:
            nrows, ncols = 1, total_subplots
        elif total_subplots <= 6:
            nrows, ncols = 2, (total_subplots + 1) // 2
        else:
            ncols = min(4, total_subplots)
            nrows = (total_subplots + ncols - 1) // ncols

        total_width = max(5 * ncols, 8)
        total_height = max(4 * nrows, 6)

        plotter = PlotBase()
        fig, axes = plt.subplots(nrows, ncols, figsize=(total_width, total_height))

        if nrows == 1 and ncols == 1:
            axes = np.array([[axes]])
        elif nrows == 1:
            axes = axes.reshape(1, -1)
        elif ncols == 1:
            axes = axes.reshape(-1, 1)

        axes_flat = axes.flatten()

        # 颜色映射
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown']
        time_colors = {time: colors[i % len(colors)] for i, time in enumerate(selected_times)}

        subplot_idx = 0

        for product_name, product_data in all_product_data.items():
            for param in selected_params:
                if subplot_idx >= len(axes_flat):
                    break

                ax = axes_flat[subplot_idx]

                # 收集数据计算bins
                combined_vals = []
                for time_label in selected_times:
                    if time_label in product_data.get(param, {}):
                        vals = product_data[param][time_label]['data']
                        if len(vals) > 0:
                            combined_vals.append(vals)

                if combined_vals:
                    combined_vals = np.concatenate(combined_vals)
                    bins = np.histogram_bin_edges(combined_vals, bins=15)

                    for time_label in selected_times:
                        if time_label not in product_data.get(param, {}):
                            continue

                        data_info = product_data[param][time_label]
                        clean_data = data_info['data']
                        stat_dict = data_info['stats']

                        if len(clean_data) > 0:
                            # 直方图
                            ax.hist(
                                clean_data, bins=bins, alpha=0.5, density=False,
                                color=time_colors[time_label],
                                label=f"{time_label} (n={stat_dict['count']}, σ={stat_dict['std']:.4f})"
                            )

                            # 正态拟合曲线
                            bin_width = float(np.mean(np.diff(bins)))
                            x = np.linspace(bins[0], bins[-1], 200)
                            y_pdf = stats.norm.pdf(x, stat_dict['mean'], stat_dict['std'])
                            y_scaled = y_pdf * stat_dict['count'] * bin_width
                            ax.plot(x, y_scaled, color=time_colors[time_label], linewidth=1.5, linestyle='--')

                ax.set_title(f'{product_name[:15]}\n{param}', fontsize=10)
                ax.set_xlabel(f'{param} 值', fontsize=9)
                ax.set_ylabel('数量', fontsize=9)
                ax.legend(fontsize=8)
                ax.grid(True, alpha=0.3)

                subplot_idx += 1

        # 隐藏未使用的子图
        for idx in range(subplot_idx, len(axes_flat)):
            axes_flat[idx].set_visible(False)

        plt.tight_layout()

        chart_path = self.generate_output_path("碳化硅JBS二极管参数正态分布图.png")
        plotter.save_plot(str(chart_path), 300)

        return chart_path

    def _calculate_statistics(
        self, all_product_data: Dict, selected_params: List[str], selected_times: List[str]
    ) -> Dict:
        """计算统计汇总"""
        statistics = {}

        for product_name, product_data in all_product_data.items():
            statistics[product_name] = {}

            for param in selected_params:
                statistics[product_name][param] = {}

                for time_label in selected_times:
                    if time_label in product_data.get(param, {}):
                        stats = product_data[param][time_label]['stats']
                        statistics[product_name][param][time_label] = stats

        return statistics