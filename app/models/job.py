import enum
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class JobType(str, enum.Enum):
    full_time = "full_time"
    part_time = "part_time"
    contract = "contract"
    internship = "internship"
    remote = "remote"
    hybrid = "hybrid"
    freelance = "freelance"

class JobStatus(str, enum.Enum):
    open = "open"
    closed = "closed"

class Job(Base):
    __tablename__ = "jobs"
    __table_args__ = (
        CheckConstraint("salary_min >= 0", name="ck_jobs_salary_min_nonnegative"),
        CheckConstraint("salary_max >= 0", name="ck_jobs_salary_max_nonnegative"),
        CheckConstraint("salary_min <= salary_max", name="ck_jobs_salary_order"),
        Index("ix_jobs_status_created_at", "status", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    employer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    job_type: Mapped[JobType] = mapped_column(Enum(JobType, name="job_type", native_enum=False), nullable=False, index=True)
    salary_min: Mapped[int] = mapped_column(Integer, nullable=False)
    salary_max: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus, name="job_status", native_enum=False), default=JobStatus.open, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    employer = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job")
