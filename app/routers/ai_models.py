#routers\ai_models.py
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List
from core.database import get_db
from crud import ai_model as ai_model_crud
from schemas.ai_model import AIModelCreate, AIModelUpdate, AIModelOut
from models.project import DataImages
from uuid import UUID
from PIL import ImageFont
import io
from ultralytics import YOLO
import tempfile
import os
import json
from PIL import Image, ImageDraw
import numpy as np
router = APIRouter()

@router.post("/", response_model=AIModelOut)
def create_ai_model(model: AIModelCreate = Depends(), file: UploadFile = File(...), db: Session = Depends(get_db)):
    return ai_model_crud.create_ai_model(db, model, file)

@router.get("/{model_id}", response_model=AIModelOut)
def read_ai_model(model_id: UUID, db: Session = Depends(get_db)):
    db_model = ai_model_crud.get_ai_model(db, model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="AI Model not found")
    return db_model

@router.get("/", response_model=List[AIModelOut])
def read_ai_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return ai_model_crud.get_ai_models(db, skip=skip, limit=limit)

@router.put("/{model_id}", response_model=AIModelOut)
def update_ai_model(model_id: UUID, model: AIModelUpdate, file: UploadFile = File(None), db: Session = Depends(get_db)):
    db_model = ai_model_crud.update_ai_model(db, model_id, model, file)
    if db_model is None:
        raise HTTPException(status_code=404, detail="AI Model not found")
    return db_model

@router.delete("/{model_id}", response_model=AIModelOut)
def delete_ai_model(model_id: UUID, db: Session = Depends(get_db)):
    db_model = ai_model_crud.delete_ai_model(db, model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="AI Model not found")
    return db_model


@router.get("/detect/{model_id}/{image_id}")
def detect_objects(model_id: UUID, image_id: UUID, db: Session = Depends(get_db)):
    model = ai_model_crud.get_ai_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="AI Model not found")
    
    image = db.query(DataImages).filter(DataImages.image_uuid == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as temp_model_file:
        temp_model_file.write(model.model_file)
        temp_model_path = temp_model_file.name
    try:
        yolo_model = YOLO(temp_model_path)
        pil_image = Image.open(io.BytesIO(image.image_data))
        np_image = np.array(pil_image)
        
        results = yolo_model(np_image)
        
        formatted_results = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x, y, w, h = box.xywh[0]
                class_id = int(box.cls)
                class_name = yolo_model.names[class_id]
                formatted_results.append({
                    "x": float(x),
                    "y": float(y),
                    "w": float(w),
                    "h": float(h),
                    "class": class_name
                })
        
        return {"detections": formatted_results}
    
    finally:
        os.unlink(temp_model_path)

@router.get("/detect_image/{model_id}/{image_id}")
def detect_objects_image(model_id: UUID, image_id: UUID, db: Session = Depends(get_db)):
    model = ai_model_crud.get_ai_model(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="AI Model not found")
    
    image = db.query(DataImages).filter(DataImages.image_uuid == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")
    
    with tempfile.NamedTemporaryFile(delete=False, suffix='.pt') as temp_model_file:
        temp_model_file.write(model.model_file)
        temp_model_path = temp_model_file.name

    try:
        yolo_model = YOLO(temp_model_path)
        pil_image = Image.open(io.BytesIO(image.image_data))
        np_image = np.array(pil_image)
        
        results = yolo_model(np_image)
        
        draw = ImageDraw.Draw(pil_image)
        font = ImageFont.load_default()
        
        detections = []
        for r in results:
            boxes = r.boxes
            for box in boxes:
                x1, y1, x2, y2 = box.xyxy[0]
                class_id = int(box.cls)
                class_name = yolo_model.names[class_id]
                
                draw.rectangle([x1, y1, x2, y2], outline="red", width=3)
                draw.text((x1, y1 - 10), class_name, font=font, fill="red")
                
                detections.append({
                    "x": float(x1),
                    "y": float(y1),
                    "w": float(x2 - x1),
                    "h": float(y2 - y1),
                    "class": class_name
                })
        
        img_byte_arr = io.BytesIO()
        pil_image.save(img_byte_arr, format='PNG')
        img_byte_arr = img_byte_arr.getvalue()
        
        headers = {
            'Content-Disposition': 'inline; filename="detected_image.png"',
            'X-Detections': json.dumps(detections)
        }
        
        return StreamingResponse(io.BytesIO(img_byte_arr), media_type="image/png", headers=headers)
    
    finally:
        os.unlink(temp_model_path)