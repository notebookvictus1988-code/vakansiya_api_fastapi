from datetime import datetime, timezone
from pydantic import BaseModel, ConfigDict, Field, model_validator
from app.models.job import JobType, JobStatus

class JobCreate(BaseModel):
    title: str = Field(min_length=2, max_length=200)
    description: str = Field(min_length=10, max_length=20000)
    job_type: JobType
    salary_min: int = Field(ge=0)
    salary_max: int = Field(ge=0)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_values(self):
        if self.salary_min > self.salary_max:
            raise ValueError("salary_min salary_max dan katta bo'lishi mumkin emas")
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None:
                raise ValueError("expires_at timezone bilan yuborilishi kerak")
            if self.expires_at <= datetime.now(timezone.utc):
                raise ValueError("expires_at kelajakdagi sana bo'lishi kerak")
        return self

class JobUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=2, max_length=200)
    description: str | None = Field(default=None, min_length=10, max_length=20000)
    job_type: JobType | None = None
    salary_min: int | None = Field(default=None, ge=0)
    salary_max: int | None = Field(default=None, ge=0)
    expires_at: datetime | None = None

    @model_validator(mode="after")
    def validate_expiry(self):
        if self.expires_at is not None:
            if self.expires_at.tzinfo is None:
                raise ValueError("expires_at timezone bilan yuborilishi kerak")
            if self.expires_at <= datetime.now(timezone.utc):
                raise ValueError("expires_at kelajakdagi sana bo'lishi kerak")
        return self

class EmployerBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    full_name: str

class JobOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    employer_id: int
    title: str
    description: str
    job_type: JobType
    salary_min: int
    salary_max: int
    status: JobStatus
    created_at: datetime
    expires_at: datetime | None
    employer: EmployerBrief | None = None
