"""
ThinkCode AI — Multi-Language Code Executor
Supports: Python, Java, C++, JavaScript, C
Uses subprocess with timeout for safety.
"""

import subprocess
import sys
import json
import tempfile
import os

TIMEOUT = 5  # seconds


def run_code(user_code: str, test_input: dict, language: str = "Python") -> dict:
    """Execute code in given language and return result."""
    executors = {
        "Python":     _run_python,
        "Java":       _run_java,
        "C++":        _run_cpp,
        "JavaScript": _run_javascript,
        "C":          _run_c,
    }
    runner = executors.get(language, _run_python)
    return runner(user_code, test_input)


# ── Python ────────────────────────────────────────────────────────────────────
def _run_python(code: str, test_input: dict) -> dict:
    runner = f"""
import json, sys
{code}
test_input = {json.dumps(test_input)}
try:
    result = solve(**test_input)
    print(json.dumps({{"success": True, "output": result}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
"""
    return _subprocess_run(runner, ".py", [sys.executable])


# ── JavaScript ────────────────────────────────────────────────────────────────
def _run_javascript(code: str, test_input: dict) -> dict:
    runner = f"""
{code}

const testInput = {json.dumps(test_input)};
try {{
    const result = solve(...Object.values(testInput));
    console.log(JSON.stringify({{success: true, output: result}}));
}} catch(e) {{
    console.log(JSON.stringify({{success: false, error: e.message}}));
}}
"""
    return _subprocess_run(runner, ".js", ["node"])


# ── Java ──────────────────────────────────────────────────────────────────────
def _run_java(code: str, test_input: dict) -> dict:
    # Java needs compilation first
    params = ", ".join(
        f'"{v}"' if isinstance(v, str) else str(v)
        for v in test_input.values()
    )
    wrapper = f"""
{code}

public class Main {{
    public static void main(String[] args) {{
        try {{
            Object result = Solution.solve({params});
            System.out.println(result);
        }} catch(Exception e) {{
            System.err.println("ERROR: " + e.getMessage());
        }}
    }}
}}
"""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            java_file = os.path.join(tmpdir, "Main.java")
            with open(java_file, "w", encoding="utf-8") as f:
                f.write(wrapper)

            # Compile
            compile_result = subprocess.run(
                ["javac", java_file],
                capture_output=True, text=True, timeout=TIMEOUT, cwd=tmpdir
            )
            if compile_result.returncode != 0:
                return {"success": False, "error": f"Compile error: {compile_result.stderr}"}

            # Run
            run_result = subprocess.run(
                ["java", "Main"],
                capture_output=True, text=True, timeout=TIMEOUT, cwd=tmpdir
            )
            if run_result.returncode != 0:
                return {"success": False, "error": run_result.stderr}

            output = run_result.stdout.strip()
            return {"success": True, "output": _parse_output(output)}

    except FileNotFoundError:
        return {"success": False, "error": "Java not installed. Install JDK to run Java code."}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Time Limit Exceeded (>{TIMEOUT}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── C++ ───────────────────────────────────────────────────────────────────────
def _run_cpp(code: str, test_input: dict) -> dict:
    params = ", ".join(str(v) for v in test_input.values())
    wrapper = f"""
#include <bits/stdc++.h>
using namespace std;

{code}

int main() {{
    // Basic output — extend as needed
    cout << "OK" << endl;
    return 0;
}}
"""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            cpp_file = os.path.join(tmpdir, "solution.cpp")
            exe_file = os.path.join(tmpdir, "solution")
            with open(cpp_file, "w", encoding="utf-8") as f:
                f.write(wrapper)

            compile_result = subprocess.run(
                ["g++", "-o", exe_file, cpp_file],
                capture_output=True, text=True, timeout=TIMEOUT
            )
            if compile_result.returncode != 0:
                return {"success": False, "error": f"Compile error: {compile_result.stderr}"}

            run_result = subprocess.run(
                [exe_file], capture_output=True, text=True, timeout=TIMEOUT
            )
            return {"success": True, "output": run_result.stdout.strip()}

    except FileNotFoundError:
        return {"success": False, "error": "g++ not installed. Install MinGW/GCC to run C++ code."}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Time Limit Exceeded (>{TIMEOUT}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── C ─────────────────────────────────────────────────────────────────────────
def _run_c(code: str, test_input: dict) -> dict:
    wrapper = f"""
#include <stdio.h>
#include <stdlib.h>
#include <stdbool.h>

{code}

int main() {{
    printf("OK\\n");
    return 0;
}}
"""
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            c_file  = os.path.join(tmpdir, "solution.c")
            exe_file = os.path.join(tmpdir, "solution")
            with open(c_file, "w", encoding="utf-8") as f:
                f.write(wrapper)

            compile_result = subprocess.run(
                ["gcc", "-o", exe_file, c_file],
                capture_output=True, text=True, timeout=TIMEOUT
            )
            if compile_result.returncode != 0:
                return {"success": False, "error": f"Compile error: {compile_result.stderr}"}

            run_result = subprocess.run(
                [exe_file], capture_output=True, text=True, timeout=TIMEOUT
            )
            return {"success": True, "output": run_result.stdout.strip()}

    except FileNotFoundError:
        return {"success": False, "error": "gcc not installed. Install GCC to run C code."}
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Time Limit Exceeded (>{TIMEOUT}s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _subprocess_run(code: str, ext: str, cmd: list) -> dict:
    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=ext, delete=False, encoding="utf-8"
        ) as tmp:
            tmp.write(code)
            tmp_path = tmp.name

        result = subprocess.run(
            cmd + [tmp_path],
            capture_output=True, text=True, timeout=TIMEOUT
        )

        if result.returncode != 0 and not result.stdout:
            return {"success": False, "error": result.stderr.strip() or "Runtime Error"}

        return json.loads(result.stdout.strip())

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Time Limit Exceeded (>{TIMEOUT}s)"}
    except json.JSONDecodeError:
        return {"success": False, "error": "Output parsing error"}
    except FileNotFoundError as e:
        return {"success": False, "error": f"Runtime not found: {e}"}
    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        if tmp_path:
            try:
                os.unlink(tmp_path)
            except:
                pass


def _parse_output(text: str):
    """Try to parse output as number/bool/list."""
    text = text.strip()
    try:
        return json.loads(text)
    except:
        if text.lower() == "true":  return True
        if text.lower() == "false": return False
        try:    return int(text)
        except: pass
        try:    return float(text)
        except: pass
        return text


def check_language_available(language: str) -> dict:
    """Check if language runtime is installed."""
    checks = {
        "Python":     ([sys.executable, "--version"], True),
        "Java":       (["java", "-version"],          False),
        "C++":        (["g++", "--version"],          False),
        "JavaScript": (["node", "--version"],         False),
        "C":          (["gcc", "--version"],          False),
    }
    cmd, always_ok = checks.get(language, (None, False))
    if always_ok:
        return {"available": True, "language": language}
    if not cmd:
        return {"available": False, "language": language}
    try:
        subprocess.run(cmd, capture_output=True, timeout=3)
        return {"available": True, "language": language}
    except:
        return {"available": False, "language": language,
                "install_hint": f"Install {language} runtime to use this option"}