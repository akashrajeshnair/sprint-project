# <<<<<<< HEAD
# from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
# from sqlalchemy.dialects.postgresql import ARRAY
# =======
# from sqlalchemy import Column, Integer, Text, DateTime
# from sqlalchemy.dialects.postgresql import JSONB

# >>>>>>> 74b3255f47e97f29216f23bbe61712b18ff64631
# from database import Base


# class StudentProfile(Base):
#     __tablename__ = "student_profiles"

#     student_profile_id = Column(Integer, primary_key=True, index=True)
# <<<<<<< HEAD
#     user_id = Column(Integer, ForeignKey("users.user_id"))

#     grade_level = Column(String)
#     learning_style = Column(String)

#     subjects_enrolled = Column(ARRAY(String))
#     xp_points = Column(Integer)

#     last_active_at = Column(DateTime)
# =======
#     user_id = Column(Integer, nullable=False, unique=True)
#     grade_level = Column(Text)
#     learning_style = Column(Text)
#     subjects_enrolled = Column(JSONB)
#     xp_points = Column(Integer, default=0)
#     last_active_at = Column(DateTime(timezone=True))
# >>>>>>> 74b3255f47e97f29216f23bbe61712b18ff64631

from sqlalchemy import Column, Integer, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from database import Base


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    student_profile_id = Column(Integer, primary_key=True, index=True)

    # 🔗 Link with users table
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)

    # 📚 Academic fields
    grade_level = Column(Text)
    learning_style = Column(Text)

    # 📦 JSON list of subjects
    subjects_enrolled = Column(JSONB)

    # ⭐ XP system
    xp_points = Column(Integer, default=0)

    # 🕒 Last activity
    last_active_at = Column(DateTime(timezone=True))