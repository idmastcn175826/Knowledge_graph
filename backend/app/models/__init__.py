"""数据模型模块，定义API请求和响应的数据结构"""
from .schema import (
    FileInfo,
    UploadFileResponse,
    AlgorithmConfig,
    KGCreateRequest,
    KGProgressResponse,
    EntitySchema,
    RelationSchema,
    KGDetailResponse,
    QARequest,
    QAResponse,
    KGCreateResponse,
    KGQueryRequest,
    KGQueryResponse,
    QAQuery,
    QAAnswer,
    QAHistoryItem,
    QAHistoryResponse
)
from .user import User
from .file import File
from .task import Task
