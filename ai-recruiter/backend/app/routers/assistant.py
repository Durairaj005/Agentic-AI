from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.candidate import Candidate
from app.models.job import Job
from app.ai.assistant import recruiter_assistant
from app.ai.vector_store import vector_store
from app.schemas.assistant import (
    ChatQueryRequest,
    ChatQueryResponse,
    QuestionGenRequest,
    OutreachGenRequest
)

router = APIRouter(prefix="/ai/assistant", tags=["AI Recruiter Assistant & Sourcing"])


@router.post("/chat", response_model=ChatQueryResponse)
def chat_with_assistant(
    payload: ChatQueryRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Conversational RAG query answering, sourcing, and decision-support."""
    res = recruiter_assistant.chat(
        db=db,
        message=payload.message,
        job_id=payload.job_id,
        candidate_id=payload.candidate_id,
        history=payload.history
    )
    return res


@router.post("/generate-questions", response_model=ChatQueryResponse)
def generate_interview_questions(
    payload: QuestionGenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate role-tailored interview protocol addressing candidate gaps."""
    res = recruiter_assistant.chat(
        db=db,
        message=f"Generate targeted technical and system design interview questions for this candidate",
        job_id=payload.job_id,
        candidate_id=payload.candidate_id
    )
    return res


@router.post("/draft-outreach", response_model=ChatQueryResponse)
def draft_outreach_email(
    payload: OutreachGenRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Draft high-converting personalized candidate outreach email."""
    res = recruiter_assistant.chat(
        db=db,
        message="Draft a personalized candidate outreach email",
        job_id=payload.job_id,
        candidate_id=payload.candidate_id
    )
    return res


@router.get("/search-candidates")
def semantic_search_candidates(
    q: str = Query(..., min_length=2),
    top_k: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Vector similarity search against candidate embeddings in FAISS."""
    # Ensure index has vectors, if empty rebuild automatically
    if vector_store.index is None or vector_store.index.ntotal == 0:
        vector_store.rebuild_index(db)

    results = vector_store.search(q, top_k=top_k)
    return {
        "query": q,
        "total_results": len(results),
        "results": results
    }


@router.post("/reindex-vectors")
def reindex_vectors(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Rebuild the FAISS candidate vector index from current database records."""
    return vector_store.rebuild_index(db)
