from pydantic import BaseModel, EmailStr
from pydantic import Field, UUID4
from typing import Optional, List
from datetime import datetime
import uuid
class UserBase(BaseModel):
    id: Optional[UUID4]
    name: Optional[str]
    email: Optional[EmailStr]
    username: Optional[str]
    status: Optional[int]
    role_code: Optional[str]
    createdBy: Optional[str]
    createdAt: Optional[datetime]
    modifiedBy: Optional[str]

    class Config:
        from_attributes = True

class UserCreate(BaseModel):
    username: str
    password: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    status: Optional[int] = 1  # Default status to 1 (active)
    role_code: Optional[str] = None
    createdBy: Optional[str] = None
    createdAt: Optional[datetime]
    modifiedBy: Optional[str]

    class Config:
        from_attributes = True

class UserRead(UserBase):
    pass


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    status: Optional[int] = None
    role_code: Optional[str] = None
    modifiedBy: Optional[str]
    password: Optional[str] = None

class UserFilter(BaseModel):
    id: Optional[UUID4] = None
    name: Optional[str] = None
    email: Optional[str] = None
    username: Optional[str] = None
    status: Optional[int] = None
    role_code: Optional[str] = None
    createdBy: Optional[str] = None
    createdAt: Optional[datetime]
    modifiedBy: Optional[str]
    