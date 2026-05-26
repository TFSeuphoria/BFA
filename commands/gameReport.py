import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from channelsData import STATS_CHANNEL
from rolesData import COACHING_ROLES


FFW_SCORE = 14
FFL_SCORE = 0


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def ensure_record(records, team_id):
    team_id = str(team_id)

    if team_id not in records:
        records[team_id] = {
            "wins": 0,
            "losses": 0,
            "points_for": 0,
            "points_against": 0
        }


def update_record(records, team_id, points_for, points_against, won):
    team_id = str(team_id)

    ensure_record(records, team_id)

    records[team_id]["points_for"] += points_for
    records[team_id]["points_against"] += points_against

    if won:
        records[team_id]["wins"] += 1
    else:
        records[team_id]["losses"] += 1


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

    if "records" not in seasons_json["seasons"][current]:
        seasons_json["seasons"][current]["records"] = {}

    if "players" not in seasons_json["seasons"][current]:
        seasons_json["seasons"][current]["players"] = {}

    return current


class GameReport(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="gamereport",
        description="Report a forfeit win/loss game"
    )
    async def gamereport(
        self,
        interaction: discord.Interaction,
        photo: discord.Attachment,
        your_team: discord.Role,
        opponent_team: discord.Role
    ):

        if not any(role.id in COACHING_ROLES for role in interaction.user.roles):
            await interaction.response.send_message(
                "Only team staff can use this.",
                ephemeral=True
            )
            return

        teams_json = load_json("teams.json")

        valid_team_ids = [
            data.get("role_id")
            for data in teams_json.values()
        ]

        if your_team.id not in valid_team_ids or opponent_team.id not in valid_team_ids:
            await interaction.response.send_message(
                "Both teams must be registered teams.",
                ephemeral=True
            )
            return

        if your_team not in interaction.user.roles:
            await interaction.response.send_message(
                "Your team must be the team you are on.",
                ephemeral=True
            )
            return

        if not photo.content_type or not photo.content_type.startswith("image/"):
            await interaction.response.send_message(
                "Please upload an image/photo.",
                ephemeral=True
            )
            return

        records_json = load_json("records.json")
        games_json = load_json("games.json")
        seasons_json = load_json(
            "seasons.json"
        )

        current_season = ensure_seasons_json(seasons_json)
        season_records = seasons_json["seasons"][current_season]["records"]

        game_id = str(len(games_json) + 1)

        update_record(
            records_json,
            your_team.id,
            FFW_SCORE,
            FFL_SCORE,
            True
        )

        update_record(
            records_json,
            opponent_team.id,
            FFL_SCORE,
            FFW_SCORE,
            False
        )

        update_record(
            season_records,
            your_team.id,
            FFW_SCORE,
            FFL_SCORE,
            True
        )

        update_record(
            season_records,
            opponent_team.id,
            FFL_SCORE,
            FFW_SCORE,
            False
        )

        games_json[game_id] = {
            "season": current_season,
            "type": "forfeit",
            "home_team": {
                "id": your_team.id,
                "score": FFW_SCORE
            },
            "away_team": {
                "id": opponent_team.id,
                "score": FFL_SCORE
            },
            "ffw_team": your_team.id,
            "ffl_team": opponent_team.id,
            "stats": {},
            "photo_url": photo.url
        }

        save_json("records.json", records_json)
        save_json("games.json", games_json)
        save_json("seasons.json", seasons_json)

        embed = discord.Embed(
            title=f"Game #{game_id} | Season {current_season}",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Result",
            value=(
                f"{your_team.mention} FFWed\n"
                f"{opponent_team.mention} FFLed"
            ),
            inline=False
        )

        embed.add_field(
            name="Score",
            value=(
                f"{your_team.mention}: **{FFW_SCORE}**\n"
                f"{opponent_team.mention}: {FFL_SCORE}"
            ),
            inline=False
        )

        embed.add_field(
            name="Reported By",
            value=interaction.user.mention,
            inline=False
        )

        embed.set_image(url=photo.url)

        stats_channel = self.bot.get_channel(STATS_CHANNEL)

        if not stats_channel:
            await interaction.response.send_message(
                "Stats channel not found.",
                ephemeral=True
            )
            return

        await stats_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Game #{game_id} reported as FFW/FFL.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(GameReport(bot))
