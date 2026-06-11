import json
import os

# Always resolve path relative to this file — fixes the path bug
_DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
_PROBLEMS_FILE = os.path.join(_DATA_DIR, "problems.json")

_cache = None

def load_problems() -> dict:
    """Load problems from JSON. Cached after first load."""
    global _cache
    if _cache is None:
        with open(_PROBLEMS_FILE, "r", encoding="utf-8") as f:
            _cache = json.load(f)
    return _cache

def get_problem_by_id(problem_id: str) -> dict | None:
    problems = load_problems()
    return problems.get(problem_id)

def get_problems_by_topic(topic: str) -> list:
    problems = load_problems()
    return [p for p in problems.values() if p["topic"] == topic]

def get_problems_by_difficulty(difficulty: str) -> list:
    problems = load_problems()
    return [p for p in problems.values() if p["difficulty"] == difficulty]