"""
ThinkCode AI — AI Analyzer
Smart fallback chain — site never goes down!

Priority:
1. Groq API (free, fast, 24/7) — all languages
2. Ollama (local LLM) — all languages
3. PyTorch model (always works) — Python only
4. Rule-based (final fallback) — basic analysis
"""

import json
import os
import requests

OLLAMA_URL  = "http://localhost:11434/api/generate"
GROQ_URL    = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL  = "llama3-8b-8192"  # Free, fast


def get_groq_key() -> str | None:
    return os.environ.get("GROQ_API_KEY")


def is_ollama_available() -> bool:
    try:
        r = requests.get("http://localhost:11434/api/tags", timeout=2)
        return r.status_code == 200
    except:
        return False


def is_groq_available() -> bool:
    return bool(get_groq_key())


def _build_prompt(user_code, thinking_text, problem, language):
    return f"""You are an expert coding interview coach. Analyze this solution.

PROBLEM: {problem.get('title', 'Unknown')}
TOPIC: {problem.get('topic', 'unknown')}
DIFFICULTY: {problem.get('difficulty', 'easy')}
LANGUAGE: {language}

THINKING EXPLANATION:
{thinking_text if thinking_text.strip() else "(No explanation provided)"}

CODE ({language}):
{user_code}

Return ONLY valid JSON (no markdown):
{{
  "thinking_score": <0-100>,
  "code_approach": "<brute_force|basic|optimized|optimal>",
  "feedback": ["<point 1>", "<point 2>"],
  "suggestions": ["<suggestion 1>"],
  "strengths": ["<strength 1>"],
  "areas_to_improve": ["<area 1>"],
  "reflection_questions": ["<q1>", "<q2>", "<q3>"],
  "complexity_analysis": {{
    "time": "<O(n)>",
    "space": "<O(1)>",
    "explanation": "<brief>"
  }}
}}"""


def _parse_json(text: str) -> dict | None:
    try:
        start = text.find("{")
        end   = text.rfind("}") + 1
        if start == -1: return None
        return json.loads(text[start:end])
    except:
        return None


def analyze_with_groq(user_code, thinking_text, problem, language) -> dict | None:
    key = get_groq_key()
    if not key:
        return None
    try:
        response = requests.post(GROQ_URL, headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json"
        }, json={
            "model": GROQ_MODEL,
            "messages": [{"role": "user", "content": _build_prompt(user_code, thinking_text, problem, language)}],
            "temperature": 0.3, "max_tokens": 800
        }, timeout=15)

        if response.status_code == 200:
            text = response.json()["choices"][0]["message"]["content"]
            result = _parse_json(text)
            if result:
                result["model_source"] = "groq"
                result["confidence"]   = 0.90
                return result
        elif response.status_code == 429:
            print("⚠️ Groq rate limit — falling back")
            return None
    except Exception as e:
        print(f"⚠️ Groq failed: {e} — falling back")
    return None


def analyze_with_ollama(user_code, thinking_text, problem, language) -> dict | None:
    try:
        response = requests.post(OLLAMA_URL, json={
            "model": "llama3",
            "prompt": _build_prompt(user_code, thinking_text, problem, language),
            "stream": False,
            "options": {"temperature": 0.3, "num_predict": 800}
        }, timeout=30)

        if response.status_code == 200:
            text = response.json().get("response", "")
            result = _parse_json(text)
            if result:
                result["model_source"] = "ollama"
                result["confidence"]   = 0.85
                return result
    except Exception as e:
        print(f"⚠️ Ollama failed: {e} — falling back")
    return None


def analyze_code(user_code, thinking_text, problem, language) -> dict | None:
    """
    Smart fallback chain:
    1. Groq  (free API, 24/7)
    2. Ollama (local)
    3. None → caller uses PyTorch/rule-based
    """
    # 1. Try Groq
    if is_groq_available():
        result = analyze_with_groq(user_code, thinking_text, problem, language)
        if result:
            print("✅ Using Groq")
            return result

    # 2. Try Ollama
    if is_ollama_available():
        result = analyze_with_ollama(user_code, thinking_text, problem, language)
        if result:
            print("✅ Using Ollama")
            return result

    # 3. Return None → fallback to PyTorch/rule-based
    print("ℹ️ Using local model fallback")
    return None


def get_ai_status() -> dict:
    return {
        "groq":   {"available": is_groq_available(),   "type": "cloud", "speed": "fast"},
        "ollama": {"available": is_ollama_available(),  "type": "local", "speed": "medium"},
        "pytorch": {"available": True,                  "type": "local", "speed": "fast"},
        "active": "groq" if is_groq_available() else
                  "ollama" if is_ollama_available() else
                  "pytorch"
    }