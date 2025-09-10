import logging
import os
import shutil
from typing import List
import torch
from huggingface_hub.errors import HfHubHTTPError
from sentence_transformers import SentenceTransformer

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 配置 - 使用你的模型名称和本地路径
DEFAULT_MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"  # 模型名称
# 修改为你的实际模型路径
LOCAL_MODEL_DIR = os.getenv(
    "LOCAL_MODEL_DIR",
    r"D:\pycharm_project\models\huggingface-embedding\embeding"
)
os.makedirs(LOCAL_MODEL_DIR, exist_ok=True)  # 确保本地模型目录存在

# 设置国内镜像源
os.environ["HF_ENDPOINT"] = os.getenv("HF_ENDPOINT", "https://hf-mirror.com")


class EmbeddingService:
    """文本嵌入服务，优先使用本地模型，本地不存在则自动下载"""
    _instance = None  # 单例模式，避免重复加载模型

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, model_name: str = DEFAULT_MODEL_NAME):
        """初始化嵌入模型，优先使用本地模型"""
        # 防止重复初始化
        if hasattr(self, '_initialized'):
            return

        self.model_name = model_name
        self.local_model_path = LOCAL_MODEL_DIR  # 直接使用指定目录
        self.model = self._load_model()
        self._initialized = True

    def _has_valid_model(self) -> bool:
        """检查目录下是否存在有效的模型文件"""
        # 模型必须包含的关键文件
        required_files = [
            "config.json",
            "pytorch_model.bin",
            "sentence_bert_config.json",
            "vocab.txt"
        ]

        # 检查是否存在至少3个关键文件（容错处理）
        found_files = 0
        for file in required_files:
            if os.path.exists(os.path.join(self.local_model_path, file)):
                found_files += 1

        return found_files >= 3

    def _load_model(self):
        """加载模型，优先使用本地模型，本地不存在则下载"""
        try:
            # 自动选择计算设备
            device = "cuda" if torch.cuda.is_available() else "cpu"
            logger.info(f"使用计算设备: {device}")

            # 模型参数
            model_kwargs = {
                "device": device,
                "cache_folder": self.local_model_path
            }

            # 检查本地是否有有效模型
            if self._has_valid_model():
                logger.info(f" 加载本地模型: {self.local_model_path}")
                model = SentenceTransformer(self.local_model_path, **model_kwargs)
            else:
                # 本地模型不存在，从网络下载
                logger.info(f" 本地目录未找到有效模型: {self.local_model_path}")
                logger.info(f" 开始下载模型: {self.model_name}")
                logger.info(f" 下载目标路径: {self.local_model_path}")
                model = SentenceTransformer(self.model_name, **model_kwargs)
                self._save_model_to_local(model)

            return model

        except HfHubHTTPError as e:
            logger.error(f" 模型下载失败: {str(e)}")
            raise RuntimeError(f"模型下载失败，请检查网络: {str(e)}")
        except Exception as e:
            logger.error(f" 模型加载失败: {str(e)}")
            raise RuntimeError(f"嵌入模型初始化失败: {str(e)}")

    def _save_model_to_local(self, model: SentenceTransformer):
        """将模型保存到指定目录"""
        try:
            # 清空目录（避免残留文件导致冲突）
            if os.listdir(self.local_model_path):
                for item in os.listdir(self.local_model_path):
                    item_path = os.path.join(self.local_model_path, item)
                    if os.path.isfile(item_path):
                        os.remove(item_path)
                    else:
                        shutil.rmtree(item_path)

            model.save(self.local_model_path)
            logger.info(f" 模型已成功保存到目录: {self.local_model_path}")

        except Exception as e:
            logger.warning(f" 模型保存警告: {str(e)}")

    def embed_texts(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """批量生成文本嵌入向量"""
        if not texts:
            return []

        try:
            embeddings = self.model.encode(
                texts,
                batch_size=batch_size,
                truncation=True,
                show_progress_bar=False
            )
            return embeddings.tolist()

        except Exception as e:
            logger.error(f"文本嵌入失败: {str(e)}")
            raise

    def embed_query(self, query: str) -> List[float]:
        """生成单个查询的嵌入向量"""
        if not query:
            return []

        return self.embed_texts([query])[0]

    # 关键修复：添加兼容方法，保持与调用代码一致
    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        兼容方法：为文本列表生成嵌入向量
        与embed_texts功能相同，用于适配RAGService中的调用
        """
        return self.embed_texts(texts)


# 全局实例（程序启动时预加载）
embedding_service = EmbeddingService()
