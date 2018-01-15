#!/usr/bin/env python3
import crypto_commands
import general_commands
import portfolio_commands
import os
import util

import discord
from discord.ext import commands
import coin_data

bot = commands.Bot(command_prefix='!' if os.name != 'nt' else '?', 
                   description="CryptoCurrency Bot")

@bot.event
async def on_ready():
  print('Logged in as')
  print(bot.user.name)
  print(bot.user.id)
  print('------')

token = open(util.GetSettingsFilepath('crypto-bot-token')).read()
bot.loop.create_task(coin_data.TrackCoins())
bot.add_cog(crypto_commands.Crypto(bot))
bot.add_cog(portfolio_commands.Portfolio(bot))
bot.add_cog(general_commands.General(bot))
bot.run(token)
