import atexit
import os
import threading
import time

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from db.config import DBConfig


def create_engine_from_config(config: DBConfig):
    return create_engine(
        config.get_link(),
        echo=True,
        max_overflow=0,
        pool_size=40,
        pool_timeout=30,
        pool_recycle=10
    )


def read_config_from_system() -> DBConfig:
    env = os.environ
    port_str = env.get("TELEGRAM_DB_PORT")
    if port_str is None or port_str == '':
        port = 0
    else:
        port = int(port_str)
    conf = DBConfig(
        username=env.get("TELEGRAM_DB_USERNAME"),
        password=env.get("TELEGRAM_DB_PASSWORD"),
        host=env.get("TELEGRAM_DB_HOST"),
        port=port,
        database=env.get("TELEGRAM_DB_DATABASE"),
        db_type=env.get("TELEGRAM_DB_TYPE")
    )
    print(conf)
    return conf


class DBSessionManager:
    def __init__(self, core: int = 4, limit: int = 100):
        self.engine = create_engine_from_config(read_config_from_system())
        self.db_session = sessionmaker(bind=self.engine)
        self.session_pool = []
        self.core = core
        self.used = core
        for i in range(core):
            self.session_pool.append(self.db_session())
        self.lock = threading.Lock()
        self.limit = limit
        atexit.register(self.shutdown)

    def borrow_session(self) -> Session | None:
        return self.db_session()
        # self.lock.acquire()
        # try:
        #     if len(self.session_pool) <= 0:
        #         if self.used < self.limit:
        #             self.used += 1
        #             return self.db_session()
        #         return None
        #     session = self.session_pool[0]
        #     self.session_pool = self.session_pool[1:]
        # finally:
        #     self.lock.release()
        # return session

    def return_session(self, session: Session):
        session.flush()
        session.close()
        # self.lock.acquire()
        # try:
        #     if len(self.session_pool) > self.core:
        #         session.flush()
        #         session.close()
        #         self.used -= 1
        #     else:
        #         self.session_pool.append(session)
        # finally:
        #     self.lock.release()

    def shutdown(self):
        def clean_up():
            while len(self.session_pool) < self.used:
                time.sleep(1000)
            for session in self.session_pool:
                session.close()
        return clean_up
