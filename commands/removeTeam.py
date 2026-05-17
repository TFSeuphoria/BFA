import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE

class RemoveTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="removeteam", description="Remove a team")
    async def removeteam(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "No permission.",
                ephemeral=True
            )
            return

        if not os.path.exists("teams.json"):
            await interaction.response.send_message(
                "teams.json not found.",
                ephemeral=True
            )
            return

        with open("teams.json", "r") as f:
            teams = json.load(f)

        if role.name not in teams:
            await interaction.response.send_message(
                "That team does not exist.",
                ephemeral=True
            )
            return

        del teams[role.name]

        with open("teams.json", "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message(
            f"Removed {role.name}"
        )

async def setup(bot):
    await bot.add_cog(RemoveTeam(bot))
