import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE, REFEREE_ROLE, STREAMER_ROLE
from channelsData import SCHEDULE_CHANNEL


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

    return wins, losses, pf, pa, pd, win_pct


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
    teams = sort_teams(teams)

    for index, team in enumerate(teams, start=1):
        team["seed"] = index

    matchups = []

    for i in range(0, len(teams), 2):
        if i + 1 >= len(teams):
            matchups.append({"team1": teams[i], "team2": None, "primetime": False})
        else:
            matchups.append({
                "team1": teams[i],
                "team2": teams[i + 1],
                "primetime": i in [0, 2]
            })

    return matchups


def team_line(team):
    return (
        f"#{team['seed']} {team['emoji']} {team['mention']} "
        f"`{team['wins']}-{team['losses']}` PD: `{team['pd']}`"
    )


def make_schedule_embed(matchups, deadline, league_name):
    embed = discord.Embed(
        title=f"{league_name} Schedule",
        color=discord.Color.blue()
    )

    embed.add_field(name="Deadline", value=deadline, inline=False)

    lines = []

    for matchup in matchups:
        team1 = matchup["team1"]
        team2 = matchup["team2"]

        if team2 is None:
            lines.append(f"{team_line(team1)}\n**BYE**")
            continue

        text = f"{team_line(team1)}\nvs\n{team_line(team2)}"

        if matchup["primetime"]:
            text = f"⭐ **PRIMETIME** ⭐\n**{text}**"

        lines.append(text)

    embed.description = "\n\n".join(lines) if lines else "No teams found."
    return embed


class CreateThreadsView(discord.ui.View):
    def __init__(self, matchups):
        super().__init__(timeout=None)
        self.matchups = matchups
        self.created = False

    @discord.ui.button(label="Create Threads", style=discord.ButtonStyle.green)
    async def create_threads(self, interaction: discord.Interaction, button: discord.ui.Button):

        if not any(r.id == COMMISSIONER_ROLE for r in interaction.user.roles):
            await interaction.response.send_message(
                "Only commissioners can create threads.",
                ephemeral=True
            )
            return

        if self.created:
            await interaction.response.send_message(
                "Threads were already created for this schedule.",
                ephemeral=True
            )
            return

        self.created = True
        button.disabled = True

        created_count = 0

        for index, matchup in enumerate(self.matchups, start=1):
            team1 = matchup["team1"]
            team2 = matchup["team2"]

            if team2 is None:
                continue

            thread = await interaction.channel.create_thread(
                name=f"Game {index} - {team1['name']} vs {team2['name']}",
                type=discord.ChannelType.private_thread,
                invitable=False
            )

            content = f"{team1['mention']} {team2['mention']}"

            if matchup["primetime"]:
                content += f" <@&{REFEREE_ROLE}> <@&{STREAMER_ROLE}>"

            await thread.send(content)
            created_count += 1

        await interaction.response.edit_message(view=self)

        await interaction.followup.send(
            f"Created {created_count} matchup threads.",
            ephemeral=True
        )


class CreateSchedule(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="createschedule", description="Create an auto-generated schedule")
    async def createschedule(
        self,
        interaction: discord.Interaction,
        deadline: str
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

            wins, losses, pf, pa, pd, win_pct = get_record(records_json, role_id)

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
                "win_pct": win_pct
            })

        matchups = build_matchups(teams)
        embed = make_schedule_embed(matchups, deadline, interaction.guild.name)

        schedule_channel = self.bot.get_channel(SCHEDULE_CHANNEL)

        if not schedule_channel:
            await interaction.response.send_message(
                "Schedule channel not found.",
                ephemeral=True
            )
            return

        await schedule_channel.send(
            embed=embed,
            view=CreateThreadsView(matchups)
        )

        await interaction.response.send_message(
            f"Schedule sent to {schedule_channel.mention}.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(CreateSchedule(bot))
