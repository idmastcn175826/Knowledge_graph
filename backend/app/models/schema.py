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
    id: int = Field(description="用户ID")
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
    """问答请求的 Query 模型（嵌套在 history 中）"""
    kg_id: Optional[str] = None
    question: str
    top_k: int = 5  # 已添加默认值
    use_context: bool = True  # 已添加默认值
    session_id: Optional[str] = None
    # 关键：添加 model_api_key 字段（与接口调用一致，允许为 None）
    model_api_key: Optional[str] = None

    class Config:
        from_attributes = True  # 保持 Pydantic V2 兼容性

class QAAnswer(BaseModel):
    """问答响应的 Answer 模型（嵌套在 history 中）"""
    kg_id: Optional[str]  # 关键：改为 Optional[str]，允许 None
    question: str
    answer: str
    confidence: float
    related_entities: List[Dict]
    related_relations: List[Dict]
    reasoning_steps: List[str]
    response_time: int
    session_id: Optional[str]  # 允许 None
    timestamp: str

class QAHistoryItem(BaseModel):
    """单个问答历史项（嵌套在 history 列表中）"""
    query: QAQuery  # 依赖上述修改后的 QAQuery
    answer: QAAnswer  # 依赖上述修改后的 QAAnswer
    timestamp: str

class QAHistoryResponse(BaseModel):
    """问答历史的顶层响应模型"""
    kg_id: Optional[str]  # 关键：改为 Optional[str]，允许 None（未传 kg_id 时）
    session_id: Optional[str]  # 允许 None（无会话时）
    history: List[QAHistoryItem]  # 依赖上述修改后的 QAHistoryItem
    total: int
    page: int
    page_size: int

    class Config:
        from_attributes = True


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

# 补充缺失的知识图谱列表相关模型
class KnowledgeGraphInfo(BaseModel):
    """知识图谱基本信息模型（用于列表展示）"""
    kg_id: str = Field(description="知识图谱ID")  # 改为 kg_id
    name: str = Field(description="知识图谱名称")
    entity_count: int = Field(default=0, description="实体数量")
    relation_count: int = Field(default=0, description="关系数量")
    create_time: datetime = Field(description="创建时间")
    status: str = Field(default="completed", description="图谱状态")# 图谱状态

class KGListResponse(BaseModel):
    """知识图谱列表响应模型"""
    graphs: List[KnowledgeGraphInfo]
    total: int
    page: int
    page_size: int
    """
    分页说明：
    - total: 总记录数
    - page: 当前页码
    - page_size: 每页记录数
    """
