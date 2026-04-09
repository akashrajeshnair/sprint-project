from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class MessageBase(BaseModel):
	role: str | None = Field(default=None, description="user|assistant|system")
	content: str | None = None
	tool_calls_used: dict | list | None = None
	tokens_used: int | None = Field(default=None, ge=0)


class MessageCreate(MessageBase):
	session_id: int


class MessageRead(MessageBase):
	message_id: int
	session_id: int
	created_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
