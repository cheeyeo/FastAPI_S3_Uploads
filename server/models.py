from datetime import datetime
from pydantic import BaseModel, Field


class UploadSchema(BaseModel):
    filename: str = Field(...)
    current: int = Field(default=0)
    size: float = Field(...)
    percentage: float = Field(default=0.0)
    created_at: datetime = datetime.now()


class UpdateUploadSchema(BaseModel):
    current: int
    percentage: float
