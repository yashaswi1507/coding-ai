from services.code_executor import run_code
from services.validator import validate_output
from services.thinking_analyzer import analyze_thinking
from services.interviewer import generate_followup_questions
from services.analytics import (
    update_streak, update_mentor_memory, update_leaderboard,
    check_and_award_achievements, get_score_breakdown,
    detect_missing_edge_cases, award_xp
)
from model.auto_trainer import trigger_if_needed
from database import get_connection
import json

def evaluate_solution(problem, user_code, thinking_text,
                      user_id="guest", is_daily=False, language="Python"):

    # No code written — return early, no XP, no score
    def _is_empty_solution(code: str) -> bool:
        """Check if user actually wrote any solution logic."""
        lines = code.splitlines()
        solution_lines = []
        for line in lines:
            stripped = line.strip()
            # Skip boilerplate lines
            if not stripped: continue
            if stripped.startswith("from typing"): continue
            if stripped.startswith("class Solution"): continue
            if stripped.startswith("def solve("): continue
            if stripped.startswith("return Solution()"): continue
            if stripped.startswith("def ") and "self" in stripped: continue
            if stripped.startswith("#"): continue
            if stripped == "pass": continue
            solution_lines.append(stripped)
        return len(solution_lines) == 0

    if _is_empty_solution(user_code):
        return {
            "passed": 0, "visible_passed": 0, "hidden_passed": 0,
            "total": len(problem.get("test_cases", [])),
            "visible_total": len(problem.get("visible_test_cases", [])),
            "hidden_total": len(problem.get("hidden_test_cases", [])),
            "all_passed": False,
            "results": [],
            "thinking_score": 0,
            "code_approach": "none",
            "feedback": ["❌ No code written — write your solution first!"],
            "suggestions": ["Write your solution inside the solve() function"],
            "strengths": [], "areas_to_improve": ["Write actual code to get feedback"],
            "reflection_questions": [], "complexity_analysis": {},
            "model_source": "none", "followup_questions": [],
            "score_breakdown": {}, "missing_edge_cases": [],
            "new_achievements": [], "xp": {},
            "error": "no_code"
        }

    visible_cases = problem.get("visible_test_cases", problem.get("test_cases", []))
    hidden_cases  = problem.get("hidden_test_cases", [])
    all_cases     = visible_cases + hidden_cases

    visible_results = []
    hidden_passed = total_passed = 0

    for test in visible_cases:
        execution = run_code(user_code, test["input"], language)
        if not execution["success"]:
            visible_results.append({"passed": False, "message": execution["error"],
                                    "expected": test["output"], "got": None})
            continue
        v = validate_output(test["output"], execution["output"])
        if v["passed"]: total_passed += 1
        visible_results.append(v)

    for test in hidden_cases:
        execution = run_code(user_code, test["input"], language)
        if not execution["success"]: continue
        v = validate_output(test["output"], execution["output"])
        if v["passed"]:
            total_passed += 1
            hidden_passed += 1

    total_cases  = len(all_cases)
    visible_pass = sum(1 for r in visible_results if r["passed"])
    all_passed   = total_passed == total_cases

    # Analyze thinking — Ollama handles all languages, fallback for Python only
    thinking_analysis = analyze_thinking(
        user_code=user_code, thinking_text=thinking_text,
        problem=problem, passed_tests=total_passed, total_tests=total_cases,
        language=language
    )
    # Edge case detection — Python only (rule-based)
    missing_edge_cases = detect_missing_edge_cases(user_code, problem.get("topic",""))         if language == "Python" else []

    followup_questions = generate_followup_questions(user_code, thinking_text, problem)
    features           = thinking_analysis.get("features", [0]*25)
    score_breakdown    = get_score_breakdown(features, thinking_text, thinking_analysis.get("code_approach","basic"))

    # Save to DB
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO submissions (
        user_id, problem_id, thinking_score, code_score,
        passed, total, topic, difficulty, thinking_text, user_code,
        ai_feedback, code_approach
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""", (
        user_id, problem["id"],
        thinking_analysis["thinking_score"],
        int((total_passed/total_cases)*100) if total_cases else 0,
        total_passed, total_cases,
        problem["topic"], problem["difficulty"],
        thinking_text, user_code,
        json.dumps(thinking_analysis.get("feedback", [])),
        thinking_analysis.get("code_approach","basic")
    ))
    conn.commit()
    conn.close()

    # Analytics
    try:
        update_streak(user_id)
        update_mentor_memory(user_id)
        update_leaderboard(user_id)
        new_achievements = check_and_award_achievements(user_id)
        xp_result = award_xp(
            user_id=user_id,
            reason="submission",
            thinking_score=thinking_analysis["thinking_score"],
            all_passed=all_passed,
            is_daily=is_daily
        )
    except Exception:
        new_achievements = []
        xp_result = {}

    # Auto-train if enough new data collected
    try:
        trigger_if_needed()
    except Exception:
        pass

    return {
        "passed": total_passed, "visible_passed": visible_pass,
        "hidden_passed": hidden_passed, "total": total_cases,
        "visible_total": len(visible_cases), "hidden_total": len(hidden_cases),
        "all_passed": all_passed, "results": visible_results,
        "thinking_score":        thinking_analysis["thinking_score"],
        "code_approach":         thinking_analysis["code_approach"],
        "feedback":              thinking_analysis["feedback"],
        "suggestions":           thinking_analysis["suggestions"],
        "strengths":             thinking_analysis.get("strengths", []),
        "areas_to_improve":      thinking_analysis.get("areas_to_improve", []),
        "reflection_questions":  thinking_analysis["reflection_questions"],
        "complexity_analysis":   thinking_analysis.get("complexity_analysis", {}),
        "model_source":          thinking_analysis.get("model_source","rule_based"),
        "followup_questions":    followup_questions,
        "score_breakdown":       score_breakdown,
        "missing_edge_cases":    missing_edge_cases,
        "new_achievements":      new_achievements,
        "xp":                    xp_result,
    }