import discord
import asyncio
from discord.ext import commands

class VoiceEntry:
	def __init__(self, message, player):
		self.requester = message.author
		self.channel = message.channel
		self.player = player

	def __str__(self):
		fmt = '*{0.title}* uploaded by {0.uploader} and requested by {1.display_name}'
		duration = self.player.duration
		if duration:
			fmt = fmt + ' [length: {0[0]}m {0[1]}s]'.format(divmod(duration, 60))
		return fmt.format(self.player, self.requester)


class VoiceState:
	def __init__(self, bot):
		self.current = None
		self.voice = None
		self.bot = bot
		self.play_next_song = asyncio.Event()
		self.songs = asyncio.Queue()
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

	async def create_voice_client(self, channel):
		voice = await self.bot.join_voice_channel(channel)
		state = self.get_voice_state(channel.server)
		state.voice = voice

	@commands.command(pass_context=True)
	async def summon(self, ctx):
		summoned_channel = ctx.message.author.voice_channel
		if summoned_channel is None:
			await self.bot.say('You are not in a voice channel.')
			return False
		state = self.get_voice_state(ctx.message.server)
		if state.voice is None:
			state.voice = await self.bot.join_voice_channel(summoned_channel)
		else:
			await state.voice.move_to(summoned_channel)
		return True

	@commands.command(pass_context=True)
	async def play(self, ctx, *, song: str):
		state = self.get_voice_state(ctx.message.server)
		opts = {
			'default_search': 'auto',
			'quiet': True,
		}
		if state.voice is None:
			success = await ctx.invoke(self.summon)
			if not success:
				return
		try:
			player = await state.voice.create_ytdl_player(song, ytdl_options=opts, after=state.toggle_next)
		except:
			await self.bot.send_message(ctx.message.channel, 'Sorry, can\'t do that')
		else:
			player.volume = 0.6
			entry = VoiceEntry(ctx.message, player)
			await self.bot.say('Enqueued : ' + str(entry))
			await state.songs.put(entry)

	@commands.command(pass_context=True)
	async def pause(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		if state.is_playing():
			player = state.player
			player.pause()

	@commands.command(pass_context=True)
	async def resume(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		if state.voice:
			player = state.player
			player.resume()

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

	@commands.command(pass_context=True)
	async def skip(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		if not state.is_playing():
			await self.bot.say('Not playing any music right now.')
			return
		await self.bot.say('Skipping current music...')
		state.skip()

	@commands.command(pass_context=True)
	async def song(self, ctx):
		state = self.get_voice_state(ctx.message.server)
		if not state.is_playing():
			await self.bot.say('Not playing any music right now.')
			return
		await self.bot.send_message(ctx.message.channel, 'Currently playing : ' + str(state.current))