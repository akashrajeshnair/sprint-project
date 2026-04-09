from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class SessionBase(BaseModel):
	user_id: int
	subject: str | None = None
	topic: str | None = None
	difficulty_level: str | None = None


class SessionCreate(SessionBase):
	pass


class SessionUpdate(BaseModel):
	subject: str | None = None
	topic: str | None = None
	difficulty_level: str | None = None


class SessionRead(SessionBase):
	session_id: int
	started_at: datetime | None = None
	updated_at: datetime | None = None

	model_config = ConfigDict(from_attributes=True)
