import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

from rolesData import COACHING_ROLES
from channelsData import TRANSACTIONS_CHANNEL


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def get_team_emoji(team_role_id):
    teams_json = load_json("teams.json")

    for team_name, data in teams_json.items():
        if data.get("role_id") == team_role_id:
            return data.get("emoji", "")

    return ""


def set_embed_emoji_thumbnail(embed, emoji):
    emoji_match = re.search(r"<a?:.+:(\d+)>", emoji)

    if emoji_match:
        emoji_id = emoji_match.group(1)
        extension = "gif" if emoji.startswith("<a:") else "png"

        embed.set_thumbnail(
            url=f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"
        )


class OfferButtons(discord.ui.View):
    def __init__(self, bot, coach, player, team_role):
        super().__init__(timeout=600)

        self.bot = bot
        self.coach = coach
        self.player = player
        self.team_role = team_role

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "This offer is not for you.",
                ephemeral=True
            )
            return

        await self.player.add_roles(self.team_role)

        try:
            await self.coach.send(
                f"{self.player} accepted the offer to {self.team_role.name}."
            )
        except:
            pass

        team_emoji = get_team_emoji(self.team_role.id)

        embed = discord.Embed(
            title="Contract Offer Accepted",
            color=discord.Color.green()
        )

        set_embed_emoji_thumbnail(embed, team_emoji)

        embed.add_field(
            name="Player",
            value=self.player.mention,
            inline=False
        )

        embed.add_field(
            name="Team",
            value=f"{team_emoji} {self.team_role.mention}",
            inline=False
        )

        embed.add_field(
            name="Offered By",
            value=self.coach.mention,
            inline=False
        )

        embed.add_field(
            name="Team Members",
            value=str(len(self.team_role.members)),
            inline=False
        )

        transactions_channel = self.bot.get_channel(TRANSACTIONS_CHANNEL)

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"You accepted the offer to {self.team_role.name}.",
            view=self
        )

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if interaction.user.id != self.player.id:
            await interaction.response.send_message(
                "This offer is not for you.",
                ephemeral=True
            )
            return

        try:
            await self.coach.send(
                f"{self.player} declined the offer to {self.team_role.name}."
            )
        except:
            pass

        for child in self.children:
            child.disabled = True

        await interaction.response.edit_message(
            content=f"You declined the offer to {self.team_role.name}.",
            view=self
        )


class Offer(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="offer",
        description="Offer a player a contract"
    )
    async def offer(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):

        if not any(role.id in COACHING_ROLES for role in interaction.user.roles):
            await interaction.response.send_message(
                "You are not team staff.",
                ephemeral=True
            )
            return

        teams_json = load_json("teams.json")

        team_role = None

        for team_name, data in teams_json.items():
            role = interaction.guild.get_role(data.get("role_id"))

            if role and role in interaction.user.roles:
                team_role = role
                break

        if not team_role:
            await interaction.response.send_message(
                "Could not determine your team.",
                ephemeral=True
            )
            return

        for team_name, data in teams_json.items():
            role = interaction.guild.get_role(data.get("role_id"))

            if role and role in user.roles:
                await interaction.response.send_message(
                    "That user is already on a team.",
                    ephemeral=True
                )
                return

        view = OfferButtons(
            self.bot,
            interaction.user,
            user,
            team_role
        )

        try:
            await user.send(
                f"{interaction.user} has offered you a contract to {team_role.name}.",
                view=view
            )

        except:
            await interaction.response.send_message(
                "Could not DM that user.",
                ephemeral=True
            )
            return

        await interaction.response.send_message(
            f"Sent contract offer to {user.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Offer(bot))
