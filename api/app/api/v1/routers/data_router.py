import logging
import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv

# 导入数据处理相关模块
# from core.agents.formatters import AlpacaFormatter
from app.Fine_tune_datasets.agents.sql_formatters import SqlAlpacaFormatter
from app.Fine_tune_datasets.agents.unstructured_formatter import UnstructuredAlpacaFormatter
from app.Fine_tune_datasets.foundation.data_processor import DataProcessorFactory
from app.Fine_tune_datasets.loaders.data_loaders import FileDataLoader
from app.Fine_tune_datasets.loaders.sql_data_loader import SqlDatabaseDataLoader
from app.Fine_tune_datasets.loaders.unstructured_loader import UnstructuredDataLoader

from app.Fine_tune_datasets.agents.formatters import AlpacaFormatter

# 加载环境变量
load_dotenv()

router = APIRouter()
logger = logging.getLogger(__name__)

# 初始化处理器工厂
processor_factory = DataProcessorFactory()

# 注册加载器
processor_factory.register_loader('file', FileDataLoader)  # json
processor_factory.register_loader('unstructured', UnstructuredDataLoader)  # pdf
processor_factory.register_loader('sql', SqlDatabaseDataLoader)  # 数据库加载器

# 注册格式化器
processor_factory.register_formatter('alpaca', AlpacaFormatter)  # json 结构化数据
processor_factory.register_formatter('unstructured_alpaca', UnstructuredAlpacaFormatter)  # pdf非结构化数据
processor_factory.register_formatter('sql_alpaca', SqlAlpacaFormatter)  # sql数据


# 请求模型
class ConvertRequest(BaseModel):
    source_type: str
    source_info: dict
    output_path: str


@router.post("/convert", summary="转换数据格式")
def convert_data(request: ConvertRequest):
    try:
        params = request.dict()

        # 根据数据源类型自动匹配格式化器
        formatter_type_map = {
            'file': 'alpaca',  # file类型（JSON/CSV）用alpaca格式化器
            'unstructured': 'unstructured_alpaca',  # 非结构化（PDF/Word）用对应格式化器
            'sql': 'sql_alpaca'  # SQL数据库用sql专用格式化器
        }
        formatter_type = formatter_type_map.get(params['source_type'])
        if not formatter_type:
            raise HTTPException(
                status_code=400,
                detail=f"不支持的数据源类型: {params['source_type']}"
            )
        logger.info(f"数据源类型: {params['source_type']}，使用格式化器: {formatter_type}")

        # 创建处理器（确保使用正确的格式化器）
        processor = processor_factory.create_processor(
            source_type=params['source_type'],
            formatter_type=formatter_type,
            source_info=params['source_info'],
            qwen_api_key=os.getenv('QWEN_API_KEY')
        )

        # 加载数据
        logger.info(f"开始加载{params['source_type']}数据")
        data = processor.load_data(params['source_info'])
        if not data:
            raise HTTPException(
                status_code=400,
                detail="数据源返回空数据"
            )
        logger.info(f"成功加载{len(data)}条数据")

        # 转换数据（核心步骤：使用注册的格式化器）
        logger.info("开始转换数据...")
        converted_data = processor.convert(data)

        # 检查转换结果
        if not converted_data:
            raise HTTPException(
                status_code=500,
                detail="数据转换后为空，可能是格式化器未生效或模型调用失败"
            )
        logger.info(f"成功转换{len(converted_data)}条数据")

        # 保存数据
        output_path = params['output_path']
        # 基于输出文件路径创建父目录
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        processor.save_data(converted_data, output_path)

        return {
            "status": "success",
            "output_path": output_path,
            "converted_count": len(converted_data)
        }

    except Exception as e:
        logger.error(f"转换失败: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/health", summary="检查服务健康状态")
def health_check():
    return {
        "status": "healthy",
        "formatters": list(processor_factory.formatters.keys()),
        "loaders": list(processor_factory.loaders.keys())
    }
