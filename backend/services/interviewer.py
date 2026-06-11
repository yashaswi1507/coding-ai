"""
ThinkCode AI — AI Interviewer v2
Generates accurate, relevant follow-up questions based on:
- User's actual code approach
- Problem topic
- Thinking explanation quality
Max 3 focused questions — not overwhelming
"""

from model.feature_extractor import extract_features

# ── Topic-based question banks ────────────────────────────────────────────────
TOPIC_QUESTIONS = {
    "arrays": [
        "What is the time complexity of your solution and why?",
        "How would your solution handle an empty array?",
        "Can you solve this without using extra space?",
        "What happens if the array has duplicate values?",
        "How would performance change if input size was 10 million?",
    ],
    "strings": [
        "How does your solution handle an empty string?",
        "What is the space complexity of your approach?",
        "Would your solution work with Unicode characters?",
        "Can you optimize this to use O(1) extra space?",
        "How would you handle case sensitivity?",
    ],
    "dynamic-programming": [
        "Can you explain the recurrence relation you used?",
        "Is this top-down or bottom-up DP? What are the tradeoffs?",
        "Can you reduce the space complexity of your DP solution?",
        "How did you identify this as a DP problem?",
        "What are the overlapping subproblems here?",
    ],
    "graphs": [
        "Why did you choose DFS over BFS (or vice versa)?",
        "What is the time complexity in terms of V and E?",
        "How does your solution handle disconnected graphs?",
        "How are you tracking visited nodes to avoid cycles?",
        "What would change if the graph was directed?",
    ],
    "trees": [
        "Why did you choose recursive over iterative approach?",
        "What is the space complexity considering the call stack?",
        "How would your solution handle a skewed tree?",
        "Can you solve this iteratively using a stack?",
        "What happens if the tree is empty?",
    ],
    "binary-search": [
        "Why use lo + (hi-lo)//2 instead of (lo+hi)//2?",
        "What is the loop termination condition and why?",
        "How does your solution handle a single-element array?",
        "Can binary search be applied to a 2D matrix?",
        "What if there are duplicate elements in the array?",
    ],
    "stack": [
        "Why is a stack the right data structure here?",
        "What is the time and space complexity?",
        "How does your solution handle an empty input?",
        "Can you solve this without using a stack?",
        "What happens with deeply nested inputs?",
    ],
    "linked-lists": [
        "How does your solution handle a single-node list?",
        "Are you using O(1) or O(n) extra space?",
        "How would you detect a cycle in a linked list?",
        "Can you do this in a single pass?",
        "What happens if the list is empty?",
    ],
}

# ── Approach-based questions ──────────────────────────────────────────────────
APPROACH_QUESTIONS = {
    "brute_force": [
        "Your approach is O(n²) — can you optimize it to O(n)?",
        "What data structure could eliminate the nested loop?",
        "If input was 10 million elements, how would this perform?",
    ],
    "optimized": [
        "You used a hashmap — what is the space complexity tradeoff?",
        "Why is hashmap lookup O(1) on average?",
        "Can you further reduce the space complexity?",
    ],
    "optimal": [
        "Can you prove this is the most optimal solution?",
        "How would you explain this solution to a junior developer?",
        "What follow-up variations of this problem should you prepare for?",
    ],
    "basic": [
        "Can this be optimized further in time or space?",
        "What is the exact time and space complexity?",
        "How does this scale with very large inputs?",
    ],
}

# ── Thinking quality questions ────────────────────────────────────────────────
THINKING_QUESTIONS = {
    "no_explanation": [
        "Walk me through your thought process before you started coding.",
        "Why did you choose this approach over alternatives?",
    ],
    "no_complexity": [
        "What is the time and space complexity of your solution?",
        "How does the complexity change with input size?",
    ],
    "no_edge_cases": [
        "What edge cases did you consider before writing this?",
        "How does your solution handle empty or null inputs?",
    ],
    "good_explanation": [
        "If you had to optimize this further, where would you start?",
        "How would you test this solution thoroughly?",
    ],
}


def generate_followup_questions(
    user_code: str,
    thinking_text: str,
    problem: dict
) -> list:
    """
    Generate 3 relevant, accurate interview questions.
    Based on: actual code + problem topic + thinking quality.
    """
    topic    = problem.get("topic", "arrays")
    approach = _detect_approach(user_code)
    thinking = (thinking_text or "").lower()

    questions = []

    # 1. One approach-based question (most relevant)
    approach_qs = APPROACH_QUESTIONS.get(approach, APPROACH_QUESTIONS["basic"])
    questions.append(approach_qs[0])

    # 2. One topic-based question
    topic_qs = TOPIC_QUESTIONS.get(topic, TOPIC_QUESTIONS["arrays"])
    # Pick one that's not already covered
    for q in topic_qs:
        if q not in questions:
            questions.append(q)
            break

    # 3. One thinking-quality question
    if not thinking.strip():
        questions.append(THINKING_QUESTIONS["no_explanation"][0])
    elif not any(w in thinking for w in ["o(n", "o(1", "complexity", "linear"]):
        questions.append(THINKING_QUESTIONS["no_complexity"][0])
    elif not any(w in thinking for w in ["edge", "empty", "null", "zero"]):
        questions.append(THINKING_QUESTIONS["no_edge_cases"][0])
    else:
        questions.append(THINKING_QUESTIONS["good_explanation"][0])

    return questions[:3]  # Max 3 questions


def _detect_approach(code: str) -> str:
    c = code.lower()
    if "dict" in c or "{}" in c or "defaultdict" in c or "counter" in c:
        return "optimized"
    if ("lo" in c and "hi" in c) or ("left" in c and "right" in c and "mid" in c):
        return "optimal"
    if c.count("for") >= 2:
        return "brute_force"
    return "basic"