import selectors
import socket
import logging
import re
import sys
from selectors import SelectSelector

logging.basicConfig(
    format='%(asctime)s - [%(levelname)s] - %(message)s', level=logging.DEBUG)

CRLF = '\r\n'
bCRLF = b'\r\n'
_MAX_LINE = 4096

HeaderRe = re.compile(r"(?P<Key>.+): (?P<Value>.+)")
HTTPRe = re.compile(r"(?P<ReqType>.*) (?P<URI>.*) HTTP/(?P<HTTPVersion>.*)")


def _fix_eol(msg):
  return re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, msg)


class Server:
  def __init__(self, host="127.0.0.1", port=8080, queue_size=5, poll_timeout=1.0):
    self.host = host
    self.port = port
    self.request_queue_size = queue_size
    self.poll_timeout = poll_timeout
    self._bind()

  def _bind(self):
    self.sock = socket.socket()
    self.sock.bind((self.host, self.port))
    self.sock.listen(self.request_queue_size)
    logging.info(f"Server is listening on http://{self.host}:{self.port}")
    self.sock.setblocking(False)

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

  def __exit__(self):
    try:
      self.sock.shutdown(socket.SHUT_RDWR)
    except OSError:
      pass
    self.sock.close()

  def hand_req(self):
    req, addr = self.sock.accept()
    stream = req.makefile("rb")
    try:
      logging.info(f"New connection from {addr}")
      header = self.process_header(stream)
    finally:
      stream.close()
      req.close()

  def process_header(self, stream):
    data = self._get_resp(stream)
    print(data.decode())

  def serve_forever(self):
    with SelectSelector() as selector:
      selector.register(self, selectors.EVENT_READ)
      try:
        while True:
          ready = selector.select(self.poll_timeout)
          if ready:
            self.hand_req()
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
  s = Server().start()


if __name__ == "__main__":
  main()
