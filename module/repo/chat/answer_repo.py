from typing import List
from model.db.t_answer import TAnswer
from provider.db import TelegramBotDBManager


def batch_save_answer(t_answer_list: List[TAnswer]):
    session = TelegramBotDBManager.borrow_session()
    try:
        session.add_all(t_answer_list)
        session.commit()
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)


def batch_get_answer_in_session_collection(session_id_list: List[int]) -> list[TAnswer]:
    session = TelegramBotDBManager.borrow_session()
    condition = TAnswer.session_id.in_(session_id_list)
    if len(session_id_list) == 1:
        condition = TAnswer.session_id == session_id_list[0]
    try:
        answer_list = session.query(TAnswer).filter(condition, TAnswer.is_deleted == 0).all()
        return answer_list
    finally:
        if session is not None:
            TelegramBotDBManager.return_session(session)
