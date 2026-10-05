import urllib.request
import json

base_url = "http://127.0.0.1:8000/api/v1"

# 1. Login
login_payload = json.dumps({"email": "recruiter@smartrecruit.ai", "password": "Recruiter@123456"}).encode("utf-8")
req = urllib.request.Request(f"{base_url}/auth/login", data=login_payload, headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))
    token = data["access_token"]
    user = data["user"]
    print(f"Logged in as: {user['name']} ({user['email']})")

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

# 2. Check Jobs
jobs_req = urllib.request.Request(f"{base_url}/jobs", headers=headers)
with urllib.request.urlopen(jobs_req) as resp:
    jobs = json.loads(resp.read().decode("utf-8"))

if len(jobs) == 0:
    print("Seeding 5 realistic technical job requisitions...")
    seed_j_req = urllib.request.Request(f"{base_url}/jobs/seed", data=b"{}", headers=headers)
    urllib.request.urlopen(seed_j_req)

# 3. Check Candidates
cands_req = urllib.request.Request(f"{base_url}/candidates", headers=headers)
with urllib.request.urlopen(cands_req) as resp:
    candidates = json.loads(resp.read().decode("utf-8"))

if len(candidates) == 0:
    print("Seeding 20 realistic technical candidates...")
    seed_c_req = urllib.request.Request(f"{base_url}/candidates/seed", data=b"{}", headers=headers)
    urllib.request.urlopen(seed_c_req)

print("Seeding 8-stage recruitment pipeline & calculating match matrices...")
seed_pipe_req = urllib.request.Request(f"{base_url}/pipeline/seed", data=b"{}", headers=headers)
urllib.request.urlopen(seed_pipe_req)

print("Building FAISS vector index for local semantic search...")
seed_vec_req = urllib.request.Request(f"{base_url}/ai/assistant/reindex-vectors", data=b"{}", headers=headers)
urllib.request.urlopen(seed_vec_req)

# Refresh counts
with urllib.request.urlopen(jobs_req) as resp:
    jobs = json.loads(resp.read().decode("utf-8"))
    print(f"\nTotal Live Jobs: {len(jobs)}")
    for j in jobs[:5]:
        print(f"  • {j['title']} at {j['company']} ({j['location']})")

with urllib.request.urlopen(cands_req) as resp:
    candidates = json.loads(resp.read().decode("utf-8"))
    print(f"\nTotal Live Candidates: {len(candidates)}")
    for c in candidates[:5]:
        print(f"  • {c['name']} ({c['total_experience']} yrs exp, {c['education_level']})")

# 4. Get Analytics
analytics_req = urllib.request.Request(f"{base_url}/analytics/overview", headers=headers)
with urllib.request.urlopen(analytics_req) as resp:
    analytics = json.loads(resp.read().decode("utf-8"))
    print(f"\nAnalytics Pipeline Overview:")
    print(f"  • Active Jobs: {analytics['active_jobs']}")
    print(f"  • Candidates in Talent Pool: {analytics['total_candidates']}")
    print(f"  • Applications Evaluated: {analytics['total_applications']}")
    print(f"  • Candidates Hired: {analytics['hired_count']}")
    print(f"  • Average Match Score: {analytics['average_match_score']}%")

print("\n>>> ALL LIVE SERVICES, PIPELINE STAGES, AND FAISS VECTORS ARE PRIMED & OPERATIONAL! <<<")
