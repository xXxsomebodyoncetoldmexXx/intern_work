import selectors
import socket
import logging
import re
import sys
import mimetypes
import time
import email.utils
from pathlib import Path
from selectors import SelectSelector
from http import HTTPStatus
from platform import pyhon_version as pyver

# Dev
from pprint import pprint
import json

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.DEBUG)

CRLF = '\r\n'
bCRLF = b'\r\n'
_MAX_LINE = 4096

_HeaderRe = re.compile(r"(?P<Key>.+): (?P<Value>.+)")
_HTTPRe = re.compile(r"(?P<ReqType>.*) (?P<URI>.*) HTTP/(?P<HTTPVersion>.*)")
_asciire = re.compile('([\x00-\x7f]+)')
_hex_digits = '0123456789ABCDEFabcdef'
_hex_to_bytes = {(a + b).encode(): bytes.fromhex(a + b)
                 for a in _hex_digits for b in _hex_digits}


def _fix_eol(msg):
  return re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, msg)


def unquote_to_bytes(s):
  if not s:
    return b''
  if isinstance(s, str):
    s = s.encode()
  bits = s.split(b'%')
  if len(bits) == 1:
    return s
  res = [bits[0]]
  for part in bits[1:]:
    if part[:2] in _hex_to_bytes:
      res.append(_hex_to_bytes[part[:2]])
      res.append(part[2:])
    else:
      res.append(b'%' + part)
  return b''.join(res)


def unquote(s):
  if '%' not in s:
    return s
  bits = _asciire.split(s)
  res = [bits[0]]
  for i in range(1, len(bits), 2):
    res.append(unquote_to_bytes(bits[i]).decode('utf-8', 'replace'))
    res.append(bits[i + 1])
  return ''.join(res)


DEFAULT_ERROR_MESSAGE = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Error response</title>
    </head>
    <body>
        <h1>Error response</h1>
        <p>Error code: %(code)d</p>
        <p>Message: %(message)s.</p>
        <p>Error code explanation: %(code)s - %(explain)s.</p>
    </body>
</html>
"""


class SimpleServer:

  extensions_map = {
      '.gz': 'application/gzip',
      '.Z': 'application/octet-stream',
      '.bz2': 'application/x-bzip2',
      '.xz': 'application/x-xz',
  }

  responses = {
      v: (v.phrase, v.description)
      for v in HTTPStatus.__members__.values()
  }

  def __init__(self, host="127.0.0.1", port=8080, queue_size=5, poll_timeout=1.0):
    self.host = host
    self.port = port
    self.request_queue_size = queue_size
    self.poll_timeout = poll_timeout
    self.__header_buffer = dict()
    self.header = dict()
    self._bind()

  def _bind(self):
    self.sock = socket.socket()
    self.sock.bind((self.host, self.port))
    self.sock.listen(self.request_queue_size)
    logging.info(f"Server is listening on http://{self.host}:{self.port}")
    self.sock.setblocking(False)

  def _server_version(self):
    return f"MySimpleHTTP/1.0 Python/{pyver()}"

  def _get_time(self):
    t = time.time()
    return email.utils.formatdate(t, usegmt=True)

  def _get_resp(self, stream):
    resp = list()
    while True:
      line = stream.readline(_MAX_LINE).strip(b" \r\t\n")
      if not line:
        break
      logging.debug(f"recv {line}")
      resp.append(line)
    # Process
    return b'\n'.join(resp)

  def _do_resp(self, sock, data):
    sock.sendall(data)
    self.header = {}

  def _process_params(self, uri):
    path, query = uri.split('?', 1)
    query = query.split('#', 1)[0]
    params = dict()
    if query:
      for name_value in query.split('&'):
        if name_value:
          nv = name_value.split('=', 1)
          if nv and len(nv) == 2:
            name = nv[0].replace('+', ' ')
            name = unquote(name)
            value = nv[1].replace('+', ' ')
            value = unquote(value)
            params[name] = value
    return (path, params)

  def _process_header(self, stream):
    data = [s.decode() for s in self._get_resp(stream).split(b'\n')]
    for line in data:
      mo = _HeaderRe.match(line)
      if mo:
        self.header[mo.group("Key")] = mo.group("Value")
      else:
        mo = _HTTPRe.match(line)
        if mo:
          self.header["Request-Type"] = mo.group("ReqType")
          self.header["URI"] = mo.group("URI")
          self.header["HTTP-Version"] = mo.group("HTTPVersion")
          if "?" in self.header["URI"]:
            self.header["File-Path"], self.header["Params"] = self._process_params(
                self.header["URI"])

  def _process_body(self, stream):
    return self._get_resp(stream)

  def _make_resp(self, code):
    return f"HTTP/1.0 {code} {responses[code][0]}{CRLF}"

  def _set_header(self, key, value):
    self.__header_buffer[key] = value

  def __translate_header(self):
    h = list()
    for key, value in self.__header_buffer.items():
      line = f"{key}: {value}" + CRLF
      h.append(line.encode('latin-1', 'strict'))

    # Clear buffer
    self.__header_buffer = {}
    return CRLF.join(h).encode() + bCRLF

  def _err(self, code, msg=None):
    try:
      shortmsg, longmsg = self.responses[code]
    except KeyError:
      shortmsg, longmsg = '???', '???'
    if not msg:
      msg = shortmsg
    self._set_header("Connection", "close")


    self._set_header("Content-Type", "text/html;charset=utf-8")
    self._set_header("Connection", "close")
    payload = self._make_resp(code)

  def __exit__(self):
    try:
      self.sock.shutdown(socket.SHUT_RDWR)
    except OSError:
      pass
    self.sock.close()

  def hander_req(self):
    req, addr = self.sock.accept()
    stream = req.makefile("rb")
    try:
      logging.info(f"New connection from {addr}")
      self._process_header(stream)
      if self.header["Request-Type"] in ("POST", "PUT"):
        body = self._process_body(stream)
        with open("upload.data", "wb") as f:
          f.write(body)

      self.hander_resp(req)
    finally:
      stream.close()
      req.close()

  def translate_path(self, path):
    path = path.lstrip('/').split('/')
    if len(path) == 1:
      return Path('index.html')
    path = Path(*path)
    # Check file exist
    try:
      path.stat()
      return path
    except FileNotFoundError:
      return None

  def guess_type(self, path):
    ext = path.suffix
    if ext in self.extensions_map:
      return self.extensions_map[ext]
    guess, _ = mimetypes.guess_extension(path)
    if guess:
      return guess
    return 'application/octet-stream'

  def hander_resp(self, sock):
    self._set_header("Server", self._server_version)
    self._set_header("Date", self._get_time)
    path = self.translate_path(self.header["File-Path"])
    if not path:
      return self._err(404)

  def serve_forever(self):
    with SelectSelector() as selector:
      selector.register(self, selectors.EVENT_READ)
      try:
        while True:
          ready = selector.select(self.poll_timeout)
          if ready:
            self.hander_req()
      finally:
        self.__exit__()

  def start(self):
    try:
      self.serve_forever()
    except KeyboardInterrupt:
      print("\nKeyboard interrupt received, exiting.")
      sys.exit(0)

  def fileno(self):
    # For selector
    return self.sock.fileno()


def main():
  SimpleServer().start()


if __name__ == "__main__":
  main()
