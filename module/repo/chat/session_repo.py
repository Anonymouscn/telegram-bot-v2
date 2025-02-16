from typing import List
from sqlalchemy import desc, func
from model.db.t_session import TSession
from provider.db import TelegramBotDBManager


def batch_save_session(t_session_list: List[TSession]):
    session = TelegramBotDBManager.borrow_session()
    try:
        session.add_all(t_session_list)
        session.commit()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def get_session_id_by_name(user_id: int, name: str, factory: str):
    session = TelegramBotDBManager.borrow_session()
    conditions = [
        TSession.user_id == user_id,
        TSession.name == name,
        TSession.factory == factory,
    ]
    try:
        return session.query(TSession.id).filter(*conditions).first()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def count_user_sessions(user_id: int, factory: str, search: str = None, offset: int = None):
    session = TelegramBotDBManager.borrow_session()
    conditions = [
        TSession.user_id == user_id,
        TSession.factory == factory
    ]
    if search is not None and search != '':
        conditions.append(TSession.name.like('%'+search+'%'))
    try:
        result = session.query(func.count(TSession.id)).filter(*conditions).scalar()
        if offset is not None and offset > 0:
            result -= offset
        return result
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def is_exist_session(user_id: int, factory: str, name: str):
    session = TelegramBotDBManager.borrow_session()
    conditions = [
        TSession.user_id == user_id,
        TSession.factory == factory,
        TSession.name == name,
    ]
    try:
        result = session.query(TSession).filter(*conditions).first()
        return result is not None
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def get_session_by_name(user_id: int, name: str, factory: str):
    session = TelegramBotDBManager.borrow_session()
    conditions = [
        TSession.user_id == user_id,
        TSession.name == name,
        TSession.factory == factory,
    ]
    try:
        return session.query(TSession).filter(*conditions).first()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def batch_get_session_in_user_collection(
        user_id_list: List[int], factory: str = None, model: str = None, limit: int = None, search: str = None, offset: int = None) -> list[TSession]:
    session = TelegramBotDBManager.borrow_session()
    conditions = []
    if factory is not None:
        conditions.append(TSession.factory == factory)
    if model is not None:
        conditions.append(TSession.model == model)
    if len(user_id_list) > 1:
        conditions.append(TSession.user_id.in_(user_id_list))
    else:
        if len(user_id_list) == 1:
            conditions.append(TSession.user_id == user_id_list[0])
    if search is not None and search != '':
        conditions.append(TSession.name.like('%'+search+'%'))
    try:
        query = session.query(TSession).filter(*conditions).order_by(desc(TSession.id))
        if limit is not None:
            query = query.limit(limit)
        if offset is not None and offset != 0:
            query = query.offset(offset)
        session_list = query.all()
        return session_list
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def get_last_session(user_id: int, factory: str):
    session = TelegramBotDBManager.borrow_session()
    conditions = [
        TSession.user_id == user_id,
        TSession.factory == factory
    ]
    try:
        return session.query(TSession).filter(*conditions).order_by(desc(TSession.id)).first()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)
