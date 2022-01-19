import sqlite3
import logging


logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s', level=logging.DEBUG)


class Server:
  def __init__(self):
    self.con = sqlite3.connect("data.db")
    self.cur = self.con.cursor()
    self._create_table()

  def _create_table(self):
    cmd = "CREATE TABLE IF NOT EXISTS servers (userId INTEGER REFERENCES users(id) ON DELETE CASCADE ON UPDATE CASCADE , ip VARCHAR(15) NOT NULL, scanresult BLOB NOT NULL, PRIMARY KEY(userId, ip))"
    self._run(cmd)

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

  def get_servers(self):
    cmd = "SELECT * FROM servers"
    return self._run(cmd)

  def get_server(self, userId, ip):
    cmd = "SELECT * FROM servers WHERE userId=(?) and ip=(?)"
    return self._run(cmd, (userId, ip))

  def get_user_servers(self, userId):
    cmd = "SELECT * FROM servers WHERE userId=(?)"
    return self._run(cmd, (userId,))

  def insert_server(self, userId, ip, scandata):
    cmd = "INSERT INTO servers (userId, ip, scanresult) values (?, ?, ?)"
    self._run(cmd, (userId, ip, scandata))
    return self.get_server(userId, ip)

  def delete_server(self, userId, ip):
    cmd = "DELETE FROM servers WHERE userId=(?) and ip=(?)"
    bef = self.get_server(userId, ip)
    self._run(cmd, (userId, ip))
    aft = self.get_server(userId, ip)
    return (bef, aft)

  def get_scan_result(self, userId, ip):
    cmd = "SELECT scanresult FROM servers WHERE userId=(?) and ip=(?)"
    return self._run(cmd, (userId, ip))


if __name__ == "__main__":
  servers = Server()
  # print(servers.insert_server('1', '192.168.1.1'))
  # print(servers.insert_server('1', '192.168.1.188'))
  # print(servers.insert_server('2', '10.10.5.2'))
  # print(servers.insert_server('3', '10.10.18.7'))
  # print(servers.insert_server('3', '10.10.18.9'))
  # print(servers.get_user_servers("234"))
  # print(servers.delete_server('1', '192.168.1.1'))
  print(servers.get_servers())
