import hmac
import socket
import logging
import re
import ssl
import base64
from binascii import b2a_base64


CRLF = "\r\n"
bCRLF = b"\r\n"
_MAX_LINE = 8192
_MAXCHALLENGE = 5

AUTH_RE = re.compile(r"auth=(.*)", re.I)

LOCAL = ("192.168.97.101", 1025)
GOOGLE_TLS = ("smtp.gmail.com", 587)
GOOGLE_SSL = ("smtp.gmail.com", 465)  # todo

ACCOUNT_NAME_PASS = ("account name", "password")
TEST_ACCOUNT_NAME = "target account name"

MAIL_BODY_FORMAT = """\
From: {}
To: {}
Subject: {}

{}"""

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.ERROR)


def enc_base64(s, maxlinelen=76):
  result = list()
  step = maxlinelen * 3 // 4
  for i in range(0, len(s), step):
    ss = b2a_base64(s[i:i + step]).decode("ascii")
    if ss.endswith('\n'):
      ss = ss[:-1]
    result.append(ss)
  return ''.join(result)


def _fix_eol(msg):
  return re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, msg)


def _quote_periods(bindata):
  return re.sub(br'(?m)^\.', b'..', bindata)


class My_SMTP:

  def __init__(self, host, port, timeout=socket._GLOBAL_DEFAULT_TIMEOUT, encoding=None) -> None:
    self.host = host
    self.port = port
    self.timeout = timeout
    self.encoding = encoding or "ascii"
    self.stream = None
    (code, msg) = self.connect()
    if code != 220:
      self.close()
      raise Exception(f"Cannot connect to {host} with port {port}")

    # Get host name
    fqdn = socket.getfqdn()
    self.local_hostname = fqdn
    if "." not in fqdn:
      try:
        self.local_hostname = f'[{socket.gethostbyname(socket.gethostname())}]'
      except socket.gaierror:
        self.local_hostname = '[127.0.0.1]'

  def connect(self):
    self.sock = socket.create_connection(
        (self.host, self.port), timeout=self.timeout)
    code, msg = self.get_reply()
    return (code, msg)

  def close(self):
    self.stream.close()
    self.sock.close()

  def get_reply(self):
    resp = list()
    if not self.stream:
      self.stream = self.sock.makefile('rb')
    while True:
      line = self.stream.readline(_MAX_LINE)
      if not line:
        self.close()
      resp.append(line[4:].strip(b' \t\r\n'))
      code = int(line[:3])
      logging.debug(f'resp {line}')

      # Check if multiline response.
      if line[3:4] != b"-":
        break
    msg = b'\n'.join(resp)
    return (code, msg)

  def send(self, msg):
    try:
      msg = msg.encode(self.encoding)
    except AttributeError:
      pass
    self.sock.sendall(msg)
    logging.debug(f"send {msg}")

  def cmd(self, cmd, args=""):
    if args:
      cmd = f"{cmd} {args}"
    self.send(f'{cmd}{CRLF}')
    return self.get_reply()

  def helo(self):
    return self.cmd('helo', self.local_hostname)

  def ehlo(self):
    self.esmtp_features = {}
    (code, msg) = self.cmd('ehlo', self.local_hostname)

    if code != 250:
      return (code, msg)

    self.esmtp = True
    resp = msg.decode("latin-1").split('\n')
    for line in resp[1:]:
      auth_match = AUTH_RE.match(line)
      if auth_match:
        self.esmtp_features["auth"] = f'{self.esmtp_features.get("auth", "")} {auth_match.groups(0)[0]}'
        continue

      m = re.match(r'(?P<feature>[A-Za-z0-9][A-Za-z0-9\-]*) ?', line)
      if m:
        feature = m.group("feature").lower()
        params = m.string[m.end("feature"):].strip()
        if feature == "auth":
          self.esmtp_features[feature] = self.esmtp_features.get(feature, "") \
              + " " + params
        else:
          self.esmtp_features[feature] = params

    return (code, msg)

  def ehlo_helo(self):
    if not (200 <= self.ehlo()[0] <= 299) and not (200 <= self.helo()[0] <= 299):
      raise Exception("Cannot start tls: fail at ehlo|helo")

  def starttls(self):
    self.ehlo_helo()
    (code, msg) = self.cmd("STARTTLS")
    if code == 220:
      context = ssl._create_stdlib_context(certfile=None, keyfile=None)
      self.sock = context.wrap_socket(self.sock, server_hostname=self.host)
      self.stream = None  # reset stream
    else:
      raise Exception(f"Cannot start tls: {code} - {msg}")

  def auth(self, method):
    func_lkup = {
        'CRAM-MD5': self.auth_cram_md5,
        'PLAIN': self.auth_plain,
        'LOGIN': self.auth_login
    }

    self._auth_challenge_count = 0
    (code, resp) = self.cmd("AUTH", method)
    while code == 334:
      challenge = base64.decodebytes(resp)
      msg = enc_base64(func_lkup[method](challenge).encode('ascii'))
      (code, resp) = self.cmd(msg)
      self._auth_challenge_count += 1
      if self._auth_challenge_count > _MAXCHALLENGE:
        raise Exception(f"Cannot auth, last resp: {resp}")
    return (code, resp)

  def auth_cram_md5(self, challenge):
    return self.username + " " + hmac.HMAC(self.password.encode('ascii'), challenge, 'md5').hexdigest()

  def auth_plain(self, challenge):
    return f"\0{self.username}\0{self.password}"

  def auth_login(self, challenge):
    if self._auth_challenge_count < 1:
      return self.username
    return self.password

  def login(self, username, password):
    self.ehlo_helo()
    server_auth = self.esmtp_features['auth'].split()
    self.username = username
    self.password = password
    authlist = [auth for auth in ['CRAM-MD5',
                                  'PLAIN', 'LOGIN'] if auth in server_auth]
    logging.debug(f'Server accept these kind of auth: {authlist}')
    for method in authlist:
      (code, resp) = self.auth(method)
      if code in (235, 503):
        return (code, resp)

  def sendmail(self, from_addr, to_addrs, subject, message):
    self.ehlo_helo()
    if not isinstance(to_addrs, list):
      to_addrs = [to_addrs]

    message = _fix_eol(MAIL_BODY_FORMAT.format(
        from_addr, ", ".join(to_addrs), subject, message))

    opts = list()
    if self.esmtp:
      if self.esmtp_features.get('size', ''):
        opts.append(f"size={len(message)}")
    opts = ' ' + ' '.join(opts)
    (code, resp) = self.cmd("mail", f"FROM:<{from_addr}>{opts}")
    if code != 250:
      if code == 421:
        self.close()
      else:
        self.rset()
      raise Exception(f"Server refused to send mail from {from_addr} - {resp}")

    send_status = dict()
    for addr in to_addrs:
      (code, resp) = self.cmd("rcpt", f"TO:<{addr}>")
      if code != 250 and code != 251:
        send_status[addr] = (code, resp)
      if code == 421:
        self.close()
        raise Exception(f"Server refused to send mail to {addr} - {resp}")
    if len(send_status) == len(to_addrs):
      # Server refused all
      self.rset()
      logging.error(send_status)
      raise Exception(f"Server refused all to_addrs")
    (code, resp) = self.data(message)
    return (code, resp)

  def data(self, msg):
    (code, resp) = self.cmd("data")
    if code != 354:
      raise Exception(f"Data error - {resp}")
    msg = _fix_eol(msg).encode(self.encoding)

    # Some quacky period shit, end of msg need to be <CRLF>.<CRLF>
    # https://datatracker.ietf.org/doc/html/rfc821#:~:text=NOOP%0A%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20%20QUIT%0A%0A%20%20%20%20%20%204.5.2.-,TRANSPARENCY,-Without%20some%20provision
    msg = _quote_periods(msg)
    if msg[-2:] != bCRLF:
      msg = msg + bCRLF
    msg = msg + b"." + bCRLF

    self.send(msg)
    return self.get_reply()

  def rset(self):
    return self.cmd("rset")

  def noop(self):
    return self.cmd("noop")

  def quit(self):
    resp = self.cmd("quit")
    self.close()
    return resp


def main():
  client = My_SMTP(*GOOGLE_TLS)
  client.starttls()
  client.login(*ACCOUNT_NAME_PASS)
  client.sendmail(ACCOUNT_NAME_PASS[0], TEST_ACCOUNT_NAME,
                  "TestSubject", "Hello world!")
  client.quit()


if __name__ == "__main__":
  main()
