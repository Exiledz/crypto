from discord.ext import commands
import util
import datetime
import time
import meme_helper
import graph
import portfolio

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
    p = portfolio.GetPortfolio(user.id)
    tuples = []
    for i in range(0, len(amount_and_symbol),2):
      tuples.append((amount_and_symbol[i+1], float(amount_and_symbol[i])))
    p.Init(tuples)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' %
                       (ctx.message.author, p.Value()))

  @commands.command(aliases=['reset'], pass_context=True)
  async def clear(self, ctx, confirm=None):
    """Wipe out all portfolio data.
    
    This pretty much should only be used if incorrect data is in your portfolio.
    """
    user = ctx.message.author
    p = portfolio.GetPortfolio(user.id)
    if confirm != 'confirm':
      await self.bot.say('Are you sure you want to wipe out your portfolio and '
                         'its entire history? To confirm say "!clear confirm"')
    else:
      p.ClearRemote()
      await self.bot.say('Cleared all portfolio data for %s' % user)


  @commands.command(pass_context=True)
  async def value(self, ctx, user=None):
    """Check the value of your portfolio, or of another user on the server."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    p = portfolio.GetPortfolio(user.id)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (user, p.Value()))

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
    p = portfolio.GetPortfolio(user.id)
    p.Buy(symbol, amount, util.GetTimestamp(date))
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, p.Value()))

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
    p = portfolio.GetPortfolio(user.id)
    p.Sell(symbol, amount, util.GetTimestamp(date))
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, p.Value()))

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
    p = portfolio.GetPortfolio(user.id)
    p.Trade(buy_symbol, buy_amount, sell_symbol, sell_amount,
            util.GetTimestamp(date))
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (user, p.Value()))

  @commands.command(pass_context=True)
  async def graph(self, ctx, time_delta="", *users : str):
    """Graph portfolios."""
    if not users:
      users = [user for user in ctx.message.server.members
               if len(portfolio.GetPortfolio(user.id))]
    else:
      users = [util.GetUserFromNameStr(ctx.message.server.members, user)
               for user in users]
    if time_delta is "":
      start_t = min(portfolio.GetPortfolio(user.id).CreationDate() for user in users)
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
    timestamp = util.GetTimestamp(date)
    p = portfolio.GetPortfolio(user.id)
    await self.bot.say(
        '```%s\'s portfolio:\n'
        'Total Value: $%s (%s) \n'
        '%s```' % (user, p.Value(timestamp), p.GetChange(timestamp),
                   p.AsTable(timestamp)))

  @commands.command(aliases=['bd'], pass_context=True)
  async def breakdown(self, ctx, user=None, date=None):
    """Display your portfolio, or optionally another user's portfolio."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    timestamp = util.GetTimestamp(date)
    p = portfolio.GetPortfolio(user.id)
    change = p.GetChange(timestamp)
    await self.bot.say(
        '```%s\'s portfolio diversity breakdown:\n'
        'Total Value: $%s (%s) \n'
        '%s```' % (user, p.Value(timestamp), p.GetChange(timestamp),
                   p.BreakTable(timestamp)))
