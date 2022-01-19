import re
from pathlib import Path


PREFIX = "template/"
CRLF = "\r\n"


def _fix_eol(msg):
  return re.sub(r'(?:\r\n|\n|\r(?!\n))', CRLF, msg)


def read_file(path):
  data = ''
  with open(path, "r") as f:
    data = f.read()
  return _fix_eol(data)


def read_bytes(path):
  data = b''
  with open(path, "rb") as f:
    data = f.read()
  return data


def servers_to_html(servers):
  result = ["<ul>"]
  result.append(CRLF.join(
      [f"<li><span>\
          <form class='form' method='get'><button type='submit' class='btn' name='get-result' value='{ip}'>{ip}</button></form>\
          <form class='form' method='post'><button type='submit' class='btn' name='delete' value='{ip}'>delete</button></form>\
        </span></li>" for ip in servers]))
  result.append("</ul>")
  return CRLF.join(result) + CRLF


def result_to_html(scan_result):
  result = ["<h2>Scan result</h2>"]
  if isinstance(scan_result, list):
    for r in scan_result:
      result.append(f"<hr /><p>{_fix_eol(r)}</p>")
  else:
    result.append(f"<hr /><p>{_fix_eol(scan_result)}</p>")
  return CRLF.join(result) + CRLF


def users_to_html(users):
  result = ["<hr />", "<h2>Admin control</h2>"]
  for name, servers in users.items():
    result.append(
        f"<form class='form' method='post'>\
            {name}\
            <button type='submit' class='btn' name='delete-user' value='{name}'>delete user</button>\
          </form>")
    result.append("<ul>")
    for ip in servers:
      result.append(
          f"<li><form class='form' method='post'>\
              {ip}\
              <input type='hidden' name='user' value='{name}'>\
              <button type='submit' class='btn' name='delete-ip' value='{ip}'>delete</button>\
            </form></li>")
    result.append("</ul>")
  return CRLF.join(result) + CRLF


def render(path, args):
  path = Path(PREFIX + path)
  if path.exists():
    data = read_file(path)
    if args.get("servers", ""):
      args["servers"] = servers_to_html(args["servers"])
    if args.get("result", ""):
      args["result"] = result_to_html(args["result"])
    if args.get("other_user", ""):
      args["other_user"] = users_to_html(args["other_user"])
    return data.format(**args)
  return None


def serve_file(path):
  path = Path(PREFIX + path)
  if path.exists():
    return read_bytes(path)
  return None
