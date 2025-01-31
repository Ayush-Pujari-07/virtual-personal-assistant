import re  # type: ignore
from bson import ObjectId
from datetime import datetime  # type: ignore
from typing_extensions import Annotated  # type: ignore
from pydantic import EmailStr, Field, field_validator, BaseModel, AfterValidator
from fastapi import UploadFile

# Updated regex to include at least one uppercase letter
STRONG_PASSWORD_PATTERN = re.compile(
    r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[\d])(?=.*[!@#$%^&*])[\w!@#$%^&*]{6,128}$"
)


class AuthUser(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=128)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)

    @field_validator("password", mode="after")
    @classmethod
    def valid_password(cls, password: str) -> str:
        if not re.match(STRONG_PASSWORD_PATTERN, password):
            raise ValueError(
                "Password must contain at least one lowercase letter, one uppercase letter, one digit, and one special symbol"
            )
        return password


class JWTData(BaseModel):
    user_id: str = Field(alias="sub")
    is_admin: bool = False


class AccessTokenResponse(BaseModel):
    access_token: str
    refresh_token: str


class UserResponse(BaseModel):
    email: EmailStr


Password = Annotated[str, AfterValidator(AuthUser.valid_password)]


class UserCreate(BaseModel):
    email: EmailStr
    password: Password


class RefreshToken(BaseModel):
    refresh_token: str
    exp: datetime


class AuthRefreshToken(BaseModel):
    _id: str
    refresh_token: str
    user_id: str
