import logging
from fastapi import APIRouter, Depends, Response, status, HTTPException, File, UploadFile

from backend.auth import jwt, service, utils
from backend.auth.dependencies import valid_user_create
from backend.auth.schemas import AccessTokenResponse, AuthUser, UserResponse

router = APIRouter()

logger = logging.getLogger(__name__)


@router.post("/users", status_code=status.HTTP_201_CREATED, response_model=UserResponse)
async def register_user(
    auth_data: AuthUser = Depends(valid_user_create),
) -> UserResponse:
    try:
        user = await service.create_user(auth_data)
        logger.info(
            f"User created with ID: {user['_id']}, Email: {user['email']}")
        return UserResponse(email=user["email"])
    except Exception as e:
        logger.error(
            f"Error creating user with username {auth_data.name}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Error creating user: {str(e)}"
        )


@router.post("/users/tokens", response_model=AccessTokenResponse)
async def auth_user(
    auth_data: AuthUser,
    response: Response,
) -> AccessTokenResponse:
    user = await service.authenticate_user(auth_data)
    refresh_token_value = await service.create_refresh_token(user_id=user["_id"])

    response.set_cookie(**utils.get_refresh_token_settings(refresh_token_value))

    return AccessTokenResponse(
        access_token=jwt.create_access_token(user=user),
        refresh_token=refresh_token_value,
    )
