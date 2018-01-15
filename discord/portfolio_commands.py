from discord.ext import commands
from portfolio import GetPortfolio, ClearPortfolioData, GetPortfolioCreationDate, GetPortfolioValueList, GetPortfolioChange, HasPortfolio
import util
import datetime
import time
import meme_helper
import graph

class Portfolio(object):
  """Commands related to interacting with portfolios."""

  def __init__(self, bot):
    self.bot = bot

  @commands.command(aliases=['reinit'], pass_context=True)
  async def init(self, ctx, *amount_and_symbol : str):
    """Initialize your portfolio with a list of coins.

    **Important** This will set the exact contents of your portfolio at the
    current timestamp. If you want to be able to do correct graphing of your
    portfolio, you have to instead do a list of !buy, !sell, and !trade
    commands, specifying dates of transactions.

    This command will not erase your historical data, meaning
    you can use this command. Instead of a list of !buy, !sell, and !trades
    if you made a lot of transactions within a short timeframe.
    
    example: !portfolio_init 0.13 BTC 127.514 XRB 2 ETH
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id)
    for i in range(0, len(amount_and_symbol),2):
      portfolio.SetOwnedCurrency(amount_and_symbol[i], amount_and_symbol[i+1])
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' %
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(aliases=['reset'], pass_context=True)
  async def clear(self, ctx, confirm=None):
    """Wipe out all portfolio data.
    
    This pretty much should only be used if incorrect data is in your portfolio.
    """
    user = ctx.message.author
    if confirm != 'confirm':
      await self.bot.say('Are you sure you want to wipe out your portfolio and '
                         'its entire history? To confirm say "!clear confirm"')
    else:
      ClearPortfolioData(user.id)
      await self.bot.say('Cleared all portfolio data for %s' % user)


  @commands.command(pass_context=True)
  async def value(self, ctx, user=None):
    """Check the value of your portfolio, or of another user on the server."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    portfolio = GetPortfolio(user.id)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (user, portfolio.Value()))

  @commands.command(pass_context=True)
  async def buy(self, ctx, amount : float, symbol, date=None):
    """Buy a crypto currency (add it to your portfolio).

    If specified, date should be in YYYY/MM/DD(HH:MM:SS) format.
    (HH:MM:SS) is optional, with HH being 0-23.
    
    It would be most appropriate to use this command when buying a
    coin from fiat currency (e.g. with USD). For trading between 
    cryptocurrencies, see !trade.
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id, util.GetTimestamp(date))
    portfolio.Buy(amount, symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(pass_context=True)
  async def sell(self, ctx, amount : float, symbol, date=None):
    """Sell a crypto currency.

    If specified, date should be in YYYY/MM/DD(HH:MM:SS) format.
    (HH:MM:SS) is optional, with HH being 0-23.
    
    It would be most appropriate to use this command when selling a
    coin from fiat currency (e.g. with USD). For trading between 
    cryptocurrencies, see !trade.
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id, util.GetTimestamp(date))
    portfolio.Sell(amount, symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(pass_context=True)
  async def trade(self, ctx, sell_amount : float, sell_symbol, 
                  buy_amount : float, buy_symbol, date=None):
    """Trade a specified amount of one cryptocurrency for another.

    If specified, date should be in YYYY/MM/DD(HH:MM:SS) format.
    (HH:MM:SS) is optional, with HH being 0-23.
    
    example: In order to trade 1000 Raiblocks for one Bitcoin
      !trade 1000 XRB 1 BTC
    """
    user = ctx.message.author
    portfolio = GetPortfolio(user.id, util.GetTimestamp(date))
    portfolio.Sell(sell_amount, sell_symbol)
    portfolio.Buy(buy_amount, buy_symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (user, portfolio.Value()))
    portfolio.Save()

  @commands.command(pass_context=True)
  async def graph(self, ctx, time_delta="", *users : str):
    """Graph portfolios."""
    if not users:
      users = [user for user in ctx.message.server.members if HasPortfolio(user.id)]
    else:
      users = [util.GetUserFromNameStr(ctx.message.server.members, user)
               for user in users]
    if time_delta is "":
      start_t = min(GetPortfolioCreationDate(user.id) for user in users)
    else:
      start_t = int((datetime.datetime.now() - util.GetTimeDelta(time_delta)).timestamp())
    end_t = int(datetime.datetime.now().timestamp())
    graph_file = graph.GraphPortfolioTimeSeries('Gainz', users, start_t, end_t)
    await self.bot.upload(graph_file)

  @commands.command(aliases=['display', 'ls'], pass_context=True)
  async def list(self, ctx, user=None, date=None):
    """Display your portfolio, or optionally another user's portfolio."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    change = GetPortfolioChange(user.id)
    portfolio = GetPortfolio(user.id, util.GetTimestamp(date))
    await self.bot.say(
        '```%s\'s portfolio:\n'
        'Total Value: $%s (%.2f%s) \n'
        '%s```' % (user, portfolio.Value(), change, "%", portfolio.AsTable()))

  @commands.command(aliases=['bd'], pass_context=True)
  async def breakdown(self, ctx, user=None, date=None):
    """Display your portfolio, or optionally another user's portfolio."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    change = GetPortfolioChange(user.id)
    portfolio = GetPortfolio(user.id, util.GetTimestamp(date))
    await self.bot.say(
        '```%s\'s portfolio diversity breakdown:\n'
        'Total Value: $%s (%.2f%s) \n'
        '%s```' % (user, portfolio.Value(), change, "%", portfolio.BreakTable()))
