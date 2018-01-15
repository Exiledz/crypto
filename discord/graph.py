import matplotlib
# Force matplotlib to not use any Xwindows backend.
matplotlib.use('Agg')
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
from portfolio import GetPortfolioValueList
import datetime
import os

if os.name != 'nt':
  GRAPHLOC = '/tmp/fig.png'
else:
  GRAPHLOC = 'fig.png'

def GraphPortfolioTimeSeries(title, users, start_t, end_t):
  t_list = list(range(start_t, end_t, (end_t-start_t)//100)) + [end_t]
  x_values = [
      mdates.date2num(datetime.datetime.fromtimestamp(t)) for t in t_list]
  # build the figure
  fig, ax = plt.subplots()
  dfs = []
  for i, user in enumerate(users):
    y_values = GetPortfolioValueList(user.id, t_list)
    df = pd.DataFrame({'USD': y_values, 'Date': x_values})
    df['unit'] = 'USD'
    df['User'] = ('%s' % user)
    dfs.append(df)
  all_dfs = pd.concat(dfs)
  graph = sns.tsplot(data=all_dfs, value='USD', time='Date', unit='unit', condition='User')
  graph.set_title(title)

  # assign locator and formatter for the xaxis ticks.
  ax.xaxis.set_major_locator(mdates.AutoDateLocator())
  f = '%Y/%m/%d' if end_t - start_t > 86400 * 2 else '%m/%d %H:%M'
  ax.xaxis.set_major_formatter(mdates.DateFormatter(f))

  # put the labels at 45deg since they tend to be too long
  fig.autofmt_xdate()
  plt.savefig(GRAPHLOC)
  return GRAPHLOC
