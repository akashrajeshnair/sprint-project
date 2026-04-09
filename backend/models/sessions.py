from __future__ import annotations

from sqlalchemy import DateTime, ForeignKey, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

try:
	from database import Base
except ModuleNotFoundError:
	from backend.database import Base


class Session(Base):
	__tablename__ = "sessions"

	session_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"), nullable=False, index=True)
	subject: Mapped[str | None] = mapped_column(Text, nullable=True)
	topic: Mapped[str | None] = mapped_column(Text, nullable=True)
	difficulty_level: Mapped[str | None] = mapped_column(Text, nullable=True)
	started_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[DateTime | None] = mapped_column(
		DateTime(timezone=True),
		server_default=func.now(),
		onupdate=func.now(),
	)

	messages = relationship("Message", back_populates="session", cascade="all, delete-orphan")
