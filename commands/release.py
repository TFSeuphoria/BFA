import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COACHING_ROLES
from channelsData import TRANSACTIONS_CHANNEL


class Release(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="release", description="Release a user from your team")
    async def release(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):

        if not any(r.id in COACHING_ROLES for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only team staff can use this.",
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

        staff_team_role = None

        for team_name, data in teams.items():
            team_role = interaction.guild.get_role(data["role_id"])

            if team_role and team_role in interaction.user.roles:
                staff_team_role = team_role
                break

        if not staff_team_role:
            await interaction.response.send_message(
                "You are not on a registered team.",
                ephemeral=True
            )
            return

        if staff_team_role not in user.roles:
            await interaction.response.send_message(
                "That user is not on your team.",
                ephemeral=True
            )
            return

        await user.remove_roles(staff_team_role)

        team_count = len([
            member for member in interaction.guild.members
            if staff_team_role in member.roles
        ])

        try:
            await user.send(
                f"You have been released from **{staff_team_role.name}** by **{interaction.user}**."
            )
        except:
            pass

        embed = discord.Embed(
            title="Player Released",
            color=discord.Color.red()
        )

        embed.add_field(name="Released User", value=user.mention, inline=False)
        embed.add_field(name="Team", value=staff_team_role.mention, inline=False)
        embed.add_field(name="Released By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Team Members", value=str(team_count), inline=False)

        transactions_channel = self.bot.get_channel(TRANSACTIONS_CHANNEL)

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Released {user.mention} from {staff_team_role.mention}"
        )


async def setup(bot):
    await bot.add_cog(Release(bot))
