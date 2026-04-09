from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
	from database import Base
except ModuleNotFoundError:
	from database import Base


class Message(Base):
	__tablename__ = "messages"

	message_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	session_id: Mapped[int] = mapped_column(ForeignKey("sessions.session_id"), nullable=False, index=True)
	role: Mapped[str | None] = mapped_column(Text, nullable=True)
	content: Mapped[str | None] = mapped_column(Text, nullable=True)
	tool_calls_used: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
	tokens_used: Mapped[int | None] = mapped_column(Integer, nullable=True)
	created_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())

	session = relationship("Session", back_populates="messages")
