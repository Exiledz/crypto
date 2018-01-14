"""Logic for dealing with coin data / prices over time.

Has a global CoinData object which can be called to get the
value of a crypto currency at a specific time, or at the current
time. This object is kept up to date through the coin market cap api
when a thread/ event loop is running TrackCoins.

Coin data is constantly written to the ~/coinhistory folder, and
is reloaded from the ~/coinhistory folder on import.

Currently, all coin data is a stored in a SortedSet of CoinDataPoints.

TODO(brandonsalmon): This should probably be a database, because we might
start to run out of memory after a few weeks...
"""
import traceback
import sys
import os
import json
import coinmarketcap
import collections
from discord.enums import ChannelType
from sortedcontainers import SortedSet
from datetime import datetime, date, time, timedelta
from time import time as timestamp
import asyncio
import util

STORAGE_DIR = os.path.expanduser('~/coinhistory')
if not os.path.exists(STORAGE_DIR):
  os.mkdir(STORAGE_DIR)

async def TrackCoins():
  while True:
    try:
      CoinData._DownloadNewDataPoint()
    except Exception as e:
      print('Exception in UpdateCoins:\n%s' % (traceback.format_exc()))
    await asyncio.sleep(300)


class _CDPEncoder(json.JSONEncoder):

  @staticmethod
  def decode_hook(dct):
    if len(dct) == 2 and 'coin_data' in dct:
      return _CoinDataPoint(dct['timestamp'], dct['coin_data'])
    return dct

  def default(self, obj):
    if not isinstance(obj, _CoinDataPoint):
      return super(MyEncoder, self).default(obj)

    return obj.__dict__


class _CoinDataPoint(object):

  def __init__(self, timestamp, coin_data=None):
    self.timestamp = int(timestamp)
    self.coin_data = coin_data

  def __lt__(self, oth):
    return self.timestamp < oth.timestamp

  def __repr__(self):
    return "_CoinDataPoint object at timestamp %s" % self.timestamp

class _CoinDataSet(object):
  
  def __init__(self, init_from_file=True):
    self._market = coinmarketcap.Market()
    self._data = SortedSet()
    if init_from_file:
      for filename in os.listdir(STORAGE_DIR):
        with open(os.path.join(STORAGE_DIR,filename), 'r') as fp:
          datapoint_list = json.load(fp, object_hook=_CDPEncoder.decode_hook)
          self._data.update(datapoint_list)

  def _DownloadNewDataPoint(self):
    cmc_dict = self._market.ticker(limit=0)
    def GetPriceFloat(price_str_or_null):
      price_str = price_str_or_null or '0'
      return float(price_str.replace(',',''))
    data_to_store = {coin["symbol"]: GetPriceFloat(coin["price_usd"]) for coin in cmc_dict}
    self._data.add(_CoinDataPoint(timestamp(), data_to_store))
    self._DumpCurrentDayToFile()

  def _DumpAllToFile(self, filestr):
    data_to_dump = list(self._data)

    with open(filestr, 'w') as fp:
      json.dump(data_to_dump, fp, cls=_CDPEncoder)

  def _DumpCurrentDayToFile(self):
    # Midnight in unix time (system time zone)
    midnight = datetime.combine(date.today(), time.min)
    midnight_unix = int(midnight.timestamp())

    # All data since midnight.
    data_to_dump = list(self._data.irange(_CoinDataPoint(midnight_unix)))

    filestr = os.path.join(STORAGE_DIR, midnight.strftime('%Y-%m-%d.coinjson'))
    with open(filestr, 'w') as fp:
      json.dump(data_to_dump, fp, cls=_CDPEncoder)

  def GetValue(self, symbol, time=None):
    try:
      if not time:
        return self._data[-1].coin_data[symbol.upper()]
      else:
        bisect_point = self._data.bisect(_CoinDataPoint(time))
        if(bisect_point) is 0:
          return None
        return self._data[bisect_point-1].coin_data[symbol.upper()]
    except (IndexError, KeyError):
      return None

  def GetDayChange(self, symbol):
    currentVal = self.GetValue(symbol)
    yesterday_time = datetime.today() - timedelta(days=1)
    oldVal = self.GetValue(symbol, yesterday_time.timestamp())
    if oldVal is None:
      return None
    return 100*((currentVal - oldVal) / oldVal)

# Create a Singleton.
# TODO(brandonsalmon): See top of file.
CoinData = _CoinDataSet()
#print('Size of CoinData is %s MB' % (util.GetSize(CoinData) / 1024 / 1024))
