from . import *
from base64 import b64encode as be


class Message:
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
        cmd = "CREATE TABLE IF NOT EXISTS message(messageid INTEGER PRIMARY KEY AUTO_INCREMENT, content TEXT NOT NULL, fromuser INTEGER NOT NULL, touser INTEGER NOT NULL, FOREIGN KEY (fromuser) REFERENCES user(userid) ON DELETE CASCADE ON UPDATE CASCADE, FOREIGN KEY (touser) REFERENCES user(userid) ON DELETE CASCADE ON UPDATE CASCADE)"
        self._run(cmd)

    def get_messages(self):
        cmd = "SELECT * FROM message"
        return self._run(cmd, is_list=True)

    def get_message(self, messageid):
        cmd = "SELECT * FROM message WHERE messageid=%s"
        return self._run(cmd, (messageid,))

    def get_user_message(self, userid):
        cmd = "SELECT username, content FROM message m JOIN user u on m.fromuser=u.userid WHERE touser=%s"
        return self._run(cmd, (userid,), is_list=True)

    def get_send_message(self, userid, targetid):
        cmd = "SELECT * FROM message WHERE fromuser=%s and touser=%s"
        return self._run(cmd, (userid, targetid), is_list=True)

    def insert_message(self, content, fromuser, touser):
        cmd = "INSERT INTO message (content, fromuser, touser) VALUES (%s, %s, %s)"
        self._run(cmd, (content, fromuser, touser))

    def update_message(self, messageid, content):
        cmd = "UPDATE message SET content=%s WHERE messageid=%s"
        self._run(cmd, (content, messageid))
        return self.get_message(messageid)

    def delete_message(self, messageid):
        cmd = "DELETE FROM message WHERE messageid=%s"
        bef = self.get_message(messageid)
        self._run(cmd, (messageid,))
        aft = self.get_message(messageid)
        return (bef, aft)


if __name__ == "__main__":
    m = Message()
    # m.insert_message(be("Hello world"), 1, 2)
    # m.insert_message(be("testing testing"), 1, 2)
    # m.insert_message(be("xin chào"), 1, 2)
    # m.insert_message(be("Lorem ipsum dolor sit amet, consectetur adipiscing elit. Suspendisse mattis, nunc sit amet venenatis semper, augue mauris ullamcorper massa, nec laoreet purus ligula eget nunc. Etiam vitae porttitor sem, non aliquet nisl. Nullam rhoncus faucibus malesuada. Etiam molestie quam lectus, non tincidunt lacus finibus porttitor. Nam ac risus iaculis, porta erat id, pharetra neque. Vestibulum nec eleifend magna. In ut efficitur mi. Morbi eget sem et eros ultrices tristique eget vel ipsum. "), 1, 3)
    # m.insert_message(be("Hắn vừa đi vừa chửi. Bao giờ cũng thế, cứ rượu xong là hắn chửi. Bắt đầu chửi trời, có hề gì? Trời có của riêng nhà nào? Rồi hắn chửi đời. Thế cũng chẳng sao: Đời là tất cả nhưng cũng chẳng là ai. Tức mình hắn chửi ngay tất cả làng Vũ Đại. Nhưng cả làng Vũ Đại ai cũng nhủ: “Chắc nó trừ mình ra!”. Không ai lên tiếng cả. Tức thật! Ồ thế này thì tức thật! Tức chết đi được mất! Đã thế, hắn phải chửi cha đứa nào không chửi nhau với hắn. Nhưng cũng không ai ra điều. Mẹ kiếp! Thế thì có phí rượu không? Thế thì có khổ hắn không? Không biết đứa chết mẹ nào đẻ ra thân hắn cho hắn khổ đến nông nỗi này! A ha! Phải đấy hắn cứ thế mà chửi, hắn chửi đứa chết mẹ nào đẻ ra thân hắn, đẻ ra cái thằng Chí Phèo? Mà có trời biết! Hắn không biết, cả làng Vũ Đại cũng không ai biết."), 1, 3)
    # m.insert_message(be("testing 123"), 2, 3)
    # print(m.get_user_message(3))
    # m.update_message(4, "shorter lorem ipsum sit amet")
    # print(m.delete_message(3))
    print(m.get_messages())
