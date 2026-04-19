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
EVENT_FILE = Path("event.json")
SLOTS_FILE = Path("slots.json")
ECONOMY_STATS_FILE = Path("economy_stats.json")
FACTIONS_FILE = Path("factions.json")
COMBAT_FILE = Path("combat.json")
DEFAULT_SLOTS_POT = 0


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


def load_combat_state() -> dict[str, dict[str, object]]:
    if not COMBAT_FILE.exists():
        return {}

    with COMBAT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, dict) else {}


def save_combat_state(data: dict[str, dict[str, object]]) -> None:
    with COMBAT_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def _normalize_combat_profile(raw_value: object, *, max_energy: int) -> dict[str, object]:
    energy = max_energy
    last_refill_at = datetime.now(timezone.utc).isoformat()
    force = 0
    defense = 0
    speed = 0

    if isinstance(raw_value, dict):
        try:
            energy = max(0, min(max_energy, int(raw_value.get("energy", max_energy))))
        except (TypeError, ValueError):
            energy = max_energy

        for stat_name in ("force", "defense", "speed"):
            try:
                value = max(0, int(raw_value.get(stat_name, 0)))
            except (TypeError, ValueError):
                value = 0
            if stat_name == "force":
                force = value
            elif stat_name == "defense":
                defense = value
            else:
                speed = value

        raw_last_refill_at = raw_value.get("last_refill_at")
        if isinstance(raw_last_refill_at, str):
            try:
                datetime.fromisoformat(raw_last_refill_at)
                last_refill_at = raw_last_refill_at
            except ValueError:
                pass

    return {
        "energy": energy,
        "last_refill_at": last_refill_at,
        "force": force,
        "defense": defense,
        "speed": speed,
    }


def _get_refilled_combat_profile(
    user_id: int,
    *,
    max_energy: int,
    refill_amount: int,
    refill_interval: timedelta,
) -> tuple[dict[str, object], timedelta | None]:
    data = load_combat_state()
    key = str(user_id)
    profile = _normalize_combat_profile(data.get(key), max_energy=max_energy)

    now = datetime.now(timezone.utc)
    try:
        last_refill_at = datetime.fromisoformat(str(profile.get("last_refill_at", "")))
    except ValueError:
        last_refill_at = now

    energy = int(profile.get("energy", max_energy))
    if energy < max_energy:
        elapsed = now - last_refill_at
        if elapsed >= refill_interval:
            ticks = int(elapsed.total_seconds() // refill_interval.total_seconds())
            energy = min(max_energy, energy + ticks * refill_amount)
            last_refill_at = last_refill_at + (refill_interval * ticks)

    profile["energy"] = max(0, min(max_energy, energy))
    profile["last_refill_at"] = last_refill_at.isoformat()
    data[key] = profile
    save_combat_state(data)

    if energy >= max_energy:
        return profile, None
    next_refill_at = last_refill_at + refill_interval
    return profile, max(timedelta(seconds=0), next_refill_at - now)


def get_attack_energy_state(
    user_id: int,
    *,
    max_energy: int,
    refill_amount: int,
    refill_interval: timedelta,
) -> tuple[int, timedelta | None]:
    profile, next_refill_in = _get_refilled_combat_profile(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    return int(profile.get("energy", max_energy)), next_refill_in


def spend_attack_energy(
    user_id: int,
    amount: int,
    *,
    max_energy: int,
    refill_amount: int,
    refill_interval: timedelta,
) -> tuple[bool, int, timedelta | None]:
    profile, next_refill_in = _get_refilled_combat_profile(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    current_energy = int(profile.get("energy", max_energy))
    if current_energy < amount:
        return False, current_energy, next_refill_in

    profile["energy"] = current_energy - amount
    data = load_combat_state()
    data[str(user_id)] = profile
    save_combat_state(data)

    refreshed_energy, refreshed_next_refill = get_attack_energy_state(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    return True, refreshed_energy, refreshed_next_refill


def get_combat_profile(
    user_id: int,
    *,
    max_energy: int,
    refill_amount: int,
    refill_interval: timedelta,
) -> dict[str, object]:
    profile, _ = _get_refilled_combat_profile(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    return profile


def refill_combat_energy(
    user_id: int,
    *,
    max_energy: int,
    refill_amount: int,
    refill_interval: timedelta,
) -> dict[str, object]:
    data = load_combat_state()
    key = str(user_id)
    profile = get_combat_profile(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    profile["energy"] = max_energy
    data[key] = profile
    save_combat_state(data)
    return profile


def train_combat_stat(
    user_id: int,
    stat_name: str,
    *,
    energy_cost: int,
    max_energy: int,
    refill_amount: int,
    refill_interval: timedelta,
    stat_cap: int,
) -> tuple[bool, dict[str, object], timedelta | None, str | None]:
    if stat_name not in {"force", "defense", "speed"}:
        profile, next_refill_in = _get_refilled_combat_profile(
            user_id,
            max_energy=max_energy,
            refill_amount=refill_amount,
            refill_interval=refill_interval,
        )
        return False, profile, next_refill_in, "Stat inconnue."

    data = load_combat_state()
    key = str(user_id)
    profile, next_refill_in = _get_refilled_combat_profile(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    current_energy = int(profile.get("energy", max_energy))
    current_stat = int(profile.get(stat_name, 0))

    if current_stat >= stat_cap:
        return False, profile, next_refill_in, f"{stat_name} est déjà au maximum."
    if current_energy < energy_cost:
        return False, profile, next_refill_in, "Pas assez d'énergie."

    profile["energy"] = current_energy - energy_cost
    profile[stat_name] = current_stat + 1
    data[key] = profile
    save_combat_state(data)

    refreshed_profile = get_combat_profile(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    refreshed_energy, refreshed_next_refill = get_attack_energy_state(
        user_id,
        max_energy=max_energy,
        refill_amount=refill_amount,
        refill_interval=refill_interval,
    )
    refreshed_profile["energy"] = refreshed_energy
    return True, refreshed_profile, refreshed_next_refill, None


def load_lottery_state() -> dict[str, object]:
    if not LOTTERY_FILE.exists():
        return {}

    with LOTTERY_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, dict) else {}


def save_lottery_state(data: dict[str, object]) -> None:
    with LOTTERY_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_event_state() -> dict[str, object]:
    if not EVENT_FILE.exists():
        return {}

    with EVENT_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return data if isinstance(data, dict) else {}


def save_event_state(data: dict[str, object]) -> None:
    with EVENT_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def load_slots_state() -> dict[str, int]:
    if not SLOTS_FILE.exists():
        return {"pot": DEFAULT_SLOTS_POT}

    with SLOTS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        return {"pot": DEFAULT_SLOTS_POT}

    pot = data.get("pot", 0)
    try:
        pot = max(0, int(pot))
    except (TypeError, ValueError):
        pot = DEFAULT_SLOTS_POT
    return {"pot": pot}


def save_slots_state(data: dict[str, int]) -> None:
    with SLOTS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_slots_pot() -> int:
    return load_slots_state().get("pot", 0)


def add_slots_pot(amount: int) -> int:
    state = load_slots_state()
    state["pot"] = max(0, int(state.get("pot", 0)) + int(amount))
    save_slots_state(state)
    return state["pot"]


def reset_slots_pot() -> int:
    save_slots_state({"pot": DEFAULT_SLOTS_POT})
    return DEFAULT_SLOTS_POT


def load_economy_stats() -> dict[str, dict[str, int]]:
    if not ECONOMY_STATS_FILE.exists():
        return {}

    with ECONOMY_STATS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        return {}

    normalized: dict[str, dict[str, int]] = {}
    for source, raw_entry in data.items():
        if not isinstance(raw_entry, dict):
            continue
        entry: dict[str, int] = {}
        for field in ("gained", "lost", "gain_events", "loss_events"):
            try:
                entry[field] = max(0, int(raw_entry.get(field, 0)))
            except (TypeError, ValueError):
                entry[field] = 0
        normalized[str(source)] = entry
    return normalized


def save_economy_stats(data: dict[str, dict[str, int]]) -> None:
    with ECONOMY_STATS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def record_economy_stat(source: str, amount: int) -> None:
    if amount == 0:
        return

    data = load_economy_stats()
    entry = data.setdefault(
        str(source),
        {"gained": 0, "lost": 0, "gain_events": 0, "loss_events": 0},
    )

    if amount > 0:
        entry["gained"] += int(amount)
        entry["gain_events"] += 1
    else:
        entry["lost"] += abs(int(amount))
        entry["loss_events"] += 1

    save_economy_stats(data)


def get_economy_stats() -> dict[str, dict[str, int]]:
    return load_economy_stats()


def load_faction_state() -> dict[str, dict[str, object]]:
    if not FACTIONS_FILE.exists():
        return {"factions": {}, "invites": {}, "ally_requests": {}}

    with FACTIONS_FILE.open("r", encoding="utf-8") as file:
        data = json.load(file)

    if not isinstance(data, dict):
        return {"factions": {}, "invites": {}, "ally_requests": {}}

    raw_factions = data.get("factions", {})
    raw_invites = data.get("invites", {})
    raw_ally_requests = data.get("ally_requests", {})

    factions: dict[str, dict[str, object]] = {}
    if isinstance(raw_factions, dict):
        for owner_id, raw_faction in raw_factions.items():
            if not isinstance(raw_faction, dict):
                continue

            name = str(raw_faction.get("name") or "").strip()
            tag = str(raw_faction.get("tag") or "").strip()
            created_at = str(raw_faction.get("created_at") or "")
            raw_allies = raw_faction.get("allies", [])
            raw_members = raw_faction.get("members", {})
            raw_channel_id = raw_faction.get("channel_id")
            raw_ally_channels = raw_faction.get("ally_channels", {})
            raw_role_id = raw_faction.get("role_id")

            allies: list[str] = []
            if isinstance(raw_allies, list):
                allies = [str(ally_id) for ally_id in raw_allies]

            channel_id: int | None
            try:
                channel_id = int(raw_channel_id) if raw_channel_id is not None else None
            except (TypeError, ValueError):
                channel_id = None

            role_id: int | None
            try:
                role_id = int(raw_role_id) if raw_role_id is not None else None
            except (TypeError, ValueError):
                role_id = None

            ally_channels: dict[str, int] = {}
            if isinstance(raw_ally_channels, dict):
                for ally_owner_id, ally_channel_id in raw_ally_channels.items():
                    try:
                        ally_channels[str(ally_owner_id)] = int(ally_channel_id)
                    except (TypeError, ValueError):
                        continue

            members: dict[str, dict[str, object]] = {}
            if isinstance(raw_members, dict):
                for member_id, raw_member in raw_members.items():
                    if isinstance(raw_member, dict):
                        joined_at = str(raw_member.get("joined_at") or "")
                        base_nick = raw_member.get("base_nick")
                        raw_role = raw_member.get("role")
                    else:
                        joined_at = ""
                        base_nick = None
                        raw_role = None
                    if str(member_id) == str(owner_id):
                        role = "owner"
                    else:
                        role = str(raw_role) if isinstance(raw_role, str) and raw_role in {"member", "co_leader", "owner"} else "member"
                    members[str(member_id)] = {
                        "joined_at": joined_at,
                        "base_nick": str(base_nick) if isinstance(base_nick, str) else None,
                        "role": role,
                    }
            elif isinstance(raw_members, list):
                for member_id in raw_members:
                    role = "owner" if str(member_id) == str(owner_id) else "member"
                    members[str(member_id)] = {"joined_at": "", "base_nick": None, "role": role}

            factions[str(owner_id)] = {
                "name": name,
                "tag": tag,
                "created_at": created_at,
                "allies": allies,
                "channel_id": channel_id,
                "ally_channels": ally_channels,
                "role_id": role_id,
                "members": members,
            }

    invites: dict[str, str] = {}
    if isinstance(raw_invites, dict):
        for target_id, owner_id in raw_invites.items():
            invites[str(target_id)] = str(owner_id)

    ally_requests: dict[str, list[str]] = {}
    if isinstance(raw_ally_requests, dict):
        for target_owner_id, raw_requesters in raw_ally_requests.items():
            if isinstance(raw_requesters, list):
                ally_requests[str(target_owner_id)] = [str(requester_id) for requester_id in raw_requesters]

    return {"factions": factions, "invites": invites, "ally_requests": ally_requests}


def save_faction_state(data: dict[str, dict[str, object]]) -> None:
    with FACTIONS_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def get_faction_by_owner(owner_id: int) -> dict[str, object] | None:
    state = load_faction_state()
    factions = state.get("factions", {})
    if not isinstance(factions, dict):
        return None
    faction = factions.get(str(owner_id))
    return faction if isinstance(faction, dict) else None


def get_faction_for_member(user_id: int) -> tuple[int, dict[str, object]] | None:
    state = load_faction_state()
    factions = state.get("factions", {})
    if not isinstance(factions, dict):
        return None

    user_key = str(user_id)
    for owner_id, faction in factions.items():
        if not isinstance(faction, dict):
            continue
        members = faction.get("members", {})
        if isinstance(members, dict) and user_key in members:
            try:
                return int(owner_id), faction
            except ValueError:
                continue
    return None


def get_all_factions() -> list[tuple[int, dict[str, object]]]:
    state = load_faction_state()
    factions = state.get("factions", {})
    if not isinstance(factions, dict):
        return []

    result: list[tuple[int, dict[str, object]]] = []
    for owner_id, faction in factions.items():
        if not isinstance(faction, dict):
            continue
        try:
            result.append((int(owner_id), faction))
        except ValueError:
            continue
    return result


def get_faction_invite(user_id: int) -> int | None:
    state = load_faction_state()
    invites = state.get("invites", {})
    if not isinstance(invites, dict):
        return None
    owner_id = invites.get(str(user_id))
    try:
        return int(owner_id) if owner_id is not None else None
    except (TypeError, ValueError):
        return None


def set_faction_invite(user_id: int, owner_id: int) -> None:
    state = load_faction_state()
    invites = state.setdefault("invites", {})
    if not isinstance(invites, dict):
        invites = {}
        state["invites"] = invites
    invites[str(user_id)] = str(owner_id)
    save_faction_state(state)


def clear_faction_invite(user_id: int) -> None:
    state = load_faction_state()
    invites = state.get("invites", {})
    if isinstance(invites, dict):
        invites.pop(str(user_id), None)
        save_faction_state(state)


def reset_cooldown_files(*, max_energy: int) -> None:
    for path in (DAILY_FILE, WORK_FILE):
        save_json_dict(path, {})

    attack_data = load_json_dict(ATTACK_FILE)
    preserved_attack_data = {
        key: value
        for key, value in attack_data.items()
        if isinstance(key, str) and ":" in key
    }
    save_json_dict(ATTACK_FILE, preserved_attack_data)

    combat_state = load_combat_state()
    now_iso = datetime.now(timezone.utc).isoformat()
    updated_state: dict[str, dict[str, object]] = {}
    for user_id, raw_profile in combat_state.items():
        profile = _normalize_combat_profile(raw_profile, max_energy=max_energy)
        profile["energy"] = max_energy
        profile["last_refill_at"] = now_iso
        updated_state[str(user_id)] = profile
    save_combat_state(updated_state)


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
            "last_tax_at": raw_value,
            "reason": "",
            "channel_id": None,
            "challenge": "",
            "challenge_sent_at": None,
            "attempts": 0,
            "variant": "memory",
            "tax_amount": 0,
            "prompt_message_id": None,
            "memory_progress": 0,
        }

    if not isinstance(raw_value, dict):
        return None

    jailed_at = raw_value.get("jailed_at")
    if not isinstance(jailed_at, str):
        jailed_at = datetime.now(timezone.utc).isoformat()

    last_tax_at = raw_value.get("last_tax_at")
    if not isinstance(last_tax_at, str):
        last_tax_at = jailed_at

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

    variant = raw_value.get("variant")
    if not isinstance(variant, str) or not variant:
        variant = "memory"

    tax_amount = raw_value.get("tax_amount", 0)
    try:
        tax_amount = max(0, int(tax_amount))
    except (TypeError, ValueError):
        tax_amount = 0

    prompt_message_id = raw_value.get("prompt_message_id")
    if isinstance(prompt_message_id, bool):
        prompt_message_id = None
    elif prompt_message_id is not None:
        try:
            prompt_message_id = int(prompt_message_id)
        except (TypeError, ValueError):
            prompt_message_id = None

    memory_progress = raw_value.get("memory_progress", 0)
    try:
        memory_progress = max(0, int(memory_progress))
    except (TypeError, ValueError):
        memory_progress = 0

    return {
        "jailed_at": jailed_at,
        "last_tax_at": last_tax_at,
        "reason": reason,
        "channel_id": channel_id,
        "challenge": challenge,
        "challenge_sent_at": challenge_sent_at,
        "attempts": attempts,
        "variant": variant,
        "tax_amount": tax_amount,
        "prompt_message_id": prompt_message_id,
        "memory_progress": memory_progress,
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
        "last_tax_at": datetime.now(timezone.utc).isoformat(),
        "reason": reason,
        "channel_id": channel_id,
        "challenge": challenge,
        "challenge_sent_at": challenge_sent_at,
        "attempts": 0,
        "variant": "memory",
        "tax_amount": 0,
        "prompt_message_id": None,
        "memory_progress": 0,
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
