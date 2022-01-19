from base64 import b64decode
import html
import mimetypes
import re
import email
from http import HTTPStatus
from pathlib import Path
from subprocess import Popen, PIPE

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

_asciire = re.compile('([\x00-\x7f]+)')
_hex_digits = '0123456789ABCDEFabcdef'
_hex_to_bytes = {(a + b).encode(): bytes.fromhex(a + b)
                 for a in _hex_digits for b in _hex_digits}


def get_err_msg(code):
  try:
    shortmsg, longmsg = responses[code]
  except KeyError:
    shortmsg, longmsg = '???', '???'
  return {
      "code": code,
      "message": html.escape(shortmsg, quote=False),
      "explain": html.escape(longmsg, quote=False)
  }


def guess_file_type(path):
  path = Path(path)
  ext = path.suffix
  if ext in extensions_map:
    return extensions_map[ext]
  guess, _ = mimetypes.guess_type(path)
  if guess:
    return guess
  return 'application/octet-stream'


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


def scan_host(ip):
  cmd = f"nmap {ip}"
  data = b''
  with Popen(cmd, stdout=PIPE, shell=True) as proc:
    data = proc.stdout.read()
  return data


def b64_to_list(data):
  return b64decode(data.split(",", 1)[1]).decode()
