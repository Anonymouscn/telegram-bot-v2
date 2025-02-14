import datetime

from model.db.t_base import Base
from sqlalchemy import Column, Integer, DateTime, BigInteger, String


class TSession(Base):
    __tablename__ = 't_session'

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=True)  # id
    user_id = Column(BigInteger, nullable=False)  # 用户 id
    name = Column(String(50), nullable=False)  # 名称
    factory = Column(String(50), nullable=False)  # 工厂
    model = Column(String(50), nullable=False)  # 模型
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录创建时间
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录更新时间
    is_deleted = Column(Integer, nullable=False, default=0)  # 删除标记位
