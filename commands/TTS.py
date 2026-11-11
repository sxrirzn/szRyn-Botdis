import asyncio
import os
import re
import tempfile
import uuid

import discord
from discord import app_commands
from discord.ext import commands
from gtts import gTTS

DEFAULT_LANG = "th"  # language used for people who haven't picked one (th = Thai)
MAX_CHARS = 200      # max characters read per message

# Menu label -> gTTS language code (add or remove freely, max 25 entries)
LANGUAGES = {
    "ไทย (Thai)": "th",
    "English": "en",
    "日本語 (Japanese)": "jp",
    "한국어 (Korean)": "ko",
    "中文 (Chinese)": "cn",
    "Español (Spanish)": "es",
    "Français (French)": "fr",
    "Deutsch (German)": "de",
    "Bahasa Indonesia (Indonesian)": "id",
    "Tiếng Việt (Vietnamese)": "vn",
    "Русский (Russian)": "ru",
    "हिन्दी (Hindi)": "hi",
}

# Word spoken in place of a URL (falls back to "link" for other languages)
LINK_WORDS = {"th": "ลิงก์"}

URL_RE = re.compile(r"https?://\S+")
CUSTOM_EMOJI_RE = re.compile(r"<a?:(\w+):\d+>")


class TTS(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.text_channels: dict[int, int] = {}      # guild_id -> text channel id
        self.queues: dict[int, asyncio.Queue] = {}   # guild_id -> message queue
        self.workers: dict[int, asyncio.Task] = {}   # guild_id -> task that plays audio
        self.user_langs: dict[int, str] = {}         # user_id -> language code (resets on restart)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def clean(message: discord.Message, lang: str) -> str:
        text = message.clean_content                          # turns @mentions into names
        text = URL_RE.sub(LINK_WORDS.get(lang, "link"), text)  # don't read long URLs aloud
        text = CUSTOM_EMOJI_RE.sub(r"\1", text)               # custom emoji -> read its name
        return text.strip()[:MAX_CHARS]

    @staticmethod
    def _make_mp3(text: str, path: str, lang: str):
        gTTS(text=text, lang=lang).save(path)

    def _start_session(self, guild_id: int, text_channel_id: int):
        self.text_channels[guild_id] = text_channel_id
        if guild_id not in self.queues:
            self.queues[guild_id] = asyncio.Queue()
        if guild_id not in self.workers:
            self.workers[guild_id] = asyncio.create_task(self._worker(guild_id))

    def _end_session(self, guild_id: int):
        task = self.workers.pop(guild_id, None)
        if task:
            task.cancel()
        self.queues.pop(guild_id, None)
        self.text_channels.pop(guild_id, None)

    async def _worker(self, guild_id: int):
        """Take messages from the queue one at a time, generate audio, and play it."""
        queue = self.queues[guild_id]
        loop = asyncio.get_running_loop()
        while True:
            text, lang = await queue.get()
            guild = self.bot.get_guild(guild_id)
            vc = guild.voice_client if guild else None
            if vc is None or not vc.is_connected():
                continue

            path = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.mp3")
            try:
                # gTTS is blocking, so run it in a separate thread
                await asyncio.to_thread(self._make_mp3, text, path, lang)

                done = asyncio.Event()
                vc.play(
                    discord.FFmpegPCMAudio(path),
                    after=lambda err: loop.call_soon_threadsafe(done.set),
                )
                await done.wait()
            except asyncio.CancelledError:
                raise
            except Exception as e:
                print(f"TTS error: {e}")
            finally:
                try:
                    os.remove(path)
                except OSError:
                    pass

    # ------------------------------------------------------------------
    # Slash commands: /join | /leave | /skip | /lang
    # ------------------------------------------------------------------
    @app_commands.guild_only()
    @app_commands.command(name="join", description="Join your voice channel and read messages from this channel")
    async def join(self, interaction: discord.Interaction):
        voice = interaction.user.voice
        if voice is None or voice.channel is None:
            return await interaction.response.send_message(
                "You need to join a voice channel first.", ephemeral=True
            )

        await interaction.response.defer(ephemeral=True)
        vc = interaction.guild.voice_client
        try:
            if vc:
                await vc.move_to(voice.channel)
            else:
                await voice.channel.connect()
        except Exception as e:
            return await interaction.followup.send(f"Failed to join: {e}", ephemeral=True)

        self._start_session(interaction.guild_id, interaction.channel_id)
        vc = interaction.guild.voice_client
        vc.play(discord.FFmpegPCMAudio("sine=frequency=440:duration=3", before_options="-f lavfi"))
        await interaction.followup.send(
            f"Joined {voice.channel.mention}. I'll read messages from this channel "
            "(only from people in the same voice channel as me).",
            ephemeral=True,
        )

    @app_commands.guild_only()
    @app_commands.command(name="leave", description="Leave the voice channel")
    async def leave(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc is None:
            return await interaction.response.send_message("I'm not in a voice channel.", ephemeral=True)
        await vc.disconnect()
        self._end_session(interaction.guild_id)
        await interaction.response.send_message("Left the voice channel.", ephemeral=True)

    @app_commands.guild_only()
    @app_commands.command(name="skip", description="Skip the message currently being read")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if vc and vc.is_playing():
            vc.stop()
            return await interaction.response.send_message("Skipped.", ephemeral=True)
        await interaction.response.send_message("Nothing is playing right now.", ephemeral=True)

    @app_commands.command(name="lang", description="Choose the language the bot uses to read your messages")
    @app_commands.describe(language="The language you want")
    @app_commands.choices(
        language=[app_commands.Choice(name=name, value=code) for name, code in LANGUAGES.items()]
    )
    async def lang(self, interaction: discord.Interaction, language: app_commands.Choice[str]):
        self.user_langs[interaction.user.id] = language.value
        await interaction.response.send_message(
            f"Your messages will now be read in {language.name}.", ephemeral=True
        )

    # ------------------------------------------------------------------
    # Listeners
    # ------------------------------------------------------------------
    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        print(f"got message: {message.content!r} in channel {message.channel.id}")
        if message.author.bot or message.guild is None:
            return

        gid = message.guild.id
        if self.text_channels.get(gid) != message.channel.id:
            return

        vc = message.guild.voice_client
        if vc is None or not vc.is_connected():
            return

        # Only read messages from people in the same voice channel as the bot
        author_voice = getattr(message.author, "voice", None)
        if author_voice is None or author_voice.channel != vc.channel:
            return

        lang = self.user_langs.get(message.author.id, DEFAULT_LANG)
        text = self.clean(message, lang)
        if text:
            await self.queues[gid].put((text, lang))

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        # If the bot was disconnected or kicked, clean up its state
        if member.id == self.bot.user.id and before.channel and after.channel is None:
            self._end_session(member.guild.id)
            return

        # If only bots are left in the channel, leave
        vc = member.guild.voice_client
        if vc and vc.channel and len([m for m in vc.channel.members if not m.bot]) == 0:
            await vc.disconnect()
            self._end_session(member.guild.id)

    async def cog_unload(self):
        for vc in list(self.bot.voice_clients):
            await vc.disconnect()
        for gid in list(self.workers):
            self._end_session(gid)


async def setup(bot: commands.Bot):
    await bot.add_cog(TTS(bot))