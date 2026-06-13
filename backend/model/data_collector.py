"""
ThinkCode AI — Training Data Collector
Collects submissions + allows manual labeling for model training.

Two sources of data:
    1. Auto-collected: every /submit/ call saves raw data here
    2. Manual labels: you review submissions and assign ground-truth scores

Data format (each sample):
{
    "id": "uuid",
    "code": "...",
    "thinking_text": "...",
    "problem_id": "two_sum",
    "topic": "arrays",
    "difficulty": "easy",
    "thinking_score": 75,         ← ground truth (0-100)
    "approach": "optimized",      ← ground truth label
    "labeled": true/false,        ← manually verified?
    "timestamp": "2024-..."
}
"""

import json
import uuid
import os
from datetime import datetime

# Paths
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, "training_data")
SUBMISSIONS_FILE = os.path.join(DATA_DIR, "submissions.json")
LABELED_FILE = os.path.join(DATA_DIR, "labeled.json")

os.makedirs(DATA_DIR, exist_ok=True)


# ── Read / Write helpers ──────────────────────────────────────────────────────

def _load_json(path: str) -> list:
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: str, data: list):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


# ── Auto-collection ───────────────────────────────────────────────────────────

def collect_submission(
    code: str,
    thinking_text: str,
    problem_id: str,
    topic: str,
    difficulty: str,
    rule_based_score: int,       # Initial score from rule-based engine
    rule_based_approach: str,    # Initial approach from rule-based engine
    passed_tests: int,
    total_tests: int,
):
    """
    Called after every submission. Saves raw data for future training.
    Rule-based scores are the initial labels — override them via manual_label().
    """
    submissions = _load_json(SUBMISSIONS_FILE)

    sample = {
        "id": str(uuid.uuid4()),
        "code": code,
        "thinking_text": thinking_text,
        "problem_id": problem_id,
        "topic": topic,
        "difficulty": difficulty,
        "thinking_score": rule_based_score,   # Will be refined by manual labeling
        "approach": rule_based_approach,
        "passed_tests": passed_tests,
        "total_tests": total_tests,
        "labeled": False,                     # Not yet manually verified
        "timestamp": datetime.now().isoformat()
    }

    submissions.append(sample)
    _save_json(SUBMISSIONS_FILE, submissions)
    return sample["id"]


# ── Manual Labeling ───────────────────────────────────────────────────────────

def get_unlabeled_samples(limit: int = 20) -> list:
    """Returns unlabeled submissions for manual review."""
    submissions = _load_json(SUBMISSIONS_FILE)
    return [s for s in submissions if not s.get("labeled", False)][:limit]


def manual_label(
    sample_id: str,
    thinking_score: int,
    approach: str,
    notes: str = ""
):
    """
    Manually assign ground-truth labels to a submission.
    These become high-quality training samples.
    """
    submissions = _load_json(SUBMISSIONS_FILE)
    labeled = _load_json(LABELED_FILE)

    for s in submissions:
        if s["id"] == sample_id:
            s["thinking_score"] = thinking_score
            s["approach"] = approach
            s["labeled"] = True
            s["label_notes"] = notes
            s["labeled_at"] = datetime.now().isoformat()
            labeled.append(s)
            break

    _save_json(SUBMISSIONS_FILE, submissions)
    _save_json(LABELED_FILE, labeled)
    print(f"✅ Labeled sample {sample_id[:8]}... → score={thinking_score}, approach={approach}")


def get_all_training_data() -> list:
    """
    Returns all available training data:
    1. Manually labeled samples (high quality, used first)
    2. Auto-collected with rule-based scores (lower quality)
    """
    labeled = _load_json(LABELED_FILE)
    submissions = _load_json(SUBMISSIONS_FILE)

    # Combine: labeled first, then unlabeled auto-collected
    labeled_ids = {s["id"] for s in labeled}
    auto = [s for s in submissions if s["id"] not in labeled_ids]

    return labeled + auto


def get_stats() -> dict:
    submissions = _load_json(SUBMISSIONS_FILE)
    labeled = _load_json(LABELED_FILE)
    return {
        "total_submissions": len(submissions),
        "labeled": len(labeled),
        "unlabeled": len(submissions) - len([s for s in submissions if s.get("labeled")]),
        "ready_for_training": len(get_all_training_data())
    }


# ── Seed Data ─────────────────────────────────────────────────────────────────

def create_seed_data():
    """
    Creates initial training data to bootstrap the model.
    Covers a range of quality levels for balanced training.
    """
    seed_samples = [
        # ── HIGH QUALITY SAMPLES ──────────────────────────────────────────────
        {
            "code": "def solve(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        complement = target - num\n        if complement in seen:\n            return [seen[complement], i]\n        seen[num] = i\n    return []",
            "thinking_text": "I'll use a hashmap to achieve O(n) time complexity. As I traverse the array, I store each number and its index. For each number, I check if its complement (target - num) already exists in the hashmap. If yes, I found the pair. This is better than brute force O(n²). Space complexity is O(n) for the hashmap.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 92, "approach": "optimized", "labeled": True
        },
        {
            "code": "def solve(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]",
            "thinking_text": "I'll check all pairs of numbers. For each number, I check every other number to see if they sum to target.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 25, "approach": "brute_force", "labeled": True
        },
        {
            "code": "def solve(nums, target):\n    for i in range(len(nums)):\n        for j in range(i+1, len(nums)):\n            if nums[i] + nums[j] == target:\n                return [i, j]",
            "thinking_text": "",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 10, "approach": "brute_force", "labeled": True
        },
        {
            "code": "def solve(nums, target):\n    seen = {}\n    for i, num in enumerate(nums):\n        comp = target - num\n        if comp in seen:\n            return [seen[comp], i]\n        seen[num] = i",
            "thinking_text": "Hashmap approach. O(n) time, O(n) space. Check complement for each number.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 65, "approach": "optimized", "labeled": True
        },
        {
            "code": "def solve(n):\n    if n <= 2:\n        return n\n    dp = [0] * (n + 1)\n    dp[1] = 1\n    dp[2] = 2\n    for i in range(3, n + 1):\n        dp[i] = dp[i-1] + dp[i-2]\n    return dp[n]",
            "thinking_text": "This is a Fibonacci-like DP problem. At each step n, I can arrive from n-1 or n-2. So ways(n) = ways(n-1) + ways(n-2). I'll use bottom-up DP with O(n) time and space. Could optimize to O(1) space by keeping only last two values.",
            "problem_id": "climbing_stairs", "topic": "dynamic-programming", "difficulty": "easy",
            "thinking_score": 88, "approach": "optimized", "labeled": True
        },
        {
            "code": "def solve(prices):\n    min_price = float('inf')\n    max_profit = 0\n    for price in prices:\n        if price < min_price:\n            min_price = price\n        elif price - min_price > max_profit:\n            max_profit = price - min_price\n    return max_profit",
            "thinking_text": "I track the minimum price seen so far and at each step compute potential profit. O(n) time, O(1) space. One pass is enough because we must buy before sell.",
            "problem_id": "best_time_to_buy_stock", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 85, "approach": "optimal", "labeled": True
        },
        {
            "code": "def solve(s):\n    left = 0\n    seen = {}\n    max_len = 0\n    for right, char in enumerate(s):\n        if char in seen and seen[char] >= left:\n            left = seen[char] + 1\n        seen[char] = right\n        max_len = max(max_len, right - left + 1)\n    return max_len",
            "thinking_text": "Sliding window with hashmap. I expand the window to the right and shrink from the left when a duplicate is found. O(n) time and space. The key insight is storing the last seen index to jump left pointer efficiently.",
            "problem_id": "longest_substring_without_repeating", "topic": "strings", "difficulty": "medium",
            "thinking_score": 90, "approach": "optimal", "labeled": True
        },
        {
            "code": "def solve(nums):\n    curr = nums[0]\n    best = nums[0]\n    for num in nums[1:]:\n        curr = max(num, curr + num)\n        best = max(best, curr)\n    return best",
            "thinking_text": "Kadane's algorithm. At each position, decide: extend previous subarray or start fresh. curr = max(num, curr + num). Track global max.",
            "problem_id": "maximum_subarray", "topic": "dynamic-programming", "difficulty": "medium",
            "thinking_score": 82, "approach": "optimal", "labeled": True
        },
        {
            "code": "def solve(nums):\n    max_sum = float('-inf')\n    for i in range(len(nums)):\n        for j in range(i, len(nums)):\n            curr = sum(nums[i:j+1])\n            max_sum = max(max_sum, curr)\n    return max_sum",
            "thinking_text": "Check all subarrays and track max sum.",
            "problem_id": "maximum_subarray", "topic": "dynamic-programming", "difficulty": "medium",
            "thinking_score": 20, "approach": "brute_force", "labeled": True
        },
        {
            "code": "def solve(nums, target):\n    lo, hi = 0, len(nums) - 1\n    while lo <= hi:\n        mid = lo + (hi - lo) // 2\n        if nums[mid] == target:\n            return mid\n        elif nums[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1",
            "thinking_text": "Classic binary search. Divide search space in half each iteration. O(log n) time, O(1) space. Using lo + (hi-lo)//2 to avoid integer overflow.",
            "problem_id": "binary_search", "topic": "binary-search", "difficulty": "easy",
            "thinking_score": 88, "approach": "optimal", "labeled": True
        },

        # ── JAVA SAMPLES ──────────────────────────────────────────────────────
        {
            "code": "import java.util.*;\npublic class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        HashMap<Integer, Integer> seen = new HashMap<>();\n        for (int i = 0; i < nums.length; i++) {\n            int comp = target - nums[i];\n            if (seen.containsKey(comp)) return new int[]{seen.get(comp), i};\n            seen.put(nums[i], i);\n        }\n        return new int[]{};\n    }\n}",
            "thinking_text": "Using HashMap for O(1) lookup. For each number check if complement exists. O(n) time O(n) space.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 88, "approach": "optimized", "labeled": True
        },
        {
            "code": "import java.util.*;\npublic class Solution {\n    public int[] twoSum(int[] nums, int target) {\n        for (int i = 0; i < nums.length; i++)\n            for (int j = i+1; j < nums.length; j++)\n                if (nums[i] + nums[j] == target) return new int[]{i, j};\n        return new int[]{};\n    }\n}",
            "thinking_text": "Checking all pairs of numbers.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 20, "approach": "brute_force", "labeled": True
        },
        {
            "code": "import java.util.*;\npublic class Solution {\n    public boolean containsDuplicate(int[] nums) {\n        HashSet<Integer> seen = new HashSet<>();\n        for (int num : nums) { if (!seen.add(num)) return true; }\n        return false;\n    }\n}",
            "thinking_text": "HashSet add returns false if element exists. O(n) time O(n) space elegant solution.",
            "problem_id": "contains_duplicate", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 85, "approach": "optimized", "labeled": True
        },
        # ── C++ SAMPLES ───────────────────────────────────────────────────────
        {
            "code": "#include<vector>\n#include<unordered_map>\nusing namespace std;\nclass Solution{public:\n    vector<int> twoSum(vector<int>& nums,int target){\n        unordered_map<int,int> seen;\n        for(int i=0;i<nums.size();i++){\n            int c=target-nums[i];\n            if(seen.count(c)) return {seen[c],i};\n            seen[nums[i]]=i;\n        }\n        return {};\n    }\n};",
            "thinking_text": "unordered_map gives O(1) average lookup. Single pass O(n) time O(n) space. Much better than nested loops.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 90, "approach": "optimized", "labeled": True
        },
        {
            "code": "#include<vector>\nusing namespace std;\nclass Solution{public:\n    int search(vector<int>&nums,int target){\n        int lo=0,hi=nums.size()-1;\n        while(lo<=hi){int mid=lo+(hi-lo)/2;\n            if(nums[mid]==target)return mid;\n            else if(nums[mid]<target)lo=mid+1;\n            else hi=mid-1;}\n        return -1;\n    }\n};",
            "thinking_text": "Binary search. lo+(hi-lo)/2 avoids overflow. O(log n) time O(1) space.",
            "problem_id": "binary_search", "topic": "binary-search", "difficulty": "easy",
            "thinking_score": 88, "approach": "optimal", "labeled": True
        },
        # ── JAVASCRIPT SAMPLES ────────────────────────────────────────────────
        {
            "code": "var twoSum=function(nums,target){\n    const seen=new Map();\n    for(let i=0;i<nums.length;i++){\n        const c=target-nums[i];\n        if(seen.has(c))return[seen.get(c),i];\n        seen.set(nums[i],i);\n    }\n    return[];\n};",
            "thinking_text": "Map for O(1) lookup. Check complement each iteration. O(n) time O(n) space.",
            "problem_id": "two_sum", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 82, "approach": "optimized", "labeled": True
        },
        {
            "code": "var containsDuplicate=function(nums){\n    return new Set(nums).size!==nums.length;\n};",
            "thinking_text": "Set removes duplicates. Compare sizes. O(n) time O(n) space. Clean one-liner optimal solution.",
            "problem_id": "contains_duplicate", "topic": "arrays", "difficulty": "easy",
            "thinking_score": 90, "approach": "optimal", "labeled": True
        },
    ]

    labeled = _load_json(LABELED_FILE)
    existing_ids = {s.get("id") for s in labeled}

    added = 0
    for sample in seed_samples:
        sample["id"] = str(uuid.uuid4())
        sample["passed_tests"] = 3
        sample["total_tests"] = 3
        sample["timestamp"] = datetime.now().isoformat()
        sample["labeled_at"] = datetime.now().isoformat()
        if sample["id"] not in existing_ids:
            labeled.append(sample)
            added += 1

    _save_json(LABELED_FILE, labeled)
    print(f"✅ Created {added} seed training samples in {LABELED_FILE}")
    return added