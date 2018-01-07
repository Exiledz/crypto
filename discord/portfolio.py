import os
from coin_data import CoinData
import json
from tabulate import tabulate

STORAGE_DIR = os.path.expanduser('~/portfolios')

_portfolios = {}
def GetPortfolio(user_id):
  if user_id in _portfolios:
    return _portfolios[user_id]

  _portfolios[user_id] = _Portfolio(user_id)
  return _portfolios[user_id]


class _Portfolio(object):

  def __init__(self, user_id):
    self.portfolio_file = os.path.join(STORAGE_DIR, str(user_id))
    if os.path.exists(self.portfolio_file):
      with open(self.portfolio_file, 'r') as fp:
        self._data = json.load(fp)
    else:
      self._data = {}

  def SetOwnedCurrency(self, amount, symbol):
    if amount == 0:
      if symbol.upper() in self._data:
        del self._data[symbol.upper()]
    else:
      self._data[symbol.upper()] = float(amount)

  def Sell(self, amount, symbol):
    curr_owned = self.GetOwnedCurrency(symbol)
    self.SetOwnedCurrency(max([curr_owned - amount, 0]), symbol)

  def Buy(self, amount, symbol):
    curr_owned = self.GetOwnedCurrency(symbol)
    self.SetOwnedCurrency(curr_owned + amount, symbol)

  def GetOwnedCurrency(self, symbol):
    try:
      return self._data[symbol.upper()]
    except KeyError:
      return 0

  def Value(self):
    value = 0.0
    for symbol in self._data:
      value += self._data[symbol]*CoinData.GetLatest(symbol)
    return value

  def Save(self):
    with open(self.portfolio_file, 'w') as fp:
      json.dump(self._data, fp)

  def AsTable(self):
    tuples = []
    for symbol in self._data:
      curr_value = self._data[symbol]*CoinData.GetLatest(symbol)
      tuples.append([
          symbol, 
          float(self._data[symbol]),
          '$%.2f' % curr_value,
          curr_value
      ])
    tuples = sorted(tuples, key=lambda x: x[3], reverse=True)
    for t in tuples:
      t.pop()
    return tabulate(tuples, tablefmt='fancy_grid', floatfmt='.4f')
