import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

LEVELS_FILE = Path("levels.json")


def load_levels() -> dict[str, dict[str, object]]:
    if not LEVELS_FILE.exists():
        return {}

    with LEVELS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, dict) else {}


def save_levels(data: dict[str, dict[str, object]]) -> None:
    with LEVELS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def xp_needed_for_next_level(level: int) -> int:
    return 100 + max(0, level - 1) * 75


def get_level_profile(user_id: int) -> dict[str, object]:
    data = load_levels()
    profile = data.get(str(user_id), {})
    if not isinstance(profile, dict):
        profile = {}
    return {
        "level": int(profile.get("level", 1)),
        "xp": int(profile.get("xp", 0)),
        "last_message_at": str(profile.get("last_message_at", "")),
    }


def apply_message_xp(
    user_id: int,
    gained_xp: int,
    *,
    cooldown: timedelta,
) -> tuple[int, int]:
    data = load_levels()
    key = str(user_id)
    profile = data.get(key, {})
    if not isinstance(profile, dict):
        profile = {}

    now = datetime.now(timezone.utc)
    raw_last_message = profile.get("last_message_at")
    if isinstance(raw_last_message, str) and raw_last_message:
        try:
            last_message_at = datetime.fromisoformat(raw_last_message)
        except ValueError:
            last_message_at = None
        else:
            if now - last_message_at < cooldown:
                return int(profile.get("level", 1)), 0

    level = int(profile.get("level", 1))
    xp = int(profile.get("xp", 0)) + gained_xp
    levels_gained = 0

    while xp >= xp_needed_for_next_level(level):
        xp -= xp_needed_for_next_level(level)
        level += 1
        levels_gained += 1

    data[key] = {
        "level": level,
        "xp": xp,
        "last_message_at": now.isoformat(),
    }
    save_levels(data)
    return level, levels_gained


def get_top_levels(limit: int = 10) -> list[tuple[int, int, int]]:
    data = load_levels()
    entries: list[tuple[int, int, int]] = []
    for raw_user_id, raw_profile in data.items():
        if not isinstance(raw_profile, dict):
            continue
        try:
            user_id = int(raw_user_id)
            level = int(raw_profile.get("level", 1))
            xp = int(raw_profile.get("xp", 0))
        except (TypeError, ValueError):
            continue
        entries.append((user_id, level, xp))

    return sorted(entries, key=lambda item: (item[1], item[2]), reverse=True)[:limit]
