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


class Release(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="release",
        description="Release a player from your team"
    )
    async def release(
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

        coach_team_role = None

        for team_name, data in teams_json.items():
            role = interaction.guild.get_role(data.get("role_id"))

            if role and role in interaction.user.roles:
                coach_team_role = role
                break

        if not coach_team_role:
            await interaction.response.send_message(
                "Could not determine your team.",
                ephemeral=True
            )
            return

        if coach_team_role not in user.roles:
            await interaction.response.send_message(
                "That user is not on your team.",
                ephemeral=True
            )
            return

        await user.remove_roles(coach_team_role)

        try:
            await user.send(
                f"You have been released from **{coach_team_role.name}** by {interaction.user}."
            )
        except:
            pass

        team_emoji = get_team_emoji(coach_team_role.id)

        embed = discord.Embed(
            title="Player Released",
            color=discord.Color.red()
        )

        set_embed_emoji_thumbnail(embed, team_emoji)

        embed.add_field(
            name="Player",
            value=user.mention,
            inline=False
        )

        embed.add_field(
            name="Team",
            value=f"{team_emoji} {coach_team_role.mention}",
            inline=False
        )

        embed.add_field(
            name="Released By",
            value=interaction.user.mention,
            inline=False
        )

        embed.add_field(
            name="Team Members",
            value=str(len(coach_team_role.members)),
            inline=False
        )

        transactions_channel = self.bot.get_channel(
            TRANSACTIONS_CHANNEL
        )

        if transactions_channel:
            await transactions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Released {user.mention} from {coach_team_role.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Release(bot))
