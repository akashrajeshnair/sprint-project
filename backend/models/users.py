from __future__ import annotations

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

try:
	from database import Base
except ModuleNotFoundError:
	from backend.database import Base


class User(Base):
	__tablename__ = "users"

	user_id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
	name: Mapped[str | None] = mapped_column(String(255), nullable=True)
	email: Mapped[str | None] = mapped_column(String(255), nullable=True)
	password: Mapped[str | None] = mapped_column(String(255), nullable=True)
	role: Mapped[str | None] = mapped_column(String(50), nullable=True)
	subject: Mapped[str | None] = mapped_column(String(255), nullable=True)
	timestamp: Mapped[DateTime | None] = mapped_column("timestamp", DateTime(timezone=True), server_default=func.now())
	updated_at: Mapped[DateTime | None] = mapped_column(DateTime(timezone=True), nullable=True)
