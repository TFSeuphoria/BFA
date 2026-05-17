import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    FRANCHISE_OWNER_ROLE,
    COACHING_ROLES
)

from channelsData import TRANSACTIONS_CHANNEL


class Demote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="demote",
        description="Demote a team staff member"
    )
    async def demote(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):

        if not any(r.id == FRANCHISE_OWNER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only franchise owners can use this.",
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

        owner_team_role = None

        for team_name, data in teams.items():
            team_role = interaction.guild.get_role(data["role_id"])

            if team_role and team_role in interaction.user.roles:
                owner_team_role = team_role
                break

        if not owner_team_role:
            await interaction.response.send_message(
                "You are not assigned to a team.",
                ephemeral=True
            )
            return

        if owner_team_role not in user.roles:
            await interaction.response.send_message(
                "That user is not on your team.",
                ephemeral=True
            )
            return

        roles_to_remove = [
            role for role in user.roles
            if role.id in COACHING_ROLES
        ]

        if not roles_to_remove:
            await interaction.response.send_message(
                "That user has no coach roles.",
                ephemeral=True
            )
            return

        await user.remove_roles(*roles_to_remove)

        embed = discord.Embed(
            title="Staff Demotion",
            color=discord.Color.red()
        )

        embed.add_field(name="Demoted User", value=user.mention, inline=False)
        embed.add_field(name="Team", value=owner_team_role.mention, inline=False)
        embed.add_field(name="Demoted By", value=interaction.user.mention, inline=False)

        transactions_channel = self.bot.get_channel(TRANSACTIONS_CHANNEL)

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Demoted {user.mention}"
        )


async def setup(bot):
    await bot.add_cog(Demote(bot))
