import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Index, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class ApplicationStatus(str, enum.Enum):
    submitted = "submitted"
    reviewed = "reviewed"
    accepted = "accepted"
    rejected = "rejected"

class Application(Base):
    __tablename__ = "applications"
    __table_args__ = (
        UniqueConstraint("job_id", "candidate_id", name="uq_application_job_candidate"),
        Index("ix_applications_candidate_created", "candidate_id", "created_at"),
        Index("ix_applications_job_created", "job_id", "created_at"),
    )
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    job_id: Mapped[int] = mapped_column(ForeignKey("jobs.id", ondelete="RESTRICT"), nullable=False)
    candidate_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    cover_letter: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ApplicationStatus] = mapped_column(Enum(ApplicationStatus, name="application_status", native_enum=False), default=ApplicationStatus.submitted, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    job = relationship("Job", back_populates="applications")
    candidate = relationship("User", back_populates="applications")
