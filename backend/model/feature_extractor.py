"""
Feature Extractor for ThinkCode AI
Converts raw code + thinking text into a 25-dimensional feature vector.
This vector is the input to the PyTorch thinking model.
"""

import re
import ast

# ── Technical vocabulary for thinking text scoring ────────────────────────────
COMPLEXITY_WORDS = [
    "o(n)", "o(1)", "o(log", "o(n^2)", "o(n²)", "o(nlogn)",
    "time complexity", "space complexity", "complexity", "linear", "quadratic",
    "logarithmic", "constant time", "amortized"
]

OPTIMIZATION_WORDS = [
    "optimize", "optimized", "optimization", "efficient", "faster",
    "better approach", "reduce", "instead of", "rather than", "improve",
    "bottleneck", "tradeoff", "trade-off", "versus", "vs"
]

EDGE_CASE_WORDS = [
    "edge case", "empty", "null", "none", "zero", "negative", "single element",
    "empty array", "empty string", "overflow", "underflow", "boundary",
    "corner case", "special case", "duplicate"
]

DATA_STRUCTURE_WORDS = [
    "hashmap", "hash map", "dictionary", "dict", "hashtable", "hash table",
    "array", "list", "stack", "queue", "tree", "graph", "heap", "trie",
    "linked list", "set", "deque", "priority queue"
]

ALGORITHM_WORDS = [
    "binary search", "two pointer", "sliding window", "dynamic programming",
    "recursion", "iteration", "bfs", "dfs", "greedy", "divide and conquer",
    "memoization", "backtracking", "sorting", "kadane"
]


def extract_features(user_code: str, thinking_text: str) -> list:
    """
    Extract a 25-dimensional feature vector from code + thinking text.
    All values are normalized to [0, 1] range for stable training.

    Feature layout:
        [0-14]  Code features (15 features)
        [15-24] Thinking text features (10 features)
    """
    code_feats = _extract_code_features(user_code or "")
    think_feats = _extract_thinking_features(thinking_text or "")
    return code_feats + think_feats


# ── Code Feature Extraction (15 features) ────────────────────────────────────

def _extract_code_features(code: str) -> list:
    c = code.lower()
    lines = [l for l in code.split("\n") if l.strip()]

    # 0: nested loops (bool)
    nested = 1.0 if c.count("for ") >= 2 or c.count("while ") >= 2 else 0.0

    # 1: loop count (normalized 0-1, cap at 4)
    loop_count = min((c.count("for ") + c.count("while ")), 4) / 4.0

    # 2: uses hashmap / dict (bool)
    has_dict = 1.0 if ("dict" in c or "{}" in c or "= {}" in c or
                        "defaultdict" in c or "counter" in c) else 0.0

    # 3: uses set (bool)
    has_set = 1.0 if ("set()" in c or "= set(" in c or "seen = {" in c) else 0.0

    # 4: uses sorting (bool)
    has_sort = 1.0 if "sort" in c else 0.0

    # 5: uses recursion (bool) — function calls itself
    has_recursion = _detect_recursion(code)

    # 6: edge case handling (bool)
    has_edge = 1.0 if ("if not " in c or "if len(" in c or
                        "is none" in c or "== []" in c or
                        "== 0" in c or "return []" in c) else 0.0

    # 7: line count (normalized 0-1, cap at 40 lines)
    line_count = min(len(lines), 40) / 40.0

    # 8: has comments (bool)
    has_comments = 1.0 if "#" in code else 0.0

    # 9: list comprehension usage (bool)
    has_listcomp = 1.0 if re.search(r'\[.+for.+in.+\]', c) else 0.0

    # 10: uses defaultdict (bool)
    has_defaultdict = 1.0 if "defaultdict" in c else 0.0

    # 11: binary search pattern (lo/hi/mid) (bool)
    has_binsearch = 1.0 if (("lo" in c and "hi" in c) or
                             ("left" in c and "right" in c and "mid" in c)) else 0.0

    # 12: DP array pattern (bool)
    has_dp = 1.0 if re.search(r'\bdp\b', c) else 0.0

    # 13: two-pointer pattern (bool)
    has_two_ptr = 1.0 if (("left" in c and "right" in c) and
                           "sort" in c) else 0.0

    # 14: function count (normalized 0-1, cap at 5)
    func_count = min(len(re.findall(r'\bdef\s+\w+', code)), 5) / 5.0

    return [
        nested, loop_count, has_dict, has_set, has_sort,
        has_recursion, has_edge, line_count, has_comments, has_listcomp,
        has_defaultdict, has_binsearch, has_dp, has_two_ptr, func_count
    ]


def _detect_recursion(code: str) -> float:
    """Check if any function calls itself (recursion)."""
    try:
        tree = ast.parse(code)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_name = node.func_name if hasattr(node, 'func_name') else node.name
                for child in ast.walk(node):
                    if isinstance(child, ast.Call):
                        if isinstance(child.func, ast.Name):
                            if child.func.id == func_name:
                                return 1.0
    except Exception:
        pass
    # Fallback: simple string check
    lines = code.split("\n")
    for line in lines:
        if "return " in line and "(" in line:
            return 0.5
    return 0.0


# ── Thinking Text Feature Extraction (10 features) ───────────────────────────

def _extract_thinking_features(text: str) -> list:
    if not text or not text.strip():
        return [0.0] * 10

    t = text.lower()
    words = t.split()
    sentences = re.split(r'[.!?]+', t)
    sentences = [s.strip() for s in sentences if s.strip()]

    # 15: word count (normalized 0-1, cap at 200 words)
    word_count = min(len(words), 200) / 200.0

    # 16: mentions complexity (bool)
    mentions_complexity = 1.0 if any(w in t for w in COMPLEXITY_WORDS) else 0.0

    # 17: mentions optimization (bool)
    mentions_opt = 1.0 if any(w in t for w in OPTIMIZATION_WORDS) else 0.0

    # 18: mentions edge cases (bool)
    mentions_edge = 1.0 if any(w in t for w in EDGE_CASE_WORDS) else 0.0

    # 19: mentions data structures (bool)
    mentions_ds = 1.0 if any(w in t for w in DATA_STRUCTURE_WORDS) else 0.0

    # 20: sentence count (normalized 0-1, cap at 10)
    sent_count = min(len(sentences), 10) / 10.0

    # 21: technical word density (0-1)
    all_tech = COMPLEXITY_WORDS + OPTIMIZATION_WORDS + DATA_STRUCTURE_WORDS + ALGORITHM_WORDS
    tech_hits = sum(1 for w in all_tech if w in t)
    tech_density = min(tech_hits / 10.0, 1.0)

    # 22: explicit Big-O notation (bool)
    has_bigo = 1.0 if re.search(r'o\([^)]+\)', t) else 0.0

    # 23: mentions algorithms by name (bool)
    mentions_algo = 1.0 if any(w in t for w in ALGORITHM_WORDS) else 0.0

    # 24: explanation quality score (0-1)
    # Combines length + vocabulary + structure
    quality = _explanation_quality(t, words, sentences)

    return [
        word_count, mentions_complexity, mentions_opt, mentions_edge,
        mentions_ds, sent_count, tech_density, has_bigo,
        mentions_algo, quality
    ]


def _explanation_quality(text: str, words: list, sentences: list) -> float:
    """
    Heuristic quality score for a thinking explanation.
    Based on length, vocabulary richness, and technical depth.
    """
    score = 0.0

    # Length quality (0-0.3)
    if len(words) >= 10:
        score += 0.1
    if len(words) >= 30:
        score += 0.1
    if len(words) >= 60:
        score += 0.1

    # Technical vocabulary (0-0.4)
    all_tech = (COMPLEXITY_WORDS + OPTIMIZATION_WORDS +
                DATA_STRUCTURE_WORDS + ALGORITHM_WORDS + EDGE_CASE_WORDS)
    tech_count = sum(1 for w in all_tech if w in text)
    score += min(tech_count * 0.1, 0.4)

    # Structure quality (0-0.3)
    if len(sentences) >= 2:
        score += 0.1
    if any(w in text for w in ["because", "since", "therefore", "so", "thus"]):
        score += 0.1
    if any(w in text for w in ["first", "then", "finally", "next", "also"]):
        score += 0.1

    return min(score, 1.0)


def get_feature_names() -> list:
    """Returns human-readable names for all 25 features (useful for debugging)."""
    return [
        # Code features
        "nested_loops", "loop_count", "has_dict", "has_set", "has_sort",
        "has_recursion", "has_edge_case", "line_count", "has_comments",
        "has_listcomp", "has_defaultdict", "has_binsearch", "has_dp",
        "has_two_ptr", "func_count",
        # Thinking features
        "word_count", "mentions_complexity", "mentions_optimization",
        "mentions_edge_cases", "mentions_ds", "sentence_count",
        "tech_density", "has_bigo", "mentions_algo", "explanation_quality"
    ]