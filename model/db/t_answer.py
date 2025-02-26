import datetime
from model.db.t_base import Base
from sqlalchemy import Column, Integer, String, DateTime, BigInteger


# 回复表
class TAnswer(Base):
    __tablename__ = 't_answer'

    id = Column(BigInteger, primary_key=True, nullable=False)  # 回复 id
    session_id = Column(BigInteger, nullable=False)  # 关联会话 id
    question_id = Column(BigInteger, nullable=False)  # 关联问题 id
    type = Column(Integer, nullable=False, default=0)  # 回复数据类型
    content = Column(String(255), nullable=False)  # 回复内容
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录创建时间
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录更新时间
    is_deleted = Column(Integer, nullable=False, default=0)  # 删除标记位
