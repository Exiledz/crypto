#!/usr/bin/env python3
import crypto_commands
import general_commands
import portfolio_commands
import os

import discord
from discord.ext import commands
import coin_data

if os.name != 'nt':
  SECLOC = '/etc/crypto-bot-token'
  flag = '!'
else:
  SECLOC = 'crypto-bot-token.txt'
  flag = '?'

bot = commands.Bot(command_prefix=flag, description="CryptoCurrency Bot")

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print(bot.user.id)
  print('------')

bot.loop.create_task(coin_data.TrackCoins())
bot.add_cog(crypto_commands.Crypto(bot, coin_data.CoinData))
bot.add_cog(portfolio_commands.Portfolio(bot, coin_data.CoinData))
bot.add_cog(general_commands.General(bot))
bot.run(open(SECLOC, 'r').read())
