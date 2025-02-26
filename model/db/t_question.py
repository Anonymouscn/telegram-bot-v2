import datetime
from model.db.t_base import Base
from sqlalchemy import Column, Integer, String, DateTime, BigInteger


# 问题表
class TQuestion(Base):
    __tablename__ = 't_question'

    id = Column(BigInteger, primary_key=True, autoincrement=True)  # 问题 id
    session_id = Column(BigInteger, nullable=False)  # 关联会话 id
    parent_id = Column(BigInteger, nullable=False, default=0)  # 关联上个问题
    type = Column(Integer, nullable=False, default=0)  # 问题数据类型
    content = Column(String(255), nullable=False)  # 问题内容
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录创建时间
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录更新时间
    is_deleted = Column(Integer, nullable=False, default=0)  # 删除标记位
