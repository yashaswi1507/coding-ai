def validate_output(expected, got) -> dict:
    """
    Compare expected vs actual output.
    Handles lists, sets (order-independent), and primitives.
    """

    # Normalize lists that can be in any order
    def normalize(val):
        if isinstance(val, list):
            try:
                return sorted(val)
            except TypeError:
                return val
        return val

    if normalize(expected) == normalize(got):
        return {
            "passed": True,
            "message": "Correct Output ✅",
            "expected": expected,
            "got": got
        }

    return {
        "passed": False,
        "message": f"Wrong Answer",
        "expected": expected,
        "got": got
    }