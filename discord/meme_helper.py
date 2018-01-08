"""Functions for interacting with memes."""
from datetime import timedelta

# TODO(brandonsalmon): external repository for memes.

def PossiblyAddMemeToTxt(txt, symbol, percent_change=None,
                         percent_change_timedelta=None, user=None):
  """Possibly returns a meme for the specified setting.
  
  Args:
    txt: The text to add the meme to.
    symbol: A cryptocurrency symbol.
    percent_change: a percent change (e.g. a float) indicating how much
      a cryptocurrency has gone up or down.
    percent_change_timedelta: A timedelta object indicating what duration the
      percent change is over.
    user: A user to possibly custom tailor the meme for.
  """
  big_change = 40 + percent_change_timedelta.days

  meme = None
  if (percent_change_timedelta <= timedelta(days=2) and
      percent_change > big_change):
    meme = 'https://media.giphy.com/media/9lV50AKNEZ77W/giphy.gif'
  elif percent_change > big_change:
    meme = "https://i.redd.it/rn32uylurwdz.gif"
  elif percent_change > big_change/2:
    meme = "https://i.redd.it/yx4o4otzjpfz.gif"
  elif percent_change < -big_change:
    meme = "https://i.redd.it/4y6efz4jb3dz.gif"

  if meme:
    return '%s\n%s' % (txt, meme)
  return txt
