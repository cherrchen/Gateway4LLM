from uuid import UUID
from pydantic import BaseModel, ConfigDict, model_validator

class UserCreate(BaseModel):
    username: str | None = None
    email: str | None = None
    password: str

    @model_validator(mode="after")
    def validate_username(self, v):
        if self.username is None and self.email is None:
            raise ValueError("Username or email must be provided")

class UserUpdate(BaseModel):
    """
    unset
    """
    username: str | None = None
    email: str | None = None
    password: str | None = None
    is_active: bool | None = None

    @model_validator(mode="after")
    def validate(self, v):
        pass

class UserResponse(BaseModel):
    id: UUID
    username: str | None = None
    email: str | None = None
    is_active: bool | None = None

    model_config = ConfigDict(from_attributes=True)

class UserToken(BaseModel):
    access_token: str
    token_type: str