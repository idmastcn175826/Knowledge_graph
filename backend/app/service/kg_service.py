import uuid
import logging
import time
from typing import List, Dict, Tuple, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from neo4j import GraphDatabase, exceptions
from app.core.config import settings
from app.algorithm.preprocess.factory import PreprocessFactory
from app.algorithm.extraction.factory import EntityExtractionFactory, RelationExtractionFactory
from app.algorithm.fusion.entity_alignment import EntityAlignment
from app.algorithm.completion.factory import KnowledgeCompletionFactory
from app.utils.file_parser import FileParser
from app.models.schema import KGCreateRequest, KGProgressResponse

logger = logging.getLogger(__name__)

class Neo4jConnection:
    """Neo4j数据库连接管理(单例模式)"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jConnection, cls).__new__(cls)
            cls._instance.driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            # 测试连接
            try:
                cls._instance.driver.verify_connectivity()
                logger.info("Neo4j连接成功")
            except exceptions.Neo4jError as e:
                logger.error(f"Neo4j连接失败: {str(e)}")
                raise
        return cls._instance
    
    def close(self):
        """关闭连接"""
        if self.driver:
            self.driver.close()
            logger.info("Neo4j连接已关闭")
    
    def get_session(self):
        """获取会话"""
        return self.driver.session()


class KGService:
    """知识图谱服务类"""
    
    def __init__(self):
        self.neo4j_conn = Neo4jConnection()
        self.task_progress = {}  # 存储任务进度 {task_id: progress}
    
    def create_knowledge_graph(self, user_id: str, request: KGCreateRequest) -> str:
        """
        创建知识图谱
        
        Args:
            user_id: 用户ID
            request: 知识图谱创建请求参数
            
        Returns:
            任务ID
        """
        task_id = str(uuid.uuid4())
        self.task_progress[task_id] = 0
        
        # 使用线程池异步处理图谱构建
        with ThreadPoolExecutor() as executor:
            executor.submit(
                self._build_kg_async,
                task_id,
                user_id,
                request.file_ids,
                request.algorithms,
                request.model_api_key
            )
        
        logger.info(f"知识图谱构建任务已启动，task_id: {task_id}")
        return task_id
    
    def _build_kg_async(self, task_id: str, user_id: str, file_ids: List[str], 
                       algorithms: Dict, model_api_key: Optional[str]):
        """异步构建知识图谱"""
        try:
            # 1. 初始化进度
            self._update_progress(task_id, 5)
            
            # 2. 解析文件
            parser = FileParser()
            texts = []
            for i, file_id in enumerate(file_ids):
                file_path = f"{settings.UPLOAD_DIR}/{file_id}"
                text = parser.parse(file_path)
                texts.append(text)
                self._update_progress(task_id, 5 + int(10 * (i + 1) / len(file_ids)))
            
            # 3. 数据预处理
            preprocess_strategy = PreprocessFactory.get_strategy(algorithms.get("preprocess", "simhash"))
            processed_texts = []
            for i, text in enumerate(texts):
                processed_text = preprocess_strategy.process(text)
                processed_texts.append(processed_text)
                self._update_progress(task_id, 15 + int(10 * (i + 1) / len(texts)))
            
            # 4. 实体抽取
            entity_algorithm = algorithms.get("entity_extraction", "bert")
            entity_strategy = EntityExtractionFactory.get_strategy(entity_algorithm, model_api_key)
            
            all_entities = []
            for i, text in enumerate(processed_texts):
                entities = entity_strategy.extract(text)
                all_entities.extend(entities)
                self._update_progress(task_id, 25 + int(15 * (i + 1) / len(processed_texts)))
            
            # 5. 实体对齐
            alignment = EntityAlignment()
            aligned_entities = alignment.align(all_entities)
            self._update_progress(task_id, 40)
            
            # 6. 关系抽取
            relation_algorithm = algorithms.get("relation_extraction", "qwen")
            relation_strategy = RelationExtractionFactory.get_strategy(relation_algorithm, model_api_key)
            
            all_relations = []
            for i, (text, processed_text) in enumerate(zip(texts, processed_texts)):
                relations = relation_strategy.extract(processed_text, aligned_entities)
                all_relations.extend(relations)
                self._update_progress(task_id, 40 + int(15 * (i + 1) / len(processed_texts)))
            
            # 7. 知识补全
            completion_algorithm = algorithms.get("knowledge_completion", "transe")
            completion_strategy = KnowledgeCompletionFactory.get_strategy(completion_algorithm)
            completed_triples = completion_strategy.complete(aligned_entities, all_relations)
            self._update_progress(task_id, 60)
            
            # 8. 存储到Neo4j
            self._save_to_neo4j(user_id, aligned_entities, completed_triples)
            self._update_progress(task_id, 90)
            
            # 9. 完成
            self._update_progress(task_id, 100)
            logger.info(f"知识图谱构建完成，task_id: {task_id}")
            
        except Exception as e:
            logger.error(f"知识图谱构建失败，task_id: {task_id}, 错误: {str(e)}", exc_info=True)
            self.task_progress[task_id] = -1  # 标记为失败
    
    def _save_to_neo4j(self, user_id: str, entities: List[Dict], relations: List[Tuple]):
        """将实体和关系保存到Neo4j"""
        session = self.neo4j_conn.get_session()
        
        try:
            # 创建用户节点(如果不存在)
            session.run(
                "MERGE (u:User {id: $user_id})",
                user_id=user_id
            )
            
            # 创建实体节点
            for entity in entities:
                session.run(
                    f"MERGE (e:{entity['type']} {{id: $id, name: $name}}) "
                    f"MERGE (u:User {{id: $user_id}})-[:OWNS]->(e)",
                    id=entity["id"],
                    name=entity["name"],
                    user_id=user_id
                )
            
            # 创建关系
            for subj_id, rel_type, obj_id in relations:
                session.run(
                    "MATCH (s {id: $subj_id}), (o {id: $obj_id}) "
                    f"MERGE (s)-[r:{rel_type}]->(o)",
                    subj_id=subj_id,
                    obj_id=obj_id
                )
                
            logger.info(f"已保存 {len(entities)} 个实体和 {len(relations)} 个关系到Neo4j")
            
        except exceptions.Neo4jError as e:
            logger.error(f"保存到Neo4j失败: {str(e)}")
            raise
        finally:
            session.close()
    
    def _update_progress(self, task_id: str, progress: int):
        """更新任务进度"""
        if 0 <= progress <= 100:
            self.task_progress[task_id] = progress
            logger.info(f"任务 {task_id} 进度: {progress}%")
        # 防止内存泄漏，定期清理已完成的任务
        if progress == 100:
            time.sleep(3600)  # 1小时后清理
            if task_id in self.task_progress:
                del self.task_progress[task_id]
    
    def get_progress(self, task_id: str) -> KGProgressResponse:
        """获取任务进度"""
        progress = self.task_progress.get(task_id, -1)
        
        if progress == -1:
            return KGProgressResponse(
                task_id=task_id,
                progress=0,
                status="failed",
                message="任务执行失败"
            )
        elif progress == 100:
            return KGProgressResponse(
                task_id=task_id,
                progress=100,
                status="completed",
                message="任务已完成"
            )
        elif progress > 0:
            return KGProgressResponse(
                task_id=task_id,
                progress=progress,
                status="processing",
                message="任务处理中"
            )
        else:
            return KGProgressResponse(
                task_id=task_id,
                progress=0,
                status="not_found",
                message="任务不存在"
            )
    
    def query_kg(self, user_id: str, query: Dict) -> List[Dict]:
        """查询知识图谱"""
        session = self.neo4j_conn.get_session()
        try:
            # 构建Cypher查询
            if "entity" in query:
                # 查询实体相关的关系
                entity_name = query["entity"]
                cypher = (
                    "MATCH (u:User {id: $user_id})-[:OWNS]->(e) "
                    "WHERE e.name CONTAINS $entity_name "
                    "OPTIONAL MATCH (e)-[r]->(neighbor) "
                    "RETURN e, r, neighbor"
                )
                result = session.run(cypher, user_id=user_id, entity_name=entity_name)
            elif "relation" in query:
                # 查询特定关系
                relation_type = query["relation"]
                cypher = (
                    "MATCH (u:User {id: $user_id})-[:OWNS]->(e1) "
                    f"MATCH (e1)-[r:{relation_type}]->(e2) "
                    "RETURN e1, r, e2"
                )
                result = session.run(cypher, user_id=user_id)
            else:
                # 查询所有实体和关系
                cypher = (
                    "MATCH (u:User {id: $user_id})-[:OWNS]->(e) "
                    "OPTIONAL MATCH (e)-[r]->(neighbor) "
                    "RETURN e, r, neighbor"
                )
                result = session.run(cypher, user_id=user_id)
            
            # 处理查询结果
            nodes = []
            edges = []
            node_ids = set()
            
            for record in result:
                # 处理实体节点
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
                
                # 处理关系
                if "r" in record and record["r"] is not None:
                    rel = record["r"]
                    edges.append({
                        "id": rel.id,
                        "source": rel.start_node.id,
                        "target": rel.end_node.id,
                        "type": rel.type,
                        "properties": dict(rel)
                    })
            
            return {
                "nodes": nodes,
                "edges": edges
            }
            
        except exceptions.Neo4jError as e:
            logger.error(f"知识图谱查询失败: {str(e)}")
            raise
        finally:
            session.close()
