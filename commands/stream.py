import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import STREAMER_ROLE
from channelsData import STREAMS_CHANNEL


class Stream(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="stream", description="Post a game stream")
    @app_commands.choices(
        primetime=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ]
    )
    async def stream(
        self,
        interaction: discord.Interaction,
        link: str,
        platform: str,
        team1: discord.Role,
        team2: discord.Role,
        primetime: app_commands.Choice[str]
    ):

        if not any(r.id == STREAMER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only streamers can use this.",
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

        valid_team_ids = [data["role_id"] for data in teams.values()]

        if team1.id not in valid_team_ids or team2.id not in valid_team_ids:
            await interaction.response.send_message(
                "Both roles must be registered teams.",
                ephemeral=True
            )
            return

        streams_channel = self.bot.get_channel(STREAMS_CHANNEL)

        if not streams_channel:
            await interaction.response.send_message(
                "Streams channel not found.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Game Stream",
            color=discord.Color.purple()
        )

        embed.add_field(
            name="Streamer",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Matchup",
            value=f"{team1.mention} vs {team2.mention}",
            inline=False
        )

        embed.add_field(
            name="Platform",
            value=platform,
            inline=False
        )

        embed.add_field(
            name="Primetime",
            value=primetime.value,
            inline=False
        )

        embed.add_field(
            name="Stream Link",
            value=link,
            inline=False
        )

        ping = "@everyone" if primetime.value == "Yes" else "@here"

        await streams_channel.send(
            content=ping,
            embed=embed
        )

        await interaction.response.send_message(
            "Stream post sent.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Stream(bot))
