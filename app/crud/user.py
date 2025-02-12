#crud/user.py
from sqlalchemy.orm import Session
from sqlalchemy import desc

from models.user import User
from schemas.user import UserCreate, UserFilter, UserUpdate
from secure.security_user import get_password_hash, decode_access_token
import uuid


def get_current_user(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session):
    return db.query(User).all()

def get_user_by_username(db: Session, username: str):
    return db.query(User).filter(User.username == username).first()

def get_users_by_filter_createdBy(db: Session, user_id: str, filter: UserFilter = None, pages: int = 1, numbers: int = 100):
    list_user_id = get_all_descendants(db, user_id)
    query = db.query(User).filter(User.id.in_(list_user_id))

    if filter:
        if filter.id:
            query = query.filter(User.id == filter.id)
        if filter.name:
            query = query.filter(User.name == filter.name)
        if filter.email:
            query = query.filter(User.email == filter.email)
        if filter.username:
            query = query.filter(User.username == filter.username)
        if filter.status is not None:
            query = query.filter(User.status == filter.status)
        if filter.role_code:
            query = query.filter(User.role_code == filter.role_code)
        if filter.createdBy:
            query = query.filter(User.createdBy == filter.createdBy)

    total = query.count()
    max_pages = -(-total // numbers)
    results = query.order_by(desc(User.createdAt)).offset((pages - 1) * numbers).limit(numbers).all()

    return {"total": total, "max_pages": max_pages, "results": results}

def create_user(db: Session, user: UserCreate):
    db_user = User(
        username=user.username,
        email=user.email,
        name=user.name,
        status=user.status,
        role_code=user.role_code,
        createdBy=user.createdBy,
        password=get_password_hash(user.password),
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: str, user: UserUpdate):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db_user.name = user.name
        db_user.email = user.email
        db_user.status = user.status
        db_user.role_code = user.role_code
        db_user.modifiedBy = user.modifiedBy
        if user.password:
            db_user.password = get_password_hash(user.password)
        db.commit()
        db.refresh(db_user)
        return db_user
    return None

def delete_user(db: Session, user_id: str):
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user:
        db.delete(db_user)
        db.commit()
        return True
    return False

def get_users_by_filter(db: Session, filter: UserFilter, pages: int = 1, numbers: int = 100):
    query = db.query(User)
    if filter:
        if filter.id:
            query = query.filter(User.id == filter.id)
        if filter.name:
            query = query.filter(User.name == filter.name)
        if filter.email:
            query = query.filter(User.email == filter.email)
        if filter.username:
            query = query.filter(User.username == filter.username)
        if filter.status is not None:
            query = query.filter(User.status == filter.status)
        if filter.role_code:
            query = query.filter(User.role_code == filter.role_code)
        if filter.createdBy:
            query = query.filter(User.createdBy == filter.createdBy)

    total = query.count()
    max_pages = -(-total // numbers)
    results = query.order_by(desc(User.createdAt)).offset((pages - 1) * numbers).limit(numbers).all()

    return {"total": total, "max_pages": max_pages, "results": results}

def get_all_descendants(db: Session, user_id: str):
    user_ids = [user_id]
    descendants = db.query(User).filter(User.createdBy == user_id).all()
    for desc in descendants:
        user_ids.extend(get_all_descendants(db, desc.id))
    return user_ids

def get_user_projects(db: Session, user_id: uuid.UUID):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return None
    return user.own_projects