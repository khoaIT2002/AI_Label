from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from jose import jwt
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from datetime import datetime, timedelta
from typing import Union
from models.user import User
from core.config import settings
from core.database import get_db
from schemas.user import UserRead, UserBase


# Password hashing and verification
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Token creation and decoding
def create_access_token(data: dict, expires_delta: int = 86400) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(seconds=expires_delta)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

def decode_access_token(token: str) -> Union[dict, None]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except jwt.ExpiredSignatureError:
        return None
    except jwt.JWTError:
        return None

# Define the role-based user class
class RoleChecker:
    def __init__(self, allowed_roles: list):
        self.allowed_roles = allowed_roles

    def __call__(self, current_user: UserRead):
        if current_user.role_code not in self.allowed_roles:
            raise HTTPException(status_code=403, detail="You do not have access to this resource")

def get_current_user(db: Session = Depends(get_db), token: str = Depends(oauth2_scheme)) ->UserBase:
    try:
        payload = decode_access_token(token)
        user = db.query(User).filter(User.id == payload["sub"]).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Invalid user")
        return user
    except Exception as e:
        raise HTTPException(status_code=401, detail="Invalid token")