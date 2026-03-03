"""
Report Generation Processor - 测试报告数据整理处理

重构自 update_report_perfect.py
核心功能：Word报告自动生成
"""
import re
import statistics as stats
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

import pandas as pd
from docx import Document
from docx.table import Table

from app.core.processor_base import ProcessorBase


@dataclass
class TableConfig:
    """表格配置"""
    name: str
    keywords: tuple
    title_keywords: tuple
    duration: str = "1000h"


class ReportGenerationProcessor(ProcessorBase):
    """测试报告生成处理器"""

    # 表格配置
    CONFIGS: List[TableConfig] = [
        TableConfig(
            name="HTRB",
            keywords=("HTRB", "数据处理", "1000H"),
            title_keywords=("HTRB", "高温反偏"),
        ),
        TableConfig(
            name="H3TRB",
            keywords=("H3TRB", "数据处理", "1000H"),
            title_keywords=("H3TRB", "高温高湿"),
        ),
        TableConfig(
            name="HTGB+",
            keywords=("HTGB", "正向", "POS", "+"),
            title_keywords=("HTGB", "高温正向", "正向栅偏"),
        ),
        TableConfig(
            name="HTGB-",
            keywords=("HTGB", "负向", "NEG", "-"),
            title_keywords=("HTGB", "高温负向", "负向栅偏"),
        ),
        TableConfig(
            name="TC",
            keywords=("TC", "数据处理", "1000H"),
            title_keywords=("TC", "温度循环"),
        ),
        TableConfig(
            name="IOL",
            keywords=("IOL", "数据处理"),
            title_keywords=("IOL", "闭锁电流"),
            duration="96h",
        ),
        TableConfig(
            name="AC",
            keywords=("AC", "数据处理"),
            title_keywords=("AC", "交流"),
        ),
    ]

    def __init__(self, job_id: str, params: Dict[str, Any]):
        super().__init__(job_id, params)
        self.template_id = params.get("template_id")
        self.data_file_id = params.get("data_file_id")
        self.report_type = params.get("report_type", "HTRB")

    async def process(self) -> Dict[str, Any]:
        """执行报告生成"""
        await self.update_progress(10, "加载模板文件...")

        if not self.template_id or not self.data_file_id:
            raise ValueError("未提供模板文件ID或数据文件ID")

        # 获取文件
        template_info = await self.file_service.get_file_info(self.template_id)
        data_info = await self.file_service.get_file_info(self.data_file_id)

        if not template_info or not data_info:
            raise ValueError("模板文件或数据文件不存在")

        template_path = Path(template_info["path"])
        data_path = Path(data_info["path"])

        await self.update_progress(20, "读取数据文件...")

        # 读取Excel数据
        df = pd.read_excel(data_path)

        await self.update_progress(40, "加载Word模板...")

        # 加载Word文档
        doc = Document(template_path)

        await self.update_progress(50, "匹配表格配置...")

        # 获取表格配置
        config = self._get_table_config(self.report_type)

        await self.update_progress(60, "查找并填充表格...")

        # 处理表格
        tables_updated = 0
        fields_updated = 0

        for table in doc.tables:
            result = self._process_table(table, df, config)
            if result:
                tables_updated += 1
                fields_updated += result

        await self.update_progress(90, "保存报告...")

        # 保存报告
        output_name = self.params.get("output_name", f"报告_{self.report_type}.docx")
        output_path = self.generate_output_path(output_name)
        doc.save(str(output_path))

        await self.update_progress(100, "完成")

        return {
            "report_path": str(output_path),
            "tables_updated": tables_updated,
            "fields_updated": fields_updated,
            "output_files": [str(output_path)]
        }

    def _get_table_config(self, report_type: str) -> Optional[TableConfig]:
        """获取报告类型配置"""
        for config in self.CONFIGS:
            if config.name == report_type:
                return config
        return self.CONFIGS[0]  # 默认返回HTRB配置

    def _process_table(self, table: Table, df: pd.DataFrame, config: TableConfig) -> int:
        """处理单个表格"""
        # 检查表格是否匹配配置
        table_text = self._get_table_text(table)

        if not any(kw in table_text for kw in config.title_keywords):
            return 0

        fields_updated = 0

        # 查找数据列
        data_columns = self._find_data_columns(df)

        # 填充表格
        for row_idx, row in enumerate(table.rows):
            for col_idx, cell in enumerate(row.cells):
                cell_text = cell.text.strip()

                # 尝试匹配并填充数据
                value = self._find_matching_value(cell_text, df, data_columns)
                if value is not None:
                    cell.text = str(value)
                    fields_updated += 1

        return fields_updated

    def _get_table_text(self, table: Table) -> str:
        """获取表格中的所有文本"""
        texts = []
        for row in table.rows:
            for cell in row.cells:
                texts.append(cell.text)
        return " ".join(texts)

    def _find_data_columns(self, df: pd.DataFrame) -> Dict[str, int]:
        """查找数据列索引"""
        columns = {}

        for idx, col in enumerate(df.columns):
            col_str = str(col).upper()

            if 'VF' in col_str:
                columns['VF'] = idx
            elif 'IR' in col_str:
                columns['IR'] = idx
            elif 'BV' in col_str:
                columns['BV'] = idx
            elif 'SERIAL' in col_str or '#' in col_str:
                columns['Serial'] = idx

        return columns

    def _find_matching_value(
        self, cell_text: str, df: pd.DataFrame, columns: Dict[str, int]
    ) -> Optional[Any]:
        """查找匹配的值"""
        cell_upper = cell_text.upper()

        # 匹配VF
        if 'VF' in cell_upper:
            return self._calculate_column_stats(df, columns.get('VF'))
        # 匹配IR
        elif 'IR' in cell_upper:
            return self._calculate_column_stats(df, columns.get('IR'))
        # 匹配BV
        elif 'BV' in cell_upper:
            return self._calculate_column_stats(df, columns.get('BV'))

        return None

    def _calculate_column_stats(
        self, df: pd.DataFrame, col_idx: Optional[int]
    ) -> Optional[str]:
        """计算列统计值"""
        if col_idx is None or col_idx >= len(df.columns):
            return None

        col_data = df.iloc[:, col_idx]
        numeric_data = pd.to_numeric(col_data, errors='coerce').dropna()

        if numeric_data.empty:
            return None

        mean_val = numeric_data.mean()
        std_val = numeric_data.std()

        return f"{mean_val:.4f} ± {std_val:.4f}"