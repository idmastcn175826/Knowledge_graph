# 在Python中检查
from app.models.knowledge_graphs import KnowledgeGraph
from app.utils.db import get_db

db = next(get_db())
graphs = db.query(KnowledgeGraph).all()
for graph in graphs:
    print(f"ID: {graph.id}, KG_ID: {graph.kg_id}, Name: {graph.name}, Entities: {graph.entity_count}, Relations: {graph.relation_count}")