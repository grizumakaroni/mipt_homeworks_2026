from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypeAlias


Role: TypeAlias = Literal['system', 'user', 'assistant']


@dataclass(frozen=True)
class Message:
    role: Role
    content: str
