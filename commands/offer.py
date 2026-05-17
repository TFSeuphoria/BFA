import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COACHING_ROLES
from channelsData import TRANSACTIONS_CHANNEL


class OfferView(discord.ui.View):
    def __init__(self, bot, guild_id, user_id, coach_id, team_role_id):
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.user_id = user_id
        self.coach_id = coach_id
        self.team_role_id = team_role_id

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This offer is not for you.", ephemeral=True)
            return

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        coach = guild.get_member(self.coach_id)
        team_role = guild.get_role(self.team_role_id)

        if not guild or not member or not team_role:
            await interaction.response.send_message("Something went wrong.", ephemeral=True)
            return

        await member.add_roles(team_role)

        team_count = len([m for m in guild.members if team_role in m.roles])

        if coach:
            try:
                await coach.send(f"{member.mention} accepted the offer from {team_role.name}.")
            except:
                pass

        embed = discord.Embed(
            title="Offer Accepted",
            color=discord.Color.green()
        )

        embed.add_field(name="Player", value=member.mention, inline=False)
        embed.add_field(name="Team", value=team_role.mention, inline=False)
        embed.add_field(name="Offered By", value=coach.mention if coach else "Unknown", inline=False)
        embed.add_field(name="Team Members", value=str(team_count), inline=False)

        transactions_channel = self.bot.get_channel(TRANSACTIONS_CHANNEL)

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"You accepted the offer from {team_role.name}.",
            ephemeral=True
        )

        self.clear_items()
        await interaction.message.edit(view=self)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):

        if interaction.user.id != self.user_id:
            await interaction.response.send_message("This offer is not for you.", ephemeral=True)
            return

        guild = self.bot.get_guild(self.guild_id)
        member = guild.get_member(self.user_id)
        coach = guild.get_member(self.coach_id)
        team_role = guild.get_role(self.team_role_id)

        if coach:
            try:
                await coach.send(f"{member.mention} declined the offer from {team_role.name}.")
            except:
                pass

        await interaction.response.send_message(
            f"You declined the offer from {team_role.name}.",
            ephemeral=True
        )

        self.clear_items()
        await interaction.message.edit(view=self)


class Offer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="offer", description="Offer a player to join your team")
    async def offer(
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

        for team_name, data in teams.items():
            team_role = interaction.guild.get_role(data["role_id"])

            if team_role and team_role in user.roles:
                await interaction.response.send_message(
                    "That user is already on a team.",
                    ephemeral=True
                )
                return

        view = OfferView(
            self.bot,
            interaction.guild.id,
            user.id,
            interaction.user.id,
            coach_team_role.id
        )

        try:
            await user.send(
                f"You have been offered by **{coach_team_role.name}**.\n"
                f"Offered by: **{interaction.user}**\n\n"
                f"Click **Accept** to join or **Decline** to reject.",
                view=view
            )
        except:
            await interaction.response.send_message(
                "I could not DM that user.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Offer sent to {user.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Offer(bot))
