from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.db.session import get_db
from app.dependencies import require_roles
from app.models.application import Application, ApplicationStatus
from app.models.job import Job, JobStatus, JobType
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationCreate,
    ApplicationOut,
    EmployerApplicationOut,
)
from app.schemas.job import JobCreate, JobOut, JobUpdate

router = APIRouter(prefix="/jobs", tags=["Jobs"])

def utc_now():
    return datetime.now(UTC)

def ensure_owner(job: Job, user: User):
    if job.employer_id != user.id:
        raise HTTPException(status_code=403, detail="Bu vakansiya sizga tegishli emas")

@router.get("", response_model=list[JobOut])
def list_jobs(title: str | None = Query(default=None, max_length=200),
              job_type: JobType | None = None,
              requested_salary: int | None = Query(default=None, ge=0),
              skip: int = Query(default=0, ge=0),
              limit: int = Query(default=20, ge=1, le=100),
              db: Session = Depends(get_db)):
    now = utc_now()
    conditions = [Job.status == JobStatus.open,
                  or_(Job.expires_at.is_(None), Job.expires_at > now)]
    if title:
        conditions.append(Job.title.ilike(f"%{title.strip()}%"))
    if job_type:
        conditions.append(Job.job_type == job_type)
    if requested_salary is not None:
        conditions.append(Job.salary_min >= requested_salary)
    stmt = (select(Job).options(joinedload(Job.employer))
            .where(and_(*conditions)).order_by(Job.created_at.desc())
            .offset(skip).limit(limit))
    return list(db.scalars(stmt).unique().all())

@router.get("/{job_id}", response_model=JobOut)
def get_job(job_id: int, db: Session = Depends(get_db)):
    job = db.scalar(select(Job).options(joinedload(Job.employer)).where(Job.id == job_id))
    if not job or job.status != JobStatus.open or (job.expires_at and job.expires_at <= utc_now()):
        raise HTTPException(status_code=404, detail="Vakansiya topilmadi")
    return job

@router.post("", response_model=JobOut, status_code=status.HTTP_201_CREATED)
def create_job(payload: JobCreate, db: Session = Depends(get_db),
               employer: User = Depends(require_roles(UserRole.employer))):
    job = Job(employer_id=employer.id, **payload.model_dump())
    db.add(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=422, detail="Vakansiya ma'lumotlari noto'g'ri")
    db.refresh(job)
    job.employer = employer
    return job

def update_job_common(job_id: int, payload: JobUpdate, db: Session, employer: User):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vakansiya topilmadi")
    ensure_owner(job, employer)
    if job.status != JobStatus.open:
        raise HTTPException(status_code=400, detail="Yopilgan vakansiyani tahrirlab bo'lmaydi")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(job, key, value)
    if job.salary_min < 0 or job.salary_max < 0 or job.salary_min > job.salary_max:
        raise HTTPException(status_code=422, detail="0 <= salary_min <= salary_max bo'lishi kerak")
    if job.expires_at is not None:
        if job.expires_at.tzinfo is None or job.expires_at <= utc_now():
            raise HTTPException(status_code=422, detail="expires_at kelajakdagi timezone'li sana bo'lishi kerak")
    db.commit()
    db.refresh(job)
    job.employer = employer
    return job

@router.put("/{job_id}", response_model=JobOut)
def replace_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db),
                employer: User = Depends(require_roles(UserRole.employer))):
    return update_job_common(job_id, payload, db, employer)

@router.patch("/{job_id}", response_model=JobOut)
def patch_job(job_id: int, payload: JobUpdate, db: Session = Depends(get_db),
              employer: User = Depends(require_roles(UserRole.employer))):
    return update_job_common(job_id, payload, db, employer)

@router.patch("/{job_id}/close", response_model=JobOut)
def close_job(job_id: int, db: Session = Depends(get_db),
              employer: User = Depends(require_roles(UserRole.employer))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vakansiya topilmadi")
    ensure_owner(job, employer)
    job.status = JobStatus.closed
    db.commit()
    db.refresh(job)
    job.employer = employer
    return job

@router.delete("/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_job(job_id: int, db: Session = Depends(get_db),
               employer: User = Depends(require_roles(UserRole.employer))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vakansiya topilmadi")
    ensure_owner(job, employer)
    count = db.scalar(select(func.count(Application.id)).where(Application.job_id == job_id)) or 0
    if count:
        raise HTTPException(status_code=400, detail="Arizalar mavjud vakansiyani o'chirib bo'lmaydi")
    db.delete(job)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Vakansiyani o'chirib bo'lmadi")

@router.post("/{job_id}/apply", response_model=ApplicationOut, status_code=status.HTTP_201_CREATED)
def apply_to_job(job_id: int, payload: ApplicationCreate, db: Session = Depends(get_db),
                 candidate: User = Depends(require_roles(UserRole.candidate))):
    job = db.scalar(select(Job).where(Job.id == job_id).with_for_update())
    if not job:
        raise HTTPException(status_code=404, detail="Vakansiya topilmadi")
    if job.status == JobStatus.closed or (job.expires_at and job.expires_at <= utc_now()):
        raise HTTPException(status_code=400, detail="Yopilgan yoki muddati o'tgan vakansiyaga ariza berib bo'lmaydi")
    existing = db.scalar(select(Application.id).where(
        Application.job_id == job_id, Application.candidate_id == candidate.id))
    if existing:
        raise HTTPException(status_code=409, detail="Bu vakansiyaga avval ariza topshirgansiz")
    application = Application(job_id=job_id, candidate_id=candidate.id,
                              cover_letter=payload.cover_letter.strip(),
                              status=ApplicationStatus.submitted)
    db.add(application)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Bu vakansiyaga avval ariza topshirgansiz")
    db.refresh(application)
    return application

@router.get("/{job_id}/applications", response_model=list[EmployerApplicationOut])
def list_job_applications(job_id: int, db: Session = Depends(get_db),
                          employer: User = Depends(require_roles(UserRole.employer))):
    job = db.get(Job, job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Vakansiya topilmadi")
    ensure_owner(job, employer)
    stmt = (select(Application).options(joinedload(Application.candidate))
            .where(Application.job_id == job_id).order_by(Application.created_at.desc()))
    return list(db.scalars(stmt).unique().all())
