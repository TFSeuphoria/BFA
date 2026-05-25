import discord
from discord.ext import commands
from discord import app_commands
import json
import os
import math

from rolesData import (
    COMMISSIONER_ROLE,
    REFEREE_ROLE,
    STREAMER_ROLE
)


def load_json(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f, indent=4)

    with open(path, "r") as f:
        return json.load(f)


def get_record(records, team_id):
    data = records.get(str(team_id), {
        "wins": 0,
        "losses": 0,
        "points_for": 0,
        "points_against": 0
    })

    wins = data.get("wins", 0)
    losses = data.get("losses", 0)
    pf = data.get("points_for", 0)
    pa = data.get("points_against", 0)
    pd = pf - pa
    games = wins + losses
    win_pct = wins / games if games > 0 else 0

    return wins, losses, pf, pa, pd, games, win_pct


def sort_teams(teams):
    return sorted(
        teams,
        key=lambda x: (
            x["wins"],
            x["win_pct"],
            x["pd"],
            x["name"].lower()
        ),
        reverse=True
    )


def build_matchups(teams):
    sorted_teams = sort_teams(teams)
    matchups = []

    for i in range(0, len(sorted_teams), 2):
        if i + 1 >= len(sorted_teams):
            matchups.append({
                "team1": sorted_teams[i],
                "team2": None,
                "primetime": False
            })
        else:
            matchups.append({
                "team1": sorted_teams[i],
                "team2": sorted_teams[i + 1],
                "primetime": i in [0, 2]
            })

    return matchups


def make_schedule_embed(matchups):
    embed = discord.Embed(
        title="Auto Generated Schedule",
        color=discord.Color.blue()
    )

    lines = []

    for index, matchup in enumerate(matchups, start=1):
        team1 = matchup["team1"]
        team2 = matchup["team2"]

        if team2 is None:
            line = (
                f"**Game {index}:** {team1['emoji']} {team1['mention']} "
                f"`{team1['wins']}-{team1['losses']}` | PD: `{team1['pd']}` "
                f"has a BYE"
            )
        else:
            line = (
                f"**Game {index}:** "
                f"#{team1['rank']} {team1['emoji']} {team1['mention']} "
                f"`{team1['wins']}-{team1['losses']}` PD: `{team1['pd']}` "
                f"vs "
                f"#{team2['rank']} {team2['emoji']} {team2['mention']} "
                f"`{team2['wins']}-{team2['losses']}` PD: `{team2['pd']}`"
            )

        if matchup["primetime"]:
            line = f"⭐ **PRIMETIME** ⭐\n**{line}**"

        lines.append(line)

    embed.description = "\n\n".join(lines) if lines else "No teams found."

    return embed


class CreateThreadsButton(discord.ui.View):
    def __init__(self, matchups):
        super().__init__(timeout=600)
        self.matchups = matchups
        self.created = False

    @discord.ui.button(label="Create Threads", style=discord.ButtonStyle.green)
    async def create_threads(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can create schedule threads.",
                ephemeral=True
            )
            return

        if self.created:
            await interaction.response.send_message(
                "Threads were already created.",
                ephemeral=True
            )
            return

        self.created = True

        created_count = 0

        for index, matchup in enumerate(self.matchups, start=1):
            team1 = matchup["team1"]
            team2 = matchup["team2"]

            if team2 is None:
                continue

            thread_name = f"Game {index} - {team1['name']} vs {team2['name']}"

            thread = await interaction.channel.create_thread(
                name=thread_name,
                type=discord.ChannelType.private_thread,
                invitable=False
            )

            content = f"{team1['mention']} {team2['mention']}"

            if matchup["primetime"]:
                content += f" <@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>"

            await thread.send(content)

            created_count += 1

        button.disabled = True

        await interaction.response.edit_message(view=self)

        await interaction.followup.send(
            f"Created {created_count} matchup threads.",
            ephemeral=True
        )


class CreateSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="createschedule",
        description="Auto generate a schedule from standings"
    )
    async def createschedule(
        self,
        interaction: discord.Interaction,
        channel_id: str = None
    ):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        teams_json = load_json("teams.json")
        records_json = load_json("records.json")

        teams = []

        for team_name, data in teams_json.items():
            role_id = data.get("role_id")
            emoji = data.get("emoji", "")

            role = interaction.guild.get_role(role_id)

            if not role:
                continue

            wins, losses, pf, pa, pd, games, win_pct = get_record(
                records_json,
                role_id
            )

            teams.append({
                "role_id": role_id,
                "name": role.name,
                "mention": role.mention,
                "emoji": emoji,
                "wins": wins,
                "losses": losses,
                "pf": pf,
                "pa": pa,
                "pd": pd,
                "games": games,
                "win_pct": win_pct
            })

        teams = sort_teams(teams)

        for index, team in enumerate(teams, start=1):
            team["rank"] = index

        matchups = build_matchups(teams)
        embed = make_schedule_embed(matchups)
        view = CreateThreadsButton(matchups)

        if channel_id:
            try:
                target_channel = self.bot.get_channel(int(channel_id))
            except:
                target_channel = None

            if not target_channel:
                await interaction.response.send_message(
                    "Invalid channel ID.",
                    ephemeral=True
                )
                return

            await target_channel.send(
                content="@everyone",
                embed=embed,
                view=view,
                allowed_mentions=discord.AllowedMentions(everyone=True)
            )

            await interaction.response.send_message(
                f"Schedule sent to {target_channel.mention}.",
                ephemeral=True
            )

        else:
            await interaction.response.send_message(
                embed=embed,
                view=view,
                ephemeral=True
            )


async def setup(bot):
    await bot.add_cog(CreateSchedule(bot))
