import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import (
    COACHING_ROLES,
    REFEREE_ROLE,
    STREAMER_ROLE
)

from channelsData import GAMETIMES_CHANNEL


class GametimeView(discord.ui.View):
    def __init__(self, bot, embed, referee_id=None, streamer_id=None):
        super().__init__(timeout=None)
        self.bot = bot
        self.embed = embed
        self.referee_id = referee_id
        self.streamer_id = streamer_id

    def update_embed(self):
        self.embed.set_field_at(
            4,
            name="Referee",
            value=f"<@{self.referee_id}>" if self.referee_id else "None",
            inline=False
        )

        self.embed.set_field_at(
            5,
            name="Streamer",
            value=f"<@{self.streamer_id}>" if self.streamer_id else "None",
            inline=False
        )

    @discord.ui.button(label="Claim Referee", style=discord.ButtonStyle.blurple)
    async def claim_referee(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not any(role.id == REFEREE_ROLE for role in interaction.user.roles):
            await interaction.response.send_message(
                "You do not have the referee role.",
                ephemeral=True
            )
            return

        if self.referee_id is None:
            self.referee_id = interaction.user.id
        elif self.referee_id == interaction.user.id:
            self.referee_id = None
        else:
            await interaction.response.send_message(
                "This game already has a referee.",
                ephemeral=True
            )
            return

        self.update_embed()

        await interaction.response.edit_message(
            embed=self.embed,
            view=self
        )

    @discord.ui.button(label="Claim Streamer", style=discord.ButtonStyle.green)
    async def claim_streamer(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not any(role.id == STREAMER_ROLE for role in interaction.user.roles):
            await interaction.response.send_message(
                "You do not have the streamer role.",
                ephemeral=True
            )
            return

        if self.streamer_id is None:
            self.streamer_id = interaction.user.id
        elif self.streamer_id == interaction.user.id:
            self.streamer_id = None
        else:
            await interaction.response.send_message(
                "This game already has a streamer.",
                ephemeral=True
            )
            return

        self.update_embed()

        await interaction.response.edit_message(
            embed=self.embed,
            view=self
        )


class Gametime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gametime", description="Schedule a game")
    @app_commands.choices(
        forced=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ],
        date=[
            app_commands.Choice(name="Today", value="Today"),
            app_commands.Choice(name="Tomorrow", value="Tomorrow"),
            app_commands.Choice(name="In 2 days", value="In 2 days"),
            app_commands.Choice(name="In 3 days", value="In 3 days")
        ]
    )
    async def gametime(
        self,
        interaction: discord.Interaction,
        time: str,
        team1: discord.Role,
        team2: discord.Role,
        forced: app_commands.Choice[str],
        date: app_commands.Choice[str]
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

        valid_team_ids = [data["role_id"] for data in teams.values()]

        if team1.id not in valid_team_ids or team2.id not in valid_team_ids:
            await interaction.response.send_message(
                "Both roles must be registered teams.",
                ephemeral=True
            )
            return

        user_team_ids = [role.id for role in interaction.user.roles]

        if team1.id not in user_team_ids and team2.id not in user_team_ids:
            await interaction.response.send_message(
                "One of the teams must be your team.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Game Scheduled",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Matchup",
            value=f"{team1.mention} vs {team2.mention}",
            inline=False
        )

        embed.add_field(
            name="Time",
            value=time,
            inline=False
        )

        embed.add_field(
            name="Date",
            value=date.value,
            inline=False
        )

        embed.add_field(
            name="Forced",
            value=forced.value,
            inline=False
        )

        embed.add_field(
            name="Referee",
            value="None",
            inline=False
        )

        embed.add_field(
            name="Streamer",
            value="None",
            inline=False
        )

        embed.add_field(
            name="Scheduled By",
            value=interaction.user.mention,
            inline=False
        )

        view = GametimeView(self.bot, embed)

        gametimes_channel = self.bot.get_channel(GAMETIMES_CHANNEL)

        if not gametimes_channel:
            await interaction.response.send_message(
                "Gametimes channel not found.",
                ephemeral=True
            )
            return

        message = await gametimes_channel.send(
            content=f"<@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>",
            embed=embed,
            view=view
        )

        for member in interaction.guild.members:
            if (
                (team1 in member.roles or team2 in member.roles)
                and any(role.id in COACHING_ROLES for role in member.roles)
            ):
                try:
                    await member.send(
                        f"A gametime has been set:\n"
                        f"{team1.name} vs {team2.name}\n"
                        f"Date: {date.value}\n"
                        f"Time: {time}\n"
                        f"Forced: {forced.value}"
                    )
                except:
                    pass

        await interaction.response.send_message(
            "Gametime posted.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Gametime(bot))
