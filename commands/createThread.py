import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    COMMISSIONER_ROLE,
    REFEREE_ROLE,
    STREAMER_ROLE
)


class CreateThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="createthread",
        description="Create a private game thread"
    )
    @app_commands.choices(
        primetime=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ]
    )
    async def createthread(
        self,
        interaction: discord.Interaction,
        team1: discord.Role,
        team2: discord.Role,
        primetime: app_commands.Choice[str]
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
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

        valid_team_ids = [data["role_id"] for data in teams.values()]

        if team1.id not in valid_team_ids or team2.id not in valid_team_ids:
            await interaction.response.send_message(
                "Both roles must be registered teams.",
                ephemeral=True
            )
            return

        thread_name = f"{team1.name} vs {team2.name}"

        thread = await interaction.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        content = f"{team1.mention} {team2.mention}"

        if primetime.value == "Yes":
            content += f" <@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>"

        await thread.send(content)

        await interaction.response.send_message(
            f"Created private thread: {thread.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(CreateThread(bot))
