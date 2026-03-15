from pathlib import Path
from typing import Set
from fastapi import UploadFile, HTTPException
import magic


class FileValidator:
    def __init__(
        self,
        max_size: int,
        allowed_extensions: Set[str] = None,
        allowed_content_types: Set[str] = None,
    ):
        self.max_size = max_size
        self.allowed_extensions = allowed_extensions
        self.allowed_content_types = allowed_content_types

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

        # validate content type
        # read first 2048 bytes from file header
        header = await file.read(2048)
        await file.seek(0)

        detected_type = magic.from_buffer(header, mime=True)

        if detected_type not in self.allowed_content_types:
            raise HTTPException(
                status_code=400,
                detail=f"Content type {detected_type} not allowed. Allowed content types: {self.allowed_content_types}",
            )

        return file
