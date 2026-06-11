from services.code_executor import run_code
from services.validator import validate_output
from services.thinking_analyzer import analyze_thinking
from services.interviewer import generate_followup_questions
from services.analytics import update_streak, update_mentor_memory, update_leaderboard
from database import get_connection
import json

def evaluate_solution(problem, user_code, thinking_text, user_id="guest"):

    visible_cases = problem.get("visible_test_cases", problem.get("test_cases", []))
    hidden_cases  = problem.get("hidden_test_cases", [])
    all_cases     = visible_cases + hidden_cases

    visible_results = []
    hidden_passed   = 0
    total_passed    = 0

    for test in visible_cases:
        execution = run_code(user_code, test["input"])
        if not execution["success"]:
            visible_results.append({"passed": False, "message": execution["error"], "expected": test["output"], "got": None, "hidden": False})
            continue
        v = validate_output(test["output"], execution["output"])
        v["hidden"] = False
        if v["passed"]: total_passed += 1
        visible_results.append(v)

    for test in hidden_cases:
        execution = run_code(user_code, test["input"])
        if not execution["success"]: continue
        v = validate_output(test["output"], execution["output"])
        if v["passed"]:
            total_passed += 1
            hidden_passed += 1

    total_cases  = len(all_cases)
    visible_pass = sum(1 for r in visible_results if r["passed"])

    thinking_analysis = analyze_thinking(
        user_code=user_code, thinking_text=thinking_text,
        problem=problem, passed_tests=total_passed, total_tests=total_cases,
    )
    followup_questions = generate_followup_questions(user_code, thinking_text, problem)

    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO submissions (
        user_id, problem_id, thinking_score, code_score,
        passed, total, topic, difficulty, thinking_text, user_code, ai_feedback
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
        user_id, problem["id"],
        thinking_analysis["thinking_score"],
        int((total_passed/total_cases)*100) if total_cases else 0,
        total_passed, total_cases,
        problem["topic"], problem["difficulty"],
        thinking_text, user_code,
        json.dumps(thinking_analysis.get("feedback", []))
    ))
    conn.commit()
    conn.close()

    # Update all analytics
    try:
        update_streak(user_id)
        update_mentor_memory(user_id)
        update_leaderboard(user_id)
    except Exception:
        pass

    return {
        "passed": total_passed, "visible_passed": visible_pass,
        "hidden_passed": hidden_passed, "total": total_cases,
        "visible_total": len(visible_cases), "hidden_total": len(hidden_cases),
        "all_passed": total_passed == total_cases,
        "results": visible_results,
        "thinking_score":       thinking_analysis["thinking_score"],
        "code_approach":        thinking_analysis["code_approach"],
        "feedback":             thinking_analysis["feedback"],
        "suggestions":          thinking_analysis["suggestions"],
        "strengths":            thinking_analysis.get("strengths", []),
        "areas_to_improve":     thinking_analysis.get("areas_to_improve", []),
        "reflection_questions": thinking_analysis["reflection_questions"],
        "complexity_analysis":  thinking_analysis.get("complexity_analysis", {}),
        "model_source":         thinking_analysis.get("model_source", "rule_based"),
        "followup_questions":   followup_questions,
    }