"""MySQLdb doesn't really support threading very well out of the box.

This file should maintain a threadsafe pool of database connections.

Example usage:
  with GetCursor() as cursor:
    cursor.execute(
        'SELECT timestamp, price FROM coinhistory '
        'where symbol = "%s"' % self.GetSymbol())
    for t in cursor.fetchall():
      self[t[0]] = t[1]
"""
from MySQLdb import connections
import util
import json
_pool = []

class _Connection(connections.Connection):

  def __enter__(self):
    self.ping(True)
    self._cursor = super(_Connection, self).cursor()
    return self._cursor

  def __exit__(self, exception, value, traceback):
    if exception:
      self.rollback()
    self._cursor.close()
    _pool.append(self)

def GetCursor():
  if _pool:
    return _pool.pop()
  with open(util.GetSettingsFilepath('crypto-db')) as fp:
    connection_details = json.load(fp)
  connection = _Connection(
      host=connection_details['host'],
      user=connection_details['user'],
      password=connection_details['password'],
      db=connection_details['db'])
  connection.autocommit(True)
  return connection

