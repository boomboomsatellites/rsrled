from dataclasses import dataclass

@dataclass
class Post:
    source: str
    external_id: str
    posted_at: str
    author_name: str
    text: str
    url: str = ""

@dataclass
class DisplayMessage:
    message_type: str
    title: str
    body: str
    priority: int = 0
    duration_seconds: int = 8
