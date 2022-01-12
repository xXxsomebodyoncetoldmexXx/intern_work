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
    format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.INFO)

CRLF = '\r\n'
bCRLF = b'\r\n'
_MAX_LINE = 4096

_HeaderRe = re.compile(r"(?P<Key>.+): (?P<Value>.+)")
_HTTPRe = re.compile(r"(?P<ReqType>.*) (?P<URI>.*) HTTP/(?P<HTTPVersion>.*)")
_asciire = re.compile('([\x00-\x7f]+)')
_hex_digits = '0123456789ABCDEFabcdef'
_hex_to_bytes = {(a + b).encode(): bytes.fromhex(a + b)
                 for a in _hex_digits for b in _hex_digits}


ERROR_BODY = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <title>Error response</title>
    </head>
    <body>
        <h1>Error response</h1>
        <p>Error code: {code}</p>
        <p>Message: {message}.</p>
        <p>Error code explanation: {code} - {explain}.</p>
    </body>
</html>
"""

OK_BODY = """\
<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN"
        "http://www.w3.org/TR/html4/strict.dtd">
<html>
    <head>
        <meta http-equiv="Content-Type" content="text/html;charset=utf-8">
        <script
          src="https://cdnjs.cloudflare.com/ajax/libs/axios/0.24.0/axios.min.js"
          integrity="sha512-u9akINsQsAkG9xjc1cnGF4zw5TFDwkxuc9vUp5dltDWYCSmyd0meygbvgXrlc/z7/o4a19Fb5V0OUE58J7dcyw=="
          crossorigin="anonymous"
          referrerpolicy="no-referrer"
        ></script>
        <script type="text/javascript" defer src="/main.js"></script>
        <title>Directory listing for {path}</title>
    </head>
    <body>
        <h1>Directory listing for {path}</h1>
        {body}
        <hr>
        <h1>Upload file to {path}</h1>
        <input type="file" name="upload" id="uploadFile" />
        <button type="button" onclick="saveFile()">Send</button>
    </body>
</html>
"""


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

  def __init__(self, host="127.0.0.1", port=8080, queue_size=5, poll_timeout=1.0):
    self.host = host
    self.port = port
    self.request_queue_size = queue_size
    self.poll_timeout = poll_timeout
    self.__header_buffer = dict()
    self.resp_code = None
    self.header = dict()
    self.body = None
    self.client_sock = None
    self.client_stream = None
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
    resp = list()
    while True:
      line = self.client_stream.readline(_MAX_LINE).strip(b" \r\t\n")
      if not line:
        break
      logging.debug(f"recv {line}")
      resp.append(line)
    # Process
    return b'\n'.join(resp)

  def _do_resp(self, body=b""):
    self._set_header("Content-Length", str(len(body)))

    data = self.resp_code
    data += self.__translate_header()
    data += body
    if not data.endswith(bCRLF):
      data += bCRLF
    self.client_sock.sendall(data)
    logging.debug(b"send %s" % data)

  def _clean_up(self):
    self.resp_code = None
    self.__header_buffer = {}
    self.header = {}
    self.body = None
    self.client_stream.close()
    try:
      self.client_sock.shutdown(socket.SHUT_RDWR)
    except OSError:
      pass
    self.client_sock.close()
    self.client_stream = None
    self.client_sock = None

  def _process_params(self, uri):
    path, query = uri.split('?', 1)
    if not query[1]:
      return (path, {})
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

  def _process_header(self):
    data = [s.decode() for s in self._get_resp().split(b'\n')]
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
          else:
            self.header["File-Path"] = self.header["URI"]

  def _process_body(self):
    data = self._get_resp()
    if self.header["Content-Type"] == "application/json":
      data = json.loads(data)
      data["data"] = data["data"].split(",", 1)[1]
      print(data["data"])
      data["data"] = b64decode(data["data"])
    return data

  def _set_resp_code(self, code):
    self.resp_code = f"HTTP/1.0 {code} {self.responses[code][0]}{CRLF}".encode(
    )

  def _set_header(self, key, value):
    self.__header_buffer[key] = value

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

  def err(self, code):
    try:
      shortmsg, longmsg = self.responses[code]
    except KeyError:
      shortmsg, longmsg = '???', '???'

    self._set_resp_code(code)
    self._set_header("Connection", "close")
    body = ERROR_BODY.format(**{
        "code": code,
        "message": html.escape(shortmsg, quote=False),
        "explain": html.escape(longmsg, quote=False)
    })
    body = _fix_eol(body).encode('utf-8', 'replace')
    self._set_header("Content-Type", "text/html;charset=utf-8")
    if self.header["Request-Type"] != "HEAD":
      return self._do_resp(body)
    self._do_resp()

  def redirect(self, path):
    self._set_resp_code(HTTPStatus.MOVED_PERMANENTLY)
    self._set_header("Location", path)
    self._do_resp()

  def hander_req(self):
    try:
      self.client_sock, addr = self.sock.accept()
      self.client_stream = self.client_sock.makefile("rb")
      logging.debug(f"New connection from {addr}")
      self._process_header()
      logging.debug(self.header)
      logging.info(
          f"{addr[0]} - {self.header['Request-Type']} - {self.header['URI']}")
      if self.header["Request-Type"] in ("POST"):
        self.body = self._process_body()
      if self.header.get("Connection", "") != "close":
        self.hander_resp()
    except Exception:
      # FIXME: Some time it die, no idea why????????????????????????????
      # the client send no content and/or browser just end the connection
      pass

  def check_parent(self, path):
    path = path.lstrip('/').split('/')
    path = Path(*path)
    parent = []
    for part in list(path.parents)[:-1]:
      parent.append(part if part.exists() else None)
    return (path, parent)

  def guess_type(self, path):
    ext = path.suffix
    if ext in self.extensions_map:
      return self.extensions_map[ext]
    guess, _ = mimetypes.guess_extension(path)
    if guess:
      return guess
    return 'application/octet-stream'

  def list_dir(self, path):
    self._set_resp_code(HTTPStatus.OK)
    body = []
    lnk = '<li><a href="{name}">{name}</a></li>'
    params = json.dumps(self.header.get("Params", ""), ensure_ascii=False)
    body.append(f"<h2>Parameters include in the request: {params}</h2>")
    body.append("<hr>")
    body.append("<ur>")
    if path.name:
      body.append(lnk.format(**{
          "name": ".."
      }))
    for directory in path.iterdir():
      name = directory.name if directory.is_file() else f"{directory.name}/"
      body.append(lnk.format(**{
          "name": name
      }))
    body.append("</ur>")
    body = OK_BODY.format(**{
        "path": self.header["File-Path"],
        "body": '\n'.join(body)
    }).encode('utf-8', 'replace')
    self._do_resp(body)

  def send_file(self, file):
    self._set_resp_code(HTTPStatus.OK)
    # Only nessensary for live reading
    # self._set_header("Content-type", self.guess_type(file))

    # Instally download
    self._set_header("Content-Type", "application/octet-stream")

    with open(file, "rb") as f:
      content = f.read()
    self._do_resp(content)

  def save_file(self, path):
    # There is a security vulnerability here, but it's just a challenge for web server so i'm just gonna ignore it ;)
    with open(Path(path, self.body["name"]), "wb") as f:
      f.write(self.body["data"])

  def hander_resp(self):
    self._set_header("Server", self._server_version())
    self._set_header("Date", self._get_time())
    path, parents = self.check_parent(self.header["File-Path"])
    if None in parents:
      return self.err(HTTPStatus.NOT_FOUND)
    if self.header["Request-Type"] not in self.support_request_type:
      return self.err(HTTPStatus.NOT_IMPLEMENTED)
    elif self.header["Request-Type"] == "GET":
      # do_GET
      if path.is_dir():
        if not self.header["File-Path"].endswith("/"):
          return self.redirect(self.header["File-Path"] + "/")
        return self.list_dir(path)
      if not path.exists() and path.name:
        return self.err(HTTPStatus.NOT_FOUND)
      self.send_file(path)
    else:
      # do_POST
      if not path.is_dir():
        return self.err(HTTPStatus.NOT_ACCEPTABLE)
      self.save_file(path)
      # Delay
      time.sleep(1)
      self.redirect(self.header["File-Path"])

  def serve_forever(self):
    with SelectSelector() as selector:
      selector.register(self, selectors.EVENT_READ)
      try:
        while True:
          ready = selector.select(self.poll_timeout)
          if ready:
            self.hander_req()
            self._clean_up()
      finally:
        self.__exit__()

  def start(self):
    try:
      while True:
        self.serve_forever()
    except KeyboardInterrupt:
      print("\nKeyboard interrupt received, exiting.")
      sys.exit(0)
    # except Exception:
    #   logging.CRITICAL(f"Server reboot")
    #   time.sleep(3)

  def fileno(self):
    # For selector
    return self.sock.fileno()


def main():
  SimpleServer().start()


if __name__ == "__main__":
  main()
