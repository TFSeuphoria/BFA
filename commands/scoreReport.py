import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

from channelsData import STATS_CHANNEL

CATEGORY_NAMES = {
    "qb": "QB",
    "rb": "RB",
    "wr": "WR",
    "db": "DB",
    "def": "DEF",
    "k": "Kicker"
}


def load_json_file(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)

    with open(path, "r") as f:
        return json.load(f)


def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def parse_score_file(raw_text):
    parts = raw_text.split("///", 1)

    if len(parts) != 2:
        raise ValueError("Stats file must contain score /// json data.")

    score_text = parts[0].strip()
    json_text = parts[1].strip()

    score_match = re.search(r"(\d+)\s*-\s*(\d+)", score_text)

    if not score_match:
        raise ValueError("Could not read score.")

    away_score = int(score_match.group(1))
    home_score = int(score_match.group(2))

    game_stats = json.loads(json_text)

    return away_score, home_score, game_stats


def add_numeric_stats(old_stats, new_stats):
    for key, value in new_stats.items():
        if isinstance(value, dict):
            if key not in old_stats:
                old_stats[key] = {}
            add_numeric_stats(old_stats[key], value)
        elif isinstance(value, (int, float)):
            old_stats[key] = old_stats.get(key, 0) + value


def find_verified_user(stats_json, player_data):
    roblox_name = player_data.get("other", {}).get("name")
    display_name = player_data.get("other", {}).get("display")

    for discord_id, data in stats_json.items():
        users = data.get("users", [])

        if roblox_name in users or display_name in users:
            return discord_id

    return None


def get_team_emoji(guild, teams_json, team_name):
    for saved_team, data in teams_json.items():
        role = guild.get_role(data.get("role_id"))

        if role and role.name == team_name:
            return data.get("emoji", "")

        if saved_team == team_name:
            return data.get("emoji", "")

    return ""


class StatsDropdown(discord.ui.Select):
    def __init__(self, game_stats, teams_json):
        self.game_stats = game_stats
        self.teams_json = teams_json

        options = [
            discord.SelectOption(label="QB", value="qb"),
            discord.SelectOption(label="RB", value="rb"),
            discord.SelectOption(label="WR", value="wr"),
            discord.SelectOption(label="DB", value="db"),
            discord.SelectOption(label="DEF", value="def"),
            discord.SelectOption(label="Kicker", value="k")
        ]

        super().__init__(
            placeholder="View Stats",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        category = self.values[0]

        stats_json = load_json_file("stats.json")

        embed = discord.Embed(
            title=f"{CATEGORY_NAMES[category]} Stats",
            color=discord.Color.blue()
        )

        found_any = False

        for player_id, player_data in self.game_stats.items():
            cat_stats = player_data.get(category, {})

            if not cat_stats:
                continue

            if all(value == 0 for value in cat_stats.values() if isinstance(value, (int, float))):
                continue

            found_any = True

            other = player_data.get("other", {})
            display = other.get("display", "Unknown")
            username = other.get("name", "Unknown")
            team_name = other.get("team", "No Team")

            emoji = get_team_emoji(interaction.guild, self.teams_json, team_name)

            verified_id = find_verified_user(stats_json, player_data)

            verified_text = ""
            if not verified_id:
                verified_text = " **THIS USER ISNT VERIFIED**"

            stat_lines = []

            for stat, value in cat_stats.items():
                stat_lines.append(f"**{stat}:** {value}")

            embed.add_field(
                name=f"{emoji} {display} ({username}){verified_text}",
                value="\n".join(stat_lines),
                inline=False
            )

        if not found_any:
            embed.description = "No stats found for this category."

        await interaction.response.send_message(embed=embed, ephemeral=True)


class StatsView(discord.ui.View):
    def __init__(self, game_stats, teams_json):
        super().__init__(timeout=None)
        self.add_item(StatsDropdown(game_stats, teams_json))


class ScoreReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="scorereport", description="Report a game score and stats")
    async def scorereport(
        self,
        interaction: discord.Interaction,
        stats_file: discord.Attachment,
        home_team: discord.Role,
        away_team: discord.Role
    ):

        raw_bytes = await stats_file.read()
        raw_text = raw_bytes.decode("utf-8")

        try:
            away_score, home_score, game_stats = parse_score_file(raw_text)
        except Exception as e:
            await interaction.response.send_message(
                f"Could not read stats file: {e}",
                ephemeral=True
            )
            return

        stats_json = load_json_file("stats.json")
        teams_json = load_json_file("teams.json")

        for player_id, player_data in game_stats.items():
            verified_id = find_verified_user(stats_json, player_data)

            if verified_id:
                if "game_stats" not in stats_json[verified_id]:
                    stats_json[verified_id]["game_stats"] = {}

                add_numeric_stats(stats_json[verified_id]["game_stats"], player_data)

        save_json_file("stats.json", stats_json)

        home_won = home_score > away_score
        away_won = away_score > home_score

        home_score_text = f"**{home_score}**" if home_won else str(home_score)
        away_score_text = f"**{away_score}**" if away_won else str(away_score)

        embed = discord.Embed(
            title="Score Report",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Matchup",
            value=f"{away_team.mention} @ {home_team.mention}",
            inline=False
        )

        embed.add_field(
            name="Score",
            value=f"{away_team.mention}: {away_score_text}\n{home_team.mention}: {home_score_text}",
            inline=False
        )

        embed.add_field(
            name="Referee",
            value="None listed",
            inline=True
        )

        embed.add_field(
            name="Streamer",
            value="None listed",
            inline=True
        )

        stats_channel = self.bot.get_channel(STATS_CHANNEL)

        if not stats_channel:
            await interaction.response.send_message(
                "Stats channel not found.",
                ephemeral=True
            )
            return

        view = StatsView(game_stats, teams_json)

        await stats_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "Score report posted and verified stats updated.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ScoreReport(bot))
