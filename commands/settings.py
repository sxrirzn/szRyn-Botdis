
import discord
from discord import app_commands
from discord.ext import commands

import json
from pathlib import Path


CONFIG_FILE = Path(__file__).resolve().parent.parent / "config.json"


def load_config():
    if CONFIG_FILE.exists():
        with CONFIG_FILE.open("r", encoding="utf-8") as file:
            return json.load(file)

    return {}


def save_config(config):
    with CONFIG_FILE.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=4)


class SetGroup(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="set",
            description="Bot settings"
        )

    @app_commands.command(
        name="greet",
        description="Configure greet settings"
    )
    async def greet(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = load_config()

        guild_id = str(interaction.guild.id)

        if guild_id not in config:
            config[guild_id] = {}

        config[guild_id]["greet_channel"] = channel.id

        save_config(config)

        await interaction.response.send_message(
            f"Greet channel has been set to {channel.mention}!",
            ephemeral=True
        )


async def setup(bot):
    bot.tree.add_command(SetGroup())
