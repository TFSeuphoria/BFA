import discord
from discord.ext import commands
from discord import app_commands
import json
import os


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
    games_played = wins + losses
    win_pct = wins / games_played if games_played > 0 else 0

    return wins, losses, pf, pa, pd, games_played, win_pct


def sort_teams(team_list):
    return sorted(
        team_list,
        key=lambda x: (
            x["wins"],
            x["win_pct"],
            x["pd"],
            x["name"].lower()
        ),
        reverse=True
    )


def build_divisions(teams):
    teams = sort_teams(teams)

    total = len(teams)
    d1_size = total // 2

    division_1 = teams[:d1_size]
    division_2 = teams[d1_size:]

    return division_1, division_2


def make_embed(division_name, division_teams):
    embed = discord.Embed(
        title=f"{division_name} Standings",
        color=discord.Color.blue()
    )

    if not division_teams:
        embed.description = "No teams found."
        return embed

    lines = []

    for index, team in enumerate(division_teams, start=1):
        lines.append(
            f"**#{index}** {team['emoji']} {team['mention']} "
            f"`{team['wins']}-{team['losses']}` | "
            f"Win%: `{team['win_pct']:.3f}` | "
            f"PF: `{team['pf']}` | PA: `{team['pa']}` | PD: `{team['pd']}`"
        )

    embed.description = "\n".join(lines)

    return embed


class StandingsDropdown(discord.ui.Select):
    def __init__(self, division_1, division_2):
        self.division_1 = division_1
        self.division_2 = division_2

        options = [
            discord.SelectOption(label="Division 1", value="division_1"),
            discord.SelectOption(label="Division 2", value="division_2")
        ]

        super().__init__(
            placeholder="View division",
            min_values=1,
            max_values=1,
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "division_1":
            embed = make_embed("Division 1", self.division_1)
        else:
            embed = make_embed("Division 2", self.division_2)

        await interaction.response.edit_message(
            embed=embed,
            view=self.view
        )


class StandingsView(discord.ui.View):
    def __init__(self, division_1, division_2):
        super().__init__(timeout=300)
        self.add_item(StandingsDropdown(division_1, division_2))


class ViewStandings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="viewstandings",
        description="View league standings"
    )
    async def viewstandings(self, interaction: discord.Interaction):

        teams_json = load_json("teams.json")
        records_json = load_json("records.json")

        all_teams = []

        for team_name, data in teams_json.items():
            role_id = data.get("role_id")
            emoji = data.get("emoji", "")

            role = interaction.guild.get_role(role_id)

            if not role:
                continue

            wins, losses, pf, pa, pd, games_played, win_pct = get_record(records_json, role_id)

            all_teams.append({
                "role_id": role_id,
                "name": role.name,
                "mention": role.mention,
                "emoji": emoji,
                "wins": wins,
                "losses": losses,
                "pf": pf,
                "pa": pa,
                "pd": pd,
                "games_played": games_played,
                "win_pct": win_pct
            })

        division_1, division_2 = build_divisions(all_teams)

        await interaction.response.send_message(
            embed=make_embed("Division 1", division_1),
            view=StandingsView(division_1, division_2),
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(ViewStandings(bot))
