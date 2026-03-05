import os
from pathlib import Path
from fastapi import UploadFile, HTTPException


MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 50 * 1024 * 1024))  # 50MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".pdf", ".doc", ".docx"}


class FileValidator:
    def __init__(
        self,
        max_size: int = MAX_FILE_SIZE,
        allowed_extensions: set = ALLOWED_EXTENSIONS,
    ):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions

    async def __call__(self, file: UploadFile) -> UploadFile:
        ext = Path(file.filename).suffix.lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(status_code=400, detail=f"Extension {ext} not allowed")

        content = await file.read()
        if len(content) > self.max_size:
            raise HTTPException(
                status_code=400,
                detail=f"File exceeds max size of {self.max_size} bytes",
            )

        # reset file position
        await file.seek(0)

        return file
