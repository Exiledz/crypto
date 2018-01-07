#!/usr/bin/env python3
import os
import json
import coinmarketcap
import collections
from sortedcontainers import SortedSet
from datetime import datetime, date, time, timedelta
from time import time as timestamp

class CDPEncoder(json.JSONEncoder):

  @staticmethod
  def decode_hook(dct):
    if len(dct) == 2 and 'coin_data' in dct:
      return CoinDataPoint(dct['timestamp'], dct['coin_data'])
    return dct

  def default(self, obj):
    if not isinstance(obj, CoinDataPoint):
      return super(MyEncoder, self).default(obj)

    return obj.__dict__


class CoinDataPoint(object):

  def __init__(self, timestamp, coin_data=None):
    self.timestamp = int(timestamp)
    self.coin_data = coin_data

  def __lt__(self, oth):
    self.timestamp < oth.timestamp

  def __repr__(self):
    return "CoinDataPoint object at timestamp %s" % self.timestamp

class CoinDataSet(object):
  
  def __init__(self):
    self._market = coinmarketcap.Market()
    self._data = SortedSet()
    if os.path.exists('coinhistory'):
      for filename in os.listdir('coinhistory'):
        with open(os.path.join('coinhistory',filename), 'r') as fp:
          datapoint_list = json.load(fp)
          self._data.update(datapoint_list)
    else:
      os.mkdir('coinhistory')

  def DownloadNewDataPoint(self):
    cmc_dict = self._market.ticker(limit=0)
    data_to_store = {coin["symbol"]: coin["price_usd"] for coin in cmc_dict}
    self._data.add(CoinDataPoint(timestamp(), data_to_store))
    self.DumpCurrentDayToFile()

  def DumpCurrentDayToFile(self):
    # Midnight in unix time (system time zone)
    midnight = datetime.combine(date.today(), time.min)
    midnight_unix = int(midnight.strftime('%s'))

    # All data since midnight.
    data_to_dump = list(self._data.irange(CoinDataPoint(midnight_unix)))

    filestr = os.path.join('coinhistory', midnight.strftime('%Y-%m-%d.coinjson'))
    with open(filestr, 'w') as fp:
      json.dump(data_to_dump, fp, cls=CDPEncoder)

  def GetLatest(self, ticker):
    try:
      return self._data[-1].coin_data[ticker]
    except KeyError:
      return None
