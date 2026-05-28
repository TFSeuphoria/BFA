import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COACHING_ROLES, REFEREE_ROLE, STREAMER_ROLE
from channelsData import GAMETIMES_CHANNEL, SCHEDULE_CHANNEL


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def get_user_team(guild, member):
    teams_json = load_json("teams.json")

    for team_name, data in teams_json.items():
        role = guild.get_role(data.get("role_id"))
        if role and role in member.roles:
            return role

    return None


def is_registered_team(role):
    teams_json = load_json("teams.json")
    return role.id in [data.get("role_id") for data in teams_json.values()]


def get_team_coaches(guild, team_role):
    return [
        member for member in guild.members
        if team_role in member.roles
        and any(role.id in COACHING_ROLES for role in member.roles)
    ]


async def find_game_thread(bot, guild, team1, team2):
    schedule_channel = bot.get_channel(SCHEDULE_CHANNEL)

    if not schedule_channel:
        return None

    threads = list(schedule_channel.threads)

    try:
        async for thread in schedule_channel.archived_threads(limit=50):
            threads.append(thread)
    except:
        pass

    for thread in threads:
        try:
            async for msg in thread.history(limit=20):
                content = msg.content
                if team1.mention in content and team2.mention in content:
                    return thread
        except:
            continue

    return None


async def send_gametime_post(bot, team1, team2, time, date, force, primetime, requested_by):
    gametimes_channel = bot.get_channel(GAMETIMES_CHANNEL)

    if not gametimes_channel:
        return

    embed = discord.Embed(
        title="Gametime Confirmed",
        color=discord.Color.green()
    )

    embed.add_field(name="Matchup", value=f"{team1.mention} vs {team2.mention}", inline=False)
    embed.add_field(name="Time", value=time, inline=True)
    embed.add_field(name="Date", value=date, inline=True)
    embed.add_field(name="Forced", value=force, inline=True)
    embed.add_field(name="Primetime", value=primetime, inline=True)
    embed.add_field(name="Requested By", value=requested_by.mention, inline=False)

    content = ""

    if primetime == "Yes":
        content = f"<@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>"

    await gametimes_channel.send(content=content, embed=embed)


async def dm_coaches(team1, team2, time, date, opponent_map, message_link=None):
    guild = team1.guild
    coaches = get_team_coaches(guild, team1) + get_team_coaches(guild, team2)

    for coach in coaches:
        opponent = opponent_map.get(coach.id)

        text = (
            f"Gametime confirmed.\n"
            f"Opponent: **{opponent.name if opponent else 'Unknown'}**\n"
            f"Date: **{date}**\n"
            f"Time: **{time}**"
        )

        if message_link:
            text += f"\nMessage: {message_link}"

        try:
            await coach.send(text)
        except:
            pass


class GametimeRequestView(discord.ui.View):
    def __init__(self, bot, team1, team2, time, date, primetime, requested_by):
        super().__init__(timeout=None)
        self.bot = bot
        self.team1 = team1
        self.team2 = team2
        self.time = time
        self.date = date
        self.primetime = primetime
        self.requested_by = requested_by
        self.used = False

    def is_opponent_coach(self, member):
        return (
            self.team2 in member.roles
            and any(role.id in COACHING_ROLES for role in member.roles)
        )

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.used:
            await interaction.response.send_message("This request was already answered.", ephemeral=True)
            return

        if not self.is_opponent_coach(interaction.user):
            await interaction.response.send_message("Only the opponent coaching staff can accept this.", ephemeral=True)
            return

        self.used = True

        for child in self.children:
            child.disabled = True

        await send_gametime_post(
            self.bot,
            self.team1,
            self.team2,
            self.time,
            self.date,
            "No",
            self.primetime,
            self.requested_by
        )

        await interaction.message.reply(
            f"{self.team1.mention} {self.team2.mention}\n"
            f"Gametime accepted and confirmed.\n"
            f"**Date:** {self.date}\n"
            f"**Time:** {self.time}"
        )

        opponent_map = {}

        for coach in get_team_coaches(interaction.guild, self.team1):
            opponent_map[coach.id] = self.team2

        for coach in get_team_coaches(interaction.guild, self.team2):
            opponent_map[coach.id] = self.team1

        await dm_coaches(
            self.team1,
            self.team2,
            self.time,
            self.date,
            opponent_map,
            interaction.message.jump_url
        )

        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="Decline", style=discord.ButtonStyle.red)
    async def decline(self, interaction: discord.Interaction, button: discord.ui.Button):

        if self.used:
            await interaction.response.send_message("This request was already answered.", ephemeral=True)
            return

        if not self.is_opponent_coach(interaction.user):
            await interaction.response.send_message("Only the opponent coaching staff can decline this.", ephemeral=True)
            return

        self.used = True

        for child in self.children:
            child.disabled = True

        await interaction.message.reply("This gametime request was declined.")
        await interaction.response.edit_message(view=self)


class Gametime(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="gametime", description="Request or force a gametime")
    @app_commands.choices(
        force=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ],
        primetime=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ],
        date=[
            app_commands.Choice(name="Today", value="Today"),
            app_commands.Choice(name="Tomorrow", value="Tomorrow"),
            app_commands.Choice(name="In 2 days", value="In 2 days"),
            app_commands.Choice(name="In 3 days", value="In 3 days")
        ]
    )
    async def gametime(
        self,
        interaction: discord.Interaction,
        time: str,
        force: app_commands.Choice[str],
        primetime: app_commands.Choice[str],
        opponent_team: discord.Role,
        date: app_commands.Choice[str]
    ):

        if not any(role.id in COACHING_ROLES for role in interaction.user.roles):
            await interaction.response.send_message(
                "Only team staff can use this.",
                ephemeral=True
            )
            return

        user_team = get_user_team(interaction.guild, interaction.user)

        if not user_team:
            await interaction.response.send_message(
                "Could not detect your team.",
                ephemeral=True
            )
            return

        if not is_registered_team(opponent_team):
            await interaction.response.send_message(
                "Opponent team must be a registered team.",
                ephemeral=True
            )
            return

        if opponent_team.id == user_team.id:
            await interaction.response.send_message(
                "You cannot set a gametime against your own team.",
                ephemeral=True
            )
            return

        thread = await find_game_thread(
            self.bot,
            interaction.guild,
            user_team,
            opponent_team
        )

        if not thread:
            await interaction.response.send_message(
                "Could not find the schedule thread for those teams.",
                ephemeral=True
            )
            return

        if force.value == "Yes":
            await send_gametime_post(
                self.bot,
                user_team,
                opponent_team,
                time,
                date.value,
                "Yes",
                primetime.value,
                interaction.user
            )

            await thread.send(
                f"{user_team.mention} {opponent_team.mention}\n"
                f"Gametime confirmed.\n"
                f"**Date:** {date.value}\n"
                f"**Time:** {time}"
            )

            opponent_map = {}

            for coach in get_team_coaches(interaction.guild, user_team):
                opponent_map[coach.id] = opponent_team

            for coach in get_team_coaches(interaction.guild, opponent_team):
                opponent_map[coach.id] = user_team

            await dm_coaches(
                user_team,
                opponent_team,
                time,
                date.value,
                opponent_map
            )

            await interaction.response.send_message(
                "Forced gametime confirmed.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="REQUESTED GAMETIME",
            color=discord.Color.blue()
        )

        embed.add_field(name="Requested By", value=interaction.user.mention, inline=False)
        embed.add_field(name="Requesting Team", value=user_team.mention, inline=True)
        embed.add_field(name="Opponent Team", value=opponent_team.mention, inline=True)
        embed.add_field(name="Date", value=date.value, inline=True)
        embed.add_field(name="Time", value=time, inline=True)
        embed.add_field(name="Primetime", value=primetime.value, inline=True)

        request_message = await thread.send(
            content=opponent_team.mention,
            embed=embed,
            view=GametimeRequestView(
                self.bot,
                user_team,
                opponent_team,
                time,
                date.value,
                primetime.value,
                interaction.user
            )
        )

        for coach in get_team_coaches(interaction.guild, opponent_team):
            try:
                await coach.send(
                    f"Gametime requested vs **{user_team.name}**.\n"
                    f"Date: **{date.value}**\n"
                    f"Time: **{time}**\n"
                    f"Message: {request_message.jump_url}"
                )
            except:
                pass

        await interaction.response.send_message(
            "Gametime request sent.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Gametime(bot))
