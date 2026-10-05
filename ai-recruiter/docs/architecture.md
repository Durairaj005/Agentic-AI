# Architecture & Technical Design Document
## AI-Powered Smart Recruitment & Candidate Matching Platform

### 1. Executive Summary
This document outlines the technical architecture, data model, AI/NLP subsystem, and security policies for the **AI-Powered Smart Recruitment & Candidate Matching Platform**. The system assists technical and IT recruiters by automating candidate parsing, normalization, multi-factor matching, and pipeline management while ensuring transparent, explainable AI and human-in-the-loop governance.

---

### 2. High-Level Architecture
The platform is organized as a decoupled monorepo:
- **Presentation Layer**: React (v18), TypeScript, Tailwind CSS, Lucide icons, Recharts, and Vite.
- **API & Application Gateway**: FastAPI running under Uvicorn, with Pydantic v2 schemas and OAuth2/JWT security.
- **Relational Storage**: SQLAlchemy 2.0 ORM with seamless switching between SQLite (local development) and PostgreSQL (production).
- **AI & NLP Pipeline**: Deterministic document parsing (PyMuPDF, python-docx), canonical skill taxonomy mapping, dense sentence embeddings (`all-MiniLM-L6-v2`), FAISS vector store, and transparent multi-factor scoring.
- **LLM / RAG Layer**: Local Ollama support with deterministic rule-based fallback ensuring zero paid API dependencies.

---

### 3. Database Schema Overview
The relational model consists of 9 core tables:
1. `users`: System users (Recruiters and Admins) with hashed credentials and role-based permissions.
2. `jobs`: Requisition postings with experience requirements, location, and status.
3. `job_skills`: Required vs. preferred technical skills with importance ratings.
4. `candidates`: Candidate profiles with parsed resume text, education tier, and experience years.
5. `candidate_skills`: Normalized skills extracted from resumes with confidence ratings.
6. `applications`: Candidate-job linkage with multi-factor match scores, explainability JSON, and Kanban pipeline stage.
7. `interviews`: Scheduled interview rounds with feedback, dates, and 1-5 ratings.
8. `notes`: Recruiter annotations and internal commentary per candidate.
9. `followups`: Actionable recruiter follow-ups categorized by overdue, today, and upcoming.

---

### 4. Matching Algorithm Specifications
The matching score $S_{total} \in [0, 100]\%$ is calculated via a configurable weighted sum:
$$S_{total} = (0.40 \times S_{req}) + (0.20 \times S_{pref}) + (0.20 \times S_{exp}) + (0.10 \times S_{edu}) + (0.10 \times S_{sem})$$

- **$S_{req}$ (Required Skills, 40%)**: Intersection ratio between candidate skills and required job skills.
- **$S_{pref}$ (Preferred Skills, 20%)**: Intersection ratio between candidate skills and preferred job skills.
- **$S_{exp}$ (Experience, 20%)**: Linear ramp up to required minimum years.
- **$S_{edu}$ (Education, 10%)**: Tier comparison (`PHD` > `MASTERS` > `BACHELORS` > `DIPLOMA`) with work experience equivalency floor.
- **$S_{sem}$ (Semantic Vector Match, 10%)**: Cosine similarity between dense embedding vectors of the resume and JD generated via Sentence Transformers.

---

### 5. Responsible AI and Transparency
- **No Protected Attributes**: Ranking explicitly ignores gender, race, age, religion, or other protected demographic attributes.
- **Explainability**: Every match score is accompanied by an itemized list of matched skills, missing required skills, missing preferred skills, and an explanatory justification.
- **Decision-Support Guardrail**: AI scores serve exclusively to assist recruiter efficiency. The human recruiter maintains complete authority over stage advancement, interview decisions, and final offers.
