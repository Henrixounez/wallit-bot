import asyncio
import discord
import os
from discord.ext import commands


from discord import opus

OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']


def load_opus_lib(opus_libs=OPUS_LIBS):
    if opus.is_loaded():
        return True

    for opus_lib in opus_libs:
        try:
            opus.load_opus(opus_lib)
            return
        except OSError:
            pass

    raise RuntimeError('Could not load an opus lib. Tried %s' % (', '.join(opus_libs)))


bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description='Stupid bot')

load_opus_lib()

#Inits bots
@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)

# !cat
# Displays Transcendance cat gif
@bot.command()
async def cat():
	await bot.say("https://media.giphy.com/media/26FPCXdkvDbKBbgOI/giphy.gif")

# !ping
# Responds Pong
@bot.command()
async def ping():
	await bot.say('Pong! :smiley:')

class VoiceState:
	def __init__(self, bot):
		self.current = None
		self.voice = None
		self.bot = bot
		self.play_next_song = asyncio.Event()
		self.songs = asyncio.Queue()
		self.skip_votes = set() # a set of user_ids that voted
		self.audio_player = self.bot.loop.create_task(self.audio_player_task())

	def is_playing(self):
		if self.voice is None or self.current is None:
			return False
		player = self.current.player
		return not player.is_done()

	@property
	def player(self):
		return self.current.player

	def skip(self):
		self.skip_votes.clear()
		if self.is_playing():
			self.player.stop()

	def toggle_next(self):
		self.bot.loop.call_soon_threadsafe(self.play_next_song.set)

	async def audio_player_task(self):
		while True:
			self.play_next_song.clear()
			self.current = await self.songs.get()
			await self.bot.send_message(self.current.channel, 'Now playing ' + str(self.current))
			self.current.player.start()
			await self.play_next_song.wait()

class Music:

	def __init__(self, bot):
		self.bot = bot
		self.voice_states = {}

	def get_voice_state(self, server):
		state = self.voice_states.get(server.id)
		if state is None:
			state = VoiceState(self.bot)
			self.voice_states[server.id] = state
		return state
	# !summon
	# Bot joins voice channel
	@commands.command(pass_context=True)
	async def summon(self, ctx):
		summoned_channel = ctx.message.author.voice.voice_channel
		if summoned_channel is None:
			await self.bot.say('You are not in a voice channel')
			return False

		state = self.get_voice_state(ctx.message.server)
		if state.voice is None:
			state.voice = await self.bot.join_voice_channel(summoned_channel)
		else:
			await state.voice.move_to(summoned_channel)
		# player = await state.voice.create_ytdl_player('https://www.youtube.com/watch?v=uwmeH6Rnj2E')
		# player.start()
		return True

	# !stop
	# Bot stops music and leaves
	@commands.command(pass_context=True)
	async def stop(self, ctx):
		server = ctx.message.server
		state = self.get_voice_state(server)
		if state.is_playing():
			player = state.player
			player.stop()

		try:
			state.audio_player.cancel()
			del self.voice_states[server.id]
			await state.voice.disconnect()
		except:
			pass

	# !play
	# Bot play a music via an yt url
	@commands.command(pass_context=True)
	async def play(self, ctx, *, song: str):
		state = self.get_voice_state(ctx.message.server)
		if state.voice is None:
			success = await ctx.invoke(self.summon)
			if not success:
				return
		try:
			player = await state.voice.create_ytdl_player(song)
			player.start()
		except:
			self.bot.say('Wrong URL entered, please verify.')

bot.add_cog(Music(bot))
bot.run(os.environ['DISCORD_TOKEN'])