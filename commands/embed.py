import discord
from discord import app_commands
from discord.ext import commands

def create_greet_embed():
    embed = discord.Embed(
        title="successfully created an embed called: greet.",
        description="please select from the buttons below for what you'd like to edit!",
        color=discord.Color.from_rgb(178, 134, 223)
    )
    return embed


# Embed Editor Modal


class EmbedEditModal(discord.ui.Modal):

    def __init__(self, edit_type: str, message: discord.Message):
        super().__init__(title=f"Edit {edit_type}")
        self.edit_type = edit_type
        self.message = message

        if edit_type == "Basic Information":
            self.title_input = discord.ui.TextInput(
                label="Title",
                required=False,
                max_length=256
            )
            self.description_input = discord.ui.TextInput(
                label="Description",
                style=discord.TextStyle.paragraph,
                required=False,
                max_length=4000
            )
            self.color_input = discord.ui.TextInput(
                label="Color (Hex)",
                placeholder="#B286DF",
                required=False,
                max_length=7
            )

            self.add_item(self.title_input)
            self.add_item(self.description_input)
            self.add_item(self.color_input)

        elif edit_type == "Author":
            self.author_input = discord.ui.TextInput(
                label="Author Name",
                required=False
            )
            self.add_item(self.author_input)

        elif edit_type == "Footer":
            self.footer_input = discord.ui.TextInput(
                label="Footer Text",
                required=False
            )
            self.add_item(self.footer_input)

        elif edit_type == "Images":
            self.image_input = discord.ui.TextInput(
                label="Image URL",
                required=False
            )
            self.thumbnail_input = discord.ui.TextInput(
                label="Thumbnail URL",
                required=False
            )
            self.add_item(self.image_input)
            self.add_item(self.thumbnail_input)

    async def on_submit(self, interaction: discord.Interaction):
        message = self.message
        embed = message.embeds[0] if message.embeds else discord.Embed()

        if self.edit_type == "Basic Information":
            if self.title_input.value:
                embed.title = self.title_input.value

            if self.description_input.value:
                embed.description = self.description_input.value

            if self.color_input.value:
                try:
                    color = int(self.color_input.value.replace("#", ""), 16)
                    embed.color = discord.Color(color)
                except ValueError:
                    await interaction.response.send_message(
                        "Invalid color format. Please use Hex, e.g. #B286DF",
                        ephemeral=True
                    )
                    return

        elif self.edit_type == "Author":
            embed.set_author(
                name=self.author_input.value or None
            )

        elif self.edit_type == "Footer":
            embed.set_footer(
                text=self.footer_input.value or None
            )

        elif self.edit_type == "Images":
            if self.image_input.value:
                embed.set_image(url=self.image_input.value)

            if self.thumbnail_input.value:
                embed.set_thumbnail(url=self.thumbnail_input.value)

        await message.edit(embed=embed)

        await interaction.response.send_message(
            "Embed updated successfully!",
            ephemeral=True
        )


# Embed Editor Buttons

class EmbedEditorView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)

    @discord.ui.button(
        label="Edit Basic Information",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def basic_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedEditModal("Basic Information", interaction.message)
        )

    @discord.ui.button(
        label="Edit Author",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def author_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedEditModal("Author", interaction.message)
        )

    @discord.ui.button(
        label="Edit Footer",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def footer_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedEditModal("Footer", interaction.message)
        )

    @discord.ui.button(
        label="Edit Images",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def images_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(
            EmbedEditModal("Images", interaction.message)
        )


class EmbedGroup(app_commands.Group):
    def __init__(self):
        super().__init__(
            name="embed",
            description="Embed management commands"
        )

    @app_commands.command(
        name="create",
        description="Create an embed message"
    )
    @app_commands.describe(name="Name of the embed template")
    async def create(self, interaction: discord.Interaction, name: str):
        await interaction.response.defer()

        if name.lower() == "greet":
            embed = create_greet_embed()

            await interaction.followup.send(
                content=f"Created an embed with name `{name}`.",
                embed=embed,
                view=EmbedEditorView()
            )
        else:
            await interaction.followup.send(
                f"ไม่พบ Embed Template ชื่อ `{name}`",
                ephemeral=True
            )


async def setup(bot):
    bot.tree.add_command(EmbedGroup())

    