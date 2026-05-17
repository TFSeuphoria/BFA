import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    FRANCHISE_OWNER_ROLE,
    GENERAL_MANAGER_ROLE,
    HEAD_COACH_ROLE,
    ASSISTANT_COACH_ROLE,
    COACHING_ROLES
)

from channelsData import TRANSACTIONS_CHANNEL


PROMOTION_ROLES = {
    "general manager": GENERAL_MANAGER_ROLE,
    "head coach": HEAD_COACH_ROLE,
    "assistant coach": ASSISTANT_COACH_ROLE
}


class Promote(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="promote",
        description="Promote a user to a coaching role"
    )
    @app_commands.describe(
        rank="general manager, head coach, or assistant coach"
    )
    async def promote(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        rank: str
    ):

        if not any(r.id == FRANCHISE_OWNER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only franchise owners can use this.",
                ephemeral=True
            )
            return

        rank = rank.lower()

        if rank not in PROMOTION_ROLES:
            await interaction.response.send_message(
                "Invalid rank.",
                ephemeral=True
            )
            return

        target_role_id = PROMOTION_ROLES[rank]
        target_role = interaction.guild.get_role(target_role_id)

        if not target_role:
            await interaction.response.send_message(
                "That rank role was not found.",
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

        if any(r.id in COACHING_ROLES for r in user.roles):
            await interaction.response.send_message(
                "That user already has a coaching role.",
                ephemeral=True
            )
            return

        for member in interaction.guild.members:
            if owner_team_role not in member.roles:
                continue

            if target_role in member.roles:
                await interaction.response.send_message(
                    f"Your team already has a {rank}.",
                    ephemeral=True
                )
                return

        await user.add_roles(target_role)

        embed = discord.Embed(
            title="Staff Promotion",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Promoted User",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Rank",
            value=target_role.mention,
            inline=False
        )

        embed.add_field(
            name="Team",
            value=owner_team_role.mention,
            inline=False
        )

        embed.add_field(
            name="Promoted By",
            value=interaction.user.mention,
            inline=False
        )

        transactions_channel = self.bot.get_channel(TRANSACTIONS_CHANNEL)

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Promoted {user.mention} to {target_role.mention}"
        )


async def setup(bot):
    await bot.add_cog(Promote(bot))
