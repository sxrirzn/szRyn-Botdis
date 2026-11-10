import sqlite3
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

DB_PATH = "reaction_roles.db"


@app_commands.guild_only()
@app_commands.default_permissions(manage_roles=True)
class ReactionRole(commands.GroupCog, group_name="reactionrole", group_description="Set up reaction roles"):
    def __init__(self, bot: commands.Bot):
        super().__init__()
        self.bot = bot
        self.db = sqlite3.connect(DB_PATH)
        self.db.execute(
            """
            CREATE TABLE IF NOT EXISTS reaction_roles (
                guild_id   INTEGER NOT NULL,
                channel_id INTEGER NOT NULL,
                message_id INTEGER NOT NULL,
                emoji      TEXT    NOT NULL,
                role_id    INTEGER NOT NULL,
                PRIMARY KEY (message_id, emoji)
            )
            """
        )
        self.db.commit()

    async def cog_unload(self):
        self.db.close()

    def get_role_id(self, message_id: int, emoji: str):
        row = self.db.execute(
            "SELECT role_id FROM reaction_roles WHERE message_id = ? AND emoji = ?",
            (message_id, emoji),
        ).fetchone()
        return row[0] if row else None

    # ------------------------------------------------------------------
    # Slash commands: /reactionrole panel | add | remove | list
    # ------------------------------------------------------------------
    @app_commands.command(name="panel", description="Send a message members can react to for roles")
    @app_commands.describe(text="The text to display on the panel")
    async def panel(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message("Panel sent.", ephemeral=True)
        msg = await interaction.channel.send(text)
        await interaction.followup.send(
            f"Message ID: `{msg.id}`\nUse `/reactionrole add` to link emojis to roles.",
            ephemeral=True,
        )

    @app_commands.command(name="add", description="Link emojis to roles on a message (up to 7 pairs at once)" "Run it in the message's channel.")
    @app_commands.describe(
        message_id="Message ID (right-click > Copy Message ID)",
        emoji1="Emoji 1", role1="Role 1",
        emoji2="Emoji 2", role2="Role 2",
        emoji3="Emoji 3", role3="Role 3",
        emoji4="Emoji 4", role4="Role 4",
        emoji5="Emoji 5", role5="Role 5",
        emoji6="Emoji 6", role6="Role 6",
        emoji7="Emoji 7", role7="Role 7",
    )
    async def add(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji1: str, role1: discord.Role,
        emoji2: Optional[str] = None, role2: Optional[discord.Role] = None,
        emoji3: Optional[str] = None, role3: Optional[discord.Role] = None,
        emoji4: Optional[str] = None, role4: Optional[discord.Role] = None,
        emoji5: Optional[str] = None, role5: Optional[discord.Role] = None,
        emoji6: Optional[str] = None, role6: Optional[discord.Role] = None,
        emoji7: Optional[str] = None, role7: Optional[discord.Role] = None,
    ):
        if not message_id.isdigit():
            return await interaction.response.send_message("message_id must be a number.", ephemeral=True)

        # Collect the pairs that were filled in (each emoji needs a matching role)
        raw_pairs = [
            (emoji1, role1), (emoji2, role2), (emoji3, role3),
            (emoji4, role4), (emoji5, role5), (emoji6, role6), (emoji7, role7)
        ]
        pairs = []
        for emoji, role in raw_pairs:
            if emoji is None and role is None:
                continue
            if emoji is None or role is None:
                return await interaction.response.send_message(
                    "Each emoji must be paired with a role (and vice versa).", ephemeral=True
                )
            pairs.append((str(discord.PartialEmoji.from_str(emoji.strip())), role))

        keys = [key for key, _ in pairs]
        if len(set(keys)) != len(keys):
            return await interaction.response.send_message(
                "The same emoji was used more than once in this command.", ephemeral=True
            )

        # Make sure the bot can assign every role before doing anything
        me = interaction.guild.me
        for _, role in pairs:
            if role.managed or role.is_default() or role >= me.top_role:
                return await interaction.response.send_message(
                    f"I can't assign {role.mention}. Move my role above it in the role list "
                    "(and the role can't be a bot role or @everyone).",
                    ephemeral=True,
                )

        await interaction.response.defer(ephemeral=True)  # Adding several reactions can take a moment

        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except discord.NotFound:
            return await interaction.followup.send(
                "Message not found in this channel. Run the command in the same channel as the message.",
                ephemeral=True,
            )

        done, failed = [], []
        for key, role in pairs:
            try:
                await message.add_reaction(key)
            except discord.HTTPException:
                failed.append(key)
                continue
            self.db.execute(
                "INSERT OR REPLACE INTO reaction_roles VALUES (?, ?, ?, ?, ?)",
                (interaction.guild_id, interaction.channel_id, message.id, key, role.id),
            )
            done.append(f"{key} → {role.mention}")
        self.db.commit()

        text = ""
        if done:
            text += "Saved:\n" + "\n".join(done)
        if failed:
            text += (
                "\nFailed to add (invalid emoji, or the message already has 20 reactions): "
                + " ".join(failed)
            )
        await interaction.followup.send(text, ephemeral=True)

    @app_commands.command(name="remove", description="Remove an emoji-to-role link")
    @app_commands.describe(message_id="Message ID", emoji="The emoji to remove")
    async def remove(self, interaction: discord.Interaction, message_id: str, emoji: str):
        if not message_id.isdigit():
            return await interaction.response.send_message("message_id must be a number.", ephemeral=True)

        key = str(discord.PartialEmoji.from_str(emoji.strip()))
        cur = self.db.execute(
            "DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ? AND guild_id = ?",
            (int(message_id), key, interaction.guild_id),
        )
        self.db.commit()
        msg = "Removed." if cur.rowcount else "No matching setup found."
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="list", description="Show all reaction roles set up in this server")
    async def list_roles(self, interaction: discord.Interaction):
        rows = self.db.execute(
            "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = ?",
            (interaction.guild_id,),
        ).fetchall()
        if not rows:
            return await interaction.response.send_message("Nothing has been set up yet.", ephemeral=True)
        lines = [
            f"{emoji} → <@&{role_id}> "
            f"([message](https://discord.com/channels/{interaction.guild_id}/{ch}/{mid}))"
            for ch, mid, emoji, role_id in rows
        ]
        await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)

    # ------------------------------------------------------------------
    # Listeners: give/remove the role when someone adds/removes the reaction
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None or payload.user_id == self.bot.user.id:
            return
        role_id = self.get_role_id(payload.message_id, str(payload.emoji))
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        role = guild.get_role(role_id) if guild else None
        if role and payload.member:
            try:
                await payload.member.add_roles(role, reason="Reaction role")
            except discord.Forbidden:
                print(f"Could not give role {role.name}: missing permission or bot role is too low.")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        if payload.guild_id is None:
            return
        role_id = self.get_role_id(payload.message_id, str(payload.emoji))
        if not role_id:
            return
        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return
        member = guild.get_member(payload.user_id)
        role = guild.get_role(role_id)
        if member and role:
            try:
                await member.remove_roles(role, reason="Reaction role")
            except discord.Forbidden:
                print(f"Could not remove role {role.name}: missing permission or bot role is too low.")


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRole(bot))