import random
import wikipediaapi
import os
import discord
from discord.ext import commands
from discord import opus
from music import *

bot = commands.Bot(command_prefix=commands.when_mentioned_or('!'), description='Stupid bot')
OPUS_LIBS = ['libopus-0.x86.dll', 'libopus-0.x64.dll', 'libopus-0.dll', 'libopus.so.0', 'libopus.0.dylib']


# Init bot
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


load_opus_lib()


@bot.event
async def on_ready():
	print('Logged in as')
	print(bot.user.name)
	print(bot.user.id)


@bot.command(pass_context=True)
async def category(ctx):
	list = ctx.message.content.split(" ")
	small = 0
	if list[0] == '!category':
		small = 1
	if ((small and len(list) != 2) or (not small and len(list) != 3)):
		await bot.say('Usage : `!category CategoryName`, you can find categories by using `!categories`')
		return
	if small:
		searched = list[1]
	else:
		searched = list[2]
	searched = searched.lower()
	if searched == 'music':
		message = discord.Embed(title='**Music**', description='\n' +
		'• `!summon`  : Bot comes to your channel\n' +
		'• `!play []` : Bot comes to your channel, searches for given video title or url and add it to the queue\n' +
		'• `!pause`   : Bot pauses current song\n' +
		'• `!resume`  : Bot resumes current song\n' +
		'• `!stop`    : Bot stops playing music and leaves channel\n' +
		'• `!skip`    : Bot skips current music and play next in the queue\n' +
		'• `!song`    : Bot gives information about current song being played\n'
		, colour=0x40e0d0)
	elif searched == 'games':
		message = discord.Embed(title='**Games**', description='\n' +
		'• `!dice []` : Rolls the dice and gives a number from 1 to the `given number`\n'
		, colour=0x40e0d0)
	elif searched == 'utility':
		message = discord.Embed(title='**Utility**', description='\n' +
		'• `!ping` : Bot answers you with pong !\n' +
		'• `!wiki []` : Bot searched for given page on wikipedia and gives the summary\n'
		, colour=0x40e0d0)
	elif searched == 'fun':
		message = discord.Embed(title='**Fun**', description='\n' +
		'• `!cat` : Bot answers with an awesome GIF of a cat\n'
		, colour=0x40e0d0)
	elif searched == 'help':
		message = discord.Embed(title='**Help**', description='\n' +
		'• `!h`   : Displays help menu\n' +
		'• `!category` : Displays all commands categories\n' +
		'• `!commands []` : Displays details about commands in given category\n'
		, colour=0x40e0d0)
	else:
		await bot.say('Wrong category given, you can find categories by using `!categories`')
		return
	await bot.send_message(ctx.message.channel, embed=message)

@bot.command(pass_context=True)
async def categories(ctx):
	list = ctx.message.content.split(" ")
	small = 0
	if list[0] == '!categories':
		small = 1
	if (small and len(list) > 1) or (not small and len(list) > 2):
		await bot.say('Usage : `!categories`')
		return
	message = discord.Embed(title='**List of categories**', description = '\n• Music\n• Games\n• Utility\n• Fun\n• Help\n', colour=0x40e0d0)
	await bot.send_message(ctx.message.channel, embed=message)

@bot.command(pass_context=True)
async def h(ctx):
	list = ctx.message.content.split(" ")
	small = 0
	if list[0] == '!h':
		small = 1
	if (small and len(list) > 1) or (not small and len(list) > 3):
		await bot.say('Usage : `!h`')
		return
	message = discord.Embed(description=
	'You can use `!categories` to see a list of all categories\n' +
	'You can use `!category CategoryName` to see a list of all of the commands in that category. (for example `!commands music`)\n'
	, colour=0x40e0d0)
	await bot.send_message(ctx.message.channel, embed=message)



# !cat
# Displays Transcendence cat gif
@bot.command(pass_context=True)
async def cat(ctx):
	message = discord.Embed()
	message.set_image(url="https://media.giphy.com/media/26FPCXdkvDbKBbgOI/giphy.gif")
	await bot.send_message(ctx.message.channel, embed=message)
	# await bot.say("https://media.giphy.com/media/26FPCXdkvDbKBbgOI/giphy.gif")


# !ping
# Responds Pong
@bot.command()
async def ping():
	await bot.say('Pong! :smiley:')


# !wiki
# Searches wikipedia for given page and prints the summary
@bot.command(pass_context=True)
async def wiki(ctx):
	list = ctx.message.content.split(" ")
	small = 0
	if list[0] == '!wiki':
		small = 1
	if (small and len(list) != 2) or (not small and len(list) != 3):
		await bot.say('You have to give a page to search')
		return
	if small:
		page = list[1]
	else:
		page = list[2]
	wiki_wiki = wikipediaapi.Wikipedia('en')
	page_py = wiki_wiki.page(page)
	if page_py.exists() is False:
		await bot.send_message(ctx.message.channel, 'Page doesn\'t exists')
		return
	await bot.send_message(ctx.message.channel, '**' + page_py.title + '**')
	size = len(page_py.summary)
	i = 0
	while i < size:
		await bot.send_message(ctx.message.channel, '```' + page_py.summary[i:i + 2000] + '```')
		i = i + 2000


# !ping
# Roll the dice and gives number between 1 and n
@bot.command(pass_context=True)
async def dice(ctx):
	list = ctx.message.content.split(" ")
	small = 0
	if list[0] == '!dice':
		small = 1
	if (small and len(list) != 2) or (not small and len(list) != 3):
		await bot.say('You have to give a number, please')
		return
	if small:
		arg = list[1]
	else:
		arg = list[2]
	try:
		limit = int(arg)
	except:
		await bot.send_message(ctx.message.channel, 'Please give a number : !dice 10')
		return
	number = random.randint(1, limit)
	await bot.say(number)


# Error catcher
@bot.event
async def on_command_error(ctx, error):
	if isinstance(error, commands.MissingRequiredArgument):
		await ctx.send(content="You are missing and argument")

bot.add_cog(Music(bot))
bot.run(os.environ['DISCORD_TOKEN'])
