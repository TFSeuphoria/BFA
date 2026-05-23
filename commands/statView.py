import discord
from discord.ext import commands
from discord import app_commands
import json
import os

CATEGORY_ORDER = ["qb", "rb", "wr", "db", "def", "k"]
CATEGORY_NAMES = {
    "qb": "QB",
    "rb": "RB",
    "wr": "WR",
    "db": "DB",
    "def": "DEF",
    "k": "Kicker"
}


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)
    with open(path, "r") as f:
        return json.load(f)


def get_nested(data, *keys):
    current = data
    for key in keys:
        current = current.get(key, {})
    return current


def score_category(category, stats):
    if not stats:
        return 0

    if category == "qb":
        yds = stats.get("yds", 0)
        comp = stats.get("comp", 0)
        inc = stats.get("inc", 0)
        td = stats.get("td", 0)
        ints = stats.get("int", 0)
        sack = stats.get("sack", 0)
        attempts = comp + inc

        score = 0
        score += yds * 0.1
        score += td * 10
        score += comp * 1
        score -= inc * 0.5
        score -= ints * 5
        score -= sack * 1

        if attempts > 0:
            ypa = yds / attempts
            if ypa > 40:
                score += 60
            elif ypa > 30:
                score += 45
            elif ypa > 20:
                score += 30
            elif ypa > 10:
                score += 15

        return round(score, 2)

    if category == "rb":
        score = 0
        score += stats.get("yds", 0) * 0.1
        score += stats.get("td", 0) * 10
        return round(score, 2)

    if category == "wr":
        yds = stats.get("yds", 0)
        yac = stats.get("yac", 0)
        catches = stats.get("catch", 0)
        targets = stats.get("tgt", 0)
        drops = max(targets - catches, 0)

        score = 0
        score += yds * 0.1
        score += yac * 0.1
        score += stats.get("td", 0) * 10
        score += catches * 1
        score -= drops * 0.5
        score -= stats.get("int_allow", 0) * 5

        if catches > 0:
            yac_per_catch = yac / catches
            if yac_per_catch > 40:
                score += 60
            elif yac_per_catch > 30:
                score += 45
            elif yac_per_catch > 20:
                score += 30
            elif yac_per_catch > 10:
                score += 15

        return round(score, 2)

    if category == "db":
        score = 0
        score += stats.get("int", 0) * 10
        score += stats.get("defl", 0) * 5
        score -= stats.get("catch_allow", 0) * 3
        score -= stats.get("td_allow", 0) * 10
        score -= stats.get("yds_allow", 0) * 0.1
        return round(score, 2)

    if category == "def":
        score = 0
        score += stats.get("sack", 0) * 10
        score += stats.get("tack", 0) * 1
        score += stats.get("ffum", 0) * 10
        score += stats.get("rec", 0) * 10
        return round(score, 2)

    if category == "k":
        good = stats.get("good", 0)
        att = stats.get("att", 0)

        score = good * 1

        if att > 0 and good / att > 0.8:
            score += 10

        return round(score, 2)

    return 0


def find_player_by_query(players, query):
    query = query.lower()

    for discord_id, data in players.items():
        users = data.get("users", [])
        for user in users:
            if user.lower() == query:
                return discord_id, data

    for discord_id, data in players.items():
        users = data.get("users", [])
        for user in users:
            if query in user.lower():
                return discord_id, data

    return None, None


def get_rank(players, category, target_id):
    scored = []

    for discord_id, data in players.items():
        cat_stats = get_nested(data, "game_stats", category)
        points = score_category(category, cat_stats)

        if points > 0:
            scored.append((discord_id, points))

    scored.sort(key=lambda x: x[1], reverse=True)

    for index, item in enumerate(scored, start=1):
        if item[0] == target_id:
            return index, item[1]

    return None, 0


def get_best_category(player_data):
    best_category = "qb"
    best_score = -999999

    for category in CATEGORY_ORDER:
        points = score_category(category, get_nested(player_data, "game_stats", category))

        if points > best_score:
            best_score = points
            best_category = category

    return best_category


def count_games_played(discord_id, stats_json, games_json, season=None):
    users = stats_json.get(discord_id, {}).get("users", [])
    count = 0

    for game in games_json.values():
        if season and str(game.get("season")) != str(season):
            continue

        for player_data in game.get("stats", {}).values():
            other = player_data.get("other", {})
            if other.get("name") in users or other.get("display") in users:
                count += 1
                break

    return count


def get_current_season_data():
    seasons_json = load_json("seasons.json")

    seasons = seasons_json.get("seasons", {})
    if not seasons:
        return "1", {}

    highest = max(seasons.keys(), key=lambda x: int(x))
    return highest, seasons[highest]


def make_embed(guild, discord_id, player_data, players, category, scope, games_played):
    rank, points = get_rank(players, category, discord_id)

    users = player_data.get("users", [])
    shown_name = users[0] if users else f"<@{discord_id}>"

    embed = discord.Embed(
        title=f"{shown_name} Stats",
        color=discord.Color.blue()
    )

    embed.add_field(name="Scope", value=scope, inline=True)
    embed.add_field(name="Games Played", value=str(games_played), inline=True)
    embed.add_field(name="Category", value=CATEGORY_NAMES[category], inline=True)
    embed.add_field(name="Category Points", value=str(points), inline=True)
    embed.add_field(name="Ranking", value=f"#{rank}" if rank else "Unranked", inline=True)

    cat_stats = get_nested(player_data, "game_stats", category)

    if cat_stats:
        lines = [f"**{k}:** {v}" for k, v in cat_stats.items()]
        embed.add_field(name="Stats", value="\n".join(lines), inline=False)
    else:
        embed.add_field(name="Stats", value="No stats.", inline=False)

    return embed


class StatDropdown(discord.ui.Select):
    def __init__(self, discord_id, player_data, players, scope, games_played):
        self.discord_id = discord_id
        self.player_data = player_data
        self.players = players
        self.scope = scope
        self.games_played = games_played

        options = [
            discord.SelectOption(label="QB", value="qb"),
            discord.SelectOption(label="RB", value="rb"),
            discord.SelectOption(label="WR", value="wr"),
            discord.SelectOption(label="DB", value="db"),
            discord.SelectOption(label="DEF", value="def"),
            discord.SelectOption(label="Kicker", value="k")
        ]

        super().__init__(
            placeholder="View another category",
            options=options,
            min_values=1,
            max_values=1
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        embed = make_embed(
            interaction.guild,
            self.discord_id,
            self.player_data,
            self.players,
            category,
            self.scope,
            self.games_played
        )

        await interaction.response.edit_message(embed=embed, view=self.view)


class StatViewButtons(discord.ui.View):
    def __init__(self, discord_id, player_data, players, scope, games_played):
        super().__init__(timeout=300)
        self.add_item(StatDropdown(discord_id, player_data, players, scope, games_played))


class StatView(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def user_autocomplete(
        self,
        interaction: discord.Interaction,
        current: str
    ):
        stats_json = load_json("stats.json")
        results = []

        for discord_id, data in stats_json.items():
            for user in data.get("users", []):
                if current.lower() in user.lower():
                    results.append(app_commands.Choice(name=user, value=user))

                if len(results) >= 25:
                    return results

        return results

    @app_commands.command(name="statview", description="View player stats")
    @app_commands.autocomplete(user=user_autocomplete)
    @app_commands.choices(
        scope=[
            app_commands.Choice(name="All-Time", value="alltime"),
            app_commands.Choice(name="Current Season", value="season")
        ]
    )
    async def statview(
        self,
        interaction: discord.Interaction,
        user: str,
        scope: app_commands.Choice[str]
    ):

        stats_json = load_json("stats.json")
        games_json = load_json("games.json")

        if scope.value == "alltime":
            players = stats_json
            scope_text = "All-Time"
            season_id = None
        else:
            season_id, season_data = get_current_season_data()
            players = season_data.get("players", {})
            scope_text = f"Season {season_id}"

        discord_id, player_data = find_player_by_query(players, user)

        if not player_data:
            await interaction.response.send_message(
                "Could not find that user in the stats database.",
                ephemeral=True
            )
            return

        best_category = get_best_category(player_data)

        games_played = count_games_played(
            discord_id,
            stats_json,
            games_json,
            season_id
        )

        embed = make_embed(
            interaction.guild,
            discord_id,
            player_data,
            players,
            best_category,
            scope_text,
            games_played
        )

        await interaction.response.send_message(
            embed=embed,
            view=StatViewButtons(discord_id, player_data, players, scope_text, games_played),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(StatView(bot))
