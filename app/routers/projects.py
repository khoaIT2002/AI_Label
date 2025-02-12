from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Query, Path, Request, Form,  Body
from fastapi.responses import FileResponse,HTMLResponse
from sqlalchemy.orm import Session
import uuid
from typing import List
from schemas.project import (
    ProjectLabelCreate, ProjectLabelInDB,
    DataImageCreate, DataImageInDB, DataImageUpdate,
    BoundingBoxCreate, BoundingBoxInDB, DataImageResponse, DataImagesRead
)
from models.project import DataImages
# from crud.project import label_image_with_yolo
from fastapi.responses import StreamingResponse
from crud.project import (
    create_project_label, create_project, get_project_label, get_all_project_labels,
    update_project_label, delete_project_label, add_user_to_project, get_project_users,
    create_data_image,  delete_data_image, update_data_image,
    create_bbox, get_bbox, get_all_bboxes, update_bbox, delete_bbox, get_project_images, get_all_data_images,
)

from uuid import uuid4
from core.database import get_db
from secure.security_user import  RoleChecker
from PIL import Image
from PIL import Image as PILImage
import aiofiles
import os
import io 
from io import BytesIO
import json
from ultralytics import YOLO
import pandas as pd
from secure.security_user import decode_access_token, RoleChecker
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import base64
router = APIRouter()
import uuid
import logging
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/users/login")

# Role-based permissions
super_admin_only = RoleChecker(["super-admin"])
admin_only = RoleChecker(["admin"])
admin_or_super_admin = RoleChecker(["admin", "super-admin"])
user_only = RoleChecker(["user"])
all_roles = RoleChecker(["super-admin", "admin", "user"])

# Project Label Endpoints
@router.post("/projects", response_model=ProjectLabelInDB)
async def create_new_project(
    project: ProjectLabelCreate,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    decoded_token = decode_access_token(token)
    user_id = decoded_token.get('user_id')
    return create_project(db, project.project_name, user_id, project.label_names)

@router.post("/projects/{project_uuid}/users/{user_id}")
async def add_user_to_project_route(
    project_uuid: uuid.UUID,
    user_id: uuid.UUID,
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    decoded_token = decode_access_token(token)
    current_user_role = decoded_token.get('role_code')
    if current_user_role not in ['super-admin', 'admin']:
        raise HTTPException(status_code=403, detail="Not authorized to add users to projects")
    
    if add_user_to_project(db, project_uuid, user_id):
        return {"message": "User added to project successfully"}
    raise HTTPException(status_code=404, detail="Project or user not found")
@router.post("/projects/", response_model=ProjectLabelInDB)
def create_project_label_endpoint(
    project_label: ProjectLabelCreate, 
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    decoded_token = decode_access_token(token)
    user_id = uuid.UUID(decoded_token.get('user_id'))
    return create_project_label(db=db, project_label=project_label, user_id=user_id)

@router.get("/projects/{project_uuid}", response_model=ProjectLabelInDB)
def read_project_label(project_uuid: uuid.UUID, db: Session = Depends(get_db)):
    db_project_label = get_project_label(db=db, project_uuid=project_uuid)
    if db_project_label is None:
        raise HTTPException(status_code=404, detail="Project label not found")
    return db_project_label

@router.get("/projects/", response_model=List[ProjectLabelInDB])
def read_all_project_labels(db: Session = Depends(get_db)):
    return get_all_project_labels(db=db)

@router.put("/projects/{project_uuid}", response_model=ProjectLabelInDB)
def update_project_label_endpoint(project_uuid: uuid.UUID, project_label: ProjectLabelCreate, db: Session = Depends(get_db)):
    return update_project_label(db=db, project_uuid=project_uuid, project_label=project_label)

@router.delete("/projects/{project_uuid}", response_model=ProjectLabelInDB)
def delete_project_label_endpoint(project_uuid: uuid.UUID, db: Session = Depends(get_db)):
    return delete_project_label(db=db, project_uuid=project_uuid)
@router.get("/projects/{project_uuid}/data_images/{image_uuid}")
async def get_image(
    project_uuid: uuid.UUID,
    image_uuid: uuid.UUID,
    db: Session = Depends(get_db)
):
    db_image = db.query(DataImages).filter(DataImages.image_uuid == image_uuid, DataImages.project_uuid == project_uuid).first()
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    return StreamingResponse(io.BytesIO(db_image.image_data), media_type="image/jpeg") 
@router.post("/project_uuid/data_images/upload_images")
async def upload_images(
    project_uuid: uuid.UUID,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db)
):
    results = []
    for file in files:
        try:
            image_uuid = uuid.uuid4()
            image_data = await file.read()
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size 
            db_image = create_data_image(
                db=db,
                image_uuid=image_uuid,
                image_name=file.filename,
                image_data=image_data,
                project_uuid=project_uuid,
                flag_label=False,  # Thêm trường này, mặc định là False khi mới upload
                image_width=width,
                image_height=height 
            )
            
            image_url = f"/images/{image_uuid}"

            results.append({
                "image_uuid": str(db_image.image_uuid),
                "image_name": db_image.image_name,
                "image_url": image_url,
                "flag_label": db_image.flag_label  # Thêm trường này vào kết quả trả về
            })
        
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to upload {file.filename}: {str(e)}"
            )

    return {"uploaded_images": results}

@router.get("/images/{image_uuid}")
async def get_image(image_uuid: uuid.UUID, db: Session = Depends(get_db)):
    db_image = db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()
    
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_data = BytesIO(db_image.image_data)
    return StreamingResponse(image_data, media_type="image/jpeg")


# @router.post("/project_uuid/data_images/upload_images")
# async def upload_images(
#     project_uuid: uuid.UUID,
#     files: List[UploadFile] = File(...),
#     db: Session = Depends(get_db)
# ):
#     results = []
#     for file in files:
#         try:
#             image_uuid = uuid.uuid4()
#             image_data = await file.read()
            
#             db_image = create_data_image(
#                 db=db,
#                 image_uuid=image_uuid,
#                 image_name=file.filename,
#                 image_data=image_data,
#                 project_uuid=project_uuid,
#                 flag_label=False
#             )
            
#             image_url = f"/images/{image_uuid}"

#             results.append({
#                 "image_uuid": str(db_image.image_uuid),
#                 "image_name": db_image.image_name,
#                 "image_url": image_url,
#                 "flag_label": db_image.flag_label,
#                 "width": db_image.image_width,
#                 "height": db_image.image_height
#             })
        
#         except Exception as e:
#             raise HTTPException(
#                 status_code=500,
#                 detail=f"Failed to upload {file.filename}: {str(e)}"
#             )

#     return {"uploaded_images": results}
@router.get("/images/{image_uuid}")
async def get_image(image_uuid: uuid.UUID, db: Session = Depends(get_db)):
    db_image = db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()

    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")

    image_data = BytesIO(db_image.image_data)
    return StreamingResponse(image_data, media_type="image/jpeg")
@router.get("/image/{image_uuid}")
async def get_image(image_uuid: uuid.UUID, db: Session = Depends(get_db)):
    db_image = db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()
    
    if db_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    image_data = BytesIO(db_image.image_data)
    return StreamingResponse(image_data, media_type="image/jpeg")

@router.get("/projects/{project_uuid}/data_images/", response_model=List[DataImageResponse])
def get_data_images(project_uuid: uuid.UUID, db: Session = Depends(get_db)):
    
    try:
        data_images = db.query(DataImages).filter(DataImages.project_uuid == project_uuid).all()
        
        if not data_images:
            raise HTTPException(status_code=404, detail="No images found for this project")
        
        response_images = [
            DataImageResponse(
                image_uuid=str(image.image_uuid),
                image_name=image.image_name,
                image_url=f"/images/{image.image_uuid}",  # Adjust URL format if needed
                image_width=image.image_width,
                image_height=image.image_height,
                flag_label=image.flag_label
            )
            for image in data_images
        ]

        return response_images
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
@router.get("/projects/all_data_images/", response_model=List[DataImagesRead])
def read_all_data_images(db: Session = Depends(get_db)):
   
    try:
        images = db.query(DataImages).all()
        return [
            DataImagesRead(
                image_uuid=image.image_uuid,
                image_name=image.image_name,
                image_data=base64.b64encode(image.image_data).decode('utf-8') if image.image_data else None,
                project_uuid=image.project_uuid,
                label=image.label,
                modify_by=image.modify_by,
                image_url=image.image_url if image.image_url else "",
                image_width=image.image_width if image.image_width else 0,
                image_height=image.image_height if image.image_height else 0,
                flag_label=image.flag_label if hasattr(image, 'flag_label') else False  # Add this line

            )
            for image in images
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/projects/data_images/{image_uuid}", response_model=DataImageInDB)
def update_data_image_endpoint(
    image_uuid: uuid.UUID, 
    data_image: DataImageUpdate, 
    db: Session = Depends(get_db)
):
    updated_image = update_data_image(db, image_uuid, data_image)
    if updated_image is None:
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Refresh the object from the database to ensure we have the latest data
    db.refresh(updated_image)
    
    return updated_image


@router.delete("/data_images/{image_uuid}", response_model=DataImageInDB)
def delete_data_image_endpoint(image_uuid: uuid.UUID, db: Session = Depends(get_db)):
    return delete_data_image(db=db, image_uuid=image_uuid)


@router.get("/images/{image_uuid}")
async def read_image(image_uuid: uuid.UUID = Path(...), thumbnail: bool = True, db: Session = Depends(get_db)):
    db_data_image = db.query(DataImages).filter(DataImages.image_uuid == image_uuid).first()

    if db_data_image is None:
        raise HTTPException(status_code=404, detail="DataImage not found")

    image_path = db_data_image.image_path
    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail="Image file not found")

    try:
        image = Image.open(image_path)

        if image.mode == "RGBA":
            image = image.convert("RGB")

        if thumbnail:
            image.thumbnail((400, 225))

        image_stream = io.BytesIO()
        image.save(image_stream, format='JPEG')
        image_stream.seek(0)

        return StreamingResponse(image_stream, media_type="image/jpeg")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
# Bounding Boxes Endpoints
@router.post("/project/data_images/boxes/", response_model=BoundingBoxInDB)
def create_boxes(image_uuid: uuid.UUID, bbox: BoundingBoxCreate, db: Session = Depends(get_db)):
    return create_bbox(db=db, bbox=bbox)

@router.get("/project/data_images/boxes/", response_model=List[BoundingBoxInDB])
def read_all_boxes(image_uuid: uuid.UUID, db: Session = Depends(get_db)):
    return get_all_bboxes(db=db,  image_uuid=image_uuid)

@router.get("/project/data_images/boxes/{bbox_uuid}", response_model=BoundingBoxInDB)
def read_boxes(bbox_uuid: uuid.UUID, db: Session = Depends(get_db)):
    bbox = get_bbox(db, bbox_uuid)
    if bbox is None:
        raise HTTPException(status_code=404, detail="Bounding box not found")
    return bbox

@router.put("/project/data_images/boxes/{bbox_uuid}", response_model=BoundingBoxInDB)
def update_boxes(
    bbox_uuid: uuid.UUID,
    bbox: BoundingBoxCreate = Body(...),
    db: Session = Depends(get_db)
):
    existing_bbox = get_bbox(db, bbox_uuid)
    if existing_bbox is None:
        raise HTTPException(status_code=404, detail="Bounding box not found")
    
    updated_data = bbox.dict(exclude_unset=True)
    for key, value in updated_data.items():
        setattr(existing_bbox, key, value)
    
    db.commit()
    db.refresh(existing_bbox)
    return existing_bbox
@router.delete("/project/data_images/boxes/{bbox_uuid}", response_model=BoundingBoxInDB)
def delete_boxes(bbox_uuid: uuid.UUID, db: Session = Depends(get_db)):
    return delete_bbox(db=db, bbox_uuid=bbox_uuid)




