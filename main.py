
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

intents = discord.Intents.default()
intents.members = True

bot = MyBot(
    command_prefix="!",
    intents=intents,
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


# Bot Events

@bot.event
async def on_ready():
    print(f"Bot Online! Logged in as {bot.user}")



@bot.event
async def on_member_join(member):

    config = load_config()

    guild_id = str(member.guild.id)

    channel_id = config.get(guild_id, {}).get("greet_channel")

    if not channel_id:
        print("Welcome channel has not been set.")
        return

    channel = bot.get_channel(int(channel_id))

    if channel is None:
        try:
            channel = await bot.fetch_channel(int(channel_id))
        except discord.NotFound:
            print("Welcome channel not found.")
            return

    if isinstance(channel, discord.TextChannel):
        try:
            await channel.send(
                f"Welcome {member.mention}!"
            )

            print(f"Welcome message sent to {channel.name}")

        except discord.Forbidden:
            print("Missing permission to send welcome message.")

        except discord.HTTPException as e:
            print(f"Welcome Event Error: {e}")


# Run Bot

bot.run(TOKEN)
