#   
from sqlalchemy import Column, String, ARRAY, Float, ForeignKey, DateTime, LargeBinary, Boolean, Integer, Table

from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
import uuid
from core.database import Base
from datetime import datetime
project_users = Table('project_users', Base.metadata,
    Column('project_uuid', UUID(as_uuid=True), ForeignKey('projects.project_uuid')),
    Column('user_id', UUID(as_uuid=True), ForeignKey('users.id'))
)
class ProjectLabel(Base):
    __tablename__ = 'projects'

    project_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    project_name = Column(String(255), nullable=False)
    label_names = Column(ARRAY(JSONB), nullable=True)
    created_by = Column(ARRAY(UUID(as_uuid=True)), ForeignKey('users.id'), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


    
    users = relationship("User", secondary=project_users, back_populates="projects")

    creator = relationship("User", foreign_keys=[created_by], overlaps="users")
class DataImages(Base):
    __tablename__ = 'data_image'

    image_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_name = Column(String(255), nullable=False)
    image_data = Column(LargeBinary, nullable=False)  # Store binary data
    project_uuid = Column(UUID(as_uuid=True), nullable=False)
    label = Column(JSONB, nullable=True)
    flag_label = Column(Boolean, default=False)
    modify_by = Column(UUID(as_uuid=True), nullable=True)
    image_url = Column(String(255), default=False)
    image_width = Column(Integer, nullable=True)
    image_height = Column(Integer, nullable=True)
class BoundingBox(Base):
    __tablename__ = 'bounding_boxes'

    bbox_uuid = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    image_uuid = Column(UUID(as_uuid=True))
    name = Column(String(255), nullable=False)
    bbox = Column(ARRAY(Float), nullable=False)
    color = Column(String(7), nullable=True)
