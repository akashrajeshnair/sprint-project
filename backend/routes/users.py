# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from backend.database import SessionLocal
# from backend.models.users import User

# router = APIRouter()


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @router.get("/users/{user_id}")
# def get_user(user_id: int, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == user_id).first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return {
#         "user_id": user.user_id,
#         "name": user.name,
#         "email": user.email,
#         "role": user.role,
#         "subject": user.subject,
#     }

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from backend.database import SessionLocal
# from backend.models.users import User

# router = APIRouter()


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @router.get("/users/students")
# def get_all_students(db: Session = Depends(get_db)):
#     students = db.query(User).filter(User.role == "student").all()

#     return [
#         {
#             "user_id": student.user_id,
#             "name": student.name,
#             "email": student.email,
#             "role": student.role,
#             "subject": student.subject,
#         }
#         for student in students
#     ]


# @router.get("/users/{user_id}")
# def get_user(user_id: int, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == user_id).first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return {
#         "user_id": user.user_id,
#         "name": user.name,
#         "email": user.email,
#         "role": user.role,
#         "subject": user.subject,
#     }

# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session
# from backend.database import SessionLocal
# from backend.models.users import User
# from pydantic import BaseModel

# router = APIRouter()

# # ----------------------
# # DB session dependency
# # ----------------------
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()

# # ----------------------
# # Pydantic response model
# # ----------------------
# class UserOut(BaseModel):
#     user_id: int
#     name: str
#     email: str
#     role: str
#     subject: str

#     class Config:
#         orm_mode = True

# # ----------------------
# # 1️⃣ Get all students
# # Route: /users/students
# # ----------------------
# @router.get("/students", response_model=list[UserOut])
# def get_all_students(db: Session = Depends(get_db)):
#     students = db.query(User).filter(User.role == "student").all()
#     return students

# # ----------------------
# # 2️⃣ Get single user by ID (safe route)
# # Route: /users/by-id/{user_id}
# # ----------------------
# @router.get("/by-id/{user_id}", response_model=UserOut)
# def get_user(user_id: int, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == user_id).first()
#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")
#     return user

# from pydantic import BaseModel, EmailStr
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from backend.database import SessionLocal
# from backend.models.users import User

# router = APIRouter()


# class CreateUserRequest(BaseModel):
#     name: str
#     email: EmailStr
#     password: str
#     role: str
#     subject: str | None = None


# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @router.get("/users/students")
# def get_all_students(db: Session = Depends(get_db)):
#     students = db.query(User).filter(User.role == "student").all()

#     return [
#         {
#             "user_id": student.user_id,
#             "name": student.name,
#             "email": student.email,
#             "role": student.role,
#             "subject": student.subject,
#         }
#         for student in students
#     ]


# @router.get("/users/teachers")
# def get_all_teachers(db: Session = Depends(get_db)):
#     teachers = db.query(User).filter(User.role == "teacher").all()

#     return [
#         {
#             "user_id": teacher.user_id,
#             "name": teacher.name,
#             "email": teacher.email,
#             "role": teacher.role,
#             "subject": teacher.subject,
#         }
#         for teacher in teachers
#     ]


# @router.get("/users/by-id/{user_id}")
# def get_user(user_id: int, db: Session = Depends(get_db)):
#     user = db.query(User).filter(User.user_id == user_id).first()

#     if not user:
#         raise HTTPException(status_code=404, detail="User not found")

#     return {
#         "user_id": user.user_id,
#         "name": user.name,
#         "email": user.email,
#         "role": user.role,
#         "subject": user.subject,
#     }


# @router.post("/users")
# def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
#     role = payload.role.lower().strip()

#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Role must be student or teacher")

#     if role == "teacher" and not payload.subject:
#         raise HTTPException(status_code=400, detail="Subject is required for teacher")

#     subject_value = None if role == "student" else payload.subject

#     existing_user = db.query(User).filter(User.email == payload.email).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Email already exists")

#     new_user = User(
#         name=payload.name,
#         email=payload.email,
#         password=payload.password,
#         role=role,
#         subject=subject_value,
#     )

#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     return {
#         "message": "User created successfully",
#         "user": {
#             "user_id": new_user.user_id,
#             "name": new_user.name,
#             "email": new_user.email,
#             "role": new_user.role,
#             "subject": new_user.subject,
#         },
#     }
# from pydantic import BaseModel, EmailStr
# from fastapi import APIRouter, Depends, HTTPException
# from sqlalchemy.orm import Session

# from database import SessionLocal
# from models.users import User

# router = APIRouter()


# # ✅ Request Schema
# class CreateUserRequest(BaseModel):
#     name: str
#     email: EmailStr
#     password: str
#     role: str
#     subject: str | None = None


# # ✅ DB Dependency
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# # ✅ GET ALL STUDENTS
# @router.get("/students")
# def get_students(db: Session = Depends(get_db)):
#     students = db.query(User).filter(User.role == "student").all()

#     return [
#         {
#             "name": s.name,
#             "email": s.email,
#             "role": s.role,
#             "subject": s.subject,
#         }
#         for s in students
#     ]


# # ✅ GET ALL TEACHERS
# @router.get("/teachers")
# def get_teachers(db: Session = Depends(get_db)):
#     teachers = db.query(User).filter(User.role == "teacher").all()

#     return [
#         {
#             "name": t.name,
#             "email": t.email,
#             "role": t.role,
#             "subject": t.subject,
#         }
#         for t in teachers
#     ]


# # ✅ CREATE USER (MAIN FUNCTION)
# @router.post("/users")
# def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
#     role = payload.role.lower().strip()

#     # ✅ Validate role
#     if role not in ["student", "teacher"]:
#         raise HTTPException(status_code=400, detail="Role must be student or teacher")

#     # ✅ Validate subject
#     if role == "teacher" and not payload.subject:
#         raise HTTPException(status_code=400, detail="Subject is required for teacher")

#     subject_value = payload.subject if role == "teacher" else None

#     # ✅ Check duplicate email
#     existing_user = db.query(User).filter(User.email == payload.email).first()
#     if existing_user:
#         raise HTTPException(status_code=400, detail="Email already exists")

#     # ✅ Create user
#     new_user = User(
#         name=payload.name,
#         email=payload.email,
#         password=payload.password,
#         role=role,
#         subject=subject_value,
#     )

#     db.add(new_user)
#     db.commit()
#     db.refresh(new_user)

#     return {
#         "message": "User created successfully",
#         "name": new_user.name,
#         "email": new_user.email,
#         "role": new_user.role,
#         "subject": new_user.subject,
#     }

from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import SessionLocal
from models.users import User

router = APIRouter()


class CreateUserRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    role: str
    subject: str | None = None


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/students")
def get_students(db: Session = Depends(get_db)):
    students = db.query(User).filter(User.role == "student").all()

    return [
        {
            "user_id": s.user_id,
            "name": s.name,
            "email": s.email,
            "role": s.role,
            "subject": s.subject,
        }
        for s in students
    ]


@router.get("/teachers")
def get_teachers(db: Session = Depends(get_db)):
    teachers = db.query(User).filter(User.role == "teacher").all()

    return [
        {
            "user_id": t.user_id,
            "name": t.name,
            "email": t.email,
            "role": t.role,
            "subject": t.subject,
        }
        for t in teachers
    ]


@router.get("/users/{user_id}")
def get_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.user_id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "user_id": user.user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "subject": user.subject,
    }


@router.post("/users")
def create_user(payload: CreateUserRequest, db: Session = Depends(get_db)):
    role = payload.role.lower().strip()

    if role not in ["student", "teacher"]:
        raise HTTPException(status_code=400, detail="Role must be student or teacher")

    if role == "teacher" and not payload.subject:
        raise HTTPException(status_code=400, detail="Subject is required for teacher")

    subject_value = payload.subject if role == "teacher" else None

    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already exists")

    new_user = User(
        name=payload.name,
        email=payload.email,
        password=payload.password,
        role=role,
        subject=subject_value,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return {
        "message": "User created successfully",
        "name": new_user.name,
        "email": new_user.email,
        "role": new_user.role,
        "subject": new_user.subject,
    }