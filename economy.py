import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

ECONOMY_FILE = Path("economy.json")
ECONOMY_META_FILE = Path("economy_meta.json")
DAILY_FILE = Path("daily.json")
WORK_FILE = Path("work.json")
JOB_FILE = Path("jobs.json")
PRISON_FILE = Path("prison.json")
ATTACK_FILE = Path("attack_cooldowns.json")
CHANGEJOB_FILE = Path("changejob.json")
LOTTERY_FILE = Path("lottery.json")
ECOBAN_FILE = Path("ecoban.json")


def load_economy() -> dict[str, int]:
    if not ECONOMY_FILE.exists():
        return {}

    with ECONOMY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {str(user_id): int(balance) for user_id, balance in data.items()}


def save_economy(data: dict[str, int]) -> None:
    with ECONOMY_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_economy_meta() -> dict[str, list[str]]:
    if not ECONOMY_META_FILE.exists():
        return {"seeded_guilds": []}

    with ECONOMY_META_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    seeded = data.get("seeded_guilds", [])
    if not isinstance(seeded, list):
        seeded = []
    return {"seeded_guilds": [str(guild_id) for guild_id in seeded]}


def save_economy_meta(data: dict[str, list[str]]) -> None:
    with ECONOMY_META_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_ecobans() -> set[int]:
    if not ECOBAN_FILE.exists():
        return set()

    with ECOBAN_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, list):
        return set()

    result: set[int] = set()
    for user_id in data:
        try:
            result.add(int(user_id))
        except (TypeError, ValueError):
            continue
    return result


def save_ecobans(user_ids: set[int]) -> None:
    with ECOBAN_FILE.open("w", encoding="utf-8") as file:
        json.dump(sorted(user_ids), file, indent=2, ensure_ascii=False)


def is_ecobanned(user_id: int) -> bool:
    return user_id in load_ecobans()


def add_ecoban(user_id: int) -> bool:
    ecobans = load_ecobans()
    if user_id in ecobans:
        return False
    ecobans.add(user_id)
    save_ecobans(ecobans)
    return True


def remove_ecoban(user_id: int) -> bool:
    ecobans = load_ecobans()
    if user_id not in ecobans:
        return False
    ecobans.discard(user_id)
    save_ecobans(ecobans)
    return True


def get_balance_value(user_id: int) -> int:
    data = load_economy()
    return data.get(str(user_id), 0)


def set_balance_value(user_id: int, amount: int) -> int:
    data = load_economy()
    data[str(user_id)] = max(0, int(amount))
    save_economy(data)
    return data[str(user_id)]


def add_balance(user_id: int, amount: int) -> int:
    data = load_economy()
    key = str(user_id)
    data[key] = data.get(key, 0) + amount
    save_economy(data)
    return data[key]


def ensure_minimum_balance(user_id: int, minimum: int = 1000) -> int:
    data = load_economy()
    key = str(user_id)
    if key in data:
        return data[key]

    data[key] = minimum
    save_economy(data)
    return data[key]


def get_top_balances(limit: int = 10) -> list[tuple[int, int]]:
    data = load_economy()
    sorted_balances = sorted(
        ((int(user_id), balance) for user_id, balance in data.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return sorted_balances[:limit]


def reset_all_balances(amount: int) -> int:
    data = load_economy()
    for user_id in list(data.keys()):
        data[user_id] = amount
    save_economy(data)
    return len(data)


def load_json_dict(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {str(key): str(value) for key, value in data.items()}


def save_json_dict(path: Path, data: dict[str, str]) -> None:
    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_lottery_state() -> dict[str, object]:
    if not LOTTERY_FILE.exists():
        return {}

    with LOTTERY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, dict) else {}


def save_lottery_state(data: dict[str, object]) -> None:
    with LOTTERY_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def reset_cooldown_files() -> None:
    for path in (DAILY_FILE, WORK_FILE, CHANGEJOB_FILE, ATTACK_FILE):
        save_json_dict(path, {})


def get_cooldown_remaining(path: Path, user_id: int, cooldown: timedelta) -> timedelta | None:
    data = load_json_dict(path)
    raw_value = data.get(str(user_id))
    if raw_value is None:
        return None

    ready_at = datetime.fromisoformat(raw_value) + cooldown
    now = datetime.now(timezone.utc)
    if ready_at <= now:
        data.pop(str(user_id), None)
        save_json_dict(path, data)
        return None
    return ready_at - now


def update_cooldown(path: Path, user_id: int) -> None:
    data = load_json_dict(path)
    data[str(user_id)] = datetime.now(timezone.utc).isoformat()
    save_json_dict(path, data)


def get_job(user_id: int) -> str | None:
    data = load_json_dict(JOB_FILE)
    return data.get(str(user_id))


def set_job(user_id: int, job_key: str) -> None:
    data = load_json_dict(JOB_FILE)
    data[str(user_id)] = job_key
    save_json_dict(JOB_FILE, data)


def _normalize_prison_record(raw_value: object) -> dict[str, object] | None:
    if isinstance(raw_value, str):
        return {
            "jailed_at": raw_value,
            "reason": "",
            "channel_id": None,
            "challenge": "",
            "challenge_sent_at": None,
            "attempts": 0,
        }

    if not isinstance(raw_value, dict):
        return None

    jailed_at = raw_value.get("jailed_at")
    if not isinstance(jailed_at, str):
        jailed_at = datetime.now(timezone.utc).isoformat()

    reason = raw_value.get("reason")
    if not isinstance(reason, str):
        reason = ""

    channel_id = raw_value.get("channel_id")
    if isinstance(channel_id, bool):
        channel_id = None
    elif channel_id is not None:
        try:
            channel_id = int(channel_id)
        except (TypeError, ValueError):
            channel_id = None

    challenge = raw_value.get("challenge")
    if not isinstance(challenge, str):
        challenge = ""

    challenge_sent_at = raw_value.get("challenge_sent_at")
    if not isinstance(challenge_sent_at, str):
        challenge_sent_at = None

    attempts = raw_value.get("attempts", 0)
    try:
        attempts = max(0, int(attempts))
    except (TypeError, ValueError):
        attempts = 0

    return {
        "jailed_at": jailed_at,
        "reason": reason,
        "channel_id": channel_id,
        "challenge": challenge,
        "challenge_sent_at": challenge_sent_at,
        "attempts": attempts,
    }


def load_prison_records() -> dict[str, dict[str, object]]:
    if not PRISON_FILE.exists():
        return {}

    with PRISON_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        return {}

    normalized: dict[str, dict[str, object]] = {}
    changed = False
    for user_id, raw_value in data.items():
        record = _normalize_prison_record(raw_value)
        if record is None:
            changed = True
            continue
        normalized[str(user_id)] = record
        if raw_value != record:
            changed = True

    if changed:
        save_prison_records(normalized)
    return normalized


def save_prison_records(data: dict[str, dict[str, object]]) -> None:
    with PRISON_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_prison_record(user_id: int) -> dict[str, object] | None:
    return load_prison_records().get(str(user_id))


def get_all_prison_records() -> list[tuple[int, dict[str, object]]]:
    data = load_prison_records()
    result: list[tuple[int, dict[str, object]]] = []
    for user_id, record in data.items():
        try:
            result.append((int(user_id), record))
        except ValueError:
            continue
    return result


def set_prison_record(user_id: int, record: dict[str, object]) -> dict[str, object]:
    normalized = _normalize_prison_record(record)
    if normalized is None:
        raise ValueError("Invalid prison record.")

    data = load_prison_records()
    data[str(user_id)] = normalized
    save_prison_records(data)
    return normalized


def remove_prison_record(user_id: int) -> bool:
    data = load_prison_records()
    if str(user_id) not in data:
        return False
    data.pop(str(user_id), None)
    save_prison_records(data)
    return True


def is_in_prison(user_id: int) -> bool:
    return get_prison_record(user_id) is not None


def get_prison_release(user_id: int) -> datetime | None:
    record = get_prison_record(user_id)
    if record is None:
        return None

    raw_value = record.get("challenge_sent_at") or record.get("jailed_at")
    if not isinstance(raw_value, str):
        return None

    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def imprison_user(
    user_id: int,
    duration: timedelta | None = None,
    *,
    reason: str = "",
    channel_id: int | None = None,
    challenge: str = "",
    challenge_sent_at: str | None = None,
) -> dict[str, object]:
    del duration
    record = {
        "jailed_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "channel_id": channel_id,
        "challenge": challenge,
        "challenge_sent_at": challenge_sent_at,
        "attempts": 0,
    }
    return set_prison_record(user_id, record)


def make_pair_cooldown_key(user_id: int, target_id: int) -> str:
    return f"{user_id}:{target_id}"


def get_pair_cooldown_remaining(
    path: Path,
    user_id: int,
    target_id: int,
    cooldown: timedelta,
) -> timedelta | None:
    data = load_json_dict(path)
    raw_value = data.get(make_pair_cooldown_key(user_id, target_id))
    if raw_value is None:
        return None

    ready_at = datetime.fromisoformat(raw_value) + cooldown
    now = datetime.now(timezone.utc)
    if ready_at <= now:
        data.pop(make_pair_cooldown_key(user_id, target_id), None)
        save_json_dict(path, data)
        return None
    return ready_at - now


def update_pair_cooldown(path: Path, user_id: int, target_id: int) -> None:
    data = load_json_dict(path)
    data[make_pair_cooldown_key(user_id, target_id)] = datetime.now(timezone.utc).isoformat()
    save_json_dict(path, data)
