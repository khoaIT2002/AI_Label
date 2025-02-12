
from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Integer, ARRAY
from core.database import Base
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from models.project import project_users
import uuid
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String)
    email = Column(String)
    username = Column(String, unique=True)
    password = Column(String)
    status = Column(Integer)
    role_code = Column(String, ForeignKey('roles.code'))
    createdBy = Column(String, default="", nullable=True)
    createdAt = Column(DateTime(timezone=True), default=datetime.utcnow)
    modifiedBy = Column(String, default="", nullable=True)
    role = relationship("Role", back_populates="users")

    projects = relationship("ProjectLabel", secondary=project_users, back_populates="users")