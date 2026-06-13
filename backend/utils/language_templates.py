"""
ThinkCode AI — Language Templates
Generates starter code for each supported language.
"""

SUPPORTED_LANGUAGES = ["Python", "Java", "C++", "JavaScript", "C"]

# Language metadata
LANGUAGE_INFO = {
    "Python":     {"icon": "🐍", "extension": ".py",   "comment": "#",  "run": "python"},
    "Java":       {"icon": "☕", "extension": ".java", "comment": "//", "run": "javac+java"},
    "C++":        {"icon": "⚙️", "extension": ".cpp",  "comment": "//", "run": "g++"},
    "JavaScript": {"icon": "🟨", "extension": ".js",   "comment": "//", "run": "node"},
    "C":          {"icon": "🔧", "extension": ".c",    "comment": "//", "run": "gcc"},
}

# Templates per problem per language
PROBLEM_TEMPLATES = {
    "two_sum": {
        "Python": '''from typing import List

class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # Write your solution here
        pass

def solve(nums, target):
    return Solution().twoSum(nums, target)''',

        "Java": '''import java.util.*;

public class Solution {
    public int[] twoSum(int[] nums, int target) {
        // Write your solution here
        return new int[]{};
    }

    public static int[] solve(int[] nums, int target) {
        return new Solution().twoSum(nums, target);
    }
}''',

        "C++": '''#include <vector>
#include <unordered_map>
using namespace std;

class Solution {
public:
    vector<int> twoSum(vector<int>& nums, int target) {
        // Write your solution here
        return {};
    }
};''',

        "JavaScript": '''/**
 * @param {number[]} nums
 * @param {number} target
 * @return {number[]}
 */
var twoSum = function(nums, target) {
    // Write your solution here
};''',

        "C": '''#include <stdio.h>
#include <stdlib.h>

int* twoSum(int* nums, int numsSize, int target, int* returnSize) {
    // Write your solution here
    *returnSize = 2;
    int* result = (int*)malloc(2 * sizeof(int));
    return result;
}''',
    },

    "contains_duplicate": {
        "Python": '''from typing import List

class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        # Write your solution here
        pass

def solve(nums):
    return Solution().containsDuplicate(nums)''',

        "Java": '''import java.util.*;

public class Solution {
    public boolean containsDuplicate(int[] nums) {
        // Write your solution here
        return false;
    }

    public static boolean solve(int[] nums) {
        return new Solution().containsDuplicate(nums);
    }
}''',

        "C++": '''#include <vector>
#include <unordered_set>
using namespace std;

class Solution {
public:
    bool containsDuplicate(vector<int>& nums) {
        // Write your solution here
        return false;
    }
};''',

        "JavaScript": '''/**
 * @param {number[]} nums
 * @return {boolean}
 */
var containsDuplicate = function(nums) {
    // Write your solution here
};''',

        "C": '''#include <stdio.h>
#include <stdbool.h>

bool containsDuplicate(int* nums, int numsSize) {
    // Write your solution here
    return false;
}''',
    },
}

# Generic template generator for problems not in PROBLEM_TEMPLATES
def get_generic_template(language: str, problem_title: str) -> str:
    title = problem_title.replace(" ", "")

    templates = {
        "Python": f'''class Solution:
    def {title[0].lower() + title[1:]}(self):
        # Write your solution here
        pass

def solve(*args, **kwargs):
    return Solution().{title[0].lower() + title[1:]}(*args, **kwargs)''',

        "Java": f'''public class Solution {{
    public Object {title[0].lower() + title[1:]}() {{
        // Write your solution here
        return null;
    }}
}}''',

        "C++": f'''#include <bits/stdc++.h>
using namespace std;

class Solution {{
public:
    // Write your solution here
}};''',

        "JavaScript": f'''/**
 * {problem_title}
 */
var solve = function() {{
    // Write your solution here
}};''',

        "C": f'''#include <stdio.h>
#include <stdlib.h>

// Write your solution here
void solve() {{

}}''',
    }
    return templates.get(language, templates["Python"])


def get_starter_code(problem_id: str, problem_title: str, language: str) -> str:
    """Get starter code for a specific problem and language."""
    if problem_id in PROBLEM_TEMPLATES and language in PROBLEM_TEMPLATES[problem_id]:
        return PROBLEM_TEMPLATES[problem_id][language]
    return get_generic_template(language, problem_title)