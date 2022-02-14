from . import *
from hashlib import sha256


def __h(p):
  return sha256(p.encode()).hexdigest()


class User:

  def __init__(self):
    self.con = DB_CON
    self.cur = self.con.cursor()
    self._create_table()

  def _run(self, cmd, args=None, is_list=False):
    logging.debug(f"execute {cmd} with {args}")
    if args:
      self.cur.execute(cmd.format(*args))
    else:
      self.cur.execute(cmd)
    self.con.commit()
    if is_list:
      return list(self.cur.fetchmany(MAX_SIZE))
    else:
      return self.cur.fetchone()

  def _create_table(self):
    cmd = "CREATE TABLE IF NOT EXISTS user(userid INTEGER PRIMARY KEY AUTO_INCREMENT, username TEXT NOT NULL, password nvarchar(64), fullname TEXT NOT NULL, email TEXT NOT NULL, phone TEXT NOT NULL, is_teacher BOOLEAN DEFAULT(FALSE) NOT NULL)"
    self._run(cmd)

  def set_teacher(self, userid):
    cmd = "UPDATE user SET is_teacher=TRUE WHERE userid='{}'"
    self._run(cmd, (userid,))
    return self.get_user(userid)

  def get_users(self):
    cmd = "SELECT * FROM user"
    return self._run(cmd, is_list=True)

  def get_user(self, userid):
    cmd = "SELECT * FROM user WHERE userid='{}'"
    return self._run(cmd, (userid,))

  def check_user(self, username, password):
    cmd = "SELECT * FROM user WHERE username='{}' and password='{}'"
    return self._run(cmd, (username, password), is_list=True)

  def insert_user(self, username, password, fullname, email, phone):
    cmd = "INSERT INTO user (username, password, fullname, email, phone) VALUES('{}', '{}', '{}', '{}', '{}')"
    self._run(cmd, (username, password, fullname, email, phone))
    return self.check_user(username, password)

  def update_user(self, userid, username, password, fullname, email, phone):
    cmd = "UPDATE user SET username='{}', password='{}', fullname='{}', email='{}', phone='{}' WHERE userid='{}'"
    self._run(cmd, (username, password, fullname, email, phone, userid))
    return self.get_user(userid)

  def delete_user(self, userid):
    bef = self.get_user(userid)
    cmd = "DELETE FROM user WHERE userid='{}'"
    self._run(cmd, (userid,))
    aft = self.get_user(userid)
    return (bef, aft)


if __name__ == "__main__":
  u = User()
  # print(u.insert_user("admin", __h("password"), "administrator", "admin@localhost", "09097651234"))
  # print(u.insert_user("steve", __h("1234"), "steven", "steve@gmail.com", "123456789"))
  # print(u.insert_user("john", __h("abc"), "johnson", "john@yahoo.com", "000011112222"))
  # print(u.delete_user(3))
  u.set_teacher(1)
  print(u.get_users())
