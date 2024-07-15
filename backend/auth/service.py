import io  # type: ignore
import logging
import pdfplumber

from bson import ObjectId
from datetime import datetime  # type: ignore
from typing import Optional, Dict, Any  # type: ignore

from fastapi import UploadFile, HTTPException

from backend.db import get_db
from backend.auth import utils
from backend.config import settings
from backend.auth.schemas import AuthUser
from backend.auth.exceptions import InvalidCredentials
from backend.auth.security import hash_password, check_password

# Initialize the database connection and logger
db = get_db(settings.PROJECT_NAME)
logger = logging.getLogger(__name__)


async def create_user(user_data: AuthUser) -> Dict[str, Any]:
    try:
        hashed_password = hash_password(user_data.password)
        created_user = {
            "name": user_data.name,
            "email": user_data.email.lower(),
            "password": hashed_password,
            "pdf_data": ""
        }
        result = await db["users"].insert_one(created_user)
        created_user["_id"] = result.inserted_id
        return created_user
    except Exception as e:
        logger.error(f"Error creating user: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal Server Error") from e


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    if not ObjectId.is_valid(user_id):
        return None
    return await db["users"].find_one({"_id": ObjectId(user_id)})


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    return await db["users"].find_one({"email": email.lower()})


async def create_refresh_token(user_id: str, refresh_token: Optional[str] = None) -> str:
    if not refresh_token:
        refresh_token = utils.generate_random_alphanum(64)

    new_refresh_token = {
        "refresh_token": refresh_token,
        "expires_at": utils.calculate_refresh_token_expiry(),
        "user_id": user_id,
    }
    await db["refresh_tokens"].insert_one(new_refresh_token)
    return refresh_token


async def get_refresh_token(refresh_token: str) -> Optional[Dict[str, Any]]:
    return await db["refresh_tokens"].find_one({"refresh_token": refresh_token})


async def expire_refresh_token(refresh_token_uuid: str) -> None:
    if not ObjectId.is_valid(refresh_token_uuid):
        raise ValueError("Invalid refresh_token_uuid")

    await db["refresh_tokens"].update_one(
        {"_id": ObjectId(refresh_token_uuid)},
        {"$set": {"expires_at": datetime.now()}}
    )


async def authenticate_user(auth_data: AuthUser) -> Dict[str, Any]:
    try:
        user = await get_user_by_email(auth_data.email.lower())
        if not user or not check_password(auth_data.password, user["password"]):
            logger.warning(f"Invalid credentials for user: {auth_data.email}")
            raise InvalidCredentials()
        logger.info(f"User authenticated: {auth_data.email}")
        return user
    except InvalidCredentials as e:
        raise e
    except Exception as e:
        logger.error(f"Error authenticating user: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal Server Error") from e


async def upload_file(file: UploadFile) -> Optional[list]:
    try:
        content = await file.read()
        buf = io.BytesIO(content)

        with pdfplumber.open(buf) as pdf:
            number_of_pages = len(pdf.pages)
            logger.info(f"Number of pages in uploaded PDF: {number_of_pages}")
            pages_content = []

            for page_number in range(number_of_pages):
                page = pdf.pages[page_number]
                text = page.extract_text()
                logger.info(f"Extracted text from page {page_number}: {text}")
                pages_content.append(text)

        return pages_content
    except Exception as e:
        logger.error(f"Error uploading file: {e}")
        raise HTTPException(
            status_code=500, detail="An error occurred while uploading the file.") from e
