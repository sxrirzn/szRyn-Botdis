
import discord
from discord import app_commands
from discord.ext import commands

import os

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN not found. Please set the token first.")


# Bot Setup

class MyBot(commands.Bot):

   async def setup_hook(self):
    extensions = [
        "commands.help",
        "commands.embed",
        "commands.settings"
    ]

    for extension in extensions:
        await self.load_extension(extension)
        print(f"Loaded extension: {extension}")

    print("\n--- Registered Slash Commands ---")

    for command in self.tree.get_commands():
        if isinstance(command, app_commands.Group):
            print(f"Group: /{command.name}")

            for subcommand in command.commands:
                print(f"  Subcommand: /{command.name} {subcommand.name}")
        else:
            print(f"Command: /{command.name}")

    await self.tree.sync()
    print("\nSlash Commands Synced!")


bot = MyBot(
    command_prefix="!",
    intents=discord.Intents.default(),
    help_command=None
)


# Slash Command Error Handler

@bot.tree.error
async def on_app_command_error(
    interaction: discord.Interaction,
    error: app_commands.AppCommandError
):

    print(f"Slash Command Error: {error}")

    message = "An unexpected error occurred while executing this command."

    if interaction.response.is_done():
        await interaction.followup.send(
            message,
            ephemeral=True
        )
    else:
        await interaction.response.send_message(
            message,
            ephemeral=True
        )


# Bot Ready

@bot.event
async def on_ready():
    print(f"Bot Online! Logged in as {bot.user}")


# Run Bot

bot.run(TOKEN)
