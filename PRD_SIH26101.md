# Product Requirements Document (PRD)
## AI-Enabled Competency Gap Learning Platform
**PS Number:** SIH26101 | **Organization:** MoSPI | **Theme:** Smart Education

---

## 1. Problem Statement (as given)
Develop an AI-enabled learning platform that:
- Identifies competency gaps in learners
- Recommends personalized training
- Integrates with the iGOT Karmayogi ecosystem
- Generates Quizzes and MCQs from uploaded learning materials
- Strengthens capacity building in India's Official Statistical System

## 2. Reality Check / Scoping Decision
iGOT Karmayogi is a live, closed government platform — no public API access exists for a 2-day hackathon build. **We will simulate the integration** (a "Sync with iGOT Karmayogi" action that maps a user's gap-analysis result to a mocked catalog of iGOT-style course modules). This is disclosed openly in the pitch as "designed for real iGOT API integration in production; simulated here via a mock adapter for demo purposes." Judges at SIH consistently accept this framing as long as the rest of the pipeline (upload → AI analysis → quiz → recommendation) genuinely works end-to-end.

Everything else in the PS — AI competency gap detection, personalized recommendation, quiz/MCQ generation from uploaded docs — will be **fully functional**, not mocked.

## 3. Goals
1. A working, demoable pipeline: upload material → AI generates quiz → user attempts quiz → system identifies weak competency areas → recommends targeted modules.
2. Basic authentication so the "learner profile" and progress tracking feel real.
3. Clean, presentable React UI — judges see polish as much as function.
4. A FastAPI backend that is simple, well-structured, and easy to demo live (not just slides).

## 4. Non-Goals (explicitly out of scope for 2 days)
- Real iGOT Karmayogi API integration (mocked instead)
- Multi-tenant / admin panel for MoSPI staff
- Advanced analytics dashboards
- Mobile app
- Production-grade security hardening (rate limiting, refresh token rotation, etc.)
- Support for video/audio learning materials (text/PDF only)

## 5. Target User
A government employee or trainee within India's Official Statistical System who needs to upskill against a defined competency framework (e.g., data collection, survey methodology, statistical analysis basics).

## 6. Core User Flow
1. **Sign up / Log in** (basic auth)
2. **Upload learning material** (PDF or pasted text) tagged to a competency area (e.g., "Survey Design")
3. System calls **Gemini API** to generate a 5–10 question MCQ quiz from the material
4. User **attempts the quiz**
5. System scores the attempt and marks the **competency area as Strong / Moderate / Weak** based on score thresholds
6. System shows a **Personalized Recommendation** panel: weak competency areas + a "Recommended Module" card per weak area, sourced from a small mock catalog
7. User clicks **"Sync with iGOT Karmayogi"** → simulated success state shows how the recommended module would map to a real iGOT course code
8. **Dashboard** shows competency radar/bar chart of strong vs weak areas over time (even just 2–3 quiz attempts is enough to demo "over time")

## 7. Feature List (Prioritized for 2-Day Build)

### P0 — Must have (Day 1 core)
- Auth: register/login (JWT-based)
- Upload material (text paste is fine; PDF upload is a stretch goal)
- Gemini-powered MCQ generation from material
- Quiz-taking UI + scoring
- Competency gap logic (rule-based: score < 50% = Weak, 50–75% = Moderate, >75% = Strong)

### P1 — Should have (Day 2 core)
- Recommendation engine (map weak competency → mock course catalog entry)
- Mock "Sync with iGOT Karmayogi" action + response UI
- Dashboard with competency overview (simple bar/radar chart)
- Basic profile page

### P2 — Nice to have (only if time remains)
- PDF text extraction (vs. paste-only)
- Multiple learning materials per competency area
- Retake quiz / progress-over-time chart
- Export competency report as PDF

## 8. Tech Stack
| Layer | Choice |
|---|---|
| Frontend | React (Vite), Axios, React Router, Recharts (for dashboard chart) |
| Backend | FastAPI (Python) |
| Database | MongoDB (via Motor async driver or PyMongo) |
| AI | Google Gemini API (`gemini-1.5-flash` or `gemini-2.0-flash` for speed/cost) |
| Auth | JWT (python-jose) + bcrypt password hashing |
| Hosting (demo) | Local (localhost) is fine for judging; optional: Render/Railway for backend, Vercel for frontend if time allows |

## 9. Data Models (MongoDB Collections)

**users**
```json
{
  "_id": "ObjectId",
  "name": "string",
  "email": "string",
  "password_hash": "string",
  "created_at": "datetime"
}
```

**materials**
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "title": "string",
  "competency_area": "string",
  "raw_text": "string",
  "created_at": "datetime"
}
```

**quizzes**
```json
{
  "_id": "ObjectId",
  "material_id": "ObjectId",
  "questions": [
    {
      "question": "string",
      "options": ["string", "string", "string", "string"],
      "correct_index": 0
    }
  ],
  "created_at": "datetime"
}
```

**quiz_attempts**
```json
{
  "_id": "ObjectId",
  "user_id": "ObjectId",
  "quiz_id": "ObjectId",
  "competency_area": "string",
  "score_percent": 80,
  "gap_level": "Strong | Moderate | Weak",
  "attempted_at": "datetime"
}
```

**course_catalog** (mock iGOT data, seeded manually)
```json
{
  "_id": "ObjectId",
  "competency_area": "string",
  "igot_course_code": "string",
  "course_title": "string",
  "description": "string"
}
```

## 10. API Endpoints (FastAPI)

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/auth/register` | Create user |
| POST | `/auth/login` | Return JWT |
| GET | `/auth/me` | Get current user profile |
| POST | `/materials` | Upload material (text/title/competency_area) |
| GET | `/materials` | List user's materials |
| POST | `/materials/{id}/generate-quiz` | Calls Gemini, generates & stores quiz |
| GET | `/quizzes/{id}` | Fetch quiz questions (without correct answers) |
| POST | `/quizzes/{id}/submit` | Submit answers, returns score + gap_level |
| GET | `/dashboard` | Returns all quiz_attempts + gap summary per competency area |
| GET | `/recommendations` | Returns weak competency areas mapped to course_catalog entries |
| POST | `/recommendations/{competency_area}/sync-igot` | Simulated iGOT sync response |

## 11. Success Criteria for Demo
- [ ] Judge can watch: upload text → AI quiz appears in <10 seconds → take quiz → see instant gap result → see recommendation → click "sync with iGOT" → see confirmation
- [ ] Dashboard shows at least 2 competency areas with different gap levels (Weak/Strong) to prove differentiation works
- [ ] No crashes during the live demo path (this matters more than feature count)
- [ ] Clear 1-slide explanation of what's real vs. simulated (iGOT) for transparency with judges

## 12. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Gemini API rate limits / latency during live demo | Pre-generate and cache a backup quiz for the demo material in case live call fails |
| PDF parsing complexity eats into time | Ship text-paste only for demo; mention PDF as "coming next" |
| MongoDB connection issues at venue (no internet) | Use MongoDB Atlas free tier tested beforehand, or fallback to local `mongod` instance with pre-seeded data |
| Auth complexity slows Day 1 | Use a minimal JWT flow — no email verification, no password reset, no refresh tokens |
