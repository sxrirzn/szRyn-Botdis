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
            name="/reaction_role add",
            value=(
                "Add a reaction role to a message.\n"
                "• **MESSAGE_ID:** Enter the ID of the message you want to add the reaction role to.\n"
                "• **EMOJI:** Enter the emoji for the reaction role.\n"
                "• **ROLE:** Select the role to assign when the reaction is added."
            ),
            inline=False
        )

        embed.add_field(
            name="/reaction_role list",
            value="Show all reaction roles set up in this server.",
            inline=False
        )

        embed.add_field(
            name="/reaction_role panel",
            value="Create a Text Panel for reaction roles.",
            inline=False
        )

        embed.add_field(
            name="/reaction_role remove",
            value=(
                "Remove a reaction role from a message.\n"
                "• **MESSAGE_ID:** Enter the ID of the message you want to remove the reaction role from.\n"
                "• **EMOJI:** Enter the emoji for the reaction role."
            ),
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