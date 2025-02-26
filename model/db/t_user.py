import datetime
from model.db.t_base import Base
from sqlalchemy import Column, Integer, String, DateTime, BigInteger


# 用户表
class TUser(Base):
    __tablename__ = 't_user'

    id = Column(BigInteger, primary_key=True, nullable=False, autoincrement=False)  # id
    first_name = Column(String(100), nullable=False, default='')  # 名
    last_name = Column(String(100), nullable=False, default='')  # 姓
    full_name = Column(String(200), nullable=False, default='')  # 全名
    is_bot = Column(Integer, nullable=False, default=False)  # 是否是机器人
    language_code = Column(String(50), nullable=False, default='')  # 语言代码
    remark = Column(String(50), nullable=False, default='')  # 备注
    is_ban = Column(Integer, nullable=False, default=0)  # 是否被封禁
    created_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录创建时间
    updated_at = Column(DateTime, nullable=False, default=datetime.datetime.now())  # 记录更新时间
    is_deleted = Column(Integer, nullable=False, default=0)  # 删除标记位
