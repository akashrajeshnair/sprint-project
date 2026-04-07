from sqlalchemy import BigInteger, Column, Integer, String

from .database import Base


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(120), unique=True, nullable=False)
    total_tokens = Column(BigInteger, nullable=False)
    tokens_used = Column(BigInteger, nullable=False, default=0)