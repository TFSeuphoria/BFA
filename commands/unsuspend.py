import discord
from discord.ext import commands
from discord import app_commands

from rolesData import (
    COMMISSIONER_ROLE,
    SUSPENDED_ROLE
)

from channelsData import DECISIONS_CHANNEL


class Unsuspend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="unsuspend", description="Unsuspend a user")
    async def unsuspend(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        suspended_role = interaction.guild.get_role(SUSPENDED_ROLE)

        if not suspended_role:
            await interaction.response.send_message(
                "Suspended role not found.",
                ephemeral=True
            )
            return

        if suspended_role not in user.roles:
            await interaction.response.send_message(
                "That user is not suspended.",
                ephemeral=True
            )
            return

        await user.remove_roles(suspended_role)

        embed = discord.Embed(
            title="User Unsuspended",
            color=discord.Color.green()
        )

        embed.add_field(
            name="Unsuspended User",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Unsuspended By",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

        decisions_channel = self.bot.get_channel(DECISIONS_CHANNEL)

        if decisions_channel:
            await decisions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Unsuspended {user.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Unsuspend(bot))
