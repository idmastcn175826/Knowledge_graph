import logging
import os
import re
from typing import Tuple, Optional

import openpyxl
import pdfplumber
from docx import Document
from tika import parser as tika_parser

logger = logging.getLogger(__name__)


class FileParser:
    """文件解析工具类，支持多种格式文件的文本提取"""

    def __init__(self):
        """初始化文件解析器"""
        # 初始化 tika（如果需要）
        try:
            import tika
            tika.initVM()
        except Exception as e:
            logger.warning(f"初始化tika失败，某些文件格式可能无法解析: {str(e)}")

    def parse_file(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """
        解析文件并提取文本内容

        Args:
            file_path: 文件路径

        Returns:
            三元组 (是否成功, 文本内容, 错误信息)
        """
        if not os.path.exists(file_path):
            return False, "", f"文件不存在: {file_path}"

        # 获取文件扩展名
        file_ext = os.path.splitext(file_path)[1].lower()

        try:
            if file_ext in ['.txt']:
                return self._parse_text(file_path)
            elif file_ext in ['.pdf']:
                return self._parse_pdf(file_path)
            elif file_ext in ['.docx']:
                return self._parse_docx(file_path)
            elif file_ext in ['.doc']:
                return self._parse_doc(file_path)
            elif file_ext in ['.xlsx', '.xls']:
                return self._parse_excel(file_path)
            else:
                # 尝试使用tika解析其他格式
                return self._parse_with_tika(file_path)
        except Exception as e:
            error_msg = f"解析文件 {file_path} 失败: {str(e)}"
            logger.error(error_msg)
            return False, "", error_msg

    def _parse_text(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """解析文本文件"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            # 清理文本
            content = self._clean_text(content)
            return True, content, None
        except Exception as e:
            return False, "", str(e)

    def _parse_pdf(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """解析PDF文件"""
        try:
            content = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        content.append(text)
            full_text = '\n'.join(content)
            full_text = self._clean_text(full_text)
            return True, full_text, None
        except Exception as e:
            return False, "", str(e)

    def _parse_docx(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """解析docx文件"""
        try:
            doc = Document(file_path)
            content = []
            for para in doc.paragraphs:
                if para.text.strip():
                    content.append(para.text)
            full_text = '\n'.join(content)
            full_text = self._clean_text(full_text)
            return True, full_text, None
        except Exception as e:
            return False, "", str(e)

    def _parse_doc(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """解析doc文件（使用tika）"""
        return self._parse_with_tika(file_path)

    def _parse_excel(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """解析Excel文件"""
        try:
            wb = openpyxl.load_workbook(file_path, read_only=True)
            content = []

            for sheet_name in wb.sheetnames:
                sheet = wb[sheet_name]
                content.append(f"工作表: {sheet_name}")

                for row in sheet.iter_rows(values_only=True):
                    row_text = [str(cell) if cell is not None else "" for cell in row]
                    row_text = [t for t in row_text if t.strip()]
                    if row_text:
                        content.append('\t'.join(row_text))

            full_text = '\n'.join(content)
            full_text = self._clean_text(full_text)
            return True, full_text, None
        except Exception as e:
            return False, "", str(e)

    def _parse_with_tika(self, file_path: str) -> Tuple[bool, str, Optional[str]]:
        """使用tika解析其他格式文件"""
        try:
            parsed = tika_parser.from_file(file_path)
            content = parsed.get('content', '') or ''
            content = self._clean_text(content)
            return True, content, None
        except Exception as e:
            return False, "", str(e)

    def _clean_text(self, text: str) -> str:
        """清理文本内容，去除多余空白和特殊字符"""
        # 去除多余的空白字符
        text = re.sub(r'\s+', ' ', text)
        # 去除特殊字符
        text = re.sub(r'[^\w\s.,!?;:\'\"()\[\]]', '', text)
        # 去除首尾空白
        return text.strip()
