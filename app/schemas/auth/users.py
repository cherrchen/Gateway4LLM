from typing import Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, EmailStr, ConfigDict, model_validator

class UserCreate(BaseModel):
    username: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    password: str = Field(min_length=6, max_length=32)

    @model_validator(mode="after")
    def validate_username(self):
        if self.username is None and self.email is None:
            raise ValueError("Username or email must be provided")
        return self

class UserUpdate(BaseModel):
    """
    unset
    """
    username: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate(self):
        if self.username is None and self.email is None and self.password is None and self.is_active is None:
            raise ValueError("Username, email, password or is_active must be provided")
        return self

class UserResponse(BaseModel):
    id: UUID
    username: str | None = None
    email: str | None = None
    is_active: bool

    created_at: datetime
    updated_at: datetime | None

    model_config = ConfigDict(from_attributes=True)

class UserToken(BaseModel):
    access_token: str
    token_type: Literal["Bearer", "JWT"] | None = "Bearer"