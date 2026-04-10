from sqlalchemy import Column, Integer, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB

from database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    student_profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, unique=True)
    grade_level = Column(Text)
    learning_style = Column(Text)
    subjects_enrolled = Column(JSONB)
    xp_points = Column(Integer, default=0)
    last_active_at = Column(DateTime(timezone=True))