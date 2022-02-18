import re
import html
from pathlib import Path
from .index import parse_options as index_parse
from .user import parse_options as user_parse
from .message import parse_options as message_parse
from .problem import parse_options as problem_parse
from .challenge import parse_options as challenge_parse

PREFIX = "template/"
CRLF = "\r\n"


parser_list = {
    "index.html": index_parse,
    "user.html": user_parse,
    "message.html": message_parse,
    "problem.html": problem_parse,
    "challenge.html": challenge_parse,
}


def _fix_eol(msg):
    return re.sub(r"(?:\r\n|\n|\r(?!\n))", CRLF, msg)


def html_safe_escape(data):
    if isinstance(data, str):
        data = html.escape(data)
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            data[idx] = html_safe_escape(value)
    elif isinstance(data, dict):
        for key, value in data.items():
            data[key] = html_safe_escape(value)
    return data


def read_file(path):
    data = ""
    with open(path, "r") as f:
        data = f.read()
    return data


def read_bytes(path):
    data = b""
    with open(path, "rb") as f:
        data = f.read()
    return data


def render(path, args):
    path = Path(PREFIX + path)
    if path.exists():
        print("bef", args)
        args = html_safe_escape(args)
        print("aft", args)
        if parser_list.get(path.name, ""):
            args = parser_list[path.name](args)
        data = read_file(path)
        return _fix_eol(data.format(**args))
    return None


def serve_file(path):
    path = Path(PREFIX + path)
    if path.exists():
        return read_bytes(path)
    return None
