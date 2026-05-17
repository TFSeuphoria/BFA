import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE

class AddTeam(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="addteam", description="Add a team")
    async def addteam(
        self,
        interaction: discord.Interaction,
        role: discord.Role,
        emoji: str
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "No permission.",
                ephemeral=True
            )
            return

        if not os.path.exists("teams.json"):
            with open("teams.json", "w") as f:
                json.dump({}, f)

        with open("teams.json", "r") as f:
            teams = json.load(f)

        teams[role.name] = {
            "role_id": role.id,
            "emoji": emoji
        }

        with open("teams.json", "w") as f:
            json.dump(teams, f, indent=4)

        await interaction.response.send_message(
            f"Added {emoji} {role.name}"
        )

async def setup(bot):
    await bot.add_cog(AddTeam(bot))
