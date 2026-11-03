import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="Show bot commands and instructions"
    )
    async def help_command(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="Bot Help",
            description="Here are the available commands.",
            color=discord.Color.from_rgb(178, 134, 223)
        )

        embed.add_field(
            name="/embed create",
            value=(
                "Create a new embed template.\n"
                "• **NAME:** Enter `greet` to create the greet embed template."
            ),
            inline=False
        )

        embed.add_field(
            name="/set greet",
            value="Set the bot’s message channel.",
            inline=False
        )
        
        embed.add_field(
            name="/test greet",
            value="Test the greet embed template.",
            inline=False
        )

        embed.add_field(
            name="/help",
            value="Show this help menu.",
            inline=False
        )

        embed.set_footer(text="Bot Help Menu")

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(Help(bot))