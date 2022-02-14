import sqlite3


class User:
  def __init__(self):
    self.con = sqlite3.connect("database.db", check_same_thread=False)
    self.cur = self.con.cursor()
    self._make_table()

  def _make_table(self):
    cmd = """CREATE TABLE IF NOT EXISTS user (
      id INTEGER PRIMARY KEY AUTOINCREMENT, 
      username TEXT NOT NULL, 
      password TEXT NOT NULL, 
      fullname TEXT,
      phone TEXT,
      email TEXT
    )"""
    self.cur.execute(cmd)
    self.con.commit()

  def insert_user(self, username, password, fullname, phone, email):
    cmd = f"""INSERT INTO user (username, password, fullname, phone, email) VALUES 
    ('{username}', '{password}', '{fullname}', '{phone}', '{email}')"""
    self.cur.execute(cmd)
    self.con.commit()

  def check_user(self, username, password):
    cmd = f"""SELECT * FROM user WHERE username='{username}' and password='{password}'"""
    self.cur.execute(cmd)
    return self.cur.fetchone()

  def get_user(self, id):
    cmd = f"""SELECT * FROM user WHERE id='{id}'"""
    self.cur.execute(cmd)
    return self.cur.fetchone()
