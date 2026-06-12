from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from services.evaluator import evaluate_solution
from services.analytics import (
    get_streak_info, get_weakness_report, get_next_recommended_problems,
    get_mentor_message, get_leaderboard, get_thinker_level,
    get_thinking_patterns, get_user_achievements,
    get_daily_challenge, is_daily_completed, get_learning_path,
    score_reflection, LEARNING_PATHS
)
from utils.problem_loader import load_problems, get_problem_by_id, get_problems_by_topic, get_problems_by_difficulty
from database import create_tables, get_connection
from model.data_collector import get_unlabeled_samples, manual_label, get_stats
from model.inference import get_model_info

app = FastAPI(title="ThinkCode AI", version="4.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
create_tables()

# Auto-train on startup if model missing
from model.auto_trainer import startup_train_if_needed, get_training_status
startup_train_if_needed()

class SubmitRequest(BaseModel):
    problem_id: str
    user_code: str
    thinking_text: str = ""
    user_id: str = "guest"
    display_name: str = "Anonymous"

class ReflectionRequest(BaseModel):
    question: str
    answer: str

class LabelRequest(BaseModel):
    sample_id: str
    thinking_score: int
    approach: str
    notes: str = ""

class TrainRequest(BaseModel):
    epochs: int = 150
    seed_only: bool = False

# ── Core ──────────────────────────────────────────────────────────────────────
@app.get("/")
def home():
    return {"message": "ThinkCode AI v4.0 — Train Your Thinking"}

@app.get("/problems/")
def get_problems(topic: Optional[str]=None, difficulty: Optional[str]=None, company: Optional[str]=None):
    problems = load_problems()
    result = list(problems.values())
    if topic:      result = [p for p in result if p["topic"] == topic]
    if difficulty: result = [p for p in result if p["difficulty"] == difficulty]
    if company:    result = [p for p in result if company in p.get("companies", [])]
    return result

@app.get("/problem/{problem_id}")
def get_problem(problem_id: str):
    p = get_problem_by_id(problem_id)
    if not p: raise HTTPException(status_code=404, detail="Problem not found")
    return p

@app.post("/submit/")
def submit_solution(body: SubmitRequest):
    problem = get_problem_by_id(body.problem_id)
    if not problem: raise HTTPException(status_code=404, detail="Problem not found")
    return evaluate_solution(problem, body.user_code, body.thinking_text, body.user_id)

@app.post("/score-reflection/")
def score_reflection_endpoint(body: ReflectionRequest):
    return score_reflection(body.question, body.answer)

# ── Analytics ─────────────────────────────────────────────────────────────────
@app.get("/streak/")
def streak(user_id: str = "guest"):
    return get_streak_info(user_id)

@app.get("/weakness/")
def weakness(user_id: str = "guest"):
    return get_weakness_report(user_id)

@app.get("/mentor/")
def mentor(user_id: str = "guest"):
    return get_mentor_message(user_id)

@app.get("/recommended/")
def recommended(user_id: str = "guest"):
    return get_next_recommended_problems(user_id, load_problems())

@app.get("/leaderboard/")
def leaderboard(limit: int = 10):
    return get_leaderboard(limit)

@app.get("/history/")
def history(user_id: str = "guest", limit: int = 20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT problem_id, thinking_score, code_score, passed, total,
               topic, difficulty, code_approach, submitted_at
               FROM submissions WHERE user_id=? ORDER BY submitted_at DESC LIMIT ?""", (user_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/patterns/")
def patterns(user_id: str = "guest"):
    return get_thinking_patterns(user_id)

@app.get("/achievements/")
def achievements(user_id: str = "guest"):
    return get_user_achievements(user_id)

@app.get("/daily-challenge/")
def daily_challenge(user_id: str = "guest"):
    problems = load_problems()
    challenge = get_daily_challenge(problems)
    challenge["completed"] = is_daily_completed(user_id, challenge["id"])
    return challenge

@app.get("/learning-path/{path_id}")
def learning_path(path_id: str, user_id: str = "guest"):
    problems = load_problems()
    path = get_learning_path(path_id, problems, user_id)
    if not path: raise HTTPException(status_code=404, detail="Path not found")
    return path

@app.get("/learning-paths/")
def all_learning_paths():
    return [{"id": k, "title": v["title"], "desc": v["desc"]} for k, v in LEARNING_PATHS.items()]

@app.get("/dashboard/")
def dashboard(user_id: str = "guest"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as count FROM submissions WHERE user_id=?", (user_id,))
    total = c.fetchone()["count"]
    c.execute("SELECT AVG(thinking_score) as avg FROM submissions WHERE user_id=?", (user_id,))
    avg_t = round(c.fetchone()["avg"] or 0, 1)
    c.execute("SELECT AVG(code_score) as avg FROM submissions WHERE user_id=?", (user_id,))
    avg_c = round(c.fetchone()["avg"] or 0, 1)
    c.execute("SELECT topic, COUNT(*) as count, AVG(thinking_score) as avg_score FROM submissions WHERE user_id=? GROUP BY topic", (user_id,))
    topics = [dict(r) for r in c.fetchall()]
    conn.close()
    level = get_thinker_level(avg_t)
    return {"total_submissions": total, "average_thinking_score": avg_t,
            "average_code_score": avg_c, "topics": topics, "thinker_level": level}

@app.get("/companies/")
def get_companies():
    problems = load_problems()
    companies = set()
    for p in problems.values(): companies.update(p.get("companies", []))
    return sorted(list(companies))

@app.get("/stats/")
def get_stats_route():
    problems = load_problems()
    by_diff, by_topic = {}, {}
    for p in problems.values():
        by_diff[p["difficulty"]] = by_diff.get(p["difficulty"], 0) + 1
        by_topic[p["topic"]] = by_topic.get(p["topic"], 0) + 1
    return {"total_problems": len(problems), "by_difficulty": by_diff, "by_topic": by_topic}

# ── Admin ─────────────────────────────────────────────────────────────────────
@app.get("/admin/stats/")
def admin_stats():
    return {**get_stats(), **get_model_info()}

@app.get("/admin/unlabeled/")
def admin_unlabeled(limit: int = 20):
    return get_unlabeled_samples(limit)

@app.post("/admin/label/")
def admin_label(body: LabelRequest):
    manual_label(body.sample_id, body.thinking_score, body.approach, body.notes)
    return {"success": True}

@app.post("/admin/train/")
def admin_train(body: TrainRequest):
    import threading
    def run():
        from model.trainer import train
        train(epochs=body.epochs, seed_only=body.seed_only)
    threading.Thread(target=run, daemon=True).start()
    return {"success": True, "message": f"Training started — {body.epochs} epochs"}

# ── XP & Evolution ────────────────────────────────────────────────────────────
from services.analytics import (
    get_user_xp, get_weakness_evolution, get_thinking_replay
)
from database import add_xp_tables as _add_xp

# Create XP tables
try:
    _add_xp()
except:
    pass

@app.get("/xp/")
def xp(user_id: str = "guest"):
    return get_user_xp(user_id)

@app.get("/weakness-evolution/")
def weakness_evolution(user_id: str = "guest"):
    return get_weakness_evolution(user_id)

@app.get("/thinking-replay/")
def thinking_replay(user_id: str = "guest", problem_id: str = "two_sum"):
    return get_thinking_replay(user_id, problem_id)


# ── Reflection & Interview Score Tracking ─────────────────────────────────────
class SaveScoreRequest(BaseModel):
    user_id: str = "guest"
    problem_id: str = "unknown"
    avg_score: int = 0
    score_type: str = "reflection"  # "reflection" or "interview"

@app.post("/save-score/")
def save_score(body: SaveScoreRequest):
    conn = get_connection()
    c = conn.cursor()
    if body.score_type == "reflection":
        c.execute("""INSERT INTO reflection_scores (user_id, problem_id, avg_score)
                      VALUES (?, ?, ?)""", (body.user_id, body.problem_id, body.avg_score))
    else:
        c.execute("""INSERT INTO interview_scores (user_id, problem_id, avg_score)
                      VALUES (?, ?, ?)""", (body.user_id, body.problem_id, body.avg_score))
    conn.commit()
    conn.close()
    return {"success": True}

@app.get("/reflection-trend/")
def reflection_trend(user_id: str = "guest", limit: int = 20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT problem_id, avg_score, scored_at
                  FROM reflection_scores WHERE user_id=?
                  ORDER BY scored_at DESC LIMIT ?""", (user_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/interview-trend/")
def interview_trend(user_id: str = "guest", limit: int = 20):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT problem_id, avg_score, scored_at
                  FROM interview_scores WHERE user_id=?
                  ORDER BY scored_at DESC LIMIT ?""", (user_id, limit))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

@app.get("/cognitive-report/")
def cognitive_report(user_id: str = "guest"):
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT AVG(thinking_score) as avg, COUNT(*) as cnt FROM submissions WHERE user_id=?", (user_id,))
    row = c.fetchone()
    avg_thinking = round(row["avg"] or 0, 1)
    total_subs   = row["cnt"] or 0

    c.execute("SELECT AVG(code_score) as avg FROM submissions WHERE user_id=?", (user_id,))
    avg_code = round(c.fetchone()["avg"] or 0, 1)

    c.execute("SELECT AVG(avg_score) as avg FROM reflection_scores WHERE user_id=?", (user_id,))
    avg_reflection = round(c.fetchone()["avg"] or 0, 1)

    c.execute("SELECT AVG(avg_score) as avg FROM interview_scores WHERE user_id=?", (user_id,))
    avg_interview = round(c.fetchone()["avg"] or 0, 1)

    c.execute("SELECT COUNT(*) as cnt FROM user_achievements WHERE user_id=?", (user_id,))
    achievements = c.fetchone()["cnt"] or 0

    conn.close()

    # Overall cognitive score
    scores = [s for s in [avg_thinking, avg_code, avg_reflection, avg_interview] if s > 0]
    overall = round(sum(scores) / len(scores), 1) if scores else 0

    grade = "S" if overall >= 90 else "A" if overall >= 80 else "B" if overall >= 70 else "C" if overall >= 60 else "D" if overall >= 40 else "F"

    return {
        "overall_score":    overall,
        "grade":            grade,
        "thinking_score":   avg_thinking,
        "code_score":       avg_code,
        "reflection_score": avg_reflection,
        "interview_score":  avg_interview,
        "total_submissions": total_subs,
        "achievements":     achievements,
    }


@app.get("/training-status/")
def training_status():
    return get_training_status()