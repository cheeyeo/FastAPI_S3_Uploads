from datetime import datetime
from typing import Optional, Annotated
from pydantic import BaseModel, Field, ConfigDict
from pydantic.functional_validators import BeforeValidator


PyObjectId = Annotated[str, BeforeValidator(str)]


class UploadSchema(BaseModel):
    id: Optional[PyObjectId] = Field(alias="_id", default=None)
    filename: str = Field(...)
    current: int = Field(default=0)
    size: float = Field(...)
    percentage: float = Field(default=0.0)
    status: str = Field(default="pending")
    exception: Optional[str] = None
    s3_url: Optional[str] = None
    s3_key: Optional[str] = None
    created_at: datetime = datetime.now()
    updated_at: datetime = datetime.now()
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )


class UpdateUploadSchema(BaseModel):
    current: int
    percentage: float
    updated_at: datetime


class UploadResponse(BaseModel):
    message: str = Field(...)
    original_filename: str = Field(...)
    s3_key: str = Field(...)
    s3_url: str = Field(...)
    size: int = Field(default=0)


class S3UploadResponse(BaseModel):
    s3_url: str = Field()
    s3_key: str = Field()
