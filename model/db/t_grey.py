from model.db.t_base import Base
from sqlalchemy import Column, Integer, DateTime, BigInteger


class TAnswer(Base):
    __tablename__ = 't_grey'

    id = Column(BigInteger, primary_key=True)  # 回复 id
    grey_enum = Column(Integer)  # 灰度枚举值
    user_id = Column(BigInteger)  # 用户 id
    created_at = Column(DateTime)  # 记录创建时间
    updated_at = Column(DateTime)  # 记录更新时间
    is_deleted = Column(Integer)  # 删除标记位
