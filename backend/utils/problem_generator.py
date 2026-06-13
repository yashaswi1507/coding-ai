"""
ThinkCode AI — Problem Generator
Two modes:
1. Ollama (Local LLM) — generates new problems when available
2. Problem Bank — releases pre-written problems when Ollama not available
"""

import json
import os
import random
import requests
from datetime import datetime

OLLAMA_URL   = "http://localhost:11434/api/generate"
BANK_FILE    = os.path.join(os.path.dirname(__file__), "../data/problem_bank.json")
PROBLEMS_FILE = os.path.join(os.path.dirname(__file__), "../data/problems.json")


# ── Ollama Check ──────────────────────────────────────────────────────────────

def is_ollama_available() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False


def generate_with_ollama(topic: str, difficulty: str) -> dict | None:
    """Generate a new problem using local Ollama LLM."""
    prompt = f"""Generate a coding interview problem for ThinkCode AI platform.

Topic: {topic}
Difficulty: {difficulty}

Return ONLY a valid JSON object (no markdown, no extra text):
{{
  "id": "unique_snake_case_id",
  "title": "Problem Title",
  "topic": "{topic}",
  "difficulty": "{difficulty}",
  "question": "Clear problem description with examples",
  "hints": ["hint 1", "hint 2", "hint 3"],
  "companies": ["Company1", "Company2"],
  "starter_code": "from typing import List\\n\\nclass Solution:\\n    def methodName(self, ...) -> ...:\\n        pass\\n\\ndef solve(...):\\n    return Solution().methodName(...)",
  "optimal_solution": "def solve(...):\\n    # optimal solution here",
  "optimal_explanation": "Brief explanation of approach and complexity",
  "test_cases": [
    {{"input": {{"param": "value"}}, "output": "expected_output"}},
    {{"input": {{"param": "value2"}}, "output": "expected_output2"}},
    {{"input": {{"param": "value3"}}, "output": "expected_output3"}}
  ]
}}"""

    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.7, "max_tokens": 1500}
        }, timeout=60)

        if response.status_code != 200:
            return None

        text = response.json().get("response", "").strip()
        # Extract JSON
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start == -1 or end == 0:
            return None

        problem = json.loads(text[start:end])
        problem["source"]      = "ollama_generated"
        problem["created_at"]  = datetime.now().isoformat()
        problem["visible_test_cases"] = problem.get("test_cases", [])[:3]
        problem["hidden_test_cases"]  = problem.get("test_cases", [])[3:]
        return problem

    except Exception as e:
        print(f"Ollama generation failed: {e}")
        return None


# ── Problem Bank ──────────────────────────────────────────────────────────────

def load_bank() -> list:
    if not os.path.exists(BANK_FILE):
        return []
    with open(BANK_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_bank(bank: list):
    with open(BANK_FILE, "w", encoding="utf-8") as f:
        json.dump(bank, f, indent=2, ensure_ascii=False)


def get_unreleased_from_bank() -> list:
    """Get problems from bank that haven't been released yet."""
    bank = load_bank()
    with open(PROBLEMS_FILE, "r", encoding="utf-8") as f:
        active = json.load(f)
    active_ids = set(active.keys())
    return [p for p in bank if p["id"] not in active_ids]


# ── Auto Release ──────────────────────────────────────────────────────────────

def release_problems(count: int = 3) -> list:
    """
    Release N new problems. Uses Ollama if available, else problem bank.
    Returns list of newly added problem titles.
    """
    with open(PROBLEMS_FILE, "r", encoding="utf-8") as f:
        problems = json.load(f)

    added = []
    topics     = ["arrays", "strings", "dynamic-programming", "graphs", "trees", "binary-search", "stack"]
    difficulties = ["easy", "medium", "hard"]

    # Try Ollama first
    if is_ollama_available():
        print("🤖 Ollama available — generating problems with LLM...")
        for _ in range(count):
            topic  = random.choice(topics)
            diff   = random.choice(difficulties[:2])  # mostly easy/medium
            problem = generate_with_ollama(topic, diff)
            if problem and problem.get("id") and problem["id"] not in problems:
                problems[problem["id"]] = problem
                added.append(problem["title"])
                print(f"✅ Generated: {problem['title']}")

    # Fallback to bank for remaining
    remaining = count - len(added)
    if remaining > 0:
        unreleased = get_unreleased_from_bank()
        to_release = unreleased[:remaining]
        for p in to_release:
            if p["id"] not in problems:
                p["released_at"] = datetime.now().isoformat()
                problems[p["id"]] = p
                added.append(p["title"])
                print(f"📚 Released from bank: {p['title']}")

    if added:
        with open(PROBLEMS_FILE, "w", encoding="utf-8") as f:
            json.dump(problems, f, indent=2, ensure_ascii=False)

    return added


def get_generator_status() -> dict:
    unreleased = get_unreleased_from_bank()
    with open(PROBLEMS_FILE, "r", encoding="utf-8") as f:
        active = json.load(f)

    ollama = is_ollama_available()
    return {
        "ollama_available":   ollama,
        "active_problems":    len(active),
        "bank_unreleased":    len(unreleased),
        "mode":               "ollama" if ollama else "bank",
        "can_release_more":   len(unreleased) > 0 or ollama,
    }