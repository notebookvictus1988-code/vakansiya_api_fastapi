from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field
from app.models.application import ApplicationStatus
from app.schemas.job import JobOut
from app.schemas.auth import UserOut

class ApplicationCreate(BaseModel):
    cover_letter: str = Field(min_length=10, max_length=10000)

class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus

class ApplicationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    job_id: int
    candidate_id: int
    cover_letter: str
    status: ApplicationStatus
    created_at: datetime

class MyApplicationOut(ApplicationOut):
    job: JobOut

class EmployerApplicationOut(ApplicationOut):
    candidate: UserOut
