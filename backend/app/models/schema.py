from datetime import datetime
from typing import List, Optional, Dict, Any, Union

from pydantic import BaseModel, Field, EmailStr


class UserCreate(BaseModel):
    """用户注册请求模型"""
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="电子邮箱")
    password: str = Field(description="密码")
    full_name: Optional[str] = Field(default=None, description="全名")

class UserResponse(BaseModel):
    """用户信息响应模型"""
    id: str = Field(description="用户ID")
    username: str = Field(description="用户名")
    email: EmailStr = Field(description="电子邮箱")
    full_name: Optional[str] = Field(default=None, description="全名")
    role: str = Field(default="user", description="用户角色")

class Token(BaseModel):
    """登录令牌响应模型"""
    access_token: str = Field(description="访问令牌")
    token_type: str = Field(description="令牌类型")

class TokenPayload(BaseModel):
    """令牌载荷模型"""
    sub: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class QAQuery(BaseModel):
    """问答查询请求模型"""
    kg_id: str = Field(description="知识图谱ID")
    question: str = Field(description="用户的问题")
    top_k: int = Field(default=5, ge=1, le=20, description="返回相关实体/关系的数量")
    use_context: bool = Field(default=True, description="是否使用上下文信息")
    session_id: Optional[str] = Field(default=None, description="会话ID，用于多轮对话")

class QAAnswer(BaseModel):
    """问答回答响应模型"""
    kg_id: str
    question: str
    answer: str = Field(description="问题的答案")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="答案的置信度")
    related_entities: Optional[List[Dict]] = Field(default=None, description="相关实体列表")
    related_relations: Optional[List[Dict]] = Field(default=None, description="相关关系列表")
    reasoning_steps: Optional[List[str]] = Field(default=None, description="推理步骤")
    response_time: float = Field(description="响应时间（秒）")
    session_id: Optional[str] = Field(default=None, description="会话ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="回答生成时间")

class QAHistoryItem(BaseModel):
    """问答历史项模型"""
    query: QAQuery
    answer: QAAnswer
    timestamp: datetime = Field(default_factory=datetime.now)

class QAHistoryResponse(BaseModel):
    """问答历史响应模型"""
    kg_id: str
    session_id: str
    history: List[QAHistoryItem] = Field(default_factory=list, description="问答历史列表")
    total: int = Field(description="历史记录总数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页记录数")

class KGQueryResponse(BaseModel):
    """知识图谱查询响应模型"""
    kg_id: str
    query: Union[str, Dict]
    total: int = Field(description="匹配结果的总数量")
    entities: Optional[List[Dict]] = Field(default=None, description="查询到的实体列表")
    relations: Optional[List[Dict]] = Field(default=None, description="查询到的关系列表")
    results: Optional[List[Dict]] = Field(default=None, description="组合后的查询结果")
    answer: Optional[str] = Field(default=None, description="针对自然语言查询的回答总结")
    execution_time: float = Field(description="查询执行时间（秒）")
    message: Optional[str] = Field(default=None, description="查询状态消息")

class KGQueryRequest(BaseModel):
    """知识图谱查询请求模型"""
    kg_id: str
    query: Union[str, Dict] = Field(description="可以是自然语言查询或结构化查询条件")
    query_type: str = Field(default="natural", description="查询类型：natural（自然语言）或 structured（结构化）")
    top_k: int = Field(default=10, ge=1, le=100, description="返回结果的最大数量")
    include_entities: bool = Field(default=True, description="是否返回实体信息")
    include_relations: bool = Field(default=True, description="是否返回关系信息")
    filters: Optional[Dict[str, Any]] = Field(default=None, description="额外的过滤条件，如实体类型、关系类型等")

class KGCreateResponse(BaseModel):
    """知识图谱创建响应模型"""
    success: bool
    task_id: str
    kg_id: Optional[str] = None
    message: Optional[str] = None
    start_time: datetime = Field(default_factory=datetime.now)
    estimated_time: Optional[int] = None  # 预计完成时间（秒）

# 确保其他模型定义如下（保持不变）：
class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    upload_time: datetime = Field(default_factory=datetime.now)

class UploadFileResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    file_id: Optional[str] = None
    message: Optional[str] = None
    file_info: Optional[FileInfo] = None

class FileInfo(BaseModel):
    """文件信息模型"""
    file_id: str
    file_name: str
    file_size: int
    file_type: str
    upload_time: datetime = Field(default_factory=datetime.now)

class UploadFileResponse(BaseModel):
    """文件上传响应模型"""
    success: bool
    file_id: Optional[str] = None
    message: Optional[str] = None
    file_info: Optional[FileInfo] = None

class AlgorithmConfig(BaseModel):
    """算法配置模型"""
    preprocess: str = Field(default="simhash")
    entity_extraction: str = Field(default="bert")
    relation_extraction: str = Field(default="qwen")
    knowledge_completion: str = Field(default="transe")

class KGCreateRequest(BaseModel):
    """知识图谱创建请求模型"""
    file_ids: List[str]
    kg_name: str
    algorithms: AlgorithmConfig
    model_api_key: Optional[str] = None
    enable_completion: bool = Field(default=True)
    enable_visualization: bool = Field(default=True)

class KGProgressResponse(BaseModel):
    """知识图谱构建进度响应模型"""
    task_id: str
    progress: int = Field(default=0, ge=0, le=100)
    status: str = Field(default="pending")  # pending, processing, completed, failed
    stage: str = Field(default="准备中")
    message: Optional[str] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None

class EntitySchema(BaseModel):
    """实体数据模型"""
    id: str
    name: str
    type: str
    start_pos: Optional[int] = None
    end_pos: Optional[int] = None
    merged_ids: Optional[List[str]] = None
    attributes: Optional[Dict[str, Any]] = None

class RelationSchema(BaseModel):
    """关系数据模型"""
    id: str
    entity1_id: str
    entity2_id: str
    relation_type: str
    confidence: Optional[float] = None

class KGDetailResponse(BaseModel):
    """知识图谱详情响应模型"""
    kg_id: str
    kg_name: str
    entity_count: int
    relation_count: int
    create_time: datetime
    update_time: datetime
    entities: Optional[List[EntitySchema]] = None
    relations: Optional[List[RelationSchema]] = None

class QARequest(BaseModel):
    """问答请求模型"""
    kg_id: str
    question: str
    top_k: int = Field(default=5)

class QAResponse(BaseModel):
    """问答响应模型"""
    question: str
    answer: str
    related_entities: Optional[List[EntitySchema]] = None
    related_relations: Optional[List[RelationSchema]] = None
    confidence: float = Field(default=0.0)
    reasoning_steps: Optional[List[str]] = None
