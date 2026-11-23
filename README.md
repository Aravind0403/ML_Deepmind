# Private ML Command Center — Deep-Path & 4-Stage Interview Studio

A local-first, private Machine Learning Mastery & Staff/Research Interview Readiness platform implementing all 5 pillars:

1. **Overview Dashboard (`/`)** — Unified 5-track Core Syllabus progress (Peak Mastery vs. FSRS Effective Readiness Today) + Target Company Pipelines with countdown pacing.
2. **Core Syllabus — "The Deep-Path" (`/syllabus`)** — De-duplicated 5-track taxonomy, Placement Quiz skipping, Daily Time-Boxed Paths, 150-XP FSRS Spaced Repetition, YouTube IFrame Pause-Checkpoint Lectures (with offline local checkpoint simulator), and sandboxed Coding / Puzzle / SymPy Math / Real-Dataset Lab / Multi-Step Project workspaces.
3. **Interview Studio (`/studio`)** — Private local vault (`private/` + gitignored `db/progress.sqlite`) for your CV, Project War-Room Dossiers, STAR Story Bank, and Target JDs → dynamically generates a strictly gated **4-Stage Gauntlet** (Stage 1 Dual-Zone `CV ∩ JD` & `JD \ CV` → Stage 2 Timed Coding + System Design w/ Mid-Flight Constraint Shift + Deep Knowledge → Stage 3 CV Project Deep-Dive → Stage 4 Seniority-Calibrated Behavioral).
4. **Prep Recap (`/recap/[sessionId]`)** — Strengths Heatmap, 5-Bucket Root-Cause Failure Taxonomy, Attempt Diffing, and one-click Targeted Remediation links (auto-boosting failed concepts 3× in FSRS).
5. **Readiness Score (`/readiness/[targetId]`)** — Strictly locked until all 4 stages complete. Computes 3-Axis Decomposition (`CV Fit × JD Coverage × Execution`), The Delta to the 85% Bar, Per-Stage Hard Floor Veto Gates (`≥ 75%`), Confidence Interval, Go/No-Go Verdict, and a Simulated Hiring Committee Debrief Memo.

## Quick Start

### 1. Verify & Compile Content into Local SQLite
```bash
python3 scripts/build_and_verify.py
```

### 2. Start the FastAPI Backend (Port 8000)
```bash
uvicorn backend.main:app --reload --port 8000
```
*(Optional: copy `.env.example` to `.env` and add `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, or `GEMINI_API_KEY` for live Bar-Raiser LLM grading in Stages 2–4. Without a key, the calibrated offline rubric evaluator works out-of-the-box.)*

### 3. Start the Next.js Frontend (Port 3000)
```bash
cd frontend && npm run dev
```
Open `http://localhost:3000`.

### 4. Run Automated Backend Verification Tests
```bash
pytest -v backend/tests/test_platform.py
```
