from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from app.db.session import get_db
from app.dependencies import require_roles
from app.models.user import User, UserRole
from app.models.job import Job
from app.models.application import Application, ApplicationStatus
from app.schemas.application import MyApplicationOut, ApplicationStatusUpdate, EmployerApplicationOut

router = APIRouter(prefix="/applications", tags=["Applications"])

@router.get("/my", response_model=list[MyApplicationOut])
def my_applications(db: Session = Depends(get_db),
                    candidate: User = Depends(require_roles(UserRole.candidate))):
    stmt = (select(Application)
            .options(joinedload(Application.job).joinedload(Job.employer))
            .where(Application.candidate_id == candidate.id)
            .order_by(Application.created_at.desc()))
    return list(db.scalars(stmt).unique().all())

@router.patch("/{application_id}/status", response_model=EmployerApplicationOut)
def update_application_status(application_id: int, payload: ApplicationStatusUpdate,
                              db: Session = Depends(get_db),
                              employer: User = Depends(require_roles(UserRole.employer))):
    if payload.status not in (ApplicationStatus.reviewed, ApplicationStatus.accepted, ApplicationStatus.rejected):
        raise HTTPException(status_code=422, detail="Ushbu statusga o'tish mumkin emas")
    application = db.scalar(
        select(Application).options(joinedload(Application.job), joinedload(Application.candidate))
        .where(Application.id == application_id).with_for_update()
    )
    if not application:
        raise HTTPException(status_code=404, detail="Ariza topilmadi")
    if application.job.employer_id != employer.id:
        raise HTTPException(status_code=403, detail="Bu ariza sizning vakansiyangizga tegishli emas")
    allowed = {
        ApplicationStatus.submitted: {ApplicationStatus.reviewed},
        ApplicationStatus.reviewed: {ApplicationStatus.accepted, ApplicationStatus.rejected},
        ApplicationStatus.accepted: set(),
        ApplicationStatus.rejected: set(),
    }
    if payload.status not in allowed[application.status]:
        raise HTTPException(status_code=400, detail=f"{application.status.value} holatidan {payload.status.value} holatiga o'tish mumkin emas")
    application.status = payload.status
    db.commit()
    db.refresh(application)
    return application
