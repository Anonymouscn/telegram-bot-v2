import datetime
from typing import List, Type
from model.db.t_user import TUser
from provider.db import TelegramBotDBManager
from sqlalchemy.dialects.mysql import insert as mysql_upsert
from util.dict_util import to_dict


def batch_save_user(t_user_list: List[TUser]):
    session = TelegramBotDBManager.borrow_session()
    try:
        session.add_all(t_user_list)
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def batch_save_or_update(t_user_list: List[TUser]):
    session = TelegramBotDBManager.borrow_session()
    try:
        for user in t_user_list:
            stmt = mysql_upsert(TUser).values([to_dict(user)])
            stmt = stmt.on_duplicate_key_update(
                [
                    ("first_name", user.first_name),
                    ("last_name", user.last_name),
                    ("full_name", user.full_name),
                    ("is_bot", user.is_bot),
                    ("language_code", user.language_code),
                    ("updated_at", datetime.datetime.now()),
                ]
            )
            session.execute(stmt)
        session.commit()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def batch_get_user_in_user_id_list(user_id_list: List[int]) -> list[Type[TUser]]:
    if len(user_id_list) == 0:
        return []
    session = TelegramBotDBManager.borrow_session()
    try:
        condition = TUser.id.in_(user_id_list)
        if len(user_id_list) == 1:
            condition = TUser.id == user_id_list[0]
        user_list = session.query(TUser).filter(condition).all()
        return user_list
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)
