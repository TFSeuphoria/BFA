import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE


class UpdateRecord(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="updaterecord",
        description="Update a team's record"
    )
    async def updaterecord(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        wins: int,
        losses: int,
        points_for: int,
        points_against: int
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        if not os.path.exists("records.json"):
            with open("records.json", "w") as f:
                json.dump({}, f)

        with open("records.json", "r") as f:
            records = json.load(f)

        records[str(role.id)] = {
            "wins": wins,
            "losses": losses,
            "points_for": points_for,
            "points_against": points_against
        }

        with open("records.json", "w") as f:
            json.dump(records, f, indent=4)

        await interaction.response.send_message(
            f"Updated record for {role.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(UpdateRecord(bot))
