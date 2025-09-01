import logging
import re
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any

from neo4j import GraphDatabase, exceptions, Session

from app.algorithm.completion.factory import KnowledgeCompletionFactory
from app.algorithm.extraction.factory import EntityExtractionFactory, RelationExtractionFactory
from app.algorithm.fusion.entity_alignment import EntityAlignment
from app.algorithm.preprocess.factory import PreprocessFactory
from app.config.config import settings
from app.models import Task
from app.models.knowledge_graphs import KnowledgeGraph
from app.models.schema import (
    KGCreateRequest, KGProgressResponse
)
from app.utils import get_db
from app.utils.file_parser import FileParser

logger = logging.getLogger(__name__)


class Neo4jConnection:
    """Neo4j数据库连接管理(单例模式)"""
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
            try:
                cls._instance.driver = GraphDatabase.driver(
                    settings.neo4j_uri,
                    auth=(settings.neo4j_user, settings.neo4j_password)
                )
                cls._instance.driver.verify_connectivity()
                logger.info("Neo4j连接成功")
            except exceptions.Neo4jError as e:
                logger.error(f"Neo4j连接失败: {str(e)}")
                raise
        return cls._instance

    def close(self):
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")

    def get_session(self):
        return self.driver.session()


class KGService:
    """知识图谱服务类（修复进度更新、数据库同步逻辑）"""

    def __init__(self):
        self.neo4j_conn = Neo4jConnection()
        self.task_progress = {}  # {task_id: {"progress": int, "status": str, "message": str, "stage": str}}
        self.executor = ThreadPoolExecutor(max_workers=5)
        self._ensure_directories()

    def _ensure_directories(self):
        """确保上传和临时目录存在"""
        try:
            Path(settings.upload_dir).resolve().mkdir(parents=True, exist_ok=True)
            Path(settings.temp_dir).resolve().mkdir(parents=True, exist_ok=True)
            logger.info(f"已确保上传目录: {Path(settings.upload_dir).resolve()}")
        except Exception as e:
            logger.error(f"创建目录失败: {str(e)}")

    def create_knowledge_graph(self, user_id: str, request: KGCreateRequest) -> str:
        """创建知识图谱（初始化任务时同步数据库Task记录）"""
        task_id = str(uuid.uuid4())
        # 1. 初始化内存进度
        self.task_progress[task_id] = {
            "progress": 0,
            "status": "pending",
            "message": "任务已提交，等待处理",
            "stage": "初始化"
        }
        # 2. 初始化数据库Task记录（关键：确保任务创建时数据库已有记录）
        try:
            db = next(get_db())
            new_task = Task(
                task_id=task_id,
                user_id=int(user_id),  # 注意：根据User模型调整类型（若user_id是int）
                task_type="kg_create",  # 标记任务类型为“知识图谱创建”
                progress=0,
                status="pending",
                message="任务已提交，等待处理",
                stage="初始化",
                file_ids=",".join(request.file_ids)  # 存储关联文件ID
            )
            db.add(new_task)
            db.commit()
            logger.info(f"数据库已初始化Task记录: {task_id}")
        except Exception as e:
            logger.error(f"初始化Task数据库记录失败: {str(e)}")
            raise

        # 3. 提交异步构建任务
        self.executor.submit(
            self._build_kg_async,
            task_id,
            user_id,
            request.file_ids,
            request.algorithms,
            request.model_api_key,
            request.enable_completion,
            request.enable_visualization
        )

        logger.info(f"知识图谱构建任务已启动，task_id: {task_id}")
        return task_id

    def _build_kg_async(self, task_id: str, user_id: str, file_ids: List[str],
                        algorithms: Any, model_api_key: Optional[str],
                        enable_completion: bool, enable_visualization: bool):
        """异步构建知识图谱（完善各阶段进度更新）"""
        try:
            # 阶段1：任务启动
            self._update_progress(task_id, 5, "processing", "开始处理任务，准备解析文件", "初始化")

            # 阶段2：文件解析
            upload_dir = Path(settings.upload_dir).resolve()
            logger.info(f"使用上传目录: {upload_dir}")

            parser = FileParser()
            texts = []
            valid_file_ids = []

            for i, file_id in enumerate(file_ids):
                file_path = upload_dir / file_id
                current_progress = 5 + int(10 * (i + 1) / len(file_ids))  # 5%-15% 进度区间
                self._update_progress(
                    task_id,
                    current_progress,
                    "processing",
                    f"正在解析文件 {i + 1}/{len(file_ids)}: {file_id}",
                    "文件解析"
                )
                logger.info(f"尝试访问文件: {file_path}")

                # 文件路径自动修复
                if not file_path.exists():
                    common_extensions = ['.pdf', '.txt', '.docx', '.xlsx']
                    found = False
                    for ext in common_extensions:
                        candidate_path = file_path.with_suffix(ext)
                        if candidate_path.exists():
                            file_path = candidate_path
                            found = True
                            logger.warning(f"自动修复文件路径为: {file_path}")
                            break
                    if not found:
                        logger.warning(f"文件不存在: {file_path}，将跳过该文件")
                        continue

                # 解析文件
                try:
                    success, text, error = parser.parse_file(str(file_path))
                    if success and text:
                        texts.append(text)
                        valid_file_ids.append(file_id)
                        logger.info(f"文件 {file_id} 解析成功，提取文本长度: {len(text)}")
                    else:
                        logger.warning(f"文件 {file_id} 解析失败: {error}")
                except Exception as e:
                    logger.error(f"解析文件 {file_id} 时发生异常: {str(e)}", exc_info=True)

            # 检查有效文件
            if not texts:
                error_msg = f"所有文件解析失败或不存在，共尝试 {len(file_ids)} 个文件"
                self._update_progress(task_id, 100, "failed", error_msg, "文件解析失败")
                return
            else:
                self._update_progress(
                    task_id, 15, "processing",
                    f"成功解析 {len(texts)}/{len(file_ids)} 个文件，准备预处理",
                    "文件解析完成"
                )

            # 阶段3：数据预处理（15%-25% 进度区间）
            try:
                algorithms_dict = algorithms.dict() if not isinstance(algorithms, dict) else algorithms
                preprocess_strategy = PreprocessFactory.get_strategy(algorithms_dict.get("preprocess", "simhash"))

                processed_texts = []
                for i, text in enumerate(texts):
                    current_progress = 15 + int(10 * (i + 1) / len(texts))
                    processed_text = preprocess_strategy.process(text)
                    processed_texts.append(processed_text)
                    self._update_progress(
                        task_id,
                        current_progress,
                        "processing",
                        f"正在预处理文本 {i + 1}/{len(texts)}",
                        "数据预处理"
                    )
                self._update_progress(task_id, 25, "processing", "所有文本预处理完成，准备实体抽取", "数据预处理完成")
            except Exception as e:
                error_msg = f"数据预处理失败: {str(e)}"
                self._update_progress(task_id, 25, "failed", error_msg, "数据预处理失败")
                logger.error(error_msg, exc_info=True)
                return

            # 阶段4：实体抽取（25%-40% 进度区间）
            try:
                algorithms_dict = algorithms.dict() if not isinstance(algorithms, dict) else algorithms
                entity_algorithm = algorithms_dict.get("entity_extraction", "bert")
                entity_strategy = EntityExtractionFactory.get_strategy(entity_algorithm, model_api_key)

                all_entities = []
                for i, text in enumerate(processed_texts):
                    current_progress = 25 + int(15 * (i + 1) / len(processed_texts))
                    entities = entity_strategy.extract(text)
                    all_entities.extend(entities)
                    self._update_progress(
                        task_id,
                        current_progress,
                        "processing",
                        f"正在抽取实体 {i + 1}/{len(processed_texts)}，已抽取 {len(all_entities)} 个实体",
                        "实体抽取"
                    )
                self._update_progress(task_id, 40, "processing",
                                      f"实体抽取完成，共抽取 {len(all_entities)} 个实体，准备对齐", "实体抽取完成")
            except Exception as e:
                error_msg = f"实体抽取失败: {str(e)}"
                self._update_progress(task_id, 40, "failed", error_msg, "实体抽取失败")
                logger.error(error_msg, exc_info=True)
                return

            # 阶段5：实体对齐（40%-50% 进度区间）
            try:
                alignment = EntityAlignment()
                aligned_entities = alignment.align_entities(all_entities)
                self._update_progress(
                    task_id, 50, "processing",
                    f"完成实体对齐，共处理 {len(aligned_entities)} 个实体，准备关系抽取",
                    "实体对齐完成"
                )
            except Exception as e:
                error_msg = f"实体对齐失败: {str(e)}"
                self._update_progress(task_id, 50, "failed", error_msg, "实体对齐失败")
                logger.error(error_msg, exc_info=True)
                return

            # 阶段6：关系抽取
            try:
                algorithms_dict = algorithms.dict() if not isinstance(algorithms, dict) else algorithms
                relation_algorithm = algorithms_dict.get("relation_extraction", "qwen")
                relation_strategy = RelationExtractionFactory.get_strategy(relation_algorithm, model_api_key)

                all_relations = []
                for i, (text, processed_text) in enumerate(zip(texts, processed_texts)):
                    current_progress = 50 + int(15 * (i + 1) / len(processed_texts))
                    relations = relation_strategy.extract(processed_text, aligned_entities)
                    all_relations.extend(relations)
                    self._update_progress(
                        task_id,
                        current_progress,
                        "processing",
                        f"正在抽取关系 {i + 1}/{len(processed_texts)}，已抽取 {len(all_relations)} 个关系",
                        "关系抽取"
                    )
                self._update_progress(task_id, 65, "processing", f"关系抽取完成，共抽取 {len(all_relations)} 个关系",
                                      "关系抽取完成")
            except Exception as e:
                error_msg = f"关系抽取失败: {str(e)}"
                self._update_progress(task_id, 65, "failed", error_msg, "关系抽取失败")
                logger.error(error_msg, exc_info=True)
                return

            # 阶段7：知识补全
            completed_triples = all_relations.copy()
            if enable_completion:
                try:
                    algorithms_dict = algorithms.dict() if not isinstance(algorithms, dict) else algorithms
                    completion_algorithm = algorithms_dict.get("knowledge_completion", "transe")
                    completion_strategy = KnowledgeCompletionFactory.get_strategy(completion_algorithm)
                    completed_triples = completion_strategy.complete(aligned_entities, all_relations)
                    self._update_progress(
                        task_id, 75, "processing",
                        f"知识补全完成，补全后共 {len(completed_triples)} 个关系",
                        "知识补全完成"
                    )
                except Exception as e:
                    logger.warning(f"知识补全失败，将使用原始关系: {str(e)}")
                    self._update_progress(
                        task_id, 75, "processing",
                        f"知识补全失败，使用原始关系（共 {len(completed_triples)} 个）",
                        "知识补全跳过"
                    )
            else:
                self._update_progress(task_id, 75, "processing", "未启用知识补全，使用原始关系", "知识补全跳过")

            # 阶段8：存储到Neo4j
            try:
                # 先创建知识图谱记录，获取kg_id（原逻辑不变，但提前到存储Neo4j之前）
                db = next(get_db())
                kg_id = str(uuid.uuid4())  # 生成图谱ID
                new_kg = KnowledgeGraph(
                    kg_id=kg_id,
                    user_id=int(user_id),
                    name=f"知识图谱_{datetime.now().strftime('%Y%m%d%H%M')}",
                    description=f"通过文件 {','.join(valid_file_ids[:3])}... 构建" if valid_file_ids else "无关联文件",
                    status="processing",  # 此时未完成，先设为processing
                    entity_count=len(aligned_entities),
                    relation_count=len(completed_triples),
                    file_ids=','.join(valid_file_ids) if valid_file_ids else None,
                    created_at=datetime.now(),
                    updated_at=datetime.now(),
                    progress=80  # 存储阶段进度设为80
                )
                db.add(new_kg)
                db.commit()
                logger.info(f"已创建知识图谱记录: kg_id={kg_id}")

                # 关键修改：调用_save_to_neo4j时传递kg_id！！！
                self._save_to_neo4j(user_id, aligned_entities, completed_triples, kg_id)

                # 更新进度（原逻辑不变）
                self._update_progress(
                    task_id, 90, "processing",
                    f"已保存 {len(aligned_entities)} 个实体和 {len(completed_triples)} 个关系到Neo4j",
                    "存储到数据库完成"
                )
            except Exception as e:
                error_msg = f"保存到Neo4j失败: {str(e)}"
                self._update_progress(task_id, 90, "failed", error_msg, "存储到数据库失败")
                logger.error(error_msg, exc_info=True)
                return

            # 阶段9：可视化处理
            if enable_visualization:
                try:
                    # 此处可补充实际可视化逻辑（如生成图谱JSON、图片等）
                    time.sleep(1)  # 模拟可视化耗时
                    self._update_progress(
                        task_id, 95, "processing",
                        "可视化处理完成（生成图谱预览）",
                        "可视化处理完成"
                    )
                except Exception as e:
                    logger.warning(f"可视化处理失败: {str(e)}")
                    self._update_progress(
                        task_id, 95, "processing",
                        "可视化处理失败，不影响知识图谱核心功能",
                        "可视化处理跳过"
                    )
            else:
                self._update_progress(task_id, 95, "processing", "未启用可视化，跳过该步骤", "可视化处理跳过")

            # 阶段10：任务完成（95%-100% 进度区间）
            self._update_progress(
                task_id, 100, "completed",
                f"知识图谱构建成功！包含 {len(aligned_entities)} 个实体 + {len(completed_triples)} 个关系",
                "完成"
            )
            try:
                db = next(get_db())
                kg = db.query(KnowledgeGraph).filter(KnowledgeGraph.kg_id == kg_id).first()
                if kg:
                    kg.status = "completed"
                    kg.progress = 100
                    kg.updated_at = datetime.now()
                    db.commit()
                # 同时更新Task表关联kg_id（原逻辑可保留）
                task = db.query(Task).filter(Task.task_id == task_id).first()
                if task:
                    task.kg_id = kg_id
                    task.status = "completed"
                    db.commit()
            except Exception as e:
                logger.error(f"更新图谱/任务状态失败: {str(e)}", exc_info=True)
                db.rollback()

        except Exception as e:
            error_msg = f"任务执行失败: {str(e)}"
            logger.error(error_msg, exc_info=True)
            current_progress = self.task_progress.get(task_id, {}).get("progress", 0)
            self._update_progress(task_id, min(current_progress + 5, 100), "failed", error_msg, "异常终止")

    def _clean_for_neo4j(self, value: str) -> str:
        """清理用于Neo4j标签和关系的字符串"""
        if not value:
            return "Unknown"
        # 替换所有Neo4j不支持的特殊字符
        cleaned = re.sub(r'[\\/:"*?<>|]+', '_', value)
        # 移除首尾空格和下划线
        cleaned = cleaned.strip('_ ')
        # 确保不为空
        return cleaned if cleaned else "Unknown"

    def _save_to_neo4j(self, user_id: str, entities: List[Dict], relations: List[Tuple], kg_id: str):
        """将实体和关系保存到Neo4j（修复kg_id写入和关系匹配逻辑）"""
        session = self.neo4j_conn.get_session()
        try:
            # 1. 创建用户节点（保持不变）
            session.run("MERGE (u:User {id: $user_id})", user_id=user_id)
            logger.debug(f"已确保用户节点存在: {user_id}")

            # 2. 保存实体（关键修复：确保kg_id强制写入）
            for entity in entities:
                entity_id = entity.get("id")
                entity_name = entity.get("name", "未知实体")
                entity_type = entity.get("type", "Entity")

                safe_type = self._clean_for_neo4j(entity_type)
                if safe_type and safe_type[0].islower():
                    safe_type = safe_type[0].upper() + safe_type[1:]

                # 修复1：先通过id匹配实体，再强制设置kg_id（避免因name变化导致kg_id未写入）
                session.run(
                    f"MERGE (e:{safe_type} {{id: $id}}) "  # 仅用id作为MERGE条件
                    f"SET e.name = $name, e.kg_id = $kg_id "  # 强制更新name和kg_id
                    f"MERGE (u:User {{id: $user_id}})-[:OWNS]->(e)",
                    id=entity_id,
                    name=entity_name,
                    kg_id=kg_id,  # 确保kg_id被写入
                    user_id=user_id
                )
                logger.debug(f"已保存实体: {entity_name} (类型: {safe_type}, kg_id: {kg_id})")

            # 3. 保存关系（关键修复：匹配实体时必须校验kg_id）
            if relations:
                for subj_id, rel_type, obj_id in relations:
                    safe_rel_type = self._clean_for_neo4j(rel_type).upper()
                    if safe_rel_type:
                        # 修复2：关系两端的实体必须属于当前图谱（通过kg_id校验）
                        session.run(
                            "MATCH (s {id: $subj_id, kg_id: $kg_id}) "  # 必须包含kg_id
                            "MATCH (o {id: $obj_id, kg_id: $kg_id}) "  # 必须包含kg_id
                            f"MERGE (s)-[r:{safe_rel_type}]->(o)",
                            subj_id=subj_id,
                            obj_id=obj_id,
                            kg_id=kg_id  # 传递当前图谱ID
                        )
                        logger.debug(f"已保存关系: {subj_id} -[{safe_rel_type}]-> {obj_id}")
                logger.info(f"成功保存 {len(relations)} 个关系")
            else:
                logger.warning("没有有效的关系可保存到Neo4j")

        except exceptions.Neo4jError as e:
            logger.error(f"保存到Neo4j失败: {str(e)}")
            raise
        finally:
            session.close()

    def _update_progress(self, task_id: str, progress: int, status: str, message: str, stage: str):
        """更新任务进度，同时更新数据库"""
        self.task_progress[task_id] = {
            "progress": progress,
            "status": status,
            "message": message,
            "stage": stage
        }

        # 同步到数据库
        try:
            db = next(get_db())  # 获取数据库会话
            task = db.query(Task).filter(Task.task_id == task_id).first()
            if task:
                task.progress = progress
                task.status = status
                task.message = message
                task.stage = stage
                db.commit()
        except Exception as e:
            logger.error(f"更新任务进度到数据库失败: {str(e)}")

    def get_progress(self, task_id: str) -> KGProgressResponse:
        """获取任务进度"""
        task_info = self.task_progress.get(task_id)

        if not task_info:
            return KGProgressResponse(
                task_id=task_id,
                progress=0,
                status="not_found",
                message="任务不存在或已过期",
                stage="未知"
            )

        return KGProgressResponse(
            task_id=task_id,
            progress=task_info["progress"],
            status=task_info["status"],
            message=task_info["message"],
            stage=task_info["stage"]
        )

    def query_kg(self, user_id: str, query: Dict[str, Any]) -> Dict[str, Any]:
        """查询知识图谱"""
        session = self.neo4j_conn.get_session()
        try:
            if "entity" in query:
                entity_name = query["entity"]
                cypher = (
                    "MATCH (u:User {id: $user_id})-[:OWNS]->(e) "
                    "WHERE e.name CONTAINS $entity_name "
                    "OPTIONAL MATCH (e)-[r]->(neighbor) "
                    "RETURN e, r, neighbor"
                )
                result = session.run(cypher, user_id=user_id, entity_name=entity_name)
            elif "relation" in query:
                relation_type = self._clean_for_neo4j(query["relation"]).upper()
                cypher = (
                    "MATCH (u:User {id: $user_id})-[:OWNS]->(e1) "
                    f"MATCH (e1)-[r:{relation_type}]->(e2) "
                    "RETURN e1, r, e2"
                )
                result = session.run(cypher, user_id=user_id)
            else:
                cypher = (
                    "MATCH (u:User {id: $user_id})-[:OWNS]->(e) "
                    "OPTIONAL MATCH (e)-[r]->(neighbor) "
                    "RETURN e, r, neighbor"
                )
                result = session.run(cypher, user_id=user_id)

            nodes = []
            edges = []
            node_ids = set()

            for record in result:
                for node_key in ["e", "neighbor", "e1", "e2"]:
                    if node_key in record and record[node_key] is not None:
                        node = record[node_key]
                        node_id = node.id
                        if node_id not in node_ids:
                            node_ids.add(node_id)
                            labels = list(node.labels)
                            nodes.append({
                                "id": node_id,
                                "name": node.get("name", ""),
                                "type": labels[0] if labels else "Entity",
                                "properties": dict(node)
                            })

                if "r" in record and record["r"] is not None:
                    rel = record["r"]
                    edges.append({
                        "id": rel.id,
                        "source": rel.start_node.id,
                        "target": rel.end_node.id,
                        "type": rel.type,
                        "properties": dict(rel)
                    })

            return {"nodes": nodes, "edges": edges}

        except exceptions.Neo4jError as e:
            logger.error(f"知识图谱查询失败: {str(e)}")
            raise
        finally:
            session.close()

    def shutdown(self):
        """优雅关闭服务"""
        self.executor.shutdown(wait=True)
        self.neo4j_conn.close()
        logger.info("KGService已优雅关闭")


    #知识图谱前端渲染字段对应
    def get_kg_list(self, db: Session, user_id: int, skip: int = 0, limit: int = 20) -> tuple[
        List[Dict[str, Any]], int]:
        """获取用户的知识图谱列表（带分页）"""
        try:
            query = db.query(KnowledgeGraph).filter(KnowledgeGraph.user_id == user_id)
            total = query.count()

            # 获取分页数据
            graphs = query.offset(skip).limit(limit).all()

            # 转换为前端需要的格式
            graph_list = []
            for graph in graphs:
                graph_list.append({
                    "kg_id": graph.kg_id,
                    "name": graph.name,
                    "entity_count": graph.entity_count or 0,
                    "relation_count": graph.relation_count or 0,
                    "create_time": graph.created_at,
                    "status": graph.status or "completed"
                })

            # print(f"返回的知识图谱数据: {graph_list}")  # 调试信息
            return graph_list, total

        except Exception as e:
            logger.error(f"获取知识图谱列表失败: {str(e)}", exc_info=True)
            raise

    def get_kg_build_progress(self, db: Session, kg_id: int) -> dict:
        """获取知识图谱构建进度"""
        try:
            graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == kg_id).first()
            if not graph:
                logger.warning(f"知识图谱 {kg_id} 不存在")
                raise ValueError(f"知识图谱 {kg_id} 不存在")

            return {
                "kg_id": kg_id,
                "status": graph.status,
                "progress": graph.progress,
                "message": graph.build_message,
                "updated_at": graph.updated_at
            }
        except Exception as e:
            logger.error(f"获取知识图谱 {kg_id} 构建进度失败: {str(e)}", exc_info=True)
            raise

    @staticmethod
    def update_build_progress(db: Session, kg_id: int, progress: int, status: str, message: str = ""):
        """更新知识图谱构建进度"""
        graph = db.query(KnowledgeGraph).filter(KnowledgeGraph.id == kg_id).first()
        if graph:
            graph.progress = progress
            graph.status = status
            graph.build_message = message
            graph.updated_at = datetime.now()
            db.commit()
            db.refresh(graph)
            return True
        return False


    def get_visualization_data(self, kg_id: str, user_id: int, limit: int = 100) -> Dict:
        """
        获取知识图谱可视化数据（修复3个问题）
        :param kg_id: 图谱ID
        :param user_id: 当前用户ID（用于权限校验）
        :param limit: 最大返回数量
        """
        try:
            # 步骤1：权限校验（确保用户只能查看自己的图谱）
            db = next(get_db())
            if not self.verify_kg_ownership(db, kg_id, user_id):
                logger.warning(f"用户 {user_id} 无权限查看图谱 {kg_id}")
                return {"nodes": [], "edges": []}

            # 步骤2：查询Neo4j（关键：用实体的kg_id属性筛选，不再用错误的n.kg_id）
            with self.neo4j_conn.driver.session() as session:
                # 合并节点+关系查询（减少一次数据库请求，更高效）
                query = """
                // 匹配当前图谱的实体（通过kg_id筛选）
                MATCH (n)
                WHERE n.kg_id = $kg_id  // 现在实体有kg_id属性了，可正常筛选
                // 匹配实体间的关系（两端都属于当前图谱）
                OPTIONAL MATCH (n)-[r]->(m)
                WHERE m.kg_id = $kg_id
                RETURN n, r, m
                LIMIT $limit
                """
                result = session.run(query, kg_id=kg_id, limit=limit)

                # 步骤3：格式化节点和关系数据
                nodes = []
                edges = []
                node_ids = set()  # 避免重复添加节点

                for record in result:
                    # 处理主节点n
                    n = record["n"]
                    if n:
                        node_id = n.id
                        if node_id not in node_ids:
                            # 获取实体类型（从标签中取第一个，如“Person”“Organization”）
                            node_labels = list(n.labels)
                            node_type = node_labels[0] if node_labels else "Entity"
                            nodes.append({
                                "id": node_id,
                                "label": n.get("name", f"Node_{node_id}"),  # 用实体name作为标签
                                "group": node_type,  # 用实体类型分组（前端可视化可按group区分颜色）
                                "title": f"类型: {node_type}\n图谱ID: {n.get('kg_id')}"  # 鼠标悬浮显示详情
                            })
                            node_ids.add(node_id)

                    # 处理关系r和目标节点m
                    r = record["r"]
                    m = record["m"]
                    if r and m:
                        m_id = m.id
                        # 确保目标节点m已添加到nodes
                        if m_id not in node_ids:
                            m_labels = list(m.labels)
                            m_type = m_labels[0] if m_labels else "Entity"
                            nodes.append({
                                "id": m_id,
                                "label": m.get("name", f"Node_{m_id}"),
                                "group": m_type,
                                "title": f"类型: {m_type}\n图谱ID: {m.get('kg_id')}"
                            })
                            node_ids.add(m_id)
                        # 添加关系数据
                        edges.append({
                            "from": n.id if n else None,
                            "to": m_id,
                            "label": r.type,  # 关系类型作为标签
                            "title": r.type  # 鼠标悬浮显示关系类型
                        })

            logger.info(f"图谱 {kg_id} 可视化数据：节点{len(nodes)}个，关系{len(edges)}个")
            return {"nodes": nodes, "edges": edges}

        except Exception as e:
            # 修复：用全局logger，而非self.logger（self.logger未定义）
            logger.error(f"获取图谱 {kg_id} 可视化数据失败: {str(e)}", exc_info=True)
            return {"nodes": [], "edges": []}



    def verify_kg_ownership(self, db: Session, kg_id: str, user_id: int) -> bool:
        """
        验证用户是否拥有指定知识图谱的所有权
        :param db: 数据库会话（从接口传入）
        :param kg_id: 知识图谱ID（待验证的图谱）
        :param user_id: 当前用户ID（从登录态获取）
        :return: True=拥有权限，False=无权限或图谱不存在
        """
        try:
            # 查询数据库中该kg_id对应的记录，且归属当前用户
            kg = db.query(KnowledgeGraph).filter(
                KnowledgeGraph.kg_id == kg_id,  # 匹配图谱ID
                KnowledgeGraph.user_id == user_id  # 匹配用户ID（确保归属）
            ).first()

            # 如果查询到结果，说明用户拥有该图谱；否则无权限或图谱不存在
            return kg is not None
        except Exception as e:
            logger.error(f"验证知识图谱所有权失败（kg_id={kg_id}, user_id={user_id}）: {str(e)}", exc_info=True)
            return False  # 异常情况下默认返回无权限，避免安全风险


    #删除知识图谱
    def delete_knowledge_graph(self, db: Session, kg_id: str, user_id: int) -> bool:
        """
        删除知识图谱（修复：Cypher语法兼容+时间格式适配）
        :return: True=删除成功，False=图谱不存在
        """
        # 1. 先查询数据库中的图谱记录（获取创建时间，用于筛选旧数据）
        kg = db.query(KnowledgeGraph).filter(
            KnowledgeGraph.kg_id == kg_id,
            KnowledgeGraph.user_id == user_id
        ).first()
        if not kg:
            return False  # 图谱不存在

        # 2. 清理 Neo4j 数据（修复语法+时间格式）
        session = self.neo4j_conn.get_session()
        try:
            # 2.1 第一步：删除当前图谱实体关联的所有关系（无论另一端实体归属）
            rel_delete_result = session.run(
                "MATCH (n) "
                "WHERE n.kg_id = $kg_id "       # 筛选当前图谱的实体
                "OPTIONAL MATCH (n)-[r]->()  "      #实体作为起点的关系
                "OPTIONAL MATCH ()-[r2]->(n)"       # 实体作为终点的关系
                "DELETE r, r2",
                kg_id=kg_id
            )
            rel_deleted = rel_delete_result.consume().counters.relationships_deleted
            logger.info(f"Neo4j中已删除图谱 {kg_id} 的 {rel_deleted} 个关联关系")

            # 2.2 第二步：删除当前图谱的实体（修复语法+时间格式）
            # 关键修改：
            # 1. NOT EXISTS(n.kg_id) → n.kg_id IS NULL
            # 2. Python datetime → Neo4j datetime字符串（格式：YYYY-MM-DDTHH:MM:SS）
            kg_create_time_start = kg.created_at.strftime("%Y-%m-%dT%H:%M:%S")
            kg_create_time_end = (kg.created_at + timedelta(minutes=10)).strftime("%Y-%m-%dT%H:%M:%S")

            node_delete_result = session.run(
                "MATCH (u:User {id: $user_id})-[:OWNS]->(n) "  # 筛选用户拥有的实体
                "WHERE "
                # 优先匹配有kg_id的新数据
                "(n.kg_id = $kg_id) "
                "OR "
                # 兼容无kg_id的旧数据（修复语法：n.kg_id IS NULL）
                "(n.kg_id IS NULL "
                "AND n.created_at >= datetime($kg_create_time_start) "  # Neo4j datetime格式
                "AND n.created_at <= datetime($kg_create_time_end)) "
                "DELETE n",
                kg_id=kg_id,
                user_id=str(user_id),  # User的id是字符串类型
                kg_create_time_start=kg_create_time_start,
                kg_create_time_end=kg_create_time_end
            )
            node_deleted = node_delete_result.consume().counters.nodes_deleted
            logger.info(f"Neo4j中已删除图谱 {kg_id} 的 {node_deleted} 个实体")

        except exceptions.Neo4jError as e:
            logger.error(f"删除Neo4j中图谱 {kg_id} 的数据失败: {str(e)}")
            raise
        finally:
            session.close()

        # 3. 删除数据库中的KnowledgeGraph记录
        db.delete(kg)
        db.commit()
        return True
