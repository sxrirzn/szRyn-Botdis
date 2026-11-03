import sqlite3

import discord
from discord import app_commands
from discord.ext import commands

DB_PATH = "reaction_roles.db"


@app_commands.guild_only()
@app_commands.default_permissions(manage_roles=True)
class ReactionRole(commands.GroupCog, group_name="reactionrole", group_description="ตั้งค่ายศผ่านอิโมจิ"):
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
    @app_commands.command(name="panel", description="ส่งข้อความสำหรับให้สมาชิกกดอิโมจิรับยศ")
    @app_commands.describe(text="ข้อความที่จะแสดงบนแผง")
    async def panel(self, interaction: discord.Interaction, text: str):
        await interaction.response.send_message("ส่งแผงแล้ว", ephemeral=True)
        msg = await interaction.channel.send(text)
        await interaction.followup.send(
            f"ID ข้อความ: `{msg.id}`\nใช้ `/reactionrole add` เพื่อผูกอิโมจิกับยศต่อได้เลย",
            ephemeral=True,
        )

    @app_commands.command(name="add", description="ผูกอิโมจิกับยศบนข้อความ (ใช้ในแชนเนลเดียวกับข้อความ)")
    @app_commands.describe(
        message_id="ID ของข้อความ (คลิกขวา > Copy Message ID)",
        emoji="อิโมจิที่ต้องการ",
        role="ยศที่จะแจก",
    )
    async def add(self, interaction: discord.Interaction, message_id: str, emoji: str, role: discord.Role):
        if not message_id.isdigit():
            return await interaction.response.send_message("message_id ต้องเป็นตัวเลข", ephemeral=True)

        me = interaction.guild.me
        if role.managed or role.is_default() or role >= me.top_role:
            return await interaction.response.send_message(
                "บอทให้ยศนี้ไม่ได้ ต้องย้ายยศบอทให้อยู่สูงกว่ายศนี้ก่อน (และห้ามเป็นยศของบอท/@everyone)",
                ephemeral=True,
            )

        try:
            message = await interaction.channel.fetch_message(int(message_id))
        except discord.NotFound:
            return await interaction.response.send_message(
                "ไม่พบข้อความนี้ในแชนเนลนี้ ลองพิมพ์คำสั่งในแชนเนลเดียวกับข้อความ", ephemeral=True
            )

        key = str(discord.PartialEmoji.from_str(emoji.strip()))
        try:
            await message.add_reaction(key)
        except discord.HTTPException:
            return await interaction.response.send_message(
                "อิโมจิไม่ถูกต้อง หรือบอทเข้าถึงอิโมจินี้ไม่ได้", ephemeral=True
            )

        self.db.execute(
            "INSERT OR REPLACE INTO reaction_roles VALUES (?, ?, ?, ?, ?)",
            (interaction.guild_id, interaction.channel_id, message.id, key, role.id),
        )
        self.db.commit()
        await interaction.response.send_message(f"ตั้งค่าแล้ว: {key} → {role.mention}", ephemeral=True)

    @app_commands.command(name="remove", description="ลบการผูกอิโมจิกับยศ")
    @app_commands.describe(message_id="ID ของข้อความ", emoji="อิโมจิที่ต้องการลบ")
    async def remove(self, interaction: discord.Interaction, message_id: str, emoji: str):
        if not message_id.isdigit():
            return await interaction.response.send_message("message_id ต้องเป็นตัวเลข", ephemeral=True)

        key = str(discord.PartialEmoji.from_str(emoji.strip()))
        cur = self.db.execute(
            "DELETE FROM reaction_roles WHERE message_id = ? AND emoji = ? AND guild_id = ?",
            (int(message_id), key, interaction.guild_id),
        )
        self.db.commit()
        msg = "ลบแล้ว" if cur.rowcount else "ไม่พบการตั้งค่านี้"
        await interaction.response.send_message(msg, ephemeral=True)

    @app_commands.command(name="list", description="ดูรายการที่ตั้งค่าไว้ทั้งหมดในเซิร์ฟเวอร์")
    async def list_roles(self, interaction: discord.Interaction):
        rows = self.db.execute(
            "SELECT channel_id, message_id, emoji, role_id FROM reaction_roles WHERE guild_id = ?",
            (interaction.guild_id,),
        ).fetchall()
        if not rows:
            return await interaction.response.send_message("ยังไม่มีการตั้งค่า", ephemeral=True)
        lines = [
            f"{emoji} → <@&{role_id}> "
            f"([ข้อความ](https://discord.com/channels/{interaction.guild_id}/{ch}/{mid}))"
            for ch, mid, emoji, role_id in rows
        ]
        await interaction.response.send_message("\n".join(lines)[:1900], ephemeral=True)

    # ------------------------------------------------------------------
    # Listeners: แจก/ถอนยศเมื่อมีคนกด/เอาอิโมจิออก
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
                print(f"ให้ยศ {role.name} ไม่ได้: สิทธิ์หรือลำดับยศของบอทไม่พอ")

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
                print(f"ถอนยศ {role.name} ไม่ได้: สิทธิ์หรือลำดับยศของบอทไม่พอ")


async def setup(bot: commands.Bot):
    await bot.add_cog(ReactionRole(bot))