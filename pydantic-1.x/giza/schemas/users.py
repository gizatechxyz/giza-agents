from typing import Optional

from pydantic import BaseModel, EmailStr, SecretStr, validator


class UserBase(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None


class UserCreate(UserBase):
    username: str
    email: EmailStr
    password: SecretStr

    @validator("username", "email", "password")
    def str_not_emtpy(cls, s: str):
        """
        Validate that none of the provided information is an empty string

        Args:
            s (str): value to check if `""`

        Raises:
            ValueError: If the value is an empty string

        Returns:
            str: return the provided value if not empty
        """
        if s == "":
            raise ValueError
        return s


class UserLogin(BaseModel):
    username: str
    password: SecretStr


class UserResponse(UserBase):
    username: str
    email: EmailStr
    is_active: bool


class UserCreateApiKeys(BaseModel):
    id: SecretStr
