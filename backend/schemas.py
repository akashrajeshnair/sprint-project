from pydantic import BaseModel, Field


class ModelCreate(BaseModel):
    model_name: str = Field(min_length=1, max_length=120)
    total_tokens: int = Field(ge=0)
    tokens_used: int = Field(ge=0)


class ModelResponse(ModelCreate):
    id: int

    class Config:
        from_attributes = True
