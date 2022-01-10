import logging
import ssl
import socket
import re
import email
import os
from pathlib import PurePath, Path
from random import choices

_MAXLINE = 1000000
CRLF = '\r\n'
bCRLF = b'\r\n'
Literal = re.compile(br'.*{(?P<size>\d+)}\r\n$', re.ASCII)

GOOGLE = ("imap.gmail.com", 993)
ACCOUNT = ("account name", "password")

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.ERROR)


def gen_AP():
  AP = "ABCDEFGHIJKLMNOP"
  tag = ''.join(choices(AP, k=4))
  while tag[0] == 'A':
    tag = ''.join(choices(AP, k=4))
  return tag.encode()


class My_IMAP4_SSL:

  def __init__(self, host, port, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, encoding='utf-8'):
    self.host = host
    self.port = port
    self.timeout = timeout
    self.encoding = encoding
    self.types = dict()
    self._connect()

  def _connect(self):
    self.socket = socket.create_connection(
        (self.host, self.port), self.timeout)

    # SSL
    self.ssl_context = ssl._create_stdlib_context(certfile=None, keyfile=None)
    self.socket = self.ssl_context.wrap_socket(
        self.socket, server_hostname=self.host)

    self.stream = self.socket.makefile('rb')
    self.tag = gen_AP()
    self.tagnum = 0

    logging.debug(b"New IMAP4 connection, %s" % self.tag)

    # Consume first greeting line
    self.readline()

  def send(self, data):
    self.socket.sendall(data + bCRLF)
    logging.debug(f"send {data}")

  def read(self, size):
    resp = self.stream.read(size)
    logging.debug(f"recv {resp}")
    return resp

  def readline(self):
    resp = self.stream.readline(_MAXLINE)
    logging.debug(f"recv line {resp}")
    return resp

  def get_match(self, pattern, s):
    self.mo = pattern.match(s)
    return self.mo is not None

  def get_resp(self):
    line = self.readline()

    while line.startswith(b"* "):
      type, data = line[2:].split(maxsplit=1)
      if type.decode().isnumeric():
        type, *data = data.split(maxsplit=1)

      # Fetch
      if self.get_match(Literal, line):
        size = int(self.mo.group('size'))
        data = self.read(size)

        # Read final ')'
        self.readline()

      self.types[type] = data

      line = self.readline()

    line = line.split(maxsplit=2)
    # Wrong tag
    if line[0] != self.cur_tag:
      raise Exception(f"Got wrong tag: {line[0]}")
    return line[1] == b"OK"

  def cmd(self, data, args=b""):
    self.cur_tag = b"%s%d" % (self.tag, self.tagnum)
    if args:
      args = b" %s" % args
    data = b"%s %s%s" % (self.cur_tag, data, args)
    self.tagnum += 1
    self.send(data)
    return self.get_resp()

  def login(self, email, password):
    email = email.encode()
    password = password.encode()
    args = b'%s "%s"' % (email, password)
    self.capability()
    return self.cmd(b"LOGIN", args)

  def capability(self):
    return self.cmd(b"CAPABILITY")

  def close(self):
    return self.cmd(b"CLOSE")

  def logout(self):
    return self.cmd(b"LOGOUT")

  def get_mail_indexs(self):
    self.cmd(b"SELECT", b"INBOX")
    if self.cmd(b"SEARCH", b"ALL"):
      return self.types[b"SEARCH"].split()
    return None

  def fetch_mail(self, idx):
    self.cmd(b"FETCH", b"%s (RFC822)" % idx)
    return self.types[b"FETCH"].decode()

  def parse_mail(self, mail, idx):
    data = dict()
    data["Id"] = idx.decode()
    data["Date"] = email.utils.parsedate_to_datetime(mail["Date"])
    data["From"] = mail["From"]
    data["To"] = mail["To"]
    data["Subject"] = mail["Subject"]

    if data["Subject"].startswith("=?UTF-8"):
      data["Subject"] = email.header.decode_header(mail["Subject"])[
          0][0].decode()

    for part in mail.walk():
      if part.get_content_maintype() == 'multipart':
        continue
      filename = part.get_filename()
      if part.get_content_type() == "text/plain" and filename == None:
        body = data.get("Body", "")
        body += part.get_payload(decode=True).decode()
        data["Body"] = body
      elif filename:
        attachments = data.get("Attachments", [])
        attachments.append(filename)
        data["Attachments"] = attachments
    return data

  def get_mails(self, indexs):
    if not isinstance(indexs, list):
      indexs = [indexs]
    mails = list()
    for idx in indexs:
      raw_mail = self.fetch_mail(idx)
      mail = email.message_from_string(raw_mail)
      mails.append(self.parse_mail(mail, idx))
    return mails

  def get_attachments(self, idx, filenames, save_path="./attachments"):
    if not isinstance(filenames, list):
      filenames = [filenames]
    if not Path(save_path).is_dir():
      os.mkdir(save_path)
    mail = email.message_from_string(self.fetch_mail(idx))
    result = list()
    for part in mail.walk():
      if part.get_content_maintype() == "multipart":
        continue
      filename = part.get_filename()
      if filename and filename in filenames:
        file_path = PurePath(save_path, filename)
        with open(file_path, "wb") as f:
          f.write(part.get_payload(decode=True))
        logging.debug(f"Save {filename} to {file_path}")
        result.append((filename, file_path))
    return result


def main():
  receiver = My_IMAP4_SSL(*GOOGLE)
  receiver.login(*ACCOUNT)
  mail_idxs = receiver.get_mail_indexs()
  mails = receiver.get_mails(b"3")
  print(mails)
  receiver.close()
  receiver.logout()


if __name__ == "__main__":
  main()
