import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import re

from rolesData import COMMISSIONER_ROLE


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def clean_text(text):
    return (
        str(text)
        .lower()
        .replace("@", "")
        .replace("(", "")
        .replace(")", "")
        .replace("_", "")
        .replace("-", "")
        .replace(".", "")
        .replace(" ", "")
    )


def extract_names(server_name):
    names = []

    names.append(server_name)

    match = re.search(r"(.+?)\s*\(@(.+?)\)", server_name)

    if match:
        display_name = match.group(1).strip()
        username = match.group(2).strip()

        names.append(display_name)
        names.append(username)

    final_names = []

    for name in names:
        if name and name not in final_names:
            final_names.append(name)

    return final_names


class ForceVerify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="forceverify",
        description="Force verify a user's league name"
    )
    async def forceverify(
        self,
        interaction: discord.Interaction,
        user: discord.Member
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        stats_json = load_json("stats.json")

        discord_id = str(user.id)
        server_name = user.display_name
        names_to_add = extract_names(server_name)

        for saved_discord_id, data in stats_json.items():
            saved_users = data.get("users", [])

            for saved_user in saved_users:
                for new_name in names_to_add:
                    if clean_text(saved_user) == clean_text(new_name) and saved_discord_id != discord_id:
                        owner = interaction.guild.get_member(int(saved_discord_id))
                        owner_text = owner.mention if owner else f"<@{saved_discord_id}>"

                        await interaction.response.send_message(
                            f"`{new_name}` is already verified to {owner_text}.",
                            ephemeral=True
                        )
                        return

        if discord_id not in stats_json:
            stats_json[discord_id] = {
                "users": []
            }

        added = []

        for name in names_to_add:
            already_saved = any(
                clean_text(existing) == clean_text(name)
                for existing in stats_json[discord_id].get("users", [])
            )

            if not already_saved:
                stats_json[discord_id]["users"].append(name)
                added.append(name)

        if not added:
            await interaction.response.send_message(
                f"{user.mention} already has that name verified.",
                ephemeral=True
            )
            return

        save_json("stats.json", stats_json)

        await interaction.response.send_message(
            f"Force verified {user.mention}: `{', '.join(added)}`",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ForceVerify(bot))
