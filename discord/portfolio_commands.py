from discord.ext import commands
from portfolio import GetPortfolio, ClearPortfolioData
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import util
import datetime
import time
import meme_helper

class Portfolio(object):
  """Commands related to interacting with portfolios."""

  def __init__(self, bot, coin_data):
    self.bot = bot
    self.coin_data = coin_data

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
  async def graph(self):
    """Graph portfolios."""
    user = ctx.message.author
    start_t = portfolio.GetPortfolioCreationDate(user.id)
    end_t = int(time.time())
    t_list = list(range(start_t, end_t, (start_t-end_t)/100)) + [end_t]
    y_values = portfolio.GetPortfolioValueList(user.id, t_list)
    x_values = [
        mdates.date2num(datetime.datetime.fromtimestamp(t)) for t in t_list]
    # build the figure
    fig, ax = plt.subplots()
    df = pd.DataFrame({'usd': y_values, 'dates': x_values})
    df['subject'] = 0
    sns.tsplot(data=df, value='usd', time='dates', unit='subject')

    # assign locator and formatter for the xaxis ticks.
    ax.xaxis.set_major_locator(mdates.AutoDateLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y.%m.%d'))

    # put the labels at 45deg since they tend to be too long
    fig.autofmt_xdate()
    plt.savefig('/tmp/fig.png')

    self.bot.upload('/tmp/fig.png')


  @commands.command(aliases=['display'], pass_context=True)
  async def list(self, ctx, user=None, date=None):
    """Display your portfolio, or optionally another user's portfolio."""
    if not user:
      user = ctx.message.author
    else:
      user = util.GetUserFromNameStr(ctx.message.server.members, user)
    portfolio = GetPortfolio(user.id, util.GetTimestamp(date))
    await self.bot.say(
        '```%s\'s portfolio:\n'
        'Total Value: $%s\n'
        '%s```' % (user, portfolio.Value(), portfolio.AsTable()))
