from model.db.t_base import Base
from sqlalchemy import Column, Integer, String, DateTime, BigInteger


class TAnswer(Base):
    __tablename__ = 't_analysis'

    id = Column(BigInteger, primary_key=True)  # 回复 id
    user_id = Column(BigInteger)  # 用户 id
    month = Column(Integer)  # 月
    year = Column(Integer)  # 年
    domain = Column(String(255))  # 提问领域
    activity_index = Column(Integer)  # 活跃指数
    keyword = Column(String(255))  # 提问关键词
    created_at = Column(DateTime)  # 记录创建时间
    updated_at = Column(DateTime)  # 记录更新时间
    is_deleted = Column(Integer)  # 删除标记位
