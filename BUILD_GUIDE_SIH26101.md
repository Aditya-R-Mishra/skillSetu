# Build Guide — SIH26101 (2-Day Plan)
**Stack:** React (Vite) + FastAPI + MongoDB + Google Gemini API + JWT Auth

This guide assumes a team of 3–4: 1–2 on backend, 1–2 on frontend, working in parallel from Hour 1 using an agreed API contract (see PRD section 10).

---

## Day 0 (Before hackathon starts, if possible)
- [ ] Create a **Google AI Studio** account, generate a **Gemini API key** (free tier at ai.google.dev)
- [ ] Create a **MongoDB Atlas** free cluster (or install MongoDB locally as backup), get connection string
- [ ] All members install: Node.js 18+, Python 3.11+, `pip`, `npm`
- [ ] Create a shared GitHub repo with `frontend/` and `backend/` folders

---

## DAY 1 — Core Pipeline (Upload → AI Quiz → Attempt → Gap Detection)

### Hour 0–1: Project Setup
**Backend:**
```bash
mkdir backend && cd backend
python -m venv venv
source venv/bin/activate   # (venv\Scripts\activate on Windows)
pip install fastapi uvicorn motor pymongo python-jose[cryptography] passlib[bcrypt] python-dotenv google-generativeai python-multipart
```
Create `.env`:
```
MONGO_URI=your_mongodb_atlas_connection_string
GEMINI_API_KEY=your_gemini_key
JWT_SECRET=some_random_long_string
```

Folder structure:
```
backend/
  main.py
  database.py
  auth.py
  models.py
  routers/
    auth_router.py
    materials_router.py
    quiz_router.py
    dashboard_router.py
    recommendations_router.py
  services/
    gemini_service.py
```

**Frontend:**
```bash
npm create vite@latest frontend -- --template react
cd frontend
npm install axios react-router-dom recharts
```

Folder structure:
```
frontend/src/
  pages/
    Login.jsx
    Register.jsx
    Upload.jsx
    Quiz.jsx
    Dashboard.jsx
    Recommendations.jsx
  components/
    Navbar.jsx
    QuizQuestion.jsx
    CompetencyCard.jsx
  api/
    client.js   (axios instance with baseURL + JWT header)
  App.jsx
```

### Hour 1–3: Auth (Backend + Frontend in parallel)
**Backend (`auth.py` + `auth_router.py`):**
- `POST /auth/register` — hash password with bcrypt, insert into `users` collection
- `POST /auth/login` — verify password, return JWT (payload: `user_id`, expiry ~24h)
- `GET /auth/me` — dependency-protected route returning current user from JWT
- Create a reusable `get_current_user` FastAPI dependency using `python-jose` to decode JWT from `Authorization: Bearer` header

**Frontend:**
- `Login.jsx` / `Register.jsx` forms → call `/auth/login` and `/auth/register`
- Store JWT in `localStorage` (fine for hackathon demo)
- `api/client.js` axios interceptor auto-attaches `Authorization` header
- Simple `PrivateRoute` wrapper in `App.jsx` to protect authenticated pages

**Milestone check:** Can register, log in, and hit a protected `/auth/me` route successfully.

### Hour 3–5: Material Upload + Gemini Quiz Generation
**Backend (`services/gemini_service.py`):**
```python
import google.generativeai as genai
import os, json

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel("gemini-2.0-flash")

def generate_mcqs(text: str, num_questions: int = 6):
    prompt = f"""
    You are an assessment generator. Read the learning material below and generate
    {num_questions} multiple-choice questions testing understanding of the content.
    Return ONLY valid JSON, no markdown, no explanation, in this exact schema:
    [
      {{"question": "...", "options": ["A", "B", "C", "D"], "correct_index": 0}}
    ]

    Material:
    \"\"\"{text}\"\"\"
    """
    response = model.generate_content(prompt)
    cleaned = response.text.strip().replace("```json", "").replace("```", "")
    return json.loads(cleaned)
```

**Backend (`materials_router.py`):**
- `POST /materials` — save `title`, `competency_area`, `raw_text` under current user
- `POST /materials/{id}/generate-quiz` — fetch material, call `generate_mcqs()`, store result in `quizzes` collection linked to `material_id`, return quiz `_id`

**Frontend (`Upload.jsx`):**
- Simple form: Title, Competency Area (dropdown: e.g. "Survey Design", "Data Analysis", "Field Methodology"), Text Area for material (paste-in for demo speed)
- On submit → `POST /materials` → then immediately `POST /materials/{id}/generate-quiz` → redirect to `Quiz.jsx` with quiz ID
- Show a loading state ("Generating your quiz with AI...") since Gemini call takes a few seconds

**Milestone check:** Paste a paragraph of text, hit submit, and a real AI-generated quiz JSON comes back and renders.

### Hour 5–7: Quiz Attempt + Gap Scoring Logic
**Backend (`quiz_router.py`):**
- `GET /quizzes/{id}` — return questions + options WITHOUT `correct_index` (don't leak answers to frontend)
- `POST /quizzes/{id}/submit` — accept `{answers: [selected_index, ...]}`, compare server-side against stored `correct_index`, compute `score_percent`
- Gap logic:
```python
def gap_level(score_percent: float) -> str:
    if score_percent >= 75:
        return "Strong"
    elif score_percent >= 50:
        return "Moderate"
    return "Weak"
```
- Store result in `quiz_attempts` collection (user_id, competency_area, score_percent, gap_level, attempted_at)

**Frontend (`Quiz.jsx`):**
- Fetch quiz, render one question at a time or all at once (all-at-once is faster to build)
- Radio buttons per question, "Submit Quiz" button
- On submit, show immediate result screen: score %, gap level badge (color-coded: red=Weak, yellow=Moderate, green=Strong)

**Milestone check:** Full loop works — upload → quiz → answer → see your gap level. **This is your Day 1 demo-safe checkpoint.** If nothing else gets built, this alone is a working MVP.

### Hour 7–8: Seed Mock Course Catalog + Buffer
- Manually insert 5–8 documents into `course_catalog` collection covering competency areas you plan to demo (e.g. "Survey Design" → "IGOT-SD-101: Advanced Survey Methodology")
- Use this hour as buffer for whatever ran over

---

## DAY 2 — Recommendations, iGOT Simulation, Dashboard, Polish

### Hour 0–2: Recommendation Engine + iGOT Sync Simulation
**Backend (`recommendations_router.py`):**
- `GET /recommendations` — query `quiz_attempts` for current user, find all with `gap_level = "Weak"` or `"Moderate"`, join against `course_catalog` by `competency_area`, return list of `{competency_area, gap_level, recommended_course}`
- `POST /recommendations/{competency_area}/sync-igot` — simulated response:
```python
@router.post("/recommendations/{competency_area}/sync-igot")
def sync_igot(competency_area: str):
    # Simulated adapter — in production this would call the real iGOT Karmayogi API
    return {
        "status": "synced",
        "igot_course_code": f"IGOT-{competency_area[:3].upper()}-101",
        "message": f"Enrollment request sent to iGOT Karmayogi for {competency_area}."
    }
```

**Frontend (`Recommendations.jsx`):**
- List cards per weak/moderate competency area with course title + "Sync with iGOT Karmayogi" button
- On click → call sync endpoint → show success toast/badge with returned course code

### Hour 2–4: Dashboard
**Backend (`dashboard_router.py`):**
- `GET /dashboard` — aggregate all `quiz_attempts` for user, group by `competency_area`, return latest `gap_level` and `score_percent` per area

**Frontend (`Dashboard.jsx`):**
- Use **Recharts** to render a bar chart: competency area (x-axis) vs score_percent (y-axis), color bars by gap_level
- Add a summary row of cards: total quizzes taken, weak areas count, strong areas count

### Hour 4–6: UI Polish
- Add a clean `Navbar.jsx` with logo/name, nav links, logout button
- Consistent color scheme (pick 2–3 brand colors, e.g. govt-appropriate navy blue + white + accent teal)
- Loading spinners, error toasts, empty states ("No materials uploaded yet")
- Make sure mobile/laptop demo screen looks presentable (judges often view on a laptop screen or projector)

### Hour 6–7: PDF Upload (Stretch Goal, P2)
- Only attempt if Day 1 milestones were hit on time
- Backend: use `pypdf` to extract text from uploaded PDF before passing to `generate_mcqs()`
- Frontend: swap text area for file input in `Upload.jsx`

### Hour 7–8: End-to-End Test + Demo Script Rehearsal
- [ ] Test the full flow fresh (new user, new material, new quiz) at least twice
- [ ] Pre-generate and cache 1–2 backup quizzes in the database in case live Gemini call fails during judging (edge-case safety net)
- [ ] Prepare a 2-minute live demo script: Register → Upload material → Generate quiz live → Attempt → Show gap result → Show recommendation → Sync iGOT → Show dashboard
- [ ] Prepare 1 slide clarifying: "iGOT Karmayogi integration is simulated via a mock adapter for this POC; architecture is built to plug into the real iGOT API in production"
- [ ] Charge laptops, test venue Wi-Fi/hotspot for Gemini API + MongoDB Atlas access, have a local MongoDB fallback if internet is unreliable

---

## Quick Reference: Environment Variables
**backend/.env**
```
MONGO_URI=...
GEMINI_API_KEY=...
JWT_SECRET=...
```

**frontend/.env**
```
VITE_API_BASE_URL=http://localhost:8000
```

## Quick Reference: Run Commands
```bash
# Backend
cd backend && uvicorn main:app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

## Priority Order If Time Runs Short
1. Auth + Upload + Gemini Quiz Generation + Quiz Attempt + Gap Scoring (Day 1 core) — **never skip this**
2. Recommendations list (even without iGOT sync button)
3. Dashboard chart
4. iGOT sync simulation button
5. PDF upload
6. UI polish beyond basic styling
