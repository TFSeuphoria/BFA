import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE


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


class SetSeason(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="setseason", description="Set the current season")
    async def setseason(
        self,
        interaction: discord.Interaction,
        number: int
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        if number < 1:
            await interaction.response.send_message(
                "Season number must be 1 or higher.",
                ephemeral=True
            )
            return

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

        if "seasons" not in seasons_json:
            seasons_json["seasons"] = {}

        season_id = str(number)

        if season_id not in seasons_json["seasons"]:
            seasons_json["seasons"][season_id] = {
                "players": {},
                "records": {}
            }

        seasons_json["current_season"] = season_id

        save_json_file("seasons.json", seasons_json)

        await interaction.response.send_message(
            f"Current season set to Season {season_id}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(SetSeason(bot))
