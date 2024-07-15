import logging

from typing import Any, Dict  # type: ignore
from fastapi import Depends, APIRouter, UploadFile

from backend.auth import dependencies as auth_deps
from backend.data.services import upload_file
router = APIRouter()
logger = logging.getLogger(__name__)
# Create Routes for data here


@router.post("/upload-pdf")
async def _upload_file(
    file: UploadFile,
    user_id: Dict[str, Any] = Depends(auth_deps.valid_refresh_token)
):
    logger.info(
        f"User {user_id['user_id']} uploading file {file.filename}")
    return await upload_file(file, user_id["user_id"])
