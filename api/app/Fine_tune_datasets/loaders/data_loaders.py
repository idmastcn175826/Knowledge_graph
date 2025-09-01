import os
import json
import pandas as pd
from sqlalchemy import create_engine
from app.Fine_tune_datasets.foundation.data_processor import DataLoader

class FileDataLoader(DataLoader):
    """文件数据加载器，支持多种文件格式"""

    def load(self, source_info):
        """
        从文件加载数据

        Args:
            source_info: 包含文件路径和格式的字典

        Returns:
            数据列表
        """
        file_path = source_info.get('path')
        file_format = source_info.get('format', self._infer_format(file_path))

        if not file_path or not os.path.exists(file_path):
            raise ValueError(f"文件路径不存在: {file_path}")

        load_methods = {
            'json': self._load_json,
            'csv': self._load_csv,
            'xlsx': self._load_excel,
            'txt': self._load_text
        }

        if file_format not in load_methods:
            raise ValueError(f"不支持的文件格式: {file_format}")

        return load_methods[file_format](file_path)

    def _infer_format(self, file_path):
        """从文件路径推断文件格式"""
        ext = os.path.splitext(file_path)[1].lower().lstrip('.')
        return ext if ext else 'txt'

    def _load_json(self, file_path):
        """加载JSON文件"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _load_csv(self, file_path):
        """加载CSV文件"""
        df = pd.read_csv(file_path)
        return df.to_dict('records')

    def _load_excel(self, file_path):
        """加载Excel文件"""
        df = pd.read_excel(file_path)
        return df.to_dict('records')

    def _load_text(self, file_path):
        """加载文本文件，每行作为一条记录"""
        with open(file_path, 'r', encoding='utf-8') as f:
            return [{'content': line.strip()} for line in f if line.strip()]


