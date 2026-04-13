from sqlalchemy import Column, Integer, Text, Float, DateTime

from database import Base


class StudentProgress(Base):
    __tablename__ = "student_progress"

    student_progress_id = Column(Integer, primary_key=True, index=True)
    student_profile_id = Column(Integer, nullable=False)
    subject = Column(Text)
    topic = Column(Text)
    score = Column(Float)
    updated_at = Column(DateTime(timezone=True))

