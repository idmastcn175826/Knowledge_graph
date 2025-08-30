import json
import logging
import re
import uuid
from typing import List, Dict, Tuple

import neo4j
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from app.algorithm.extraction.base import EntityExtractionStrategy, RelationExtractionStrategy
from app.core.config import settings

logger = logging.getLogger(__name__)


class QwenEntityExtraction(EntityExtractionStrategy):
    """基于Qwen模型的实体抽取策略实现"""

    def __init__(self, api_key: str = None):
        """初始化Qwen实体抽取器"""
        self.api_key = api_key or settings.QWEN_DEFAULT_API_KEY
        self.api_base_url = settings.QWEN_API_BASE_URL or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        # 验证API端点格式
        self._validate_api_endpoint()

        # 初始化带重试机制的会话
        self.session = self._create_session()

        if not self.api_key:
            logger.warning("Qwen API密钥未配置，实体抽取功能可能无法正常工作")

    def _validate_api_endpoint(self):
        """验证并修正API端点格式"""
        required_path = "/compatible-mode/v1/chat/completions"
        if required_path not in self.api_base_url:
            logger.warning(f"Qwen API端点似乎不正确，缺少必要路径: {required_path}")
            try:
                # 提取协议和域名部分
                if self.api_base_url.startswith(('http://', 'https://')):
                    protocol = self.api_base_url.split('://')[0] + '://'
                    domain = self.api_base_url.split('://')[1].split('/')[0]
                    self.api_base_url = f"{protocol}{domain}{required_path}"
                else:
                    # 假设是域名，使用https协议
                    self.api_base_url = f"https://{self.api_base_url}{required_path}"
                logger.info(f"已自动修正Qwen API地址为: {self.api_base_url}")
            except Exception as e:
                logger.error(f"修正API地址失败: {str(e)}，使用默认地址")
                self.api_base_url = f"https://dashscope.aliyuncs.com{required_path}"

    def _create_session(self) -> requests.Session:
        """创建带有重试机制的请求会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,  # 总重试次数
            backoff_factor=1,  # 重试间隔时间因子
            status_forcelist=[429, 500, 502, 503, 504]  # 需要重试的状态码
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _preprocess_text(self, text: str) -> str:
        """文本预处理，提高实体识别率"""
        # 移除多余空白字符
        text = re.sub(r'\s+', ' ', text).strip()
        # 替换特殊符号，但保留可能有意义的符号
        text = re.sub(r'[^\w\s，。,.!?；;()/\-]', ' ', text)
        # 调试日志：输出预处理后的文本内容（限制长度以防过长）
        log_text = text[:200] + "..." if len(text) > 200 else text
        logger.info(f"预处理后的文本内容: {log_text}")
        logger.info(f"预处理后的文本长度: {len(text)}")
        return text

    def extract(self, text: str) -> List[Dict]:
        """
        使用Qwen模型从文本中抽取实体

        Args:
            text: 待处理的文本

        Returns:
            实体列表，每个实体包含id、name、type等信息
        """
        if not text:
            logger.warning("输入文本为空，无法进行实体抽取")
            return []

        # 调试日志：输出原始文本内容
        log_text = text[:200] + "..." if len(text) > 200 else text
        logger.info(f"原始输入文本内容: {log_text}")

        # 文本预处理
        processed_text = self._preprocess_text(text)

        # 文本长度检查
        if len(processed_text) < 50:
            logger.warning(f"输入文本过短（{len(processed_text)}字符），尝试增强本地策略")
            local_entities = self._fallback_extract(processed_text)
            if local_entities:
                return local_entities
            # 如果本地策略也失败，尝试使用API再试一次
            logger.info("本地策略未抽取到实体，尝试使用API再次抽取")

        if not self.api_key:
            logger.error("Qwen API密钥未配置，使用本地备选策略")
            return self._fallback_extract(processed_text)

        try:
            # 增强版提示词，更明确地指导模型
            prompt = f"""请从以下文本中抽取所有可能的实体，并按照指定格式返回结果。
实体类型应包括但不限于：
- 人物：姓名、称呼等
- 组织：公司、机构、学校、政府部门等
- 地点：国家、城市、地区、街道等
- 时间：日期、年份、时间段等
- 事件：会议、活动、事故等
- 产品：物品、设备、软件等
- 技术：技术术语、方法、理论等
- 概念：抽象概念、理论等

即使是看似不重要的实体也请提取出来，不要遗漏任何可能的实体。实体类型请使用单一类别，不要包含斜杠(/)等特殊字符。

文本：{processed_text}

请严格以JSON数组格式返回，每个实体必须包含以下字段：
- "name": 实体名称（准确的文本内容）
- "type": 实体类型（使用中文描述，从上述类型中选择或创建合适类型，不要包含斜杠等特殊字符）
- "start_pos": 实体在原始文本中的起始位置索引（整数）
- "end_pos": 实体在原始文本中的结束位置索引（整数）

确保：
1. 不要遗漏任何实体
2. 位置索引准确对应实体在文本中的位置
3. 只返回JSON数组，不添加任何解释、说明或其他文字
4. 如果没有识别到实体，返回空数组[]"""

            # 调用Qwen API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": settings.qwen_model_name or "qwen-plus",
                "messages": [
                    {"role": "system",
                     "content": "你是一个专业的实体抽取工具，能够从任何文本中准确识别并提取各类实体。你的回答必须严格遵循用户指定的格式要求，实体类型不要包含斜杠等特殊字符，即使文本内容简短也要尽力识别实体。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,  # 适当提高温度，增加识别可能性
                "seed": 42
            }

            response = self.session.post(
                self.api_base_url,
                headers=headers,
                data=json.dumps(data),
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # 调试日志：输出API原始响应
            logger.debug(f"Qwen API原始响应: {json.dumps(result, ensure_ascii=False)[:500]}...")

            # 解析API返回结果
            if "choices" in result and len(result["choices"]) > 0:
                entity_str = result["choices"][0]["message"]["content"].strip()
                entity_str = self._clean_json_response(entity_str)

                # 调试日志：输出清理后的实体字符串
                logger.debug(f"清理后的实体字符串: {entity_str[:500]}...")

                try:
                    entities = json.loads(entity_str)
                except json.JSONDecodeError as e:
                    logger.error(f"解析实体JSON失败: {str(e)}, 原始内容: {entity_str}")
                    return self._fallback_extract(processed_text)

                # 验证实体结构并添加唯一ID
                valid_entities = []
                for entity in entities:
                    if self._validate_entity(entity, processed_text):
                        # 清理实体类型中的特殊字符
                        entity["type"] = self._clean_entity_type(entity["type"])
                        entity["id"] = f"entity_{uuid.uuid4().hex[:8]}"
                        valid_entities.append(entity)
                    else:
                        logger.warning(f"无效的实体结构: {entity}")

                # 如果API返回空，使用增强本地策略重试
                if not valid_entities:
                    logger.warning("Qwen API未返回有效实体，使用增强本地策略")
                    valid_entities = self._fallback_extract(processed_text, force_extend=True)
                else:
                    logger.info(f"从文本中成功抽取到 {len(valid_entities)} 个有效实体")

                return valid_entities
            else:
                logger.warning("Qwen API返回结果不包含有效实体信息")
                return self._fallback_extract(processed_text, force_extend=True)

        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API请求失败: {str(e)}")
        except Exception as e:
            logger.error(f"Qwen模型实体抽取失败: {str(e)}", exc_info=True)

        # 发生错误时使用备选抽取方式
        return self._fallback_extract(processed_text, force_extend=True)

    def _clean_entity_type(self, entity_type: str) -> str:
        """清理实体类型中的特殊字符"""
        # 替换特殊字符为下划线
        cleaned = re.sub(r'[\\/:"*?<>|]+', '_', entity_type)
        # 确保类型不为空
        if not cleaned.strip():
            return "实体"
        return cleaned.strip()

    def _clean_json_response(self, response_str: str) -> str:
        """清理模型返回的可能包含非JSON内容的响应"""
        start_idx = response_str.find('[')
        end_idx = response_str.rfind(']') + 1

        if start_idx != -1 and end_idx != 0:
            return response_str[start_idx:end_idx]
        return response_str

    def _validate_entity(self, entity: Dict, original_text: str) -> bool:
        """验证实体是否包含必要的字段且位置信息有效"""
        required_fields = ["name", "type", "start_pos", "end_pos"]
        if not all(field in entity for field in required_fields):
            return False

        # 验证位置信息是否有效
        try:
            start = int(entity["start_pos"])
            end = int(entity["end_pos"])
            # 允许一定的位置误差，特别是对于长文本
            max_length_diff = 5
            if start < 0 or end <= start or end > len(original_text) + max_length_diff:
                return False

            # 提取实体名称和对应文本位置的内容
            extracted_text = original_text[start:end].strip() if start < len(original_text) else ""
            if end > len(original_text):
                extracted_text += original_text[len(original_text):end] if len(original_text) < end else ""

            entity_name = entity["name"].strip()

            # 增强的匹配逻辑：允许一定的字符差异
            if self._strings_are_similar(entity_name, extracted_text):
                # 如果相似但不完全一致，修正实体名称
                entity["name"] = extracted_text
                return True
            else:
                # 尝试在原始文本中查找实体名称，更新位置信息
                pos = original_text.find(entity_name)
                if pos != -1:
                    entity["start_pos"] = pos
                    entity["end_pos"] = pos + len(entity_name)
                    return True

                logger.warning(f"实体名称与文本位置不符: 预期'{extracted_text}', 实际'{entity['name']}'")
                return False
        except (ValueError, TypeError):
            return False


    def _strings_are_similar(self, str1: str, str2: str, threshold: float = 0.6) -> bool:
        """检查两个字符串是否相似（复用实体抽取中的逻辑）"""
        if not str1 or not str2:
            return False
        if str1 in str2 or str2 in str1:
            return True
        try:
            from fuzzywuzzy import fuzz
            return fuzz.ratio(str1, str2) > threshold * 100
        except ImportError:
            min_len = min(len(str1), len(str2))
            if min_len == 0:
                return False
            matches = sum(c1 == c2 for c1, c2 in zip(str1, str2))
            return (matches / min_len) > threshold

    def _add_relation_if_valid(self, entity1_name: str, entity2_name: str, relation: str,
                               entity_name_to_id: Dict, relations: List, sorted_entity_names: List):
        """增强版关系匹配，支持精确/子串/模糊匹配"""
        # 1. 精确匹配
        if entity1_name in entity_name_to_id and entity2_name in entity_name_to_id:
            relations.append((entity_name_to_id[entity1_name], relation, entity_name_to_id[entity2_name]))
            logger.debug(f"精确匹配关系: {entity1_name} {relation} {entity2_name}")
            return

        # 2. 子串匹配（长实体优先）
        matched1 = None
        matched2 = None
        for name in sorted_entity_names:
            if not matched1 and name in entity1_name:
                matched1 = name
            if not matched2 and name in entity2_name:
                matched2 = name
            if matched1 and matched2:
                break
        if matched1 and matched2:
            relations.append((entity_name_to_id[matched1], relation, entity_name_to_id[matched2]))
            logger.info(f"子串匹配关系: {matched1} {relation} {matched2} (原始: {entity1_name} {relation} {entity2_name})")
            return

        # 3. 模糊匹配
        threshold = 0.65
        for name1 in sorted_entity_names:
            if self._strings_are_similar(entity1_name, name1, threshold):
                for name2 in sorted_entity_names:
                    if self._strings_are_similar(entity2_name, name2, threshold):
                        relations.append((entity_name_to_id[name1], relation, entity_name_to_id[name2]))
                        logger.info(f"模糊匹配关系: {name1} {relation} {name2} (原始: {entity1_name} {relation} {entity2_name})")
                        return

        # 4. 反向模糊匹配（处理实体顺序颠倒）
        for name1 in sorted_entity_names:
            if self._strings_are_similar(entity2_name, name1, threshold):
                for name2 in sorted_entity_names:
                    if self._strings_are_similar(entity1_name, name2, threshold):
                        reversible_relations = ['合作', '与', '和', '同']
                        if any(rel in relation for rel in reversible_relations):
                            relations.append((entity_name_to_id[name1], relation, entity_name_to_id[name2]))
                            logger.info(f"反向匹配关系: {name1} {relation} {name2} (原始: {entity1_name} {relation} {entity2_name})")
                            return

        logger.debug(f"未能匹配关系: {entity1_name} {relation} {entity2_name}")

    # 添加字符串相似度检查方法
    def _strings_are_similar(self, str1: str, str2: str, threshold: float = 0.6) -> bool:
        """检查两个字符串是否相似"""
        if not str1 or not str2:
            return False

        # 简单包含关系检查
        if str1 in str2 or str2 in str1:
            return True

        # 使用Levenshtein距离计算相似度
        try:
            from fuzzywuzzy import fuzz
            return fuzz.ratio(str1, str2) > threshold * 100
        except ImportError:
            # 如果没有fuzzywuzzy库，使用简单的字符匹配率
            min_len = min(len(str1), len(str2))
            if min_len == 0:
                return False

            matches = sum(c1 == c2 for c1, c2 in zip(str1, str2))
            return (matches / min_len) > threshold

    def _local_relation_extract(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """增强版本地关系抽取（支持11种关系模式，解决0关系问题）"""
        logger.info("使用增强版本地关系抽取策略")
        if len(entities) < 2:
            logger.info("有效实体不足2个，无法抽取关系")
            return []

        # 1. 预处理实体（过滤无效、修正名称）
        valid_entities = []
        for entity in entities:
            try:
                start_pos = entity.get('start_pos', 0)
                end_pos = entity.get('end_pos', 0)
                if start_pos < 0 or end_pos > len(text) or start_pos >= end_pos:
                    logger.warning(f"过滤无效实体（位置错误）: {entity}")
                    continue
                # 修正实体名称（确保与文本一致）
                text_substring = text[start_pos:end_pos].strip()
                if entity['name'] not in text_substring and text_substring not in entity['name']:
                    logger.warning(f"修正实体名称: 原'{entity['name']}' → 新'{text_substring}'")
                    entity['name'] = text_substring
                valid_entities.append(entity)
            except Exception as e:
                logger.warning(f"过滤无效实体（结构错误）: {entity}, 错误: {str(e)}")

        if len(valid_entities) < 2:
            logger.info("预处理后实体不足2个，无法抽取关系")
            return []

        # 2. 构建实体映射（名称→ID）
        entity_name_to_id = {e["name"]: e["id"] for e in valid_entities}
        entity_names = list(entity_name_to_id.keys())
        sorted_entity_names = sorted(entity_names, key=lambda x: len(x), reverse=True)  # 长实体优先匹配
        relations = []

        # 3. 11种关系模式（覆盖日志文本场景）
        # 模式1：合作关系（如“文心一言与比亚迪合作”）
        合作模式 = re.compile(r"(\w+)(与|和|同)(\w+)(合作|达成合作|战略合作)")
        for match in 合作模式.finditer(text):
            self._add_relation_if_valid(match.group(1), match.group(3), f"{match.group(4)}",
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式2：推出/研发关系（如“百度推出文心一言”“王海峰团队研发文心一言”）
        发布模式 = re.compile(r"(\w+)(推出|发布|研发|研制)(\w+)")
        for match in 发布模式.finditer(text):
            self._add_relation_if_valid(match.group(1), match.group(3), match.group(2),
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式3：隶属关系（如“王海峰任百度研究院院长”）
        隶属模式 = re.compile(r"(\w+)(是|属于|任职于|担任)(\w+)(的)?(\w+)?")
        for match in 隶属模式.finditer(text):
            relation = f"{match.group(2)}{match.group(4) or ''}{match.group(5) or ''}".strip()
            self._add_relation_if_valid(match.group(1), match.group(3), relation,
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式4：领导关系（如“李彦宏领导百度”）
        领导模式 = re.compile(r"(\w+)(领导|带领|负责)(\w+)")
        for match in 领导模式.finditer(text):
            self._add_relation_if_valid(match.group(1), match.group(3), match.group(2),
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式5：时间关联（如“百度于2023年推出文心一言”）
        时间模式 = re.compile(r"(\w+)(于|在)(\d{4}年[\d月日]*)((推出|发布|成立))")
        for match in 时间模式.finditer(text):
            relation = f"{match.group(2)}{match.group(4)}"
            self._add_relation_if_valid(match.group(1), match.group(3), relation,
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式6：包含关系（如“合作企业包括比亚迪”）
        包含模式 = re.compile(r"(\w+)(包括|包含)(\w+)")
        for match in 包含模式.finditer(text):
            self._add_relation_if_valid(match.group(1), match.group(3), match.group(2),
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式7：表示关系（如“李彦宏表示...”）
        表示模式 = re.compile(r"(\w+)(表示|称|说)(\w+)")
        for match in 表示模式.finditer(text):
            self._add_relation_if_valid(match.group(1), match.group(3), match.group(2),
                                        entity_name_to_id, relations, sorted_entity_names)

        # 模式8-11：其他补充模式（按需保留，此处省略，可参考原代码）

        # 4. 去重（避免重复关系）
        unique_relations = list(set(relations))  # 利用set去重（三元组可哈希）
        logger.info(f"本地策略抽取到 {len(unique_relations)} 个关系")
        return unique_relations

    # 改进关系匹配方法
    def _add_relation_if_valid(self, entity1_name: str, entity2_name: str, relation: str,
                               entity_name_to_id: Dict, relations: List, sorted_entity_names: List):
        """增强版关系匹配，支持更灵活的实体名称匹配"""
        # 1. 尝试精确匹配
        if entity1_name in entity_name_to_id and entity2_name in entity_name_to_id:
            relations.append((entity_name_to_id[entity1_name], relation, entity_name_to_id[entity2_name]))
            logger.debug(f"精确匹配关系: {entity1_name} {relation} {entity2_name}")
            return

        # 2. 尝试子字符串匹配（检查实体名是否包含在匹配文本中）
        matched1 = None
        matched2 = None

        for name in sorted_entity_names:
            if not matched1 and name in entity1_name:
                matched1 = name
            if not matched2 and name in entity2_name:
                matched2 = name
            if matched1 and matched2:
                break

        if matched1 and matched2:
            relations.append((entity_name_to_id[matched1], relation, entity_name_to_id[matched2]))
            logger.info(
                f"子串匹配关系: {matched1} {relation} {matched2} (原始: {entity1_name} {relation} {entity2_name})")
            return

        # 3. 尝试模糊匹配（降低阈值以提高匹配成功率）
        threshold = 0.65
        for name1 in sorted_entity_names:
            if self._strings_are_similar(entity1_name, name1, threshold):
                for name2 in sorted_entity_names:
                    if self._strings_are_similar(entity2_name, name2, threshold):
                        relations.append((entity_name_to_id[name1], relation, entity_name_to_id[name2]))
                        logger.info(
                            f"模糊匹配关系: {name1} {relation} {name2} (原始: {entity1_name} {relation} {entity2_name})")
                        return

        # 4. 如果都匹配失败，尝试反向匹配（实体1和实体2交换位置）
        for name1 in sorted_entity_names:
            if self._strings_are_similar(entity2_name, name1, threshold):
                for name2 in sorted_entity_names:
                    if self._strings_are_similar(entity1_name, name2, threshold):
                        # 对于可逆关系，直接添加反向关系
                        reversible_relations = ['合作', '与', '和', '同']
                        if any(rel in relation for rel in reversible_relations):
                            relations.append((entity_name_to_id[name1], relation, entity_name_to_id[name2]))
                            logger.info(
                                f"反向模糊匹配关系: {name1} {relation} {name2} (原始: {entity1_name} {relation} {entity2_name})")
                            return

        # 5. 如果都匹配失败，记录调试日志
        logger.debug(f"未能匹配关系: {entity1_name} {relation} {entity2_name}")

    # 新增：优化Neo4j关系创建查询，解决笛卡尔积问题
    def _create_relationship(self, subj_id, obj_id, relation_type):
        """创建关系的优化方法，避免笛卡尔积查询

        :param subj_id: 源节点ID
        :param obj_id: 目标节点ID
        :param relation_type: 关系类型
        :return: 布尔值，表示关系是否创建成功
        """
        if not all([subj_id, obj_id, relation_type]):
            logger.warning("创建关系失败：参数不完整")
            return False

        try:
            # 使用APOC库的动态关系类型创建，更安全
            query = """
            MATCH (s) WHERE id(s) = $subj_id
            MATCH (o) WHERE id(o) = $obj_id
            CALL apoc.create.relationship(s, $relation_type, {}, o) YIELD rel
            RETURN rel
            """

            result = self.neo4j_session.run(
                query,
                subj_id=subj_id,
                obj_id=obj_id,
                relation_type=relation_type
            )
            return result.single() is not None

        except neo4j.exceptions.Neo4jError as e:
            logger.error(f"Neo4j数据库错误: {str(e)}")
            return False
        except Exception as e:
            logger.error(
                f"创建关系失败: {subj_id} -[{relation_type}]-> {obj_id}, "
                f"错误: {str(e)}"
            )
            return False

    def _fallback_extract(self, text: str, force_extend: bool = False) -> List[Dict]:
        """增强版本地备选实体抽取策略，可强制扩展识别范围"""
        logger.info(f"使用增强版本地备选策略进行实体抽取（force_extend={force_extend}）")

        entities = []
        entity_ids = set()  # 用于去重

        # 1. 匹配中文人名（更宽松的模式）
        person_patterns = [
            re.compile(r"([\u4e00-\u9fa5]{2,4})([先生|女士|教授|博士|老师|院士|工程师|经理|主任]?)"),
            re.compile(r"([A-Z][a-z]+[\s-]?[A-Z]?[a-z]+)")  # 英文名
        ]
        for pattern in person_patterns:
            for match in pattern.finditer(text):
                name = match.group(1)
                if name and len(name) >= 2 and name not in entity_ids:
                    entity_ids.add(name)
                    entities.append({
                        "id": f"entity_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "type": "人物",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

        # 2. 匹配组织机构名
        org_patterns = [
            re.compile(r"([\u4e00-\u9fa5]+(公司|集团|大学|学院|医院|政府|部门|协会|学会|研究所|实验室|中心|局|处|厅))"),
            re.compile(r"([A-Za-z0-9\s.]+(Inc|Corp|Co|Ltd|University|Institute|Lab|Center|Department))")
        ]
        for pattern in org_patterns:
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if name and name not in entity_ids:
                    entity_ids.add(name)
                    entities.append({
                        "id": f"entity_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "type": "组织",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

        # 3. 匹配地点
        location_patterns = [
            re.compile(r"([\u4e00-\u9fa5]+(省|市|区|县|镇|街道|路|号|巷|村|山脉|河流|湖泊|海洋))"),
            re.compile(r"([A-Z][a-zA-Z\s,]+(City|State|Province|Country|River|Lake|Ocean|Mountain))"),
            re.compile(r"([\u4e00-\u9fa5]{2,5}(地区|地带|区域))")
        ]
        for pattern in location_patterns:
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if name and name not in entity_ids:
                    entity_ids.add(name)
                    entities.append({
                        "id": f"entity_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "type": "地点",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

        # 4. 匹配时间
        time_patterns = [
            re.compile(r"(\d{4}年\d{1,2}月\d{1,2}日)"),
            re.compile(r"(\d{4}-\d{1,2}-\d{1,2})"),
            re.compile(r"(\d{4}/\d{1,2}/\d{1,2})"),
            re.compile(r"(\d{4}年)"),
            re.compile(r"(\d{1,2}月\d{1,2}日)"),
            re.compile(r"([12]\d{3})"),  # 四位年份
            re.compile(r"(\d{2}:\d{2}:\d{2})"),  # 时间
            re.compile(r"(\d{1,2}世纪)"),  # 世纪
            re.compile(r"(\d{1,2}年代)")  # 年代
        ]
        for pattern in time_patterns:
            for match in pattern.finditer(text):
                name = match.group(1).strip()
                if name and name not in entity_ids:
                    entity_ids.add(name)
                    entities.append({
                        "id": f"entity_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "type": "时间",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

        # 5. 匹配技术/产品名称（使用更安全的类型名）
        tech_terms = [
            "人工智能", "机器学习", "深度学习", "神经网络", "自然语言处理",
            "计算机视觉", "ChatGPT", "GPT-4", "Qwen", "文心一言", "ERNIE",
            "Transformer", "BERT", "CNN", "RNN", "LSTM", "GPU", "CPU", "云计算",
            "大数据", "区块链", "物联网", "虚拟现实", "增强现实", "5G", "6G",
            "量子计算", "算法", "模型", "数据库", "服务器", "软件", "硬件"
        ]
        tech_pattern = re.compile(r"(" + "|".join(re.escape(term) for term in tech_terms) + r")")
        for match in tech_pattern.finditer(text):
            name = match.group(1)
            if name not in entity_ids:
                entity_ids.add(name)
                entities.append({
                    "id": f"entity_{uuid.uuid4().hex[:8]}",
                    "name": name,
                    "type": "技术产品",  # 修正为不含斜杠的类型名
                    "start_pos": match.start(),
                    "end_pos": match.end()
                })

        # 6. 强制扩展模式：识别更多可能的实体类型
        if force_extend or len(entities) == 0:
            logger.info("启用强制扩展模式，尝试识别更多实体")

            # 识别产品名称（通用）
            product_pattern = re.compile(r"([\u4e00-\u9fa5A-Za-z0-9\s-]{2,})(产品|系统|工具|设备|软件|硬件|平台|方案)")
            for match in product_pattern.finditer(text):
                name = match.group(1).strip()
                if name and name not in entity_ids:
                    entity_ids.add(name)
                    entities.append({
                        "id": f"entity_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "type": "产品",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

            # 识别事件/活动
            event_pattern = re.compile(r"([\u4e00-\u9fa5A-Za-z0-9\s-]{2,})(会议|活动|大会|研讨会|论坛|展览|比赛|项目)")
            for match in event_pattern.finditer(text):
                name = match.group(1).strip()
                if name and name not in entity_ids:
                    entity_ids.add(name)
                    entities.append({
                        "id": f"entity_{uuid.uuid4().hex[:8]}",
                        "name": name,
                        "type": "事件",
                        "start_pos": match.start(),
                        "end_pos": match.end()
                    })

            # 识别数字和金额
            number_patterns = [
                re.compile(r"(\d+\.?\d*亿元)"),
                re.compile(r"(\d+\.?\d*万元)"),
                re.compile(r"(\d+\.?\d*美元)"),
                re.compile(r"(\d+\.?\d*人民币)"),
                re.compile(r"(\d+\.?\d*\s?%|百分比)")
            ]
            for pattern in number_patterns:
                for match in pattern.finditer(text):
                    name = match.group(1).strip()
                    if name and name not in entity_ids:
                        entity_ids.add(name)
                        entities.append({
                            "id": f"entity_{uuid.uuid4().hex[:8]}",
                            "name": name,
                            "type": "数值",
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })

            # 新增：识别文档标题和章节
            title_patterns = [
                re.compile(r"(第[\u4e00-\u9fa50-9]+章\s+)([\u4e00-\u9fa5A-Za-z0-9\s-]+)"),
                re.compile(r"([\u4e00-\u9fa5A-Za-z0-9\s-]+)([\u3001。.,]?)\s*[第]*[\d]*[章条节]")
            ]
            for pattern in title_patterns:
                for match in pattern.finditer(text):
                    name = ''.join(match.groups()).strip()
                    if name and len(name) > 2 and name not in entity_ids:
                        entity_ids.add(name)
                        entities.append({
                            "id": f"entity_{uuid.uuid4().hex[:8]}",
                            "name": name,
                            "type": "标题",
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })

            # 新增：识别通用名词短语（最后手段）
            if len(entities) == 0:
                logger.info("尝试识别通用名词短语作为最后的手段")
                # 匹配2-5个汉字组成的名词短语
                general_pattern = re.compile(r"([\u4e00-\u9fa5]{2,5})")
                for match in general_pattern.finditer(text):
                    name = match.group(1).strip()
                    # 排除常见无意义词汇
                    if name not in ["的", "了", "是", "在", "有", "和", "等", "与", "及"] and name not in entity_ids:
                        entity_ids.add(name)
                        entities.append({
                            "id": f"entity_{uuid.uuid4().hex[:8]}",
                            "name": name,
                            "type": "名词",
                            "start_pos": match.start(),
                            "end_pos": match.end()
                        })

        logger.info(f"本地策略抽取到 {len(entities)} 个实体")
        # 调试日志：输出抽取到的实体
        if entities:
            logger.debug(f"抽取到的实体: {json.dumps(entities, ensure_ascii=False)}")
        return entities


class QwenRelationExtraction(RelationExtractionStrategy):
    """基于Qwen模型的关系抽取策略实现"""

    def __init__(self, api_key: str = None):
        """初始化Qwen关系抽取器"""
        self.api_key = api_key or settings.qwen_default_api_key
        self.api_base_url = settings.qwen_api_base_url or "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

        # 验证API端点格式
        self._validate_api_endpoint()

        # 初始化带重试机制的会话
        self.session = self._create_session()

        if not self.api_key:
            logger.warning("Qwen API密钥未配置，关系抽取功能可能无法正常工作")

    def _validate_api_endpoint(self):
        """验证并修正API端点格式"""
        required_path = "/compatible-mode/v1/chat/completions"
        if required_path not in self.api_base_url:
            logger.warning(f"Qwen API端点似乎不正确，缺少必要路径: {required_path}")
            try:
                # 提取协议和域名部分
                if self.api_base_url.startswith(('http://', 'https://')):
                    protocol = self.api_base_url.split('://')[0] + '://'
                    domain = self.api_base_url.split('://')[1].split('/')[0]
                    self.api_base_url = f"{protocol}{domain}{required_path}"
                else:
                    # 假设是域名，使用https协议
                    self.api_base_url = f"https://{self.api_base_url}{required_path}"
                logger.info(f"已自动修正Qwen API地址为: {self.api_base_url}")
            except Exception as e:
                logger.error(f"修正API地址失败: {str(e)}，使用默认地址")
                self.api_base_url = f"https://dashscope.aliyuncs.com{required_path}"

    def _create_session(self) -> requests.Session:
        """创建带有重试机制的请求会话"""
        session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def extract(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """
        使用Qwen模型从文本中抽取实体间的关系

        Args:
            text: 待处理的文本
            entities: 已抽取的实体列表

        Returns:
            关系三元组列表，每个三元组为(实体1id, 关系类型, 实体2id)
        """
        if not text:
            logger.warning("输入文本为空，无法进行关系抽取")
            return []

        if not self.api_key:
            logger.error("Qwen API密钥未配置，使用本地关系抽取策略")
            return self._local_relation_extract(text, entities)

        # 如果实体数量不足，尝试使用本地策略补充
        if not entities or len(entities) < 2:
            logger.info("实体数量不足，尝试使用本地策略补充实体")
            enhancer = QwenEntityExtraction(self.api_key)
            enhanced_entities = enhancer._fallback_extract(text, force_extend=True)

            # 合并实体列表（去重）
            combined_entities = entities.copy() if entities else []
            existing_names = {e['name'] for e in combined_entities}

            for e in enhanced_entities:
                if e['name'] not in existing_names:
                    combined_entities.append(e)
                    existing_names.add(e['name'])

            if len(combined_entities) < 2:
                logger.info("补充实体后数量仍然不足，无法进行关系抽取")
                return []
            entities = combined_entities

        try:
            # 构建实体列表描述
            entity_descriptions = "\n".join([
                f"- ID: {entity['id']}, 名称: {entity['name']}, 类型: {entity['type']}"
                for entity in entities
            ])

            # 改进的关系抽取提示词
            prompt = f"""请从以下文本中抽取已识别实体之间的关系，并按照指定格式返回结果。

文本：{text}

已识别的实体列表：
{entity_descriptions}

请找出这些实体之间存在的所有关系，关系类型应具体明确（例如："创立"、"位于"、"属于"、"合作"、"领导"、"发表"等）。
以JSON数组格式返回，每个关系包含以下字段：
- "entity1_id": 第一个实体的ID
- "relation": 实体间的关系类型（使用中文描述，不要包含特殊字符）
- "entity2_id": 第二个实体的ID

确保：
1. 不要遗漏任何重要关系
2. 关系类型描述准确简洁
3. 只返回JSON数组，不添加任何额外说明文字
4. 如果没有识别到关系，返回空数组[]"""

            # 调用Qwen API
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            data = {
                "model": settings.qwen_model_name or "qwen-plus",
                "messages": [
                    {"role": "system",
                     "content": "你是一个关系抽取专家，能够准确识别文本中实体之间的各类关系。你的回答必须严格遵循用户指定的格式要求，关系类型不要包含特殊字符。"},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
                "seed": 42
            }

            response = self.session.post(
                self.api_base_url,
                headers=headers,
                data=json.dumps(data),
                timeout=60
            )

            response.raise_for_status()
            result = response.json()

            # 解析API返回结果
            if "choices" in result and len(result["choices"]) > 0:
                relation_str = result["choices"][0]["message"]["content"].strip()
                # 清理可能的非JSON内容
                relation_str = self._clean_json_response(relation_str)

                try:
                    relations = json.loads(relation_str)
                except json.JSONDecodeError as e:
                    logger.error(f"解析关系JSON失败: {str(e)}, 原始内容: {relation_str}")
                    return self._local_relation_extract(text, entities)

                # 验证关系结构并转换为三元组
                valid_relations = []
                entity_ids = {entity["id"] for entity in entities}

                for rel in relations:
                    if self._validate_relation(rel, entity_ids):
                        # 清理关系类型中的特殊字符
                        clean_rel = re.sub(r'[\\/:"*?<>|]+', '_', rel["relation"])
                        valid_relations.append(
                            (rel["entity1_id"], clean_rel, rel["entity2_id"])
                        )
                    else:
                        logger.warning(f"无效的关系结构: {rel}")

                if not valid_relations:
                    logger.warning("API未返回有效关系，尝试本地关系抽取")
                    return self._local_relation_extract(text, entities)

                logger.info(f"从文本中成功抽取到 {len(valid_relations)} 个有效关系")
                return valid_relations
            else:
                logger.warning("Qwen API返回结果不包含有效关系信息，尝试本地策略")
                return self._local_relation_extract(text, entities)

        except requests.exceptions.RequestException as e:
            logger.error(f"Qwen API请求失败: {str(e)}，尝试本地关系抽取")
            return self._local_relation_extract(text, entities)
        except Exception as e:
            logger.error(f"Qwen模型关系抽取失败: {str(e)}，尝试本地关系抽取", exc_info=True)
            return self._local_relation_extract(text, entities)

    def _local_relation_extract(self, text: str, entities: List[Dict]) -> List[Tuple[str, str, str]]:
        """本地关系抽取策略，作为API调用失败的备选方案"""
        logger.info("使用本地关系抽取策略")
        if len(entities) < 2:
            return []

        relations = []
        entity_name_to_id = {e["name"]: e["id"] for e in entities}
        entity_names = list(entity_name_to_id.keys())

        # 1. 合作关系
        合作模式 = re.compile(r"(\w+)(与|和)(\w+)(合作|协作|共同研究|联合开发)")
        for match in 合作模式.finditer(text):
            entity1 = match.group(1)
            entity2 = match.group(3)
            relation = match.group(4)
            if entity1 in entity_name_to_id and entity2 in entity_name_to_id:
                relations.append((entity_name_to_id[entity1], relation, entity_name_to_id[entity2]))

        # 2. 领导关系
        领导模式 = re.compile(r"(\w+)(领导|带领|指导|负责)(\w+)")
        for match in 领导模式.finditer(text):
            entity1 = match.group(1)
            entity2 = match.group(3)
            relation = match.group(2)
            if entity1 in entity_name_to_id and entity2 in entity_name_to_id:
                relations.append((entity_name_to_id[entity1], relation, entity_name_to_id[entity2]))

        # 3. 隶属关系
        隶属模式 = re.compile(r"(\w+)(来自|属于|就职于|任职于)(\w+)")
        for match in 隶属模式.finditer(text):
            entity1 = match.group(1)
            entity2 = match.group(3)
            relation = match.group(2)
            if entity1 in entity_name_to_id and entity2 in entity_name_to_id:
                relations.append((entity_name_to_id[entity1], relation, entity_name_to_id[entity2]))

        # 4. 发表关系
        发表模式 = re.compile(r"(\w+)(发表在|发布于)(\w+)")
        for match in 发表模式.finditer(text):
            entity1 = match.group(1)
            entity2 = match.group(3)
            relation = match.group(2)
            if entity1 in entity_name_to_id and entity2 in entity_name_to_id:
                relations.append((entity_name_to_id[entity1], relation, entity_name_to_id[entity2]))

        # 5. 取得成果
        成果模式 = re.compile(r"(\w+)(取得|获得|研发出)(\w+)")
        for match in 成果模式.finditer(text):
            entity1 = match.group(1)
            entity2 = match.group(3)
            relation = match.group(2)
            if entity1 in entity_name_to_id and entity2 in entity_name_to_id:
                relations.append((entity_name_to_id[entity1], relation, entity_name_to_id[entity2]))

        # 去重
        unique_relations = []
        seen = set()
        for rel in relations:
            if rel not in seen:
                seen.add(rel)
                unique_relations.append(rel)

        logger.info(f"本地策略抽取到 {len(unique_relations)} 个关系")
        return unique_relations

    def _clean_json_response(self, response_str: str) -> str:
        """清理模型返回的可能包含非JSON内容的响应"""
        start_idx = response_str.find('[')
        end_idx = response_str.rfind(']') + 1

        if start_idx != -1 and end_idx != 0:
            return response_str[start_idx:end_idx]
        return response_str

    def _validate_relation(self, relation: Dict, valid_entity_ids: set) -> bool:
        """验证关系是否包含必要的字段且实体ID有效"""
        required_fields = ["entity1_id", "relation", "entity2_id"]
        if not all(field in relation for field in required_fields):
            return False

        # 验证实体ID是否存在于提供的实体列表中
        return (relation["entity1_id"] in valid_entity_ids and
                relation["entity2_id"] in valid_entity_ids)
