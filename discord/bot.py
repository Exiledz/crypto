#!/usr/bin/env python3
import discord
from discord.ext import commands
from discord.enums import ChannelType
import random
import asyncio
from coin_data import CoinDataSet

DESCRIPTION = """An example bot to showcase the discord.ext.commands extension module.
There are a number of utility commands being showcased here."""
bot = commands.Bot(command_prefix='?', description=DESCRIPTION)

coin_data = CoinDataSet()

async def track_coin_market_cap():
  await bot.wait_until_ready()
  counter = 0
  while not bot.is_closed:
    counter += 1
    coin_data.DownloadNewDataPoint()
    try:
      for channel in bot.get_all_channels():
        if channel.type is ChannelType.text:
          await bot.send_message(channel, 'XRB is currently at %s' % coin_data.GetLatest('XRB'))
    except Exception as e:
      print('EXCEPTION %s' % e)
      pass
    await asyncio.sleep(300)

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print(bot.user.id)
  print('------')

@bot.command()
async def add(left : int, right : int):
  """Adds two numbers together."""
  await bot.say(left + right)

@bot.command()
async def roll(dice : str):
  """Rolls a dice in NdN format."""
  try:
    rolls, limit = map(int, dice.split('d'))
  except Exception:
    await bot.say('Format has to be in NdN!')
    return

  result = ', '.join(str(random.randint(1, limit)) for r in range(rolls))
  await bot.say(result)

@bot.command(description='For when you wanna settle the score some other way')
async def choose(*choices : str):
  """Chooses between multiple choices."""
  await bot.say(random.choice(choices))

@bot.command()
async def repeat(times : int, content='repeating...'):
  """Repeats a message multiple times."""
  for i in range(times):
    await bot.say(content)

@bot.command()
async def joined(member : discord.Member):
  """Says when a member joined."""
  await bot.say('{0.name} joined in {0.joined_at}'.format(member))

@bot.group(pass_context=True)
async def cool(ctx):
  """Says if a user is cool.
  In reality this just checks if a subcommand is being invoked.
  """
  if ctx.invoked_subcommand is None:
    await bot.say('No, {0.subcommand_passed} is not cool'.format(ctx))

@cool.command(name='bot')
async def _bot():
  """Is the bot cool?"""
  await bot.say('Yes, the bot is cool.')

bot.loop.create_task(track_coin_market_cap())
bot.run(open('/etc/crypto-bot-token', 'r').read())
