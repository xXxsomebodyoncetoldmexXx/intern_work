import sqlite3
import logging


logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s', level=logging.INFO)


class Users:
  def __init__(self):
    self.con = sqlite3.connect("data.db")
    self.cur = self.con.cursor()
    self._create_table()

  def _run(self, cmd, args=None):
    if not args:
      logging.debug(f"execute {cmd}")
      self.cur.execute(cmd)
    else:
      logging.debug(f"execute {cmd} with args {args}")
      self.cur.execute(cmd, args)
    self.con.commit()
    return self.cur.fetchall()

  def __exit__(self):
    self.cur.close()
    self.con.close()

  def _create_table(self):
    cmd = "CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name VARCHAR(50) NOT NULL, password VARCHAR(64) NOT NULL, is_admin BOOLEAN DEFAULT(FALSE) NOT NULL)"
    self._run(cmd)

  def _set_admin(self, username, password):
    cmd = "UPDATE users set is_admin=TRUE WHERE name=(?) and password=(?)"
    self._run(cmd, (username, password))
    return self.get_user(username, password)

  def get_users(self):
    cmd = "SELECT * FROM users"
    return self._run(cmd)

  def get_user(self, username, password):
    cmd = "SELECT * FROM users WHERE name=(?) and password=(?)"
    return self._run(cmd, (username, password))

  def get_user_by_id(self, id):
    cmd = "SELECT * FROM users WHERE id=(?)"
    return self._run(cmd, (id,))

  def get_user_by_name(self, name):
    cmd = "SELECT * FROM users WHERE name=(?)"
    return self._run(cmd, (name, ))

  def insert_user(self, username, password):
    cmd = "INSERT INTO users (name, password) values (?, ?)"
    self._run(cmd, (username, password))
    return self.get_user(username, password)

  def delete_user(self, username):
    cmd = "DELETE FROM users WHERE name=(?)"
    bef = self.get_user_by_name(username)
    self._run(cmd, (username,))
    aft = self.get_user_by_name(username)
    return (bef, aft)


if __name__ == "__main__":
  user = Users()
  # print(user.insert_user("admin", "root"))
  # print(user.insert_user("john", "password"))
  # print(user.insert_user("test_user", "1234"))
  user._set_admin("admin", "root")
  print(user.get_users())
  print(user.delete_user("test_user", "1234"))
