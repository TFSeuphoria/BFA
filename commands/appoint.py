import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

from rolesData import (
    COMMISSIONER_ROLE,
    FRANCHISE_OWNER_ROLE
)

from channelsData import DECISIONS_CHANNEL


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


class Appoint(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="appoint",
        description="Appoint a franchise owner to a team"
    )
    async def appoint(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
        role: discord.Role
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "No permission.",
                ephemeral=True
            )
            return

        teams_json = load_json("teams.json")

        if role.name not in teams_json:
            await interaction.response.send_message(
                "That role is not a registered team.",
                ephemeral=True
            )
            return

        franchise_owner_role = interaction.guild.get_role(
            FRANCHISE_OWNER_ROLE
        )

        await user.add_roles(role)

        if franchise_owner_role:
            await user.add_roles(franchise_owner_role)

        try:
            await user.send(
                f"You have been appointed as Franchise Owner of **{role.name}** by **{interaction.user}**."
            )
        except:
            pass

        team_emoji = get_team_emoji(role.id)

        embed = discord.Embed(
            title="New Appointment",
            color=discord.Color.green()
        )

        set_embed_emoji_thumbnail(embed, team_emoji)

        embed.add_field(
            name="User",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Team",
            value=f"{team_emoji} {role.mention}",
            inline=False
        )

        embed.add_field(
            name="Appointed By",
            value=interaction.user.mention,
            inline=False
        )

        decisions_channel = self.bot.get_channel(
            DECISIONS_CHANNEL
        )

        if decisions_channel:
            await decisions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Appointed {user.mention} to {role.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Appoint(bot))
