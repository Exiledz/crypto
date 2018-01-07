from discord.ext import commands
from portfolio import GetPortfolio

class Crypto(object):
  """Crypto related commands."""

  def __init__(self, bot, coin_data):
    self.bot = bot
    self.coin_data = coin_data

  @commands.command()
  async def price(self, symbol : str):
    """Get the price of a crypto currency."""
    val = self.coin_data.GetLatest(symbol.upper())
    if val is not None:
      await self.bot.say('%s is currently at $%s.' % (symbol.upper(), val))
    else:
      await self.bot.say('Unknown symbol %s.' % symbol.upper())

  @commands.command()
  async def price(self, symbol : str):
    """Get the price of a crypto currency."""
    val = self.coin_data.GetLatest(symbol.upper())
    if val is not None:
      await self.bot.say('%s is currently at $%.2f.' % (symbol.upper(), val))
    else:
      await self.bot.say('Unknown symbol %s.' % symbol.upper())

  @commands.command(alias='init', pass_context=True)
  async def portfolio_init(self, ctx, *amount_and_symbol : str):
    """Initialize your portfolio with a list of coins.
    
    example: !portfolio_init 0.13 BTC 127.514 XRB 2 ETH
    """
    user_id = ctx.message.author.id
    portfolio = GetPortfolio(user_id)
    for i in range(0, len(amount_and_symbol),2):
      portfolio.SetOwnedCurrency(amount_and_symbol[i], amount_and_symbol[i+1])
    portfolio.Save()

  @commands.command(pass_context=True)
  async def portfolio_value(self, ctx):
    """Check the value of your portfolio."""
    user_id = ctx.message.author.id
    portfolio = GetPortfolio(user_id)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, portfolio.Value()))

  @commands.command(pass_context=True)
  async def buy(self, ctx, amount : float, symbol):
    """Buy a crypto currency (add it to your portfolio).
    
    It would be most appropriate to use this command when buying a
    coin from fiat currency (e.g. with USD). For trading between 
    cryptocurrencies, see !trade.
    """
    user_id = ctx.message.author.id
    portfolio = GetPortfolio(user_id)
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
    user_id = ctx.message.author.id
    portfolio = GetPortfolio(user_id)
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
    user_id = ctx.message.author.id
    portfolio = GetPortfolio(user_id)
    portfolio.Sell(sell_amount, sell_symbol)
    portfolio.Buy(buy_amount, buy_symbol)
    await self.bot.say('%s\'s portfolio is now worth $%.2f.' % 
                       (ctx.message.author, portfolio.Value()))
    portfolio.Save()

  @commands.command(alias='list', pass_context=True)
  async def portfolio_list(self, ctx):
    user_id = ctx.message.author.id
    portfolio = GetPortfolio(user_id)
    await self.bot.say(
        '```%s\'s portfolio:\n'
        'Total Value: %s\n'
        '%s```' % (ctx.message.author, portfolio.Value(), portfolio.AsTable()))
