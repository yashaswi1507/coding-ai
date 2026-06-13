"""
ThinkCode AI — Thinking Analyzer
Uses OUR OWN PyTorch model. Zero external API dependency.
"""

from model.inference import predict, is_model_available
from model.data_collector import collect_submission
from services.ollama_analyzer import analyze_code, get_ai_status
from services.ollama_analyzer import analyze_code, get_ai_status

APPROACH_LABELS_FEEDBACK = {
    "brute_force": "⚠️ Brute-force approach detected — O(n²) or worse",
    "basic":       "🔵 Basic approach — correct but room for optimization",
    "optimized":   "✅ Optimized approach — efficient use of data structures",
    "optimal":     "🏆 Optimal approach — best possible complexity",
}

APPROACH_SUGGESTIONS = {
    "brute_force": [
        "You are checking all combinations manually — this is O(n²).",
        "Think about how a hashmap could reduce repeated lookups to O(1).",
        "Can you solve this in a single pass with extra memory?"
    ],
    "basic": [
        "Your solution works but may not scale to large inputs.",
        "Consider the time complexity — can it be reduced?",
        "What data structure could make this more efficient?"
    ],
    "optimized": [
        "Good use of data structures! This is much better than brute force.",
        "Make sure you are explaining this tradeoff in interviews.",
        "Can you reduce space complexity further?"
    ],
    "optimal": [
        "Excellent! This is the best complexity achievable for this problem.",
        "Focus on explaining WHY this is optimal in interviews.",
        "Can you also handle follow-up variations of this problem?"
    ]
}

THINKING_FEEDBACK_TEMPLATES = [
    (0,  20,  "⚠️ Very little thinking explanation — interviewers need to hear your reasoning"),
    (21, 40,  "⚠️ Weak explanation — add complexity analysis and approach justification"),
    (41, 60,  "🔵 Decent explanation — mention time/space tradeoffs more explicitly"),
    (61, 80,  "✅ Good thinking process — clear approach with technical depth"),
    (81, 100, "🏆 Excellent thinking — clear, technical, and well-reasoned explanation"),
]

REFLECTION_QUESTIONS = {
    "brute_force": [
        "After seeing the optimal solution, what would you change in your approach?",
        "What did you learn from solving this problem?",
        "How would you explain the difference between your approach and the optimal one to a fresher?",
        "Can you think of another problem where the same optimization applies?",
    ],
    "basic": [
        "After solving this, what would you do differently next time?",
        "What was the hardest part of this problem and how did you overcome it?",
        "How would you explain your solution to someone who has never seen this problem?",
        "What similar problems can this approach be applied to?",
    ],
    "optimized": [
        "What was your thought process when you decided to use this data structure?",
        "After solving this, what follow-up problem would you practice next?",
        "How would you teach this approach to a beginner?",
        "What would break your solution — and how would you handle it?",
    ],
    "optimal": [
        "What made you confident this was the best approach?",
        "How would you extend this solution if the problem had additional constraints?",
        "What other problems use the same core idea?",
        "How would you explain this solution in a real interview setting?",
    ]
}


def analyze_thinking(user_code, thinking_text, problem,
                     passed_tests=0, total_tests=0, language="Python"):
    """
    Full thinking analysis.
    - Ollama available → analyze any language with LLM
    - Python → PyTorch model + rule-based
    - Other  → thinking text analysis only
    """

    # ── Try AI (Groq → Ollama → fallback) ────────────────────────────────
    ai_result = analyze_code(user_code, thinking_text, problem, language)
    if ai_result:
        score    = ai_result.get("thinking_score", 50)
        approach = ai_result.get("code_approach", "basic")
        source   = ai_result.get("model_source", "ai")

        # Source label
        source_labels = {
            "groq":   "☁️ Groq AI (LLaMA3) — all languages supported!",
            "ollama": "🖥️ Local Ollama — all languages supported!",
        }
        ai_result["feedback"] = ai_result.get("feedback", [])
        ai_result["feedback"].append(source_labels.get(source, "🤖 AI Analysis"))

        # Collect training data for Python only
        if language == "Python" and user_code.strip():
            try:
                collect_submission(
                    code=user_code, thinking_text=thinking_text,
                    problem_id=problem.get("id","unknown"),
                    topic=problem.get("topic","unknown"),
                    difficulty=problem.get("difficulty","easy"),
                    rule_based_score=score, rule_based_approach=approach,
                    passed_tests=passed_tests, total_tests=total_tests,
                )
            except Exception:
                pass

        return {
            "thinking_score":       score,
            "code_approach":        approach,
            "feedback":             ai_result.get("feedback", []),
            "suggestions":          ai_result.get("suggestions", []),
            "strengths":            ai_result.get("strengths", []),
            "areas_to_improve":     ai_result.get("areas_to_improve", []),
            "reflection_questions": ai_result.get("reflection_questions", [])[:4],
            "complexity_analysis":  ai_result.get("complexity_analysis", {}),
            "model_source":         source,
            "confidence":           ai_result.get("confidence", 0.85),
            "features":             [0]*25,
        }

    # ── Fallback: PyTorch model (Python only) ─────────────────────────────
    prediction = predict(user_code, thinking_text)
    score    = prediction["thinking_score"]
    approach = prediction["approach"]
    source   = prediction["source"]

    # Override approach if set/dict detected
    approach = _detect_approach_override(user_code, approach)

    # Build feedback
    feedback = []
    for lo, hi, msg in THINKING_FEEDBACK_TEMPLATES:
        if lo <= score <= hi:
            feedback.append(msg)
            break

    feedback.append(APPROACH_LABELS_FEEDBACK.get(approach, ""))

    if not thinking_text or not thinking_text.strip():
        feedback.append("⚠️ No thinking explanation — major weakness in interviews")
    elif len(thinking_text.split()) < 15:
        feedback.append("⚠️ Explanation too brief — elaborate on your reasoning")
    else:
        feedback.append("✅ You explained your approach before coding — great habit")

    if source == "neural_network":
        feedback.append("🤖 Evaluated by ThinkCode AI neural network")
    else:
        feedback.append("📏 Rule-based engine — train model for better accuracy")

    # Auto-collect for training — Python only
    try:
        if user_code.strip() and language == "Python":
            collect_submission(
                code=user_code, thinking_text=thinking_text,
                problem_id=problem.get("id", "unknown"),
                topic=problem.get("topic", "unknown"),
                difficulty=problem.get("difficulty", "easy"),
                rule_based_score=score, rule_based_approach=approach,
                passed_tests=passed_tests, total_tests=total_tests,
            )
    except Exception:
        pass

    return {
        "thinking_score":      score,
        "code_approach":       approach,
        "feedback":            [f for f in feedback if f],
        "suggestions":         APPROACH_SUGGESTIONS.get(approach, []),
        "strengths":           _detect_strengths(user_code, thinking_text, approach),
        "areas_to_improve":    _detect_weaknesses(user_code, thinking_text, approach, score),
        "reflection_questions":REFLECTION_QUESTIONS.get(approach, [])[:4],
        "complexity_analysis": _estimate_complexity(user_code),
        "model_source":        source,
        "confidence":          prediction.get("confidence", 0.0),
    }


def _extract_inner_code(code: str) -> str:
    """Extract solution code from class Solution or plain solve()."""
    if "class Solution" not in code:
        return code
    lines = code.split("\n")
    result, inside = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("class Solution") or s.startswith("def solve("):
            continue
        if s.startswith("def ") and not inside:
            inside = True
            continue
        if inside:
            result.append(line)
    extracted = "\n".join(result)
    return extracted if extracted.strip() else code


def _detect_approach_override(code: str, current_approach: str) -> str:
    """
    Override model approach if code uses efficient data structures.
    Works with both plain solve() and class Solution style.
    """
    c = _extract_inner_code(code).lower()

    # Set usage
    if ("set()" in c or "= set(" in c or "set(self" in c or
            "set(nums" in c or "set(s" in c or ".add(" in c):
        return "optimized"

    # Dict/hashmap usage
    if ("dict" in c or "{}" in c or "defaultdict" in c or
            "counter" in c or "= {}" in c or "seen = " in c):
        return "optimized"

    # Binary search
    if (("lo" in c and "hi" in c) or
            ("left" in c and "right" in c and "mid" in c)):
        return "optimal"

    # One-liner optimal
    non_empty = [l for l in code.split("\n") if l.strip()
                 and not l.strip().startswith("#")
                 and not l.strip().startswith("class")
                 and not l.strip().startswith("def")
                 and not l.strip().startswith("from")
                 and not l.strip().startswith("return Solution")]
    if len(non_empty) <= 2 and "return" in c and ("len(" in c or "set(" in c):
        return "optimal"

    return current_approach


def _detect_strengths(code, thinking, approach):
    s = []
    t = (thinking or "").lower()
    c = _extract_inner_code(code).lower()

    # Approach-based strengths
    if approach in ("optimized", "optimal"):
        s.append("Uses efficient data structures")

    # Set detection
    if "set(" in c or "set()" in c or ".add(" in c:
        s.append("Used Set — O(1) lookup, smart choice!")

    # Hashmap detection
    if "dict" in c or "{}" in c or "defaultdict" in c:
        s.append("Used Hashmap — efficient O(n) solution")

    # Edge case handling in code
    if "if not" in c or "len(" in c or "is none" in c:
        s.append("Handles edge cases in code")

    # Thinking quality
    if any(w in t for w in ["o(n", "complexity", "linear"]):
        s.append("Demonstrates complexity awareness")
    if any(w in t for w in ["tradeoff", "instead", "better than"]):
        s.append("Shows optimization thinking")
    if "#" in code:
        s.append("Code is commented — good readability")
    if thinking and len(thinking.split()) >= 30:
        s.append("Provided thorough explanation")

    return s


def _detect_weaknesses(code, thinking, approach, score):
    w = []
    t = (thinking or "").lower()
    c = _extract_inner_code(code).lower()

    if approach == "brute_force":
        w.append("Brute-force approach — not scalable for large inputs")
    if not t.strip():
        w.append("No thinking explanation — critical weakness in interviews")
    elif len(t.split()) < 15:
        w.append("Explanation too brief — needs more depth")
    if not any(x in t for x in ["o(n", "o(1", "complexity", "linear", "constant"]):
        w.append("Never mentioned time/space complexity")
    if not any(x in t for x in ["edge", "empty", "null", "zero"]):
        w.append("No mention of edge cases in explanation")
    return w


def _estimate_complexity(code):
    inner = _extract_inner_code(code)
    c = inner.lower()
    lines = [l.strip() for l in inner.split("\n") if l.strip() and not l.strip().startswith("#")]

    # One-liner optimal — e.g. return len(nums) != len(set(nums))
    if len(lines) <= 3 and "return" in c and "set(" in c and "len(" in c:
        return {"time": "O(n)", "space": "O(n)",
                "explanation": "One-liner set conversion — elegant O(n) solution"}

    # DP patterns — check before nested loops
    if "dp" in c and ("for" in c or "while" in c):
        if c.count("for") >= 2:
            return {"time": "O(n²)", "space": "O(n)",
                    "explanation": "2D DP — nested loops with DP array"}
        return {"time": "O(n)", "space": "O(n)",
                "explanation": "1D DP — single pass with memoization"}

    # Divide and Conquer / Merge Sort pattern
    if "def " in c and c.count("def ") >= 2 and ("merge" in c or "divide" in c):
        return {"time": "O(n log n)", "space": "O(n)",
                "explanation": "Divide and conquer pattern detected"}

    # Binary search pattern
    if (("lo" in c and "hi" in c) or
            ("left" in c and "right" in c and "mid" in c) or
            ("low" in c and "high" in c)):
        return {"time": "O(log n)", "space": "O(1)",
                "explanation": "Binary search — halving search space each step"}

    # Two pointer pattern
    if ("left" in c and "right" in c and "while" in c and
            ("left" not in ["left_pad"] and "sort" in c)):
        return {"time": "O(n)", "space": "O(1)",
                "explanation": "Two pointers — linear scan after sorting"}

    # Sliding window pattern
    if (("window" in c or "sliding" in c) or
            ("left" in c and "right" in c and "for" in c and "max" in c)):
        return {"time": "O(n)", "space": "O(1)",
                "explanation": "Sliding window — single pass with two pointers"}

    # BFS/DFS pattern
    if "deque" in c or "queue" in c or ("from collections" in c and "deque" in c):
        return {"time": "O(V+E)", "space": "O(V)",
                "explanation": "BFS — visits each node and edge once"}
    if "stack" in c and ("dfs" in c or "def dfs" in c):
        return {"time": "O(V+E)", "space": "O(V)",
                "explanation": "DFS — depth-first traversal"}

    # Recursion without memoization
    if c.count("def ") >= 2 and "return" in c:
        func_lines = [l for l in lines if l.startswith("def ")]
        if len(func_lines) >= 2:
            return {"time": "O(2ⁿ) worst case", "space": "O(n) stack",
                    "explanation": "Recursive — check if memoization is needed"}

    # Set usage
    if "set(" in c or ".add(" in c:
        return {"time": "O(n)", "space": "O(n)",
                "explanation": "Set-based — O(1) average lookup"}

    # Hashmap/dict usage
    if "dict" in c or "{}" in c or "defaultdict" in c or "counter" in c:
        return {"time": "O(n)", "space": "O(n)",
                "explanation": "Hashmap — single pass with O(1) lookup"}

    # Sort
    if "sort" in c:
        return {"time": "O(n log n)", "space": "O(1)",
                "explanation": "Sorting dominates — O(n log n) time"}

    # Nested loops
    if c.count("for") >= 2 or (c.count("for") >= 1 and c.count("while") >= 1):
        return {"time": "O(n²)", "space": "O(1)",
                "explanation": "Nested loops — consider optimization"}

    # Single loop
    if "for" in c or "while" in c:
        return {"time": "O(n)", "space": "O(1)",
                "explanation": "Single pass — linear time"}

    return {"time": "O(n)", "space": "O(1)",
            "explanation": "Linear estimate — analyze manually for precision"}