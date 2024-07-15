# add course data to course
import io  # type: ignore
import logging
import pdfplumber

from bson.objectid import ObjectId
from fastapi import HTTPException, UploadFile

from backend.db import get_db
from backend.config import settings


logger = logging.getLogger(__name__)

# Create services for data here


async def upload_file(file: UploadFile, user_id: int):
    try:
        logger.info(
            f"User {user_id} uploading file {file.filename}")
        content = await file.read()
        buf = io.BytesIO(content)
        # Use context manager to ensure the PDF is properly closed
        with pdfplumber.open(buf) as data:
            logger.info(f"Number of pages: {len(data.pages)}")
            number_of_pages = len(data.pages)
            pages_content = []

            for page_number in range(number_of_pages):
                page = data.pages[page_number]
                text = page.extract_text()
                logger.info(f"Page {page_number} text: {text}")
                pages_content.append(text)

        # TODO: Vector DB
        
        db = get_db(settings.PROJECT_NAME)
        result = await db.users.update_one(
            {"_id": ObjectId(user_id)},
            {"$set": {"pdf_data": " ".join(pages_content)}}
        )

        # Check the result of the update operation
        if result.modified_count == 0:
            logger.error("No document was updated. Check the query criteria.")
            raise HTTPException(
                status_code=404,
                detail="No document found to update."
            )

        logger.info(f"User {user_id} uploaded file {file.filename}")
        return {"message": "File uploaded successfully"}

    except Exception as e:
        logger.error(f"Error uploading pdf file: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail="An error occurred while uploading the pdf file."
        ) from e
