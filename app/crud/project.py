#crud/project.py
from sqlalchemy.orm import Session
from fastapi import  HTTPException
from core.database import SessionLocal
from models.project import ProjectLabel, DataImages, BoundingBox
from schemas.project import ProjectLabelCreate, DataImageCreate, DataImageUpdate,BoundingBoxCreate, DataImageInDB
from typing import List, Dict,Optional
from models.user import User
import pandas as pd
import uuid
from PIL import Image
from ultralytics import YOLO
from PIL import Image as PILImage
import datetime
import io


def get_user_projects(db: Session, user_id: uuid.UUID):
    return db.query(ProjectLabel).filter(ProjectLabel.created_by == user_id).all()

def create_project_label(db: Session, project_label: ProjectLabelCreate, user_id: uuid.UUID):
    db_project_label = ProjectLabel(
        project_name=project_label.project_name,
        label_names=[label.dict() for label in project_label.label_names],
        created_by=user_id,
        arr_owner=[user_id]
    )
    db.add(db_project_label)
    db.commit()
    db.refresh(db_project_label)
    return db_project_label
def create_project(db: Session, project_name: str, created_by: uuid.UUID, label_names: list = None):
    new_project = ProjectLabel(
        project_name=project_name,
        created_by=created_by,
        label_names=label_names
    )
    db.add(new_project)
    db.commit()
    db.refresh(new_project)
    return new_project
def add_user_to_project(db: Session, project_uuid: uuid.UUID, user_id: uuid.UUID):
    project = db.query(ProjectLabel).filter(ProjectLabel.project_uuid == project_uuid).first()
    user = db.query(User).filter(User.id == user_id).first()
    if project and user:
        project.users.append(user)
        db.commit()
        return True
    return False
def get_project_users(db: Session, project_uuid: uuid.UUID):
    project = db.query(ProjectLabel).filter(ProjectLabel.project_uuid == project_uuid).first()
    if project:
        return project.users
    return []

def get_user_projects(db: Session, user_id: uuid.UUID):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        return user.projects
    return []
def remove_user_from_project(db: Session, project_uuid: uuid.UUID, user_id: uuid.UUID):
    project = db.query(ProjectLabel).filter(ProjectLabel.project_uuid == project_uuid).first()
    user = db.query(User).filter(User.id == user_id).first()
    if project and user:
        project.users.remove(user)
        db.commit()
        return True
    return False
def get_user_projects(db: Session, user_id: uuid.UUID):
    return db.query(ProjectLabel).filter(ProjectLabel.created_by == user_id).all()
def create_project(db: Session, project: ProjectLabelCreate, user_id: uuid.UUID):
    db_project = ProjectLabel(
        project_name=project.project_name,
        label_names=project.label_names,
        created_by=user_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project
def get_project_label(db: Session, project_uuid: uuid.UUID):
    return db.query(ProjectLabel).filter(ProjectLabel.project_uuid == project_uuid).first()

def get_all_project_labels(db: Session):
    return db.query(ProjectLabel).all()

def update_project_label(db: Session, project_uuid: uuid.UUID, project_label: ProjectLabelCreate):
    db_project_label = get_project_label(db, project_uuid)
    if db_project_label:
        if project_label.project_name is not None:
            db_project_label.project_name = project_label.project_name
        if project_label.label_names is not None:
            db_project_label.label_names = [label.to_dict() for label in project_label.label_names]  # Convert LabelItem to dict
        db.commit()
        db.refresh(db_project_label)
    return db_project_label

def delete_project_label(db: Session, project_uuid: uuid.UUID):
    db_project_label = get_project_label(db, project_uuid)
    if db_project_label:
        db.delete(db_project_label)
        db.commit()
    return db_project_label


def create_data_image(
    db: Session,
    image_uuid: uuid.UUID,
    image_name: str,
    image_data: bytes,
    project_uuid: uuid.UUID,
    label: dict = None,
    modify_by: uuid.UUID = None,
    image_url: str = None,
    flag_label: bool = False,
    image_width: int = None,
    image_height: int = None
) -> DataImages:
    image = Image.open(io.BytesIO(image_data))
    width, height = image.size

    db_image = DataImages(
        image_uuid=image_uuid,
        image_name=image_name,
        image_data=image_data,
        project_uuid=project_uuid,
        label=label,
        modify_by=modify_by,
        image_url=image_url,
        flag_label=flag_label,
        image_width=width,
        image_height=height
    )
    db.add(db_image)
    db.commit()
    db.refresh(db_image)
    return db_image
    

def get_image_path(image_uuid: str, db: Session) -> str:
    # Giả sử bạn có model DataImages để lưu trữ thông tin ảnh
    image_record = db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()
    if not image_record:
        raise HTTPException(status_code=404, detail="Image not found")

    return image_record.image_path  # Trả về đường dẫn của file ảnh

def get_all_project_images(db: Session, project_uuid: uuid.UUID):
    return db.query(DataImages).filter(DataImages.project_uuid == project_uuid).all()

def get_project_images(db: Session, project_uuid: uuid.UUID, skip: int = 0, limit: int = 10) -> List[DataImages]:
    return db.query(DataImages).filter(DataImages.project_uuid == project_uuid).offset(skip).limit(limit).all()

def get_data_image(db: Session, image_uuid: uuid.UUID):
    return db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()

def get_all_data_images(db: Session, skip: int = 0, limit: int = 10) -> List[DataImages]:
    return db.query(DataImages).offset(skip).limit(limit).all()

def update_data_image(db: Session, image_uuid: uuid.UUID, data_image: DataImageUpdate):
    db_image = db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()
    if not db_image:
        return None
    
    update_data = data_image.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_image, key, value)
    
    db.commit()
    db.refresh(db_image)
    return db_image

def delete_data_image(db: Session, image_uuid: uuid.UUID):
    db_data_image = get_data_image(db, image_uuid)
    if db_data_image:
        db.delete(db_data_image)
        db.commit()
    return db_data_image

def create_bbox(db: Session, bbox: BoundingBoxCreate):
    db_bbox = BoundingBox(
        image_uuid=bbox.image_uuid,
        name=bbox.name,
        bbox=bbox.bbox,
        color=bbox.color
    )
    db.add(db_bbox)
    db.commit()
    db.refresh(db_bbox)
    return db_bbox

def get_all_bboxes(db: Session, image_uuid: uuid.UUID):
    return db.query(BoundingBox).filter(BoundingBox.image_uuid == image_uuid).all()

def get_bbox(db: Session, bbox_uuid: uuid.UUID):
    bbox = db.query(BoundingBox).filter(BoundingBox.bbox_uuid == bbox_uuid).first()
    if not bbox:
        raise HTTPException(status_code=404, detail="Bounding box not found")
    return bbox

def update_bbox(db: Session, bbox_uuid: uuid.UUID, bbox_data: dict):
    db_bbox = get_bbox(db, bbox_uuid)
    if db_bbox:
        for key, value in bbox_data.items():
            setattr(db_bbox, key, value)
        db.commit()
        db.refresh(db_bbox)
    return db_bbox

def delete_bbox(db: Session, bbox_uuid: uuid.UUID):
    db_bbox = get_bbox(db, bbox_uuid)
    if db_bbox:
        db.delete(db_bbox)
        db.commit()
    return db_bbox