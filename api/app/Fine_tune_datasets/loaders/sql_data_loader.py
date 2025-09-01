from datetime import datetime, date
from typing import List, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from app.Fine_tune_datasets.foundation.data_processor import DataLoader


class SqlDatabaseDataLoader(DataLoader):
    """数据库数据加载器，支持MySQL、PostgreSQL、SQLite、Oracle"""

    def __init__(self):
        super().__init__()  # 调用父类构造方法
        self.supported_db_types = {
            'mysql': self._get_mysql_connection_str,
            'postgresql': self._get_postgresql_connection_str,
            'sqlite': self._get_sqlite_connection_str,
            'oracle': self._get_oracle_connection_str
        }

    def load(self, source_info: Dict[str, Any]) -> List[Dict]:
        """从数据库加载数据（实现DataLoader的抽象方法）"""
        # 获取数据库配置
        db_type = source_info.get('type', 'mysql')
        connection_str = source_info.get('connection_str')
        query = source_info.get('query')
        config = source_info.get('config', {})

        # 验证必要参数
        if not query:
            raise ValueError("数据库查询语句不能为空")

        # 验证数据库类型是否支持
        if db_type not in self.supported_db_types:
            raise ValueError(f"不支持的数据库类型: {db_type}，当前支持：{list(self.supported_db_types.keys())}")

        # 如果没有提供连接字符串，尝试从配置构建
        if not connection_str:
            connection_str = self._build_connection_str(db_type, config)
            if not connection_str:
                raise ValueError("数据库连接信息不完整")

        try:
            # 创建数据库连接
            engine = create_engine(connection_str, **self._get_engine_options(db_type))

            # 执行查询
            with engine.connect() as conn:
                result = conn.execute(text(query))
                columns = result.keys()
                data = [dict(zip(columns, row)) for row in result.fetchall()]

            # 修复：日期时间类型转换（关键修改点）
            processed_data = []
            for item in data:
                processed_item = {}
                for key, value in item.items():
                    # 处理date类型（直接使用导入的date）
                    if isinstance(value, date):
                        processed_item[key] = value.strftime('%Y-%m-%d')
                    # 处理datetime类型（直接使用导入的datetime）
                    elif isinstance(value, datetime):
                        processed_item[key] = value.strftime('%Y-%m-%d %H:%M:%S')
                    # 其他类型保持不变
                    else:
                        processed_item[key] = value
                processed_data.append(processed_item)

            return processed_data  # 返回处理后的数据

        except SQLAlchemyError as e:
            raise Exception(f"数据库查询失败: {str(e)}")
        except Exception as e:
            raise Exception(f"数据库操作异常: {str(e)}")

    # 以下方法保持不变
    def _build_connection_str(self, db_type: str, config: Dict) -> str:
        """根据配置构建数据库连接字符串"""
        if db_type not in self.supported_db_types:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        return self.supported_db_types[db_type](config)

    def _get_mysql_connection_str(self, config: Dict) -> str:
        """构建MySQL连接字符串（包含字符集配置）"""
        required = ['host', 'database', 'user', 'password']
        self._validate_config(config, required, 'MySQL')
        port = config.get('port', 3306)
        return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{port}/{config['database']}?charset=utf8mb4"

    def _get_postgresql_connection_str(self, config: Dict) -> str:
        """构建PostgreSQL连接字符串"""
        required = ['host', 'database', 'user', 'password']
        self._validate_config(config, required, 'PostgreSQL')
        port = config.get('port', 5432)
        return f"postgresql://{config['user']}:{config['password']}@{config['host']}:{port}/{config['database']}"

    def _get_sqlite_connection_str(self, config: Dict) -> str:
        """构建SQLite连接字符串"""
        if 'database' not in config:
            raise ValueError("SQLite配置需要database参数（数据库文件路径）")
        return f"sqlite:///{config['database']}"

    def _get_oracle_connection_str(self, config: Dict) -> str:
        """构建Oracle连接字符串"""
        required = ['host', 'service_name', 'user', 'password']
        self._validate_config(config, required, 'Oracle')
        port = config.get('port', 1521)
        return f"oracle+cx_oracle://{config['user']}:{config['password']}@{config['host']}:{port}/?service_name={config['service_name']}"

    def _validate_config(self, config: Dict, required_fields: List[str], db_name: str):
        """验证配置是否包含必要字段"""
        missing = [field for field in required_fields if field not in config]
        if missing:
            raise ValueError(f"{db_name}配置缺少必要字段: {', '.join(missing)}")

    def _get_engine_options(self, db_type: str) -> Dict:
        """获取数据库引擎选项"""
        options = {
            'pool_recycle': 3600,
            'pool_pre_ping': True
        }
        if db_type == 'postgresql':
            options['client_encoding'] = 'utf8'
        return options

    def test_connection(self, config: Dict) -> bool:
        """测试数据库连接是否正常"""
        try:
            test_config = {
                'config': config,
                'type': config.get('type', 'mysql'),
                'query': 'SELECT 1'
            }
            self.load(test_config)
            return True
        except Exception:
            return False

    def get_table_schema(self, config: Dict, table_name: str) -> List[Dict]:
        """获取指定表的结构信息"""
        schema_queries = {
            'mysql': f"DESCRIBE {table_name}",
            'postgresql': f"SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = '{table_name}'",
            'sqlite': f"PRAGMA table_info({table_name})",
            'oracle': f"SELECT column_name, data_type, nullable FROM all_tab_columns WHERE table_name = '{table_name.upper()}'"
        }
        db_type = config.get('type', 'mysql')
        if db_type not in schema_queries:
            raise ValueError(f"不支持的数据库类型: {db_type}")
        try:
            test_config = {
                'config': config,
                'type': db_type,
                'query': schema_queries[db_type]
            }
            return self.load(test_config)
        except Exception as e:
            raise Exception(f"获取表结构失败: {str(e)}")