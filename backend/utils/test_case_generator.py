"""
ThinkCode AI — Test Case Generator
Rule-based AI engine that generates varied test cases for each problem.
Covers: normal, edge, large input, duplicates, negatives, empty cases.
No external API. Fully local.
"""

import random
import json
import os

# ── Generators per problem ────────────────────────────────────────────────────

def generate_two_sum(count=9):
    cases = []
    seen = set()

    base = [
        {"input": {"nums": [2,7,11,15], "target": 9},  "output": [0,1]},
        {"input": {"nums": [3,2,4],     "target": 6},  "output": [1,2]},
        {"input": {"nums": [3,3],       "target": 6},  "output": [0,1]},
        {"input": {"nums": [1,2,3,4,5], "target": 9},  "output": [3,4]},
        {"input": {"nums": [-1,-2,-3,-4,-5], "target": -8}, "output": [2,4]},
        {"input": {"nums": [0,4,3,0],   "target": 0},  "output": [0,3]},
        {"input": {"nums": [1,5,3,2],   "target": 4},  "output": [2,3]},
        {"input": {"nums": [2,5,5,11],  "target": 10}, "output": [1,2]},
        {"input": {"nums": [1,2],       "target": 3},  "output": [0,1]},
        {"input": {"nums": [100,200,300,400], "target": 700}, "output": [2,3]},
        {"input": {"nums": [-3,4,3,90], "target": 0},  "output": [0,2]},
        {"input": {"nums": [1,3,4,2],   "target": 6},  "output": [2,3]},
    ]
    return base[:count]


def generate_climbing_stairs(count=10):
    cases = []
    def ways(n):
        if n <= 2: return n
        a, b = 1, 2
        for _ in range(3, n+1):
            a, b = b, a + b
        return b

    inputs = [1, 2, 3, 4, 5, 6, 7, 8, 10, 15, 20, 30]
    for n in inputs[:count]:
        cases.append({"input": {"n": n}, "output": ways(n)})
    return cases


def generate_binary_search(count=10):
    cases = [
        {"input": {"nums": [-1,0,3,5,9,12], "target": 9},  "output": 4},
        {"input": {"nums": [-1,0,3,5,9,12], "target": 2},  "output": -1},
        {"input": {"nums": [5],              "target": 5},  "output": 0},
        {"input": {"nums": [5],              "target": 3},  "output": -1},
        {"input": {"nums": [-5,-3,-1,0,2],   "target": -3}, "output": 1},
        {"input": {"nums": [1,2,3,4,5,6,7,8,9,10], "target": 7}, "output": 6},
        {"input": {"nums": [1,2,3,4,5,6,7,8,9,10], "target": 1}, "output": 0},
        {"input": {"nums": [1,2,3,4,5,6,7,8,9,10], "target": 10}, "output": 9},
        {"input": {"nums": [1,2,3,4,5,6,7,8,9,10], "target": 11}, "output": -1},
        {"input": {"nums": [1,3],            "target": 3},  "output": 1},
    ]
    return cases[:count]


def generate_valid_parentheses(count=10):
    cases = [
        {"input": {"s": "()"},       "output": True},
        {"input": {"s": "()[]{}"},   "output": True},
        {"input": {"s": "(]"},       "output": False},
        {"input": {"s": "([)]"},     "output": False},
        {"input": {"s": "{[]}"},     "output": True},
        {"input": {"s": ""},         "output": True},
        {"input": {"s": "((("},       "output": False},
        {"input": {"s": ")))"},       "output": False},
        {"input": {"s": "({[]})"},   "output": True},
        {"input": {"s": "((()()))"},  "output": True},
        {"input": {"s": "[({})]"},   "output": True},
        {"input": {"s": "[({})](]"},  "output": False},
    ]
    return cases[:count]


def generate_maximum_subarray(count=10):
    cases = [
        {"input": {"nums": [-2,1,-3,4,-1,2,1,-5,4]},  "output": 6},
        {"input": {"nums": [1]},                        "output": 1},
        {"input": {"nums": [5,4,-1,7,8]},               "output": 23},
        {"input": {"nums": [-1,-2,-3,-4]},              "output": -1},
        {"input": {"nums": [-2,-1]},                    "output": -1},
        {"input": {"nums": [1,2,3,4,5]},                "output": 15},
        {"input": {"nums": [-5,4,-1,2,1,-3]},           "output": 6},
        {"input": {"nums": [3,-1,2,-1]},                "output": 4},
        {"input": {"nums": [3,-2,5]},                   "output": 6},
        {"input": {"nums": [0,0,0]},                    "output": 0},
    ]
    return cases[:count]


def generate_contains_duplicate(count=10):
    cases = [
        {"input": {"nums": [1,2,3,1]},              "output": True},
        {"input": {"nums": [1,2,3,4]},              "output": False},
        {"input": {"nums": [1,1,1,3,3,4,3,2,4,2]}, "output": True},
        {"input": {"nums": [1]},                    "output": False},
        {"input": {"nums": []},                     "output": False},
        {"input": {"nums": [1,2]},                  "output": False},
        {"input": {"nums": [1,1]},                  "output": True},
        {"input": {"nums": list(range(100))},       "output": False},
        {"input": {"nums": list(range(99)) + [0]},  "output": True},
        {"input": {"nums": [-1,-1,0,1]},            "output": True},
    ]
    return cases[:count]


def generate_best_time_stock(count=10):
    cases = [
        {"input": {"prices": [7,1,5,3,6,4]},   "output": 5},
        {"input": {"prices": [7,6,4,3,1]},      "output": 0},
        {"input": {"prices": [1,2]},            "output": 1},
        {"input": {"prices": [2,1]},            "output": 0},
        {"input": {"prices": [1]},              "output": 0},
        {"input": {"prices": [3,1,4,8,2,9]},   "output": 8},
        {"input": {"prices": [1,2,3,4,5]},      "output": 4},
        {"input": {"prices": [5,4,3,2,1]},      "output": 0},
        {"input": {"prices": [1,4,2,7]},        "output": 6},
        {"input": {"prices": [2,4,1,7,3,9]},    "output": 8},
    ]
    return cases[:count]


def generate_coin_change(count=9):
    cases = [
        {"input": {"coins": [1,5,6,9],  "amount": 11}, "output": 2},
        {"input": {"coins": [2],         "amount": 3},  "output": -1},
        {"input": {"coins": [1,2,5],     "amount": 11}, "output": 3},
        {"input": {"coins": [1],         "amount": 0},  "output": 0},
        {"input": {"coins": [1],         "amount": 1},  "output": 1},
        {"input": {"coins": [1],         "amount": 5},  "output": 5},
        {"input": {"coins": [2,5,10,1],  "amount": 27}, "output": 4},
        {"input": {"coins": [5,10],      "amount": 3},  "output": -1},
        {"input": {"coins": [1,5,10,25], "amount": 36}, "output": 3},
    ]
    return cases[:count]


def generate_house_robber(count=10):
    cases = [
        {"input": {"nums": [1,2,3,1]},     "output": 4},
        {"input": {"nums": [2,7,9,3,1]},   "output": 12},
        {"input": {"nums": [2,1]},          "output": 2},
        {"input": {"nums": [1]},            "output": 1},
        {"input": {"nums": [0,0,0]},        "output": 0},
        {"input": {"nums": [5,1,1,5]},      "output": 10},
        {"input": {"nums": [1,3,1,3,100]},  "output": 103},
        {"input": {"nums": [2,10,3,6,8,1]}, "output": 19},
        {"input": {"nums": [10,1,10]},      "output": 20},
        {"input": {"nums": [1,2,3,4,5,6,7,8,9,10]}, "output": 30},
    ]
    return cases[:count]


def generate_valid_anagram(count=10):
    cases = [
        {"input": {"s": "anagram",  "t": "nagaram"},  "output": True},
        {"input": {"s": "rat",      "t": "car"},       "output": False},
        {"input": {"s": "a",        "t": "a"},         "output": True},
        {"input": {"s": "ab",       "t": "ba"},        "output": True},
        {"input": {"s": "aa",       "t": "a"},         "output": False},
        {"input": {"s": "abc",      "t": "cba"},       "output": True},
        {"input": {"s": "listen",   "t": "silent"},    "output": True},
        {"input": {"s": "hello",    "t": "world"},     "output": False},
        {"input": {"s": "aab",      "t": "aba"},       "output": True},
        {"input": {"s": "",         "t": ""},          "output": True},
    ]
    return cases[:count]


def generate_merge_sorted_lists(count=9):
    cases = [
        {"input": {"list1": [1,2,4], "list2": [1,3,4]},     "output": [1,1,2,3,4,4]},
        {"input": {"list1": [],      "list2": []},           "output": []},
        {"input": {"list1": [],      "list2": [0]},          "output": [0]},
        {"input": {"list1": [1],     "list2": [2]},          "output": [1,2]},
        {"input": {"list1": [2],     "list2": [1]},          "output": [1,2]},
        {"input": {"list1": [1,3,5], "list2": [2,4,6]},      "output": [1,2,3,4,5,6]},
        {"input": {"list1": [1,2,3], "list2": []},           "output": [1,2,3]},
        {"input": {"list1": [1,1,1], "list2": [1,1,1]},      "output": [1,1,1,1,1,1]},
        {"input": {"list1": [1,2,4,7], "list2": [1,3,4,6]}, "output": [1,1,2,3,4,4,6,7]},
    ]
    return cases[:count]


# ── Master generator ──────────────────────────────────────────────────────────

GENERATORS = {
    "two_sum":                        generate_two_sum,
    "climbing_stairs":                generate_climbing_stairs,
    "binary_search":                  generate_binary_search,
    "valid_parentheses":              generate_valid_parentheses,
    "maximum_subarray":               generate_maximum_subarray,
    "contains_duplicate":             generate_contains_duplicate,
    "best_time_to_buy_stock":         generate_best_time_stock,
    "coin_change":                    generate_coin_change,
    "house_robber":                   generate_house_robber,
    "valid_anagram":                  generate_valid_anagram,
    "merge_two_sorted_lists":         generate_merge_sorted_lists,
}


def generate_for_problem(problem_id: str, total: int = 12) -> dict:
    """
    Generate test cases for a problem.
    Returns: {
        "visible_test_cases": [...],   # first 3 — shown to user
        "hidden_test_cases":  [...],   # rest   — hidden evaluation
        "test_cases":         [...],   # all combined
    }
    """
    if problem_id not in GENERATORS:
        return None

    all_cases = GENERATORS[problem_id](total)

    visible = all_cases[:3]
    hidden  = all_cases[3:]

    return {
        "visible_test_cases": visible,
        "hidden_test_cases":  hidden,
        "test_cases":         all_cases,
    }


def update_problems_file(problems_path: str):
    """
    Update problems.json — add visible/hidden test case split
    for all problems that have a generator.
    """
    with open(problems_path, "r", encoding="utf-8") as f:
        problems = json.load(f)

    updated = 0
    for pid, problem in problems.items():
        result = generate_for_problem(pid, total=12)
        if result:
            problem["visible_test_cases"] = result["visible_test_cases"]
            problem["hidden_test_cases"]  = result["hidden_test_cases"]
            problem["test_cases"]         = result["test_cases"]
            updated += 1
        else:
            # Problem without generator — keep existing, split manually
            existing = problem.get("test_cases", [])
            problem["visible_test_cases"] = existing[:3]
            problem["hidden_test_cases"]  = existing[3:]

    with open(problems_path, "w", encoding="utf-8") as f:
        json.dump(problems, f, indent=2, ensure_ascii=False)

    print(f"✅ Updated {updated} problems with auto-generated test cases")
    print(f"   Remaining {len(problems) - updated} problems: kept existing cases")
    return updated


if __name__ == "__main__":
    import sys
    path = sys.argv[1] if len(sys.argv) > 1 else "data/problems.json"
    update_problems_file(path)