"""Project model"""
from sqlalchemy import Column, Integer, String, Boolean, Text, TIMESTAMP
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Project(Base):
    """Project model"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_code = Column(String(50), unique=True, nullable=False, index=True)
    project_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    stations = relationship("Station", back_populates="project", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Project {self.project_code}>"
