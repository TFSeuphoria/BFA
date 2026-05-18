import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    FRANCHISE_OWNER_ROLE,
    GENERAL_MANAGER_ROLE,
    HEAD_COACH_ROLE,
    ASSISTANT_COACH_ROLE
)


class Roster(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="roster", description="View a team's roster")
    async def roster(
        self,
        interaction: discord.Interaction,
        team: discord.Role
    ):

        if not os.path.exists("teams.json"):
            await interaction.response.send_message(
                "teams.json not found.",
                ephemeral=True
            )
            return

        with open("teams.json", "r") as f:
            teams = json.load(f)

        valid_team_ids = [data["role_id"] for data in teams.values()]

        if team.id not in valid_team_ids:
            await interaction.response.send_message(
                "That role is not a registered team.",
                ephemeral=True
            )
            return

        members = [member for member in interaction.guild.members if team in member.roles]

        def get_staff(staff_role_id):
            staff_role = interaction.guild.get_role(staff_role_id)

            if not staff_role:
                return "None"

            staff_members = [
                member.mention for member in members
                if staff_role in member.roles
            ]

            return "\n".join(staff_members) if staff_members else "None"

        players = [
            member.mention for member in members
            if not any(role.id in [
                FRANCHISE_OWNER_ROLE,
                GENERAL_MANAGER_ROLE,
                HEAD_COACH_ROLE,
                ASSISTANT_COACH_ROLE
            ] for role in member.roles)
        ]

        embed = discord.Embed(
            title=f"{team.name} Roster",
            color=team.color
        )

        embed.add_field(
            name="Franchise Owner",
            value=get_staff(FRANCHISE_OWNER_ROLE),
            inline=False
        )

        embed.add_field(
            name="General Manager",
            value=get_staff(GENERAL_MANAGER_ROLE),
            inline=False
        )

        embed.add_field(
            name="Head Coach",
            value=get_staff(HEAD_COACH_ROLE),
            inline=False
        )

        embed.add_field(
            name="Assistant Coach",
            value=get_staff(ASSISTANT_COACH_ROLE),
            inline=False
        )

        embed.add_field(
            name="Players",
            value="\n".join(players) if players else "None",
            inline=False
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Roster(bot))
