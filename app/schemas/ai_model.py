#schemas\ai_model.py
from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class AIModelBase(BaseModel):
    name: str

class AIModelCreate(AIModelBase):
    pass

class AIModelUpdate(AIModelBase):
    pass

class AIModelInDB(AIModelBase):
    id: UUID4
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class AIModelOut(AIModelInDB):
    pass