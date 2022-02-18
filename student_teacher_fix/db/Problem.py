from . import *


class Problem:
    def __init__(self):
        self.con = DB_CON
        self.cur = self.con.cursor()
        self._create_table()

    def _run(self, cmd, args=None, is_list=False):
        logging.debug(f"execute {cmd} with {args}")
        if args:
            self.cur.execute(cmd, args)
        else:
            self.cur.execute(cmd)
        self.con.commit()
        if is_list:
            return list(self.cur.fetchmany(MAX_SIZE))
        else:
            return self.cur.fetchone()

    def _create_table(self):
        cmd = "CREATE TABLE IF NOT EXISTS problem(problemid INTEGER PRIMARY KEY AUTO_INCREMENT, problemname TEXT NOT NULL, content MEDIUMTEXT NOT NULL)"
        self._run(cmd)

    def get_problems(self):
        cmd = "SELECT * FROM problem"
        return self._run(cmd, is_list=True)

    def get_problem(self, problemid):
        cmd = "SELECT * FROM problem WHERE problemid=%s"
        return self._run(cmd, (problemid,))

    def get_unsolve_problems(self, userid):
        cmd = "SELECT problemid, problemname FROM problem WHERE problemid NOT IN \
      (SELECT a.problemid FROM user u JOIN answer a ON u.userid=a.userid WHERE u.userid=%s)"
        return self._run(cmd, (userid,), is_list=True)

    def insert_problem(self, problemname, content):
        cmd = "INSERT INTO problem (problemname, content) VALUES(%s, %s)"
        self._run(cmd, (problemname, content))

    def update_problem(self, problemid, problemname, content):
        cmd = "UPDATE problem SET problemname=%s, content=%s WHERE problemid=%s"
        self._run(cmd, (problemname, content, problemid))
        return self.get_problem(problemid)

    def delete_problem(self, problemid):
        cmd = "DELETE FROM problem WHERE problemid=%s"
        bef = self.get_problem(problemid)
        self._run(cmd, (problemid,))
        aft = self.get_problem(problemid)
        return (bef, aft)


if __name__ == "__main__":
    p = Problem()
    # p.insert_problem("test problem", "Who the strongest in the world?")
    # p.insert_problem("problem123", "What is this?")
    # p.insert_problem("problem456", "Who is this?")
    # p.insert_problem("problem789", "Why is this?")
    # p.insert_problem("problem000", "Where is this?")
    # print(p.get_problem(3))
    # p.update_problem(1, "not a test problem anymore", "Again who is the strongest in the world?")
    # print(p.delete_problem(3))
    print(p.get_problems())
