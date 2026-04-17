import json
from datetime import datetime, timezone
from pathlib import Path

import discord

TEMPBAN_FILE = Path("tempbans.json")


def load_tempbans() -> dict[str, dict[str, str]]:
    if not TEMPBAN_FILE.exists():
        return {}

    with TEMPBAN_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_tempbans(data: dict[str, dict[str, str]]) -> None:
    with TEMPBAN_FILE.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=2, ensure_ascii=False)


def make_tempban_key(guild_id: int, user_id: int) -> str:
    return f"{guild_id}:{user_id}"


def upsert_tempban(
    guild_id: int,
    user_id: int,
    unban_at: datetime,
    reason: str | None,
) -> None:
    data = load_tempbans()
    data[make_tempban_key(guild_id, user_id)] = {
        "guild_id": str(guild_id),
        "user_id": str(user_id),
        "unban_at": unban_at.astimezone(timezone.utc).isoformat(),
        "reason": reason or "",
    }
    save_tempbans(data)


def remove_tempban(guild_id: int, user_id: int) -> None:
    data = load_tempbans()
    data.pop(make_tempban_key(guild_id, user_id), None)
    save_tempbans(data)


def get_moderator_member(interaction: discord.Interaction) -> discord.Member | None:
    return interaction.user if isinstance(interaction.user, discord.Member) else None


def get_bot_member(
    guild: discord.Guild,
    client_user: discord.ClientUser | None,
) -> discord.Member | None:
    if client_user is None:
        return None
    return guild.get_member(client_user.id)


def can_act_on_target(
    moderator: discord.Member,
    target: discord.Member,
    bot_member: discord.Member,
) -> tuple[bool, str | None]:
    if target.id == moderator.id:
        return False, "Vous ne pouvez pas utiliser cette commande sur vous-même."
    if target.id == bot_member.id:
        return False, "Je ne peux pas exécuter cette action sur moi-même."
    if target.guild.owner_id == target.id:
        return False, "Vous ne pouvez pas exécuter cette action sur le propriétaire du serveur."
    if moderator.guild.owner_id != moderator.id and moderator.top_role <= target.top_role:
        return False, "Vous ne pouvez agir que sur des membres situés sous votre rôle principal."
    if bot_member.top_role <= target.top_role:
        return False, "Je ne peux agir que sur des membres situés sous mon rôle principal."
    return True, None
