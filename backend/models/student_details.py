from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import ARRAY
from database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    student_profile_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"))

    grade_level = Column(String)
    learning_style = Column(String)

    subjects_enrolled = Column(ARRAY(String))
    xp_points = Column(Integer)

    last_active_at = Column(DateTime)