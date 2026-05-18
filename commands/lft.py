import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COACHING_ROLES
from channelsData import FREE_AGENTS_CHANNEL


class LFTView(discord.ui.View):
    def __init__(self, player_id):
        super().__init__(timeout=None)
        self.player_id = player_id

    @discord.ui.button(label="Send a Message", style=discord.ButtonStyle.green)
    async def send_message(self, interaction: discord.Interaction, button: discord.ui.Button):

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

        coach_team_role = None

        for team_name, data in teams.items():
            team_role = interaction.guild.get_role(data["role_id"])

            if team_role and team_role in interaction.user.roles:
                coach_team_role = team_role
                break

        if not coach_team_role:
            await interaction.response.send_message(
                "You are not on a registered team.",
                ephemeral=True
            )
            return

        player = interaction.guild.get_member(self.player_id)

        thread = await interaction.channel.create_thread(
            name=f"{interaction.user.name}-to-{player.name if player else self.player_id}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        await thread.send(
            f"{interaction.user.mention} {player.mention if player else f'<@{self.player_id}>'}\n"
            f"{interaction.user.mention} is a coach on {coach_team_role.mention}."
        )

        await interaction.response.send_message(
            "Private thread created.",
            ephemeral=True
        )


class LFT(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="lft", description="Post that you are looking for a team")
    async def lft(
        self,
        interaction: discord.Interaction,
        offensive_position: str,
        defensive_position: str,
        experience: str
    ):

        if not os.path.exists("teams.json"):
            await interaction.response.send_message(
                "teams.json not found.",
                ephemeral=True
            )
            return

        with open("teams.json", "r") as f:
            teams = json.load(f)

        for team_name, data in teams.items():
            team_role = interaction.guild.get_role(data["role_id"])

            if team_role and team_role in interaction.user.roles:
                await interaction.response.send_message(
                    "You are already on a team.",
                    ephemeral=True
                )
                return

        free_agents_channel = self.bot.get_channel(FREE_AGENTS_CHANNEL)

        if not free_agents_channel:
            await interaction.response.send_message(
                "Free agents channel not found.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Looking For Team",
            color=discord.Color.blue()
        )

        embed.add_field(name="Player", value=interaction.user.mention, inline=False)
        embed.add_field(name="Offensive Position", value=offensive_position, inline=False)
        embed.add_field(name="Defensive Position", value=defensive_position, inline=False)
        embed.add_field(name="Experience", value=experience, inline=False)

        view = LFTView(interaction.user.id)

        await free_agents_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "LFT post sent.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(LFT(bot))
