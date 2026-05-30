import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE


def load_json(path, default=None):
    if default is None:
        default = {}

    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump(default, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def add_value(container, category, stat, amount):
    if category not in container:
        container[category] = {}

    container[category][stat] = container[category].get(stat, 0) + amount


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

    return current


def ensure_player(data, user_id, users=None):
    user_id = str(user_id)

    if user_id not in data:
        data[user_id] = {
            "users": users or [],
            "game_stats": {},
            "games_played": 0
        }

    if "users" not in data[user_id]:
        data[user_id]["users"] = users or []

    if "game_stats" not in data[user_id]:
        data[user_id]["game_stats"] = {}

    if "games_played" not in data[user_id]:
        data[user_id]["games_played"] = 0


class StatAdd(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="statadd",
        description="Manually add stats to a verified user"
    )
    async def statadd(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        passing_tds: int,
        passing_yards: int,
        picks_thrown: int,
        completions_thrown: int,
        total_passes: int,
        sacks_taken: int,
        rushing_yards: int,
        rushing_tds: int,
        rushing_attempts: int,
        receiving_yards: int,
        receiving_tds: int,
        picks_allowed: int,
        catches: int,
        targets: int,
        tackles: int,
        sacks: int,
        tackles_missed: int,
        completions_allowed: int,
        picks_caught: int,
        passes_swatted: int,
        kicks_made: int,
        kicks_attempted: int
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        stats_json = load_json("stats.json")

        user_id = str(user.id)

        if user_id not in stats_json or not stats_json[user_id].get("users"):
            await interaction.response.send_message(
                "That user is not verified.",
                ephemeral=True
            )
            return

        seasons_json = load_json(
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
        season_players = seasons_json["seasons"][current_season]["players"]

        ensure_player(
            stats_json,
            user_id,
            stats_json[user_id].get("users", [])
        )

        ensure_player(
            season_players,
            user_id,
            stats_json[user_id].get("users", [])
        )

        all_time_stats = stats_json[user_id]["game_stats"]
        season_stats = season_players[user_id]["game_stats"]

        inc = max(total_passes - completions_thrown, 0)

        stat_map = {
            "qb": {
                "td": passing_tds,
                "yds": passing_yards,
                "int": picks_thrown,
                "comp": completions_thrown,
                "inc": inc,
                "sack": sacks_taken
            },
            "rb": {
                "yds": rushing_yards,
                "td": rushing_tds,
                "att": rushing_attempts
            },
            "wr": {
                "yds": receiving_yards,
                "td": receiving_tds,
                "int_allow": picks_allowed,
                "catch": catches,
                "tgt": targets
            },
            "def": {
                "tack": tackles,
                "sack": sacks,
                "miss": tackles_missed
            },
            "db": {
                "catch_allow": completions_allowed,
                "int": picks_caught,
                "defl": passes_swatted
            },
            "k": {
                "good": kicks_made,
                "att": kicks_attempted
            }
        }

        for category, stats in stat_map.items():
            for stat, amount in stats.items():
                if amount != 0:
                    add_value(all_time_stats, category, stat, amount)
                    add_value(season_stats, category, stat, amount)

        stats_json[user_id]["games_played"] += 1
        season_players[user_id]["games_played"] += 1

        save_json("stats.json", stats_json)
        save_json("seasons.json", seasons_json)

        embed = discord.Embed(
            title="Stats Added",
            color=discord.Color.green()
        )

        embed.add_field(
            name="User",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Season",
            value=current_season,
            inline=True
        )

        embed.add_field(
            name="Games Played Added",
            value="+1",
            inline=True
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(StatAdd(bot))
