from typing import List
from model.data.d_chat import ChatMessage, SessionInfo, ChatContent
from module.repo.chat.answer_repo import batch_get_answer_in_session_collection
from module.repo.chat.question_repo import batch_get_question_in_session_collection
from module.repo.chat.session_repo import batch_get_session_in_user_collection


def batch_get_sessions_in_user_collection(
        user_id_list: List[int], factory: str = None, model: str = None) -> List[SessionInfo]:
    sessions = batch_get_session_in_user_collection(user_id_list, factory, model)
    result = []
    for session in sessions:
        result.append(SessionInfo(session.id, session.name))
    return result


class QuestionPoint:
    def __init__(self, message: ChatMessage, parent: int = 0, answer: ChatMessage = None,
                 next_ptr: ChatMessage = None):
        self.message = message
        self.parent = parent
        self.answer = answer
        self.next_ptr = next_ptr


def batch_get_chat_content_in_session_collection(session_id_list: List[int], content_type: str = 'multiple') \
        -> list[list[dict]]:
    questions = batch_get_question_in_session_collection(session_id_list)
    answers = batch_get_answer_in_session_collection(session_id_list)
    # 1.建问题图
    question_map: dict[int, QuestionPoint] = {}
    for question in questions:
        content: ChatContent | None = None
        match question.type:
            case 0:
                content = ChatContent(t='text', text=question.content)
            case 1:
                content = ChatContent(t='image_url', image_url=question.content)
        if content is not None:
            if content_type == 'multiple':
                point = QuestionPoint(
                    parent=question.parent_id,
                    message=ChatMessage(role='user', content=[content])
                )
            else:
                point = QuestionPoint(
                    parent=question.parent_id,
                    message=ChatMessage(role='user', content=content.text)
                )
            question_map[question.id] = point
    # 2.倒转链条
    raw_table = []
    for point in question_map.values():
        if point.parent is not None and point.parent in question_map:
            prev_node = question_map[point.parent]
            if prev_node is not None:
                prev_node.next_ptr = point
        else:
            raw_table.append(point)
    # 3.补充回复
    for answer in answers:
        c = None
        match answer.type:
            case 0:
                c = ChatContent(t='text', text=answer.content)
            case 1:
                c = ChatContent(t='image_url', image_url=answer.content)
        if content_type == 'multiple':
            ans = [c]
        else:
            ans = c.text
        question_map[answer.question_id].answer = (
            ChatMessage(role='assistant', content=ans)
        )
    # 4.提取链条
    result: list[list[dict]] = []
    for chain in raw_table:
        chat_content = []
        ptr = chain
        while ptr is not None:
            if ptr.message is not None:
                chat_content.append(ptr.message.to_map())
            if ptr.answer is not None:
                chat_content.append(ptr.answer.to_map())
            ptr = ptr.next_ptr
        result.append(chat_content)
    return result
