"""
ThinkCode AI — AI Interviewer
Generates follow-up questions. Zero external API. Fully rule-based + model-driven.
"""

from model.feature_extractor import extract_features

QUESTION_BANK = {
    "brute_force": [
        "Your solution uses nested loops — what is the exact time complexity and can you do better?",
        "If the input size was 10 million elements, how would your solution perform?",
        "What data structure could help you avoid the repeated inner loop?",
        "Can you reduce the time complexity from O(n²) to O(n)?",
        "Walk me through exactly what happens on each iteration of your outer loop.",
    ],
    "hashmap": [
        "Why is hashmap lookup O(1) on average but O(n) in the worst case?",
        "What is the space complexity tradeoff you made by using a hashmap?",
        "How would your solution change if the input could have duplicate keys?",
        "What happens to your hashmap if there are hash collisions?",
    ],
    "sorting": [
        "Does sorting affect the original order of elements — does that matter here?",
        "You used O(n log n) sort — is there a way to solve this without sorting?",
        "What sorting algorithm does Python use internally and why?",
        "Can you solve this in O(n) without sorting using a different approach?",
    ],
    "recursion": [
        "What is the maximum call stack depth for your recursive solution?",
        "Can you convert this recursive solution to an iterative one?",
        "What happens if the input is very large and you hit Python's recursion limit?",
        "Does your recursive solution use memoization? Should it?",
    ],
    "dp": [
        "Can you explain the DP recurrence relation you used?",
        "Is this top-down or bottom-up DP? What are the tradeoffs?",
        "Can you reduce the space complexity of your DP solution?",
        "How did you identify this as a DP problem?",
    ],
    "binary_search": [
        "Why do you use lo + (hi - lo) // 2 instead of (lo + hi) // 2?",
        "What happens if lo and hi are both very large integers?",
        "Can you apply binary search to a 2D matrix?",
        "How do you handle the case where the target doesn't exist?",
    ],
    "edge_case": [
        "Great — you handled edge cases. What other edge cases could break your solution?",
        "How does your solution handle an empty input?",
        "What happens with a single-element input?",
        "Does your solution handle negative numbers correctly?",
    ],
    "general": [
        "Can your solution be optimized further in time or space?",
        "Walk me through your solution as if explaining to a junior developer.",
        "What is the time and space complexity of your full solution?",
        "What was the hardest part of this problem and how did you approach it?",
        "How would you modify your solution if the problem constraints changed?",
    ]
}


def generate_followup_questions(user_code, thinking_text, problem):
    """
    Generate context-aware interview questions based on code analysis.
    Fully local — no external API.
    """
    features = extract_features(user_code, thinking_text)
    c = user_code.lower()
    questions = []

    # Approach-based questions
    if c.count("for") >= 2 and "dict" not in c:
        questions.extend(QUESTION_BANK["brute_force"][:2])

    if "dict" in c or "{}" in c or "defaultdict" in c:
        questions.extend(QUESTION_BANK["hashmap"][:2])

    if "sort" in c:
        questions.append(QUESTION_BANK["sorting"][0])

    if _has_recursion(c):
        questions.append(QUESTION_BANK["recursion"][0])

    if "dp" in c:
        questions.append(QUESTION_BANK["dp"][0])

    if ("lo" in c and "hi" in c) or ("left" in c and "right" in c and "mid" in c):
        questions.append(QUESTION_BANK["binary_search"][0])

    if "if not" in c or "len(" in c:
        questions.append(QUESTION_BANK["edge_case"][0])

    # Always add general questions
    questions.extend(QUESTION_BANK["general"][:2])

    # Deduplicate and limit
    seen = set()
    unique = []
    for q in questions:
        if q not in seen:
            seen.add(q)
            unique.append(q)

    return unique[:5]


def _has_recursion(code_lower):
    lines = code_lower.split("\n")
    func_names = []
    for line in lines:
        if line.strip().startswith("def "):
            parts = line.strip().split("(")
            if parts:
                name = parts[0].replace("def ", "").strip()
                func_names.append(name)
    for name in func_names:
        count = code_lower.count(name)
        if count >= 2:
            return True
    return False