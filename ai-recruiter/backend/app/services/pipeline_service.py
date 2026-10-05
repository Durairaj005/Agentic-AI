from datetime import datetime, timezone, timedelta
from typing import List, Optional
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_

from app.models.application import Application
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.followup import Note, Followup
from app.models.interview import Interview
from app.models.user import User
from app.schemas.pipeline import (
    ApplicationUpdateStage, 
    NoteCreate, 
    FollowupCreate, 
    FollowupUpdate, 
    InterviewCreate, 
    InterviewUpdate
)

VALID_STAGES = [
    "NEW", 
    "SCREENING", 
    "SHORTLISTED", 
    "CONTACTED", 
    "INTERVIEW", 
    "SELECTED", 
    "REJECTED", 
    "HIRED"
]


class PipelineService:
    @staticmethod
    def get_applications(
        db: Session,
        job_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        min_score: Optional[float] = None
    ) -> List[Application]:
        query = (
            db.query(Application)
            .options(
                joinedload(Application.candidate).joinedload(Candidate.skills),
                joinedload(Application.job)
            )
        )

        if job_id:
            query = query.filter(Application.job_id == job_id)
        if status and status.upper() != "ALL":
            query = query.filter(Application.status == status.upper())
        if min_score is not None and min_score > 0:
            query = query.filter(Application.match_score >= min_score)
        if search:
            search_pattern = f"%{search.strip().lower()}%"
            query = query.join(Application.candidate).filter(
                or_(
                    Candidate.name.ilike(search_pattern),
                    Candidate.email.ilike(search_pattern),
                    Candidate.location.ilike(search_pattern)
                )
            )

        return query.order_by(Application.match_score.desc()).all()

    @staticmethod
    def get_application_by_id(db: Session, application_id: str) -> Optional[Application]:
        return (
            db.query(Application)
            .options(
                joinedload(Application.candidate).joinedload(Candidate.skills),
                joinedload(Application.job),
                joinedload(Application.interviews)
            )
            .filter(Application.id == application_id)
            .first()
        )

    @staticmethod
    def update_application_stage(
        db: Session,
        application_id: str,
        stage: str,
        recruiter_notes: Optional[str] = None,
        user_id: Optional[str] = None
    ) -> Application:
        stage_clean = stage.upper().strip()
        if stage_clean not in VALID_STAGES:
            raise ValueError(f"Invalid recruitment stage: {stage}. Must be one of {VALID_STAGES}")

        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise LookupError(f"Application {application_id} not found")

        app.status = stage_clean
        if recruiter_notes is not None:
            app.recruiter_notes = recruiter_notes
            # Also record in notes history
            if recruiter_notes.strip():
                new_note = Note(
                    candidate_id=app.candidate_id,
                    recruiter_id=user_id,
                    note=f"Stage shifted to {stage_clean}: {recruiter_notes.strip()}"
                )
                db.add(new_note)

        db.commit()
        db.refresh(app)
        return app

    # --- Notes ---
    @staticmethod
    def get_candidate_notes(db: Session, candidate_id: str) -> List[Note]:
        return (
            db.query(Note)
            .options(joinedload(Note.recruiter))
            .filter(Note.candidate_id == candidate_id)
            .order_by(Note.created_at.desc())
            .all()
        )

    @staticmethod
    def create_candidate_note(
        db: Session,
        candidate_id: str,
        note_text: str,
        user_id: Optional[str] = None
    ) -> Note:
        candidate = db.query(Candidate).filter(Candidate.id == candidate_id).first()
        if not candidate:
            raise LookupError(f"Candidate {candidate_id} not found")

        note = Note(
            candidate_id=candidate_id,
            recruiter_id=user_id,
            note=note_text.strip()
        )
        db.add(note)
        db.commit()
        db.refresh(note)
        return note

    # --- Follow-ups ---
    @staticmethod
    def get_followups(
        db: Session,
        candidate_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Followup]:
        now = datetime.now(timezone.utc)
        query = db.query(Followup).options(joinedload(Followup.candidate), joinedload(Followup.recruiter))

        if candidate_id:
            query = query.filter(Followup.candidate_id == candidate_id)
        if status and status.upper() != "ALL":
            query = query.filter(Followup.status == status.upper())

        followups = query.order_by(Followup.followup_date.asc()).all()

        # Check and update overdue status dynamically
        changed = False
        for f in followups:
            # Handle tz-aware vs naive datetime comparison
            f_date = f.followup_date
            if f_date.tzinfo is None:
                f_date = f_date.replace(tzinfo=timezone.utc)
            if f.status == "PENDING" and f_date < now:
                f.status = "OVERDUE"
                changed = True
        if changed:
            db.commit()

        return followups

    @staticmethod
    def create_followup(
        db: Session,
        payload: FollowupCreate,
        user_id: Optional[str] = None
    ) -> Followup:
        candidate = db.query(Candidate).filter(Candidate.id == payload.candidate_id).first()
        if not candidate:
            raise LookupError(f"Candidate {payload.candidate_id} not found")

        followup = Followup(
            candidate_id=payload.candidate_id,
            recruiter_id=user_id,
            followup_date=payload.followup_date,
            method=payload.method.upper(),
            status="PENDING",
            notes=payload.notes
        )
        db.add(followup)
        db.commit()
        db.refresh(followup)
        return followup

    @staticmethod
    def update_followup(
        db: Session,
        followup_id: str,
        payload: FollowupUpdate
    ) -> Followup:
        f = db.query(Followup).filter(Followup.id == followup_id).first()
        if not f:
            raise LookupError(f"Followup {followup_id} not found")

        if payload.status:
            f.status = payload.status.upper()
        if payload.notes is not None:
            f.notes = payload.notes
        if payload.followup_date:
            f.followup_date = payload.followup_date
        if payload.method:
            f.method = payload.method.upper()

        db.commit()
        db.refresh(f)
        return f

    @staticmethod
    def delete_followup(db: Session, followup_id: str) -> bool:
        f = db.query(Followup).filter(Followup.id == followup_id).first()
        if not f:
            return False
        db.delete(f)
        db.commit()
        return True

    # --- Interviews ---
    @staticmethod
    def get_interviews(
        db: Session,
        application_id: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[Interview]:
        query = (
            db.query(Interview)
            .options(
                joinedload(Interview.application).joinedload(Application.candidate),
                joinedload(Interview.application).joinedload(Application.job)
            )
        )
        if application_id:
            query = query.filter(Interview.application_id == application_id)
        if status and status.upper() != "ALL":
            query = query.filter(Interview.status == status.upper())

        return query.order_by(Interview.interview_date.asc()).all()

    @staticmethod
    def schedule_interview(
        db: Session,
        payload: InterviewCreate
    ) -> Interview:
        app = db.query(Application).filter(Application.id == payload.application_id).first()
        if not app:
            raise LookupError(f"Application {payload.application_id} not found")

        interview = Interview(
            application_id=payload.application_id,
            interview_date=payload.interview_date,
            interview_type=payload.interview_type.upper(),
            interviewer=payload.interviewer,
            feedback=payload.feedback,
            rating=payload.rating,
            status="SCHEDULED"
        )
        db.add(interview)

        # Advance application to INTERVIEW stage if currently in earlier stage
        if app.status in ["NEW", "SCREENING", "SHORTLISTED", "CONTACTED"]:
            app.status = "INTERVIEW"

        db.commit()
        db.refresh(interview)
        return interview

    @staticmethod
    def update_interview(
        db: Session,
        interview_id: str,
        payload: InterviewUpdate
    ) -> Interview:
        interview = db.query(Interview).filter(Interview.id == interview_id).first()
        if not interview:
            raise LookupError(f"Interview {interview_id} not found")

        if payload.status:
            interview.status = payload.status.upper()
        if payload.feedback is not None:
            interview.feedback = payload.feedback
        if payload.rating is not None:
            interview.rating = payload.rating
        if payload.interview_date:
            interview.interview_date = payload.interview_date
        if payload.interview_type:
            interview.interview_type = payload.interview_type.upper()
        if payload.interviewer:
            interview.interviewer = payload.interviewer

        db.commit()
        db.refresh(interview)
        return interview

    # --- Seeder for rich pipeline demo ---
    @staticmethod
    def seed_pipeline_demo_data(db: Session) -> dict:
        """Seed realistic pipeline distribution across stages, follow-ups, and interviews."""
        from app.services.matching_service import MatchingService

        jobs = db.query(Job).all()
        candidates = db.query(Candidate).all()
        if not jobs or not candidates:
            return {"message": "Ensure jobs and candidates are seeded first."}

        # First run matching on all jobs to establish applications
        created_apps = 0
        for job in jobs:
            summary = MatchingService.execute_matching_for_job(db, job.id)
            created_apps += summary.created_applications_count

        # Get all applications
        applications = db.query(Application).all()
        if not applications:
            return {"message": "No applications created."}

        # Distribute into realistic pipeline stages
        # Stages: NEW, SCREENING, SHORTLISTED, CONTACTED, INTERVIEW, SELECTED, REJECTED, HIRED
        stages_cycle = [
            "SHORTLISTED", "INTERVIEW", "SCREENING", "SELECTED", 
            "CONTACTED", "HIRED", "SHORTLISTED", "NEW"
        ]

        now = datetime.now(timezone.utc)
        recruiter = db.query(User).filter(User.role == "RECRUITER").first()
        recruiter_id = recruiter.id if recruiter else None

        updated_count = 0
        for idx, app in enumerate(applications):
            target_stage = stages_cycle[idx % len(stages_cycle)]
            app.status = target_stage
            updated_count += 1

            # Add sample notes
            if idx % 3 == 0:
                note_text = f"Reviewed profile for {app.job.title if app.job else 'role'}. Candidate demonstrates strong technical foundation."
                db.add(Note(candidate_id=app.candidate_id, recruiter_id=recruiter_id, note=note_text))

            # Add sample follow-ups
            if idx % 4 == 0:
                followup_date = now + timedelta(days=((idx % 5) - 2))  # some in past (overdue), some future
                method = ["CALL", "EMAIL", "LINKEDIN"][idx % 3]
                status = "PENDING"
                db.add(Followup(
                    candidate_id=app.candidate_id,
                    recruiter_id=recruiter_id,
                    followup_date=followup_date,
                    method=method,
                    status=status,
                    notes=f"Follow up regarding compensation expectation and availability."
                ))

            # Add sample interviews for INTERVIEW, SELECTED, and HIRED
            if target_stage in ["INTERVIEW", "SELECTED", "HIRED"] and idx % 2 == 0:
                int_date = now + timedelta(days=((idx % 3) - 1))
                db.add(Interview(
                    application_id=app.id,
                    interview_date=int_date,
                    interview_type=["TECHNICAL", "BEHAVIORAL", "FINAL"][idx % 3],
                    interviewer="Alex Chen & Sr. Architect",
                    status="COMPLETED" if target_stage in ["SELECTED", "HIRED"] else "SCHEDULED",
                    feedback="Candidate showed solid system design principles and good communication." if target_stage in ["SELECTED", "HIRED"] else None,
                    rating=4 if target_stage in ["SELECTED", "HIRED"] else None
                ))

        db.commit()
        return {
            "message": "Pipeline demonstration data populated successfully.",
            "total_applications": len(applications),
            "updated_stages_count": updated_count
        }


pipeline_service = PipelineService()
