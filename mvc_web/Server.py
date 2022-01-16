import html
import selectors
import socket
import logging
import re
import sys
import mimetypes
import time
import json
import email.utils
from base64 import b64decode
from pathlib import Path
from selectors import SelectSelector
from http import HTTPStatus
from platform import python_version as pyver

# Dev
from pprint import pprint
import json

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(module)s - %(message)s', level=logging.INFO)

CRLF = '\r\n'
bCRLF = b'\r\n'
_MAX_LINE = 4096

_HeaderRe = re.compile(r"(?P<Key>.+): (?P<Value>.+)")
_HTTPRe = re.compile(r"(?P<ReqType>.*) (?P<URI>.*) HTTP/(?P<HTTPVersion>.*)")
_asciire = re.compile('([\x00-\x7f]+)')
_hex_digits = '0123456789ABCDEFabcdef'
_hex_to_bytes = {(a + b).encode(): bytes.fromhex(a + b)
                 for a in _hex_digits for b in _hex_digits}


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

  support_request_type = ("GET", "POST", "HEAD")

  def __init__(self, host="127.0.0.1", port=8080, queue_size=5, poll_timeout=0.1):
    self.host = host
    self.port = port
    self.request_queue_size = queue_size
    self.poll_timeout = poll_timeout
    self.__header_buffer = {}
    self.header = {}
    self.__init_resp = b""
    self.body = b""
    self.c_sock = None
    self.c_stream = None
    self.middlewares = []
    self.routes = []
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

  def _get_resp(self):
    resp = []
    blank_count = 0
    while True:
      line = self.c_stream.readline(_MAX_LINE).strip(b" \r\t\n")
      logging.debug(f"recv {line}")
      if not line:
        blank_count += 1
      elif line and blank_count:
        blank_count = 0
      if blank_count == 2:
        break
      resp.append(line)
    return b'\n'.join(resp)

  def _do_resp(self):
    if isinstance(self.body, str):
      self.body = self.body.encode()
    self.set_header("Content-Length", str(len(self.body)))

    data = self.__init_resp
    data += self.__translate_header()
    data += self.body
    while not data.endswith(bCRLF + bCRLF):
      data += bCRLF
    self.c_sock.sendall(data)
    logging.debug(b"send %s" % data)

  def _process_params(self, uri):
    path, query = uri.split('?', 1)
    if not query[1]:
      return (path, {}, '')
    query, fragment = query.split('#', 1)[0]
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
    return (path, params, fragment)

  def _process_header(self, raw):
    data = [s.decode() for s in raw.split(b'\n')]
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
            self.header["File-Path"], self.header["Params"], self.header["Fragment"] = self._process_params(
                self.header["URI"])
          else:
            self.header["File-Path"] = self.header["URI"]

  def _process_body(self, raw):
    if raw:
      return raw[0].decode()
    return ''

  def __clean_up(self):
    self.__init_resp = b""
    self.__header_buffer = {}
    self.header = {}
    self.body = b""
    self.c_stream.close()
    try:
      self.c_sock.shutdown(socket.SHUT_RDWR)
    except OSError:
      pass
    self.c_sock.close()
    self.c_stream = None
    self.c_sock = None

  def __translate_header(self):
    h = list()
    for key, value in self.__header_buffer.items():
      line = f"{key}: {value}"
      h.append(line.encode('latin-1', 'strict'))
    return bCRLF.join(h) + bCRLF + bCRLF

  def __exit__(self):
    try:
      self.sock.shutdown(socket.SHUT_RDWR)
    except OSError:
      pass
    self.sock.close()

  def middleware(self, func):
    self.middlewares.append(func)

  def route(self, route, methods=("GET")):
    if isinstance(route, str):
      # Make raw string
      route = route.encode("unicode_escape").decode()
    route = re.compile(r"^%s$" % route)

    def decorator(func, *args, **kwargs):
      self.routes.append({
          "route": route,
          "methods": methods,
          "func": func,
          "argc": len(args) + len(kwargs)
      })
    return decorator

  def set_resp_code(self, code):
    self.__init_resp = f"HTTP/1.0 {code} {self.responses[code][0]}{CRLF}".encode(
    )

  def set_header(self, key, value):
    self.__header_buffer[key] = value

  def redirect(self, path):
    self.set_resp_code(HTTPStatus.MOVED_PERMANENTLY)
    self.set_header("Location", path)

  def hander_req(self):
    try:
      self.c_sock, addr = self.sock.accept()
      self.c_stream = self.c_sock.makefile("rb")
      logging.debug(f"New connection from {addr}")
      raw_header, *raw_body = self._get_resp().split(b"\n\n")
      if len(raw_header):
        self._process_header(raw_header)
        self.body = self._process_body(raw_body)
        logging.debug(self.header)
        logging.info(
            f"{addr[0]} - {self.header['Request-Type']} - {self.header['URI']}")
        if self.header["Request-Type"] in ("POST", "PUT"):
          self.body = self._process_body()

        # Run middlewares
        for func in self.middlewares:
          cont = func(self)
          if not cont:
            return self._do_resp()

        if self.header.get("Connection", "") != "close":
          self.hander_resp()
    finally:
      self.__clean_up()

  def check_parent(self, path):
    path = path.lstrip('/').split('/')
    path = Path(*path)
    parent = []
    for part in list(path.parents)[:-1]:
      parent.append(part if part.exists() else None)
    return (path, parent)

  def guess_file_type(self, path):
    ext = path.suffix
    if ext in self.extensions_map:
      return self.extensions_map[ext]
    guess, _ = mimetypes.guess_type(path)
    if guess:
      return guess
    return 'application/octet-stream'

  def hander_resp(self):
    self.set_header("Server", self._server_version())
    self.set_header("Date", self._get_time())
    self.set_header("Connection", "close")

    # routing
    for route in self.routes:
      logging.debug(
          f"Try to match {route['route']} to path {self.header['File-Path']}")
      mo = route["route"].match(self.header["File-Path"])
      if mo and self.header["Request-Type"] in route["methods"]:
        if route["argc"] > 1:
          route["func"](self, mo.groups())
        else:
          route["func"](self)
        return self._do_resp()

    # default route
    self.set_resp_code(HTTPStatus.NOT_FOUND)
    self._do_resp()

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
      while True:
        self.serve_forever()
    except KeyboardInterrupt:
      print("\nKeyboard interrupt received, exiting.")
      sys.exit(0)

  def fileno(self):
    # For selector
    return self.sock.fileno()


def main():
  app = SimpleServer(host="0.0.0.0")

  @app.middleware
  def serve_script_file(request):
    file = Path(request.header["File-Path"].lstrip("/"))
    if file.exists() and file.is_file() and file.suffix == ".js":
      request.set_resp_code(HTTPStatus.OK)
      request.set_header("Content-type", request.guess_file_type(file))
      with open(file, "rb") as f:
        request.body = f.read()
      return False
    return True

  @app.route("/")
  def test(request):
    request.set_resp_code(HTTPStatus.OK)
    request.body = "<h1> test </h1>"

  @app.route("/path1")
  def test2(request):
    request.redirect("/")

  app.start()


if __name__ == "__main__":
  main()
