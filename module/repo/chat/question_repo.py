from typing import List
from sqlalchemy import desc
from model.db.t_question import TQuestion
from provider.db import TelegramBotDBManager


def batch_save_question(t_question_list: List[TQuestion]):
    session = TelegramBotDBManager.borrow_session()
    try:
        session.add_all(t_question_list)
        session.bulk_save_objects()
        session.commit()
        session.flush()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def save_question(question: TQuestion):
    session = TelegramBotDBManager.borrow_session()
    try:
        session.add(question)
        session.commit()
        result = session.query(TQuestion).filter(TQuestion.session_id == question.session_id,
                                                 TQuestion.is_deleted == 0).order_by(desc(TQuestion.id)).first()
        return result
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def batch_get_question_in_session_collection(session_id_list: List[int]) -> list[TQuestion]:
    session = TelegramBotDBManager.borrow_session()
    try:
        condition = TQuestion.session_id.in_(session_id_list)
        if len(session_id_list) == 1:
            condition = TQuestion.session_id == session_id_list[0]
        session_list = session.query(TQuestion).filter(condition, TQuestion.is_deleted == 0).all()
        return session_list
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def get_latest_question(session_id: int):
    session = TelegramBotDBManager.borrow_session()
    try:
        return session.query(TQuestion).filter(TQuestion.session_id == session_id, TQuestion.is_deleted == 0).order_by(
            desc(TQuestion.id)).first()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)
