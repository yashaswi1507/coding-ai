"""
ThinkCode AI — Model Inference Engine
Loads the trained PyTorch model and runs predictions.
Falls back to rule-based engine if model not yet trained.
"""

import os
import torch

from model.feature_extractor import extract_features
from model.thinking_model import ThinkingModel, APPROACH_LABELS

MODEL_PATH = os.path.join(os.path.dirname(__file__), "thinking_model.pth")

# Global model instance (loaded once, reused)
_model = None
_model_available = False


def _load_model():
    global _model, _model_available
    if _model is not None:
        return

    if not os.path.exists(MODEL_PATH):
        _model_available = False
        return

    try:
        _model = ThinkingModel()
        _model.load_state_dict(torch.load(MODEL_PATH, weights_only=True))
        _model.eval()
        _model_available = True
        print("✅ ThinkCode AI model loaded successfully")
    except Exception as e:
        print(f"⚠️  Could not load model: {e}. Using rule-based fallback.")
        _model_available = False


def is_model_available() -> bool:
    _load_model()
    return _model_available


def predict(user_code: str, thinking_text: str) -> dict:
    """
    Main inference function.
    Returns thinking_score, approach, and confidence.
    Uses trained model if available, otherwise rule-based fallback.
    """
    _load_model()

    if _model_available:
        return _predict_with_model(user_code, thinking_text)
    else:
        return _predict_rule_based(user_code, thinking_text)


def _predict_with_model(user_code: str, thinking_text: str) -> dict:
    """Run neural network prediction."""
    features = extract_features(user_code, thinking_text)
    x = torch.tensor([features], dtype=torch.float32)

    with torch.no_grad():
        score_tensor, approach_logits = _model(x)

    score = int(round(score_tensor.item()))
    score = max(0, min(100, score))  # Clamp to valid range

    # Approach with confidence
    probs = torch.softmax(approach_logits, dim=1)[0]
    approach_idx = torch.argmax(probs).item()
    approach = APPROACH_LABELS[approach_idx]
    confidence = probs[approach_idx].item()

    return {
        "thinking_score": score,
        "approach": approach,
        "confidence": round(confidence, 2),
        "source": "neural_network",
        "features": features  # Useful for debugging
    }


def _predict_rule_based(user_code: str, thinking_text: str) -> dict:
    """
    Rule-based fallback when model is not trained yet.
    Also used to generate initial labels for training data.
    """
    code = user_code.lower()
    thinking = thinking_text.lower() if thinking_text else ""

    score = 0
    approach = "basic"

    # Code analysis
    if code.count("for") >= 2 and "dict" not in code:
        score += 15
        approach = "brute_force"
    if "dict" in code or "{}" in code or "defaultdict" in code:
        score += 35
        approach = "optimized"
    if "sort" in code:
        score += 15
    if "if not" in code or "len(" in code or "is none" in code:
        score += 10
    if "lo" in code and "hi" in code or ("left" in code and "right" in code and "mid" in code):
        score += 10
        approach = "optimal"

    # Thinking text analysis
    if thinking.strip():
        if any(w in thinking for w in ["o(n", "complexity", "linear", "quadratic"]):
            score += 15
        if any(w in thinking for w in ["optimize", "efficient", "better"]):
            score += 10
        if any(w in thinking for w in ["edge case", "empty", "null"]):
            score += 5
        if len(thinking.split()) >= 30:
            score += 5
        if len(thinking.split()) >= 60:
            score += 5
    else:
        # No explanation = big penalty
        score = max(0, score - 20)

    score = max(0, min(100, score))

    return {
        "thinking_score": score,
        "approach": approach,
        "confidence": 0.6,
        "source": "rule_based",
        "features": extract_features(user_code, thinking_text)
    }


def get_model_info() -> dict:
    """Returns info about current model status."""
    _load_model()
    return {
        "model_available": _model_available,
        "model_path": MODEL_PATH,
        "model_exists": os.path.exists(MODEL_PATH),
        "source": "neural_network" if _model_available else "rule_based"
    }