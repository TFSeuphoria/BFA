import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

from rolesData import (
    FRANCHISE_OWNER_ROLE,
    COACHING_ROLES
)

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


class Demand(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="demand", description="Demand out of your team")
    async def demand(self, interaction: discord.Interaction):

        if any(r.id == FRANCHISE_OWNER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Franchise owners cannot demand.",
                ephemeral=True
            )
            return

        teams_json = load_json("teams.json")

        user_team_role = None

        for team_name, data in teams_json.items():
            team_role = interaction.guild.get_role(data.get("role_id"))

            if team_role and team_role in interaction.user.roles:
                user_team_role = team_role
                break

        if not user_team_role:
            await interaction.response.send_message(
                "You are not on a team.",
                ephemeral=True
            )
            return

        team_staff = [
            member for member in interaction.guild.members
            if user_team_role in member.roles
            and any(role.id in COACHING_ROLES for role in member.roles)
        ]

        for staff in team_staff:
            try:
                await staff.send(
                    f"{interaction.user.mention} has demanded out of **{user_team_role.name}**."
                )
            except:
                pass

        await interaction.user.remove_roles(user_team_role)

        team_emoji = get_team_emoji(user_team_role.id)

        embed = discord.Embed(
            title="Player Demand",
            color=discord.Color.orange()
        )

        set_embed_emoji_thumbnail(embed, team_emoji)

        embed.add_field(name="Player", value=interaction.user.mention, inline=False)
        embed.add_field(name="Team", value=f"{team_emoji} {user_team_role.mention}", inline=False)

        transactions_channel = self.bot.get_channel(TRANSACTIONS_CHANNEL)

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"You have demanded out of {user_team_role.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Demand(bot))
