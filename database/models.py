# database/models.py

from dataclasses import dataclass
from datetime import datetime

@dataclass
class Word:
    id: int
    english: str
    russian: str
    is_custom: bool  # Добавляем это поле

@dataclass
class UserState:
    user_id: int
    current_word_id: int
    last_interaction: datetime