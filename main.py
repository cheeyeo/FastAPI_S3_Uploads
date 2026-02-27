import shutil
from pathlib import Path
import logging
from functools import lru_cache
import uuid
import threading
import sys
from config.config import Settings
from fastapi import FastAPI, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI(
    title="File uploads example",
    description="Example of file uploads in FastAPI",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@lru_cache
def get_settings():
    return Settings()


CHUNK_SIZE = 1024 * 1024  # 1 MB
GB = 1024**3
MAX_FILE_SIZE = 50 * CHUNK_SIZE
UPLOAD_DIR = Path(get_settings().upload_dir)
S3_REGION = get_settings().s3_region
S3_PROFILE = get_settings().s3_profile
S3_BUCKET = get_settings().s3_bucket
SESSION = boto3.Session(region_name=S3_REGION, profile_name=S3_PROFILE)
S3_CLIENT = SESSION.client("s3")
# Magic number signatures for common file types
MAGIC_NUMBERS = {
    "image/jpeg": [b"\xff\xd8\xff"],
    "image/png": [b"\x89PNG\r\n\x1a\n"],
    "image/gif": [b"GIF87a", b"GIF89a"],
    "application/pdf": [b"%PDF"],
}


async def validate_magic_number(file: UploadFile, expected_type: str) -> bool:
    """
    Verify file content matches expected type using magic numbers.
    More secure than relying on Content-Type header alone.
    """

    header = await file.read(8)
    await file.seek(0)

    signatures = MAGIC_NUMBERS.get(expected_type, [])

    for sig in signatures:
        if header.startswith(sig):
            return True

    return False


def generate_safe_filename(original: str) -> str:
    unique_prefix = str(uuid.uuid4())[:8]
    return f"{unique_prefix}_{original}"


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
        "location": file_path,
    }


class ProgressPercentage:
    def __init__(self, file: UploadFile):
        self._filename = file.filename
        self._size = float(file.size)
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r%s  %s / %s  (%.2f%%)"
                % (self._filename, self._seen_so_far, self._size, percentage)
            )
            sys.stdout.flush()


@app.post("/upload/s3")
async def upload_s3_streaming(file: UploadFile):
    # uses the boto3 built-in multipart uploads
    # https://docs.aws.amazon.com/boto3/latest/guide/s3.html

    # TODO: Redo validator below as dedicated object
    # res = await validate_magic_number(file, file.content_type)
    # if not res:
    #     raise HTTPException(status_code=500, detail="File validation failed")

    filename = generate_safe_filename(file.filename)

    try:
        config = TransferConfig(
            multipart_chunksize=CHUNK_SIZE,
            multipart_threshold=5 * GB,
        )

        # ADD CALLBACK TO TRACK PROGRESS
        S3_CLIENT.upload_fileobj(
            file.file,
            S3_BUCKET,
            filename,
            ExtraArgs={"ContentType": file.content_type},
            Config=config,
            Callback=ProgressPercentage(file),
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 Upload failed: {e}")

    file_url = S3_CLIENT.generate_presigned_url(
        "get_object", Params={"Bucket": S3_BUCKET, "Key": filename}, ExpiresIn=3600
    )

    return {
        "message": "File uploaded to S3",
        "original_filename": file.filename,
        "s3_key": file.filename,
        "s3_url": file_url,
        "size": file.size,
    }
