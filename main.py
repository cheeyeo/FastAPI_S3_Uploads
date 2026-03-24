import shutil
from datetime import datetime
from pathlib import Path
import logging
from functools import partial
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
    BackgroundTasks,
    Body,
    Response,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
import boto3
from boto3.s3.transfer import TransferConfig
from botocore.exceptions import ClientError
from bson import ObjectId
from server.config import get_settings
from server.database import (
    nonasync_uploads,
    async_uploads,
    nonasync_client,
    async_client,
)
from server.models import (
    UploadSchema,
    UpdateUploadSchema,
    UploadResponse,
    S3UploadResponse,
    UpdateUpload,
    PresignedUpload,
)
from server.validator import FileValidator


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


CLIENTS = set()
CHUNK_SIZE = 1024 * 1024  # 1 MB
GB = 1024**3
MAX_FILE_SIZE = 50 * CHUNK_SIZE
# MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "application/x-executable",
    "application/octet-stream",
}
UPLOAD_DIR = Path(get_settings().upload_dir)
S3_REGION = get_settings().s3_region
S3_PROFILE = get_settings().s3_profile
S3_BUCKET = get_settings().s3_bucket
SESSION = boto3.Session(region_name=S3_REGION, profile_name=S3_PROFILE)
S3_CLIENT = SESSION.client("s3")


validate_file = FileValidator(
    max_size=5 * GB,
    allowed_extensions={".jpg", ".jpeg", ".png", ".gif", ".appimage", ".file", ".jpg"},
    allowed_content_types=ALLOWED_CONTENT_TYPES,
)


def generate_safe_filename(original: str) -> str:
    unique_prefix = str(uuid.uuid4())[:8]
    return f"{unique_prefix}_{original}"


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
    # call watch on the uploads collection; async_uploads ref the uploads collection
    async with await async_uploads.watch(
        pipeline, full_document="updateLookup", full_document_before_change="required"
    ) as stream:
        async for change in stream:
            doc_id = change["documentKey"]["_id"]
            before = change.get("fullDocumentBeforeChange", {})
            after = change.get("fullDocument", {})

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
    # close db clients on app exit
    nonasync_client.close()
    await async_client.close()


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


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    CLIENTS.add(websocket)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        # logger.info(f"WS ERROR: {e}")
        # logger.info("WS connection closed")
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
                        current=self._seen_so_far,
                        percentage=percentage,
                        status="in progress",
                        updated_at=datetime.now(),
                    ).model_dump(exclude_unset=True)
                },
            )


def s3_upload(
    file: UploadFile, upload_id: str, background: bool = False
) -> S3UploadResponse:
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

        file_url = S3_CLIENT.generate_presigned_url(
            "get_object", Params={"Bucket": S3_BUCKET, "Key": filename}, ExpiresIn=3600
        )

        # Update record with s3 url
        nonasync_uploads.update_one(
            {"_id": ObjectId(upload_id)},
            {
                "$set": {
                    "status": "completed",
                    "s3_url": file_url,
                    "s3_key": filename,
                    "updated_at": datetime.now(),
                }
            },
        )

        return S3UploadResponse(s3_url=file_url, s3_key=filename)
    except ClientError as e:
        if background:
            nonasync_uploads.update_one(
                {"_id": ObjectId(upload_id)},
                {
                    "$set": {
                        "status": "error",
                        "exception": str(e),
                        "updated_at": datetime.now(),
                    }
                },
            )
        else:
            raise e


@app.post("/upload/s3", response_model=UploadResponse)
async def upload_s3(file: UploadFile = Depends(validate_file)):
    # uses the boto3 built-in multipart uploads
    # https://docs.aws.amazon.com/boto3/latest/guide/s3.html

    # Add initial record to db
    result = await async_uploads.insert_one(
        UploadSchema(
            filename=file.filename,
            size=float(file.size),
            content_type=file.content_type,
        ).model_dump()
    )
    upload_id = str(result.inserted_id)

    upload_partial = partial(
        s3_upload, file=file, upload_id=upload_id, background=False
    )

    try:
        s3_upload_resp = await asyncio.to_thread(upload_partial)
        upload_resp = UploadResponse(
            message="File uploaded to S3",
            original_filename=file.filename,
            s3_key=s3_upload_resp.s3_key,
            s3_url=s3_upload_resp.s3_url,
            size=file.size,
        )
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"S3 Upload failed: {e}")

    return upload_resp


@app.post("/upload/background", response_model=UploadSchema)
async def upload_s3_background(
    background_tasks: BackgroundTasks, file: UploadFile = Depends(validate_file)
):
    # Add initial record to db
    result = await async_uploads.insert_one(
        UploadSchema(
            filename=file.filename,
            size=float(file.size),
            content_type=file.content_type,
        ).model_dump()
    )

    upload_id = str(result.inserted_id)
    upload_partial = partial(s3_upload, file=file, upload_id=upload_id, background=True)

    #  Add task to background
    background_tasks.add_task(upload_partial)

    new_upload = await async_uploads.find_one({"_id": result.inserted_id})

    return new_upload


@app.post("/upload/presigned-url", response_model=PresignedUpload)
async def get_presigned_url(file: UploadFile = Depends(validate_file)):
    """
    Generates presigned url for large file uploads to S3

    * Get presigned url
    * PUT file directly to presigned url. Need to include content_type as Header else upload will fail
    * Notify server upload is complete via /upload/:id PUT
    """

    s3_filename = generate_safe_filename(file.filename)

    # Add initial record to db
    resp = await async_uploads.insert_one(
        UploadSchema(
            filename=file.filename,
            s3_key=s3_filename,
            size=float(file.size),
            content_type=file.content_type,
        ).model_dump()
    )

    try:
        url = S3_CLIENT.generate_presigned_url(
            ClientMethod="put_object",
            Params={
                "Bucket": S3_BUCKET,
                "Key": s3_filename,
                "ContentType": file.content_type,  # Specify content type
            },
            ExpiresIn=3600,
        )

        return {
            "id": str(resp.inserted_id),
            "url": url,
            "content_type": file.content_type,
        }
    except ClientError as e:
        logger.error(e, exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to generate presigned URL: {e}"
        )


@app.get("/upload/{id}", response_model=UploadSchema)
async def get_upload(id: str):
    upload = await async_uploads.find_one({"_id": ObjectId(id)})

    if upload is None:
        raise HTTPException(status_code=400, detail=f"Upload with id {id} not found")

    return upload


@app.patch("/upload/{id}", response_model=UploadSchema)
async def update_upload(id: str, upload: UpdateUpload = Body(...)):
    record = await async_uploads.find_one({"_id": ObjectId(id)})
    if record is None:
        raise HTTPException(status_code=400, detail=f"Upload with id {id} not found")

    upload_items = {k: v for k, v in upload.model_dump().items() if v is not None}
    upload_items["updated_at"] = datetime.now()

    update_result = await async_uploads.update_one(
        {"_id": ObjectId(id)},
        {"$set": upload_items},
    )

    if update_result.modified_count == 0:
        raise HTTPException(status_code=400, detail=f"Upload with id {id} not updated.")

    existing_upload = await async_uploads.find_one({"_id": ObjectId(id)})
    if existing_upload is None:
        raise HTTPException(status_code=400, detail=f"Upload with id {id} not found")

    return existing_upload


@app.delete("/upload/{id}")
async def delete_upload(id: str, response: Response):
    upload_doc = await async_uploads.find_one({"_id": ObjectId(id)})
    if upload_doc is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, details=f"Upload {id} not found"
        )

    try:
        S3_CLIENT.delete_object(Bucket=S3_BUCKET, Key=upload_doc["s3_key"])
    except ClientError as e:
        logger.error(e, exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete upload: {e}")

    deleted_result = await async_uploads.delete_one({"_id": ObjectId(id)})
    if deleted_result is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Upload${id} not found"
        )

    if deleted_result.deleted_count == 1:
        response.status_code = status.HTTP_204_NO_CONTENT
        return response
