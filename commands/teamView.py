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


class TeamView(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="teamview", description="View a team")
    async def teamview(
        self,
        interaction: discord.Interaction,
        role: discord.Role
    ):

        if not os.path.exists("teams.json"):
            await interaction.response.send_message("teams.json not found.", ephemeral=True)
            return

        with open("teams.json", "r") as f:
            teams = json.load(f)

        team_data = None

        for team_name, data in teams.items():
            if data["role_id"] == role.id:
                team_data = data
                break

        if not team_data:
            await interaction.response.send_message("That role is not a registered team.", ephemeral=True)
            return

        records = {}

        if os.path.exists("records.json"):
            with open("records.json", "r") as f:
                records = json.load(f)

        record_data = records.get(str(role.id), {
            "wins": 0,
            "losses": 0,
            "points_for": 0,
            "points_against": 0
        })

        wins = record_data["wins"]
        losses = record_data["losses"]
        points_for = record_data["points_for"]
        points_against = record_data["points_against"]
        point_diff = points_for - points_against

        def find_staff(staff_role_id):
            staff_role = interaction.guild.get_role(staff_role_id)

            if not staff_role:
                return "None"

            for member in interaction.guild.members:
                if role in member.roles and staff_role in member.roles:
                    return member.mention

            return "None"

        franchise_owner = find_staff(FRANCHISE_OWNER_ROLE)
        general_manager = find_staff(GENERAL_MANAGER_ROLE)
        head_coach = find_staff(HEAD_COACH_ROLE)
        assistant_coach = find_staff(ASSISTANT_COACH_ROLE)

        embed = discord.Embed(
            title=f"{team_data.get('emoji', '')} {role.name}",
            color=role.color
        )

        embed.add_field(name="Franchise Owner", value=franchise_owner, inline=False)
        embed.add_field(name="General Manager", value=general_manager, inline=False)
        embed.add_field(name="Head Coach", value=head_coach, inline=False)
        embed.add_field(name="Assistant Coach", value=assistant_coach, inline=False)
        embed.add_field(name="Record", value=f"{wins}-{losses}", inline=True)
        embed.add_field(name="Points For", value=str(points_for), inline=True)
        embed.add_field(name="Points Against", value=str(points_against), inline=True)
        embed.add_field(name="PD", value=str(point_diff), inline=True)

        await interaction.response.send_message(embed=embed)


async def setup(bot):
    await bot.add_cog(TeamView(bot))
