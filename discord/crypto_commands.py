from discord.ext import commands
from portfolio import GetPortfolio
import util
import datetime
import meme_helper

class Crypto(object):
  """Crypto related commands."""

  def __init__(self, bot, coin_data):
    self.bot = bot
    self.coin_data = coin_data

  @commands.command()
  async def price(self, symbol : str):
    """Get the price of a crypto currency."""
    val = self.coin_data.GetValue(symbol)
    if val is not None:
      await self.bot.say('%s is currently at $%s.' % (symbol.upper(), val))
    else:
      await self.bot.say('Unknown symbol %s.' % symbol.upper())

  @commands.command()
  async def price(self, symbol : str):
    """Get the price of a crypto currency."""
    val = self.coin_data.GetValue(symbol)
    if val is not None:
      await self.bot.say('%s is currently at $%.2f.' % (symbol.upper(), val))
    else:
      await self.bot.say('Unknown symbol %s.' % symbol.upper())

  @commands.command(aliases=['init'], pass_context=True)
  async def portfolio_init(self, ctx, *amount_and_symbol : str):
    """Initialize your portfolio with a list of coins.
    
    example: !portfolio_init 0.13 BTC 127.514 XRB 2 ETH
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id)
    for i in range(0, len(amount_and_symbol),2):
      portfolio.SetOwnedCurrency(amount_and_symbol[i], amount_and_symbol[i+1])
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' %
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(aliases=['value'], pass_context=True)
  async def portfolio_value(self, ctx, user=None):
    """Check the value of your portfolio."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    portfolio = GetPortfolio(user.id)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (user, portfolio.Value()))

  @commands.command(pass_context=True)
  async def buy(self, ctx, amount : float, symbol):
    """Buy a crypto currency (add it to your portfolio).
    
    It would be most appropriate to use this command when buying a
    coin from fiat currency (e.g. with USD). For trading between 
    cryptocurrencies, see !trade.
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id)
    portfolio.Buy(amount, symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(pass_context=True)
  async def sell(self, ctx, amount : float, symbol):
    """Sell a crypto currency.
    
    It would be most appropriate to use this command when selling a
    coin from fiat currency (e.g. with USD). For trading between 
    cryptocurrencies, see !trade.
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id)
    portfolio.Sell(amount, symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(pass_context=True)
  async def trade(self, ctx, sell_amount : float, sell_symbol, buy_amount : float, buy_symbol):
    """Trade a specified amount of one cryptocurrency for another.
    
    example: In order to trade 1000 Raiblocks for one Bitcoin
      !trade 1000 XRB 1 BTC
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id)
    portfolio.Sell(sell_amount, sell_symbol)
    portfolio.Buy(buy_amount, buy_symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (user, portfolio.Value()))
    portfolio.Save()

  @commands.command(aliases=['list', 'display'], pass_context=True)
  async def portfolio_list(self, ctx, user=None):
    """Display your portfolio."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    portfolio = GetPortfolio(user.id)
    await self.bot.say(
        '```%s\'s portfolio:\n'
        'Total Value: $%s\n'
        '%s```' % (user, portfolio.Value(), portfolio.AsTable()))

  @commands.command(pass_context=True)
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
    val_old = self.coin_data.GetValue(symbol, past_time.timestamp())
    val = self.coin_data.GetValue(symbol)
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
