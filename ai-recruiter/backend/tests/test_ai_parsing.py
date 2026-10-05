import sys
import os
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from app.main import app
from app.ai.normalizer import skill_normalizer
from app.ai.parser import resume_parser
from app.ai.jd_parser import jd_parser


def test_skill_normalizer():
    # Direct alias lookups
    assert skill_normalizer.normalize("py") == "Python"
    assert skill_normalizer.normalize("python3") == "Python"
    assert skill_normalizer.normalize("k8s") == "Kubernetes"
    assert skill_normalizer.normalize("ReactJS") == "React"
    assert skill_normalizer.normalize("react.js") == "React"
    assert skill_normalizer.normalize("postgres") == "PostgreSQL"
    assert skill_normalizer.normalize("postgresql") == "PostgreSQL"
    assert skill_normalizer.normalize("springboot") == "Spring Boot"
    assert skill_normalizer.normalize("amazon web services") == "AWS"
    assert skill_normalizer.normalize("golang") == "Go"
    assert skill_normalizer.normalize("ts") == "TypeScript"

    # Fuzzy typo handling
    assert skill_normalizer.normalize("PostgreSQ") == "PostgreSQL"


def test_resume_parser_sections():
    resume_text = """
    Christopher Pike
    cpike@enterprise.org | (415) 555-8833 | San Francisco, CA

    SUMMARY
    Accomplished Senior Cloud Architect with 6+ years of experience designing scalable microservices.

    EXPERIENCE
    Lead Infrastructure Architect (2020 - Present)
    - Architected Kubernetes deployments on AWS with Terraform.
    Senior DevOps Engineer (2018 - 2020)
    - Built Docker containers and CI/CD pipelines.

    EDUCATION
    Master of Science in Computer Science
    Starfleet Institute of Technology, 2018

    SKILLS
    Python, Kubernetes, Docker, AWS, Terraform, CI/CD, Linux, Prometheus
    """

    parsed = resume_parser.parse_resume(resume_text, "christopher_pike.txt")
    assert parsed.name == "Christopher Pike"
    assert parsed.email == "cpike@enterprise.org"
    assert parsed.total_experience >= 5.0
    assert parsed.education_level == "MASTERS"
    assert len(parsed.skills) >= 6
    skill_names = [s["skill"] for s in parsed.skills]
    assert "Kubernetes" in skill_names
    assert "Python" in skill_names
    assert "Docker" in skill_names
    assert "AWS" in skill_names


def test_jd_parser_classification():
    jd_text = """
    Job Title: Senior Python & Cloud Backend Engineer
    Company: CloudInnovate
    Location: Remote
    Experience: 3-6 years

    Role Overview:
    We are seeking an engineer to build distributed services.

    Required Skills:
    - Python programming and FastAPI
    - PostgreSQL database design
    - Docker containerization

    Preferred Skills:
    - AWS cloud deployment
    - Kubernetes orchestration
    - Redis caching
    """

    parsed = jd_parser.parse_jd(jd_text)
    assert "Python" in parsed.title
    assert parsed.experience_min == 3.0
    assert parsed.experience_max == 6.0

    required_skills = [s.skill for s in parsed.skills if s.required]
    preferred_skills = [s.skill for s in parsed.skills if not s.required]

    assert "Python" in required_skills
    assert "FastAPI" in required_skills
    assert "PostgreSQL" in required_skills
    assert "Docker" in required_skills

    assert "AWS" in preferred_skills
    assert "Kubernetes" in preferred_skills
    assert "Redis" in preferred_skills


def test_ai_skills_endpoints():
    with TestClient(app) as client:
        # 1. Login
        login_res = client.post("/api/v1/auth/login", json={
            "email": "recruiter@smartrecruit.ai",
            "password": "Recruiter@123456"
        })
        token = login_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Test Skill Normalization API
        norm_res = client.post(
            "/api/v1/ai/skills/normalize",
            json={"skills": ["py", "k8s", "react.js", "postgres", "aws"]},
            headers=headers
        )
        assert norm_res.status_code == 200
        canonicals = [item["canonical"] for item in norm_res.json()["normalized"]]
        assert "Python" in canonicals
        assert "Kubernetes" in canonicals
        assert "React" in canonicals
        assert "PostgreSQL" in canonicals
        assert "AWS" in canonicals

        # 3. Test Taxonomy API
        tax_res = client.get("/api/v1/ai/skills/taxonomy", headers=headers)
        assert tax_res.status_code == 200
        assert tax_res.json()["total_canonical_skills"] > 20

        # 4. Test JD Parse API
        jd_res = client.post(
            "/api/v1/ai/parse-jd",
            json={"text": "Software Engineer with 4+ years of experience in Java, Spring Boot, and Kafka."},
            headers=headers
        )
        assert jd_res.status_code == 200
        parsed_jd = jd_res.json()
        assert any(s["skill"] == "Java" for s in parsed_jd["skills"])
        assert any(s["skill"] == "Spring Boot" for s in parsed_jd["skills"])
