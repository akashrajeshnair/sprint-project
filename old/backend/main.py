from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Model
from .schemas import ModelCreate, ModelResponse

app = FastAPI(title="LLM Token API")

Base.metadata.create_all(bind=engine)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/llms", response_model=list[ModelResponse])
def get_llms(db: Session = Depends(get_db)):
    return db.query(Model).order_by(Model.model_name.asc()).all()


@app.get("/llms/{model_name}", response_model=ModelResponse)
def get_llm_by_name(model_name: str, db: Session = Depends(get_db)):
    model = db.query(Model).filter(Model.model_name == model_name).first()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return model


@app.post("/llms", response_model=ModelResponse, status_code=201)
def create_llm(payload: ModelCreate, db: Session = Depends(get_db)):
    if payload.tokens_used > payload.total_tokens:
        raise HTTPException(
            status_code=400,
            detail="tokens_used cannot be greater than total_tokens",
        )

    llm = Model(
        model_name=payload.model_name.strip(),
        total_tokens=payload.total_tokens,
        tokens_used=payload.tokens_used,
    )

    db.add(llm)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Model name already exists")

    db.refresh(llm)
    return llm
