
import discord
from discord import app_commands

from commands.settings import load_config, save_config


def save_embed_template(
    guild_id,
    name,
    embed,
    use_member_avatar=None
):
    config = load_config()
    guild_id = str(guild_id)

    if guild_id not in config:
        config[guild_id] = {}

    if "embed_templates" not in config[guild_id]:
        config[guild_id]["embed_templates"] = {}

    config[guild_id]["embed_templates"][name] = embed.to_dict()

    if use_member_avatar is not None:
        config[guild_id]["greet_author_avatar"] = use_member_avatar

    save_config(config)


def create_greet_embed():
    return discord.Embed(
        title="Welcome!",
        description="Hello!",
        color=discord.Color.from_rgb(178, 134, 223)
    )



# Embed Editor Modal

class EmbedEditModal(discord.ui.Modal):

    def __init__(self, edit_type: str, message: discord.Message):
        super().__init__(title=f"Edit {edit_type}")

        self.edit_type = edit_type
        self.message = message
        self.guild_id = message.guild.id if message.guild else None
        self.use_member_avatar = False

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
                label="Author Text",
                placeholder="{USER_TAG}",
                required=False,
                max_length=256
            )

            self.author_image_input = discord.ui.TextInput(
                label="Author Image URL",
                placeholder="{USER_AVATAR}",
                required=False,
                max_length=400
            )

            self.add_item(self.author_input)
            self.add_item(self.author_image_input)

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
                    color = int(
                        self.color_input.value.replace("#", ""),
                        16
                    )

                    embed.color = discord.Color(color)

                except ValueError:
                    await interaction.response.send_message(
                        "Invalid color format. Use #B286DF.",
                        ephemeral=True
                    )
                    return

        elif self.edit_type == "Author":

            author_text = self.author_input.value.strip()
            author_image = self.author_image_input.value.strip()

            self.use_member_avatar = (
                author_image == "{USER_AVATAR}"
            )

            if self.use_member_avatar:
                author_image = ""

            if author_image and not author_image.startswith(
                ("https://", "http://")
            ):
                await interaction.response.send_message(
                    "Please enter a valid image URL or {USER_AVATAR}.",
                    ephemeral=True
                )
                return

            if author_text or author_image or self.use_member_avatar:
                embed.set_author(
                    name=author_text or "Welcome",
                    icon_url=author_image or None
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

        try:

            await message.edit(embed=embed)

            if self.guild_id:

                avatar_setting = (
                    self.use_member_avatar
                    if self.edit_type == "Author"
                    else None
                )

                save_embed_template(
                    self.guild_id,
                    "greet",
                    embed,
                    use_member_avatar=avatar_setting
                )

            await interaction.response.send_message(
                "Embed updated and saved successfully!",
                ephemeral=True
            )

        except discord.HTTPException as e:

            print(f"Embed Edit Error: {e}")

            await interaction.response.send_message(
                "Failed to update embed. Please check the URLs and fields.",
                ephemeral=True
            )



# Embed Editor Buttons

class EmbedEditorView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=300)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.guild_permissions.manage_guild:
            return True
        await interaction.response.send_message(
            "You do not have permission to edit this embed.", ephemeral=True
        )
        return False
    
    @discord.ui.button(
        label="Edit Basic Information",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def basic_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedEditModal("Basic Information", interaction.message)
        )

    @discord.ui.button(
        label="Edit Author",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def author_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedEditModal("Author", interaction.message)
        )

    @discord.ui.button(
        label="Edit Footer",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def footer_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedEditModal("Footer", interaction.message)
        )

    @discord.ui.button(
        label="Edit Images",
        style=discord.ButtonStyle.primary,
        row=0
    )
    async def images_button(self, interaction, button):
        await interaction.response.send_modal(
            EmbedEditModal("Images", interaction.message)
        )


# Embed Commands

class EmbedGroup(app_commands.Group):

    def __init__(self):
        super().__init__(
            name="embed",
            description="Embed management commands",
            guild_only=True,
            default_permissions=discord.Permissions(manage_guild=True)
        )

    @app_commands.command(
        name="create",
        description="Create an embed message"
    )
    @app_commands.describe(name="Name of the embed template")
    async def create(self, interaction: discord.Interaction, name: str):

        if interaction.guild is None:
            await interaction.response.send_message(
                "This command can only be used in a server.",
                ephemeral=True
            )
            return

        if name.lower() != "greet":
            await interaction.response.send_message(
                f"Embed template `{name}` not found.",
                ephemeral=True
            )
            return

        config = load_config()
        existing = (
            config.get(str(interaction.guild.id), {})
            .get("embed_templates", {})
            .get(name.lower())
        )

        if existing:
            embed = discord.Embed.from_dict(existing)
        else:
            embed = create_greet_embed()
            save_embed_template(
                interaction.guild.id,
                name.lower(),
                embed
            )

        await interaction.response.send_message(
            content=f"Created an embed with name `{name}`.",
            embed=embed,
            view=EmbedEditorView()
        )


async def setup(bot):
    bot.tree.add_command(EmbedGroup())
