import sqlite3
import logging


logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s', level=logging.DEBUG)


class Users:
  def __init__(self):
    self.con = sqlite3.connect("Users.db")
    self._create_table()
    self.con.close()

  def _create_table(self):
    cmd = "CREATE TABLE IF NOT EXISTS users ()"
    cur = self.con.cursor()
