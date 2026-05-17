import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    COMMISSIONER_ROLE,
    COACHING_ROLES
)

from channelsData import DECISIONS_CHANNEL


class Disband(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="disband", description="Disband a team")
    async def disband(
        self,
        interaction: discord.Interaction,
        team: discord.Role,
        reason: str
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

        if team.name not in teams:
            await interaction.response.send_message(
                "That role is not a registered team.",
                ephemeral=True
            )
            return

        members = [member for member in interaction.guild.members if team in member.roles]
        released_count = len(members)

        coaching_role_objects = [
            interaction.guild.get_role(role_id)
            for role_id in COACHING_ROLES
            if interaction.guild.get_role(role_id)
        ]

        await interaction.response.send_message(
            f"Disbanding {team.mention}...",
            ephemeral=True
        )

        for member in members:
            roles_to_remove = [team]

            for coach_role in coaching_role_objects:
                if coach_role in member.roles:
                    roles_to_remove.append(coach_role)

            try:
                await member.send(
                    f"Your team **{team.name}** has been disbanded.\n"
                    f"Reason: {reason}"
                )
            except:
                pass

            await member.remove_roles(*roles_to_remove)

        embed = discord.Embed(
            title="Team Disbanded",
            color=discord.Color.red()
        )

        embed.add_field(name="Team", value=team.mention, inline=False)
        embed.add_field(name="Disbanded By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Members Released", value=str(released_count), inline=False)

        decisions_channel = self.bot.get_channel(DECISIONS_CHANNEL)

        if decisions_channel:
            await decisions_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Disband(bot))
