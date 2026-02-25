from typing import Any
import shutil
from pathlib import Path
import logging
from functools import lru_cache
from config.config import Settings
from fastapi import FastAPI, UploadFile, HTTPException
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
import aiofiles


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="File uploads example",
    description="Example of file uploads in FastAPI",
    version="1.0.0"
)


@lru_cache
def get_settings():
    return Settings()

CHUNK_SIZE = 1024 * 1024  # 1 MB
GB = 1024 ** 3
MAX_FILE_SIZE = 50 * CHUNK_SIZE
UPLOAD_DIR = Path(get_settings().upload_dir)
S3_REGION = get_settings().s3_region
S3_PROFILE = get_settings().s3_profile
S3_BUCKET = get_settings().s3_bucket
SESSION = boto3.Session(region_name=S3_REGION, profile_name=S3_PROFILE)
S3_CLIENT = SESSION.client('s3')


@app.post("/upload/local")
async def upload_local_file(file: UploadFile):
    if file.filename == "":
        raise HTTPException(status_code=400, detail="No file found")
    
    file_path = Path(UPLOAD_DIR, file.filename)

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file.size,
        "location": file_path
    }


@app.post("/upload/s3")
async def upload_s3_streaming(file: UploadFile):
    # uses the boto3 built-in multipart uploads
    # https://docs.aws.amazon.com/boto3/latest/guide/s3.html

    try:
        config = TransferConfig(
            multipart_chunksize=CHUNK_SIZE,
            multipart_threshold=5*GB,
        )

        # ADD CALLBACK TO TRACK PROGRESS
        S3_CLIENT.upload_fileobj(
            file.file,
            S3_BUCKET,
            file.filename,
            ExtraArgs={
                "ContentType": file.content_type
            },
            Config=config
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 Upload failed: {e}")
    
    return {
        "message": "File uploaded to S3",
        "original_filename": file.filename,
        "s3_key": file.filename,
        "s3_url": f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{file.filename}",
        "size": file.size
    }