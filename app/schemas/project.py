from pydantic import BaseModel, Field, UUID4
from typing import List, Optional
from datetime import datetime
import uuid
class LabelItem(BaseModel):
    label_name: str
    label_color: str

    def to_dict(self):
        return {
            "label_name": self.label_name,
            "label_color": self.label_color,
        }

class ProjectLabelCreate(BaseModel):
    project_name: Optional[str] = None
    label_names: Optional[List[LabelItem]] = None
    created_by: Optional[UUID4]
    
    # created_at: Optional[datetime]
    class Config:
        from_attributes = True

class ProjectLabelInDB(BaseModel):
    project_uuid: UUID4
    project_name: str
    label_names: List[LabelItem]
    created_by: Optional[UUID4]
    created_at: Optional[datetime]
    arr_owner: Optional[List[UUID4]]
    class Config:
        from_attributes = True

class DataImageCreate(BaseModel):
    image_name: Optional[str] = None
    # image_path: Optional[str] = None
    image_url: Optional[str] = None
    project_uuid: UUID4
    label: Optional[dict] = None
    modify_by: Optional[UUID4] = None
    flag_label: bool
    image_width: Optional[int]
    image_height: Optional[int]
    class Config:
        from_attributes = True

class DataImageInDB(BaseModel):
    image_uuid: UUID4
    image_name: str
    project_uuid: UUID4
    label: Optional[dict] = None
    modify_by: Optional[UUID4] = None
    flag_label: bool
    image_width: Optional[int] = None
    image_height: Optional[int] = None
class DataImageResponse(BaseModel):
    image_uuid: str
    image_name: str
    image_url: str
    flag_label: bool
    image_width: Optional[int]
    image_height: Optional[int]
class DataImagesRead(BaseModel):
    image_uuid: uuid.UUID
    image_name: str
    image_data: Optional[str]
    project_uuid: uuid.UUID
    label: Optional[dict]
    modify_by: Optional[uuid.UUID]
    image_url: Optional[str]
    flag_label: bool 
    image_width: Optional[int]
    image_height: Optional[int]
    
class DataImageUpdate(BaseModel):
    image_name: Optional[str] = None
    project_uuid: Optional[UUID4] = None
    label: Optional[dict] = None
    modify_by: Optional[UUID4] = None
    flag_label: Optional[bool] = None
    

class BoundingBoxBase(BaseModel):
    name: str
    bbox: List[float]
    color: Optional[str] = Field(None, max_length=7)
class BoundingBoxCreate(BaseModel):
    image_uuid: uuid.UUID
    name: str
    bbox: List[float] 
    color: Optional[str] = Field(None, max_length=7) 
class BoundingBoxInDB(BoundingBoxBase):
    bbox_uuid: uuid.UUID
    image_uuid: uuid.UUID
# class BoundingBoxNameUpdate(BaseModel):
#     name: str
    class Config:
        from_attributes = True
