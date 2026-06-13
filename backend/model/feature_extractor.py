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
    Supports both plain solve() and LeetCode-style class Solution format.
    """
    # Extract actual solution code from class Solution if present
    clean_code = _extract_solution_code(user_code or "")
    code_feats  = _extract_code_features(clean_code)
    think_feats = _extract_thinking_features(thinking_text or "")
    return code_feats + think_feats


def _extract_solution_code(code: str) -> str:
    """
    Extract the core solution logic from either:
    - Plain solve() function
    - LeetCode-style class Solution with method
    Returns the inner method body for analysis.
    """
    if "class Solution" not in code:
        return code

    lines = code.split("\n")
    solution_lines = []
    inside_method = False
    method_indent = 0

    for line in lines:
        stripped = line.strip()
        # Skip class definition and solve() wrapper at bottom
        if stripped.startswith("class Solution") or stripped.startswith("def solve("):
            continue
        # Find method definition inside class
        if stripped.startswith("def ") and not inside_method:
            inside_method = True
            method_indent = len(line) - len(line.lstrip())
            continue
        # Collect method body
        if inside_method:
            if stripped and len(line) - len(line.lstrip()) <= method_indent and not stripped.startswith("#"):
                inside_method = False
            else:
                solution_lines.append(line)

    extracted = "\n".join(solution_lines)
    # Fallback to full code if extraction failed
    return extracted if extracted.strip() else code


# ── Code Feature Extraction (15 features) ────────────────────────────────────

def _extract_code_features(code: str) -> list:
    """
    Language-agnostic feature extraction.
    Works for Python, Java, C++, JavaScript, C.
    """
    c = code.lower()
    lines = [l for l in code.split("\n") if l.strip()]

    # ── 0: Nested loops ───────────────────────────────────────────────────
    # All languages use for/while
    loop_keywords = c.count("for ") + c.count("for(") + c.count("while ")
    nested = 1.0 if loop_keywords >= 2 else 0.0

    # ── 1: Loop count ─────────────────────────────────────────────────────
    loop_count = min(loop_keywords, 4) / 4.0

    # ── 2: Has hashmap/dict ───────────────────────────────────────────────
    # Python: dict, {}, defaultdict, Counter
    # Java: HashMap, LinkedHashMap, TreeMap, Hashtable
    # C++: unordered_map, map, std::map
    # JS: Map, new Map, {}
    # C: struct with key-value
    hashmap_patterns = [
        "dict", "{}", "defaultdict", "counter",           # Python
        "hashmap", "linkedhashmap", "treemap",             # Java
        "unordered_map", "std::map",                       # C++
        "new map(", "map()",                               # JS
        "= {}", "seen =",                                  # Generic
    ]
    has_dict = 1.0 if any(p in c for p in hashmap_patterns) else 0.0

    # ── 3: Has set ────────────────────────────────────────────────────────
    # Python: set(), .add()
    # Java: HashSet, TreeSet, LinkedHashSet
    # C++: unordered_set, set
    # JS: new Set(), Set
    set_patterns = [
        "set()", "= set(", ".add(",                        # Python
        "hashset", "treeset", "linkedhashset",             # Java
        "unordered_set", "std::set",                       # C++
        "new set(", "new set(",                            # JS
    ]
    has_set = 1.0 if any(p in c for p in set_patterns) else 0.0

    # ── 4: Has sorting ────────────────────────────────────────────────────
    # All languages: sort keyword present
    sort_patterns = ["sort", "arrays.sort", "collections.sort",
                     "std::sort", "qsort"]
    has_sort = 1.0 if any(p in c for p in sort_patterns) else 0.0

    # ── 5: Has recursion ──────────────────────────────────────────────────
    has_recursion = _detect_recursion_universal(code)

    # ── 6: Edge case handling ─────────────────────────────────────────────
    # Python: if not, is None, len(
    # Java: == null, .isEmpty(), .length == 0
    # C++: == nullptr, .empty(), .size() == 0
    # JS: === null, === undefined, .length === 0
    edge_patterns = [
        "if not ", "is none", "== []", "return []",        # Python
        "== null", ".isempty()", ".length == 0",            # Java
        "== nullptr", ".empty()", ".size() == 0",           # C++
        "=== null", "=== undefined", ".length === 0",       # JS
        "if (!",                                            # C/C++/Java
    ]
    has_edge = 1.0 if any(p in c for p in edge_patterns) or "if len(" in c else 0.0

    # ── 7: Line count ─────────────────────────────────────────────────────
    line_count = min(len(lines), 40) / 40.0

    # ── 8: Has comments ───────────────────────────────────────────────────
    # Python: #, Java/C++/JS/C: //, /* */
    has_comments = 1.0 if ("#" in code or "//" in code or "/*" in code) else 0.0

    # ── 9: Functional/elegant pattern ────────────────────────────────────
    # Python list comp, Java streams, JS array methods
    elegant_patterns = [
        r'\[.+for.+in.+\]',     # Python list comp
        r'\.stream()\.',         # Java streams
        r'\.filter\(',           # JS/Java filter
        r'\.map\(',              # JS/Java map
        r'\.reduce\(',           # JS reduce
    ]
    has_elegant = 1.0 if any(re.search(p, c) for p in elegant_patterns) else 0.0

    # ── 10: Stack/Queue usage ─────────────────────────────────────────────
    stack_patterns = ["stack", "queue", "deque", "arraydeque",
                      "linkedlist", "priorityqueue", "collections.deque"]
    has_stack = 1.0 if any(p in c for p in stack_patterns) else 0.0

    # ── 11: Binary search pattern ─────────────────────────────────────────
    has_binsearch = 1.0 if (
        ("lo" in c and "hi" in c) or
        ("left" in c and "right" in c and "mid" in c) or
        ("low" in c and "high" in c) or
        "binarysearch" in c or "collections.binarysearch" in c
    ) else 0.0

    # ── 12: DP pattern ────────────────────────────────────────────────────
    has_dp = 1.0 if re.search(r'\bdp\b', c) or "memo" in c or "cache" in c else 0.0

    # ── 13: Two pointers ──────────────────────────────────────────────────
    has_two_ptr = 1.0 if (
        ("left" in c and "right" in c) or
        ("start" in c and "end" in c) or
        ("i" in c and "j" in c and loop_keywords >= 1)
    ) else 0.0

    # ── 14: Function/method count ─────────────────────────────────────────
    # Python: def, Java/C++: return type + name, JS: function
    func_patterns = len(re.findall(r'\bdef\s+\w+', code))        # Python
    func_patterns += len(re.findall(r'\bfunction\s+\w+', code))  # JS
    func_patterns += len(re.findall(r'\bpublic\s+\w+\s+\w+\s*\(', code))  # Java
    func_count = min(func_patterns, 5) / 5.0

    return [
        nested, loop_count, has_dict, has_set, has_sort,
        has_recursion, has_edge, line_count, has_comments, has_elegant,
        has_stack, has_binsearch, has_dp, has_two_ptr, func_count
    ]


def _detect_recursion_universal(code: str) -> float:
    """Detect recursion in any language."""
    lines = code.split("\n")
    func_names = []

    # Python
    for line in lines:
        if line.strip().startswith("def "):
            try:
                name = line.strip().split("(")[0].replace("def ", "").strip()
                func_names.append(name)
            except: pass

    # Java/C++/JS — find method names
    for match in re.finditer(r'(?:public|private|protected|static|void|int|bool|\w+)\s+(\w+)\s*\(', code):
        func_names.append(match.group(1))

    for name in func_names:
        if name in ["main", "solve", "constructor"]: continue
        if code.lower().count(name.lower()) >= 2:
            return 1.0
    return 0.0


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