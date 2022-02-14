from . import *


class Answer:

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
    cmd = "CREATE TABLE IF NOT EXISTS answer(answerid INTEGER PRIMARY KEY AUTO_INCREMENT, userid INTEGER NOT NULL, problemid INTEGER NOT NULL, content MEDIUMTEXT NOT NULL, FOREIGN KEY (userid) REFERENCES user(userid) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY (problemid) REFERENCES problem(problemid) ON DELETE CASCADE ON UPDATE CASCADE)"
    self._run(cmd)

  def get_answers(self):
    cmd = "SELECT answerid, u.userid, username, p.problemid, problemname, a.content FROM answer a JOIN problem p ON a.problemid=p.problemid JOIN user u ON a.userid=u.userid"
    return self._run(cmd, is_list=True)

  def get_answer(self, answerid):
    cmd = "SELECT answerid, u.userid, username, p.problemid, problemname, a.content FROM answer a JOIN problem p ON a.problemid=p.problemid JOIN user u ON a.userid=u.userid WHERE answerid='{}'"
    return self._run(cmd, (answerid,))

  def get_user_answers(self, userid, problemid=None):
    cmd = "SELECT answerid, u.userid, username, p.problemid, problemname, a.content FROM answer a JOIN problem p ON a.problemid=p.problemid JOIN user u ON a.userid=u.userid WHERE a.userid='{}'"
    if problemid:
      cmd += " and a.problemid='{}'"
    return self._run(cmd, (userid, problemid), is_list=True if not problemid else False)

  def get_problem_answers(self, problemid):
    cmd = "SELECT * FROM answer WHERE problemid='{}'"
    return self._run(cmd, (problemid,))

  def insert_answer(self, userid, problemid, content):
    cmd = "INSERT INTO answer (userid, problemid, content) VALUES('{}', '{}', '{}')"
    self._run(cmd, (userid, problemid, content))

  def update_answer(self, answerid, problemid, content):
    cmd = "UPDATE answer SET content='{}', problemid='{}' WHERE answerid='{}'"
    self._run(cmd, (content, problemid, answerid))
    return self.get_answer(answerid)

  def delete_answer(self, answerid):
    cmd = "DELETE FROM answer WHERE answerid='{}'"
    bef = self.get_answer(answerid)
    self._run(cmd, (answerid,))
    aft = self.get_answer(answerid)
    return (bef, aft)


if __name__ == "__main__":
  a = Answer()
  # a.insert_answer(1, 1, "who know")
  # a.insert_answer(1, 2, "ansdf1")
  # a.insert_answer(2, 2, "idk")
  # a.insert_answer(3, 2, "is it?")
  # a.insert_answer(10, 3, "wrong user")
  # a.insert_answer(1, 30, "wrong problem")
  # a.insert_answer(10, 30, "wrong user and problem")
  # print(a.get_user_answers(1, 2))
  # print(a.delete_answer(4))
  print(a.get_answers())
