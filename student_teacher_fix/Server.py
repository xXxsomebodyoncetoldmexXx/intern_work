import selectors
import socket
import logging
import re
import sys
import time
import email.utils
from pathlib import Path
from http import HTTPStatus
from platform import python_version as pyver
from Utils import responses, get_err_msg, guess_file_type, unquote
from template import Views

logging.basicConfig(
    format="%(asctime)s - [%(levelname)s] - %(module)s - %(message)s",
    level=logging.INFO,
)

CRLF = "\r\n"
bCRLF = b"\r\n"
_MAX_DATA = 65537

_HeaderRe = re.compile(r"(?P<Key>.+): (?P<Value>.+)")
_HTTPRe = re.compile(r"(?P<ReqType>.*) (?P<URI>.*) HTTP/(?P<HTTPVersion>.*)")


class SimpleServer:
    def __init__(self, host="127.0.0.1", port=8080, queue_size=10):
        self.host = host
        self.port = port
        self.request_queue_size = queue_size
        self.__header_buffer = {}
        self.__cookie_buffer = {}
        self.header = {}
        self.__init_resp = b""
        self.body = b""
        self.rbody = b""
        self.c_sock = None
        self.middlewares = []
        self.routes = []
        self._bind()

    def _bind(self):
        self.sock = socket.socket()
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen(self.request_queue_size)
        logging.info(f"Server is listening on http://{self.host}:{self.port}")

    def _server_version(self):
        return f"MySimpleHTTP/1.0 Python/{pyver()}"

    def _get_time(self):
        t = time.time()
        return email.utils.formatdate(t, usegmt=True)

    def _get_resp(self):
        data = self.c_sock.recv(_MAX_DATA).strip(b" \r\t\n")
        logging.debug(f"recv lines {data}")
        return data.split(b"\r\n\r\n")

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
        path, query = uri.split("?", 1)
        if not query[1]:
            return (path, {}, "")
        query, *fragment = query.split("#", 1)
        params = dict()
        if query:
            for name_value in query.split("&"):
                if name_value:
                    nv = name_value.split("=", 1)
                    if nv and len(nv) == 2:
                        name = nv[0].replace("+", " ")
                        name = unquote(name)
                        value = nv[1].replace("+", " ")
                        value = unquote(value)
                        params[name] = value
        return (path, params, fragment)

    def _process_header(self, raw):
        data = [s.decode() for s in raw.split(b"\r\n")]
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
                        (
                            self.header["File-Path"],
                            self.header["Params"],
                            self.header["Fragment"],
                        ) = self._process_params(self.header["URI"])
                    else:
                        self.header["File-Path"] = self.header["URI"]
                        self.header["Params"] = {}
                        self.header["Fragment"] = None

    def _process_body(self, raw):
        if raw:
            return raw[0].strip().decode()
        return ""

    def __clean_up(self):
        self.__init_resp = b""
        self.__header_buffer = {}
        self.__cookie_buffer = {}
        self.header = {}
        self.body = b""
        self.rbody = b""
        try:
            self.c_sock.shutdown(socket.SHUT_RDWR)
            self.c_sock.close()
        except (OSError, AttributeError):
            pass
        self.c_sock = None

    def __translate_header(self):
        h = list()
        for key, value in self.__header_buffer.items():
            line = f"{key}: {value}"
            h.append(line.encode("latin-1", "strict"))
        h.extend(self.__translate_cookie())
        return bCRLF.join(h) + bCRLF + bCRLF

    def __translate_cookie(self):
        c = list()
        for key, value in self.__cookie_buffer.items():
            line = f"Set-Cookie: {key}={value}"
            c.append(line.encode("latin-1", "strict"))
        return c

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
            self.routes.append(
                {
                    "route": route,
                    "methods": methods,
                    "func": func,
                    "argc": len(args) + len(kwargs),
                }
            )

        return decorator

    def set_resp_code(self, code):
        self.__init_resp = f"HTTP/1.0 {code} {responses[code][0]}{CRLF}".encode()

    def set_header(self, key, value):
        self.__header_buffer[key] = value

    def set_cookie(self, key, value):
        self.__cookie_buffer[key] = value

    def redirect(self, path, is_post=False):
        if is_post:
            self.set_resp_code(HTTPStatus.FOUND)
        else:
            self.set_resp_code(HTTPStatus.TEMPORARY_REDIRECT)
        self.set_header("Location", path)

    def hander_req(self):
        try:
            self.c_sock, addr = self.sock.accept()
            logging.debug(f"New connection from {addr}")
            raw_header, *raw_body = self._get_resp()
            if len(raw_header):
                self._process_header(raw_header)
                logging.debug(self.header)
                logging.info(
                    f"{addr[0]} - {self.header['Request-Type']} - {self.header['URI']}"
                )
                if self.header["Request-Type"] in ("POST", "PUT"):
                    self.rbody = self._process_body(raw_body)

                # Run middlewares
                for func in self.middlewares:
                    end_resp = func(self)
                    if end_resp:
                        return self._do_resp()

                #if self.header.get("Connection", "") != "close":
                self.hander_resp()
        finally:
            self.__clean_up()

    def hander_resp(self):
        self.set_header("Server", self._server_version())
        self.set_header("Date", self._get_time())
        self.set_header("Connection", "close")

        # routing
        for route in self.routes:
            logging.debug(
                f"Try to match {route['route']} to path {self.header['File-Path']}"
            )
            mo = route["route"].match(self.header["File-Path"])
            if mo and self.header["Request-Type"] in route["methods"]:
                logging.debug("MATCH")
                self.set_resp_code(HTTPStatus.OK)  # default resp
                self.set_header("Content-Type", "text/html")  # default type
                if route["argc"] > 1:
                    route["func"](self, mo.groups())
                else:
                    route["func"](self)
                return self._do_resp()

        # default route
        self.set_resp_code(HTTPStatus.NOT_FOUND)
        self.body = Views.render("error.html", get_err_msg(HTTPStatus.NOT_FOUND))
        self._do_resp()

    def start(self):
        try:
            while True:
                self.hander_req()
        except KeyboardInterrupt:
            print("\nKeyboard interrupt received, exiting.")
        finally:
            self.__exit__()


def main():
    app = SimpleServer(host="0.0.0.0")

    @app.middleware
    def serve_script_file(request):
        file = Path(request.header["File-Path"].lstrip("/"))
        if file.exists() and file.is_file() and file.suffix == ".js":
            request.set_resp_code(HTTPStatus.OK)
            request.set_header("Content-type", guess_file_type(file))
            with open(file, "rb") as f:
                request.body = f.read()
            return True

    @app.route("/")
    def test(request):
        request.set_resp_code(HTTPStatus.OK)
        request.body = "<h1>test</h1>"

    @app.route("/path1")
    def test2(request):
        request.redirect("/")

    app.start()


if __name__ == "__main__":
    main()
