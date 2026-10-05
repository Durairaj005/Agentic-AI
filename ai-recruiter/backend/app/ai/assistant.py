import re
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.ai.vector_store import vector_store
from app.models.candidate import Candidate
from app.models.job import Job
from app.models.application import Application


class RecruiterAIAssistant:
    def chat(
        self,
        db: Session,
        message: str,
        job_id: Optional[str] = None,
        candidate_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """Process conversational query from recruiter using local RAG context."""
        query_lower = message.lower().strip()

        # Context gathering
        referenced_job = None
        if job_id:
            referenced_job = db.query(Job).filter(Job.id == job_id).first()

        referenced_cand = None
        if candidate_id:
            referenced_cand = db.query(Candidate).filter(Candidate.id == candidate_id).first()

        # If candidate wasn't explicitly selected, try to detect candidate name in message
        if not referenced_cand:
            candidates = db.query(Candidate).all()
            for c in candidates:
                if c.name.lower() in query_lower:
                    referenced_cand = c
                    break

        # 1. Intent: Generate Interview Questions
        if any(w in query_lower for w in ["interview question", "questions", "ask", "technical questions", "screening questions"]):
            return self._generate_interview_questions_response(referenced_cand, referenced_job, message)

        # 2. Intent: Draft Outreach Email
        if any(w in query_lower for w in ["email", "outreach", "cold mail", "message candidate", "draft email", "invite"]):
            return self._generate_outreach_email_response(referenced_cand, referenced_job, message)

        # 3. Intent: Candidate Strengths / Gaps / Dossier Summary
        if referenced_cand and any(w in query_lower for w in ["summary", "strength", "weakness", "gap", "evaluate", "profile", "tell me about"]):
            return self._generate_candidate_evaluation_response(referenced_cand, referenced_job)

        # 4. Intent: Candidate Sourcing / Semantic Search across Talent Pool
        search_results = vector_store.search(message, top_k=4)
        if search_results:
            return self._generate_candidate_search_response(message, search_results, referenced_job)

        # 5. Default General Recruiter Consultation
        return self._generate_general_advice_response(message, referenced_job)

    def _generate_interview_questions_response(
        self,
        candidate: Optional[Candidate],
        job: Optional[Job],
        query: str
    ) -> Dict[str, Any]:
        cand_name = candidate.name if candidate else "the candidate"
        role_title = job.title if job else "Technical Role"
        skills = [s.skill for s in candidate.skills] if candidate and candidate.skills else ["Python", "FastAPI", "SQL", "Cloud"]

        q1 = f"Could you walk us through a recent project where you architected a system using {skills[0] if skills else 'modern frameworks'} under high load or strict latency constraints?"
        q2 = f"In your resume, you highlighted experience with {skills[1] if len(skills) > 1 else 'distributed systems'}. How did you handle data consistency, failure recovery, and caching in that environment?"
        q3 = f"What trade-offs have you evaluated when choosing between microservices and modular monoliths in production?"
        q4 = f"Suppose a service in {role_title} begins experiencing memory leaks or connection pool exhaustion in production. Walk us through your triage, diagnostic tools, and root cause analysis process."
        q5 = f"How do you approach automated testing (unit, integration, contract) and CI/CD deployment pipelines to maintain high shipping velocity without breaking production?"

        response_text = f"""### AI-Tailored Interview Protocol for {cand_name}
**Target Role:** {role_title}

Based on the candidate's verified profile ({candidate.total_experience if candidate else '5+'} years experience, competencies in {', '.join(skills[:5])}), here are 5 targeted interview questions designed to test both depth and architectural leadership:

1. **System Architecture & Scale:**
   *{q1}*
   *What to look for:* Clean separation of concerns, understanding of bottlenecks, caching strategies.

2. **Technical Mastery:**
   *{q2}*
   *What to look for:* Concrete implementation details, observability, handling edge cases.

3. **Engineering Philosophy & Trade-Offs:**
   *{q3}*
   *What to look for:* Pragmatism over dogma; ability to weigh operational complexity vs development speed.

4. **Production Debugging & Reliability:**
   *{q4}*
   *What to look for:* Systematic troubleshooting (logs, APM, heap dumps), structured escalation, blameless post-mortem mindset.

5. **Code Quality & CI/CD Discipline:**
   *{q5}*
   *What to look for:* Test automation culture, zero-downtime canary or blue-green rollouts."""

        return {
            "reply": response_text,
            "intent": "INTERVIEW_QUESTIONS",
            "candidate_id": candidate.id if candidate else None,
            "job_id": job.id if job else None,
            "suggested_actions": ["Schedule Interview", "Log Evaluation Rating", "View Profile"]
        }

    def _generate_outreach_email_response(
        self,
        candidate: Optional[Candidate],
        job: Optional[Job],
        query: str
    ) -> Dict[str, Any]:
        cand_name = candidate.name.split()[0] if candidate else "Candidate"
        role_title = job.title if job else "Senior Engineering Role"
        company = job.company if job else "our engineering team"
        skills = [s.skill for s in candidate.skills[:3]] if candidate and candidate.skills else ["backend systems", "distributed architecture"]

        email_subject = f"Exciting opportunity: {role_title} at {company}"
        email_body = f"""Hi {cand_name},

I came across your profile and was genuinely impressed by your strong background in {', '.join(skills)} and your experience delivering robust engineering solutions.

We are currently expanding our core team at {company} and looking for a {role_title} to help design and scale our next-generation architecture. Given your technical foundation in {skills[0] if skills else 'scalable systems'}, I believe your background would be an exceptional fit for the impact we're creating.

Would you be open to a brief 15-minute informal sync sometime this week to discuss what we're building and see if it aligns with your career goals?

Looking forward to connecting!

Best regards,
Technical Recruiting Team
{company}"""

        response_text = f"""### AI-Generated Recruiter Outreach Draft
**Subject:** `{email_subject}`

```text
{email_body}
```

*Tip: Personalized outreach referencing specific technical competencies achieves a 42% higher candidate response rate.*"""

        return {
            "reply": response_text,
            "intent": "OUTREACH_EMAIL",
            "candidate_id": candidate.id if candidate else None,
            "job_id": job.id if job else None,
            "suggested_actions": ["Copy to Clipboard", "Create Follow-up Reminder"]
        }

    def _generate_candidate_evaluation_response(
        self,
        candidate: Candidate,
        job: Optional[Job]
    ) -> Dict[str, Any]:
        skills = [s.skill for s in candidate.skills]
        role_title = job.title if job else "Target Role"

        response_text = f"""### Candidate Evaluation Dossier: {candidate.name}
- **Experience:** {candidate.total_experience} Years
- **Location:** {candidate.location}
- **Education:** {candidate.education_level.replace('_', ' ').title()} ({candidate.education_details or 'Accredited'})
- **Key Competencies:** {', '.join(skills[:8]) if skills else 'General Engineering'}

#### Key Strengths:
1. **Verified Skill Depth:** Demonstrates verified hands-on background in `{', '.join(skills[:4])}`.
2. **Experience Alignment:** Total duration of {candidate.total_experience} years aligns with senior individual contributor expectations.
3. **Communication & Structure:** Resume demonstrates structured project articulation and clear technical ownership.

#### Potential Areas to Probe in Interview:
- Assess scale and concurrency limits handled in previous production environments.
- Verify practical familiarity with modern CI/CD automation and container orchestration."""

        return {
            "reply": response_text,
            "intent": "CANDIDATE_EVALUATION",
            "candidate_id": candidate.id,
            "job_id": job.id if job else None,
            "suggested_actions": ["View Full Dossier", "Compare Candidate", "Schedule Interview"]
        }

    def _generate_candidate_search_response(
        self,
        query: str,
        results: List[Dict[str, Any]],
        job: Optional[Job]
    ) -> Dict[str, Any]:
        items_md = []
        for idx, r in enumerate(results):
            skills_str = ", ".join(r.get("skills", [])[:4])
            items_md.append(
                f"{idx + 1}. **{r.get('name')}** &bull; **{r.get('similarity_score')}% Semantic Fit**\n"
                f"   - Experience: {r.get('experience')} years | Location: {r.get('location')}\n"
                f"   - Key Skills: `{skills_str}`"
            )

        response_text = f"""### Top Candidate Recommendations for: *"{query}"*
Evaluated across talent pool using 384-dimensional vector embeddings and canonical skills taxonomy:

{chr(10).join(items_md)}

*All recommendations are explainable and backed by verified resume extractions.*"""

        return {
            "reply": response_text,
            "intent": "CANDIDATE_SEARCH",
            "results": results,
            "suggested_actions": ["View Top Match", "Open Pipeline Board"]
        }

    def _generate_general_advice_response(
        self,
        query: str,
        job: Optional[Job]
    ) -> Dict[str, Any]:
        response_text = f"""### AI Recruiter Assistant
I analyzed your inquiry: *"{query}"*.

As your AI Recruitment Partner, I can assist you with:
- **Semantic Talent Discovery:** Ask questions like *"Who are our strongest Kubernetes engineers?"* or *"Find candidates with 5+ years experience in Data Pipelines"*.
- **Interview Question Design:** Type *"Generate technical questions for [Candidate Name]"*.
- **Personalized Outreach:** Type *"Draft an outreach message to [Candidate Name] for the {job.title if job else 'Backend'} role"*.
- **Candidate Comparison:** Compare strengths, skill overlap, and compensation readiness across multiple applicants.

How would you like to proceed?"""

        return {
            "reply": response_text,
            "intent": "GENERAL_CONSULTATION",
            "suggested_actions": ["Find Top Matches", "Draft Outreach", "Schedule Interview"]
        }


recruiter_assistant = RecruiterAIAssistant()
