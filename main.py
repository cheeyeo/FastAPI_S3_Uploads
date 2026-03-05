import shutil
from pathlib import Path
import logging
from functools import lru_cache, partial
import uuid
import threading
import json
import asyncio
from contextlib import asynccontextmanager
from fastapi import (
    FastAPI,
    UploadFile,
    HTTPException,
    WebSocket,
    WebSocketDisconnect,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from bson import ObjectId
from config.config import Settings
from server.database import nonasync_uploads, async_uploads
from server.models import UploadSchema, UpdateUploadSchema, UploadResponse
from server.validator import FileValidator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CLIENTS = set()


async def broadcast(data):
    text = json.dumps(data, default=str)
    for client in CLIENTS.copy():
        try:
            await client.send_text(text)
        except Exception:
            CLIENTS.remove(client)


async def watch_uploads_changes():
    pipeline = [
        {
            "$match": {
                "operationType": {"$in": ["insert", "update", "replace", "delete"]}
            }
        }
    ]
    async with await async_uploads.watch(
        pipeline, full_document="updateLookup", full_document_before_change="required"
    ) as stream:
        async for change in stream:
            doc_id = change["documentKey"]["_id"]
            before = change.get("fullDocumentBeforeChange", {})
            after = change.get("fullDocument", {})

            # logger.info(f"BEFORE: {before} AFTER: {after}")

            await broadcast(
                {
                    "event": change["operationType"],
                    "document_id": str(doc_id),
                    "before": before,
                    "after": after,
                }
            )


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(watch_uploads_changes())
    yield
    task.cancel()


app = FastAPI(
    title="File uploads example",
    description="Example of file uploads in FastAPI",
    version="1.0.0",
    lifespan=lifespan,
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
# MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
ALLOWED_CONTENT_TYPES = {"application/x-executable", "application/octet-stream"}
UPLOAD_DIR = Path(get_settings().upload_dir)
S3_REGION = get_settings().s3_region
S3_PROFILE = get_settings().s3_profile
S3_BUCKET = get_settings().s3_bucket
SESSION = boto3.Session(region_name=S3_REGION, profile_name=S3_PROFILE)
S3_CLIENT = SESSION.client("s3")


def generate_safe_filename(original: str) -> str:
    unique_prefix = str(uuid.uuid4())[:8]
    return f"{unique_prefix}_{original}"


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    CLIENTS.add(websocket)

    await websocket.accept()

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WS connection closed")
        CLIENTS.remove(websocket)


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
    def __init__(self, file: UploadFile, id: str):
        self._filename = file.filename
        self._size = float(file.size)
        self._seen_so_far = 0
        self._lock = threading.Lock()
        self._id = id

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100

            # Below uses non-async mongo client as the callback is non async
            nonasync_uploads.update_one(
                {"_id": ObjectId(self._id)},
                {
                    "$set": UpdateUploadSchema(
                        current=self._seen_so_far, percentage=percentage
                    ).model_dump(exclude_unset=True)
                },
            )


def s3_upload(file: UploadFile, upload_id: str) -> UploadResponse:
    filename = generate_safe_filename(file.filename)

    try:
        config = TransferConfig(
            multipart_chunksize=CHUNK_SIZE,
            multipart_threshold=5 * GB,
        )

        S3_CLIENT.upload_fileobj(
            Fileobj=file.file,
            Bucket=S3_BUCKET,
            Key=filename,
            ExtraArgs={"ContentType": file.content_type},
            Config=config,
            Callback=ProgressPercentage(file, upload_id),
        )
    except ClientError as e:
        raise e

    # Generate presigned url that's valid for an hour
    file_url = S3_CLIENT.generate_presigned_url(
        "get_object", Params={"Bucket": S3_BUCKET, "Key": filename}, ExpiresIn=3600
    )

    return UploadResponse(
        message="File uploaded to S3",
        original_filename=file.filename,
        s3_key=file.filename,
        s3_url=file_url,
        size=file.size,
    )


validate_file = FileValidator(
    max_size=5 * GB,
    allowed_extensions={".appimage", ".file"},
    allowed_content_types=ALLOWED_CONTENT_TYPES,
)


@app.post("/upload/s3", response_model=UploadResponse)
async def upload_s3_streaming(file: UploadFile = Depends(validate_file)):
    # uses the boto3 built-in multipart uploads
    # https://docs.aws.amazon.com/boto3/latest/guide/s3.html

    # Add initial record to db
    result = await async_uploads.insert_one(
        UploadSchema(filename=file.filename, size=float(file.size)).model_dump()
    )
    upload_id = str(result.inserted_id)

    loop = asyncio.get_running_loop()

    upload_partial = partial(s3_upload, file=file, upload_id=upload_id)

    try:
        upload_resp = await loop.run_in_executor(None, upload_partial)
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 Upload failed: {e}")

    return upload_resp
