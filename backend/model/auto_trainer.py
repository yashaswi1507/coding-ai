"""
ThinkCode AI — Auto Trainer
Model automatically retrains when enough new data is collected.
No manual intervention needed.

Triggers:
    1. Every 10 new submissions
    2. On server startup if model doesn't exist
"""

import os
import threading
import time
from model.data_collector import get_stats

MODEL_PATH    = os.path.join(os.path.dirname(__file__), "thinking_model.pth")
RETRAIN_EVERY = 10   # retrain after every N new submissions
_lock         = threading.Lock()
_is_training  = False
_sub_counter  = 0    # submissions since last retrain


def _run_training_background(epochs: int = 80):
    """Run training in a background thread — server stays live."""
    global _is_training
    try:
        print("🔄 Auto-training started in background...")
        from model.trainer import train
        train(epochs=epochs, batch_size=4)
        print("✅ Auto-training complete!")
    except Exception as e:
        print(f"⚠️ Auto-training failed: {e}")
    finally:
        _is_training = False


def trigger_if_needed():
    """
    Called after every submission.
    Retrains automatically when threshold is reached.
    """
    global _sub_counter, _is_training

    with _lock:
        _sub_counter += 1
        should_train = (
            _sub_counter >= RETRAIN_EVERY and
            not _is_training
        )

        if should_train:
            _sub_counter = 0
            _is_training = True
            thread = threading.Thread(
                target=_run_training_background,
                args=(80,),
                daemon=True
            )
            thread.start()
            return True

    return False


def startup_train_if_needed():
    """
    Called on server startup.
    If model doesn't exist, trains automatically with seed data.
    """
    global _is_training

    if os.path.exists(MODEL_PATH):
        print("✅ Model already exists — skipping startup training")
        return False

    print("🆕 No model found — auto-training on startup...")
    _is_training = True

    def _startup_train():
        global _is_training
        try:
            from model.data_collector import create_seed_data
            from model.trainer import train
            create_seed_data()
            train(epochs=150, batch_size=4)
            print("✅ Startup training complete!")
        except Exception as e:
            print(f"⚠️ Startup training failed: {e}")
        finally:
            _is_training = False

    thread = threading.Thread(target=_startup_train, daemon=True)
    thread.start()
    return True


def get_training_status() -> dict:
    stats = get_stats()
    return {
        "is_training":      _is_training,
        "submissions_since_last_train": _sub_counter,
        "next_train_at":    RETRAIN_EVERY - _sub_counter,
        "model_exists":     os.path.exists(MODEL_PATH),
        "total_samples":    stats.get("ready_for_training", 0),
        "labeled_samples":  stats.get("labeled", 0),
    }