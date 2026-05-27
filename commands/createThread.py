import discord
from discord.ext import commands
from discord import app_commands

from rolesData import (
    COMMISSIONER_ROLE,
    REFEREE_ROLE,
    STREAMER_ROLE
)


class CreateThread(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="createthread",
        description="Create a private game thread"
    )
    @app_commands.choices(
        primetime=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ]
    )
    async def createthread(
        self,
        interaction: discord.Interaction,
        primetime: app_commands.Choice[str],
        deadline: str
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        thread = await interaction.channel.create_thread(
            name=f"Game Thread - {deadline}",
            type=discord.ChannelType.private_thread,
            invitable=False
        )

        content = f"**Schedule Deadline:** {deadline}"

        if primetime.value == "Yes":
            content += f"\n<@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>"

        await thread.send(content)

        await interaction.response.send_message(
            f"Created private thread: {thread.mention}",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(CreateThread(bot))
