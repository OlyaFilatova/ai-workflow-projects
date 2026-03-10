from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Status = Literal['new', 'done']


class User(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    class_: str | None = Field(default=None, alias="class")
