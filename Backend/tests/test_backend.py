import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
def anyio_backend():
    return 'asyncio'

@pytest.mark.anyio
async def test_health_endpoints():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        res1 = await ac.get("/")
        assert res1.status_code == 200
        assert res1.json()["status"] == "online"

        res2 = await ac.get("/health")
        assert res2.status_code == 200
        assert res2.json()["status"] == "healthy"

@pytest.mark.anyio
async def test_end_to_end_backend_workflow():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        import time
        unique_email = f"test_learner_{int(time.time())}@mospi.gov.in"
        
        # 1. Register
        reg_payload = {
            "name": "Aditya Mishra",
            "email": unique_email,
            "password": "SecurePassword123"
        }
        reg_res = await ac.post("/auth/register", json=reg_payload)
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Get Profile
        me_res = await ac.get("/auth/me", headers=headers)
        assert me_res.status_code == 200
        assert me_res.json()["email"] == unique_email
        
        # 3. Upload Learning Material
        mat_payload = {
            "title": "Survey Design and Pre-testing Protocols",
            "competency_area": "Survey Design",
            "raw_text": "Pre-testing questionnaires is a mandatory step in survey design to identify ambiguous questions, routing errors, and non-sampling errors before national scale deployment."
        }
        mat_res = await ac.post("/materials", json=mat_payload, headers=headers)
        assert mat_res.status_code == 201
        material_id = mat_res.json()["_id"]
        
        # 4. Generate Quiz via AI Service
        gen_res = await ac.post(f"/materials/{material_id}/generate-quiz", headers=headers)
        assert gen_res.status_code == 200
        quiz_id = gen_res.json()["quiz_id"]
        
        # 5. Fetch Quiz to Take (Security check: correct_index must be scrubbed)
        quiz_res = await ac.get(f"/quizzes/{quiz_id}", headers=headers)
        assert quiz_res.status_code == 200
        quiz_data = quiz_res.json()
        assert "questions" in quiz_data
        for q in quiz_data["questions"]:
            assert "correct_index" not in q
            assert "explanation" not in q
            
        # 6. Submit Quiz Attempt
        sub_payload = {"answers": [1, 1, 1, 1, 1]}
        sub_res = await ac.post(f"/quizzes/{quiz_id}/submit", json=sub_payload, headers=headers)
        assert sub_res.status_code == 200
        attempt_data = sub_res.json()
        assert "gap_level" in attempt_data
        assert attempt_data["gap_level"] in ["Strong", "Moderate", "Weak"]
        
        # 7. Query Dashboard Analytics
        dash_res = await ac.get("/dashboard", headers=headers)
        assert dash_res.status_code == 200
        dash_data = dash_res.json()
        assert dash_data["total_quizzes_taken"] >= 1
        
        # 8. Recommendation Engine & iGOT Sync
        rec_res = await ac.get("/recommendations", headers=headers)
        assert rec_res.status_code == 200
        
        sync_res = await ac.post("/recommendations/Survey Design/sync-igot", headers=headers)
        assert sync_res.status_code == 200
        assert sync_res.json()["status"] == "synced"
        assert "IGOT-SUR-101" in sync_res.json()["igot_course_code"]
