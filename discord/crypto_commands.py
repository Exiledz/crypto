from discord.ext import commands
from portfolio import GetPortfolio
import util
import datetime
import meme_helper
import coin_data

class Crypto(object):
  """Commands for checking the value of / interacting with cryptocurrencies."""

  def __init__(self, bot):
    self.bot = bot
    self.coin_data = coin_data

  @commands.command()
  async def price(self, symbol : str):
    """Get the price of a crypto currency."""
    val = coin_data.GetHistory(symbol).GetValue()
    if val is not None:
      await self.bot.say('%s is currently at $%s.' % (symbol.upper(), val))
    else:
      await self.bot.say('Unknown symbol %s.' % symbol.upper())

  @commands.command(aliases=['hist'], pass_context=True)
  async def history(self, ctx, symbol, *time_str):
    """Reports performance history of a given coin.

    To be called with a coin parameter, followed by an optional time
    parameter, to be in the format of (N)(s | m | h | d | y). If no
    parameter for timedelta is provided, 24h will be used.
    """
    if not time_str:
      time_str = ['24', 'hours']
    time_str = ' '.join(time_str)
    td = util.GetTimeDelta(time_str)
    past_time = datetime.datetime.now() - td
    history = coin_data.GetHistory(symbol)
    val_old = history.GetValue(past_time.timestamp())
    val = history.GetValue()
    if val_old is None:
      await self.bot.say('No data for %s %s ago.' % (symbol.upper(), time_str))
    elif val is not None:
      change = ((val-val_old) / val_old) * 100
      txt = '%s is currently at $%.2f (%.2f%s in the past %s)' % (
                 symbol.upper(), val, change, "%", time_str)
      await self.bot.say(
          meme_helper.PossiblyAddMemeToTxt(txt, symbol.upper(), change, td))
    else:
      await self.bot.say('Unknown symbol %s.' % symbol.upper())
