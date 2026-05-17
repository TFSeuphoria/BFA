import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    COMMISSIONER_ROLE,
    FRANCHISE_OWNER_ROLE
)

from channelsData import DECISIONS_CHANNEL


class Appoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="appoint",
        description="Appoint a franchise owner to a team"
    )
    async def appoint(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
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
                "That role is not a registered team.",
                ephemeral=True
            )
            return

        franchise_owner_role = interaction.guild.get_role(FRANCHISE_OWNER_ROLE)

        await user.add_roles(role)

        if franchise_owner_role:
            await user.add_roles(franchise_owner_role)

        await interaction.response.send_message(
            f"Appointed {user.mention} to {role.mention}"
        )

        embed = discord.Embed(
            title="New Appointment",
            color=discord.Color.green()
        )

        embed.add_field(
            name="User",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Team",
            value=role.mention,
            inline=False
        )

        embed.add_field(
            name="Appointed By",
            value=interaction.user.mention,
            inline=False
        )

        decisions_channel = self.bot.get_channel(DECISIONS_CHANNEL)

        if decisions_channel:
            await decisions_channel.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Appoint(bot))
