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


class UploadResponse(BaseModel):
    message: str = Field(...)
    original_filename: str = Field(...)
    s3_key: str = Field(...)
    s3_url: str = Field(...)
    size: int = Field(default=0)
