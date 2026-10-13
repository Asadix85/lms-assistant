"""مدیریت State (برای جلوگیری از تکرار نوتیفیکیشن)."""

import json
from pathlib import Path


STATE_FILE = Path("data/notification_state.json")


DEFAULT_STATE = {
    "notified_assignments": [],
    "notified_quera": [],
    "notified_posts": [],
    "notified_events": [],
}


def load_state() -> dict:
    """بارخوانی state."""
    if not STATE_FILE.exists():
        return DEFAULT_STATE.copy()

    try:
        data = json.loads(STATE_FILE.read_text(encoding="utf-8"))
        # اطمینان از وجود همه‌ی کلیدها
        for key, value in DEFAULT_STATE.items():
            if key not in data:
                data[key] = value
        return data
    except (json.JSONDecodeError, OSError):
        return DEFAULT_STATE.copy()


def save_state(state: dict) -> None:
    """ذخیره‌ی state."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(
        json.dumps(state, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def filter_new(items: list, state_key: str, state: dict) -> list:
    """فیلتر آیتم‌های جدید (که توی state نیستن)."""
    notified = set(state.get(state_key, []))
    return [item for item in items if str(item["id"]) not in notified]


def mark_notified(items: list, state_key: str, state: dict) -> None:
    """علامت‌گذاری آیتم‌ها به‌عنوان نوتیف‌شده."""
    notified = set(state.get(state_key, []))
    for item in items:
        notified.add(str(item["id"]))
    # محدود به آخرین ۵۰۰ تا (جلوگیری از بزرگ شدن)
    state[state_key] = list(notified)[-500:]