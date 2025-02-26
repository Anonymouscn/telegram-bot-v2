import os
from db.engine import DBSessionManager

env = os.environ
TelegramBotDBManager = DBSessionManager(
        core=int(env.get("TELEGRAM_DB_CORE_POOL_SIZE", "4")),
        limit=int(env.get("TELEGRAM_DB_MAX_POOL_SIZE", "100"))
)


# 初始化数据库
def init_db():
    e = os.environ
    global TelegramBotDBManager
    TelegramBotDBManager = DBSessionManager(
        core=int(e.get("TELEGRAM_DB_CORE_POOL_SIZE", "4")),
        limit=int(e.get("TELEGRAM_DB_MAX_POOL_SIZE", "100"))
    )
