
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


def get_greet_embed(guild_id, member):
    config = load_config()

    guild_config = config.get(str(guild_id), {})

    template = (
        guild_config
        .get("embed_templates", {})
        .get("greet")
    )

    if not template:
        return None

    embed = discord.Embed.from_dict(template)

    def replace_placeholders(text):
        if text:
            text = text.replace("{USER_TAG}", member.mention)
            text = text.replace("{USER_NAME}", member.display_name)

        return text

    # Replace placeholders in title
    if embed.title:
        embed.title = replace_placeholders(embed.title)

    # Replace placeholders in description
    if embed.description:
        embed.description = replace_placeholders(embed.description)

    # Replace placeholders in author
    use_member_avatar = guild_config.get(
        "greet_author_avatar",
        False
    )

    print("Avatar setting:", use_member_avatar)
    print("Member avatar URL:", member.display_avatar.url)

    author_name = ""

    if embed.author:
        author_name = replace_placeholders(
            embed.author.name or ""
        )

    if use_member_avatar:
        embed.set_author(
            name=author_name or member.display_name,
            icon_url=member.display_avatar.url
        )

    elif embed.author:
        embed.set_author(
            name=author_name,
            icon_url=embed.author.icon_url
        )

    # Replace placeholders in footer
    if embed.footer and embed.footer.text:
        embed.set_footer(
            text=replace_placeholders(embed.footer.text),
            icon_url=embed.footer.icon_url
        )

    return embed


# /set commands

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



# /test commands

class TestGroup(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="test",
            description="Test bot features"
        )

    @app_commands.command(
        name="greet",
        description="Test the welcome message"
    )
    async def greet(
        self,
        interaction: discord.Interaction
    ):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        config = load_config()
        guild_id = str(interaction.guild.id)

        channel_id = config.get(guild_id, {}).get("greet_channel")

        if not channel_id:
            await interaction.response.send_message(
                "Welcome channel has not been set.",
                ephemeral=True
            )
            return

        channel = interaction.client.get_channel(int(channel_id))

        if channel is None:
            try:
                channel = await interaction.client.fetch_channel(
                    int(channel_id)
                )
            except discord.NotFound:
                await interaction.response.send_message(
                    "Welcome channel not found.",
                    ephemeral=True
                )
                return

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                "The configured channel is not a text channel.",
                ephemeral=True
            )
            return

        try:
            embed = get_greet_embed(
                interaction.guild.id,
                interaction.user
            )

            if embed is None:
                await interaction.response.send_message(
                    "Welcome embed has not been created.",
                    ephemeral=True
                )
                return

            await channel.send(
                content=interaction.user.mention,
                embed=embed
            )

            await interaction.response.send_message(
                f"Test embed sent to {channel.mention}!",
                ephemeral=True
            )

        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to send messages in that channel.",
                ephemeral=True
            )

        except discord.HTTPException as e:
            print(f"Test Greet Error: {e}")

            await interaction.response.send_message(
                "Failed to send welcome message.",
                ephemeral=True
            )


async def setup(bot):
    bot.tree.add_command(SetGroup())
    bot.tree.add_command(TestGroup())
