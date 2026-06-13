"""
ThinkCode AI — Analytics Engine v2
Handles: Streak, Weakness, Adaptive Difficulty, Mentor Memory,
         Leaderboard, Thinker Levels, Achievements, Pattern Analysis
"""

import json
from datetime import datetime, date, timedelta
from database import get_connection

USER_ID = "guest"

# ── Thinker Levels ────────────────────────────────────────────────────────────
THINKER_LEVELS = [
    {"min": 0,  "max": 30, "level": "Novice Thinker",     "icon": "🌱", "desc": "Just starting your thinking journey"},
    {"min": 31, "max": 55, "level": "Logical Thinker",    "icon": "🔵", "desc": "Getting systematic and structured"},
    {"min": 56, "max": 75, "level": "Analytical Thinker", "icon": "🟣", "desc": "Thinking like a real engineer"},
    {"min": 76, "max": 100,"level": "Architect Thinker",  "icon": "🏆", "desc": "Interview-ready deep thinking"},
]

# ── Achievements ──────────────────────────────────────────────────────────────
ALL_ACHIEVEMENTS = [
    {"id": "first_blood",      "title": "First Blood",        "icon": "⚔️",  "desc": "First submission ever"},
    {"id": "streak_3",         "title": "On Fire",            "icon": "🔥",  "desc": "3-day streak"},
    {"id": "streak_7",         "title": "Week Warrior",       "icon": "🗓️",  "desc": "7-day streak"},
    {"id": "streak_30",        "title": "Monthly Master",     "icon": "💎",  "desc": "30-day streak"},
    {"id": "perfect_thinker",  "title": "Perfect Thinker",   "icon": "🧠",  "desc": "Thinking score 90+"},
    {"id": "optimizer",        "title": "Optimizer",          "icon": "⚡",  "desc": "3 optimized approaches"},
    {"id": "complexity_master","title": "Complexity Master",  "icon": "📊",  "desc": "Mentioned O(n) 5 times"},
    {"id": "edge_case_hero",   "title": "Edge Case Hero",     "icon": "🛡️",  "desc": "Edge cases 5 times in code"},
    {"id": "problem_crusher",  "title": "Problem Crusher",    "icon": "💪",  "desc": "Solved 10 problems"},
    {"id": "speed_solver",     "title": "Speed Solver",       "icon": "⏱️",  "desc": "Solved in under 10 minutes"},
    {"id": "all_pass",         "title": "All Green",          "icon": "✅",  "desc": "All test cases passed"},
    {"id": "daily_done",       "title": "Daily Champion",     "icon": "🌟",  "desc": "Completed daily challenge"},
]


# ── Streak ────────────────────────────────────────────────────────────────────
def update_streak(user_id=USER_ID):
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        INSERT INTO streaks (user_id, date, problems_solved) VALUES (?, ?, 1)
        ON CONFLICT(user_id, date) DO UPDATE SET problems_solved = problems_solved + 1
    """, (user_id, today))
    conn.commit()
    conn.close()


def get_streak_info(user_id=USER_ID) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT date FROM streaks WHERE user_id=? ORDER BY date DESC", (user_id,))
    dates = [row["date"] for row in c.fetchall()]
    conn.close()

    if not dates:
        return {"current_streak": 0, "longest_streak": 0, "total_active_days": 0, "today_solved": False, "heatmap": []}

    today = date.today()
    date_set = set(dates)
    current = 0
    check = today
    while check.isoformat() in date_set:
        current += 1
        check -= timedelta(days=1)

    longest, streak = 0, 1
    date_objs = sorted([date.fromisoformat(d) for d in date_set])
    for i in range(1, len(date_objs)):
        if (date_objs[i] - date_objs[i-1]).days == 1:
            streak += 1
            longest = max(longest, streak)
        else:
            streak = 1
    longest = max(longest, streak)

    heatmap = []
    for i in range(29, -1, -1):
        d = (today - timedelta(days=i)).isoformat()
        heatmap.append({"date": d, "active": d in date_set})

    return {
        "current_streak": current, "longest_streak": longest,
        "total_active_days": len(date_set),
        "today_solved": today.isoformat() in date_set,
        "heatmap": heatmap
    }


# ── Thinker Level ─────────────────────────────────────────────────────────────
def get_thinker_level(avg_score: float) -> dict:
    for lvl in THINKER_LEVELS:
        if lvl["min"] <= avg_score <= lvl["max"]:
            return lvl
    return THINKER_LEVELS[0]


# ── Thinking Pattern Analysis ─────────────────────────────────────────────────
def get_thinking_patterns(user_id=USER_ID) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT thinking_text, user_code, thinking_score, code_approach, topic
        FROM submissions WHERE user_id=? ORDER BY submitted_at DESC LIMIT 20
    """, (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    if not rows:
        return {"patterns": [], "style": "Unknown", "trend": "No data yet"}

    patterns = []
    texts = [r["thinking_text"] or "" for r in rows]
    codes = [r["user_code"] or "" for r in rows]
    scores = [r["thinking_score"] or 0 for r in rows]

    # Pattern: Never mentions complexity
    complexity_count = sum(1 for t in texts if any(w in t.lower() for w in ["o(n", "o(1", "complexity", "linear", "quadratic"]))
    if complexity_count == 0:
        patterns.append({"type": "weakness", "msg": "⚠️ You never mention time/space complexity — this is critical in interviews"})
    elif complexity_count >= len(texts) * 0.7:
        patterns.append({"type": "strength", "msg": "✅ You consistently mention complexity — great interview habit"})

    # Pattern: Always brute force
    bf_count = sum(1 for r in rows if r.get("code_approach") == "brute_force")
    if bf_count >= len(rows) * 0.6:
        patterns.append({"type": "weakness", "msg": "⚠️ You tend to go brute-force first — try to think of optimization upfront"})

    # Pattern: Short explanations
    avg_words = sum(len(t.split()) for t in texts if t) / max(len([t for t in texts if t]), 1)
    if avg_words < 15:
        patterns.append({"type": "weakness", "msg": f"⚠️ Your explanations average {int(avg_words)} words — aim for 40+ words"})
    elif avg_words >= 40:
        patterns.append({"type": "strength", "msg": f"✅ Strong explanations — averaging {int(avg_words)} words"})

    # Pattern: Edge case handling
    edge_count = sum(1 for c in codes if "if not" in c or "len(" in c or "is None" in c.lower())
    if edge_count >= len(codes) * 0.6:
        patterns.append({"type": "strength", "msg": "✅ You handle edge cases consistently — good defensive coding"})
    else:
        patterns.append({"type": "weakness", "msg": "⚠️ You often miss edge cases in your code"})

    # Score trend
    if len(scores) >= 3:
        recent_avg = sum(scores[:3]) / 3
        older_avg  = sum(scores[-3:]) / 3
        if recent_avg > older_avg + 5:
            trend = f"📈 Improving! +{int(recent_avg - older_avg)} points recently"
        elif recent_avg < older_avg - 5:
            trend = f"📉 Slight dip recently — keep practicing"
        else:
            trend = "➡️ Consistent performance"
    else:
        trend = "Not enough data yet"

    # Thinking style
    opt_count = sum(1 for r in rows if r.get("code_approach") in ("optimized","optimal"))
    if opt_count >= len(rows) * 0.6:
        style = "Optimizer — you naturally think about efficiency"
    elif bf_count >= len(rows) * 0.6:
        style = "Brute-Forcer — you solve first, optimize later"
    else:
        style = "Balanced — mix of approaches"

    return {"patterns": patterns, "style": style, "trend": trend, "avg_words": int(avg_words)}


# ── Achievements ──────────────────────────────────────────────────────────────
def check_and_award_achievements(user_id=USER_ID, submission: dict = None) -> list:
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT COUNT(*) as cnt FROM submissions WHERE user_id=?", (user_id,))
    total = c.fetchone()["cnt"]

    c.execute("SELECT code_approach, thinking_text, user_code, thinking_score, passed, total FROM submissions WHERE user_id=?", (user_id,))
    rows = [dict(r) for r in c.fetchall()]

    streak = get_streak_info(user_id)

    c.execute("SELECT achievement_id FROM user_achievements WHERE user_id=?", (user_id,))
    existing = {r["achievement_id"] for r in c.fetchall()}
    conn.close()

    new_achievements = []

    def award(aid):
        if aid not in existing:
            conn2 = get_connection()
            conn2.cursor().execute(
                "INSERT OR IGNORE INTO user_achievements (user_id, achievement_id) VALUES (?,?)",
                (user_id, aid)
            )
            conn2.commit()
            conn2.close()
            badge = next((a for a in ALL_ACHIEVEMENTS if a["id"] == aid), None)
            if badge:
                new_achievements.append(badge)

    if total >= 1:   award("first_blood")
    if total >= 10:  award("problem_crusher")
    if streak["current_streak"] >= 3:  award("streak_3")
    if streak["current_streak"] >= 7:  award("streak_7")
    if streak["current_streak"] >= 30: award("streak_30")

    opt_count = sum(1 for r in rows if r.get("code_approach") in ("optimized","optimal"))
    if opt_count >= 3: award("optimizer")

    complexity_count = sum(1 for r in rows if any(w in (r.get("thinking_text") or "").lower() for w in ["o(n","o(1","complexity"]))
    if complexity_count >= 5: award("complexity_master")

    edge_count = sum(1 for r in rows if any(w in (r.get("user_code") or "").lower() for w in ["if not","len(","is none"]))
    if edge_count >= 5: award("edge_case_hero")

    high_score = any(r.get("thinking_score", 0) >= 90 for r in rows)
    if high_score: award("perfect_thinker")

    all_pass = any(r.get("passed") == r.get("total") and r.get("total", 0) > 0 for r in rows)
    if all_pass: award("all_pass")

    return new_achievements


def get_user_achievements(user_id=USER_ID) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT achievement_id, earned_at FROM user_achievements WHERE user_id=? ORDER BY earned_at DESC", (user_id,))
    earned = {r["achievement_id"]: r["earned_at"] for r in c.fetchall()}
    conn.close()

    result = []
    for a in ALL_ACHIEVEMENTS:
        result.append({**a, "earned": a["id"] in earned, "earned_at": earned.get(a["id"])})
    return result


# ── Score Breakdown ───────────────────────────────────────────────────────────
def get_score_breakdown(features: list, thinking_text: str, approach: str) -> dict:
    """Detailed breakdown of how thinking score was calculated."""
    t = (thinking_text or "").lower()
    breakdown = {}

    # Approach (30 pts)
    approach_pts = {"optimal": 30, "optimized": 25, "basic": 15, "brute_force": 8}.get(approach, 10)
    breakdown["approach"] = {"score": approach_pts, "max": 30, "label": "Algorithm Approach",
        "detail": f"You used a {approach.replace('_',' ')} approach"}

    # Complexity mention (20 pts)
    cx_pts = 20 if any(w in t for w in ["o(n","o(1","complexity","linear","quadratic","log"]) else 0
    breakdown["complexity"] = {"score": cx_pts, "max": 20, "label": "Complexity Awareness",
        "detail": "Mentioned time/space complexity" if cx_pts else "Did not mention complexity"}

    # Edge cases (15 pts)
    edge_pts = 15 if any(w in t for w in ["edge","empty","null","zero","negative","single"]) else 0
    breakdown["edge_cases"] = {"score": edge_pts, "max": 15, "label": "Edge Case Thinking",
        "detail": "Considered edge cases" if edge_pts else "No edge cases mentioned"}

    # Explanation quality (20 pts)
    words = len(t.split()) if t.strip() else 0
    exp_pts = min(20, (words // 10) * 5)
    breakdown["explanation"] = {"score": exp_pts, "max": 20, "label": "Explanation Quality",
        "detail": f"{words} words written"}

    # Optimization awareness (15 pts)
    opt_pts = 15 if any(w in t for w in ["optimize","efficient","better","tradeoff","instead"]) else 0
    breakdown["optimization"] = {"score": opt_pts, "max": 15, "label": "Optimization Thinking",
        "detail": "Showed optimization awareness" if opt_pts else "No optimization discussion"}

    total = sum(v["score"] for v in breakdown.values())
    return {"breakdown": breakdown, "total": min(total, 100)}


# ── Reflection Scoring ────────────────────────────────────────────────────────
def score_reflection(question: str, answer: str) -> dict:
    if not answer or not answer.strip():
        return {"score": 0, "feedback": "No answer provided", "level": "Empty"}

    a = answer.lower()
    words = len(a.split())
    score = 0
    feedbacks = []

    if words >= 10: score += 20; feedbacks.append("✅ Good length")
    elif words >= 5: score += 10; feedbacks.append("⚠️ Too brief")
    else: feedbacks.append("❌ Too short")

    tech_words = ["complexity","o(n","hashmap","optimize","tradeoff","efficient","approach","algorithm","data structure"]
    tech_hits = sum(1 for w in tech_words if w in a)
    score += min(tech_hits * 15, 45)
    if tech_hits >= 2: feedbacks.append("✅ Good technical vocabulary")
    elif tech_hits == 1: feedbacks.append("🔵 Some technical depth")
    else: feedbacks.append("⚠️ Add technical terms")

    reasoning = ["because","since","therefore","so that","which means","this helps","reason"]
    if any(w in a for w in reasoning):
        score += 20; feedbacks.append("✅ Shows reasoning")
    else:
        feedbacks.append("⚠️ Explain your reasoning (use 'because', 'since'...)")

    if words >= 30: score += 15

    score = min(score, 100)
    level = "Excellent" if score >= 80 else "Good" if score >= 55 else "Needs Work" if score >= 30 else "Weak"
    return {"score": score, "feedback": " · ".join(feedbacks), "level": level}


# ── Edge Case Detector ────────────────────────────────────────────────────────
def detect_missing_edge_cases(user_code: str, problem_topic: str) -> list:
    code = user_code.lower()
    missing = []

    checks = [
        ("if not " in code or "len(" in code or "== []" in code or "== ''" in code,
         "Empty input", "What happens when input is empty array/string?"),
        ("len(" in code and "== 1" in code or "single" in code,
         "Single element", "What if there's only one element?"),
        (any(w in code for w in ["< 0","negative","abs(","min("]),
         "Negative numbers", "Does your solution handle negative numbers?"),
        ("return" in code,
         "Return value", "Does solve() always return a value (not None)?"),
        ("is none" in code or "is not none" in code or "if not " in code,
         "Null check", "What if input contains None/null values?"),
    ]

    for handled, name, question in checks:
        if not handled:
            missing.append({"case": name, "question": question})

    return missing[:3]


# ── Daily Challenge ───────────────────────────────────────────────────────────
def get_daily_challenge(problems: dict) -> dict:
    import hashlib
    today = date.today().isoformat()
    problem_ids = sorted(problems.keys())
    idx = int(hashlib.md5(today.encode()).hexdigest(), 16) % len(problem_ids)
    daily_id = problem_ids[idx]
    p = problems[daily_id]
    return {**p, "is_daily": True, "date": today,
            "bonus_note": "Complete today's challenge for +10 bonus thinking score!"}


def is_daily_completed(user_id: str, problem_id: str) -> bool:
    conn = get_connection()
    c = conn.cursor()
    today = date.today().isoformat()
    c.execute("""
        SELECT COUNT(*) as cnt FROM submissions
        WHERE user_id=? AND problem_id=? AND date(submitted_at)=?
    """, (user_id, problem_id, today))
    cnt = c.fetchone()["cnt"]
    conn.close()
    return cnt > 0


# ── Learning Paths ────────────────────────────────────────────────────────────
LEARNING_PATHS = {
    "beginner": {
        "title": "🌱 Beginner Path",
        "desc": "Start from scratch — arrays to basic DP",
        "order": ["contains_duplicate","two_sum","best_time_to_buy_stock",
                  "valid_anagram","valid_parentheses","binary_search",
                  "climbing_stairs","reverse_linked_list","merge_two_sorted_lists","maximum_subarray"]
    },
    "interview": {
        "title": "🎯 Interview Ready",
        "desc": "Most asked problems in tech interviews",
        "order": ["two_sum","valid_parentheses","maximum_subarray","coin_change",
                  "number_of_islands","top_k_frequent_elements","three_sum",
                  "longest_substring_without_repeating","house_robber","word_search"]
    },
    "faang": {
        "title": "🏢 FAANG Path",
        "desc": "Hard problems asked at top companies",
        "order": ["three_sum","product_except_self","find_median_sorted_arrays",
                  "word_search","number_of_islands","top_k_frequent_elements",
                  "longest_substring_without_repeating","min_stack","house_robber","coin_change"]
    }
}

def get_learning_path(path_id: str, problems: dict, user_id: str = USER_ID) -> dict:
    if path_id not in LEARNING_PATHS:
        return {}

    path = LEARNING_PATHS[path_id]
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT problem_id FROM submissions WHERE user_id=? AND passed=total AND total>0", (user_id,))
    solved = {r["problem_id"] for r in c.fetchall()}
    conn.close()

    steps = []
    for i, pid in enumerate(path["order"]):
        p = problems.get(pid, {})
        if p:
            steps.append({
                "order": i + 1, "id": pid, "title": p.get("title", pid),
                "topic": p.get("topic", ""), "difficulty": p.get("difficulty", ""),
                "solved": pid in solved,
                "current": pid not in solved and all(p2 in solved for p2 in path["order"][:i])
            })

    solved_count = sum(1 for s in steps if s["solved"])
    return {**path, "steps": steps,
            "progress": int(solved_count / len(steps) * 100),
            "solved_count": solved_count, "total": len(steps)}


# ── Weakness Report ───────────────────────────────────────────────────────────
def get_weakness_report(user_id=USER_ID) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT topic, difficulty, COUNT(*) as attempts,
               AVG(thinking_score) as avg_thinking, AVG(code_score) as avg_code,
               SUM(CASE WHEN passed=total AND total>0 THEN 1 ELSE 0 END) as solves
        FROM submissions WHERE user_id=? GROUP BY topic, difficulty
    """, (user_id,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    if not rows:
        return {"weak_topics": [], "strong_topics": [], "topic_stats": [], "suggestions": []}

    weak, strong, topic_stats = [], [], []
    for r in rows:
        avg_t = r["avg_thinking"] or 0
        avg_c = r["avg_code"] or 0
        combined = (avg_t + avg_c) / 2
        r["combined_score"] = round(combined, 1)
        topic_stats.append(r)
        if combined < 40: weak.append(r["topic"])
        elif combined >= 70: strong.append(r["topic"])

    suggestions = []
    for topic in set(weak):
        suggestions.append(f"Practice more {topic} problems — your thinking score is low here")
    for topic in set(strong):
        suggestions.append(f"Great work on {topic}! Try harder difficulty")

    return {"weak_topics": list(set(weak)), "strong_topics": list(set(strong)),
            "topic_stats": topic_stats, "suggestions": suggestions}


# ── Adaptive Recommendations ──────────────────────────────────────────────────
def get_next_recommended_problems(user_id=USER_ID, problems: dict = None) -> list:
    if not problems: return []
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT DISTINCT problem_id FROM submissions WHERE user_id=? AND passed=total AND total>0", (user_id,))
    solved_ids = {r["problem_id"] for r in c.fetchall()}
    c.execute("SELECT difficulty, AVG(thinking_score) as avg FROM submissions WHERE user_id=? GROUP BY difficulty", (user_id,))
    diff_scores = {r["difficulty"]: r["avg"] or 0 for r in c.fetchall()}
    conn.close()

    target_diff = "easy"
    if diff_scores.get("easy", 0) >= 60: target_diff = "medium"
    if diff_scores.get("medium", 0) >= 60: target_diff = "hard"

    weakness = get_weakness_report(user_id)
    weak_topics = weakness["weak_topics"]

    scored = []
    for pid, p in problems.items():
        if pid in solved_ids: continue
        score = 0
        if p["difficulty"] == target_diff: score += 30
        if p["topic"] in weak_topics: score += 20
        scored.append((score, p))

    scored.sort(key=lambda x: -x[0])
    return [p for _, p in scored[:5]]


# ── Mentor Memory ─────────────────────────────────────────────────────────────
def update_mentor_memory(user_id=USER_ID):
    weakness = get_weakness_report(user_id)
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT AVG(thinking_score) as avg, COUNT(*) as cnt FROM submissions WHERE user_id=?", (user_id,))
    row = c.fetchone()
    avg_score = round(row["avg"] or 0, 1)
    total = row["cnt"] or 0
    c.execute("""
        INSERT INTO mentor_memory (user_id, weak_topics, strong_topics, avg_thinking_score, total_submissions)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(user_id) DO UPDATE SET
            weak_topics=excluded.weak_topics, strong_topics=excluded.strong_topics,
            avg_thinking_score=excluded.avg_thinking_score, total_submissions=excluded.total_submissions,
            last_updated=CURRENT_TIMESTAMP
    """, (user_id, json.dumps(weakness["weak_topics"]), json.dumps(weakness["strong_topics"]), avg_score, total))
    conn.commit()
    conn.close()


def get_mentor_message(user_id=USER_ID) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM mentor_memory WHERE user_id=?", (user_id,))
    row = c.fetchone()

    # Get recent submissions for deep analysis
    c.execute("""
        SELECT thinking_score, code_score, topic, difficulty, code_approach,
               thinking_text, submitted_at
        FROM submissions WHERE user_id=?
        ORDER BY submitted_at DESC LIMIT 10
    """, (user_id,))
    recent = [dict(r) for r in c.fetchall()]
    conn.close()

    if not row or not recent:
        return {
            "message": "Welcome to ThinkCode AI! Start solving to get personalized coaching.",
            "tips": [
                "Begin with Easy Array problems",
                "Always explain your thinking before writing code",
                "Mention time complexity in every explanation"
            ]
        }

    weak   = json.loads(row["weak_topics"] or "[]")
    strong = json.loads(row["strong_topics"] or "[]")
    avg    = row["avg_thinking_score"] or 0
    total  = row["total_submissions"] or 0
    streak = get_streak_info(user_id)
    level  = get_thinker_level(avg)

    # ── Deep Personalized Analysis ────────────────────────────────────────
    # Score trend
    scores = [r["thinking_score"] for r in recent if r["thinking_score"]]
    recent_avg = sum(scores[:3])/3 if len(scores) >= 3 else (scores[0] if scores else 0)
    older_avg  = sum(scores[-3:])/3 if len(scores) >= 6 else recent_avg
    trend = "improving" if recent_avg > older_avg + 3 else "declining" if recent_avg < older_avg - 3 else "stable"

    # Approach pattern
    approaches = [r.get("code_approach","") for r in recent]
    bf_count  = approaches.count("brute_force")
    opt_count = approaches.count("optimized") + approaches.count("optimal")
    always_bf = bf_count >= len(approaches) * 0.7 and len(approaches) >= 3

    # Thinking text quality
    texts = [r.get("thinking_text","") for r in recent if r.get("thinking_text","").strip()]
    avg_words = sum(len(t.split()) for t in texts) // max(len(texts), 1) if texts else 0
    never_explains = avg_words < 10 and len(recent) >= 3
    explains_well  = avg_words >= 40

    # Difficulty pattern
    difficulties = [r.get("difficulty","") for r in recent]
    stuck_on_easy = difficulties.count("easy") >= len(difficulties) * 0.8 and len(difficulties) >= 5

    # ── Build personalized message ────────────────────────────────────────
    parts = [f"{level['icon']} {level['level']}"]

    if streak["current_streak"] >= 7:
        parts.append(f"🔥 Incredible {streak['current_streak']}-day streak!")
    elif streak["current_streak"] >= 3:
        parts.append(f"🔥 {streak['current_streak']}-day streak — keep it going!")

    if trend == "improving":
        parts.append(f"📈 Your thinking score improved by +{round(recent_avg - older_avg, 1)} recently — great progress!")
    elif trend == "declining":
        parts.append(f"📉 Slight dip lately — try slowing down and thinking more before coding.")
    else:
        parts.append(f"Avg thinking score: {round(avg, 1)}/100")

    # ── Personalized tips ─────────────────────────────────────────────────
    tips = []

    if never_explains:
        tips.append("⚠️ You rarely explain your thinking — this is your #1 growth area. Write 2-3 sentences before coding!")
    elif not explains_well:
        tips.append(f"Your explanations average {avg_words} words — aim for 40+ with complexity and edge cases")
    elif explains_well:
        tips.append("✅ Great explanation habit! Now focus on mentioning trade-offs and alternatives")

    if always_bf:
        tips.append("⚠️ You tend to go brute force — try asking 'can I use a hashmap or set?' before coding")
    elif opt_count >= len(approaches) * 0.6:
        tips.append("✅ You naturally think of optimized approaches — try harder problems!")

    if weak:
        topic = weak[0]
        tips.append(f"🎯 Focus on {topic} — your thinking score is lowest here. Practice 2-3 more problems!")

    if strong:
        tips.append(f"💪 You're strong in {strong[0]} — try Hard difficulty there")

    if stuck_on_easy:
        tips.append("🚀 You've been on Easy problems — time to level up to Medium!")

    if total < 5:
        tips.append("Solve at least 10 problems to unlock full personalized insights")

    return {
        "message": " · ".join(parts),
        "tips": tips[:3],
        "avg_score": round(avg, 1),
        "total_solved": total,
        "streak": streak["current_streak"],
        "level": level,
        "trend": trend,
        "avg_explanation_words": avg_words,
    }


# ── Leaderboard ───────────────────────────────────────────────────────────────
def update_leaderboard(user_id=USER_ID, display_name="Anonymous"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT AVG(thinking_score) as avg, COUNT(*) as cnt, SUM(thinking_score) as total FROM submissions WHERE user_id=?", (user_id,))
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
    """, (user_id, display_name, int(row["total"] or 0), int(row["cnt"] or 0),
          round(row["avg"] or 0, 1), streak["current_streak"]))
    conn.commit()
    conn.close()


def get_leaderboard(limit=10) -> list:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT display_name, avg_thinking_score, submissions_count, total_thinking_score, current_streak FROM leaderboard ORDER BY avg_thinking_score DESC LIMIT ?", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows


# ── XP System ─────────────────────────────────────────────────────────────────

XP_REWARDS = {
    "submission":        10,   # Har submission
    "all_tests_passed":  25,   # Sab test pass
    "thinking_score_50": 15,   # Thinking score 50+
    "thinking_score_75": 25,   # Thinking score 75+
    "thinking_score_90": 40,   # Thinking score 90+
    "daily_challenge":   30,   # Daily challenge complete
    "streak_bonus":      20,   # Streak maintain karna
    "first_solve":       50,   # Pehli baar problem solve
}

XP_LEVELS = [
    {"level": 1,  "min_xp": 0,    "title": "Beginner",      "icon": "🌱"},
    {"level": 2,  "min_xp": 100,  "title": "Thinker",       "icon": "💭"},
    {"level": 3,  "min_xp": 250,  "title": "Analyst",       "icon": "🔍"},
    {"level": 4,  "min_xp": 500,  "title": "Optimizer",     "icon": "⚡"},
    {"level": 5,  "min_xp": 1000, "title": "Expert",        "icon": "🧠"},
    {"level": 6,  "min_xp": 2000, "title": "Master",        "icon": "🏆"},
    {"level": 7,  "min_xp": 5000, "title": "Architect",     "icon": "🏛️"},
]


def get_xp_level(total_xp: int) -> dict:
    current = XP_LEVELS[0]
    for lvl in XP_LEVELS:
        if total_xp >= lvl["min_xp"]:
            current = lvl
    # Next level
    idx = XP_LEVELS.index(current)
    next_lvl = XP_LEVELS[idx + 1] if idx + 1 < len(XP_LEVELS) else None
    progress = 0
    if next_lvl:
        progress = int((total_xp - current["min_xp"]) /
                       (next_lvl["min_xp"] - current["min_xp"]) * 100)
    return {
        **current,
        "total_xp": total_xp,
        "next_level": next_lvl,
        "progress_to_next": min(progress, 100),
        "xp_to_next": (next_lvl["min_xp"] - total_xp) if next_lvl else 0
    }


def award_xp(user_id: str, reason: str, thinking_score: int = 0,
             all_passed: bool = False, is_daily: bool = False) -> dict:
    xp = XP_REWARDS["submission"]
    reasons = ["📝 Submission: +10 XP"]

    if all_passed:
        xp += XP_REWARDS["all_tests_passed"]
        reasons.append("✅ All tests passed: +25 XP")

    if thinking_score >= 90:
        xp += XP_REWARDS["thinking_score_90"]
        reasons.append("🧠 Thinking score 90+: +40 XP")
    elif thinking_score >= 75:
        xp += XP_REWARDS["thinking_score_75"]
        reasons.append("🧠 Thinking score 75+: +25 XP")
    elif thinking_score >= 50:
        xp += XP_REWARDS["thinking_score_50"]
        reasons.append("🧠 Thinking score 50+: +15 XP")

    if is_daily:
        xp += XP_REWARDS["daily_challenge"]
        reasons.append("🌟 Daily challenge: +30 XP")

    streak = get_streak_info(user_id)
    if streak["current_streak"] >= 3:
        xp += XP_REWARDS["streak_bonus"]
        reasons.append(f"🔥 Streak bonus ({streak['current_streak']} days): +20 XP")

    # Save to DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO user_xp (user_id, total_xp, level)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id) DO UPDATE SET
            total_xp = total_xp + ?,
            last_updated = CURRENT_TIMESTAMP
    """, (user_id, xp, xp))
    c.execute("""
        INSERT INTO xp_history (user_id, xp_gained, reason)
        VALUES (?, ?, ?)
    """, (user_id, xp, ", ".join(reasons)))

    c.execute("SELECT total_xp FROM user_xp WHERE user_id=?", (user_id,))
    row = c.fetchone()
    total_xp = row["total_xp"] if row else xp
    conn.commit()
    conn.close()

    level_info = get_xp_level(total_xp)
    return {
        "xp_gained": xp,
        "reasons": reasons,
        "total_xp": total_xp,
        "level": level_info
    }


def get_user_xp(user_id: str) -> dict:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT total_xp FROM user_xp WHERE user_id=?", (user_id,))
    row = c.fetchone()
    total_xp = row["total_xp"] if row else 0

    c.execute("""SELECT xp_gained, reason, earned_at FROM xp_history
               WHERE user_id=? ORDER BY earned_at DESC LIMIT 10""", (user_id,))
    history = [dict(r) for r in c.fetchall()]
    conn.close()

    return {**get_xp_level(total_xp), "history": history}


# ── Weakness Evolution Tracking ───────────────────────────────────────────────

def get_weakness_evolution(user_id: str = USER_ID) -> dict:
    """Track how weakness has changed over time — weekly snapshots."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        SELECT topic,
               AVG(CASE WHEN submitted_at >= datetime('now', '-7 days')
                        THEN thinking_score END) as recent_avg,
               AVG(CASE WHEN submitted_at < datetime('now', '-7 days')
                        AND submitted_at >= datetime('now', '-14 days')
                        THEN thinking_score END) as prev_avg,
               COUNT(*) as total_attempts
        FROM submissions
        WHERE user_id=?
        GROUP BY topic
        HAVING total_attempts >= 2
    """, (user_id,))

    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    evolution = []
    for r in rows:
        recent = r["recent_avg"] or 0
        prev   = r["prev_avg"] or 0
        change = round(recent - prev, 1) if prev else 0

        evolution.append({
            "topic":   r["topic"],
            "recent":  round(recent, 1),
            "prev":    round(prev, 1),
            "change":  change,
            "trend":   "📈 Improving" if change > 5 else
                       "📉 Declining" if change < -5 else
                       "➡️ Stable",
            "attempts": r["total_attempts"]
        })

    evolution.sort(key=lambda x: x["change"], reverse=True)
    return {
        "evolution": evolution,
        "most_improved": evolution[0]["topic"] if evolution else None,
        "needs_attention": evolution[-1]["topic"] if len(evolution) > 1 else None
    }


# ── Thinking Replay ───────────────────────────────────────────────────────────

def get_thinking_replay(user_id: str, problem_id: str) -> list:
    """All attempts for a problem — show thinking evolution."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        SELECT thinking_text, user_code, thinking_score,
               code_approach, passed, total, submitted_at
        FROM submissions
        WHERE user_id=? AND problem_id=?
        ORDER BY submitted_at ASC
    """, (user_id, problem_id))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()

    replay = []
    for i, r in enumerate(rows):
        prev_score = rows[i-1]["thinking_score"] if i > 0 else 0
        change = r["thinking_score"] - prev_score if i > 0 else 0
        replay.append({
            **r,
            "attempt_num": i + 1,
            "score_change": change,
            "improved": change > 0
        })
    return replay