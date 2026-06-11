"""
ThinkCode AI — Analytics Engine
Handles: Streak, Weakness Detection, Adaptive Difficulty, Mentor Memory, Leaderboard
"""

import json
from datetime import datetime, date, timedelta
from database import get_connection

USER_ID = "guest"  # When auth added, replace with real user_id


# ── Streak System ─────────────────────────────────────────────────────────────

def update_streak(user_id=USER_ID):
    """Call this after every successful submission."""
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()

    c.execute("""
        INSERT INTO streaks (user_id, date, problems_solved)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, date)
        DO UPDATE SET problems_solved = problems_solved + 1
    """, (user_id, today))
    conn.commit()
    conn.close()


def get_streak_info(user_id=USER_ID) -> dict:
    conn = get_connection()
    c = conn.cursor()

    # Get all dates with activity, sorted
    c.execute("SELECT date FROM streaks WHERE user_id=? ORDER BY date DESC", (user_id,))
    dates = [row["date"] for row in c.fetchall()]
    conn.close()

    if not dates:
        return {"current_streak": 0, "longest_streak": 0, "total_active_days": 0, "today_solved": False, "heatmap": []}

    # Current streak
    today = date.today()
    current = 0
    check = today
    date_set = set(dates)
    while check.isoformat() in date_set:
        current += 1
        check -= timedelta(days=1)

    # Longest streak
    longest = 0
    streak = 1
    date_objs = sorted([date.fromisoformat(d) for d in date_set])
    for i in range(1, len(date_objs)):
        if (date_objs[i] - date_objs[i-1]).days == 1:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 1
    longest = max(longest, streak)

    # Heatmap (last 30 days)
    heatmap = []
    for i in range(29, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        heatmap.append({"date": d, "active": d in date_set})

    return {
        "current_streak": current,
        "longest_streak": longest,
        "total_active_days": len(date_set),
        "today_solved": today.isoformat() in date_set,
        "heatmap": heatmap
    }


# ── Weakness Detection ────────────────────────────────────────────────────────

def get_weakness_report(user_id=USER_ID) -> dict:
    """Analyze submissions to find weak and strong topics."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT topic, difficulty,
               COUNT(*) as attempts,
               AVG(thinking_score) as avg_thinking,
               AVG(code_score) as avg_code,
               SUM(CASE WHEN passed=total AND total>0 THEN 1 ELSE 0 END) as solves
        FROM submissions
        WHERE user_id=?
        GROUP BY topic, difficulty
    """, (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    if not rows:
        return {"weak_topics": [], "strong_topics": [], "topic_stats": [], "suggestions": []}

    # Classify topics
    weak, strong, topic_stats = [], [], []
    for r in rows:
        avg_t = r["avg_thinking"] or 0
        avg_c = r["avg_code"] or 0
        combined = (avg_t + avg_c) / 2
        r["combined_score"] = round(combined, 1)

        topic_stats.append(r)

        if combined < 40:
            weak.append(r["topic"])
        elif combined >= 70:
            strong.append(r["topic"])

    suggestions = []
    for topic in set(weak):
        suggestions.append(f"Practice more {topic} problems — your thinking score is low here")
    for topic in set(strong):
        suggestions.append(f"Great work on {topic}! Try harder difficulty next")

    return {
        "weak_topics": list(set(weak)),
        "strong_topics": list(set(strong)),
        "topic_stats": topic_stats,
        "suggestions": suggestions
    }


# ── Adaptive Difficulty ───────────────────────────────────────────────────────

def get_next_recommended_problems(user_id=USER_ID, problems: dict = None) -> list:
    """
    Recommend next problems based on:
    - Unsolved problems
    - Weak topics first
    - Progressive difficulty
    """
    if not problems:
        return []

    conn = get_connection()
    c = conn.cursor()

    # Problems already solved (passed all tests)
    c.execute("""
        SELECT DISTINCT problem_id FROM submissions
        WHERE user_id=? AND passed=total AND total>0
    """, (user_id,))
    solved_ids = {r["problem_id"] for r in c.fetchall()}

    # Avg score per difficulty
    c.execute("""
        SELECT difficulty, AVG(thinking_score) as avg
        FROM submissions WHERE user_id=?
        GROUP BY difficulty
    """, (user_id,))
    diff_scores = {r["difficulty"]: r["avg"] or 0 for r in c.fetchall()}
    conn.close()

    # Determine appropriate difficulty
    easy_avg  = diff_scores.get("easy", 0)
    med_avg   = diff_scores.get("medium", 0)
    target_diff = "easy"
    if easy_avg >= 60:
        target_diff = "medium"
    if med_avg >= 60:
        target_diff = "hard"

    weakness = get_weakness_report(user_id)
    weak_topics = weakness["weak_topics"]

    # Score and sort problems
    scored = []
    for pid, p in problems.items():
        if pid in solved_ids:
            continue
        score = 0
        if p["difficulty"] == target_diff:
            score += 30
        elif p["difficulty"] == "easy" and target_diff == "medium":
            score += 10
        if p["topic"] in weak_topics:
            score += 20
        scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:5]]


# ── AI Mentor Memory ──────────────────────────────────────────────────────────

def update_mentor_memory(user_id=USER_ID):
    """Update mentor memory after each submission."""
    weakness = get_weakness_report(user_id)
    streak   = get_streak_info(user_id)

    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT AVG(thinking_score) as avg, COUNT(*) as cnt FROM submissions WHERE user_id=?", (user_id,))
    row = c.fetchone()
    avg_score = round(row["avg"] or 0, 1)
    total     = row["cnt"] or 0

    c.execute("""
        INSERT INTO mentor_memory (user_id, weak_topics, strong_topics, avg_thinking_score, total_submissions)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            weak_topics=excluded.weak_topics,
            strong_topics=excluded.strong_topics,
            avg_thinking_score=excluded.avg_thinking_score,
            total_submissions=excluded.total_submissions,
            last_updated=CURRENT_TIMESTAMP
    """, (
        user_id,
        json.dumps(weakness["weak_topics"]),
        json.dumps(weakness["strong_topics"]),
        avg_score, total
    ))
    conn.commit()
    conn.close()


def get_mentor_message(user_id=USER_ID) -> dict:
    """Generate a personalized mentor message for the user."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM mentor_memory WHERE user_id=?", (user_id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return {
            "message": "Welcome to ThinkCode AI! Start solving problems to get personalized coaching.",
            "tips": ["Begin with easy Array problems", "Always explain your thinking before coding"]
        }

    weak   = json.loads(row["weak_topics"] or "[]")
    strong = json.loads(row["strong_topics"] or "[]")
    avg    = row["avg_thinking_score"] or 0
    total  = row["total_submissions"] or 0
    streak = get_streak_info(user_id)

    # Build message
    parts = []
    if streak["current_streak"] >= 3:
        parts.append(f"🔥 {streak['current_streak']}-day streak! Keep it up!")
    if avg >= 70:
        parts.append(f"Your thinking score avg is {avg}/100 — excellent reasoning!")
    elif avg >= 40:
        parts.append(f"Thinking score avg: {avg}/100 — you're improving!")
    else:
        parts.append(f"Focus on explaining your approach before coding — it will raise your score.")

    tips = []
    if weak:
        tips.append(f"Work on {', '.join(weak[:2])} — these are your weak areas")
    if strong:
        tips.append(f"You're great at {', '.join(strong[:2])} — try harder problems here")
    if total < 5:
        tips.append("Solve at least 5 problems to unlock full personalized insights")

    return {
        "message": " ".join(parts),
        "tips": tips,
        "avg_score": avg,
        "total_solved": total,
        "streak": streak["current_streak"]
    }


# ── Leaderboard ───────────────────────────────────────────────────────────────

def update_leaderboard(user_id=USER_ID, display_name="Anonymous"):
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT AVG(thinking_score) as avg, COUNT(*) as cnt,
               SUM(thinking_score) as total
        FROM submissions WHERE user_id=?
    """, (user_id,))
    row = c.fetchone()
    streak = get_streak_info(user_id)

    c.execute("""
        INSERT INTO leaderboard (user_id, display_name, total_thinking_score, submissions_count, avg_thinking_score, current_streak)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            total_thinking_score=excluded.total_thinking_score,
            submissions_count=excluded.submissions_count,
            avg_thinking_score=excluded.avg_thinking_score,
            current_streak=excluded.current_streak,
            last_updated=CURRENT_TIMESTAMP
    """, (
        user_id, display_name,
        int(row["total"] or 0),
        int(row["cnt"] or 0),
        round(row["avg"] or 0, 1),
        streak["current_streak"]
    ))
    conn.commit()
    conn.close()


def get_leaderboard(limit=10) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT display_name, avg_thinking_score, submissions_count,
               total_thinking_score, current_streak
        FROM leaderboard
        ORDER BY avg_thinking_score DESC
        LIMIT ?
    """, (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows