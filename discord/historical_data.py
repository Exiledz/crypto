#!/usr/bin/env python3
"""Gather historical data from coinmarketcap via scraping."""
import coin_data
import coinmarketcap
import requests
import re
import time
import datetime

REGEXP = '<td class="text-left">([^<]*)</td>[^<]*<td>([^<]*)</td>'

CoinData = coin_data._CoinDataSet(init_from_file=False)

market = coinmarketcap.Market()
coins = market.ticker(limit=0)
print('number of coins: %s' % len(coins))
symbol_to_id = {c['symbol']:c['id'] for c in coins}
#symbol_to_id = {'XRB': 'raiblocks', 'BTC': 'bitcoin'}
symbol_to_tuplelist = {}
counter = 0
for symbol in symbol_to_id:
  counter += 1
  print('on symbol %s, %s/%s' % (symbol, counter, len(symbol_to_id)))
  page=requests.get('https://coinmarketcap.com/currencies/%s/historical-data/?start=20130428&end=20180108' % symbol_to_id[symbol])
  #page=requests.get('https://coinmarketcap.com/currencies/%s/historical-data/?start=20180101&end=20180108' % symbol_to_id[symbol])
  openings=re.findall(REGEXP, page.text, flags=re.DOTALL)
  converted_openings = []
  for tup in openings:
    converted_openings.append((
        int(time.mktime(datetime.datetime.strptime(tup[0], "%b %d, %Y").timetuple())),
        tup[1]
    ))
  symbol_to_tuplelist[symbol] = converted_openings
  time.sleep(6)

for symbol in symbol_to_tuplelist:
  for t in symbol_to_tuplelist[symbol]:
    cdp = None
    timestamp = t[0]
    value = t[1]
    try:
      cdp = CoinData._data[CoinData._data.bisect_left(coin_data._CoinDataPoint(timestamp))]
    except IndexError:
      pass
    if not cdp or cdp.timestamp != timestamp:
      new_cdp = coin_data._CoinDataPoint(timestamp, coin_data={symbol:value})
      CoinData._data.add(new_cdp)
    elif cdp.timestamp == timestamp:
      cdp.coin_data[symbol] = value
    else:
      raise Error("Programming error")

CoinData._DumpAllToFile('historical_data.coin_json')
