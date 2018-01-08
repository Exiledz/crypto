"""Utility functions that didn't fit anywhere else."""
import difflib
import re
from datetime import timedelta

def GetUserFromNameStr(users, name_str):
  """Given an iterable of discord.Users, find the one with the closest name."""
  best_user_so_far = None
  best_score_so_far = 0

  def StringSimilarity(one, two):
    return difflib.SequenceMatcher(None, one.upper(), two.upper()).ratio()

  for user in users:
    score = max([
        StringSimilarity(str(user), name_str) + 0.1,
        StringSimilarity(user.name, name_str) + 0.05,
        StringSimilarity(str(user.display_name), name_str),
    ])
    if score > best_score_so_far and score > 0.5:
      best_score_so_far = score
      best_user_so_far = user
  return best_user_so_far

def GetTimeDelta(time_str):
  """Given a time string, convert it to seconds (an integer).
  
  Args:
    time_str: A time string.
  """
  days = 0
  minutes = 0
  hours = 0
  seconds = 0
  # pytimeparse doesn't work for years or months. Just change them.
  for match in re.finditer('([0-9.]+) *(year|yr|y)(s)?', time_str):
    days += 365*float(match.groups()[0])
  for match in re.finditer('([0-9.]+) *(month|mth|M)(s)?', time_str):
    days += 30*float(match.groups()[0])
  for match in re.finditer('([0-9.]+) *(week|wk|w)(s)?', time_str):
    days += 7*float(match.groups()[0])
  for match in re.finditer('([0-9.]+) *(day|dy|d)(s)?', time_str):
    days += float(match.groups()[0])
  for match in re.finditer('([0-9.]+) *(hour|hr|h)(s)?', time_str):
    hours += float(match.groups()[0])
  for match in re.finditer('([0-9.]+) *(minute|min|mn|m)(s)?', time_str):
    minutes += float(match.groups()[0])
  for match in re.finditer('([0-9.]+) *(second|sec|s)(s)?', time_str):
    seconds += float(match.groups()[0])

  return timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
