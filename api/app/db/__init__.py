# 从base_class导入Base，方便其他模块引用
from app.db.base_class import Base

# 导入所有模型，确保它们被Base.metadata识别
from app.rag.rag_models import RAGCollection, RAGDocument