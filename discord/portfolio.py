"""Logic for dealing with portfolios / portfolio changes over time.

Portfolios are stored on disk as a json of a list _Portfolio objects.
"""
from coin_data import CoinData
from sortedcontainers import SortedSet
from tabulate import tabulate
import json
import os
import time
import copy

STORAGE_DIR = os.path.expanduser('~/portfolios')
if not os.path.exists(STORAGE_DIR):
  os.mkdir(STORAGE_DIR)

_portfolio_sets = {}
# We need to use copy.deepcopy here because nobody old data needs
# to be kept.
def GetPortfolio(user_id, timestamp=None):
  if user_id in _portfolio_sets:
    return copy.deepcopy(_portfolio_sets[user_id].GetPortfolio(timestamp))

  _portfolio_sets[user_id] = _PortfolioSet(user_id)
  return copy.deepcopy(_portfolio_sets[user_id].GetPortfolio(timestamp))

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
    try:
      if not timestamp:
        return self._data[-1]
      else:
        bisect_point = self._data.bisect_left(_PortfolioAtTimestamp(timestamp))
        if(bisect_point) is 0:
          return None
        return self._data[bisect_point-1]
    except (IndexError, KeyError):
      # No portfolio at the specified time, return empty portfolio.
      return _PortfolioAtTimestamp(self.user_id, timestamp or time.time())

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

  def Value(self):
    value = 0.0
    for symbol in self._portfolio_data:
      value += self._portfolio_data[symbol]*CoinData.GetValue(symbol)
    return value

  def Save(self):
    _portfolio_sets[self.user_id].AddPortfolio(
        _PortfolioAtTimestamp(self.user_id, time.time(), 
                              data=self._portfolio_data))
    _portfolio_sets[self.user_id].Save()

  def AsTable(self):
    tuples = []
    for symbol in self._portfolio_data:
      curr_value = self._portfolio_data[symbol]*CoinData.GetValue(symbol)
      tuples.append([
          symbol, 
          float(self._portfolio_data[symbol]),
          '$%.2f' % curr_value,
          curr_value
      ])
    tuples = sorted(tuples, key=lambda x: x[3], reverse=True)
    for t in tuples:
      t.pop()
    return tabulate(tuples, tablefmt='fancy_grid', floatfmt='.4f')
