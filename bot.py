import asyncio
import json
import os
import random
import re
import string
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands

from economy import (
    add_balance,
    add_ecoban,
    ensure_minimum_balance,
    get_all_prison_records,
    get_balance_value,
    get_cooldown_remaining,
    get_job,
    get_pair_cooldown_remaining,
    get_prison_record,
    get_top_balances,
    imprison_user,
    is_in_prison,
    is_ecobanned,
    load_economy,
    load_economy_meta,
    load_lottery_state,
    load_json_dict,
    remove_prison_record,
    remove_ecoban,
    reset_all_balances,
    reset_cooldown_files,
    save_economy,
    save_economy_meta,
    save_lottery_state,
    save_json_dict,
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
JAIL_MIN_SOLVE_SECONDS = 10
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
ATTACK_STARTING_HP = 100
ATTACK_PLAYER_HIT_CHANCE = 0.78
ATTACK_AI_HIT_CHANCE = 0.55
ATTACK_PLAYER_DAMAGE = (18, 32)
ATTACK_AI_DAMAGE = (10, 20)
ATTACK_STEAL_PERCENT = (0.1, 0.15)
ACTIVE_ATTACK_USERS: set[int] = set()
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
            result = (
                f"Blackjack naturel. Tu gagnes **{gain}**.\n"
                f"Nouveau solde : **{new_balance} Sukushi Dollars**."
            )
        else:
            new_balance = add_balance(self.player.id, -self.bet)
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
            result = f"Tu dépasses 21. Tu perds **{self.bet}**.\nNouveau solde : **{new_balance} Sukushi Dollars**."
        elif dealer_total > 21 or player_total > dealer_total:
            new_balance = add_balance(self.player.id, self.bet)
            result = f"Tu gagnes **{self.bet}**.\nNouveau solde : **{new_balance} Sukushi Dollars**."
        elif player_total < dealer_total:
            new_balance = add_balance(self.player.id, -self.bet)
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


class SukushiBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tempban_tasks: dict[tuple[int, int], asyncio.Task[None]] = {}
        self.lottery_task: asyncio.Task[None] | None = None
        self.restored_tempbans = False

    async def setup_hook(self) -> None:
        guild = discord.Object(id=PRIMARY_GUILD_ID)
        self.add_view(TicketOpenView())
        self.add_view(TicketCloseView())
        self.add_view(LotteryView())
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        print(f"Synced {len(synced)} command(s) to primary guild {PRIMARY_GUILD_ID}.")

    async def on_ready(self) -> None:
        if self.user is None:
            return
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        if not self.restored_tempbans:
            await self.restore_tempbans()
            self.restored_tempbans = True
        await self.seed_existing_member_balances()
        await self.restore_prison_challenges()
        await self.restore_lottery()
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

        await guild.chunk()
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
    ) -> dict[str, object] | None:
        channel = await self.get_or_create_prison_channel(member)
        if channel is None:
            return None

        previous_record = get_prison_record(member.id)
        jailed_at = datetime.now(timezone.utc).isoformat()
        attempts = 0
        if previous_record is not None:
            previous_jailed_at = previous_record.get("jailed_at")
            if isinstance(previous_jailed_at, str):
                jailed_at = previous_jailed_at
            attempts = int(previous_record.get("attempts", 0))

        challenge = generate_prison_challenge()
        sent_at = datetime.now(timezone.utc).isoformat()
        record = set_prison_record(
            member.id,
            {
                "jailed_at": jailed_at,
                "reason": reason,
                "channel_id": channel.id,
                "challenge": challenge,
                "challenge_sent_at": sent_at,
                "attempts": attempts + 1,
            },
        )

        embed = make_embed(
            "Test de sortie de prison",
            (
                f"{member.mention}, tu es en prison pour **{reason}**.\n"
                "Retape exactement la chaîne ci-dessous dans ce salon.\n"
                "Respecte les majuscules et les minuscules.\n"
                f"N'envoie pas la bonne réponse avant **{JAIL_MIN_SOLVE_SECONDS} secondes**, sinon tu seras considéré comme un tricheur."
            ),
            color=discord.Color.red(),
            footer="Sukushi bot | Prison",
        )
        embed.add_field(name="Code", value=f"`{challenge}`", inline=False)
        embed.add_field(
            name="Règle anti-copie",
            value="Si la bonne réponse arrive trop vite, le bot considère que tu as copié-collé.",
            inline=False,
        )
        if penalty_text:
            embed.add_field(name="Sanction", value=penalty_text, inline=False)

        await channel.send(content=member.mention, embed=embed)
        return record

    async def send_member_to_prison(self, member: discord.Member, *, reason: str) -> dict[str, object] | None:
        imprison_user(member.id, reason=reason)
        return await self.send_prison_challenge(member, reason=reason)

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

        attempt = message.content.strip()
        if attempt != challenge:
            await message.channel.send(
                f"{message.author.mention} code incorrect. Réessaie en respectant exactement les majuscules et les minuscules."
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
            await message.channel.send(
                (
                    f"{message.author.mention} bien essayé. Réponse correcte en moins de **{JAIL_MIN_SOLVE_SECONDS} secondes** : "
                    "ça ressemble à un copier-coller.\n"
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
                )

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


"""Removed temporary /jail command.
    interaction: discord.Interaction,
    member: discord.Member,
    reason: str | None = None,
) -> None:
    moderator = get_moderator_member(interaction)
    if moderator is None or interaction.guild is None:
        await interaction.response.send_message(
            "Cette commande doit ?tre utilis?e dans le serveur.",
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas ? v?rifier ma hi?rarchie dans ce serveur.",
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message)
        return

    release_at = imprison_user(member.id, TEST_JAIL_DURATION)
    remaining = format_remaining_time(release_at - datetime.now(timezone.utc))
    await interaction.response.send_message(
        (
            f"{member.mention} a ?t? envoy? en prison pendant **{remaining}**.\n"
            f"Raison : {reason or 'Aucune raison fournie'}."
        )
    )


"""
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
@prison_block(allow_staff_bypass=True)
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def jaillist(interaction: discord.Interaction) -> None:
    prisoners = get_all_prison_records()
    if not prisoners:
        await interaction.response.send_message(
            "Personne n'est actuellement en prison.",
            ephemeral=True,
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
