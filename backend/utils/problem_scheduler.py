"""
ThinkCode AI — Problem Scheduler
Automatically releases new problems every 2-3 days.
Runs as background thread — no manual intervention needed.
"""

import threading
import time
import os
import json
from datetime import datetime, timedelta
from utils.problem_generator import release_problems, get_generator_status

SCHEDULE_FILE = os.path.join(os.path.dirname(__file__), "../data/schedule.json")
RELEASE_EVERY_DAYS = 2   # Release new problems every N days
PROBLEMS_PER_RELEASE = 3 # How many to release each time

_scheduler_running = False


def _load_schedule() -> dict:
    if not os.path.exists(SCHEDULE_FILE):
        return {"last_release": None, "total_releases": 0}
    with open(SCHEDULE_FILE, "r") as f:
        return json.load(f)


def _save_schedule(data: dict):
    with open(SCHEDULE_FILE, "w") as f:
        json.dump(data, f, indent=2)


def _should_release() -> bool:
    schedule = _load_schedule()
    if not schedule.get("last_release"):
        return True  # Never released — do it now
    last = datetime.fromisoformat(schedule["last_release"])
    return datetime.now() - last >= timedelta(days=RELEASE_EVERY_DAYS)


def _do_release():
    print(f"\n📅 Scheduled release triggered — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    added = release_problems(PROBLEMS_PER_RELEASE)

    schedule = _load_schedule()
    schedule["last_release"]    = datetime.now().isoformat()
    schedule["total_releases"]  = schedule.get("total_releases", 0) + 1
    schedule["last_added"]      = added
    _save_schedule(schedule)

    if added:
        print(f"✅ Released {len(added)} new problems: {', '.join(added)}")
    else:
        print("⚠️ No new problems to release")


def _scheduler_loop():
    """Background loop — checks every hour if release is needed."""
    global _scheduler_running
    while _scheduler_running:
        try:
            if _should_release():
                _do_release()
        except Exception as e:
            print(f"⚠️ Scheduler error: {e}")
        # Check every hour
        time.sleep(3600)


def start_scheduler():
    """Start the background scheduler."""
    global _scheduler_running
    if _scheduler_running:
        return
    _scheduler_running = True
    thread = threading.Thread(target=_scheduler_loop, daemon=True)
    thread.start()
    print("⏰ Problem scheduler started — releasing every 2 days")


def stop_scheduler():
    global _scheduler_running
    _scheduler_running = False


def get_schedule_status() -> dict:
    schedule  = _load_schedule()
    generator = get_generator_status()
    last      = schedule.get("last_release")

    if last:
        last_dt   = datetime.fromisoformat(last)
        next_dt   = last_dt + timedelta(days=RELEASE_EVERY_DAYS)
        hours_left = max(0, (next_dt - datetime.now()).total_seconds() / 3600)
    else:
        hours_left = 0

    return {
        "scheduler_running":    _scheduler_running,
        "last_release":         last,
        "next_release_in_hours": round(hours_left, 1),
        "total_releases":       schedule.get("total_releases", 0),
        "last_added":           schedule.get("last_added", []),
        "release_every_days":   RELEASE_EVERY_DAYS,
        "problems_per_release": PROBLEMS_PER_RELEASE,
        **generator
    }


def manual_release(count: int = 3) -> list:
    """Manually trigger a release (for admin panel)."""
    added = release_problems(count)
    schedule = _load_schedule()
    schedule["last_release"]  = datetime.now().isoformat()
    schedule["last_added"]    = added
    schedule["total_releases"] = schedule.get("total_releases", 0) + 1
    _save_schedule(schedule)
    return added