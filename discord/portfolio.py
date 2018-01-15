"""Logic for dealing with portfolios / portfolio changes over time.

Portfolios are stored on disk as a json of a list _PortfolioAtTimestamp objects.
"""
from sortedcontainers import SortedDict, SortedList
from collections import namedtuple
from tabulate import tabulate
from datetime import datetime, date, time, timedelta
import json
import os
import time
import copy
import coin_data

import util
import time
import sql

_portfolios = {}

def GetPortfolio(user_id):
  if user_id not in _portfolios:
    _portfolios[user_id] = PortfolioHistory(user_id)
  return _portfolios[user_id]

class Transaction(object):
  
  def __init__(self, type, timestamp, in_symbol=None, in_amount=None,
               out_symbol=None, out_amount=None):
    self.type = type
    self.timestamp = timestamp
    self.in_symbol = in_symbol
    self.in_amount = in_amount
    self.out_symbol = out_symbol
    self.out_amount = out_amount

  def __lt__(self, oth):
    if self.timestamp != oth.timestamp:
      return self.timestamp < oth.timestamp
    # INIT actions have to come first on the same timestamp.
    if oth.type == 'INIT':
      return False
    if self.type == 'INIT':
      return True
    return  self.type < oth.type

  def __le__(self, oth):
    return (self < oth) or not (oth < self)

class PortfolioHistory(SortedDict):
  """Represents the historical holdings of a portfolio.

  Usually this class should only be instantiated by GetPortfolio.
  """

  def __init__(self, user_id):
    super(PortfolioHistory, self).__init__()
    self._user_id = user_id
    with sql.GetCursor() as cursor:
      cursor.execute(
          'SELECT type, timestamp, in_symbol, in_amount, out_symbol, out_amount '
          'FROM transactions where user_id = %s' % user_id)
      self._transactions = SortedList([
          Transaction(type=t[0], timestamp=t[1], in_symbol=t[2], in_amount=t[3],
                      out_symbol=t[4], out_amount=t[5]) for t in cursor.fetchall()])
    self.InitFromTransactions()

  def InitFromTransactions(self):
    # TODO(brandonsalmon): If it becomes necessary, we can greatly improve
    # the performance of !buy, !sell, !trade, by adding a transaction cursor
    # and not reinitializing all transactions every time.
    self.clear()
    for t in self._transactions:
      if t.type == "INIT":
        self[t.timestamp] = {}
        continue
      if t.timestamp not in self:
        bisect_point = self.bisect(t.timestamp)
        if(bisect_point) is 0:
          copy = {}
        else:
          copy = self[self._list[bisect_point-1]].copy()
        self[t.timestamp] = copy
      if t.in_symbol:
        if t.in_symbol not in self[t.timestamp]:
          self[t.timestamp][t.in_symbol] = 0
        self[t.timestamp][t.in_symbol] += t.in_amount
      if t.out_symbol:
        if t.out_symbol not in self[t.timestamp]:
          raise Exception('%s tried to remove coin %s they didn\'t own' % (
                              self._user_id, t.out_symbol))
        self[t.timestamp][t.out_symbol] -= t.out_amount
        if self[t.timestamp][t.out_symbol] < 1e-10:
          del self[t.timestamp][t.out_symbol]

  def CreationDate(self):
    return self._transactions[0].timestamp

  def GetValueList(self, t_list):
    return [self.Value(t) for t in t_list]

  def GetChange(self, timestamp=None, timedelta='24h'):
    dt = datetime.fromtimestamp(timestamp) if timestamp else datetime.now()
    old_timestamp = (dt - util.GetTimeDelta(timedelta)).timestamp()
    old_value = self.Value(old_timestamp)
    new_value = self.Value(timestamp)
    if old_value != 0:
      return '%.2f%s' % (100*(new_value - old_value) / old_value, '%')
    elif new_value == 0:
      return "No change"
    elif new_value > 0:
      return "+Inf%"
    else:
      return "-Inf%"

  def ClearRemote(self):
    with sql.GetCursor() as cursor:
      cursor.execute(
          'DELETE FROM transactions where user_id = %s' % self._user_id)
    self.clear()

  def Init(self, tuples, timestamp=None):
    """Takes a list of tuples of (symbol, amount)."""
    timestamp = int(timestamp if timestamp else time.time())
    with sql.GetCursor() as cursor:
      cursor.execute(
          'INSERT INTO transactions (user_id, type, timestamp) '
          'values (%s, "%s", %s)' % (self._user_id, "INIT", timestamp))

    transaction = Transaction(type="INIT", timestamp=timestamp)
    self._transactions.insert(self._transactions.bisect(transaction),
                              transaction)
    for t in tuples:
      self.Buy(t[0], t[1], timestamp, init=False)
    self.InitFromTransactions()
    
  
  def Buy(self, symbol, amount, timestamp=None, init=True):
    timestamp = int(timestamp if timestamp else time.time())
    with sql.GetCursor() as cursor:
      cursor.execute(
          'INSERT INTO transactions (user_id, type, timestamp, in_symbol, in_amount) '
          'values (%s, "%s", %s, "%s", %s)' % (
              self._user_id, "BUY", timestamp, symbol.upper(), amount))
    transaction = Transaction(type="BUY", timestamp=timestamp, in_symbol=symbol.upper(),
                              in_amount=amount)
    self._transactions.insert(self._transactions.bisect(transaction),
                              transaction)
    if init:
      self.InitFromTransactions()

  def Sell(self, symbol, amount, timestamp=None):
    timestamp = int(timestamp if timestamp else time.time())
    with sql.GetCursor() as cursor:
      cursor.execute(
          'INSERT INTO transactions (user_id, type, timestamp, out_symbol, out_amount) '
          'values (%s, "%s", %s, "%s", %s)' % (
              self._user_id, "SELL", timestamp, symbol.upper(), amount))
    transaction = Transaction(type="SELL", timestamp=timestamp, out_symbol=symbol.upper(),
                              out_amount=amount)
    self._transactions.insert(self._transactions.bisect(transaction),
                              transaction)
    self.InitFromTransactions()

  def Trade(self, in_symbol, in_amount, out_symbol, out_amount, timestamp=None):
    timestamp = int(timestamp if timestamp else time.time())
    with sql.GetCursor() as cursor:
      cursor.execute(
          'INSERT INTO transactions (user_id, type, timestamp, in_symbol, in_amount, '
          'out_symbol, out_amount) values (%s, "%s", %s, "%s", %s, "%s", %s)' % (
              self._user_id, "SELL", timestamp, in_symbol.upper(), in_amount,
              out_symbol.upper(), out_amount))
    transaction = Transaction(type="TRADE", timestamp=timestamp,
                              out_symbol=out_symbol.upper(), out_amount=out_amount, 
                              in_symbol=in_symbol.upper(), in_amount=in_amount)
    self._transactions.insert(self._transactions.bisect(transaction),
                              transaction)
    self.InitFromTransactions()

  def Value(self, timestamp=None):
    try:
      if timestamp:
        bisect_point = self.bisect(timestamp)
        if(bisect_point) is 0:
          return 0.0
        data = self[self._list[bisect_point-1]]
      else:
        data = self[self._list[-1]]
    except (IndexError, KeyError):
      return 0.0
    value = 0.0
    for symbol, amount in data.items():
      price = coin_data.GetHistory(symbol).GetValue(timestamp)
      value += amount*price
    return value

  def GetOwnedCurrency(self, timestamp=None):
    try:
      if timestamp:
        bisect_point = self.bisect(timestamp)
        if(bisect_point) is 0:
          return {}
        return self[self._list[bisect_point-1]]
      else:
        return self[self._list[-1]]
    except (IndexError, KeyError):
      return {}

  def AsTable(self, timestamp=None):
    tuples = []
    for symbol, amount in self.GetOwnedCurrency(timestamp).items():
      history = coin_data.GetHistory(symbol)
      price = history.GetValue(timestamp)
      curr_value = amount*price
      change_day = history.GetDayChange(timestamp)
      tuples.append([
          symbol, 
          amount,
          '$%.2f (%.2f%s)' % (curr_value, change_day, "%"),
          curr_value
      ])
    tuples = sorted(tuples, key=lambda x: x[3], reverse=True)
    for t in tuples:
      t.pop()
    return tabulate(tuples, tablefmt='fancy_grid', floatfmt='.4f')

  def BreakTable(self, timestamp=None):
    tuples = []
    for symbol, amount in self.GetOwnedCurrency(timestamp).items():
      price = coin_data.GetHistory(symbol).GetValue(timestamp)
      value_at_t = amount*price
      tuples.append([
          symbol,
          amount,
          '%.2f%s' % ((value_at_t / self.Value(timestamp))*100, "%"),
          (value_at_t / self.Value(timestamp))*100
      ])
    tuples = sorted(tuples, key=lambda x: x[3], reverse=True)
    for t in tuples:
      t.pop()
    return tabulate(tuples, tablefmt='fancy_grid', floatfmt='.4f')
