import discord
from discord.ext import commands
from discord import app_commands
import json
import os


class Verify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="verify", description="Verify your league username")
    async def verify(self, interaction: discord.Interaction):

        stats_file = "stats.json"
        discord_id = str(interaction.user.id)
        league_user = interaction.user.display_name

        if not os.path.exists(stats_file):
            with open(stats_file, "w") as f:
                json.dump({}, f)

        with open(stats_file, "r") as f:
            stats = json.load(f)

        for saved_discord_id, data in stats.items():
            users = data.get("users", [])

            if league_user in users and saved_discord_id != discord_id:
                owner = interaction.guild.get_member(int(saved_discord_id))
                owner_text = owner.mention if owner else f"<@{saved_discord_id}>"

                await interaction.response.send_message(
                    f"`{league_user}` is already verified to {owner_text}.",
                    ephemeral=True
                )
                return

        if discord_id not in stats:
            stats[discord_id] = {
                "users": []
            }

        if league_user in stats[discord_id]["users"]:
            await interaction.response.send_message(
                f"`{league_user}` is already verified to you.",
                ephemeral=True
            )
            return

        stats[discord_id]["users"].append(league_user)

        with open(stats_file, "w") as f:
            json.dump(stats, f, indent=4)

        await interaction.response.send_message(
            f"Verified `{league_user}` to your account.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Verify(bot))
