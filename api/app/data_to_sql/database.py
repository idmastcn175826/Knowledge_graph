from enum import Enum
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker


class DatabaseType(Enum):
    """支持的数据库类型枚举"""
    MYSQL = "mysql"
    DM = "dm"  # 达梦数据库
    KINGBASE = "kingbase"  # 人大金仓



class BaseDatabase:
    """数据库连接基础类"""

    def __init__(self, host, user, password, database, port=None):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.port = port
        self.engine = None
        self.Session = None
        self.db_type = None

    def _create_connection_string(self):
        """创建连接字符串，由子类实现"""
        raise NotImplementedError("子类必须实现此方法")

    def connect(self):
        """建立数据库连接"""
        try:
            conn_str = self._create_connection_string()
            self.engine = create_engine(conn_str)
            self.Session = sessionmaker(bind=self.engine)
            return True
        except Exception as e:
            print(f"连接错误: {str(e)}")
            return False

    def test_connection(self):
        """测试数据库连接"""
        if not self.engine:
            self.connect()

        if self.engine:
            try:
                with self.engine.connect():
                    return True
            except SQLAlchemyError:
                return False
        return False

    def execute_query(self, sql):
        """执行SQL查询并返回结果"""
        if not self.engine:
            if not self.connect():
                raise Exception("数据库连接失败")

        try:
            with self.engine.connect() as connection:
                result = connection.execute(text(sql))
                # 获取列名
                columns = result.keys()
                # 获取数据行
                rows = result.fetchall()
                # 转换为字典列表
                return [dict(zip(columns, row)) for row in rows]
        except SQLAlchemyError as e:
            raise Exception(f"SQL执行错误: {str(e)}")

    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            self.Session = None


class MySQLDatabase(BaseDatabase):
    """MySQL数据库连接类"""

    def __init__(self, host, user, password, database, port=3306):
        super().__init__(host, user, password, database, port)
        self.db_type = DatabaseType.MYSQL

    def _create_connection_string(self):
        """创建MySQL连接字符串"""
        return f"mysql+pymysql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}?charset=utf8mb4"


class DMDatabase(BaseDatabase):
    """达梦数据库连接类"""

    def __init__(self, host, user, password, database, port=5236):
        super().__init__(host, user, password, database, port)
        self.db_type = DatabaseType.DM

    def _create_connection_string(self):
        """创建达梦数据库连接字符串"""
        return f"dm+dmPython://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class KingbaseDatabase(BaseDatabase):
    """人大金仓数据库连接类"""

    def __init__(self, host, user, password, database, port=54321):
        super().__init__(host, user, password, database, port)
        self.db_type = DatabaseType.KINGBASE

    def _create_connection_string(self):
        """创建人大金仓数据库连接字符串"""
        return f"kingbase8+psycopg2://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"


class DatabaseFactory:
    """数据库工厂类，用于创建不同类型的数据库连接"""

    def create_database(self, db_type, host, user, password, database, port=None):
        """
        创建数据库连接实例
        :param db_type: 数据库类型
        :param host: 主机地址
        :param user: 用户名
        :param password: 密码
        :param database: 数据库名
        :param port: 端口号，None则使用默认端口
        :return: 数据库连接实例
        """
        if db_type == DatabaseType.MYSQL:
            return MySQLDatabase(host, user, password, database, port)
        elif db_type == DatabaseType.DM:
            return DMDatabase(host, user, password, database, port)
        elif db_type == DatabaseType.KINGBASE:
            return KingbaseDatabase(host, user, password, database, port)
        else:
            raise ValueError(f"不支持的数据库类型: {db_type}")
