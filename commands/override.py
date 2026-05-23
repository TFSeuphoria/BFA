import discord
from discord.ext import commands
from discord import app_commands
import json
import os

from rolesData import COMMISSIONER_ROLE
from channelsData import DECISIONS_CHANNEL


def load_json_file(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump({}, f)

    with open(path, "r") as f:
        return json.load(f)


def save_json_file(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=4)


def subtract_stats(existing, old_stats):

    for key, value in old_stats.items():

        if isinstance(value, dict):

            if key not in existing:
                existing[key] = {}

            subtract_stats(existing[key], value)

        elif isinstance(value, (int, float)):
            existing[key] = existing.get(key, 0) - value


class Override(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="override",
        description="Override a reported game"
    )
    @app_commands.choices(
        keep_stats=[
            app_commands.Choice(name="Yes", value="Yes"),
            app_commands.Choice(name="No", value="No")
        ]
    )
    async def override(
        self,
        interaction: discord.Interaction,
        game_id: str,
        home_score: int,
        away_score: int,
        reason: str,
        keep_stats: app_commands.Choice[str]
    ):

        if not any(
            r.id == COMMISSIONER_ROLE
            for r in interaction.user.roles
        ):
            await interaction.response.send_message(
                "Only commissioners can use this.",
                ephemeral=True
            )
            return

        games_json = load_json_file("games.json")
        records_json = load_json_file("records.json")
        stats_json = load_json_file("stats.json")

        if game_id not in games_json:
            await interaction.response.send_message(
                "Invalid game ID.",
                ephemeral=True
            )
            return

        game = games_json[game_id]

        old_home_score = game["home_team"]["score"]
        old_away_score = game["away_team"]["score"]

        home_team_id = str(game["home_team"]["id"])
        away_team_id = str(game["away_team"]["id"])

        records_json[home_team_id]["points_for"] -= old_home_score
        records_json[home_team_id]["points_against"] -= old_away_score

        records_json[away_team_id]["points_for"] -= old_away_score
        records_json[away_team_id]["points_against"] -= old_home_score

        if old_home_score > old_away_score:
            records_json[home_team_id]["wins"] -= 1
            records_json[away_team_id]["losses"] -= 1

        elif old_away_score > old_home_score:
            records_json[away_team_id]["wins"] -= 1
            records_json[home_team_id]["losses"] -= 1

        records_json[home_team_id]["points_for"] += home_score
        records_json[home_team_id]["points_against"] += away_score

        records_json[away_team_id]["points_for"] += away_score
        records_json[away_team_id]["points_against"] += home_score

        if home_score > away_score:
            records_json[home_team_id]["wins"] += 1
            records_json[away_team_id]["losses"] += 1

        elif away_score > home_score:
            records_json[away_team_id]["wins"] += 1
            records_json[home_team_id]["losses"] += 1

        if keep_stats.value == "No":

            old_stats = game.get("stats", {})

            for player_id, player_data in old_stats.items():

                roblox_name = player_data.get(
                    "other",
                    {}
                ).get("name")

                display_name = player_data.get(
                    "other",
                    {}
                ).get("display")

                verified_id = None

                for discord_id, data in stats_json.items():

                    users = data.get("users", [])

                    if (
                        roblox_name in users
                        or display_name in users
                    ):
                        verified_id = discord_id
                        break

                if verified_id:

                    if "game_stats" in stats_json[verified_id]:

                        subtract_stats(
                            stats_json[verified_id]["game_stats"],
                            player_data
                        )

            game["stats"] = {}

        game["home_team"]["score"] = home_score
        game["away_team"]["score"] = away_score

        save_json_file("games.json", games_json)
        save_json_file("records.json", records_json)
        save_json_file("stats.json", stats_json)

        home_team = interaction.guild.get_role(
            int(home_team_id)
        )

        away_team = interaction.guild.get_role(
            int(away_team_id)
        )

        embed = discord.Embed(
            title=f"Game {game_id} Overridden",
            color=discord.Color.orange()
        )

        embed.add_field(
            name="Matchup",
            value=f"{away_team.mention} @ {home_team.mention}",
            inline=False
        )

        embed.add_field(
            name="New Score",
            value=(
                f"{away_team.mention}: {away_score}\n"
                f"{home_team.mention}: {home_score}"
            ),
            inline=False
        )

        embed.add_field(
            name="Keep Stats",
            value=keep_stats.value,
            inline=False
        )

        embed.add_field(
            name="Reason",
            value=reason,
            inline=False
        )

        embed.add_field(
            name="Overridden By",
            value=interaction.user.mention,
            inline=False
        )

        decisions_channel = self.bot.get_channel(
            DECISIONS_CHANNEL
        )

        if decisions_channel:
            await decisions_channel.send(embed=embed)

        await interaction.response.send_message(
            f"Game #{game_id} overridden.",
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Override(bot))
