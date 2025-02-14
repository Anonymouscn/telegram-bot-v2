from typing import List


class ChatContent:
    def __init__(self, t: str, text: str = None, image_url: str = None):
        self.t = t
        self.text = text
        self.image_url = image_url

    def to_map(self):
        return {
            "type": self.t,
            "text": self.text,
            "image_url": self.image_url,
        }


class ChatMessage:
    def __init__(self, role: str, content: List[ChatContent] | str):
        self.role = role
        self.content = content

    def to_map(self):
        if not isinstance(self.content, str):
            content = []
            for item in self.content:
                content.append(item.to_map())
        else:
            content = self.content
        return {
            "role": self.role,
            "content": content
        }


class SessionInfo:
    def __init__(self, id: int, name: str):
        self.id = id
        self.name = name
