"""Logic for dealing with portfolios / portfolio changes over time.

Portfolios are stored on disk as a json of a list _PortfolioAtTimestamp objects.
"""
from coin_data import CoinData
from sortedcontainers import SortedSet
from tabulate import tabulate
from datetime import datetime, date, time, timedelta
import json
import os
import time
import copy

STORAGE_DIR = os.path.expanduser('~/portfolios')
if not os.path.exists(STORAGE_DIR):
  os.mkdir(STORAGE_DIR)

_portfolio_sets = {}

def GetPortfolioCreationDate(user_id):
  if user_id not in _portfolio_sets:
    _portfolio_sets[user_id] = _PortfolioSet(user_id)

  try:
    return _portfolio_sets[user_id]._data[0].timestamp
  except (KeyError, IndexError) as e:
    return -1

def GetPortfolioValueList(user_id, t_list):
  return [GetPortfolio(user_id, t).Value(t) for t in t_list]

def GetPortfolio(user_id, timestamp=None):
  if user_id in _portfolio_sets:
    return _portfolio_sets[user_id].GetPortfolio(timestamp)

  _portfolio_sets[user_id] = _PortfolioSet(user_id)
  return _portfolio_sets[user_id].GetPortfolio(timestamp)

def GetPortfolioChange(user_id):
  current = GetPortfolio(user_id)
  timestamp = (datetime.now() - timedelta(days=1)).timestamp()
  old = GetPortfolio(user_id, timestamp)
  if old.Empty():
    return 0.0
  change = 100*((current.Value() - old.Value(timestamp)) / old.Value(timestamp))
  return change

def ClearPortfolioData(user_id):
  try:
    del _portfolio_sets[user_id]
  except KeyError:
    pass
  try:
    os.remove(os.path.join(STORAGE_DIR, str(user_id)))
  except FileNotFoundError:
    pass

class _PortfolioEncoder(json.JSONEncoder):

  @staticmethod
  def decode_hook(dct):
    if '_portfolio_data' in dct:
      return _PortfolioAtTimestamp(dct['user_id'], dct['timestamp'], dct['_portfolio_data'])
    return dct

  def default(self, obj):
    if not isinstance(obj, _PortfolioAtTimestamp):
      return super(MyEncoder, self).default(obj)

    return obj.__dict__

class _PortfolioSet(object):

  def __init__(self, user_id):
    self.user_id = user_id
    self._file = os.path.join(STORAGE_DIR, str(user_id))
    self._data = SortedSet()
    if os.path.exists(self._file):
      with open(self._file, 'r') as fp:
        datapoint_list = json.load(
            fp, object_hook=_PortfolioEncoder.decode_hook)
        self._data.update(datapoint_list)

  def GetPortfolio(self, timestamp=None):
    rval = None
    try:
      if not timestamp:
        rval = self._data[-1]
      else:
        bisect_point = self._data.bisect(_PortfolioAtTimestamp(0, timestamp))
        if bisect_point > 0:
          rval = self._data[bisect_point-1]
    except (IndexError, KeyError):
      pass

    # No portfolio at the specified time, return empty portfolio.
    if not rval:
      return _PortfolioAtTimestamp(self.user_id, timestamp or time.time())
    # We need to use copy.deepcopy here because nobody old data needs
    # to be kept. The timestamp is set as requested, so the copied portfolio
    # can simply be saved.
    rval = copy.deepcopy(rval)
    rval.timestamp = timestamp or time.time()
    return rval

  def AddPortfolio(self, portfolio):
    self._data.add(portfolio)

  def Save(self):
    data_to_dump = list(self._data)
    with open(self._file, 'w') as fp:
      json.dump(data_to_dump, fp, cls=_PortfolioEncoder)


class _PortfolioAtTimestamp(object):

  def __init__(self, user_id, timestamp, data=None):
    if not data:
      data = {}
    # Note: it's lazy to store the user_id here, because it gets stored on
    # disk repeatedly with every portfolio snapshot.
    self.user_id = user_id
    self.timestamp = int(timestamp)
    self._portfolio_data = data

  def __lt__(self, oth):
    return self.timestamp < oth.timestamp

  def Empty(self):
    return len(self._portfolio_data) == 0

  def SetOwnedCurrency(self, amount, symbol):
    if amount == 0:
      if symbol.upper() in self._portfolio_data:
        del self._portfolio_data[symbol.upper()]
    else:
      self._portfolio_data[symbol.upper()] = float(amount)

  def Sell(self, amount, symbol):
    curr_owned = self.GetOwnedCurrency(symbol)
    self.SetOwnedCurrency(max([curr_owned - amount, 0]), symbol)

  def Buy(self, amount, symbol):
    curr_owned = self.GetOwnedCurrency(symbol)
    self.SetOwnedCurrency(curr_owned + amount, symbol)

  def GetOwnedCurrency(self, symbol):
    try:
      return self._portfolio_data[symbol.upper()]
    except KeyError:
      return 0

  def Value(self, timestamp=None):
    value = 0.0
    for symbol in self._portfolio_data:
      value += self._portfolio_data[symbol]*CoinData.GetValue(symbol, timestamp)
    return value

  def Save(self, timestamp=None):
    _portfolio_sets[self.user_id].AddPortfolio(self)
    _portfolio_sets[self.user_id].Save()

  def AsTable(self):
    tuples = []
    for symbol in self._portfolio_data:
      curr_value = self._portfolio_data[symbol]*CoinData.GetValue(symbol)
      change_day = CoinData.GetDayChange(symbol)
      tuples.append([
          symbol, 
          float(self._portfolio_data[symbol]),
          '$%.2f (%.2f%s)' % (curr_value, change_day, "%"),
          curr_value
      ])
    tuples = sorted(tuples, key=lambda x: x[3], reverse=True)
    for t in tuples:
      t.pop()
    return tabulate(tuples, tablefmt='fancy_grid', floatfmt='.4f')
