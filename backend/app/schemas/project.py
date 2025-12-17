"""Project schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ProjectBase(BaseModel):
    """Base project schema"""
    project_code: str = Field(..., min_length=1, max_length=50)
    project_name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    """Project creation schema"""
    pass


class ProjectUpdate(BaseModel):
    """Project update schema"""
    project_name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    is_active: Optional[bool] = None


class ProjectInDB(ProjectBase):
    """Project schema for database"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Project(ProjectInDB):
    """Project response schema"""
    pass


class StationBase(BaseModel):
    """Base station schema"""
    station_code: str = Field(..., min_length=1, max_length=50)
    station_name: str = Field(..., min_length=1, max_length=100)
    test_plan_path: Optional[str] = Field(None, max_length=255)


class StationCreate(StationBase):
    """Station creation schema"""
    project_id: int


class StationUpdate(BaseModel):
    """Station update schema"""
    station_name: Optional[str] = Field(None, min_length=1, max_length=100)
    test_plan_path: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None


class StationInDB(StationBase):
    """Station schema for database"""
    id: int
    project_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class Station(StationInDB):
    """Station response schema"""
    pass


class ProjectWithStations(Project):
    """Project with stations"""
    stations: List[Station] = []

    class Config:
        from_attributes = True
