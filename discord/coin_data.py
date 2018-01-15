"""Logic for dealing with coin data / prices over time. """
from sortedcontainers import SortedDict
import coinmarketcap
import traceback
import asyncio
import sql
import time
from datetime import datetime, timedelta

_coin_cache = {}


# TODO(brandonsalmon): Move TrackCoins to a different executable so that we
# reduce the likelihood of having price data gaps.
async def TrackCoins():
  await asyncio.sleep(100)
  while True:
    try:
      _DownloadNewDataPoint()
      _coin_cache.clear()
    except Exception as e:
      print('Exception in UpdateCoins:\n%s' % (traceback.format_exc()))
    await asyncio.sleep(300)


def GetHistory(symbol):
  if not symbol.upper() in _coin_cache:
    _coin_cache[symbol.upper()] = _CoinPriceHistory(symbol.upper())
  return _coin_cache[symbol.upper()]



def _DownloadNewDataPoint():
  market = coinmarketcap.Market()
  cmc_dict = market.ticker(limit=0)

  with sql.GetCursor() as cursor:
    for coin in sorted(cmc_dict, key=lambda d: int(d["rank"])):
      if coin["price_usd"]:
        try:
          cursor.execute(
              'insert into coinhistory (symbol, price, timestamp) values '
              '("%s", %s, %s)' % (coin["symbol"].upper(),
                                  float(coin["price_usd"].replace(',','')), 
                                  int(time.time())))
        except Exception as e: 
          if not "Duplicate entry" in str(e):
            raise



class _CoinPriceHistory(SortedDict):
  """The historical price data for a coin.

  Usually this class should only be instantiated by GetHistory.
  """

  def __init__(self, symbol):
    super(_CoinPriceHistory, self).__init__()
    self._symbol = symbol.upper()
    with sql.GetCursor() as cursor:
      cursor.execute(
          'SELECT timestamp, price FROM coinhistory '
          'where symbol = "%s"' % self.GetSymbol())
      for t in cursor.fetchall():
        self[t[0]] = t[1]

  def GetSymbol(self):
    return self._symbol

  def GetValue(self, timestamp=None):
    try:
      if timestamp:
        bisect_point = self.bisect(timestamp)
        if(bisect_point) is 0:
          return 0.0
        return self[self._list[bisect_point-1]]
      else:
        return self[self._list[-1]]
    except (IndexError, KeyError):
      return 0.0

  def GetDayChange(self, timestamp=None):
    currentVal = self.GetValue(timestamp)
    if timestamp:
      yesterday_time = datetime.fromtimestamp(timestamp) - timedelta(days=1)
    else:
      yesterday_time = datetime.now() - timedelta(days=1)
    oldVal = self.GetValue(yesterday_time.timestamp())
    if oldVal is None:
      return None
    return 100*((currentVal - oldVal) / oldVal)
