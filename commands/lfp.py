import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COACHING_ROLES
from channelsData import FREE_AGENTS_CHANNEL


class LFPView(discord.ui.View):
    def __init__(self, coach_id, team_role_id):
        super().__init__(timeout=None)
        self.coach_id = coach_id
        self.team_role_id = team_role_id

    @discord.ui.button(label="Send Message", style=discord.ButtonStyle.green)
    async def send_message(self, interaction: discord.Interaction, button: discord.ui.Button):

        coach = interaction.guild.get_member(self.coach_id)
        team_role = interaction.guild.get_role(self.team_role_id)

        thread_name = f"{interaction.user.name}-interest"

        thread = await interaction.channel.create_thread(
            name=thread_name,
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        await thread.send(
            f"{coach.mention if coach else '<@' + str(self.coach_id) + '>'} "
            f"{interaction.user.mention}\n"
            f"{interaction.user.mention} is interested in joining "
            f"{team_role.mention if team_role else 'this team'}."
        )

        await interaction.response.send_message(
            "Private thread created.",
            ephemeral=True
        )


class LFP(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="lfp",
        description="Post a looking for player message"
    )
    async def lfp(
        self,
        interaction: discord.Interaction,
        offensive_position: str,
        defensive_position: str,
        server_link: str = None
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

        free_agents_channel = self.bot.get_channel(FREE_AGENTS_CHANNEL)

        if not free_agents_channel:
            await interaction.response.send_message(
                "Free agents channel not found.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="Looking For Player",
            color=discord.Color.blue()
        )

        embed.add_field(
            name="Team",
            value=coach_team_role.mention,
            inline=False
        )

        embed.add_field(
            name="Offensive Position",
            value=offensive_position,
            inline=False
        )

        embed.add_field(
            name="Defensive Position",
            value=defensive_position,
            inline=False
        )

        embed.add_field(
            name="Coach",
            value=interaction.user.mention,
            inline=False
        )

        if server_link:
            embed.add_field(
                name="Server Link",
                value=server_link,
                inline=False
            )

        view = LFPView(interaction.user.id, coach_team_role.id)

        await free_agents_channel.send(embed=embed, view=view)

        await interaction.response.send_message(
            "LFP post sent.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(LFP(bot))
