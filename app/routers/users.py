from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from models.user import User
from schemas.user import UserCreate, UserRead, UserBase, UserUpdate
from crud.user import get_current_user, create_user, get_all_users, get_user_by_username, update_user, delete_user
from secure.security_user import verify_password, create_access_token, decode_access_token
from crud.project import get_user_projects
from schemas.project import ProjectLabelInDB
from core.database import get_db
import json
import uuid
from crud.role import get_role_code_by_id

from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

@router.post("/signup_adm", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def user_signup_adm(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

@router.post("/signup", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def user_signup(user: UserCreate, db: Session = Depends(get_db)):
    if get_user_by_username(db, username=user.username):
        raise HTTPException(status_code=400, detail="Username already registered")
    return create_user(db=db, user=user)

@router.post("/login", response_model=dict)
def user_login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = get_user_by_username(db, username=form_data.username)
    if not user or not verify_password(form_data.password, user.password):
        raise HTTPException(status_code=400, detail="Invalid username or password")
    access_token = create_access_token(data={"user_id": str(user.id), "role_code": user.role_code})
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/users", response_model=List[UserBase])
async def read_users(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decoded_token = decode_access_token(token)
        role_code = decoded_token.get('role_code')
        if role_code not in ['super-admin', 'admin']:
            return "Unauthorized"   
        return get_all_users(db)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/user/me", response_model=UserBase)
async def read_user_me(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decoded_token = decode_access_token(token)
        user_id = decoded_token.get('user_id')
        user = get_current_user(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return UserBase.from_orm(user)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/user/{user_id}", response_model=UserBase)
def update_user_info(user_id: str, user: UserUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    decoded_token = decode_access_token(token)
    # Extract role_code from decoded token
    role_code = decoded_token.get('role_code')

    # Allow all roles to update user information
    updated_user = update_user(db, user_id, user)

    if not updated_user:
        raise HTTPException(status_code=404, detail="User not found")

    return updated_user

@router.delete("/user/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user_account(user_id: str, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    decoded_token = decode_access_token(token)
    role_code = decoded_token.get('role_code')
    
    # Lấy thông tin user cần xóa
    user_to_delete = get_current_user(db, user_id)
    if not user_to_delete:
        raise HTTPException(status_code=404, detail="User not found")
    
    if role_code == 'super-admin':
        # Super-admin có thể xóa tất cả các loại user
        if not delete_user(db, user_id):
            raise HTTPException(status_code=404, detail="User not found")
    elif role_code == 'admin':
        # Admin chỉ có thể xóa admin và user, không thể xóa super-admin
        if user_to_delete.role_code == 'super-admin':
            raise HTTPException(status_code=403, detail="Admin cannot delete super-admin accounts")
        elif user_to_delete.role_code in ['admin', 'user']:
            if not delete_user(db, user_id):
                raise HTTPException(status_code=404, detail="User not found")
        else:
            raise HTTPException(status_code=403, detail="Admin can only delete admin and user accounts")
    else:
        # Các role khác không có quyền xóa
        raise HTTPException(status_code=403, detail="You don't have permission to delete users")

    return {"message": "User deleted successfully"}
@router.get("/user/{user_id}/projects", response_model=List[ProjectLabelInDB])
async def read_user_projects(
    user_id: uuid.UUID, 
    token: str = Depends(oauth2_scheme), 
    db: Session = Depends(get_db)
):
    try:
        decoded_token = decode_access_token(token)
        current_user_id = decoded_token.get('user_id')
        current_user_role = decoded_token.get('role_code')

        # Kiểm tra quyền truy cập
        if str(current_user_id) != str(user_id) and current_user_role not in ['super-admin', 'admin']:
            raise HTTPException(status_code=403, detail="Not authorized to view these projects")

        user_projects = get_user_projects(db, user_id)
        if not user_projects:
            return []

        return user_projects
    except Exception as e:
         raise HTTPException(status_code=400, detail=str(e))