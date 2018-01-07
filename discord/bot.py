#!/usr/bin/env python3
import crypto_commands
import general_commands

import discord
from discord.ext import commands
import coin_data

bot = commands.Bot(command_prefix='?', description="CryptoCurrency Bot")

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print(bot.user.id)
  print('------')

bot.loop.create_task(coin_data.TrackCoins())
bot.add_cog(crypto_commands.Crypto(bot, coin_data.CoinData))
bot.add_cog(general_commands.General(bot))
bot.run(open('crypto-bot-token.txt', 'r').read())
