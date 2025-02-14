class DBConfig:
    def __init__(self, username: str, password: str, host: str, port: int, database: str, db_type: str):
        self.db_type = db_type
        self.username = username
        self.password = password
        self.host = host
        self.port = port
        self.database = database

    def get_link(self) -> str:
        link = f"{self.db_type}://{self.username}:{self.password}@{self.host}$port/{self.database}"
        mask = ""
        if self.port is not None and self.port != 0:
            mask = str(self.port)
        return link.replace("$port", mask)


class DBPoolConfig:
    def __init__(self, size, timeout, recycle):
        self.size = size
        self.timeout = timeout
        self.recycle = recycle


class DBConnConfig:
    def __init__(self, limit: int):
        self.limit = limit
