import discord
from discord.ext import commands
from discord import app_commands

from rolesData import (
    COMMISSIONER_ROLE,
    SUSPENDED_ROLE
)

from channelsData import DECISIONS_CHANNEL


class Suspend(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="suspend", description="Suspend a user")
    async def suspend(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        reason: str,
        bail: str,
        bail_end: str
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

        await user.add_roles(suspended_role)

        embed = discord.Embed(
            title="User Suspended",
            color=discord.Color.orange()
        )

        embed.add_field(name="Suspended User", value=user.mention, inline=False)
        embed.add_field(name="Suspended By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Bail", value=bail, inline=False)
        embed.add_field(name="Unsuspended", value=bail_end, inline=False)

        decisions_channel = self.bot.get_channel(DECISIONS_CHANNEL)

        if decisions_channel:
            await decisions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Suspended {user.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Suspend(bot))
