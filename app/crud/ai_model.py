#crud\ai_model.py
from sqlalchemy.orm import Session
from fastapi import UploadFile
from models.ai_model import AIModel
from schemas.ai_model import AIModelCreate, AIModelUpdate
from uuid import UUID

def create_ai_model(db: Session, model: AIModelCreate, file: UploadFile):
    db_model = AIModel(name=model.name, model_file=file.file.read())
    db.add(db_model)
    db.commit()
    db.refresh(db_model)
    return db_model

def get_ai_model(db: Session, model_id: UUID):
    return db.query(AIModel).filter(AIModel.id == model_id).first()

def get_ai_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(AIModel).offset(skip).limit(limit).all()

def update_ai_model(db: Session, model_id: UUID, model: AIModelUpdate, file: UploadFile = None):
    db_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if db_model:
        db_model.name = model.name
        if file:
            db_model.model_file = file.file.read()
        db.commit()
        db.refresh(db_model)
    return db_model

def delete_ai_model(db: Session, model_id: UUID):
    db_model = db.query(AIModel).filter(AIModel.id == model_id).first()
    if db_model:
        db.delete(db_model)
        db.commit()
    return db_model