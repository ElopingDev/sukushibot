import asyncio
import io
import json
import os
import random
import re
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands
from PIL import Image, ImageDraw, ImageFont

from economy import (
    add_balance,
    add_ecoban,
    add_slots_pot,
    clear_faction_invite,
    ensure_minimum_balance,
    get_all_factions,
    get_all_prison_records,
    get_balance_value,
    get_cooldown_remaining,
    get_faction_by_owner,
    get_faction_for_member,
    get_faction_invite,
    get_economy_stats,
    get_job,
    get_pair_cooldown_remaining,
    get_prison_record,
    get_slots_pot,
    get_top_balances,
    imprison_user,
    is_in_prison,
    is_ecobanned,
    load_economy,
    load_economy_meta,
    load_event_state,
    load_faction_state,
    load_lottery_state,
    load_json_dict,
    remove_prison_record,
    remove_ecoban,
    reset_all_balances,
    reset_slots_pot,
    reset_cooldown_files,
    record_economy_stat,
    save_economy,
    save_economy_meta,
    save_event_state,
    save_faction_state,
    save_lottery_state,
    save_json_dict,
    set_faction_invite,
    set_prison_record,
    set_balance_value,
    set_job,
    update_cooldown,
    update_pair_cooldown,
)
from moderation import (
    can_act_on_target,
    get_bot_member,
    get_moderator_member,
    load_tempbans,
    remove_tempban,
    upsert_tempban,
)
from levels import apply_message_xp, get_level_profile, get_top_levels, xp_needed_for_next_level

WELCOME_CHANNEL_ID = 1494255574949429438
GOODBYE_CHANNEL_ID = 1494255913366978641
AUTOROLE_CHANNEL_ID = 1494255821054414878
LEVELUP_CHANNEL_ID = 1494255415259693127
LOTTERY_CHANNEL_ID = 1494473046499786802
EVENT_CHANNEL_ID = 1494245154939469879
LOTTERY_PING_ROLE_ID = 1494474779355386027
TICKET_PANEL_CHANNEL_ID = 1494461780322287667
JOIN_ROLE_ID = 1494249084221919343
TICKET_STAFF_ROLE_ID = 1494265033784430632
PRIMARY_GUILD_ID = 1494245152858964070

BANNER_URL = "https://i.imgur.com/x4uAHlu.png"
SUKUSHI_PINK = discord.Color.from_rgb(255, 105, 180)
AUTOROLE_TITLE = "Autoroles"
AUTOROLE_FOOTER = "Sukushi bot | Autoroles"
ECONOMY_FILE = Path("economy.json")
ECONOMY_META_FILE = Path("economy_meta.json")
TEMPBAN_FILE = Path("tempbans.json")
DAILY_FILE = Path("daily.json")
WORK_FILE = Path("work.json")
JOB_FILE = Path("jobs.json")
PRISON_FILE = Path("prison.json")
ATTACK_FILE = Path("attack_cooldowns.json")
CHANGEJOB_FILE = Path("changejob.json")
LOTTERY_FILE = Path("lottery.json")
ECOBAN_FILE = Path("ecoban.json")
SLOTS_COOLDOWN_FILE = Path("slots_cooldowns.json")
STARTING_BALANCE = 1000
BALANCE_RESET_OWNER_ID = 885927546456272957
DAILY_REWARD = 1500
WORK_REWARD = 1000
WORK_FAIL_REWARD = 500
DAILY_COOLDOWN = timedelta(days=1)
WORK_COOLDOWN = timedelta(minutes=45)
ATTACK_COOLDOWN = timedelta(hours=5)
GLOBAL_ATTACK_COOLDOWN = timedelta(minutes=15)
CHANGEJOB_COOLDOWN = timedelta(days=1)
LOTTERY_DURATION = timedelta(hours=24)
PRISON_CHANCE = 0.15
LOTTERY_ENTRY_COST = 2000
LOTTERY_PRIZE = 10000
JAIL_CATEGORY_NAME = "prison"
JAIL_CHANNEL_PREFIX = "cellule"
JAIL_CHALLENGE_LENGTH = 35
JAIL_MEMORY_CHALLENGE_LENGTH = 7
JAIL_MIN_SOLVE_SECONDS = 10
JAIL_FAILURE_PERCENT = 0.05
JAIL_TAX_PERCENT_RANGE = (0.05, 0.12)
JAIL_VARIANTS = ("normal", "memory", "tax")
EVENT_GUESS_MIN = 1
EVENT_GUESS_MAX = 15
EVENT_GUESS_REWARD = 550
EVENT_MAX_GUESSES_PER_USER = 3
EVENT_FAST_STRING_LENGTH = 15
EVENT_TYPES = ("guess_number", "fast_string", "quick_math")
EVENT_TIMEOUT = timedelta(seconds=45)
EVENT_LOOP_POLL_INTERVAL = 30
EVENT_INTERVAL = timedelta(minutes=30)
SLOTS_COST = 100
SLOTS_JACKPOT_CHANCE = 0.03
SLOTS_COOLDOWN = timedelta(minutes=1)
MINES_GRID_SIZE = 4
MINES_TOTAL_TILES = MINES_GRID_SIZE * MINES_GRID_SIZE
MINES_HOUSE_EDGE = 0.68
MINES_MIN_CASHOUT_SAFE = 4
LEVEL_XP_COOLDOWN = timedelta(seconds=60)
LEVEL_XP_GAIN = (15, 25)
LEVEL_REWARD = 300
JOB_OPTIONS = {
    "mugger": "Braqueur",
    "dealer": "Dealer",
    "pickpocketer": "Pickpocket",
    "frauder": "Escroc",
}
JOB_ACTIONS = {
    "mugger": {
        "prompt": "Choisis ton coup du jour",
        "actions": [
            {"label": "Voler un passant", "reward": 700, "catch_chance": 0.06},
            {"label": "Braquer une supérette", "reward": 1050, "catch_chance": 0.18},
            {"label": "Braquer un bijoutier", "reward": 1500, "catch_chance": 0.40},
        ],
    },
    "dealer": {
        "prompt": "Choisis ce que tu vends",
        "actions": [
            {"label": "Vendre de la weed", "reward": 700, "catch_chance": 0.06},
            {"label": "Vendre du xanax", "reward": 1100, "catch_chance": 0.18},
            {"label": "Vendre de la meth", "reward": 1600, "catch_chance": 0.50},
        ],
    },
    "pickpocketer": {
        "prompt": "Choisis ta cible",
        "actions": [
            {"label": "Voler un portefeuille", "reward": 650, "catch_chance": 0.04},
            {"label": "Voler un téléphone", "reward": 950, "catch_chance": 0.15},
            {"label": "Détrousser un touriste riche", "reward": 1400, "catch_chance": 0.38},
        ],
    },
    "frauder": {
        "prompt": "Choisis ton arnaque",
        "actions": [
            {"label": "Petite arnaque en ligne", "reward": 750, "catch_chance": 0.03},
            {"label": "Faux virement bancaire", "reward": 1200, "catch_chance": 0.22},
            {"label": "Grosse fraude à la carte", "reward": 1700, "catch_chance": 0.55},
        ],
    },
}
ECONOMY_STAT_LABELS = {
    "daily": "Daily",
    "work_success": "Travail réussi",
    "work_caught": "Travail attrapé",
    "attack_steal": "Attaque",
    "blackjack_win": "Blackjack gain",
    "blackjack_loss": "Blackjack perte",
    "slots_jackpot": "Slots jackpot",
    "slots_spin": "Slots mise",
    "mines_cashout": "Mines cashout",
    "mines_loss": "Mines perte",
    "lottery_entry": "Loterie entrée",
    "lottery_win": "Loterie gain",
    "event_win": "Événement",
    "level_up": "Niveau",
    "prison_fail": "Prison échec",
    "prison_cheat": "Prison triche",
    "prison_tax": "Prison taxe",
    "staff_give": "Staff give",
    "staff_take": "Staff take",
}
FACTION_TAG_PATTERN = re.compile(r"^[A-Za-z0-9]{1,4}$")
ATTACK_STARTING_HP = 100
ATTACK_PLAYER_HIT_CHANCE = 0.78
ATTACK_AI_HIT_CHANCE = 0.55
ATTACK_PLAYER_DAMAGE = (18, 32)
ATTACK_AI_DAMAGE = (10, 20)
ATTACK_STEAL_PERCENT = (0.1, 0.15)
ACTIVE_ATTACK_USERS: set[int] = set()
ACTIVE_MINES_USERS: set[int] = set()
TICKET_OWNER_TOPIC_PREFIX = "ticket_owner:"
PRISONER_TOPIC_PREFIX = "prisoner:"

AUTOROLE_PANELS = [
    {
        "title": "Autoroles | Genre",
        "description": (
            "Réagis pour choisir le rôle qui correspond le mieux à ton genre.\n"
            "Un seul rôle de cette catégorie peut être actif à la fois."
        ),
        "include_banner": True,
        "entries": [
            {"emoji": "♂️", "label": "Homme", "role_id": 1494250520112791582},
            {"emoji": "♀️", "label": "Femme", "role_id": 1494250520662245446},
            {"emoji": "🌈", "label": "Non binaire", "role_id": 1494250522495029369},
            {"emoji": "❔", "label": "Autre", "role_id": 1494250524940173352},
        ],
    },
    {
        "title": "Autoroles | Âge",
        "description": (
            "Réagis pour sélectionner ta tranche d'âge.\n"
            "Un seul rôle de cette catégorie peut être actif à la fois."
        ),
        "include_banner": False,
        "entries": [
            {"emoji": "1️⃣", "label": "13-15 ans", "role_id": 1494249086126264401},
            {"emoji": "2️⃣", "label": "16-17 ans", "role_id": 1494249086931439698},
            {"emoji": "3️⃣", "label": "18 ans +", "role_id": 1494250520112533544},
        ],
    },
    {
        "title": "Autoroles | Pings",
        "description": (
            "Réagis pour recevoir les notifications qui t'intéressent.\n"
            "Tu peux cumuler plusieurs rôles dans cette catégorie."
        ),
        "include_banner": False,
        "entries": [
            {"emoji": "📢", "label": "Annonces", "role_id": 1494250525846278174},
            {"emoji": "🎁", "label": "Giveaway", "role_id": 1494250837814284389},
            {"emoji": "🎉", "label": "Events", "role_id": 1494250775734386781},
            {"emoji": "💸", "label": "Économie", "role_id": 1494474779355386027},
        ],
    },
]
AUTOROLE_MAP = {
    entry["emoji"]: entry["role_id"]
    for panel in AUTOROLE_PANELS
    for entry in panel["entries"]
}
AUTOROLE_LABELS = {
    entry["emoji"]: entry["label"]
    for panel in AUTOROLE_PANELS
    for entry in panel["entries"]
}
AUTOROLE_EXCLUSIVE_ROLE_GROUPS = [
    {1494250520112791582, 1494250520662245446, 1494250522495029369, 1494250524940173352},
    {1494249086126264401, 1494249086931439698, 1494250520112533544},
]

DURATION_PATTERN = re.compile(r"^\s*(\d+)\s*([smhd])\s*$", re.IGNORECASE)


def make_embed(
    title: str,
    description: str,
    *,
    color: discord.Color = discord.Color.blurple(),
    footer: str | None = "sukushi bot",
) -> discord.Embed:
    embed = discord.Embed(title=title, description=description, color=color)
    if footer:
        embed.set_footer(text=footer)
    return embed


def format_remaining_time(duration: timedelta) -> str:
    total_seconds = max(1, int(duration.total_seconds()))
    minutes, seconds = divmod(total_seconds, 60)
    hours, minutes = divmod(minutes, 60)

    parts: list[str] = []
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and not hours:
        parts.append(f"{seconds}s")
    return " ".join(parts)


def can_bypass_prison(member: discord.abc.User | discord.Member) -> bool:
    if not isinstance(member, discord.Member):
        return False

    permissions = member.guild_permissions
    return any(
        (
            permissions.administrator,
            permissions.moderate_members,
            permissions.kick_members,
            permissions.ban_members,
            permissions.manage_messages,
        )
    )


async def ensure_not_in_prison(
    interaction: discord.Interaction,
    *,
    allow_staff_bypass: bool = False,
) -> bool:
    if allow_staff_bypass and can_bypass_prison(interaction.user):
        return True

    record = get_prison_record(interaction.user.id)
    if record is None:
        return True

    channel_id = record.get("channel_id")
    channel_mention = f"<#{channel_id}>" if isinstance(channel_id, int) else "ton salon de prison"
    message_text = (
        "Tu es en prison et tu ne peux pas utiliser les commandes économiques pour le moment. "
        f"Va dans {channel_mention} et retape exactement le code demandé."
    )
    if interaction.response.is_done():
        await interaction.followup.send(
            message_text,
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            message_text,
            ephemeral=True,
        )
    return False


async def ensure_not_ecobanned(interaction: discord.Interaction) -> bool:
    if is_ecobanned(interaction.user.id):
        if interaction.response.is_done():
            await interaction.followup.send(
                "Tu es banni des commandes économiques du bot.",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message(
                "Tu es banni des commandes économiques du bot.",
                ephemeral=True,
            )
        return False
    return True


def prison_block(*, allow_staff_bypass: bool = False):
    async def predicate(interaction: discord.Interaction) -> bool:
        return await ensure_not_in_prison(
            interaction,
            allow_staff_bypass=allow_staff_bypass,
        )

    return app_commands.check(predicate)


def economy_block():
    async def predicate(interaction: discord.Interaction) -> bool:
        return await ensure_not_ecobanned(interaction)

    return app_commands.check(predicate)


def find_custom_emoji(guild: discord.Guild | None, name: str) -> discord.Emoji | None:
    if guild is None:
        return None
    return discord.utils.get(guild.emojis, name=name)


def get_custom_emoji_text(
    guild: discord.Guild | None,
    name: str,
    fallback: str = "🌸",
) -> str:
    emoji = find_custom_emoji(guild, name)
    return str(emoji) if emoji else fallback


def get_economy_stat_label(source: str) -> str:
    return ECONOMY_STAT_LABELS.get(source, source.replace("_", " ").title())


def normalize_faction_tag(tag: str) -> str:
    return tag.strip().upper()


def strip_faction_suffix(name: str, tag: str | None) -> str:
    if not tag:
        return name
    suffix = f" [{tag}]"
    return name[: -len(suffix)].rstrip() if name.endswith(suffix) else name


def get_faction_member_count(faction: dict[str, object]) -> int:
    members = faction.get("members", {})
    return len(members) if isinstance(members, dict) else 0


def get_faction_allies(faction: dict[str, object]) -> set[str]:
    raw_allies = faction.get("allies", [])
    if not isinstance(raw_allies, list):
        return set()
    return {str(ally_id) for ally_id in raw_allies}


def get_faction_by_tag(tag: str) -> tuple[int, dict[str, object]] | None:
    normalized_tag = normalize_faction_tag(tag)
    for owner_id, faction in get_all_factions():
        if normalize_faction_tag(str(faction.get("tag") or "")) == normalized_tag:
            return owner_id, faction
    return None


def factions_are_allied(owner_a: int, owner_b: int) -> bool:
    if owner_a == owner_b:
        return False
    faction_a = get_faction_by_owner(owner_a)
    faction_b = get_faction_by_owner(owner_b)
    if faction_a is None or faction_b is None:
        return False
    return str(owner_b) in get_faction_allies(faction_a) and str(owner_a) in get_faction_allies(faction_b)


async def sync_member_faction_nickname(
    member: discord.Member,
    *,
    old_tag: str | None = None,
    new_tag: str | None = None,
    base_nick: str | None = None,
    reason: str,
) -> bool:
    source_name = base_nick if base_nick is not None else (member.nick or member.display_name)
    clean_name = strip_faction_suffix(source_name, old_tag)

    if new_tag:
        suffix = f" [{new_tag}]"
        max_base_length = max(1, 32 - len(suffix))
        clean_name = clean_name[:max_base_length].rstrip() or member.display_name[:max_base_length]
        target_nick = f"{clean_name}{suffix}"
    else:
        target_nick = clean_name[:32] if base_nick is not None else None

    if member.nick == target_nick:
        return True

    try:
        await member.edit(nick=target_nick, reason=reason)
    except (discord.Forbidden, discord.HTTPException):
        return False
    return True


def build_faction_embed(
    guild: discord.Guild | None,
    *,
    owner_id: int,
    faction: dict[str, object],
) -> discord.Embed:
    name = str(faction.get("name") or "Faction")
    tag = str(faction.get("tag") or "Aucun")
    members = faction.get("members", {})
    member_ids = list(members.keys()) if isinstance(members, dict) else []
    member_mentions = [f"<@{member_id}>" for member_id in member_ids[:15]]
    owner_member = guild.get_member(owner_id) if guild is not None else None
    embed = make_embed(
        f"Faction | {name}",
        f"Tag actuel : **{tag}**",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Factions",
    )
    embed.add_field(
        name="Chef",
        value=owner_member.mention if owner_member is not None else f"<@{owner_id}>",
        inline=True,
    )
    embed.add_field(name="Membres", value=f"**{len(member_ids)}**", inline=True)
    embed.add_field(
        name="Liste",
        value="\n".join(member_mentions) if member_mentions else "Aucun membre.",
        inline=False,
    )
    if len(member_ids) > 15:
        embed.add_field(name="Note", value=f"{len(member_ids) - 15} autre(s) membre(s) non affiché(s).", inline=False)
    return embed


def get_role_by_id(guild: discord.Guild | None, role_id: int) -> discord.Role | None:
    if guild is None:
        return None
    return guild.get_role(role_id)


def member_has_role(member: discord.abc.User | discord.Member, role_id: int) -> bool:
    return isinstance(member, discord.Member) and any(role.id == role_id for role in member.roles)


def sanitize_ticket_name(display_name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9-]+", "-", display_name.lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "membre"


def make_ticket_topic(user_id: int) -> str:
    return f"{TICKET_OWNER_TOPIC_PREFIX}{user_id}"


def get_ticket_owner_id(channel: discord.abc.GuildChannel | None) -> int | None:
    if not isinstance(channel, discord.TextChannel) or channel.topic is None:
        return None
    if not channel.topic.startswith(TICKET_OWNER_TOPIC_PREFIX):
        return None

    raw_value = channel.topic.removeprefix(TICKET_OWNER_TOPIC_PREFIX)
    return int(raw_value) if raw_value.isdigit() else None


def find_open_ticket_channel(guild: discord.Guild, user_id: int) -> discord.TextChannel | None:
    expected_topic = make_ticket_topic(user_id)
    for channel in guild.text_channels:
        if channel.topic == expected_topic:
            return channel
    return None


def make_prison_topic(user_id: int) -> str:
    return f"{PRISONER_TOPIC_PREFIX}{user_id}"


def get_prisoner_id_from_channel(channel: discord.abc.GuildChannel | None) -> int | None:
    if not isinstance(channel, discord.TextChannel) or channel.topic is None:
        return None
    if not channel.topic.startswith(PRISONER_TOPIC_PREFIX):
        return None

    raw_value = channel.topic.removeprefix(PRISONER_TOPIC_PREFIX)
    return int(raw_value) if raw_value.isdigit() else None


def find_prison_channel(guild: discord.Guild, user_id: int) -> discord.TextChannel | None:
    expected_topic = make_prison_topic(user_id)
    for channel in guild.text_channels:
        if channel.topic == expected_topic:
            return channel
    return None


def make_prison_channel_name(display_name: str, user_id: int) -> str:
    base = sanitize_ticket_name(display_name)[:60].strip("-") or "membre"
    return f"{JAIL_CHANNEL_PREFIX}-{base}-{user_id}"[:100]


def generate_prison_challenge(length: int = JAIL_CHALLENGE_LENGTH) -> str:
    alphabet = string.ascii_letters + string.digits
    rng = random.SystemRandom()
    return "".join(rng.choice(alphabet) for _ in range(length))


def generate_memory_prison_challenge(length: int = JAIL_MEMORY_CHALLENGE_LENGTH) -> str:
    rng = random.SystemRandom()
    return "".join(rng.choice(string.digits) for _ in range(length))


def choose_prison_variant() -> str:
    return random.choice(JAIL_VARIANTS)


def compute_percentage_penalty(balance: int, percent: float) -> int:
    if balance <= 0:
        return 0
    penalty = int(balance * percent)
    return max(1, penalty)


def split_prison_challenge_text(challenge: str) -> list[str]:
    midpoint = (len(challenge) + 1) // 2
    return [challenge[:midpoint], challenge[midpoint:]]


def load_prison_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_name in ("arial.ttf", "DejaVuSans.ttf", "calibri.ttf", "tahoma.ttf"):
        try:
            return ImageFont.truetype(font_name, size=size)
        except OSError:
            continue
    return ImageFont.load_default()


def build_prison_challenge_file(challenge: str) -> discord.File:
    width = 920
    height = 220
    image = Image.new("RGB", (width, height), color=(248, 240, 234))
    draw = ImageDraw.Draw(image)

    title_font = load_prison_font(28)
    code_font = load_prison_font(46)
    draw.rounded_rectangle((16, 16, width - 16, height - 16), radius=24, outline=(40, 40, 40), width=3)
    draw.text((32, 28), "Retape exactement ce code dans le salon", font=title_font, fill=(35, 35, 35))

    lines = split_prison_challenge_text(challenge)
    y_positions = (95, 145)
    for line, y in zip(lines, y_positions):
        bbox = draw.textbbox((0, 0), line, font=code_font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        draw.text((x, y), line, font=code_font, fill=(25, 25, 25))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="prison-code.png")


def build_event_string_file(challenge: str) -> discord.File:
    width = 920
    height = 220
    image = Image.new("RGB", (width, height), color=(248, 240, 234))
    draw = ImageDraw.Draw(image)

    title_font = load_prison_font(28)
    code_font = load_prison_font(46)
    draw.rounded_rectangle((16, 16, width - 16, height - 16), radius=24, outline=(40, 40, 40), width=3)
    draw.text((32, 28), "Retape exactement cette chaîne", font=title_font, fill=(35, 35, 35))

    bbox = draw.textbbox((0, 0), challenge, font=code_font)
    text_width = bbox[2] - bbox[0]
    x = (width - text_width) // 2
    draw.text((x, 110), challenge, font=code_font, fill=(25, 25, 25))

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)
    return discord.File(buffer, filename="event-fast-string.png")


def get_autorole_exclusive_group(role_id: int) -> set[int] | None:
    for group in AUTOROLE_EXCLUSIVE_ROLE_GROUPS:
        if role_id in group:
            return group
    return None


def get_lottery_participants(state: dict[str, object]) -> list[int]:
    participants = state.get("participants", [])
    if not isinstance(participants, list):
        return []
    result: list[int] = []
    for user_id in participants:
        try:
            result.append(int(user_id))
        except (TypeError, ValueError):
            continue
    return result


def get_lottery_end_time(state: dict[str, object]) -> datetime | None:
    raw_value = state.get("ends_at")
    if not isinstance(raw_value, str):
        return None
    try:
        return datetime.fromisoformat(raw_value)
    except ValueError:
        return None


def build_guess_number_event_embed(*, message: str | None = None) -> discord.Embed:
    description = (
        f"Le bot a choisi un nombre entre **{EVENT_GUESS_MIN}** et **{EVENT_GUESS_MAX}**.\n"
        f"Le premier membre qui trouve le bon nombre gagne **{EVENT_GUESS_REWARD} Sukushi Dollars**.\n"
        f"Envoie simplement ton nombre dans ce salon.\n"
        f"Tu as droit à **{EVENT_MAX_GUESSES_PER_USER}** tentatives maximum."
    )
    if message:
        description = f"{description}\n\n{message}"

    return make_embed(
        "Événement | Devine le nombre",
        description,
        color=discord.Color.gold(),
        footer="Sukushi bot | Événement",
    )


def build_fast_string_event_embed(*, message: str | None = None) -> discord.Embed:
    description = (
        f"Le premier membre qui retape exactement cette chaîne de **{EVENT_FAST_STRING_LENGTH} caractères** gagne "
        f"**{EVENT_GUESS_REWARD} Sukushi Dollars**.\n"
        "Regarde l'image et retape exactement la chaîne dans ce salon."
    )
    if message:
        description = f"{description}\n\n{message}"

    embed = make_embed(
        "Événement | Chaîne la plus rapide",
        description,
        color=discord.Color.gold(),
        footer="Sukushi bot | Événement",
    )
    embed.set_image(url="attachment://event-fast-string.png")
    return embed


def build_quick_math_event_embed(problem_text: str, *, message: str | None = None) -> discord.Embed:
    description = (
        f"Le premier membre qui donne la bonne réponse gagne **{EVENT_GUESS_REWARD} Sukushi Dollars**.\n"
        f"Calcul : **{problem_text}**\n"
        f"Tu as droit à **{EVENT_MAX_GUESSES_PER_USER}** tentatives maximum."
    )
    if message:
        description = f"{description}\n\n{message}"

    return make_embed(
        "Événement | Calcul express",
        description,
        color=discord.Color.gold(),
        footer="Sukushi bot | Événement",
    )


def generate_fast_string_event_text(length: int = EVENT_FAST_STRING_LENGTH) -> str:
    alphabet = string.ascii_letters + string.digits
    rng = random.SystemRandom()
    return "".join(rng.choice(alphabet) for _ in range(length))


def generate_quick_math_event() -> tuple[str, str]:
    pattern = random.choice(("paren_mul", "paren_div", "mix_div", "mix_mul"))

    if pattern == "paren_mul":
        left = random.randint(2, 12)
        middle = random.randint(2, 12)
        right = random.randint(2, 8)
        answer = (left + middle) * right
        return f"({left} + {middle}) × {right}", str(answer)

    if pattern == "paren_div":
        divisor = random.randint(2, 10)
        quotient = random.randint(2, 12)
        extra = random.randint(2, 10)
        dividend = divisor * quotient
        answer = dividend // divisor + extra
        return f"({dividend} ÷ {divisor}) + {extra}", str(answer)

    if pattern == "mix_div":
        left = random.randint(2, 10)
        right = random.randint(2, 10)
        divisor = random.randint(2, 8)
        product = right * divisor
        answer = left + (product // divisor)
        return f"{left} + ({product} ÷ {divisor})", str(answer)

    left = random.randint(2, 10)
    middle = random.randint(2, 10)
    right = random.randint(2, 10)
    answer = left * middle - right
    return f"({left} × {middle}) - {right}", str(answer)


def build_lottery_embed(*, ends_at: datetime, participants_count: int) -> discord.Embed:
    unix_timestamp = int(ends_at.timestamp())
    embed = make_embed(
        "Loterie Sukushi",
        (
            f"Participe à la loterie du serveur pour **{LOTTERY_ENTRY_COST} Sukushi Dollars**.\n"
            f"Le gagnant remportera **{LOTTERY_PRIZE} Sukushi Dollars**.\n\n"
            f"Fin du tirage : <t:{unix_timestamp}:F>\n"
            f"Temps restant : <t:{unix_timestamp}:R>"
        ),
        color=discord.Color.gold(),
        footer="Sukushi bot | Loterie",
    )
    embed.add_field(name="Participants", value=f"**{participants_count}**", inline=True)
    embed.add_field(name="Coût", value=f"**{LOTTERY_ENTRY_COST} SD**", inline=True)
    embed.add_field(name="Gain", value=f"**{LOTTERY_PRIZE} SD**", inline=True)
    return embed


def build_lottery_start_message() -> str:
    return (
        f"<@&{LOTTERY_PING_ROLE_ID}> une nouvelle loterie vient de commencer !\n"
        f"Clique sur le bouton pour participer pour **{LOTTERY_ENTRY_COST} Sukushi Dollars**."
    )


def build_slots_embed(
    guild: discord.Guild | None,
    *,
    title: str,
    symbols: list[str],
    description: str,
    color: discord.Color,
    pot_amount: int,
) -> discord.Embed:
    embed = make_embed(
        title,
        description,
        color=color,
        footer="Sukushi bot | Slots",
    )
    embed.add_field(name="Machine", value=" ".join(symbols), inline=False)
    embed.add_field(name="Pot global", value=f"**{pot_amount} Sukushi Dollars**", inline=True)
    embed.add_field(name="Mise", value=f"**{SLOTS_COST} Sukushi Dollars**", inline=True)
    return embed


def calculate_mines_multiplier(bombs: int, safe_revealed: int) -> float:
    if safe_revealed <= 0:
        return 1.0

    multiplier = MINES_HOUSE_EDGE
    safe_tiles = MINES_TOTAL_TILES - bombs
    for index in range(safe_revealed):
        multiplier *= (MINES_TOTAL_TILES - index) / (safe_tiles - index)
    early_penalty = {
        1: 0.18,
        2: 0.30,
        3: 0.45,
        4: 0.62,
        5: 0.80,
    }
    multiplier *= early_penalty.get(safe_revealed, 1.0)
    return multiplier


def build_mines_embed(
    guild: discord.Guild | None,
    *,
    player: discord.abc.User,
    bet: int,
    bombs: int,
    safe_revealed: int,
    multiplier: float,
    potential_cashout: int,
    title: str,
    description: str,
    color: discord.Color,
) -> discord.Embed:
    coinbag_symbol = get_custom_emoji_text(guild, "coinbag", fallback="🪙")
    embed = make_embed(
        title,
        description,
        color=color,
        footer="Sukushi bot | Mines",
    )
    embed.add_field(name="Joueur", value=player.mention, inline=True)
    embed.add_field(name="Mise", value=f"**{bet} Sukushi Dollars**", inline=True)
    embed.add_field(name="Bombes", value=f"**{bombs}**", inline=True)
    embed.add_field(
        name="Cases sûres trouvées",
        value=f"**{safe_revealed}/{MINES_TOTAL_TILES - bombs}** {coinbag_symbol}",
        inline=True,
    )
    embed.add_field(name="Multiplicateur", value=f"**x{multiplier:.2f}**", inline=True)
    embed.add_field(name="Cashout actuel", value=f"**{potential_cashout} Sukushi Dollars**", inline=True)
    return embed


def parse_duration(value: str) -> timedelta:
    match = DURATION_PATTERN.match(value)
    if match is None:
        raise ValueError("Utilise une durée comme 10m, 2h, 3d ou 45s.")

    amount = int(match.group(1))
    unit = match.group(2).lower()
    if amount <= 0:
        raise ValueError("La durée doit être supérieure à 0.")

    multipliers = {
        "s": 1,
        "m": 60,
        "h": 3600,
        "d": 86400,
    }
    return timedelta(seconds=amount * multipliers[unit])


def format_timedelta(duration: timedelta) -> str:
    total_seconds = int(duration.total_seconds())
    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    parts: list[str] = []
    if days:
        parts.append(f"{days}d")
    if hours:
        parts.append(f"{hours}h")
    if minutes:
        parts.append(f"{minutes}m")
    if seconds and not parts:
        parts.append(f"{seconds}s")
    return " ".join(parts) or "0s"


def _legacy_get_moderator_member(interaction: discord.Interaction) -> discord.Member | None:
    return interaction.user if isinstance(interaction.user, discord.Member) else None


def _legacy_get_bot_member(
    guild: discord.Guild,
    client_user: discord.ClientUser | None,
) -> discord.Member | None:
    if client_user is None:
        return None
    return guild.get_member(client_user.id)


def _legacy_can_act_on_target(
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


CARD_VALUES = {
    "2": 2,
    "3": 3,
    "4": 4,
    "5": 5,
    "6": 6,
    "7": 7,
    "8": 8,
    "9": 9,
    "10": 10,
    "J": 10,
    "Q": 10,
    "K": 10,
    "A": 11,
}


def create_blackjack_deck() -> list[str]:
    suits = ["♠", "♥", "♦", "♣"]
    ranks = list(CARD_VALUES.keys())
    deck = [f"{rank}{suit}" for suit in suits for rank in ranks]
    random.shuffle(deck)
    return deck


def get_card_rank(card: str) -> str:
    return card[:-1]


def calculate_hand_value(cards: list[str]) -> int:
    total = 0
    aces = 0
    for card in cards:
        rank = get_card_rank(card)
        total += CARD_VALUES[rank]
        if rank == "A":
            aces += 1

    while total > 21 and aces > 0:
        total -= 10
        aces -= 1
    return total


def format_hand(cards: list[str], *, hidden: bool = False) -> str:
    if hidden and len(cards) > 1:
        return f"{cards[0]} • ?"
    return " • ".join(cards)


def make_hp_bar(current_hp: int, max_hp: int = ATTACK_STARTING_HP, length: int = 10) -> str:
    current_hp = max(0, min(current_hp, max_hp))
    filled = round((current_hp / max_hp) * length)
    return f"{'█' * filled}{'░' * (length - filled)} {current_hp}/{max_hp}"


class AttackView(discord.ui.View):
    def __init__(self, attacker: discord.Member, target: discord.Member) -> None:
        super().__init__(timeout=120)
        self.attacker = attacker
        self.target = target
        self.attacker_hp = ATTACK_STARTING_HP
        self.target_hp = ATTACK_STARTING_HP
        self.finished = False
        self.message: discord.Message | None = None
        self.log: list[str] = ["Le combat commence."]

    def build_embed(self, result_text: str | None = None) -> discord.Embed:
        embed = make_embed(
            "Attaque",
            f"{self.attacker.mention} tente de détrousser **{self.target.display_name}**.",
            color=SUKUSHI_PINK,
            footer=f"Combat de {self.attacker.display_name}",
        )
        embed.add_field(
            name=self.attacker.display_name,
            value=make_hp_bar(self.attacker_hp),
            inline=False,
        )
        embed.add_field(
            name=f"{self.target.display_name} (IA)",
            value=make_hp_bar(self.target_hp),
            inline=False,
        )
        embed.add_field(name="Journal", value="\n".join(self.log[-4:]), inline=False)
        if result_text:
            embed.add_field(name="Résultat", value=result_text, inline=False)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await ensure_not_in_prison(interaction):
            return False
        if not await ensure_not_ecobanned(interaction):
            return False
        if interaction.user.id != self.attacker.id:
            await interaction.response.send_message(
                "Seul le joueur qui a lancé cette attaque peut utiliser ce bouton.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.finished:
            return
        self.finished = True
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            await self.message.edit(
                embed=self.build_embed("Combat expiré. Aucun argent n'a été volé."),
                view=self,
            )
        ACTIVE_ATTACK_USERS.discard(self.attacker.id)
        ACTIVE_ATTACK_USERS.discard(self.target.id)

    async def finish_combat(self, interaction: discord.Interaction, *, attacker_won: bool) -> None:
        self.finished = True
        update_pair_cooldown(ATTACK_FILE, self.attacker.id, self.target.id)

        attacker_balance = get_balance_value(self.attacker.id)
        target_balance = get_balance_value(self.target.id)
        steal_ratio = random.uniform(*ATTACK_STEAL_PERCENT)

        if attacker_won:
            amount = max(1, int(target_balance * steal_ratio)) if target_balance > 0 else 0
            if amount > 0:
                set_balance_value(self.target.id, target_balance - amount)
                new_attacker_balance = add_balance(self.attacker.id, amount)
                record_economy_stat("attack_steal", amount)
                result = (
                    f"Tu as gagné le combat et volé **{amount} Sukushi Dollars** à {self.target.mention}.\n"
                    f"Nouveau solde : **{new_attacker_balance} Sukushi Dollars**."
                )
            else:
                result = f"Tu as gagné, mais {self.target.mention} n'avait rien à voler."
        else:
            amount = max(1, int(attacker_balance * steal_ratio)) if attacker_balance > 0 else 0
            if amount > 0:
                set_balance_value(self.attacker.id, attacker_balance - amount)
                new_target_balance = add_balance(self.target.id, amount)
                record_economy_stat("attack_steal", amount)
                result = (
                    f"Tu as perdu le combat. **{amount} Sukushi Dollars** ont été récupérés par {self.target.mention}.\n"
                    f"Nouveau solde de la cible : **{new_target_balance} Sukushi Dollars**."
                )
            else:
                result = "Tu as perdu le combat, mais tu n'avais rien à perdre."

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            embed=self.build_embed(result),
            view=self,
        )
        ACTIVE_ATTACK_USERS.discard(self.attacker.id)
        ACTIVE_ATTACK_USERS.discard(self.target.id)
        self.stop()

    @discord.ui.button(label="Attaquer", style=discord.ButtonStyle.danger)
    async def attack_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if self.finished:
            return

        if random.random() <= ATTACK_PLAYER_HIT_CHANCE:
            damage = random.randint(*ATTACK_PLAYER_DAMAGE)
            self.target_hp = max(0, self.target_hp - damage)
            self.log.append(f"Tu touches {self.target.display_name} pour **{damage}** dégâts.")
        else:
            self.log.append("Tu rates ton attaque.")

        if self.target_hp <= 0:
            await self.finish_combat(interaction, attacker_won=True)
            return

        if random.random() <= ATTACK_AI_HIT_CHANCE:
            damage = random.randint(*ATTACK_AI_DAMAGE)
            self.attacker_hp = max(0, self.attacker_hp - damage)
            self.log.append(f"{self.target.display_name} te touche pour **{damage}** dégâts.")
        else:
            self.log.append(f"{self.target.display_name} rate sa contre-attaque.")

        if self.attacker_hp <= 0:
            await self.finish_combat(interaction, attacker_won=False)
            return

        await interaction.response.edit_message(embed=self.build_embed(), view=self)


class BlackjackView(discord.ui.View):
    def __init__(self, player: discord.abc.User, bet: int) -> None:
        super().__init__(timeout=120)
        self.player = player
        self.bet = bet
        self.deck = create_blackjack_deck()
        self.player_cards: list[str] = []
        self.dealer_cards: list[str] = []
        self.player_cards.append(self.deck.pop())
        self.dealer_cards.append(self.deck.pop())
        self.player_cards.append(self.deck.pop())
        self.dealer_cards.append(self.deck.pop())
        self.finished = False
        self.message: discord.Message | None = None

    def build_embed(self, *, reveal_dealer: bool, result_text: str | None = None) -> discord.Embed:
        player_total = calculate_hand_value(self.player_cards)
        dealer_total = calculate_hand_value(self.dealer_cards)
        embed = make_embed(
            "Blackjack",
            f"Mise : **{self.bet} Sukushi Dollars**",
            color=SUKUSHI_PINK,
            footer=f"Partie de {self.player.display_name}",
        )
        embed.add_field(
            name=f"Ta main ({player_total})",
            value=format_hand(self.player_cards),
            inline=False,
        )
        if reveal_dealer:
            embed.add_field(
                name=f"Main du dealer ({dealer_total})",
                value=format_hand(self.dealer_cards),
                inline=False,
            )
        else:
            visible_total = CARD_VALUES[get_card_rank(self.dealer_cards[0])]
            embed.add_field(
                name=f"Main du dealer ({visible_total}+)",
                value=format_hand(self.dealer_cards, hidden=True),
                inline=False,
            )
        if result_text:
            embed.add_field(name="Résultat", value=result_text, inline=False)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await ensure_not_in_prison(interaction):
            return False
        if not await ensure_not_ecobanned(interaction):
            return False
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "Seul le joueur qui a lancé cette partie peut utiliser ces boutons.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.finished:
            return
        self.finished = True
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            await self.message.edit(
                embed=self.build_embed(
                    reveal_dealer=True,
                    result_text="Partie expirée. Aucune mise n'a été retirée.",
                ),
                view=self,
            )

    def is_blackjack(self, cards: list[str]) -> bool:
        return len(cards) == 2 and calculate_hand_value(cards) == 21

    async def start_game(self, interaction: discord.Interaction) -> None:
        player_blackjack = self.is_blackjack(self.player_cards)
        dealer_blackjack = self.is_blackjack(self.dealer_cards)

        if not player_blackjack and not dealer_blackjack:
            await interaction.response.send_message(
                embed=self.build_embed(reveal_dealer=False),
                view=self,
            )
            self.message = await interaction.original_response()
            return

        self.finished = True
        for child in self.children:
            child.disabled = True

        if player_blackjack and dealer_blackjack:
            result = (
                "Blackjack des deux côtés. Push.\n"
                f"Solde : **{get_balance_value(self.player.id)} Sukushi Dollars**."
            )
        elif player_blackjack:
            gain = int(self.bet * 1.5)
            new_balance = add_balance(self.player.id, gain)
            record_economy_stat("blackjack_win", gain)
            result = (
                f"Blackjack naturel. Tu gagnes **{gain}**.\n"
                f"Nouveau solde : **{new_balance} Sukushi Dollars**."
            )
        else:
            new_balance = add_balance(self.player.id, -self.bet)
            record_economy_stat("blackjack_loss", -self.bet)
            result = (
                f"Le dealer a un blackjack naturel. Tu perds **{self.bet}**.\n"
                f"Nouveau solde : **{new_balance} Sukushi Dollars**."
            )

        await interaction.response.send_message(
            embed=self.build_embed(reveal_dealer=True, result_text=result),
            view=self,
        )
        self.message = await interaction.original_response()
        self.stop()

    async def finalize_game(self, interaction: discord.Interaction) -> None:
        if self.finished:
            return

        self.finished = True
        player_total = calculate_hand_value(self.player_cards)
        while calculate_hand_value(self.dealer_cards) < 17:
            self.dealer_cards.append(self.deck.pop())
        dealer_total = calculate_hand_value(self.dealer_cards)

        if player_total > 21:
            new_balance = add_balance(self.player.id, -self.bet)
            record_economy_stat("blackjack_loss", -self.bet)
            result = f"Tu dépasses 21. Tu perds **{self.bet}**.\nNouveau solde : **{new_balance} Sukushi Dollars**."
        elif dealer_total > 21 or player_total > dealer_total:
            new_balance = add_balance(self.player.id, self.bet)
            record_economy_stat("blackjack_win", self.bet)
            result = f"Tu gagnes **{self.bet}**.\nNouveau solde : **{new_balance} Sukushi Dollars**."
        elif player_total < dealer_total:
            new_balance = add_balance(self.player.id, -self.bet)
            record_economy_stat("blackjack_loss", -self.bet)
            result = f"Le dealer gagne. Tu perds **{self.bet}**.\nNouveau solde : **{new_balance} Sukushi Dollars**."
        else:
            result = (
                f"Égalité. Ta mise de **{self.bet}** est conservée.\n"
                f"Solde : **{get_balance_value(self.player.id)} Sukushi Dollars**."
            )

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            embed=self.build_embed(reveal_dealer=True, result_text=result),
            view=self,
        )
        self.stop()

    @discord.ui.button(label="Hit", style=discord.ButtonStyle.success)
    async def hit_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        self.player_cards.append(self.deck.pop())
        if calculate_hand_value(self.player_cards) > 21:
            await self.finalize_game(interaction)
            return

        await interaction.response.edit_message(
            embed=self.build_embed(reveal_dealer=False),
            view=self,
        )

    @discord.ui.button(label="Stand", style=discord.ButtonStyle.secondary)
    async def stand_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        await self.finalize_game(interaction)


class MinesCellButton(discord.ui.Button):
    def __init__(self, index: int) -> None:
        super().__init__(label="?", style=discord.ButtonStyle.secondary, row=index // MINES_GRID_SIZE)
        self.index = index

    async def callback(self, interaction: discord.Interaction) -> None:
        if not isinstance(self.view, MinesView):
            return
        await self.view.handle_cell_click(interaction, self)


class MinesCashoutButton(discord.ui.Button):
    def __init__(self) -> None:
        super().__init__(
            label="Récupérer",
            style=discord.ButtonStyle.success,
            row=4,
            emoji="💰",
            disabled=True,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not isinstance(self.view, MinesView):
            return
        await self.view.cashout(interaction)


class MinesView(discord.ui.View):
    def __init__(self, player: discord.abc.User, bet: int, bombs: int, guild: discord.Guild | None) -> None:
        super().__init__(timeout=120)
        self.player = player
        self.bet = bet
        self.bombs = bombs
        self.guild = guild
        self.finished = False
        self.message: discord.Message | None = None
        self.safe_revealed = 0
        self.revealed_cells: set[int] = set()
        self.bomb_positions = set(random.sample(range(MINES_TOTAL_TILES), bombs))
        self.coinbag_symbol = get_custom_emoji_text(guild, "coinbag", fallback="🪙")
        self.cashout_button = MinesCashoutButton()

        for index in range(MINES_TOTAL_TILES):
            self.add_item(MinesCellButton(index))
        self.add_item(self.cashout_button)

    def get_multiplier(self) -> float:
        return calculate_mines_multiplier(self.bombs, self.safe_revealed)

    def get_cashout_amount(self) -> int:
        if self.safe_revealed <= 0:
            return self.bet
        return max(0, int(self.bet * self.get_multiplier()))

    def build_active_embed(self) -> discord.Embed:
        cashout_amount = self.get_cashout_amount()
        return build_mines_embed(
            self.guild,
            player=self.player,
            bet=self.bet,
            bombs=self.bombs,
            safe_revealed=self.safe_revealed,
            multiplier=self.get_multiplier(),
            potential_cashout=cashout_amount,
            title="Casino | Mines",
            description=(
                "Clique sur les cases pour trouver les sacs de pièces sans toucher une bombe.\n"
                f"Tu peux récupérer ton gain à partir de **{MINES_MIN_CASHOUT_SAFE} cases sûres**."
            ),
            color=SUKUSHI_PINK,
        )

    def reveal_board(self, *, triggered_bomb: int | None = None) -> None:
        for child in self.children:
            if isinstance(child, MinesCellButton):
                child.disabled = True
                child.label = ""
                if child.index in self.bomb_positions:
                    child.style = discord.ButtonStyle.danger
                    child.emoji = "💣"
                elif child.index in self.revealed_cells:
                    child.style = discord.ButtonStyle.success
                    child.emoji = self.coinbag_symbol
                else:
                    child.style = discord.ButtonStyle.secondary
                    child.emoji = "▫️"
                if triggered_bomb is not None and child.index == triggered_bomb:
                    child.style = discord.ButtonStyle.danger
                    child.emoji = "💥"
        self.cashout_button.disabled = True

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await ensure_not_in_prison(interaction):
            return False
        if not await ensure_not_ecobanned(interaction):
            return False
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "Seul le joueur qui a lancé cette partie peut utiliser ces boutons.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.finished:
            return
        self.finished = True
        self.reveal_board()
        ACTIVE_MINES_USERS.discard(self.player.id)
        if self.message is not None:
            await self.message.edit(
                embed=build_mines_embed(
                    self.guild,
                    player=self.player,
                    bet=self.bet,
                    bombs=self.bombs,
                    safe_revealed=self.safe_revealed,
                    multiplier=self.get_multiplier(),
                    potential_cashout=self.get_cashout_amount(),
                    title="Casino | Mines expiré",
                    description="La partie a expiré. La mise est perdue.",
                    color=discord.Color.red(),
                ),
                view=self,
            )
        self.stop()

    async def finish_loss(self, interaction: discord.Interaction, *, triggered_bomb: int) -> None:
        self.finished = True
        self.reveal_board(triggered_bomb=triggered_bomb)
        record_economy_stat("mines_loss", -self.bet)
        ACTIVE_MINES_USERS.discard(self.player.id)
        await interaction.response.edit_message(
            embed=build_mines_embed(
                self.guild,
                player=self.player,
                bet=self.bet,
                bombs=self.bombs,
                safe_revealed=self.safe_revealed,
                multiplier=self.get_multiplier(),
                potential_cashout=0,
                title="Casino | Boom",
                description=(
                    f"{self.player.mention} a touché une bombe.\n"
                    f"Tu perds **{self.bet} Sukushi Dollars**."
                ),
                color=discord.Color.red(),
            ),
            view=self,
        )
        self.stop()

    async def finish_win(self, interaction: discord.Interaction, *, perfect_clear: bool = False) -> None:
        self.finished = True
        self.reveal_board()
        winnings = self.get_cashout_amount()
        new_balance = add_balance(self.player.id, winnings)
        record_economy_stat("mines_cashout", winnings)
        ACTIVE_MINES_USERS.discard(self.player.id)
        description = (
            f"{self.player.mention} encaisse **{winnings} Sukushi Dollars**.\n"
            f"Nouveau solde : **{new_balance} Sukushi Dollars**."
        )
        if perfect_clear:
            description = (
                f"{self.player.mention} a nettoyé toute la grille.\n"
                f"Tu remportes **{winnings} Sukushi Dollars**.\n"
                f"Nouveau solde : **{new_balance} Sukushi Dollars**."
            )
        await interaction.response.edit_message(
            embed=build_mines_embed(
                self.guild,
                player=self.player,
                bet=self.bet,
                bombs=self.bombs,
                safe_revealed=self.safe_revealed,
                multiplier=self.get_multiplier(),
                potential_cashout=winnings,
                title="Casino | Cashout",
                description=description,
                color=discord.Color.green(),
            ),
            view=self,
        )
        self.stop()

    async def handle_cell_click(self, interaction: discord.Interaction, button: MinesCellButton) -> None:
        if self.finished or button.index in self.revealed_cells:
            return

        if button.index in self.bomb_positions:
            await self.finish_loss(interaction, triggered_bomb=button.index)
            return

        self.revealed_cells.add(button.index)
        self.safe_revealed += 1
        button.disabled = True
        button.label = ""
        button.style = discord.ButtonStyle.success
        button.emoji = self.coinbag_symbol

        cashout_amount = self.get_cashout_amount()
        if self.safe_revealed >= MINES_MIN_CASHOUT_SAFE:
            self.cashout_button.disabled = False
            self.cashout_button.label = f"Récupérer {cashout_amount}"
        else:
            remaining_safe = MINES_MIN_CASHOUT_SAFE - self.safe_revealed
            self.cashout_button.disabled = True
            self.cashout_button.label = f"Encore {remaining_safe}"

        if self.safe_revealed >= MINES_TOTAL_TILES - self.bombs:
            await self.finish_win(interaction, perfect_clear=True)
            return

        await interaction.response.edit_message(
            embed=self.build_active_embed(),
            view=self,
        )

    async def cashout(self, interaction: discord.Interaction) -> None:
        if self.finished:
            return
        if self.safe_revealed < MINES_MIN_CASHOUT_SAFE:
            await interaction.response.send_message(
                f"Tu dois révéler au moins **{MINES_MIN_CASHOUT_SAFE}** cases sûres avant de récupérer tes gains.",
                ephemeral=True,
            )
            return
        await self.finish_win(interaction)


class JobSelect(discord.ui.Select):
    def __init__(self, player: discord.abc.User, *, allow_change: bool = False) -> None:
        options = [
            discord.SelectOption(
                label=label,
                value=key,
                description=f"Choisis {label} comme métier criminel permanent.",
            )
            for key, label in JOB_OPTIONS.items()
        ]
        super().__init__(
            placeholder="Choisis ton métier criminel",
            min_values=1,
            max_values=1,
            options=options,
        )
        self.player = player
        self.allow_change = allow_change

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await ensure_not_ecobanned(interaction):
            return
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "Seul le joueur qui a ouvert ce menu peut choisir le métier.",
                ephemeral=True,
            )
            return

        current_job = get_job(interaction.user.id)
        if current_job is not None and not self.allow_change:
            await interaction.response.send_message(
                "Tu as déjà un métier permanent.",
                ephemeral=True,
            )
            return

        job_key = self.values[0]
        if current_job == job_key:
            await interaction.response.send_message(
                "Tu as déjà ce métier.",
                ephemeral=True,
            )
            return

        set_job(interaction.user.id, job_key)
        if self.allow_change:
            update_cooldown(CHANGEJOB_FILE, interaction.user.id)
        self.view.stop()
        for child in self.view.children:
            child.disabled = True

        title = "Métier changé" if self.allow_change else "Métier choisi"
        description = (
            f"Tu es maintenant **{JOB_OPTIONS[job_key]}**.\n"
            + (
                "Tu pourras rechanger de métier après le cooldown."
                if self.allow_change
                else "Ce choix est permanent pour le moment."
            )
        )
        embed = make_embed(
            title,
            description,
            color=SUKUSHI_PINK,
            footer="Sukushi bot | Métiers",
        )
        await interaction.response.edit_message(embed=embed, view=self.view)


class JobSelectView(discord.ui.View):
    def __init__(self, player: discord.abc.User, *, allow_change: bool = False) -> None:
        super().__init__(timeout=120)
        self.player = player
        self.add_item(JobSelect(player, allow_change=allow_change))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await ensure_not_in_prison(interaction):
            return False
        if not await ensure_not_ecobanned(interaction):
            return False
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "Seul le joueur qui a ouvert ce menu peut l'utiliser.",
                ephemeral=True,
            )
            return False
        return True


class WorkMinigameView(discord.ui.View):
    def __init__(self, player: discord.abc.User, job_key: str) -> None:
        super().__init__(timeout=90)
        self.player = player
        self.job_key = job_key
        self.finished = False
        self.message: discord.Message | None = None
        self.job_data = JOB_ACTIONS[job_key]
        self.prompt = self.job_data["prompt"]

        for action in self.job_data["actions"]:
            button = discord.ui.Button(label=action["label"], style=discord.ButtonStyle.secondary)
            button.callback = self.make_callback(action)
            self.add_item(button)

    def build_embed(self, result_text: str | None = None) -> discord.Embed:
        lines = []
        for action in self.job_data["actions"]:
            chance_percent = int(action["catch_chance"] * 100)
            lines.append(
                f"• **{action['label']}**: +{action['reward']} SD | Risque prison: **{chance_percent}%**"
            )

        embed = make_embed(
            f"Travail | {JOB_OPTIONS[self.job_key]}",
            (
                f"Tâche : **{self.prompt}**\n"
                f"{chr(10).join(lines)}"
            ),
            color=SUKUSHI_PINK,
            footer=f"Mission de {self.player.display_name}",
        )
        if result_text:
            embed.add_field(name="Résultat", value=result_text, inline=False)
        return embed

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if not await ensure_not_in_prison(interaction):
            return False
        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "Seul le joueur qui a lancé cette mission peut utiliser ces boutons.",
                ephemeral=True,
            )
            return False
        return True

    async def on_timeout(self) -> None:
        if self.finished:
            return
        self.finished = True
        for child in self.children:
            child.disabled = True
        if self.message is not None:
            await self.message.edit(
                embed=self.build_embed("Mission expirée. Aucun argent n'a été gagné."),
                view=self,
            )

    def make_callback(self, action: dict[str, object]):
        async def callback(interaction: discord.Interaction) -> None:
            if self.finished:
                return

            self.finished = True
            for child in self.children:
                child.disabled = True

            update_cooldown(WORK_FILE, interaction.user.id)

            reward = int(action["reward"])
            catch_chance = float(action["catch_chance"])
            action_label = str(action["label"])

            if random.random() < catch_chance:
                prison_reward = reward // 2
                new_balance = add_balance(interaction.user.id, prison_reward)
                record_economy_stat("work_caught", prison_reward)
                if isinstance(interaction.user, discord.Member) and isinstance(interaction.client, SukushiBot):
                    await interaction.client.send_member_to_prison(
                        interaction.user,
                        reason=f"Mission ratée : {action_label}",
                    )
                result = (
                    f"Tu as choisi **{action_label}**.\n"
                    f"Tu t'es fait attraper. Tu ne gardes que **{prison_reward} Sukushi Dollars** et tu pars en prison.\n"
                    "Tu dois maintenant réussir le test dans ton salon de prison pour sortir.\n"
                    f"Nouveau solde : **{new_balance} Sukushi Dollars**."
                )
            else:
                new_balance = add_balance(interaction.user.id, reward)
                record_economy_stat("work_success", reward)
                result = (
                    f"Tu as choisi **{action_label}**.\n"
                    f"Mission réussie. Tu gagnes **{reward} Sukushi Dollars**.\n"
                    f"Nouveau solde : **{new_balance} Sukushi Dollars**."
                )

            await interaction.response.edit_message(
                embed=self.build_embed(result),
                view=self,
            )
            self.stop()

        return callback


class TicketOpenView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Ouvrir un ticket",
        style=discord.ButtonStyle.success,
        custom_id="ticket:open",
    )
    async def open_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
            await interaction.response.send_message(
                "Cette interaction doit être utilisée dans le serveur.",
                ephemeral=True,
            )
            return

        staff_role = get_role_by_id(interaction.guild, TICKET_STAFF_ROLE_ID)
        panel_channel = interaction.guild.get_channel(TICKET_PANEL_CHANNEL_ID)
        if staff_role is None or not isinstance(panel_channel, discord.TextChannel):
            await interaction.response.send_message(
                "Le système de tickets n'est pas configuré correctement.",
                ephemeral=True,
            )
            return

        existing_channel = find_open_ticket_channel(interaction.guild, interaction.user.id)
        if existing_channel is not None:
            await interaction.response.send_message(
                f"Tu as déjà un ticket ouvert : {existing_channel.mention}.",
                ephemeral=True,
            )
            return

        bot_member = get_bot_member(interaction.guild, bot.user)
        if bot_member is None:
            await interaction.response.send_message(
                "Je n'arrive pas à vérifier mes permissions dans ce serveur.",
                ephemeral=True,
            )
            return

        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                attach_files=True,
                embed_links=True,
            ),
            staff_role: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
            ),
            bot_member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
            ),
        }

        channel_name = f"ticket-{sanitize_ticket_name(interaction.user.display_name)}"
        ticket_channel = await interaction.guild.create_text_channel(
            name=channel_name,
            category=panel_channel.category,
            topic=make_ticket_topic(interaction.user.id),
            overwrites=overwrites,
            reason=f"Ticket ouvert par {interaction.user}",
        )

        embed = make_embed(
            "Ticket ouvert",
            (
                f"Bonjour {interaction.user.mention}, un membre du staff va te répondre ici.\n"
                "Explique clairement ton problème ou ta demande pour qu'on puisse t'aider rapidement."
            ),
            color=SUKUSHI_PINK,
            footer="Sukushi bot | Tickets",
        )
        await ticket_channel.send(
            content=f"{interaction.user.mention} <@&{TICKET_STAFF_ROLE_ID}>",
            embed=embed,
            view=TicketCloseView(),
        )
        await interaction.response.send_message(
            f"Ton ticket a été créé : {ticket_channel.mention}.",
            ephemeral=True,
        )


class TicketCloseView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Fermer le ticket",
        style=discord.ButtonStyle.danger,
        custom_id="ticket:close",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Cette interaction doit être utilisée dans le serveur.",
                ephemeral=True,
            )
            return

        if not member_has_role(interaction.user, TICKET_STAFF_ROLE_ID):
            await interaction.response.send_message(
                "Seuls les membres du staff peuvent fermer un ticket.",
                ephemeral=True,
            )
            return

        if not isinstance(interaction.channel, discord.TextChannel):
            await interaction.response.send_message(
                "Ce bouton doit être utilisé dans un ticket.",
                ephemeral=True,
            )
            return

        owner_id = get_ticket_owner_id(interaction.channel)
        if owner_id is None:
            await interaction.response.send_message(
                "Ce salon n'est pas reconnu comme un ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message("Fermeture du ticket...", ephemeral=True)
        await interaction.channel.delete(reason=f"Ticket fermé par {interaction.user}")


class LotteryView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Participer",
        style=discord.ButtonStyle.success,
        custom_id="lottery:join",
    )
    async def join_lottery(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not await ensure_not_in_prison(interaction):
            return
        if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
            await interaction.response.send_message(
                "Cette interaction doit être utilisée dans le serveur.",
                ephemeral=True,
            )
            return

        state = load_lottery_state()
        message_id = state.get("message_id")
        if not isinstance(message_id, int) or interaction.message is None or interaction.message.id != message_id:
            await interaction.response.send_message(
                "Cette loterie n'est plus active.",
                ephemeral=True,
            )
            return

        ends_at = get_lottery_end_time(state)
        if ends_at is None:
            await interaction.response.send_message(
                "La loterie n'est pas configurée correctement.",
                ephemeral=True,
            )
            return

        if ends_at <= datetime.now(timezone.utc):
            await interaction.response.send_message(
                "Le tirage est en cours. Reessaie dans un instant.",
                ephemeral=True,
            )
            return

        ensure_minimum_balance(interaction.user.id)
        participants = get_lottery_participants(state)
        if interaction.user.id in participants:
            await interaction.response.send_message(
                "Tu participes déjà à cette loterie.",
                ephemeral=True,
            )
            return

        balance_value = get_balance_value(interaction.user.id)
        if balance_value < LOTTERY_ENTRY_COST:
            await interaction.response.send_message(
                f"Tu n'as pas assez d'argent. Il faut **{LOTTERY_ENTRY_COST} Sukushi Dollars** pour participer.",
                ephemeral=True,
            )
            return

        set_balance_value(interaction.user.id, balance_value - LOTTERY_ENTRY_COST)
        record_economy_stat("lottery_entry", -LOTTERY_ENTRY_COST)
        participants.append(interaction.user.id)
        state["participants"] = participants
        save_lottery_state(state)

        await interaction.response.edit_message(
            embed=build_lottery_embed(
                ends_at=ends_at,
                participants_count=len(participants),
            ),
            view=self,
        )
        await interaction.followup.send(
            (
                f"Ta participation est validée pour **{LOTTERY_ENTRY_COST} Sukushi Dollars**.\n"
                f"Bonne chance {interaction.user.mention}."
            ),
            ephemeral=True,
        )


class PrisonMemoryStartView(discord.ui.View):
    def __init__(self) -> None:
        super().__init__(timeout=None)

    @discord.ui.button(
        label="Commencer",
        style=discord.ButtonStyle.danger,
        custom_id="prison:memory_start",
    )
    async def start_button(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ) -> None:
        if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
            await interaction.response.send_message(
                "Cette interaction doit être utilisée dans le serveur.",
                ephemeral=True,
            )
            return

        prisoner_id = get_prisoner_id_from_channel(interaction.channel)
        if prisoner_id != interaction.user.id:
            await interaction.response.send_message(
                "Ce bouton n'est pas pour toi.",
                ephemeral=True,
            )
            return

        bot_client = interaction.client
        if not isinstance(bot_client, SukushiBot):
            await interaction.response.send_message(
                "Impossible de démarrer cette épreuve pour le moment.",
                ephemeral=True,
            )
            return

        started = await bot_client.start_memory_prison_challenge(interaction)
        if not started and not interaction.response.is_done():
            await interaction.response.send_message(
                "Cette épreuve a déjà commencé ou n'est plus disponible.",
                ephemeral=True,
            )


class SukushiBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tempban_tasks: dict[tuple[int, int], asyncio.Task[None]] = {}
        self.lottery_task: asyncio.Task[None] | None = None
        self.random_event_task: asyncio.Task[None] | None = None
        self.next_auto_event_at: datetime | None = None
        self.restored_tempbans = False

    async def setup_hook(self) -> None:
        guild = discord.Object(id=PRIMARY_GUILD_ID)
        self.add_view(TicketOpenView())
        self.add_view(TicketCloseView())
        self.add_view(LotteryView())
        self.add_view(PrisonMemoryStartView())
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to primary guild {PRIMARY_GUILD_ID}.")

    async def on_ready(self) -> None:
        if self.user is None:
            return
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        if self.random_event_task is None or self.random_event_task.done():
            self.random_event_task = asyncio.create_task(self.run_random_event_loop())
        if not self.restored_tempbans:
            await self.restore_tempbans()
            self.restored_tempbans = True
        await self.seed_existing_member_balances()
        await self.restore_prison_challenges()
        await self.restore_lottery()
        now = datetime.now(timezone.utc)
        if self.next_auto_event_at is None:
            self.next_auto_event_at = now + EVENT_INTERVAL
        print("Slash commands are synced and ready.")

    async def seed_existing_member_balances(self) -> None:
        meta = load_economy_meta()
        seeded_guilds = set(meta.get("seeded_guilds", []))
        guild_key = str(PRIMARY_GUILD_ID)
        if guild_key in seeded_guilds:
            return

        guild = self.get_guild(PRIMARY_GUILD_ID)
        if guild is None:
            return

        if not self.intents.members:
            print("Skipping balance seeding: members intent is disabled in code.", flush=True)
            return

        try:
            await asyncio.wait_for(guild.chunk(), timeout=15)
        except discord.HTTPException as error:
            print(f"Skipping balance seeding: unable to chunk guild members ({error}).", flush=True)
            return
        except asyncio.TimeoutError:
            print("Skipping balance seeding: guild chunk timed out.", flush=True)
            return
        except Exception as error:
            print(f"Skipping balance seeding: unexpected chunk error ({error}).", flush=True)
            return
        economy_data = load_economy()
        changed = False
        for member in guild.members:
            key = str(member.id)
            if key not in economy_data:
                economy_data[key] = STARTING_BALANCE
                changed = True

        if changed:
            save_economy(economy_data)

        seeded_guilds.add(guild_key)
        save_economy_meta({"seeded_guilds": sorted(seeded_guilds)})
        print(f"Starter balance granted for guild {guild.name} ({guild.id}).")

    async def get_or_create_prison_category(self, guild: discord.Guild) -> discord.CategoryChannel | None:
        existing = discord.utils.get(guild.categories, name=JAIL_CATEGORY_NAME)
        if existing is not None:
            return existing

        try:
            return await guild.create_category(JAIL_CATEGORY_NAME, reason="Création de la catégorie prison")
        except discord.HTTPException:
            return None

    async def get_or_create_prison_channel(self, member: discord.Member) -> discord.TextChannel | None:
        existing_channel = find_prison_channel(member.guild, member.id)
        if existing_channel is not None:
            return existing_channel

        category = await self.get_or_create_prison_category(member.guild)
        staff_role = get_role_by_id(member.guild, TICKET_STAFF_ROLE_ID)
        bot_member = get_bot_member(member.guild, self.user)

        overwrites: dict[discord.abc.Snowflake, discord.PermissionOverwrite] = {
            member.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            member: discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
            ),
        }
        if staff_role is not None:
            overwrites[staff_role] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_messages=True,
            )
        if bot_member is not None:
            overwrites[bot_member] = discord.PermissionOverwrite(
                view_channel=True,
                send_messages=True,
                read_message_history=True,
                manage_channels=True,
                manage_messages=True,
            )

        try:
            return await member.guild.create_text_channel(
                name=make_prison_channel_name(member.display_name, member.id),
                category=category,
                overwrites=overwrites,
                topic=make_prison_topic(member.id),
                reason=f"Création de la cellule de prison pour {member}",
            )
        except discord.HTTPException:
            return None

    async def send_prison_challenge(
        self,
        member: discord.Member,
        *,
        reason: str,
        penalty_text: str | None = None,
        variant: str | None = None,
    ) -> dict[str, object] | None:
        channel = await self.get_or_create_prison_channel(member)
        if channel is None:
            return None

        previous_record = get_prison_record(member.id)
        jailed_at = datetime.now(timezone.utc).isoformat()
        attempts = 0
        stored_variant = "normal"
        tax_amount = 0
        if previous_record is not None:
            previous_jailed_at = previous_record.get("jailed_at")
            if isinstance(previous_jailed_at, str):
                jailed_at = previous_jailed_at
            try:
                attempts = int(previous_record.get("attempts", 0))
            except (TypeError, ValueError):
                attempts = 0
            stored_variant = str(previous_record.get("variant") or "normal")
            try:
                tax_amount = int(previous_record.get("tax_amount", 0))
            except (TypeError, ValueError):
                tax_amount = 0

        if variant is None:
            variant = stored_variant if previous_record is not None else choose_prison_variant()

        if variant not in JAIL_VARIANTS:
            variant = "normal"

        challenge = (
            generate_memory_prison_challenge()
            if variant == "memory"
            else generate_prison_challenge()
        )
        sent_at = datetime.now(timezone.utc).isoformat() if variant != "memory" else None
        record = set_prison_record(
            member.id,
            {
                "jailed_at": jailed_at,
                "reason": reason,
                "channel_id": channel.id,
                "challenge": challenge,
                "challenge_sent_at": sent_at,
                "attempts": attempts + 1,
                "variant": variant,
                "tax_amount": tax_amount,
                "prompt_message_id": previous_record.get("prompt_message_id") if previous_record else None,
            },
        )

        description = (
            f"{member.mention}, tu es en prison pour **{reason}**.\n"
            "Regarde l'image ci-dessous et retape exactement le code dans ce salon.\n"
            "Respecte parfaitement les majuscules et les minuscules."
        )
        view: discord.ui.View | None = None
        challenge_file: discord.File | None = None

        if variant == "memory":
            description = (
                f"{member.mention}, tu es en prison pour **{reason}**.\n"
                "Appuie sur **Commencer** pour afficher le code pendant quelques secondes, puis retape-le de mémoire dans ce salon.\n"
                "Respecte parfaitement les majuscules et les minuscules."
            )
            view = PrisonMemoryStartView()
        else:
            challenge_file = build_prison_challenge_file(challenge)

        embed = make_embed(
            "Test de sortie de prison",
            description,
            color=discord.Color.red(),
            footer="Sukushi bot | Prison",
        )
        if challenge_file is not None:
            embed.set_image(url="attachment://prison-code.png")
        if variant == "memory":
            embed.add_field(name="Variante", value="Mémoire inversée", inline=False)
        elif variant == "tax":
            embed.add_field(name="Variante", value="Taxe de cellule", inline=False)
        if variant == "tax" and tax_amount > 0:
            embed.add_field(name="Taxe payée", value=f"**{tax_amount} Sukushi Dollars**", inline=False)
        if penalty_text:
            embed.add_field(name="Sanction", value=penalty_text, inline=False)

        if challenge_file is not None:
            prompt_message = await channel.send(content=member.mention, embed=embed, file=challenge_file)
        else:
            prompt_message = await channel.send(content=member.mention, embed=embed, view=view)

        record["prompt_message_id"] = prompt_message.id
        record = set_prison_record(member.id, record)
        return record

    async def send_member_to_prison(self, member: discord.Member, *, reason: str) -> dict[str, object] | None:
        variant = choose_prison_variant()
        tax_amount = 0
        if variant == "tax":
            current_balance = ensure_minimum_balance(member.id)
            tax_amount = compute_percentage_penalty(
                current_balance,
                random.uniform(*JAIL_TAX_PERCENT_RANGE),
            )
            new_balance = set_balance_value(member.id, current_balance - tax_amount)
            del new_balance
            record_economy_stat("prison_tax", -tax_amount)

        imprison_user(member.id, reason=reason)
        set_prison_record(
            member.id,
            {
                "jailed_at": datetime.now(timezone.utc).isoformat(),
                "reason": reason,
                "channel_id": None,
                "challenge": "",
                "challenge_sent_at": None,
                "attempts": 0,
                "variant": variant,
                "tax_amount": tax_amount,
                "prompt_message_id": None,
            },
        )
        penalty_text = None
        if variant == "tax" and tax_amount > 0:
            penalty_text = f"Taxe de cellule prélevée : **{tax_amount} Sukushi Dollars**."
        return await self.send_prison_challenge(member, reason=reason, penalty_text=penalty_text, variant=variant)

    async def hide_memory_prison_challenge(self, channel: discord.TextChannel, message_id: int, user_id: int) -> None:
        try:
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            return

        record = get_prison_record(user_id)
        if record is None or record.get("prompt_message_id") != message_id:
            return

        try:
            message = await channel.fetch_message(message_id)
        except (discord.NotFound, discord.HTTPException):
            return

        embed = make_embed(
            "Test de sortie de prison",
            (
                f"<@{user_id}>, l'image a disparu.\n"
                "Retape maintenant le code de mémoire dans ce salon en respectant parfaitement les majuscules et les minuscules."
            ),
            color=discord.Color.red(),
            footer="Sukushi bot | Prison",
        )
        embed.add_field(name="Variante", value="Mémoire inversée", inline=False)
        try:
            await message.edit(embed=embed, attachments=[], view=None)
        except discord.HTTPException:
            return

    async def start_memory_prison_challenge(self, interaction: discord.Interaction) -> bool:
        if not isinstance(interaction.user, discord.Member) or not isinstance(interaction.channel, discord.TextChannel):
            return False

        record = get_prison_record(interaction.user.id)
        if record is None or record.get("variant") != "memory":
            return False
        if record.get("challenge_sent_at") is not None:
            return False

        challenge = record.get("challenge")
        if not isinstance(challenge, str) or not challenge:
            return False

        sent_at = datetime.now(timezone.utc).isoformat()
        record["challenge_sent_at"] = sent_at
        record["prompt_message_id"] = interaction.message.id if interaction.message is not None else record.get("prompt_message_id")
        set_prison_record(interaction.user.id, record)

        embed = make_embed(
            "Test de sortie de prison",
            (
                f"{interaction.user.mention}, mémorise le code affiché.\n"
                "Tu devras le retaper dans quelques secondes."
            ),
            color=discord.Color.red(),
            footer="Sukushi bot | Prison",
        )
        embed.set_image(url="attachment://prison-code.png")
        embed.add_field(name="Variante", value="Mémoire inversée", inline=False)
        challenge_file = build_prison_challenge_file(challenge)
        await interaction.response.edit_message(embed=embed, attachments=[challenge_file], view=None)

        if interaction.message is not None:
            asyncio.create_task(
                self.hide_memory_prison_challenge(interaction.channel, interaction.message.id, interaction.user.id)
            )
        return True

    async def delete_prison_channel_later(self, channel: discord.TextChannel, delay: float = 10.0) -> None:
        try:
            await asyncio.sleep(delay)
            await channel.delete(reason="Défi de prison terminé")
        except (asyncio.CancelledError, discord.HTTPException):
            return

    async def handle_prison_message(self, message: discord.Message) -> bool:
        record = get_prison_record(message.author.id)
        if record is None:
            return False
        if not isinstance(message.author, discord.Member):
            return False

        channel_id = record.get("channel_id")
        if not isinstance(channel_id, int) or message.channel.id != channel_id:
            return False

        challenge = record.get("challenge")
        if not isinstance(challenge, str) or not challenge:
            await self.send_prison_challenge(
                message.author,
                reason=str(record.get("reason") or "raison inconnue"),
            )
            return True
        if record.get("variant") == "memory" and record.get("challenge_sent_at") is None:
            await message.channel.send(
                f"{message.author.mention} appuie d'abord sur **Commencer** pour lancer l'épreuve."
            )
            return True

        attempt = message.content.strip()
        if attempt != challenge:
            current_balance = ensure_minimum_balance(message.author.id)
            penalty_amount = compute_percentage_penalty(current_balance, JAIL_FAILURE_PERCENT)
            new_balance = set_balance_value(message.author.id, current_balance - penalty_amount)
            record_economy_stat("prison_fail", -penalty_amount)
            await message.channel.send(
                (
                    f"{message.author.mention} code incorrect.\n"
                    f"Tu perds **{penalty_amount} Sukushi Dollars** et une nouvelle épreuve commence.\n"
                    f"Nouveau solde : **{new_balance} Sukushi Dollars**."
                )
            )
            await self.send_prison_challenge(
                message.author,
                reason=str(record.get("reason") or "raison inconnue"),
                penalty_text=f"Échec précédent : -**{penalty_amount} Sukushi Dollars**.",
                variant=str(record.get("variant") or "normal"),
            )
            return True

        sent_at_raw = record.get("challenge_sent_at")
        sent_at = datetime.now(timezone.utc)
        if isinstance(sent_at_raw, str):
            try:
                sent_at = datetime.fromisoformat(sent_at_raw)
            except ValueError:
                sent_at = datetime.now(timezone.utc)

        elapsed = (datetime.now(timezone.utc) - sent_at).total_seconds()
        if elapsed < JAIL_MIN_SOLVE_SECONDS:
            current_balance = ensure_minimum_balance(message.author.id)
            new_balance = set_balance_value(message.author.id, current_balance // 2)
            record_economy_stat("prison_cheat", -(current_balance - new_balance))
            await message.channel.send(
                (
                    f"{message.author.mention} triche détectée : copier-coller suspect.\n"
                    f"Tu perds **{current_balance - new_balance} Sukushi Dollars** et tu dois recommencer."
                )
            )
            await self.send_prison_challenge(
                message.author,
                reason=str(record.get("reason") or "raison inconnue"),
                penalty_text=f"Perte de 50% de l'argent. Nouveau solde : **{new_balance} Sukushi Dollars**.",
            )
            return True

        remove_prison_record(message.author.id)
        embed = make_embed(
            "Libération",
            (
                f"{message.author.mention} a retapé le code correctement et sort de prison.\n"
                "Tu peux de nouveau utiliser les commandes économiques."
            ),
            color=discord.Color.green(),
            footer="Sukushi bot | Prison",
        )
        await message.channel.send(embed=embed)
        asyncio.create_task(self.delete_prison_channel_later(message.channel))
        return True

    async def restore_prison_challenges(self) -> None:
        guild = self.get_guild(PRIMARY_GUILD_ID)
        if guild is None:
            return

        for user_id, record in get_all_prison_records():
            member = guild.get_member(user_id)
            if member is None:
                try:
                    member = await guild.fetch_member(user_id)
                except discord.NotFound:
                    remove_prison_record(user_id)
                    continue
                except discord.HTTPException:
                    continue

            channel_id = record.get("channel_id")
            challenge = record.get("challenge")
            channel = guild.get_channel(channel_id) if isinstance(channel_id, int) else None
            if not isinstance(channel, discord.TextChannel) or not isinstance(challenge, str) or not challenge:
                await self.send_prison_challenge(
                    member,
                    reason=str(record.get("reason") or "raison inconnue"),
                    variant=str(record.get("variant") or "normal"),
                )

    async def get_event_channel(self) -> discord.TextChannel | None:
        channel = self.get_channel(EVENT_CHANNEL_ID)
        if isinstance(channel, discord.TextChannel):
            return channel
        try:
            fetched_channel = await self.fetch_channel(EVENT_CHANNEL_ID)
        except discord.HTTPException:
            return None
        return fetched_channel if isinstance(fetched_channel, discord.TextChannel) else None

    def get_active_event_state(self) -> dict[str, object] | None:
        state = load_event_state()
        event_type = state.get("type")
        if event_type not in EVENT_TYPES:
            return None
        created_at_raw = state.get("created_at")
        if not isinstance(created_at_raw, str):
            save_event_state({})
            return None
        try:
            created_at = datetime.fromisoformat(created_at_raw)
        except ValueError:
            save_event_state({})
            return None
        if created_at + EVENT_TIMEOUT <= datetime.now(timezone.utc):
            save_event_state({})
            return None
        answer = state.get("answer")
        if event_type == "guess_number":
            if not isinstance(answer, int):
                try:
                    answer = int(answer)
                except (TypeError, ValueError):
                    save_event_state({})
                    return None
                state["answer"] = answer
        else:
            if not isinstance(answer, str):
                save_event_state({})
                return None
        guesses = state.get("guesses")
        if not isinstance(guesses, dict):
            state["guesses"] = {}
        warned_users = state.get("warned_users")
        if not isinstance(warned_users, list):
            state["warned_users"] = []
        return state

    async def create_event_message(
        self,
        *,
        event_type: str,
        answer: int | str,
        embed: discord.Embed,
        file: discord.File | None = None,
    ) -> tuple[bool, str]:
        current_state = self.get_active_event_state()
        if current_state is not None:
            return False, "Un événement est déjà en cours dans le salon."

        channel = await self.get_event_channel()
        if channel is None:
            return False, "Le salon des événements est introuvable."

        if file is None:
            message = await channel.send(content=f"<@&{LOTTERY_PING_ROLE_ID}>", embed=embed)
        else:
            message = await channel.send(content=f"<@&{LOTTERY_PING_ROLE_ID}>", embed=embed, file=file)
        save_event_state(
            {
                "type": event_type,
                "answer": answer,
                "message_id": message.id,
                "channel_id": channel.id,
                "created_at": datetime.now(timezone.utc).isoformat(),
                "guesses": {},
                "warned_users": [],
            }
        )
        asyncio.create_task(self.expire_event_later(message.id))
        return True, f"L'événement a été lancé dans {channel.mention}."

    async def start_guess_number_event(self, *, forced: bool = False) -> tuple[bool, str]:
        answer = random.randint(EVENT_GUESS_MIN, EVENT_GUESS_MAX)
        embed = build_guess_number_event_embed(
            message="Événement forcé par le staff." if forced else None
        )
        return await self.create_event_message(
            event_type="guess_number",
            answer=answer,
            embed=embed,
        )

    async def start_fast_string_event(self, *, forced: bool = False) -> tuple[bool, str]:
        challenge_text = generate_fast_string_event_text()
        embed = build_fast_string_event_embed(
            message="Événement forcé par le staff." if forced else None,
        )
        return await self.create_event_message(
            event_type="fast_string",
            answer=challenge_text,
            embed=embed,
            file=build_event_string_file(challenge_text),
        )

    async def start_quick_math_event(self, *, forced: bool = False) -> tuple[bool, str]:
        problem_text, answer = generate_quick_math_event()
        embed = build_quick_math_event_embed(
            problem_text,
            message="Événement forcé par le staff." if forced else None,
        )
        return await self.create_event_message(
            event_type="quick_math",
            answer=answer,
            embed=embed,
        )

    async def start_random_event(self, *, forced: bool = False) -> tuple[bool, str]:
        event_type = random.choice(EVENT_TYPES)
        if event_type == "fast_string":
            return await self.start_fast_string_event(forced=forced)
        if event_type == "quick_math":
            return await self.start_quick_math_event(forced=forced)
        return await self.start_guess_number_event(forced=forced)

    async def finish_event(self, winner: discord.Member, *, win_text: str) -> bool:
        state = self.get_active_event_state()
        if state is None:
            return False

        reward_total = add_balance(winner.id, EVENT_GUESS_REWARD)
        record_economy_stat("event_win", EVENT_GUESS_REWARD)
        save_event_state({})

        channel = await self.get_event_channel()
        if channel is None:
            return True

        embed = make_embed(
            "Événement terminé",
            (
                f"{winner.mention} {win_text}\n"
                f"Récompense : **{EVENT_GUESS_REWARD} Sukushi Dollars**.\n"
                f"Nouveau solde : **{reward_total} Sukushi Dollars**."
            ),
            color=discord.Color.green(),
            footer="Sukushi bot | Événement",
        )
        await channel.send(embed=embed)
        return True

    async def clear_active_event(self, *, announce: bool = False, reason_text: str | None = None) -> bool:
        state = load_event_state()
        event_type = state.get("type")
        if event_type not in EVENT_TYPES:
            save_event_state({})
            return False

        channel = await self.get_event_channel()
        event_message: discord.Message | None = None
        message_id = state.get("message_id")
        if channel is not None and isinstance(message_id, int):
            try:
                event_message = await channel.fetch_message(message_id)
            except (discord.NotFound, discord.HTTPException):
                event_message = None

        save_event_state({})
        if not announce:
            return True

        if channel is None:
            return True

        if event_message is not None:
            expired_embed = make_embed(
                "Événement expiré",
                reason_text or "L'événement a expiré.",
                color=discord.Color.red(),
                footer="Sukushi bot | Événement",
            )
            try:
                await event_message.edit(content=None, embed=expired_embed, attachments=[], view=None)
            except discord.HTTPException:
                event_message = None

        embed = make_embed(
            "Événement expiré",
            reason_text or "L'événement a été fermé.",
            color=discord.Color.red(),
            footer="Sukushi bot | Événement",
        )
        expiry_message = await channel.send(embed=embed)
        asyncio.create_task(self.delete_event_messages_later(event_message, expiry_message))
        return True

    async def expire_event_later(self, message_id: int) -> None:
        try:
            await asyncio.sleep(EVENT_TIMEOUT.total_seconds())
        except asyncio.CancelledError:
            return

        state = load_event_state()
        if state.get("message_id") != message_id:
            return

        await self.clear_active_event(
            announce=True,
            reason_text=(
                f"Personne n'a trouvé la bonne réponse dans les **{int(EVENT_TIMEOUT.total_seconds())} secondes**."
            ),
        )

    async def delete_event_messages_later(
        self,
        event_message: discord.Message | None,
        expiry_message: discord.Message | None,
        delay: float = 5.0,
    ) -> None:
        try:
            await asyncio.sleep(delay)
        except asyncio.CancelledError:
            return

        for message in (event_message, expiry_message):
            if message is None:
                continue
            try:
                await message.delete()
            except (discord.NotFound, discord.HTTPException):
                continue

    def consume_numeric_event_attempt(self, state: dict[str, object], user_id: int) -> bool:
        guesses = state.get("guesses")
        if not isinstance(guesses, dict):
            guesses = {}

        guess_key = str(user_id)
        used_guesses = guesses.get(guess_key, 0)
        try:
            used_guesses = int(used_guesses)
        except (TypeError, ValueError):
            used_guesses = 0

        if used_guesses >= EVENT_MAX_GUESSES_PER_USER:
            return False

        guesses[guess_key] = used_guesses + 1
        state["guesses"] = guesses
        save_event_state(state)
        return True

    async def warn_event_attempts_exhausted(self, message: discord.Message, state: dict[str, object]) -> None:
        warned_users = state.get("warned_users")
        if not isinstance(warned_users, list):
            warned_users = []

        user_key = str(message.author.id)
        if user_key in warned_users:
            return

        warned_users.append(user_key)
        state["warned_users"] = warned_users
        save_event_state(state)
        await message.reply(
            f"tu as déjà utilisé tes **{EVENT_MAX_GUESSES_PER_USER}** tentatives pour cet événement.",
            mention_author=False,
        )

    async def handle_event_message(self, message: discord.Message) -> bool:
        if message.channel.id != EVENT_CHANNEL_ID or not isinstance(message.author, discord.Member):
            return False

        state = self.get_active_event_state()
        if state is None:
            return False

        content = message.content.strip()
        event_type = str(state.get("type"))
        normalized_content = content

        if event_type == "guess_number":
            if not normalized_content.isdigit():
                return False
            if not self.consume_numeric_event_attempt(state, message.author.id):
                await self.warn_event_attempts_exhausted(message, state)
                return True
            answer = state.get("answer")
            if int(normalized_content) != answer:
                return False
            await self.finish_event(message.author, win_text="a trouvé le bon nombre en premier.")
            return True

        if event_type == "fast_string":
            answer = state.get("answer")
            if normalized_content != answer:
                return False
            await self.finish_event(message.author, win_text="a retapé la chaîne en premier.")
            return True

        if event_type == "quick_math":
            if not re.fullmatch(r"-?\d+", normalized_content):
                return False
            if not self.consume_numeric_event_attempt(state, message.author.id):
                await self.warn_event_attempts_exhausted(message, state)
                return True
            answer = state.get("answer")
            if normalized_content != answer:
                return False
            await self.finish_event(message.author, win_text="a résolu le calcul en premier.")
            return True

        return False

    async def run_random_event_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(EVENT_LOOP_POLL_INTERVAL)
                try:
                    if self.next_auto_event_at is None:
                        self.next_auto_event_at = datetime.now(timezone.utc) + EVENT_INTERVAL
                        continue

                    now = datetime.now(timezone.utc)
                    if now < self.next_auto_event_at:
                        continue

                    success, message = await self.start_random_event()
                    if success:
                        self.next_auto_event_at = now + EVENT_INTERVAL
                    else:
                        active_state = self.get_active_event_state()
                        if active_state is None:
                            self.next_auto_event_at = now + timedelta(minutes=1)
                except Exception as error:
                    print(f"Random event loop error: {error}")
        except asyncio.CancelledError:
            return

    async def restore_tempbans(self) -> None:
        tempbans = load_tempbans()
        now = datetime.now(timezone.utc)

        for entry in tempbans.values():
            guild_id = int(entry["guild_id"])
            user_id = int(entry["user_id"])
            unban_at = datetime.fromisoformat(entry["unban_at"])
            reason = entry.get("reason") or None

            if unban_at <= now:
                await self.execute_persistent_unban(guild_id, user_id, reason)
                continue

            task_key = (guild_id, user_id)
            duration = unban_at - now
            self.tempban_tasks[task_key] = asyncio.create_task(
                self.schedule_tempban_unban(guild_id, user_id, duration, reason)
            )

        print(f"Restored {len(self.tempban_tasks)} persistent tempban task(s).")

    async def restore_lottery(self) -> None:
        state = load_lottery_state()
        message_id = state.get("message_id")
        ends_at = get_lottery_end_time(state)
        if not isinstance(message_id, int) or ends_at is None:
            return

        await self.schedule_lottery_draw(ends_at)

    async def schedule_lottery_draw(self, ends_at: datetime) -> None:
        if self.lottery_task is not None:
            self.lottery_task.cancel()

        async def runner(expected_end_at: datetime) -> None:
            try:
                delay = max(0.0, (expected_end_at - datetime.now(timezone.utc)).total_seconds())
                await asyncio.sleep(delay)
                await self.finish_lottery_round(expected_end_at)
            except asyncio.CancelledError:
                return
            finally:
                if asyncio.current_task() is self.lottery_task:
                    self.lottery_task = None

        self.lottery_task = asyncio.create_task(runner(ends_at))

    async def get_lottery_channel(self) -> discord.TextChannel | None:
        channel = self.get_channel(LOTTERY_CHANNEL_ID)
        return channel if isinstance(channel, discord.TextChannel) else None

    async def update_lottery_panel_message(self, state: dict[str, object]) -> None:
        channel = await self.get_lottery_channel()
        message_id = state.get("message_id")
        ends_at = get_lottery_end_time(state)
        if channel is None or not isinstance(message_id, int) or ends_at is None:
            return

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return

        await message.edit(
            embed=build_lottery_embed(
                ends_at=ends_at,
                participants_count=len(get_lottery_participants(state)),
            ),
            view=LotteryView(),
        )

    async def finish_lottery_round(self, expected_end_at: datetime) -> None:
        state = load_lottery_state()
        ends_at = get_lottery_end_time(state)
        message_id = state.get("message_id")
        if ends_at is None or ends_at != expected_end_at or not isinstance(message_id, int):
            return

        channel = await self.get_lottery_channel()
        if channel is None:
            return

        participants = get_lottery_participants(state)
        if participants:
            winner_id = random.choice(participants)
            new_balance = add_balance(winner_id, LOTTERY_PRIZE)
            record_economy_stat("lottery_win", LOTTERY_PRIZE)
            await channel.send(
                (
                    f"La loterie est terminée. Bravo <@{winner_id}> !\n"
                    f"Tu remportes **{LOTTERY_PRIZE} Sukushi Dollars**.\n"
                    f"Nouveau solde : **{new_balance} Sukushi Dollars**."
                )
            )
        else:
            await channel.send(
                "La loterie est terminée, mais personne n'a participé cette fois-ci."
            )

        next_end_at = datetime.now(timezone.utc) + LOTTERY_DURATION
        next_state: dict[str, object] = {
            "message_id": message_id,
            "participants": [],
            "ends_at": next_end_at.isoformat(),
        }
        save_lottery_state(next_state)
        await self.update_lottery_panel_message(next_state)
        await channel.send(build_lottery_start_message())
        await self.schedule_lottery_draw(next_end_at)

    async def execute_persistent_unban(
        self,
        guild_id: int,
        user_id: int,
        reason: str | None,
    ) -> None:
        guild = self.get_guild(guild_id)
        if guild is None:
            try:
                guild = await self.fetch_guild(guild_id)
            except discord.HTTPException:
                return

        try:
            await guild.unban(
                discord.Object(id=user_id),
                reason=f"Tempban expiré : {reason or 'Aucune raison fournie'}",
            )
        except (discord.Forbidden, discord.NotFound):
            pass
        finally:
            remove_tempban(guild_id, user_id)

    async def on_member_join(self, member: discord.Member) -> None:
        ensure_minimum_balance(member.id)
        join_role = get_role_by_id(member.guild, JOIN_ROLE_ID)
        if join_role is not None:
            try:
                await member.add_roles(join_role, reason="Automatic join role")
            except discord.Forbidden:
                print(f"Could not assign join role {JOIN_ROLE_ID} to {member}.")

        channel = self.get_channel(WELCOME_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            print(f"Welcome channel {WELCOME_CHANNEL_ID} not found or is not a text channel.")
            return

        flower_emoji = get_custom_emoji_text(member.guild, "emoji_3")
        embed = make_embed(
            f"{flower_emoji} Bienvenue sur Sukushi",
            (
                f"{member.mention}, bienvenue sur le serveur.\n"
                "Prends le temps de lire le règlement, pose-toi tranquillement "
                "et profite de l'ambiance."
            ),
            color=SUKUSHI_PINK,
            footer="Sukushi bot | Message de bienvenue",
        )
        embed.add_field(name="Membre", value=member.mention, inline=True)
        embed.add_field(
            name="Nous sommes",
            value=f"`{member.guild.member_count}` membres",
            inline=True,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed)

    async def on_member_remove(self, member: discord.Member) -> None:
        channel = self.get_channel(GOODBYE_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            print(f"Goodbye channel {GOODBYE_CHANNEL_ID} not found or is not a text channel.")
            return

        flower_emoji = get_custom_emoji_text(member.guild, "emoji_3")
        embed = make_embed(
            f"{flower_emoji} Au revoir",
            (
                f"**{member.display_name}** a quitté le serveur.\n"
                "On lui souhaite une bonne continuation."
            ),
            color=SUKUSHI_PINK,
            footer="Sukushi bot | Message de départ",
        )
        embed.add_field(name="Membre", value=f"`{member}`", inline=True)
        embed.add_field(
            name="Nous sommes",
            value=f"`{member.guild.member_count}` membres",
            inline=True,
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.set_image(url=BANNER_URL)
        await channel.send(embed=embed)

    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or message.guild is None:
            return
        if not isinstance(message.author, discord.Member):
            return
        if await self.handle_prison_message(message):
            return
        if await self.handle_event_message(message):
            return

        ensure_minimum_balance(message.author.id)
        gained_xp = random.randint(*LEVEL_XP_GAIN)
        new_level, levels_gained = apply_message_xp(
            message.author.id,
            gained_xp,
            cooldown=LEVEL_XP_COOLDOWN,
        )
        if levels_gained <= 0:
            return

        reward_total = LEVEL_REWARD * levels_gained
        new_balance = add_balance(message.author.id, reward_total)
        record_economy_stat("level_up", reward_total)
        channel = self.get_channel(LEVELUP_CHANNEL_ID)
        if not isinstance(channel, discord.TextChannel):
            return

        profile = get_level_profile(message.author.id)
        xp_needed = xp_needed_for_next_level(int(profile["level"]))
        embed = make_embed(
            "Niveau superieur",
            (
                f"{message.author.mention} vient de passer au **niveau {new_level}**.\n"
                f"Récompense : **{reward_total} Sukushi Dollars**.\n"
                f"Progression actuelle : **{profile['xp']}/{xp_needed} XP**."
            ),
            color=discord.Color.gold(),
            footer="Sukushi bot | Niveaux",
        )
        embed.add_field(name="Nouveau solde", value=f"**{new_balance} Sukushi Dollars**", inline=False)
        await channel.send(content=message.author.mention, embed=embed)

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent) -> None:
        await self.handle_autorole_reaction(payload, add_role=True)

    async def on_raw_reaction_remove(
        self,
        payload: discord.RawReactionActionEvent,
    ) -> None:
        await self.handle_autorole_reaction(payload, add_role=False)

    async def handle_autorole_reaction(
        self,
        payload: discord.RawReactionActionEvent,
        *,
        add_role: bool,
    ) -> None:
        if payload.channel_id != AUTOROLE_CHANNEL_ID or payload.guild_id is None:
            return
        if self.user is not None and payload.user_id == self.user.id:
            return

        emoji_name = payload.emoji.name
        if emoji_name not in AUTOROLE_MAP:
            return

        guild = self.get_guild(payload.guild_id)
        if guild is None:
            return

        channel = guild.get_channel(payload.channel_id)
        if not isinstance(channel, discord.TextChannel):
            return

        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if self.user is None or message.author.id != self.user.id:
            return
        if not message.embeds:
            return

        footer_text = message.embeds[0].footer.text if message.embeds[0].footer else None
        if footer_text != AUTOROLE_FOOTER:
            return

        role = get_role_by_id(guild, AUTOROLE_MAP[emoji_name])
        if role is None:
            return

        member = guild.get_member(payload.user_id)
        if member is None:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                return

        if add_role:
            exclusive_group = get_autorole_exclusive_group(role.id)
            if exclusive_group is not None:
                roles_to_remove = [
                    existing_role
                    for existing_role in member.roles
                    if existing_role.id in exclusive_group and existing_role.id != role.id
                ]
                if roles_to_remove:
                    await member.remove_roles(
                        *roles_to_remove,
                        reason="Autorole category swap",
                    )
            await member.add_roles(role, reason="Autorole reaction")
        else:
            await member.remove_roles(role, reason="Autorole reaction removed")

    async def schedule_tempban_unban(
        self,
        guild_id: int,
        user_id: int,
        duration: timedelta,
        reason: str | None,
    ) -> None:
        try:
            await asyncio.sleep(duration.total_seconds())
            await self.execute_persistent_unban(guild_id, user_id, reason)
        finally:
            self.tempban_tasks.pop((guild_id, user_id), None)


bot = SukushiBot()


@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError,
) -> None:
    if interaction.response.is_done():
        return

    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "Vous n'avez pas les permissions nécessaires pour cette commande.",
            ephemeral=True,
        )
        return

    if isinstance(error, app_commands.BotMissingPermissions):
        await interaction.response.send_message(
            "Il me manque des permissions Discord pour exécuter cette commande.",
            ephemeral=True,
        )
        return

    if isinstance(error, app_commands.CommandInvokeError) and error.original:
        await interaction.response.send_message(
            f"Erreur : {error.original}",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        "Une erreur est survenue pendant l'exécution de la commande.",
        ephemeral=True,
    )


async def run_balance_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    amount = get_balance_value(interaction.user.id)
    embed = make_embed(
        "Balance",
        f"{interaction.user.mention} possède **{amount} Sukushi Dollars**.",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Économie",
    )
    await interaction.response.send_message(embed=embed)


async def run_pay_action(
    interaction: discord.Interaction,
    cible: discord.Member,
    montant: int,
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
            ephemeral=True,
        )
        return

    payer = interaction.user
    if cible.id == payer.id:
        await interaction.response.send_message(
            "Tu ne peux pas te payer toi-même.",
            ephemeral=True,
        )
        return

    if cible.bot:
        await interaction.response.send_message(
            "Tu ne peux pas payer un bot.",
            ephemeral=True,
        )
        return

    ensure_minimum_balance(payer.id)
    ensure_minimum_balance(cible.id)

    payer_balance = get_balance_value(payer.id)
    if montant > payer_balance:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{payer_balance} Sukushi Dollars**.",
            ephemeral=True,
        )
        return

    new_payer_balance = set_balance_value(payer.id, payer_balance - montant)
    new_target_balance = add_balance(cible.id, montant)
    embed = make_embed(
        "Paiement envoyé",
        (
            f"{payer.mention} a envoyé **{montant} Sukushi Dollars** à {cible.mention}.\n"
            f"Ton nouveau solde : **{new_payer_balance} Sukushi Dollars**.\n"
            f"Nouveau solde de la cible : **{new_target_balance} Sukushi Dollars**."
        ),
        color=discord.Color.green(),
        footer="Sukushi bot | Économie",
    )
    await interaction.response.send_message(content=cible.mention, embed=embed)


async def run_leaderboard_action(interaction: discord.Interaction) -> None:
    top_balances = get_top_balances(10)
    if not top_balances:
        await interaction.response.send_message(
            "Aucune donnée économique disponible pour le moment.",
            ephemeral=True,
        )
        return

    lines: list[str] = []
    for index, (user_id, amount) in enumerate(top_balances, start=1):
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        user_label = member.mention if member else f"<@{user_id}>"
        lines.append(f"**{index}.** {user_label} — **{amount} Sukushi Dollars**")

    embed = make_embed(
        "Leaderboard",
        "\n".join(lines),
        color=discord.Color.gold(),
        footer="Sukushi bot | Richesse",
    )
    await interaction.response.send_message(embed=embed)


async def run_daily_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    remaining = get_cooldown_remaining(DAILY_FILE, interaction.user.id, DAILY_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Ton `/daily` est en cooldown pendant encore **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return

    update_cooldown(DAILY_FILE, interaction.user.id)
    new_balance = add_balance(interaction.user.id, DAILY_REWARD)
    record_economy_stat("daily", DAILY_REWARD)
    embed = make_embed(
        "Daily récupéré",
        (
            f"Tu as reçu **{DAILY_REWARD} Sukushi Dollars**.\n"
            f"Nouveau solde : **{new_balance} Sukushi Dollars**."
        ),
        color=discord.Color.gold(),
        footer="Sukushi bot | Daily",
    )
    await interaction.response.send_message(embed=embed)


async def run_getjob_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    current_job = get_job(interaction.user.id)
    if current_job is not None:
        await interaction.response.send_message(
            f"Tu travailles déjà comme **{JOB_OPTIONS.get(current_job, current_job)}**.",
            ephemeral=True,
        )
        return

    view = JobSelectView(interaction.user)
    embed = make_embed(
        "Choisis ton métier criminel",
        (
            "Choisis un métier avec soin.\n"
            "Il est permanent pour le moment, donc il n'y a aucun moyen d'en changer pour l'instant."
        ),
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Métiers",
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def run_changejob_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    current_job = get_job(interaction.user.id)
    if current_job is None:
        await interaction.response.send_message(
            "Tu n'as pas encore de métier. Utilise `/getjob` d'abord.",
            ephemeral=True,
        )
        return

    remaining = get_cooldown_remaining(CHANGEJOB_FILE, interaction.user.id, CHANGEJOB_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu pourras rechanger de métier dans **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return

    view = JobSelectView(interaction.user, allow_change=True)
    embed = make_embed(
        "Changer de métier",
        (
            f"Métier actuel : **{JOB_OPTIONS.get(current_job, current_job)}**\n"
            "Choisis ton nouveau métier. Tu ne pourras plus en changer avant 24h."
        ),
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Métiers",
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def run_work_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    job_key = get_job(interaction.user.id)
    if job_key is None:
        await interaction.response.send_message(
            "Tu n'as pas encore de métier. Utilise `/getjob` d'abord.",
            ephemeral=True,
        )
        return

    remaining = get_cooldown_remaining(WORK_FILE, interaction.user.id, WORK_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu as déjà travaillé aujourd'hui. Cooldown restant : **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return

    view = WorkMinigameView(interaction.user, job_key)
    await interaction.response.send_message(embed=view.build_embed(), view=view)
    view.message = await interaction.original_response()


async def run_attack_action(
    interaction: discord.Interaction,
    cible: discord.Member,
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
            ephemeral=True,
        )
        return

    attacker = interaction.user
    if cible.id == attacker.id:
        await interaction.response.send_message(
            "Tu ne peux pas t'attaquer toi-même.",
            ephemeral=True,
        )
        return

    if cible.bot:
        await interaction.response.send_message(
            "Tu ne peux pas attaquer un bot.",
            ephemeral=True,
        )
        return

    attacker_faction = get_faction_for_member(attacker.id)
    target_faction = get_faction_for_member(cible.id)
    if attacker_faction is not None and target_faction is not None:
        attacker_owner_id, _ = attacker_faction
        target_owner_id, _ = target_faction
        if attacker_owner_id == target_owner_id:
            await interaction.response.send_message(
                "Tu ne peux pas attaquer un membre de ta propre faction.",
                ephemeral=True,
            )
            return
        if factions_are_allied(attacker_owner_id, target_owner_id):
            await interaction.response.send_message(
                "Tu ne peux pas attaquer un membre d'une faction alliée.",
                ephemeral=True,
            )
            return

    attacker_faction = get_faction_for_member(attacker.id)
    target_faction = get_faction_for_member(cible.id)
    if attacker_faction is not None and target_faction is not None:
        attacker_owner_id, _ = attacker_faction
        target_owner_id, _ = target_faction
        if attacker_owner_id == target_owner_id:
            await interaction.response.send_message(
                "Tu ne peux pas attaquer un membre de ta propre faction.",
                ephemeral=True,
            )
            return
        if factions_are_allied(attacker_owner_id, target_owner_id):
            await interaction.response.send_message(
                "Tu ne peux pas attaquer un membre d'une faction alliée.",
                ephemeral=True,
            )
            return
    if attacker.id in ACTIVE_ATTACK_USERS or cible.id in ACTIVE_ATTACK_USERS:
        await interaction.response.send_message(
            "Un de ces joueurs est déjà dans un combat. Attends la fin du duel en cours.",
            ephemeral=True,
        )
        return

    if is_in_prison(cible.id):
        await interaction.response.send_message(
            f"{cible.mention} est déjà en prison et doit finir son épreuve avant de pouvoir rejouer.",
            ephemeral=True,
        )
        return

    ensure_minimum_balance(attacker.id)
    ensure_minimum_balance(cible.id)

    global_cooldown_remaining = get_cooldown_remaining(
        ATTACK_FILE,
        attacker.id,
        GLOBAL_ATTACK_COOLDOWN,
    )
    if global_cooldown_remaining is not None:
        await interaction.response.send_message(
            f"Tu dois attendre **{format_remaining_time(global_cooldown_remaining)}** avant de relancer une attaque.",
            ephemeral=True,
        )
        return

    cooldown_remaining = get_pair_cooldown_remaining(
        ATTACK_FILE,
        attacker.id,
        cible.id,
        ATTACK_COOLDOWN,
    )
    if cooldown_remaining is not None:
        await interaction.response.send_message(
            f"Tu dois attendre **{format_remaining_time(cooldown_remaining)}** avant de réattaquer {cible.mention}.",
            ephemeral=True,
        )
        return

    if get_balance_value(attacker.id) <= 0 and get_balance_value(cible.id) <= 0:
        await interaction.response.send_message(
            "Aucun de vous deux n'a assez d'argent pour que cette attaque serve à quelque chose.",
            ephemeral=True,
        )
        return

    update_cooldown(ATTACK_FILE, attacker.id)
    ACTIVE_ATTACK_USERS.add(attacker.id)
    ACTIVE_ATTACK_USERS.add(cible.id)
    view = AttackView(attacker, cible)
    await interaction.response.send_message(
        content=cible.mention,
        embed=view.build_embed(),
        view=view,
    )
    view.message = await interaction.original_response()


async def run_blackjack_action(
    interaction: discord.Interaction,
    mise: int,
) -> None:
    ensure_minimum_balance(interaction.user.id)
    balance_value = get_balance_value(interaction.user.id)
    if mise > balance_value:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{balance_value} Sukushi Dollars**.",
            ephemeral=True,
        )
        return

    view = BlackjackView(interaction.user, mise)
    await view.start_game(interaction)


async def ensure_panel_access(interaction: discord.Interaction) -> bool:
    if not await ensure_not_in_prison(interaction):
        return False
    if not await ensure_not_ecobanned(interaction):
        return False
    return True


def build_panel_embed() -> discord.Embed:
    embed = make_embed(
        "Panel Économie",
        "Choisis une action ci-dessous pour gérer ton aventure Sukushi sans spammer les commandes.",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Panel",
    )
    embed.add_field(name="Infos rapides", value="`Solde`  `Daily`  `Classement`", inline=False)
    embed.add_field(name="Actions", value="`Travail`  `Blackjack`  `Slots`  `Mines`  `Payer`  `Attaquer`", inline=False)
    embed.add_field(name="Métier", value="`Choisir`  `Changer`", inline=False)
    return embed


class OwnerRestrictedView(discord.ui.View):
    def __init__(self, owner_id: int, *, timeout: float = 300) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Ce panel n'est pas pour toi.", ephemeral=True)
            return False
        return True


class AttackTargetSelect(discord.ui.UserSelect):
    def __init__(self, owner_id: int) -> None:
        super().__init__(placeholder="Choisis la cible à attaquer", min_values=1, max_values=1)
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        target = self.values[0]
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("Impossible de récupérer ce membre.", ephemeral=True)
            return
        await run_attack_action(interaction, target)


class AttackTargetView(OwnerRestrictedView):
    def __init__(self, owner_id: int) -> None:
        super().__init__(owner_id, timeout=120)
        self.add_item(AttackTargetSelect(owner_id))


class PayAmountModal(discord.ui.Modal, title="Envoyer de l'argent"):
    montant = discord.ui.TextInput(label="Montant", placeholder="Ex: 2500", required=True, max_length=7)

    def __init__(self, target: discord.Member) -> None:
        super().__init__()
        self.target = target

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        raw_value = str(self.montant).strip()
        if not raw_value.isdigit():
            await interaction.response.send_message("Le montant doit être un nombre entier positif.", ephemeral=True)
            return
        amount = int(raw_value)
        if amount <= 0:
            await interaction.response.send_message("Le montant doit être supérieur à 0.", ephemeral=True)
            return
        await run_pay_action(interaction, self.target, amount)


class PayTargetSelect(discord.ui.UserSelect):
    def __init__(self, owner_id: int) -> None:
        super().__init__(placeholder="Choisis la personne à payer", min_values=1, max_values=1)
        self.owner_id = owner_id

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        target = self.values[0]
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("Impossible de récupérer ce membre.", ephemeral=True)
            return
        await interaction.response.send_modal(PayAmountModal(target))


class PayTargetView(OwnerRestrictedView):
    def __init__(self, owner_id: int) -> None:
        super().__init__(owner_id, timeout=120)
        self.add_item(PayTargetSelect(owner_id))


class BlackjackBetModal(discord.ui.Modal, title="Lancer une partie de blackjack"):
    mise = discord.ui.TextInput(label="Mise", placeholder="Ex: 500", required=True, max_length=7)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        raw_value = str(self.mise).strip()
        if not raw_value.isdigit():
            await interaction.response.send_message("La mise doit être un nombre entier positif.", ephemeral=True)
            return
        amount = int(raw_value)
        if amount <= 0:
            await interaction.response.send_message("La mise doit être supérieure à 0.", ephemeral=True)
            return
        await run_blackjack_action(interaction, amount)


class PanelView(OwnerRestrictedView):
    def __init__(self, owner_id: int) -> None:
        super().__init__(owner_id)

    @discord.ui.button(label="Solde", style=discord.ButtonStyle.secondary, emoji="💰", row=0)
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_balance_action(interaction)

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.success, emoji="🪙", row=0)
    async def daily_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_daily_action(interaction)

    @discord.ui.button(label="Classement", style=discord.ButtonStyle.secondary, emoji="🏆", row=0)
    async def leaderboard_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_leaderboard_action(interaction)

    @discord.ui.button(label="Travail", style=discord.ButtonStyle.primary, emoji="💼", row=1)
    async def work_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_work_action(interaction)

    @discord.ui.button(label="Blackjack", style=discord.ButtonStyle.primary, emoji="🃏", row=1)
    async def blackjack_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_modal(BlackjackBetModal())

    @discord.ui.button(label="Payer", style=discord.ButtonStyle.primary, emoji="💸", row=1)
    async def pay_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_message(
            "Choisis la personne à payer.",
            ephemeral=True,
            view=PayTargetView(self.owner_id),
        )

    @discord.ui.button(label="Attaquer", style=discord.ButtonStyle.danger, emoji="⚔️", row=2)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_message(
            "Choisis la cible à attaquer.",
            ephemeral=True,
            view=AttackTargetView(self.owner_id),
        )

    @discord.ui.button(label="Choisir métier", style=discord.ButtonStyle.secondary, emoji="🕵️", row=2)
    async def getjob_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_getjob_action(interaction)

    @discord.ui.button(label="Changer métier", style=discord.ButtonStyle.secondary, emoji="🔁", row=2)
    async def changejob_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_changejob_action(interaction)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.secondary, emoji="✖️", row=3)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.edit_message(content="Panel fermé.", embed=None, view=None)


@bot.tree.command(name="ping", description="Check if sukushi bot is online.")
async def ping(interaction: discord.Interaction) -> None:
    latency_ms = round(bot.latency * 1000)
    embed = make_embed(
        "Pong !",
        f"sukushi bot est en ligne.\nLatence de la gateway : `{latency_ms}ms`",
        color=discord.Color.green(),
        footer=f"Demandé par {interaction.user.display_name}",
    )
    await interaction.response.send_message(embed=embed)


async def run_balance_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    amount = get_balance_value(interaction.user.id)
    embed = make_embed(
        "Balance",
        f"{interaction.user.mention} possède **{amount} Sukushi Dollars**.",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Économie",
    )
    await interaction.response.send_message(embed=embed)


async def run_pay_action(interaction: discord.Interaction, cible: discord.Member, montant: int) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Cette commande doit être utilisée dans le serveur.", ephemeral=True)
        return
    payer = interaction.user
    if cible.id == payer.id:
        await interaction.response.send_message("Tu ne peux pas te payer toi-même.", ephemeral=True)
        return
    if cible.bot:
        await interaction.response.send_message("Tu ne peux pas payer un bot.", ephemeral=True)
        return
    ensure_minimum_balance(payer.id)
    ensure_minimum_balance(cible.id)
    payer_balance = get_balance_value(payer.id)
    if montant > payer_balance:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{payer_balance} Sukushi Dollars**.",
            ephemeral=True,
        )
        return
    new_payer_balance = set_balance_value(payer.id, payer_balance - montant)
    new_target_balance = add_balance(cible.id, montant)
    embed = make_embed(
        "Paiement envoyé",
        (
            f"{payer.mention} a envoyé **{montant} Sukushi Dollars** à {cible.mention}.\n"
            f"Ton nouveau solde : **{new_payer_balance} Sukushi Dollars**.\n"
            f"Nouveau solde de la cible : **{new_target_balance} Sukushi Dollars**."
        ),
        color=discord.Color.green(),
        footer="Sukushi bot | Économie",
    )
    await interaction.response.send_message(content=cible.mention, embed=embed)


async def run_leaderboard_action(interaction: discord.Interaction) -> None:
    top_balances = get_top_balances(10)
    if not top_balances:
        await interaction.response.send_message("Aucune donnée économique disponible pour le moment.", ephemeral=True)
        return
    lines: list[str] = []
    for index, (user_id, amount) in enumerate(top_balances, start=1):
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        user_label = member.mention if member else f"<@{user_id}>"
        lines.append(f"**{index}.** {user_label} - **{amount} Sukushi Dollars**")
    embed = make_embed("Leaderboard", "\n".join(lines), color=discord.Color.gold(), footer="Sukushi bot | Richesse")
    await interaction.response.send_message(embed=embed)


async def run_level_leaderboard_action(interaction: discord.Interaction) -> None:
    top_levels = get_top_levels(10)
    if not top_levels:
        await interaction.response.send_message(
            "Aucune donnee de niveau disponible pour le moment.",
            ephemeral=True,
        )
        return

    lines: list[str] = []
    for index, (user_id, level, xp) in enumerate(top_levels, start=1):
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        user_label = member.mention if member else f"<@{user_id}>"
        xp_needed = xp_needed_for_next_level(level)
        lines.append(f"**{index}.** {user_label} - **Niveau {level}** ({xp}/{xp_needed} XP)")

    embed = make_embed(
        "Classement des niveaux",
        "\n".join(lines),
        color=discord.Color.gold(),
        footer="Sukushi bot | Niveaux",
    )
    await interaction.response.send_message(embed=embed)


async def run_daily_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    remaining = get_cooldown_remaining(DAILY_FILE, interaction.user.id, DAILY_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Ton `/daily` est en cooldown pendant encore **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return
    update_cooldown(DAILY_FILE, interaction.user.id)
    new_balance = add_balance(interaction.user.id, DAILY_REWARD)
    embed = make_embed(
        "Daily récupéré",
        (
            f"Tu as reçu **{DAILY_REWARD} Sukushi Dollars**.\n"
            f"Nouveau solde : **{new_balance} Sukushi Dollars**."
        ),
        color=discord.Color.gold(),
        footer="Sukushi bot | Daily",
    )
    await interaction.response.send_message(embed=embed)


async def run_getjob_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    current_job = get_job(interaction.user.id)
    if current_job is not None:
        await interaction.response.send_message(
            f"Tu travailles déjà comme **{JOB_OPTIONS.get(current_job, current_job)}**.",
            ephemeral=True,
        )
        return
    view = JobSelectView(interaction.user)
    embed = make_embed(
        "Choisis ton métier criminel",
        "Choisis un métier avec soin.\nIl est permanent pour le moment.",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Métiers",
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def run_changejob_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    current_job = get_job(interaction.user.id)
    if current_job is None:
        await interaction.response.send_message("Tu n'as pas encore de métier. Utilise `/getjob` d'abord.", ephemeral=True)
        return
    remaining = get_cooldown_remaining(CHANGEJOB_FILE, interaction.user.id, CHANGEJOB_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu pourras rechanger de métier dans **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return
    view = JobSelectView(interaction.user, allow_change=True)
    embed = make_embed(
        "Changer de métier",
        (
            f"Métier actuel : **{JOB_OPTIONS.get(current_job, current_job)}**\n"
            "Choisis ton nouveau métier. Tu ne pourras plus en changer avant 24h."
        ),
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Métiers",
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


async def run_work_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    job_key = get_job(interaction.user.id)
    if job_key is None:
        await interaction.response.send_message("Tu n'as pas encore de métier. Utilise `/getjob` d'abord.", ephemeral=True)
        return
    remaining = get_cooldown_remaining(WORK_FILE, interaction.user.id, WORK_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu as déjà travaillé aujourd'hui. Cooldown restant : **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return
    view = WorkMinigameView(interaction.user, job_key)
    await interaction.response.send_message(embed=view.build_embed(), view=view)
    view.message = await interaction.original_response()


async def run_attack_action(interaction: discord.Interaction, cible: discord.Member) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message("Cette commande doit être utilisée dans le serveur.", ephemeral=True)
        return
    attacker = interaction.user
    if cible.id == attacker.id:
        await interaction.response.send_message("Tu ne peux pas t'attaquer toi-même.", ephemeral=True)
        return
    if cible.bot:
        await interaction.response.send_message("Tu ne peux pas attaquer un bot.", ephemeral=True)
        return
    attacker_faction = get_faction_for_member(attacker.id)
    target_faction = get_faction_for_member(cible.id)
    if attacker_faction is not None and target_faction is not None:
        attacker_owner_id, _ = attacker_faction
        target_owner_id, _ = target_faction
        if attacker_owner_id == target_owner_id:
            await interaction.response.send_message(
                "Tu ne peux pas attaquer un membre de ta propre faction.",
                ephemeral=True,
            )
            return
        if factions_are_allied(attacker_owner_id, target_owner_id):
            await interaction.response.send_message(
                "Tu ne peux pas attaquer un membre d'une faction alliée.",
                ephemeral=True,
            )
            return
    if attacker.id in ACTIVE_ATTACK_USERS or cible.id in ACTIVE_ATTACK_USERS:
        await interaction.response.send_message(
            "Un de ces joueurs est déjà dans un combat. Attends la fin du duel en cours.",
            ephemeral=True,
        )
        return
    if is_in_prison(cible.id):
        await interaction.response.send_message(
            f"{cible.mention} est déjà en prison et doit finir son épreuve avant de pouvoir rejouer.",
            ephemeral=True,
        )
        return
    ensure_minimum_balance(attacker.id)
    ensure_minimum_balance(cible.id)
    global_cooldown_remaining = get_cooldown_remaining(ATTACK_FILE, attacker.id, GLOBAL_ATTACK_COOLDOWN)
    if global_cooldown_remaining is not None:
        await interaction.response.send_message(
            f"Tu dois attendre **{format_remaining_time(global_cooldown_remaining)}** avant de relancer une attaque.",
            ephemeral=True,
        )
        return
    cooldown_remaining = get_pair_cooldown_remaining(ATTACK_FILE, attacker.id, cible.id, ATTACK_COOLDOWN)
    if cooldown_remaining is not None:
        await interaction.response.send_message(
            f"Tu dois attendre **{format_remaining_time(cooldown_remaining)}** avant de réattaquer {cible.mention}.",
            ephemeral=True,
        )
        return
    if get_balance_value(attacker.id) <= 0 and get_balance_value(cible.id) <= 0:
        await interaction.response.send_message(
            "Aucun de vous deux n'a assez d'argent pour que cette attaque serve à quelque chose.",
            ephemeral=True,
        )
        return
    update_cooldown(ATTACK_FILE, attacker.id)
    ACTIVE_ATTACK_USERS.add(attacker.id)
    ACTIVE_ATTACK_USERS.add(cible.id)
    view = AttackView(attacker, cible)
    await interaction.response.send_message(content=cible.mention, embed=view.build_embed(), view=view)
    view.message = await interaction.original_response()


async def run_blackjack_action(interaction: discord.Interaction, mise: int) -> None:
    ensure_minimum_balance(interaction.user.id)
    balance_value = get_balance_value(interaction.user.id)
    if mise > balance_value:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{balance_value} Sukushi Dollars**.",
            ephemeral=True,
        )
        return
    view = BlackjackView(interaction.user, mise)
    await view.start_game(interaction)


async def run_slots_action(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    remaining = get_cooldown_remaining(SLOTS_COOLDOWN_FILE, interaction.user.id, SLOTS_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu dois attendre **{format_remaining_time(remaining)}** avant de rejouer aux slots.",
            ephemeral=True,
        )
        return

    balance_value = get_balance_value(interaction.user.id)
    if balance_value < SLOTS_COST:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Il faut **{SLOTS_COST} Sukushi Dollars** pour jouer aux slots.",
            ephemeral=True,
        )
        return

    guild = interaction.guild
    slot_symbol = get_custom_emoji_text(guild, "slot", fallback="🎰")
    coin_symbol = get_custom_emoji_text(guild, "coinbag", fallback="🪙")
    miss_symbol = "✖️"

    update_cooldown(SLOTS_COOLDOWN_FILE, interaction.user.id)
    new_balance = set_balance_value(interaction.user.id, balance_value - SLOTS_COST)
    pot_amount = add_slots_pot(SLOTS_COST)
    record_economy_stat("slots_spin", -SLOTS_COST)

    await interaction.response.defer(thinking=True)

    spinning_embed = build_slots_embed(
        guild,
        title="Casino | Slots",
        symbols=[slot_symbol, slot_symbol, slot_symbol],
        description=(
            f"{interaction.user.mention} lance les rouleaux...\n"
            f"Entrée : **{SLOTS_COST} Sukushi Dollars**.\n"
            f"Ton solde après la mise : **{new_balance} Sukushi Dollars**."
        ),
        color=SUKUSHI_PINK,
        pot_amount=pot_amount,
    )
    await interaction.edit_original_response(embed=spinning_embed)

    await asyncio.sleep(1.1)
    mid_symbols = [random.choice((coin_symbol, miss_symbol)), slot_symbol, slot_symbol]
    await interaction.edit_original_response(
        embed=build_slots_embed(
            guild,
            title="Casino | Slots",
            symbols=mid_symbols,
            description="Les rouleaux ralentissent...",
            color=SUKUSHI_PINK,
            pot_amount=pot_amount,
        )
    )

    await asyncio.sleep(0.9)
    jackpot_hit = random.random() < SLOTS_JACKPOT_CHANCE
    final_symbols = [coin_symbol, coin_symbol, coin_symbol] if jackpot_hit else [miss_symbol, miss_symbol, miss_symbol]

    if jackpot_hit:
        winnings = pot_amount
        final_balance = add_balance(interaction.user.id, winnings)
        record_economy_stat("slots_jackpot", winnings)
        reset_pot_amount = reset_slots_pot()
        final_embed = build_slots_embed(
            guild,
            title="Casino | Jackpot !",
            symbols=final_symbols,
            description=(
                f"{interaction.user.mention} a touché le jackpot !\n"
                f"Tu remportes **{winnings} Sukushi Dollars**.\n"
                f"Ton nouveau solde : **{final_balance} Sukushi Dollars**."
            ),
            color=discord.Color.gold(),
            pot_amount=reset_pot_amount,
        )
    else:
        final_embed = build_slots_embed(
            guild,
            title="Casino | Raté",
            symbols=final_symbols,
            description=(
                f"{interaction.user.mention} n'a rien gagné cette fois.\n"
                f"Le pot continue de monter à **{pot_amount} Sukushi Dollars**.\n"
                f"Ton solde actuel : **{new_balance} Sukushi Dollars**."
            ),
            color=discord.Color.red(),
            pot_amount=pot_amount,
        )

    await interaction.edit_original_response(embed=final_embed)


async def run_mines_action(interaction: discord.Interaction, mise: int, bombes: int) -> None:
    if interaction.user.id in ACTIVE_MINES_USERS:
        await interaction.response.send_message(
            "Tu as déjà une partie de mines en cours.",
            ephemeral=True,
        )
        return

    ensure_minimum_balance(interaction.user.id)
    balance_value = get_balance_value(interaction.user.id)
    if mise > balance_value:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{balance_value} Sukushi Dollars**.",
            ephemeral=True,
        )
        return

    new_balance = set_balance_value(interaction.user.id, balance_value - mise)
    view = MinesView(interaction.user, mise, bombes, interaction.guild)
    ACTIVE_MINES_USERS.add(interaction.user.id)

    embed = build_mines_embed(
        interaction.guild,
        player=interaction.user,
        bet=mise,
        bombs=bombes,
        safe_revealed=0,
        multiplier=1.0,
        potential_cashout=mise,
        title="Casino | Mines",
        description=(
            "La grille est prête.\n"
            "Trouve les sacs de pièces, évite les bombes et récupère tes gains quand tu veux.\n"
            f"Le cashout se débloque à partir de **{MINES_MIN_CASHOUT_SAFE} cases sûres**.\n"
            f"Ton solde après la mise : **{new_balance} Sukushi Dollars**."
        ),
        color=SUKUSHI_PINK,
    )
    await interaction.response.send_message(embed=embed, view=view)
    view.message = await interaction.original_response()


async def ensure_panel_access(interaction: discord.Interaction) -> bool:
    if not await ensure_not_in_prison(interaction):
        return False
    if not await ensure_not_ecobanned(interaction):
        return False
    return True


def build_panel_embed() -> discord.Embed:
    embed = make_embed(
        "Play Hub",
        "Choisis une action ci-dessous pour gérer ton aventure Sukushi.",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Play",
    )
    embed.add_field(name="Infos", value="`Solde`  `Daily`  `Classement`", inline=False)
    embed.add_field(name="Actions", value="`Travail`  `Blackjack`  `Payer`  `Attaquer`", inline=False)
    embed.add_field(name="Métier", value="`Choisir`  `Changer`", inline=False)
    return embed


class OwnerRestrictedView(discord.ui.View):
    def __init__(self, owner_id: int, *, timeout: float = 300) -> None:
        super().__init__(timeout=timeout)
        self.owner_id = owner_id

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message("Ce panel n'est pas pour toi.", ephemeral=True)
            return False
        return True


class AttackTargetSelect(discord.ui.UserSelect):
    def __init__(self, owner_id: int) -> None:
        super().__init__(placeholder="Choisis la cible à attaquer", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        target = self.values[0]
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("Impossible de récupérer ce membre.", ephemeral=True)
            return
        await run_attack_action(interaction, target)


class AttackTargetView(OwnerRestrictedView):
    def __init__(self, owner_id: int) -> None:
        super().__init__(owner_id, timeout=120)
        self.add_item(AttackTargetSelect(owner_id))


class PayAmountModal(discord.ui.Modal, title="Envoyer de l'argent"):
    montant = discord.ui.TextInput(label="Montant", placeholder="Ex: 2500", required=True, max_length=7)

    def __init__(self, target: discord.Member) -> None:
        super().__init__()
        self.target = target

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        raw_value = str(self.montant).strip()
        if not raw_value.isdigit():
            await interaction.response.send_message("Le montant doit être un nombre entier positif.", ephemeral=True)
            return
        amount = int(raw_value)
        if amount <= 0:
            await interaction.response.send_message("Le montant doit être supérieur à 0.", ephemeral=True)
            return
        await run_pay_action(interaction, self.target, amount)


class PayTargetSelect(discord.ui.UserSelect):
    def __init__(self, owner_id: int) -> None:
        super().__init__(placeholder="Choisis la personne à payer", min_values=1, max_values=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        target = self.values[0]
        if not isinstance(target, discord.Member):
            await interaction.response.send_message("Impossible de récupérer ce membre.", ephemeral=True)
            return
        await interaction.response.send_modal(PayAmountModal(target))


class PayTargetView(OwnerRestrictedView):
    def __init__(self, owner_id: int) -> None:
        super().__init__(owner_id, timeout=120)
        self.add_item(PayTargetSelect(owner_id))


class BlackjackBetModal(discord.ui.Modal, title="Lancer une partie de blackjack"):
    mise = discord.ui.TextInput(label="Mise", placeholder="Ex: 500", required=True, max_length=7)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not await ensure_panel_access(interaction):
            return
        raw_value = str(self.mise).strip()
        if not raw_value.isdigit():
            await interaction.response.send_message("La mise doit être un nombre entier positif.", ephemeral=True)
            return
        amount = int(raw_value)
        if amount <= 0:
            await interaction.response.send_message("La mise doit être supérieure à 0.", ephemeral=True)
            return
        await run_blackjack_action(interaction, amount)


class PanelView(OwnerRestrictedView):
    def __init__(self, owner_id: int) -> None:
        super().__init__(owner_id)

    @discord.ui.button(label="Solde", style=discord.ButtonStyle.secondary, row=0)
    async def balance_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_balance_action(interaction)

    @discord.ui.button(label="Daily", style=discord.ButtonStyle.success, row=0)
    async def daily_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_daily_action(interaction)

    @discord.ui.button(label="Classement", style=discord.ButtonStyle.secondary, row=0)
    async def leaderboard_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_leaderboard_action(interaction)

    @discord.ui.button(label="Niveaux", style=discord.ButtonStyle.secondary, row=0)
    async def level_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_level_leaderboard_action(interaction)

    @discord.ui.button(label="Travail", style=discord.ButtonStyle.primary, row=1)
    async def work_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_work_action(interaction)

    @discord.ui.button(label="Blackjack", style=discord.ButtonStyle.primary, row=1)
    async def blackjack_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_modal(BlackjackBetModal())

    @discord.ui.button(label="Slots", style=discord.ButtonStyle.primary, row=1)
    async def slots_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_slots_action(interaction)

    @discord.ui.button(label="Mines", style=discord.ButtonStyle.primary, row=1)
    async def mines_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_message(
            "Utilise `/mines mise:<montant> bombes:<4-5>` pour lancer une partie de mines.",
            ephemeral=True,
        )

    @discord.ui.button(label="Payer", style=discord.ButtonStyle.primary, row=1)
    async def pay_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_message("Choisis la personne à payer.", ephemeral=True, view=PayTargetView(self.owner_id))

    @discord.ui.button(label="Attaquer", style=discord.ButtonStyle.danger, row=2)
    async def attack_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await interaction.response.send_message("Choisis la cible à attaquer.", ephemeral=True, view=AttackTargetView(self.owner_id))

    @discord.ui.button(label="Choisir métier", style=discord.ButtonStyle.secondary, row=2)
    async def getjob_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_getjob_action(interaction)

    @discord.ui.button(label="Changer métier", style=discord.ButtonStyle.secondary, row=2)
    async def changejob_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        if not await ensure_panel_access(interaction):
            return
        await run_changejob_action(interaction)

    @discord.ui.button(label="Fermer", style=discord.ButtonStyle.secondary, row=3)
    async def close_button(self, interaction: discord.Interaction, button: discord.ui.Button) -> None:
        self.stop()
        await interaction.response.edit_message(content="Play fermé.", embed=None, view=None)


@bot.tree.command(name="play", description="Ouvre le panel interactif de l'économie.")
@prison_block()
@economy_block()
async def play(interaction: discord.Interaction) -> None:
    await interaction.response.send_message(
        embed=build_panel_embed(),
        view=PanelView(interaction.user.id),
        ephemeral=True,
    )


@bot.tree.command(name="levelleaderboard", description="Affiche le classement des niveaux.")
@prison_block()
@economy_block()
async def levelleaderboard(interaction: discord.Interaction) -> None:
    await run_level_leaderboard_action(interaction)


@bot.tree.command(name="balance", description="Show your Sukushi Dollars balance.")
@prison_block()
@economy_block()
async def balance(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    amount = get_balance_value(interaction.user.id)
    embed = make_embed(
        "Balance",
        f"{interaction.user.mention} possède **{amount} Sukushi Dollars**.",
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Économie",
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="pay", description="Donne une partie de ton argent à un autre joueur.")
@prison_block()
@economy_block()
async def pay(
    interaction: discord.Interaction,
    cible: discord.Member,
    montant: app_commands.Range[int, 1, 1_000_000],
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
            ephemeral=True,
        )
        return

    payer = interaction.user
    if cible.id == payer.id:
        await interaction.response.send_message(
            "Tu ne peux pas te payer toi-même.",
            ephemeral=True,
        )
        return

    if cible.bot:
        await interaction.response.send_message(
            "Tu ne peux pas payer un bot.",
            ephemeral=True,
        )
        return

    ensure_minimum_balance(payer.id)
    ensure_minimum_balance(cible.id)

    payer_balance = get_balance_value(payer.id)
    if montant > payer_balance:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{payer_balance} Sukushi Dollars**.",
            ephemeral=True,
        )
        return

    new_payer_balance = set_balance_value(payer.id, payer_balance - montant)
    new_target_balance = add_balance(cible.id, montant)
    embed = make_embed(
        "Paiement envoyé",
        (
            f"{payer.mention} a envoyé **{montant} Sukushi Dollars** à {cible.mention}.\n"
            f"Ton nouveau solde : **{new_payer_balance} Sukushi Dollars**.\n"
            f"Nouveau solde de la cible : **{new_target_balance} Sukushi Dollars**."
        ),
        color=discord.Color.green(),
        footer="Sukushi bot | Économie",
    )
    await interaction.response.send_message(content=cible.mention, embed=embed)


@bot.tree.command(name="leaderboard", description="Show the richest users on the server.")
@prison_block()
@economy_block()
async def leaderboard(interaction: discord.Interaction) -> None:
    top_balances = get_top_balances(10)
    if not top_balances:
        await interaction.response.send_message(
            "Aucune donnée économique disponible pour le moment.",
            ephemeral=True,
        )
        return

    lines: list[str] = []
    for index, (user_id, amount) in enumerate(top_balances, start=1):
        member = interaction.guild.get_member(user_id) if interaction.guild else None
        user_label = member.mention if member else f"<@{user_id}>"
        lines.append(f"**{index}.** {user_label} — **{amount} Sukushi Dollars**")

    embed = make_embed(
        "Leaderboard",
        "\n".join(lines),
        color=discord.Color.gold(),
        footer="Sukushi bot | Richesse",
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="daily", description="Claim your daily Sukushi Dollars.")
@prison_block()
@economy_block()
async def daily(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    remaining = get_cooldown_remaining(DAILY_FILE, interaction.user.id, DAILY_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Ton `/daily` est en cooldown pendant encore **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return

    update_cooldown(DAILY_FILE, interaction.user.id)
    new_balance = add_balance(interaction.user.id, DAILY_REWARD)
    embed = make_embed(
        "Daily récupéré",
        (
            f"Tu as reçu **{DAILY_REWARD} Sukushi Dollars**.\n"
            f"Nouveau solde : **{new_balance} Sukushi Dollars**."
        ),
        color=discord.Color.gold(),
        footer="Sukushi bot | Daily",
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="getjob", description="Choose your permanent crime job.")
@prison_block()
@economy_block()
async def getjob(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    current_job = get_job(interaction.user.id)
    if current_job is not None:
        await interaction.response.send_message(
            f"Tu travailles déjà comme **{JOB_OPTIONS.get(current_job, current_job)}**.",
            ephemeral=True,
        )
        return

    view = JobSelectView(interaction.user)
    embed = make_embed(
        "Choisis ton métier criminel",
        (
            "Choisis un métier avec soin.\n"
            "Il est permanent pour le moment, donc il n'y a aucun moyen d'en changer pour l'instant."
        ),
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Métiers",
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="changejob", description="Change ton métier avec un cooldown de 24h.")
@prison_block()
@economy_block()
async def changejob(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    current_job = get_job(interaction.user.id)
    if current_job is None:
        await interaction.response.send_message(
            "Tu n'as pas encore de métier. Utilise `/getjob` d'abord.",
            ephemeral=True,
        )
        return

    remaining = get_cooldown_remaining(CHANGEJOB_FILE, interaction.user.id, CHANGEJOB_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu pourras rechanger de métier dans **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return

    view = JobSelectView(interaction.user, allow_change=True)
    embed = make_embed(
        "Changer de métier",
        (
            f"Métier actuel : **{JOB_OPTIONS.get(current_job, current_job)}**\n"
            "Choisis ton nouveau métier. Tu ne pourras plus en changer avant 24h."
        ),
        color=SUKUSHI_PINK,
        footer="Sukushi bot | Métiers",
    )
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)


@bot.tree.command(name="work", description="Do a crime job minigame for your daily pay.")
@prison_block()
@economy_block()
async def work(interaction: discord.Interaction) -> None:
    ensure_minimum_balance(interaction.user.id)
    job_key = get_job(interaction.user.id)
    if job_key is None:
        await interaction.response.send_message(
            "Tu n'as pas encore de métier. Utilise `/getjob` d'abord.",
            ephemeral=True,
        )
        return

    remaining = get_cooldown_remaining(WORK_FILE, interaction.user.id, WORK_COOLDOWN)
    if remaining is not None:
        await interaction.response.send_message(
            f"Tu as déjà travaillé aujourd'hui. Cooldown restant : **{format_remaining_time(remaining)}**.",
            ephemeral=True,
        )
        return

    view = WorkMinigameView(interaction.user, job_key)
    await interaction.response.send_message(embed=view.build_embed(), view=view)
    view.message = await interaction.original_response()


@bot.tree.command(name="attack", description="Attaque un autre joueur pour lui voler un peu d'argent.")
@prison_block()
@economy_block()
async def attack(
    interaction: discord.Interaction,
    cible: discord.Member,
) -> None:
    await run_attack_action(interaction, cible)


@bot.tree.command(name="blackjack", description="Joue une partie de blackjack.")
@prison_block()
@economy_block()
async def blackjack(
    interaction: discord.Interaction,
    mise: app_commands.Range[int, 1, 1_000_000],
) -> None:
    ensure_minimum_balance(interaction.user.id)
    balance_value = get_balance_value(interaction.user.id)
    if mise > balance_value:
        await interaction.response.send_message(
            f"Tu n'as pas assez d'argent. Solde actuel : **{balance_value} Sukushi Dollars**.",
            ephemeral=True,
        )
        return

    view = BlackjackView(interaction.user, mise)
    await view.start_game(interaction)


@bot.tree.command(name="slots", description="Lance les slots pour 100 Sukushi Dollars.")
@prison_block()
@economy_block()
async def slots(interaction: discord.Interaction) -> None:
    await run_slots_action(interaction)


@bot.tree.command(name="mines", description="Joue une partie de mines interactive.")
@prison_block()
@economy_block()
async def mines(
    interaction: discord.Interaction,
    mise: app_commands.Range[int, 100, 1_000_000],
    bombes: app_commands.Range[int, 4, 5],
) -> None:
    await run_mines_action(interaction, mise, bombes)


@bot.tree.command(name="createfaction", description="Crée ta propre faction.")
async def createfaction(
    interaction: discord.Interaction,
    nom: app_commands.Range[str, 1, 32],
) -> None:
    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    if get_faction_for_member(interaction.user.id) is not None:
        await interaction.response.send_message(
            "Tu fais déjà partie d'une faction.",
        )
        return

    faction_name = nom.strip()
    if not faction_name:
        await interaction.response.send_message(
            "Le nom de la faction ne peut pas être vide.",
        )
        return

    for _, faction in get_all_factions():
        existing_name = str(faction.get("name") or "")
        if existing_name.casefold() == faction_name.casefold():
            await interaction.response.send_message(
                "Une faction avec ce nom existe déjà.",
            )
            return

    state = load_faction_state()
    factions = state.setdefault("factions", {})
    if not isinstance(factions, dict):
        factions = {}
        state["factions"] = factions

    factions[str(interaction.user.id)] = {
        "name": faction_name,
        "tag": "",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "allies": [],
        "members": {
            str(interaction.user.id): {
                "joined_at": datetime.now(timezone.utc).isoformat(),
                "base_nick": interaction.user.nick,
            }
        },
    }
    save_faction_state(state)

    await interaction.response.send_message(
        (
            f"Ta faction **{faction_name}** a été créée.\n"
            "Utilise `/setfactiontag` pour définir un tag, puis `/invitefaction` pour recruter."
        ),
    )


@bot.tree.command(name="setfactiontag", description="Définit le tag de ta faction.")
async def setfactiontag(
    interaction: discord.Interaction,
    tag: str,
) -> None:
    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    faction = get_faction_by_owner(interaction.user.id)
    if faction is None:
        await interaction.response.send_message(
            "Tu dois être chef d'une faction pour définir un tag.",
        )
        return

    normalized_tag = normalize_faction_tag(tag)
    if not FACTION_TAG_PATTERN.fullmatch(normalized_tag):
        await interaction.response.send_message(
            "Le tag doit faire 1 à 4 caractères, sans espace, avec uniquement des lettres ou chiffres.",
        )
        return

    for owner_id, other_faction in get_all_factions():
        if owner_id == interaction.user.id:
            continue
        if normalize_faction_tag(str(other_faction.get("tag") or "")) == normalized_tag:
            await interaction.response.send_message(
                "Ce tag est déjà utilisé par une autre faction.",
            )
            return

    state = load_faction_state()
    factions = state.get("factions", {})
    if not isinstance(factions, dict):
        await interaction.response.send_message(
            "Impossible de mettre à jour la faction pour le moment.",
        )
        return

    faction_entry = factions.get(str(interaction.user.id))
    if not isinstance(faction_entry, dict):
        await interaction.response.send_message(
            "Faction introuvable.",
        )
        return

    old_tag = str(faction_entry.get("tag") or "")
    faction_entry["tag"] = normalized_tag
    save_faction_state(state)

    members = faction_entry.get("members", {})
    updated_members = 0
    failed_members = 0
    if isinstance(members, dict):
        for member_id, metadata in members.items():
            try:
                target_id = int(member_id)
            except ValueError:
                continue
            member = interaction.guild.get_member(target_id)
            if member is None:
                continue
            base_nick = metadata.get("base_nick") if isinstance(metadata, dict) else None
            success = await sync_member_faction_nickname(
                member,
                old_tag=old_tag or None,
                new_tag=normalized_tag,
                base_nick=base_nick if isinstance(base_nick, str) else None,
                reason=f"Tag de faction défini par {interaction.user}",
            )
            if success:
                updated_members += 1
            else:
                failed_members += 1

    note = ""
    if failed_members > 0:
        note = f"\n{failed_members} membre(s) n'ont pas pu être renommé(s) automatiquement."

    await interaction.response.send_message(
        (
            f"Le tag de la faction est maintenant **{normalized_tag}**.\n"
            f"Tags synchronisés pour **{updated_members}** membre(s).{note}"
        ),
    )


@bot.tree.command(name="invitefaction", description="Invite un membre dans ta faction.")
async def invitefaction(
    interaction: discord.Interaction,
    membre: discord.Member,
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    faction = get_faction_by_owner(interaction.user.id)
    if faction is None:
        await interaction.response.send_message(
            "Tu dois être chef d'une faction pour inviter quelqu'un.",
        )
        return

    if membre.bot:
        await interaction.response.send_message(
            "Tu ne peux pas inviter un bot.",
        )
        return

    if membre.id == interaction.user.id:
        await interaction.response.send_message(
            "Tu es déjà dans ta propre faction.",
        )
        return

    if get_faction_for_member(membre.id) is not None:
        await interaction.response.send_message(
            f"{membre.mention} fait déjà partie d'une faction.",
        )
        return

    set_faction_invite(membre.id, interaction.user.id)
    await interaction.response.send_message(
        (
            f"{membre.mention}, **{interaction.user.display_name}** t'invite à rejoindre la faction **{faction.get('name') or 'ta faction'}**.\n"
            "La personne doit utiliser `/joinfaction` pour accepter."
        ),
    )


@bot.tree.command(name="joinfaction", description="Accepte ton invitation de faction.")
async def joinfaction(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    if get_faction_for_member(interaction.user.id) is not None:
        await interaction.response.send_message(
            "Tu fais déjà partie d'une faction.",
        )
        return

    owner_id = get_faction_invite(interaction.user.id)
    if owner_id is None:
        await interaction.response.send_message(
            "Tu n'as aucune invitation de faction en attente.",
        )
        return

    state = load_faction_state()
    factions = state.get("factions", {})
    invites = state.get("invites", {})
    if not isinstance(factions, dict) or not isinstance(invites, dict):
        await interaction.response.send_message(
            "Impossible de rejoindre une faction pour le moment.",
        )
        return

    faction = factions.get(str(owner_id))
    if not isinstance(faction, dict):
        invites.pop(str(interaction.user.id), None)
        save_faction_state(state)
        await interaction.response.send_message(
            "Cette invitation n'est plus valide.",
        )
        return

    members = faction.get("members", {})
    if not isinstance(members, dict):
        members = {}
        faction["members"] = members

    members[str(interaction.user.id)] = {
        "joined_at": datetime.now(timezone.utc).isoformat(),
        "base_nick": interaction.user.nick,
    }
    invites.pop(str(interaction.user.id), None)
    save_faction_state(state)

    faction_tag = str(faction.get("tag") or "")
    nickname_note = ""
    if faction_tag:
        success = await sync_member_faction_nickname(
            interaction.user,
            new_tag=faction_tag,
            base_nick=interaction.user.nick,
            reason=f"Entrée dans la faction {faction.get('name') or owner_id}",
        )
        if not success:
            nickname_note = "\nLe tag n'a pas pu être appliqué automatiquement au pseudo."

    await interaction.response.send_message(
        f"Tu as rejoint la faction **{faction.get('name') or 'inconnue'}**.{nickname_note}",
    )


@bot.tree.command(name="leavefaction", description="Quitte ta faction actuelle.")
async def leavefaction(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    faction_info = get_faction_for_member(interaction.user.id)
    if faction_info is None:
        await interaction.response.send_message(
            "Tu ne fais partie d'aucune faction.",
        )
        return

    owner_id, faction = faction_info
    if owner_id == interaction.user.id:
        await interaction.response.send_message(
            "Le chef ne peut pas quitter sa faction. Utilise `/disbandfaction` à la place.",
        )
        return

    state = load_faction_state()
    factions = state.get("factions", {})
    if not isinstance(factions, dict):
        await interaction.response.send_message(
            "Impossible de quitter la faction pour le moment.",
        )
        return

    faction_entry = factions.get(str(owner_id))
    if not isinstance(faction_entry, dict):
        await interaction.response.send_message(
            "Faction introuvable.",
        )
        return

    members = faction_entry.get("members", {})
    if not isinstance(members, dict):
        members = {}
        faction_entry["members"] = members

    member_data = members.pop(str(interaction.user.id), None)
    save_faction_state(state)

    old_tag = str(faction_entry.get("tag") or "")
    base_nick = member_data.get("base_nick") if isinstance(member_data, dict) else None
    await sync_member_faction_nickname(
        interaction.user,
        old_tag=old_tag or None,
        new_tag=None,
        base_nick=base_nick if isinstance(base_nick, str) else None,
        reason=f"Départ de faction par {interaction.user}",
    )

    await interaction.response.send_message(
        f"Tu as quitté la faction **{faction_entry.get('name') or 'inconnue'}**.",
    )


@bot.tree.command(name="kickfaction", description="Retire un membre de ta faction.")
async def kickfaction(
    interaction: discord.Interaction,
    membre: discord.Member,
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    faction = get_faction_by_owner(interaction.user.id)
    if faction is None:
        await interaction.response.send_message(
            "Tu dois être chef d'une faction pour retirer un membre.",
        )
        return

    if membre.id == interaction.user.id:
        await interaction.response.send_message(
            "Utilise `/disbandfaction` si tu veux fermer ta faction.",
        )
        return

    target_faction = get_faction_for_member(membre.id)
    if target_faction is None or target_faction[0] != interaction.user.id:
        await interaction.response.send_message(
            f"{membre.mention} n'est pas dans ta faction.",
        )
        return

    state = load_faction_state()
    factions = state.get("factions", {})
    if not isinstance(factions, dict):
        await interaction.response.send_message(
            "Impossible de retirer ce membre pour le moment.",
        )
        return

    faction_entry = factions.get(str(interaction.user.id))
    if not isinstance(faction_entry, dict):
        await interaction.response.send_message(
            "Faction introuvable.",
        )
        return

    members = faction_entry.get("members", {})
    if not isinstance(members, dict):
        members = {}
        faction_entry["members"] = members

    member_data = members.pop(str(membre.id), None)
    save_faction_state(state)

    old_tag = str(faction_entry.get("tag") or "")
    base_nick = member_data.get("base_nick") if isinstance(member_data, dict) else None
    await sync_member_faction_nickname(
        membre,
        old_tag=old_tag or None,
        new_tag=None,
        base_nick=base_nick if isinstance(base_nick, str) else None,
        reason=f"Expulsion de faction par {interaction.user}",
    )

    await interaction.response.send_message(
        f"{membre.mention} a été retiré de la faction **{faction_entry.get('name') or 'inconnue'}**.",
    )


@bot.tree.command(name="disbandfaction", description="Dissout ta faction.")
async def disbandfaction(interaction: discord.Interaction) -> None:
    if not isinstance(interaction.user, discord.Member) or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    state = load_faction_state()
    factions = state.get("factions", {})
    invites = state.get("invites", {})
    if not isinstance(factions, dict) or not isinstance(invites, dict):
        await interaction.response.send_message(
            "Impossible de dissoudre la faction pour le moment.",
        )
        return

    faction = factions.pop(str(interaction.user.id), None)
    if not isinstance(faction, dict):
        await interaction.response.send_message(
            "Tu n'es chef d'aucune faction.",
        )
        return

    old_tag = str(faction.get("tag") or "")
    members = faction.get("members", {})
    if not isinstance(members, dict):
        members = {}
    allies = get_faction_allies(faction)

    for target_id, invited_owner_id in list(invites.items()):
        if invited_owner_id == str(interaction.user.id):
            invites.pop(target_id, None)

    ally_requests = state.get("ally_requests", {})
    if isinstance(ally_requests, dict):
        ally_requests.pop(str(interaction.user.id), None)
        for target_owner_id, requesters in list(ally_requests.items()):
            if isinstance(requesters, list):
                ally_requests[target_owner_id] = [requester for requester in requesters if requester != str(interaction.user.id)]

    for ally_owner_id in allies:
        other_faction = factions.get(str(ally_owner_id))
        if isinstance(other_faction, dict):
            other_allies = other_faction.get("allies", [])
            if isinstance(other_allies, list):
                other_faction["allies"] = [ally_id for ally_id in other_allies if ally_id != str(interaction.user.id)]

    save_faction_state(state)

    restored = 0
    failed = 0
    for member_id, metadata in members.items():
        try:
            target_id = int(member_id)
        except ValueError:
            continue
        member = interaction.guild.get_member(target_id)
        if member is None:
            continue
        base_nick = metadata.get("base_nick") if isinstance(metadata, dict) else None
        success = await sync_member_faction_nickname(
            member,
            old_tag=old_tag or None,
            new_tag=None,
            base_nick=base_nick if isinstance(base_nick, str) else None,
            reason=f"Faction dissoute par {interaction.user}",
        )
        if success:
            restored += 1
        else:
            failed += 1

    note = f"\n{failed} pseudo(s) n'ont pas pu être restauré(s)." if failed else ""
    await interaction.response.send_message(
        (
            f"La faction **{faction.get('name') or 'inconnue'}** a été dissoute.\n"
            f"Pseudo restauré pour **{restored}** membre(s).{note}"
        ),
    )


@bot.tree.command(name="faction", description="Affiche les informations de ta faction.")
async def faction(interaction: discord.Interaction) -> None:
    faction_info = get_faction_for_member(interaction.user.id)
    if faction_info is None:
        invite_owner_id = get_faction_invite(interaction.user.id)
        if invite_owner_id is not None:
            pending_faction = get_faction_by_owner(invite_owner_id)
            pending_name = str(pending_faction.get("name") or "inconnue") if pending_faction else "inconnue"
            await interaction.response.send_message(
                (
                    "Tu ne fais partie d'aucune faction.\n"
                    f"Invitation en attente : **{pending_name}**. Utilise `/joinfaction` pour accepter."
                ),
            )
            return

        await interaction.response.send_message(
            "Tu ne fais partie d'aucune faction.",
        )
        return

    owner_id, faction_data = faction_info
    await interaction.response.send_message(
        embed=build_faction_embed(interaction.guild, owner_id=owner_id, faction=faction_data),
    )


@bot.tree.command(name="ally", description="Envoie ou accepte une demande d'alliance via un tag de faction.")
async def ally(
    interaction: discord.Interaction,
    tag: str,
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    own_faction = get_faction_by_owner(interaction.user.id)
    if own_faction is None:
        await interaction.response.send_message(
            "Tu dois être chef d'une faction pour gérer les alliances.",
        )
        return

    target_info = get_faction_by_tag(tag)
    if target_info is None:
        await interaction.response.send_message(
            "Aucune faction ne correspond à ce tag.",
        )
        return

    target_owner_id, target_faction = target_info
    if target_owner_id == interaction.user.id:
        await interaction.response.send_message(
            "Tu ne peux pas t'allier avec ta propre faction.",
        )
        return

    if factions_are_allied(interaction.user.id, target_owner_id):
        await interaction.response.send_message(
            f"Ta faction est déjà alliée avec **{target_faction.get('name') or 'cette faction'}**.",
        )
        return

    state = load_faction_state()
    factions = state.get("factions", {})
    ally_requests = state.get("ally_requests", {})
    if not isinstance(factions, dict) or not isinstance(ally_requests, dict):
        await interaction.response.send_message(
            "Impossible de gérer les alliances pour le moment.",
        )
        return

    own_entry = factions.get(str(interaction.user.id))
    target_entry = factions.get(str(target_owner_id))
    if not isinstance(own_entry, dict) or not isinstance(target_entry, dict):
        await interaction.response.send_message(
            "Une des factions est introuvable.",
        )
        return

    incoming_requests = ally_requests.get(str(interaction.user.id), [])
    if not isinstance(incoming_requests, list):
        incoming_requests = []
        ally_requests[str(interaction.user.id)] = incoming_requests

    own_allies = own_entry.get("allies", [])
    target_allies = target_entry.get("allies", [])
    if not isinstance(own_allies, list):
        own_allies = []
        own_entry["allies"] = own_allies
    if not isinstance(target_allies, list):
        target_allies = []
        target_entry["allies"] = target_allies

    if str(target_owner_id) in incoming_requests:
        incoming_requests = [requester for requester in incoming_requests if requester != str(target_owner_id)]
        ally_requests[str(interaction.user.id)] = incoming_requests
        if str(target_owner_id) not in own_allies:
            own_allies.append(str(target_owner_id))
        if str(interaction.user.id) not in target_allies:
            target_allies.append(str(interaction.user.id))
        save_faction_state(state)
        await interaction.response.send_message(
            (
                f"Alliance confirmée entre **{own_entry.get('name') or 'ta faction'}** "
                f"et **{target_entry.get('name') or 'cette faction'}**."
            ),
        )
        return

    outgoing_requests = ally_requests.get(str(target_owner_id), [])
    if not isinstance(outgoing_requests, list):
        outgoing_requests = []
        ally_requests[str(target_owner_id)] = outgoing_requests

    if str(interaction.user.id) in outgoing_requests:
        await interaction.response.send_message(
            (
                f"Une demande d'alliance a déjà été envoyée à **{target_entry.get('name') or 'cette faction'}**.\n"
                "Le chef adverse doit utiliser `/ally <ton tag>` pour accepter."
            ),
        )
        return

    outgoing_requests.append(str(interaction.user.id))
    ally_requests[str(target_owner_id)] = outgoing_requests
    save_faction_state(state)
    await interaction.response.send_message(
        (
            f"Demande d'alliance envoyée à **{target_entry.get('name') or 'cette faction'}**.\n"
            f"Leur chef doit utiliser `/ally {own_entry.get('tag') or 'TAG'}` pour accepter."
        ),
    )


@bot.tree.command(name="disbandally", description="Met fin à une alliance avec une autre faction.")
async def disbandally(
    interaction: discord.Interaction,
    tag: str,
) -> None:
    if not isinstance(interaction.user, discord.Member):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    own_faction = get_faction_by_owner(interaction.user.id)
    if own_faction is None:
        await interaction.response.send_message(
            "Tu dois être chef d'une faction pour gérer les alliances.",
        )
        return

    target_info = get_faction_by_tag(tag)
    if target_info is None:
        await interaction.response.send_message(
            "Aucune faction ne correspond à ce tag.",
        )
        return

    target_owner_id, target_faction = target_info
    if target_owner_id == interaction.user.id:
        await interaction.response.send_message(
            "Tu ne peux pas casser une alliance avec ta propre faction.",
        )
        return

    state = load_faction_state()
    factions = state.get("factions", {})
    ally_requests = state.get("ally_requests", {})
    if not isinstance(factions, dict) or not isinstance(ally_requests, dict):
        await interaction.response.send_message(
            "Impossible de modifier les alliances pour le moment.",
        )
        return

    own_entry = factions.get(str(interaction.user.id))
    target_entry = factions.get(str(target_owner_id))
    if not isinstance(own_entry, dict) or not isinstance(target_entry, dict):
        await interaction.response.send_message(
            "Une des factions est introuvable.",
        )
        return

    own_allies = own_entry.get("allies", [])
    target_allies = target_entry.get("allies", [])
    if not isinstance(own_allies, list):
        own_allies = []
        own_entry["allies"] = own_allies
    if not isinstance(target_allies, list):
        target_allies = []
        target_entry["allies"] = target_allies

    had_alliance = str(target_owner_id) in own_allies or str(interaction.user.id) in target_allies
    own_entry["allies"] = [ally_id for ally_id in own_allies if ally_id != str(target_owner_id)]
    target_entry["allies"] = [ally_id for ally_id in target_allies if ally_id != str(interaction.user.id)]

    incoming = ally_requests.get(str(interaction.user.id), [])
    outgoing = ally_requests.get(str(target_owner_id), [])
    if isinstance(incoming, list):
        ally_requests[str(interaction.user.id)] = [requester for requester in incoming if requester != str(target_owner_id)]
    if isinstance(outgoing, list):
        ally_requests[str(target_owner_id)] = [requester for requester in outgoing if requester != str(interaction.user.id)]

    save_faction_state(state)

    if had_alliance:
        await interaction.response.send_message(
            f"L'alliance avec **{target_faction.get('name') or 'cette faction'}** a été rompue.",
        )
    else:
        await interaction.response.send_message(
            f"Aucune alliance active avec **{target_faction.get('name') or 'cette faction'}** n'a été trouvée.",
        )


@bot.tree.command(name="fleaderboard", description="Affiche le classement des factions.")
async def fleaderboard(interaction: discord.Interaction) -> None:
    factions = get_all_factions()
    if not factions:
        await interaction.response.send_message(
            "Aucune faction n'existe pour le moment.",
        )
        return

    economy_data = load_economy()
    ranked_factions: list[tuple[int, dict[str, object], int, int]] = []
    for owner_id, faction in factions:
        members = faction.get("members", {})
        if not isinstance(members, dict):
            continue

        member_ids: list[int] = []
        total_money = 0
        for member_id in members.keys():
            try:
                parsed_member_id = int(member_id)
            except ValueError:
                continue
            member_ids.append(parsed_member_id)
            total_money += int(economy_data.get(str(parsed_member_id), 0))

        ranked_factions.append((owner_id, faction, len(member_ids), total_money))

    ranked_factions.sort(key=lambda item: item[3], reverse=True)

    lines: list[str] = []
    for index, (_, faction, member_count, total_money) in enumerate(ranked_factions[:10], start=1):
        name = str(faction.get("name") or "Faction inconnue")
        tag = str(faction.get("tag") or "-")
        lines.append(
            f"**{index}.** {name} | Tag: **{tag}** | Membres: **{member_count}** | Fortune: **{total_money} SD**"
        )

    embed = make_embed(
        "Faction Leaderboard",
        "\n".join(lines),
        color=discord.Color.gold(),
        footer="Sukushi bot | Factions",
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="mute", description="Timeout a member for a set duration.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(moderate_members=True)
@app_commands.checks.has_permissions(moderate_members=True)
async def mute(
    interaction: discord.Interaction,
    member: discord.Member,
    duration: str,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    parsed_duration = parse_duration(duration)
    if parsed_duration > timedelta(days=28):
        await interaction.response.send_message(
            "Un mute Discord ne peut pas dépasser 28 jours.",
        )
        return

    await member.timeout(
        discord.utils.utcnow() + parsed_duration,
        reason=f"{moderator} | {reason or 'Aucune raison fournie'}",
    )
    await interaction.response.send_message(
        f"{member.mention} a été mute pendant `{format_timedelta(parsed_duration)}`.",
    )


@bot.tree.command(name="jail", description="Envoie un membre en prison économique.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(moderate_members=True)
@app_commands.checks.has_permissions(moderate_members=True)
async def jail(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    final_reason = reason or "Aucune raison fournie"
    challenge_record = await bot.send_member_to_prison(member, reason=final_reason)
    if challenge_record is None:
        await interaction.response.send_message(
            "Impossible de créer le salon de prison pour ce membre.",
            ephemeral=True,
        )
        return

    channel_id = challenge_record.get("channel_id")
    channel_text = f"<#{channel_id}>" if isinstance(channel_id, int) else "salon introuvable"
    await interaction.response.send_message(
        (
            f"{member.mention} a été envoyé en prison.\n"
            f"Raison : {final_reason}\n"
            f"Cellule : {channel_text}"
        )
    )


@bot.tree.command(name="unmute", description="Remove a timeout from a member.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(moderate_members=True)
@app_commands.checks.has_permissions(moderate_members=True)
async def unmute(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    await member.timeout(
        None,
        reason=f"{moderator} | {reason or 'Aucune raison fournie'}",
    )
    await interaction.response.send_message(
        f"Le mute de {member.mention} a été retiré.",
    )


@bot.tree.command(name="kick", description="Kick a member from the server.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(kick_members=True)
@app_commands.checks.has_permissions(kick_members=True)
async def kick(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    await member.kick(reason=f"{moderator} | {reason or 'Aucune raison fournie'}")
    await interaction.response.send_message(
        f"{member} a été expulsé du serveur.",
    )


@bot.tree.command(name="ban", description="Ban a member from the server.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(ban_members=True)
@app_commands.checks.has_permissions(ban_members=True)
async def ban(
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    await member.ban(reason=f"{moderator} | {reason or 'Aucune raison fournie'}")
    await interaction.response.send_message(
        f"{member} a été banni du serveur.",
    )


@bot.tree.command(name="tempban", description="Ban a member temporarily.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(ban_members=True)
@app_commands.checks.has_permissions(ban_members=True)
async def tempban(
    interaction: discord.Interaction,
    member: discord.Member,
    duration: str,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    parsed_duration = parse_duration(duration)
    await member.ban(reason=f"{moderator} | {reason or 'Aucune raison fournie'}")
    unban_at = datetime.now(timezone.utc) + parsed_duration

    task_key = (interaction.guild.id, member.id)
    existing_task = bot.tempban_tasks.pop(task_key, None)
    if existing_task is not None:
        existing_task.cancel()

    upsert_tempban(interaction.guild.id, member.id, unban_at, reason)
    bot.tempban_tasks[task_key] = asyncio.create_task(
        bot.schedule_tempban_unban(
            interaction.guild.id,
            member.id,
            parsed_duration,
            reason,
        )
    )
    await interaction.response.send_message(
        f"{member} a été banni pendant `{format_timedelta(parsed_duration)}`.",
    )


@bot.tree.command(name="unban", description="Unban a user with their ID.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(ban_members=True)
@app_commands.checks.has_permissions(ban_members=True)
async def unban(
    interaction: discord.Interaction,
    user_id: str,
    reason: str | None = None,
) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
        )
        return

    cleaned_user_id = user_id.strip()
    if not cleaned_user_id.isdigit():
        await interaction.response.send_message(
            "L'user ID doit contenir uniquement des chiffres.",
        )
        return

    user = discord.Object(id=int(cleaned_user_id))

    task_key = (interaction.guild.id, user.id)
    existing_task = bot.tempban_tasks.pop(task_key, None)
    if existing_task is not None:
        existing_task.cancel()

    remove_tempban(interaction.guild.id, user.id)
    await interaction.guild.unban(
        user,
        reason=f"{interaction.user} | {reason or 'Aucune raison fournie'}",
    )
    await interaction.response.send_message(
        f"L'utilisateur avec l'ID `{user.id}` a été débanni.",
    )


@bot.tree.command(name="clear", description="Delete a number of recent messages.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(
    interaction: discord.Interaction,
    amount: app_commands.Range[int, 1, 100],
) -> None:
    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans un salon texte.",
        )
        return

    await interaction.response.defer()
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(
        f"{len(deleted)} message(s) supprimé(s).",
    )


@bot.tree.command(name="jaillist", description="Affiche les membres actuellement en prison.")
async def jaillist(interaction: discord.Interaction) -> None:
    prisoners = get_all_prison_records()
    if not prisoners:
        await interaction.response.send_message(
            "Personne n'est actuellement en prison.",
        )
        return

    lines: list[str] = []
    for user_id, record in prisoners:
        member = interaction.guild.get_member(user_id) if interaction.guild is not None else None
        label = member.mention if member is not None else f"<@{user_id}>"
        reason = str(record.get("reason") or "Aucune raison précisée")
        channel_id = record.get("channel_id")
        channel_text = f"<#{channel_id}>" if isinstance(channel_id, int) else "salon manquant"
        jailed_at = record.get("jailed_at")
        time_text = jailed_at if isinstance(jailed_at, str) else "inconnue"
        lines.append(f"{label} • {channel_text} • {reason} • depuis `{time_text}`")

    embed = make_embed(
        "Membres en prison",
        "\n".join(lines[:25]),
        color=discord.Color.red(),
        footer="Sukushi bot | Prison",
    )
    if len(lines) > 25:
        embed.add_field(name="Note", value=f"{len(lines) - 25} autre(s) membre(s) non affiché(s).", inline=False)
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="forceevent", description="Lance immédiatement un événement pour les tests.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def forceevent(interaction: discord.Interaction) -> None:
    success, message = await bot.start_random_event(forced=True)
    await interaction.response.send_message(message, ephemeral=True)


@bot.tree.command(name="clearevent", description="Supprime l'événement actif.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def clearevent(interaction: discord.Interaction) -> None:
    cleared = await bot.clear_active_event()
    if not cleared:
        await interaction.response.send_message(
            "Aucun événement actif à supprimer.",
            ephemeral=True,
        )
        return

    await interaction.response.send_message(
        "L'événement actif a été supprimé.",
        ephemeral=True,
    )


@bot.tree.command(name="economystats", description="Affiche les statistiques globales de l'économie.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_guild=True)
@app_commands.checks.has_permissions(manage_guild=True)
async def economystats(interaction: discord.Interaction) -> None:
    stats = get_economy_stats()
    if not stats:
        await interaction.response.send_message(
            "Aucune statistique économique n'a encore été enregistrée.",
            ephemeral=True,
        )
        return

    gain_sorted = sorted(stats.items(), key=lambda item: item[1].get("gained", 0), reverse=True)
    loss_sorted = sorted(stats.items(), key=lambda item: item[1].get("lost", 0), reverse=True)
    net_sorted = sorted(
        stats.items(),
        key=lambda item: item[1].get("gained", 0) - item[1].get("lost", 0),
        reverse=True,
    )

    def format_stat_lines(items: list[tuple[str, dict[str, int]]], *, mode: str) -> str:
        lines: list[str] = []
        for source, values in items[:5]:
            gained = int(values.get("gained", 0))
            lost = int(values.get("lost", 0))
            gain_events = int(values.get("gain_events", 0))
            loss_events = int(values.get("loss_events", 0))
            label = get_economy_stat_label(source)
            if mode == "gain":
                lines.append(f"**{label}** - +{gained} SD ({gain_events} gains)")
            elif mode == "loss":
                lines.append(f"**{label}** - -{lost} SD ({loss_events} pertes)")
            else:
                net = gained - lost
                sign = "+" if net >= 0 else ""
                lines.append(f"**{label}** - {sign}{net} SD")
        return "\n".join(lines) if lines else "Aucune donnée."

    total_gained = sum(int(values.get("gained", 0)) for values in stats.values())
    total_lost = sum(int(values.get("lost", 0)) for values in stats.values())
    total_net = total_gained - total_lost

    embed = make_embed(
        "Statistiques Économie",
        (
            f"Argent gagné total : **{total_gained} SD**\n"
            f"Argent perdu total : **{total_lost} SD**\n"
            f"Net global : **{total_net:+} SD**"
        ),
        color=discord.Color.gold(),
        footer="Sukushi bot | Économie stats",
    )
    embed.add_field(name="Top gains", value=format_stat_lines(gain_sorted, mode="gain"), inline=False)
    embed.add_field(name="Top pertes", value=format_stat_lines(loss_sorted, mode="loss"), inline=False)
    embed.add_field(name="Top net", value=format_stat_lines(net_sorted, mode="net"), inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


@bot.tree.command(name="lotterypanel", description="Envoie le panneau de la loterie.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def lotterypanel(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
            ephemeral=True,
        )
        return

    panel_channel = interaction.guild.get_channel(LOTTERY_CHANNEL_ID)
    if not isinstance(panel_channel, discord.TextChannel):
        await interaction.response.send_message(
            "Le salon de la loterie est introuvable.",
            ephemeral=True,
        )
        return

    if bot.lottery_task is not None:
        bot.lottery_task.cancel()

    ends_at = datetime.now(timezone.utc) + LOTTERY_DURATION
    await panel_channel.send(build_lottery_start_message())
    message = await panel_channel.send(
        embed=build_lottery_embed(ends_at=ends_at, participants_count=0),
        view=LotteryView(),
    )
    state: dict[str, object] = {
        "message_id": message.id,
        "participants": [],
        "ends_at": ends_at.isoformat(),
    }
    save_lottery_state(state)
    await bot.schedule_lottery_draw(ends_at)
    await interaction.response.send_message(
        f"Le panneau de la loterie a été envoyé dans {panel_channel.mention}.",
        ephemeral=True,
    )


@bot.tree.command(name="rolepanel", description="Envoie le panneau des autoroles.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def rolepanel(interaction: discord.Interaction) -> None:
    if interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans le serveur.",
            ephemeral=True,
        )
        return

    panel_channel = interaction.guild.get_channel(AUTOROLE_CHANNEL_ID)
    if not isinstance(panel_channel, discord.TextChannel):
        await interaction.response.send_message(
            "Le salon des autoroles est introuvable.",
            ephemeral=True,
        )
        return

    for panel in AUTOROLE_PANELS:
        lines = [
            f"{entry['emoji']} : **{entry['label']}**"
            for entry in panel["entries"]
        ]
        embed = make_embed(
            str(panel["title"]),
            f"{panel['description']}\n\n" + "\n".join(lines),
            color=SUKUSHI_PINK,
            footer=AUTOROLE_FOOTER,
        )
        if panel["include_banner"]:
            embed.set_image(url=BANNER_URL)

        message = await panel_channel.send(embed=embed)
        for entry in panel["entries"]:
            await message.add_reaction(str(entry["emoji"]))

    await interaction.response.send_message(
        f"Le panneau des autoroles a été envoyé dans {panel_channel.mention}.",
        ephemeral=True,
    )


@bot.tree.command(name="resetall", description="Reset all bot cooldowns.")
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def resetall(interaction: discord.Interaction) -> None:
    reset_cooldown_files()
    await interaction.response.send_message(
        "Tous les cooldowns ont été réinitialisés.",
        ephemeral=True,
    )


@bot.tree.command(name="resetallbal", description="Reset everyone's balance to 1000.")
@prison_block(allow_staff_bypass=True)
async def resetallbal(interaction: discord.Interaction) -> None:
    if interaction.user.id != BALANCE_RESET_OWNER_ID:
        await interaction.response.send_message(
            "Tu n'es pas autorisé à utiliser cette commande.",
            ephemeral=True,
        )
        return

    updated_users = reset_all_balances(STARTING_BALANCE)
    await interaction.response.send_message(
        (
            f"Tous les soldes ont été réinitialisés à **{STARTING_BALANCE} Sukushi Dollars**.\n"
            f"Comptes mis à jour : **{updated_users}**."
        ),
        ephemeral=True,
    )


@bot.tree.command(name="resetmoney", description="Reset l'argent d'un utilisateur à 0.")
@prison_block(allow_staff_bypass=True)
async def resetmoney(
    interaction: discord.Interaction,
    member: discord.Member,
) -> None:
    if interaction.user.id != BALANCE_RESET_OWNER_ID:
        await interaction.response.send_message(
            "Tu n'es pas autorisé à utiliser cette commande.",
            ephemeral=True,
        )
        return

    new_balance = set_balance_value(member.id, 0)
    await interaction.response.send_message(
        f"L'argent de {member.mention} a été réinitialisé à **{new_balance} Sukushi Dollars**.",
        ephemeral=True,
    )


@bot.tree.command(name="staffgive", description="Ajoute de l'argent à un utilisateur.")
@prison_block(allow_staff_bypass=True)
async def staffgive(
    interaction: discord.Interaction,
    member: discord.Member,
    montant: app_commands.Range[int, 1, 1_000_000],
) -> None:
    if interaction.user.id != BALANCE_RESET_OWNER_ID:
        await interaction.response.send_message(
            "Tu n'es pas autorisé à utiliser cette commande.",
            ephemeral=True,
        )
        return

    ensure_minimum_balance(member.id)
    new_balance = add_balance(member.id, montant)
    record_economy_stat("staff_give", montant)
    await interaction.response.send_message(
        (
            f"**{montant} Sukushi Dollars** ont été ajoutés à {member.mention}.\n"
            f"Nouveau solde : **{new_balance} Sukushi Dollars**."
        ),
        ephemeral=True,
    )


@bot.tree.command(name="stafftake", description="Retire de l'argent à un utilisateur.")
@prison_block(allow_staff_bypass=True)
async def stafftake(
    interaction: discord.Interaction,
    member: discord.Member,
    montant: app_commands.Range[int, 1, 1_000_000],
) -> None:
    if interaction.user.id != BALANCE_RESET_OWNER_ID:
        await interaction.response.send_message(
            "Tu n'es pas autorisé à utiliser cette commande.",
            ephemeral=True,
        )
        return

    ensure_minimum_balance(member.id)
    current_balance = get_balance_value(member.id)
    removed_amount = min(current_balance, montant)
    new_balance = set_balance_value(member.id, current_balance - removed_amount)
    record_economy_stat("staff_take", -removed_amount)
    await interaction.response.send_message(
        (
            f"**{removed_amount} Sukushi Dollars** ont été retirés à {member.mention}.\n"
            f"Nouveau solde : **{new_balance} Sukushi Dollars**."
        ),
        ephemeral=True,
    )


@bot.tree.command(name="ecoban", description="Bannit un utilisateur des commandes économiques.")
@prison_block(allow_staff_bypass=True)
async def ecoban(
    interaction: discord.Interaction,
    member: discord.Member,
) -> None:
    if interaction.user.id != BALANCE_RESET_OWNER_ID:
        await interaction.response.send_message(
            "Tu n'es pas autorisé à utiliser cette commande.",
            ephemeral=True,
        )
        return

    if add_ecoban(member.id):
        await interaction.response.send_message(
            f"{member.mention} est maintenant banni des commandes économiques.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"{member.mention} est déjà banni des commandes économiques.",
            ephemeral=True,
        )


@bot.tree.command(name="ecounban", description="Retire le ban économique d'un utilisateur.")
@prison_block(allow_staff_bypass=True)
async def ecounban(
    interaction: discord.Interaction,
    member: discord.Member,
) -> None:
    if interaction.user.id != BALANCE_RESET_OWNER_ID:
        await interaction.response.send_message(
            "Tu n'es pas autorisé à utiliser cette commande.",
            ephemeral=False,
        )
        return

    if remove_ecoban(member.id):
        await interaction.response.send_message(
            f"{member.mention} peut de nouveau utiliser les commandes économiques.",
            ephemeral=False,
        )
    else:
        await interaction.response.send_message(
            f"{member.mention} n'est pas banni des commandes économiques.",
            ephemeral=False,
        )


def main() -> None:
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        raise RuntimeError(
            "Missing DISCORD_TOKEN environment variable. "
            "Set it before starting the bot."
        )

    print(f"Using single-guild sync for guild {PRIMARY_GUILD_ID}.")

    print("Server Members Intent must also be enabled in the Discord Developer Portal.")
    print("Tempbans are stored in tempbans.json and restored after a restart.")
    bot.run(token)


if __name__ == "__main__":
    main()
