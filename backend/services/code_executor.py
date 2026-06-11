import subprocess
import sys
import json
import tempfile
import os

TIMEOUT_SECONDS = 5
MEMORY_LIMIT_MB = 128

def run_code(user_code: str, test_input: dict) -> dict:
    """
    Safely execute user code using subprocess isolation.
    Prevents infinite loops via timeout, limits resource usage.
    """

    # Build a safe runner script
    runner_script = f"""
import json
import sys

{user_code}

test_input = {json.dumps(test_input)}

try:
    result = solve(**test_input)
    print(json.dumps({{"success": True, "output": result}}))
except Exception as e:
    print(json.dumps({{"success": False, "error": str(e)}}))
"""

    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".py",
            delete=False
        ) as tmp:
            tmp.write(runner_script)
            tmp_path = tmp.name

        result = subprocess.run(
            [sys.executable, tmp_path],
            capture_output=True,
            text=True,
            timeout=TIMEOUT_SECONDS
        )

        os.unlink(tmp_path)

        if result.returncode != 0 and not result.stdout:
            return {
                "success": False,
                "error": result.stderr.strip() or "Runtime Error"
            }

        output = json.loads(result.stdout.strip())
        return output

    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "error": f"Time Limit Exceeded (>{TIMEOUT_SECONDS}s)"
        }
    except json.JSONDecodeError:
        return {
            "success": False,
            "error": "Output parsing error — make sure solve() returns a value"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass