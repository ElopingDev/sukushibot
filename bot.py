import asyncio
import json
import os
import random
import re
from datetime import datetime, timedelta, timezone
from pathlib import Path

import discord
from discord import app_commands

WELCOME_CHANNEL_ID = 1494255574949429438
GOODBYE_CHANNEL_ID = 1494255913366978641
AUTOROLE_CHANNEL_ID = 1494255821054414878
JOIN_ROLE_ID = 1494249084221919343
PRIMARY_GUILD_ID = 1494245152858964070

BANNER_URL = "https://i.imgur.com/x4uAHlu.png"
SUKUSHI_PINK = discord.Color.from_rgb(255, 105, 180)
AUTOROLE_TITLE = "Autoroles"
ECONOMY_FILE = Path("economy.json")
ECONOMY_META_FILE = Path("economy_meta.json")
TEMPBAN_FILE = Path("tempbans.json")
DAILY_FILE = Path("daily.json")
WORK_FILE = Path("work.json")
JOB_FILE = Path("jobs.json")
PRISON_FILE = Path("prison.json")
ATTACK_FILE = Path("attack_cooldowns.json")
CHANGEJOB_FILE = Path("changejob.json")
STARTING_BALANCE = 1000
BALANCE_RESET_OWNER_ID = 885927546456272957
DAILY_REWARD = 500
WORK_REWARD = 1000
WORK_FAIL_REWARD = 500
DAILY_COOLDOWN = timedelta(days=1)
WORK_COOLDOWN = timedelta(days=1)
ATTACK_COOLDOWN = timedelta(hours=5)
GLOBAL_ATTACK_COOLDOWN = timedelta(minutes=30)
CHANGEJOB_COOLDOWN = timedelta(days=1)
PRISON_DURATION = timedelta(minutes=10)
PRISON_CHANCE = 0.15
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
            {"label": "Voler un passant", "reward": 700, "catch_chance": 0.05},
            {"label": "Braquer une supérette", "reward": 1050, "catch_chance": 0.15},
            {"label": "Braquer un bijoutier", "reward": 1500, "catch_chance": 0.45},
        ],
    },
    "dealer": {
        "prompt": "Choisis ce que tu vends",
        "actions": [
            {"label": "Vendre de la weed", "reward": 700, "catch_chance": 0.05},
            {"label": "Vendre du xanax", "reward": 1100, "catch_chance": 0.15},
            {"label": "Vendre de la meth", "reward": 1600, "catch_chance": 0.45},
        ],
    },
    "pickpocketer": {
        "prompt": "Choisis ta cible",
        "actions": [
            {"label": "Voler un portefeuille", "reward": 650, "catch_chance": 0.03},
            {"label": "Voler un téléphone", "reward": 950, "catch_chance": 0.12},
            {"label": "Détrousser un touriste riche", "reward": 1400, "catch_chance": 0.30},
        ],
    },
    "frauder": {
        "prompt": "Choisis ton arnaque",
        "actions": [
            {"label": "Petite arnaque en ligne", "reward": 750, "catch_chance": 0.02},
            {"label": "Faux virement bancaire", "reward": 1200, "catch_chance": 0.20},
            {"label": "Grosse fraude à la carte", "reward": 1700, "catch_chance": 0.55},
        ],
    },
}
ATTACK_STARTING_HP = 100
ATTACK_PLAYER_HIT_CHANCE = 0.78
ATTACK_AI_HIT_CHANCE = 0.55
ATTACK_PLAYER_DAMAGE = (18, 32)
ATTACK_AI_DAMAGE = (10, 20)
ATTACK_STEAL_PERCENT = (0.04, 0.1)
ACTIVE_ATTACK_USERS: set[int] = set()

AUTOROLE_MAP = {
    "emoji_1": 1494250525846278174,
    "emoji_8": 1494250837814284389,
    "emoji_6": 1494250775734386781,
}
AUTOROLE_LABELS = {
    "emoji_1": "Annonces",
    "emoji_8": "Giveaway",
    "emoji_6": "Events",
}

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


def ensure_minimum_balance(user_id: int, minimum: int = STARTING_BALANCE) -> int:
    current = get_balance_value(user_id)
    if current >= minimum:
        return current
    return set_balance_value(user_id, minimum)


def get_top_balances(limit: int = 10) -> list[tuple[int, int]]:
    data = load_economy()
    sorted_balances = sorted(
        ((int(user_id), balance) for user_id, balance in data.items()),
        key=lambda item: item[1],
        reverse=True,
    )
    return sorted_balances[:limit]


def reset_all_balances(amount: int = STARTING_BALANCE) -> int:
    data = load_economy()
    for user_id in list(data.keys()):
        data[user_id] = amount
    save_economy(data)
    return len(data)


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


def load_json_dict(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    return {str(key): str(value) for key, value in data.items()}


def save_json_dict(path: Path, data: dict[str, str]) -> None:
    with path.open("w", encoding="utf-8") as file:
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


def get_prison_release(user_id: int) -> datetime | None:
    data = load_json_dict(PRISON_FILE)
    raw_value = data.get(str(user_id))
    if raw_value is None:
        return None

    release_at = datetime.fromisoformat(raw_value)
    if release_at <= datetime.now(timezone.utc):
        data.pop(str(user_id), None)
        save_json_dict(PRISON_FILE, data)
        return None
    return release_at


def imprison_user(user_id: int, duration: timedelta = PRISON_DURATION) -> datetime:
    release_at = datetime.now(timezone.utc) + duration
    data = load_json_dict(PRISON_FILE)
    data[str(user_id)] = release_at.isoformat()
    save_json_dict(PRISON_FILE, data)
    return release_at


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


async def ensure_not_in_prison(interaction: discord.Interaction) -> bool:
    release_at = get_prison_release(interaction.user.id)
    if release_at is None:
        return True

    remaining = format_remaining_time(release_at - datetime.now(timezone.utc))
    if interaction.response.is_done():
        await interaction.followup.send(
            f"Tu es en prison pour encore **{remaining}**. Tu ne peux pas utiliser le bot pour le moment.",
            ephemeral=True,
        )
    else:
        await interaction.response.send_message(
            f"Tu es en prison pour encore **{remaining}**. Tu ne peux pas utiliser le bot pour le moment.",
            ephemeral=True,
        )
    return False


def prison_block():
    async def predicate(interaction: discord.Interaction) -> bool:
        return await ensure_not_in_prison(interaction)

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
        return f"{cards[0]} • ??"
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
                release_at = imprison_user(interaction.user.id)
                prison_reward = reward // 2
                new_balance = add_balance(interaction.user.id, prison_reward)
                remaining = format_remaining_time(release_at - datetime.now(timezone.utc))
                result = (
                    f"Tu as choisi **{action_label}**.\n"
                    f"Tu t'es fait attraper. Tu ne gardes que **{prison_reward} Sukushi Dollars** et tu pars en prison.\n"
                    f"Libération dans **{remaining}**.\n"
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


class SukushiBot(discord.Client):
    def __init__(self) -> None:
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.tempban_tasks: dict[tuple[int, int], asyncio.Task[None]] = {}
        self.restored_tempbans = False

    async def setup_hook(self) -> None:
        guild = discord.Object(id=PRIMARY_GUILD_ID)
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
            if economy_data.get(key, 0) < STARTING_BALANCE:
                economy_data[key] = STARTING_BALANCE
                changed = True

        if changed:
            save_economy(economy_data)

        seeded_guilds.add(guild_key)
        save_economy_meta({"seeded_guilds": sorted(seeded_guilds)})
        print(f"Starter balance granted for guild {guild.name} ({guild.id}).")

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
        if not message.embeds or message.embeds[0].title != AUTOROLE_TITLE:
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


@bot.tree.command(name="ping", description="Check if sukushi bot is online.")
@prison_block()
async def ping(interaction: discord.Interaction) -> None:
    latency_ms = round(bot.latency * 1000)
    embed = make_embed(
        "Pong !",
        f"sukushi bot est en ligne.\nLatence de la gateway : `{latency_ms}ms`",
        color=discord.Color.green(),
        footer=f"Demandé par {interaction.user.display_name}",
    )
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="balance", description="Show your Sukushi Dollars balance.")
@prison_block()
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


@bot.tree.command(name="leaderboard", description="Show the richest users on the server.")
@prison_block()
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

    target_prison = get_prison_release(cible.id)
    if target_prison is not None:
        remaining = format_remaining_time(target_prison - datetime.now(timezone.utc))
        await interaction.response.send_message(
            f"{cible.mention} est déjà en prison pendant encore **{remaining}**.",
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
@prison_block()
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
            ephemeral=True,
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
            ephemeral=True,
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message, ephemeral=True)
        return

    parsed_duration = parse_duration(duration)
    if parsed_duration > timedelta(days=28):
        await interaction.response.send_message(
            "Un mute Discord ne peut pas dépasser 28 jours.",
            ephemeral=True,
        )
        return

    await member.timeout(
        discord.utils.utcnow() + parsed_duration,
        reason=f"{moderator} | {reason or 'Aucune raison fournie'}",
    )
    await interaction.response.send_message(
        f"{member.mention} a été mute pendant `{format_timedelta(parsed_duration)}`.",
        ephemeral=True,
    )


@bot.tree.command(name="unmute", description="Remove a timeout from a member.")
@prison_block()
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
            ephemeral=True,
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
            ephemeral=True,
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message, ephemeral=True)
        return

    await member.timeout(
        None,
        reason=f"{moderator} | {reason or 'Aucune raison fournie'}",
    )
    await interaction.response.send_message(
        f"Le mute de {member.mention} a été retiré.",
        ephemeral=True,
    )


@bot.tree.command(name="kick", description="Kick a member from the server.")
@prison_block()
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
            ephemeral=True,
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
            ephemeral=True,
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message, ephemeral=True)
        return

    await member.kick(reason=f"{moderator} | {reason or 'Aucune raison fournie'}")
    await interaction.response.send_message(
        f"{member} a été expulsé du serveur.",
        ephemeral=True,
    )


@bot.tree.command(name="ban", description="Ban a member from the server.")
@prison_block()
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
            ephemeral=True,
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
            ephemeral=True,
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message, ephemeral=True)
        return

    await member.ban(reason=f"{moderator} | {reason or 'Aucune raison fournie'}")
    await interaction.response.send_message(
        f"{member} a été banni du serveur.",
        ephemeral=True,
    )


@bot.tree.command(name="tempban", description="Ban a member temporarily.")
@prison_block()
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
            ephemeral=True,
        )
        return

    bot_member = get_bot_member(interaction.guild, bot.user)
    if bot_member is None:
        await interaction.response.send_message(
            "Je n'arrive pas à vérifier ma hiérarchie dans ce serveur.",
            ephemeral=True,
        )
        return

    allowed, message = can_act_on_target(moderator, member, bot_member)
    if not allowed:
        await interaction.response.send_message(message, ephemeral=True)
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
        ephemeral=True,
    )


@bot.tree.command(name="unban", description="Unban a user with their ID.")
@prison_block()
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
            ephemeral=True,
        )
        return

    cleaned_user_id = user_id.strip()
    if not cleaned_user_id.isdigit():
        await interaction.response.send_message(
            "L'user ID doit contenir uniquement des chiffres.",
            ephemeral=True,
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
        ephemeral=True,
    )


@bot.tree.command(name="clear", description="Delete a number of recent messages.")
@prison_block()
@app_commands.default_permissions(manage_messages=True)
@app_commands.checks.has_permissions(manage_messages=True)
async def clear(
    interaction: discord.Interaction,
    amount: app_commands.Range[int, 1, 100],
) -> None:
    if not isinstance(interaction.channel, discord.TextChannel):
        await interaction.response.send_message(
            "Cette commande doit être utilisée dans un salon texte.",
            ephemeral=True,
        )
        return

    await interaction.response.defer(ephemeral=True)
    deleted = await interaction.channel.purge(limit=amount)
    await interaction.followup.send(
        f"{len(deleted)} message(s) supprimé(s).",
        ephemeral=True,
    )


@bot.tree.command(name="resetall", description="Reset all bot cooldowns.")
@prison_block()
@app_commands.default_permissions(administrator=True)
@app_commands.checks.has_permissions(administrator=True)
async def resetall(interaction: discord.Interaction) -> None:
    reset_cooldown_files()
    await interaction.response.send_message(
        "Tous les cooldowns ont été réinitialisés.",
        ephemeral=True,
    )


@bot.tree.command(name="resetallbal", description="Reset everyone's balance to 1000.")
@prison_block()
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
