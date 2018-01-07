"""Helpers for interacting with users."""
import difflib

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
