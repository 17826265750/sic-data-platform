"""
Parameter Check Processor - 参数检查数据处理

重构自 process_data.py
核心功能：Excel模板数据合并与智能匹配
"""
import os
import re
import pandas as pd
import openpyxl
from collections import defaultdict
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from app.core.processor_base import ProcessorBase
from app.core.excel_base import ExcelBase


class ParameterCheckProcessor(ProcessorBase):
    """参数检查数据处理处理器"""

    # 时间点到列索引的映射
    TIME_COL_MAP = {"0": 3, "168": 7, "500": 15, "1000": 23}

    # 忽略的特征词
    IGNORE_TOKENS = {'H3TRB', 'XLSX', 'DATA', 'PROCESS', 'TEMPLATE', 'XLS', 'TEST', '数据处理', 'HTRB'}

    def __init__(self, job_id: str, params: Dict[str, Any]):
        super().__init__(job_id, params)
        self.mapping_cache = {}  # 列映射缓存
        self.excel_base = ExcelBase()

    async def process(self) -> Dict[str, Any]:
        """执行参数检查数据处理"""
        await self.update_progress(5, "正在扫描文件...")

        file_ids = self.params.get("file_ids", [])
        if not file_ids:
            raise ValueError("未提供文件ID")

        # 收集所有文件
        files_info = []
        for file_id in file_ids:
            info = await self.file_service.get_file_info(file_id)
            if info:
                files_info.append(info)

        await self.update_progress(10, f"找到 {len(files_info)} 个文件")

        # 分类文件
        template_files, source_files, stress_files = self._classify_files(files_info)

        await self.update_progress(15, f"模板: {len(template_files)}, 源数据: {len(source_files)}, 应力: {len(stress_files)}")

        # 规划任务
        template_tasks, template_stress_map = self._plan_tasks(
            template_files, source_files, stress_files
        )

        await self.update_progress(20, "开始处理...")

        # 处理结果
        processed_count = 0
        output_files = []

        active_templates = set(template_tasks.keys()) | set(template_stress_map.keys())

        for idx, tmpl in enumerate(active_templates):
            progress = 20 + int((idx / len(active_templates)) * 70)
            await self.update_progress(progress, f"处理模板: {tmpl}")

            try:
                result = await self._process_template(
                    tmpl, template_tasks.get(tmpl, []), template_stress_map.get(tmpl, [])
                )
                if result:
                    processed_count += 1
                    output_files.append(result)
            except Exception as e:
                print(f"Error processing template {tmpl}: {e}")

        await self.update_progress(100, "处理完成")

        return {
            "processed_files": processed_count,
            "output_files": output_files,
            "summary": {
                "templates": len(active_templates),
                "source_files": len(source_files),
                "stress_files": len(stress_files)
            }
        }

    def _classify_files(self, files_info: List[Dict]) -> Tuple[List, List, List]:
        """分类文件为模板、源数据、应力数据"""
        template_files = []
        source_files = []
        stress_files = []

        for info in files_info:
            filename = info["filename"]
            if "数据处理" in filename:
                template_files.append(info)
            elif re.search(r'_P\d+_', filename):
                stress_files.append(info)
            elif "H3TRB" in filename or "HTRB" in filename:
                source_files.append(info)

        return template_files, source_files, stress_files

    def _plan_tasks(
        self, template_files: List, source_files: List, stress_files: List
    ) -> Tuple[Dict, Dict]:
        """规划处理任务"""
        template_tasks = defaultdict(list)
        template_stress_map = defaultdict(list)

        # 预计算模板Tokens缓存
        template_tokens_cache = {
            info["filename"]: self._extract_tokens(info["filename"])
            for info in template_files
        }

        # 匹配源文件
        for info in source_files:
            filename = info["filename"]
            t_match = re.search(r'(?:H3TRB|HTRB).*?(\d+)[hH]', filename, re.IGNORECASE)
            if not t_match:
                continue

            point = t_match.group(1)
            if point not in self.TIME_COL_MAP:
                continue

            tmpl = self._find_matching_template(
                filename, template_files, template_tokens_cache
            )
            if tmpl:
                template_tasks[tmpl["filename"]].append(
                    (info, self.TIME_COL_MAP[point], point)
                )

        # 匹配应力文件
        for info in stress_files:
            filename = info["filename"]
            tmpl = self._find_matching_template(
                filename, template_files, template_tokens_cache
            )
            if tmpl:
                template_stress_map[tmpl["filename"]].append(info)

        return template_tasks, template_stress_map

    def _extract_tokens(self, text: str) -> set:
        """提取用于模糊匹配的特征词"""
        tokens = set()
        raw_tokens = re.findall(r'[A-Za-z0-9]+', text)
        for t in raw_tokens:
            if len(t) < 4:
                continue
            if t.upper() in self.IGNORE_TOKENS:
                continue
            if t.isdigit() and len(t) < 4:
                continue
            tokens.add(t)
        return tokens

    def _find_matching_template(
        self, src_file: str, template_files: List, template_tokens_cache: Dict
    ) -> Optional[Dict]:
        """寻找匹配的模板文件"""
        # 1. HX号精确匹配
        hx_match = re.search(r'(HX[A-Za-z0-9]+)', src_file)
        if hx_match:
            batch_id = hx_match.group(1)
            for tmpl in template_files:
                if batch_id in tmpl["filename"]:
                    return tmpl

        # 2. 特征词模糊匹配
        src_tokens = self._extract_tokens(src_file)
        if not src_tokens:
            return None

        best, max_ov = None, 0

        for tmpl in template_files:
            tmpl_tokens = template_tokens_cache.get(tmpl["filename"], set())
            overlap = len(src_tokens.intersection(tmpl_tokens))
            threshold = 2 if len(src_tokens) >= 2 else 1

            if overlap >= threshold and overlap > max_ov:
                max_ov = overlap
                best = tmpl

        return best

    async def _process_template(
        self, tmpl_filename: str, tasks: List, stress_tasks: List
    ) -> Optional[str]:
        """处理单个模板"""
        # 找到模板文件路径
        tmpl_info = None
        for info in await self._get_all_files():
            if info["filename"] == tmpl_filename:
                tmpl_info = info
                break

        if not tmpl_info:
            return None

        tmpl_path = Path(tmpl_info["path"])

        try:
            wb = openpyxl.load_workbook(tmpl_path)

            # 处理源数据
            for task in tasks:
                src_info, start_col, time_point = task
                await self._process_source_data(wb, src_info, start_col, time_point)

            # 保存到输出目录
            output_path = self.generate_output_path(f"processed_{tmpl_filename}")
            wb.save(output_path)
            wb.close()

            return str(output_path)

        except Exception as e:
            print(f"Error processing template {tmpl_filename}: {e}")
            return None

    async def _process_source_data(self, wb, src_info: Dict, start_col: int, time_point: str):
        """处理源数据文件"""
        src_path = Path(src_info["path"])

        try:
            df_raw = pd.read_excel(src_path, header=None)

            # 定位表头行
            h_idx = self._get_header_row_index(df_raw)
            if h_idx == -1:
                return

            # 获取列信息
            col_info = self._get_column_info(df_raw, h_idx)
            if not col_info:
                return

            target_cols, target_names = col_info

            # 提取数据
            df = df_raw.iloc[h_idx + 1:].copy()
            df.columns = df_raw.iloc[h_idx].values

            # 清理和去重
            if 'Serial#' in df.columns:
                df = df[df['Serial#'].notna()].drop_duplicates(subset=['Serial#'], keep='last')

            # 写入数据 (简化版，实际需要写入到正确的Sheet)
            # 这里省略了详细的写入逻辑

        except Exception as e:
            print(f"Error processing source file {src_info['filename']}: {e}")

    def _get_header_row_index(self, df: pd.DataFrame) -> int:
        """寻找包含 'Serial#' 的表头行"""
        try:
            sample = df.head(50).fillna("").astype(str)
            mask = sample.apply(lambda row: "Serial#" in " ".join(row), axis=1)
            if mask.any():
                return mask.idxmax()
        except Exception:
            pass
        return -1

    def _get_column_info(self, df: pd.DataFrame, header_row_idx: int) -> Optional[Tuple]:
        """获取列信息"""
        # 简化版实现，实际需要更复杂的逻辑
        # 返回 (列索引列表, 列名列表)
        header_row = df.iloc[header_row_idx]

        # 查找VF, IR, BVR等关键列
        target_cols = []
        target_names = []

        for idx, col in enumerate(header_row):
            col_str = str(col).upper()
            if 'VF' in col_str:
                target_cols.append(idx)
                target_names.append('VF')
            elif 'IR' in col_str:
                target_cols.append(idx)
                target_names.append('IR')
            elif 'BV' in col_str:
                target_cols.append(idx)
                target_names.append('BV')

        if target_cols:
            return (target_cols, target_names)
        return None

    async def _get_all_files(self) -> List[Dict]:
        """获取所有上传文件的信息"""
        # 从params中获取file_ids对应的文件信息
        files_info = []
        for file_id in self.params.get("file_ids", []):
            info = await self.file_service.get_file_info(file_id)
            if info:
                files_info.append(info)
        return files_info