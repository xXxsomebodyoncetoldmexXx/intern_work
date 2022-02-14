from . import *


class Challenge:

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
    cmd = "CREATE TABLE IF NOT EXISTS challenge(hash NVARCHAR(32) PRIMARY KEY NOT NULL, challname TEXT NOT NULL, hint TEXT NOT NULL)"
    self._run(cmd)

  def get_chall(self, hash):
    cmd = "SELECT challname, hint FROM challenge WHERE hash='{}'"
    return self._run(cmd, (hash,))

  def insert_chall(self, hash, name, hint):
    cmd = "INSERT INTO challenge (hash, challname, hint) VALUES ('{}', '{}', '{}')"
    self._run(cmd, (hash, name, hint))
    return self.get_chall(hash)

  def update_chall(self, hash, name, hint):
    self.delete_chall(hash)
    return self.insert_chall(hash, name, hint)

  def delete_chall(self, hash):
    bef = self.get_chall(hash)
    cmd = "DELETE FROM challenge WHERE hash='{}'"
    self._run(cmd, (hash, ))
    aft = self.get_chall(hash)
    return (bef, aft)
