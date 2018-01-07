#!/usr/bin/env python3
import os
import json
import coinmarketcap
import collections
from discord.enums import ChannelType
from sortedcontainers import SortedSet
from datetime import datetime, date, time, timedelta
from time import time as timestamp
import asyncio

STORAGE_DIR = os.path.expanduser('~/coinhistory')
if not os.path.exists(STORAGE_DIR):
  os.mkdir(STORAGE_DIR)

async def TrackCoins():
  while True:
    try:
      CoinData._DownloadNewDataPoint()
    except Exception as e:
      print('Exception in UpdateCoins: %s' % e)
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
  
  def __init__(self):
    self._market = coinmarketcap.Market()
    self._data = SortedSet()
    for filename in os.listdir(STORAGE_DIR):
      with open(os.path.join(STORAGE_DIR,filename), 'r') as fp:
        datapoint_list = json.load(fp, object_hook=_CDPEncoder.decode_hook)
        self._data.update(datapoint_list)

  def _DownloadNewDataPoint(self):
    cmc_dict = self._market.ticker(limit=0)
    data_to_store = {coin["symbol"]: coin["price_usd"] for coin in cmc_dict}
    self._data.add(_CoinDataPoint(timestamp(), data_to_store))
    self._DumpCurrentDayToFile()

  def _DumpCurrentDayToFile(self):
    # Midnight in unix time (system time zone)
    midnight = datetime.combine(date.today(), time.min)
    midnight_unix = int(midnight.timestamp())

    # All data since midnight.
    data_to_dump = list(self._data.irange(_CoinDataPoint(midnight_unix)))

    filestr = os.path.join(STORAGE_DIR, midnight.strftime('%Y-%m-%d.coinjson'))
    with open(filestr, 'w') as fp:
      json.dump(data_to_dump, fp, cls=_CDPEncoder)

  def GetLatest(self, symbol):
    try:
      return float(self._data[-1].coin_data[symbol])
    except KeyError:
      return None

# Create a Singleton.
# TODO(brandonsalmon): Gotta be a better way to do this?
CoinData = _CoinDataSet()
