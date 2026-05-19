import discord
from discord.ext import commands
from discord import app_commands
import time

from rolesData import MEDIA_OWNER_ROLE


MEDIA_CATEGORY_ID = 1504748786579406958
COOLDOWN_SECONDS = 6 * 60 * 60

cooldowns = {}


class MediaPing(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="mediaping", description="Ping everyone for media")
    async def mediaping(self, interaction: discord.Interaction):

        if not any(r.id == MEDIA_OWNER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only media owners can use this.",
                ephemeral=True
            )
            return

        if not interaction.channel.category or interaction.channel.category.id != MEDIA_CATEGORY_ID:
            await interaction.response.send_message(
                "You can only use this in the media category.",
                ephemeral=True
            )
            return

        now = time.time()
        last_used = cooldowns.get(interaction.user.id, 0)

        if now - last_used < COOLDOWN_SECONDS:
            remaining = int(COOLDOWN_SECONDS - (now - last_used))
            hours = remaining // 3600
            minutes = (remaining % 3600) // 60

            await interaction.response.send_message(
                f"You can use this again in {hours}h {minutes}m.",
                ephemeral=True
            )
            return

        cooldowns[interaction.user.id] = now

        await interaction.response.send_message(
            "Check this out! @everyone",
            allowed_mentions=discord.AllowedMentions(everyone=True)
        )


async def setup(bot):
    await bot.add_cog(MediaPing(bot))
