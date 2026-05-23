import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

from channelsData import STATS_CHANNEL
from rolesData import COACHING_ROLES


CATEGORY_NAMES = {
    "qb": "QB",
    "rb": "RB",
    "wr": "WR",
    "db": "DB",
    "def": "DEF",
    "k": "Kicker"
}


def load_json_file(path, default=None):
    if default is None:
        default = {}

    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def parse_score_file(raw_text):
    parts = raw_text.split("///", 1)

    if len(parts) != 2:
        raise ValueError("Invalid stat file format.")

    score_match = re.search(r"(\d+)\s*-\s*(\d+)", parts[0].strip())

    if not score_match:
        raise ValueError("Could not read score.")

    away_score = int(score_match.group(1))
    home_score = int(score_match.group(2))
    game_stats = json.loads(parts[1].strip())

    return away_score, home_score, game_stats


def add_stats(existing, new_stats):
    for key, value in new_stats.items():
        if isinstance(value, dict):
            if key not in existing:
                existing[key] = {}
            add_stats(existing[key], value)
        elif isinstance(value, (int, float)):
            existing[key] = existing.get(key, 0) + value


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


def ensure_record(records_json, team_id):
    team_id = str(team_id)

    if team_id not in records_json:
        records_json[team_id] = {
            "wins": 0,
            "losses": 0,
            "points_for": 0,
            "points_against": 0
        }


def update_record(records_json, team_id, points_for, points_against, won):
    team_id = str(team_id)

    ensure_record(records_json, team_id)

    records_json[team_id]["points_for"] += points_for
    records_json[team_id]["points_against"] += points_against

    if won is True:
        records_json[team_id]["wins"] += 1
    elif won is False:
        records_json[team_id]["losses"] += 1


def ensure_seasons_json(seasons_json):
    if "current_season" not in seasons_json:
        seasons_json["current_season"] = "1"

    if "seasons" not in seasons_json:
        seasons_json["seasons"] = {}

    current = str(seasons_json["current_season"])

    if current not in seasons_json["seasons"]:
        seasons_json["seasons"][current] = {
            "players": {},
            "records": {}
        }

    if "players" not in seasons_json["seasons"][current]:
        seasons_json["seasons"][current]["players"] = {}

    if "records" not in seasons_json["seasons"][current]:
        seasons_json["seasons"][current]["records"] = {}

    return current


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

        found = False

        for player_id, player_data in self.game_stats.items():
            cat_stats = player_data.get(category, {})

            if not cat_stats:
                continue

            if all(value == 0 for value in cat_stats.values() if isinstance(value, (int, float))):
                continue

            found = True

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

        if not found:
            embed.description = "No stats found."

        await interaction.response.send_message(embed=embed, ephemeral=True)


class StatsView(discord.ui.View):
    def __init__(self, game_stats, teams_json):
        super().__init__(timeout=None)
        self.add_item(StatsDropdown(game_stats, teams_json))


class ScoreReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="scorereport", description="Report a game")
    async def scorereport(
        self,
        interaction: discord.Interaction,
        stats_file: discord.Attachment,
        home_team: discord.Role,
        away_team: discord.Role
    ):

        if not any(r.id in COACHING_ROLES for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only team staff can use this.",
                ephemeral=True
            )
            return

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
        records_json = load_json_file("records.json")
        games_json = load_json_file("games.json")
        seasons_json = load_json_file(
            "seasons.json",
            {
                "current_season": "1",
                "seasons": {
                    "1": {
                        "players": {},
                        "records": {}
                    }
                }
            }
        )

        current_season = ensure_seasons_json(seasons_json)
        season_data = seasons_json["seasons"][current_season]
        season_players = season_data["players"]
        season_records = season_data["records"]

        game_id = str(len(games_json) + 1)

        away_won = away_score > home_score
        home_won = home_score > away_score

        update_record(records_json, away_team.id, away_score, home_score, True if away_won else False if home_won else None)
        update_record(records_json, home_team.id, home_score, away_score, True if home_won else False if away_won else None)

        update_record(season_records, away_team.id, away_score, home_score, True if away_won else False if home_won else None)
        update_record(season_records, home_team.id, home_score, away_score, True if home_won else False if away_won else None)

        for player_id, player_data in game_stats.items():
            verified_id = find_verified_user(stats_json, player_data)

            if verified_id:
                if "game_stats" not in stats_json[verified_id]:
                    stats_json[verified_id]["game_stats"] = {}

                add_stats(stats_json[verified_id]["game_stats"], player_data)

                if verified_id not in season_players:
                    season_players[verified_id] = {
                        "users": stats_json[verified_id].get("users", []),
                        "game_stats": {}
                    }

                if "game_stats" not in season_players[verified_id]:
                    season_players[verified_id]["game_stats"] = {}

                add_stats(season_players[verified_id]["game_stats"], player_data)

        games_json[game_id] = {
            "season": current_season,
            "home_team": {
                "id": home_team.id,
                "score": home_score
            },
            "away_team": {
                "id": away_team.id,
                "score": away_score
            },
            "stats": game_stats
        }

        save_json_file("records.json", records_json)
        save_json_file("stats.json", stats_json)
        save_json_file("seasons.json", seasons_json)
        save_json_file("games.json", games_json)

        away_score_text = f"**{away_score}**" if away_won else str(away_score)
        home_score_text = f"**{home_score}**" if home_won else str(home_score)

        embed = discord.Embed(
            title=f"Game #{game_id} | Season {current_season}",
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

        embed.add_field(name="Referee", value="None listed", inline=True)
        embed.add_field(name="Streamer", value="None listed", inline=True)

        stats_channel = self.bot.get_channel(STATS_CHANNEL)

        if not stats_channel:
            await interaction.response.send_message(
                "Stats channel not found.",
                ephemeral=True
            )
            return

        await stats_channel.send(
            embed=embed,
            view=StatsView(game_stats, teams_json)
        )

        await interaction.response.send_message(
            f"Game #{game_id} reported for Season {current_season}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ScoreReport(bot))
