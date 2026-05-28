import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    COMMISSIONER_ROLE,
    FRANCHISE_OWNER_ROLE,
    REFEREE_ROLE,
    STREAMER_ROLE
)


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def find_franchise_owner(guild, team_role_id):
    for member in guild.members:
        if any(r.id == team_role_id for r in member.roles) and any(r.id == FRANCHISE_OWNER_ROLE for r in member.roles):
            return member
    return None


class CreateThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createthread", description="Create a private game thread")
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
        primetime: app_commands.Choice[str],
        deadline: str
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message("Only commissioners can use this.", ephemeral=True)
            return

        teams_json = load_json("teams.json")
        valid_team_ids = [data.get("role_id") for data in teams_json.values()]

        if team1.id not in valid_team_ids or team2.id not in valid_team_ids:
            await interaction.response.send_message("Both roles must be registered teams.", ephemeral=True)
            return

        thread = await interaction.channel.create_thread(
            name=f"{team1.name} vs {team2.name}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        team1_owner = find_franchise_owner(interaction.guild, team1.id)
        team2_owner = find_franchise_owner(interaction.guild, team2.id)

        content = (
            f"{team1.mention} {team2.mention}\n"
            f"**Schedule Deadline:** {deadline}"
        )

        if team1_owner:
            content += f"\n{team1_owner.mention}"

        if team2_owner:
            content += f"\n{team2_owner.mention}"

        if primetime.value == "Yes":
            content += f"\n<@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>"

        await thread.send(content)

        await interaction.response.send_message(
            f"Created private thread: {thread.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(CreateThread(bot))
