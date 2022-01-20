import json
from http import HTTPStatus
from Server import SimpleServer
from pathlib import Path
from hashlib import sha256
from base64 import b64encode, b64decode


from Utils import guess_file_type, get_err_msg, scan_host, b64_to_list
from template import Views
from db.Users import Users
from db.Server import Server

HOST = "0.0.0.0"
PORT = 8080
STATIC_FILE_EXT = [".js", ".css", ".txt", ".jpg", ".jpeg", ".png"]
app = SimpleServer(host=HOST, port=PORT)

models = {
    "Users": Users(),
    "Server": Server()
}


def main():
  @app.middleware
  def serve_static_file(request):
    filename = request.header["File-Path"]
    if Path(filename).suffix in STATIC_FILE_EXT:
      request.body = Views.serve_file(filename)
      if request.body:
        request.set_resp_code(HTTPStatus.OK)
        request.set_header("Content-Type", guess_file_type(filename))
      else:
        request.set_resp_code(HTTPStatus.NOT_FOUND)
        request.body = Views.render(
            "error.html", get_err_msg(HTTPStatus.NOT_FOUND))
        request.set_header(
            "Content-Type", guess_file_type("template/error.html"))
      return True

  @app.middleware
  def parse_cookie(request):
    cookies = request.header.get("Cookie", "")
    if cookies:
      c = {}
      for cookie in cookies.split(";"):
        k, v = cookie.strip().split("=", 1)
        c[k] = v
      request.header["Cookie"] = c

  @app.middleware
  def json_data(request):
    if request.header.get("Content-Type", "") and request.header["Content-Type"] == "application/json":
      request.rbody = json.loads(request.rbody)

  @app.middleware
  def form_data(request):
    if request.header.get("Content-Type", "") and request.header["Content-Type"] == "application/x-www-form-urlencoded":
      # hacky
      _, request.rbody, _ = request._process_params("?" + request.rbody)

  @app.middleware
  def Authentication(request):
    cookies = request.header.get("Cookie", "")
    if not cookies and request.header["File-Path"] != "/login":
      request.redirect("/login")
      return True
    elif cookies:
      result = models["Users"].get_user_by_id(
          request.header["Cookie"].get("id", ""))
      if result:
        userid, name, passwd, _ = request.header["Current-User"] = result[0]
        h = sha256(f"{userid}&{name}&{passwd}".encode()).hexdigest()
        if h != request.header["Cookie"].get("check", ""):
          request.redirect("/login")
          return True
      else:
        request.redirect("/login")
        return True

  @app.middleware
  def get_user_servers(request):
    if request.header.get("Current-User", ""):
      request.header["Controlled-Servers"] = models["Server"].get_user_servers(
          request.header["Current-User"][0])

  @app.route("/login", methods=("GET", "POST"))
  def login(request):
    if request.header["Request-Type"] == "GET":
      request.body = Views.render("login.html", {"error-msg": ""})
    else:
      login_info = request.rbody
      username = login_info.get("username", "")
      password = login_info.get("password", "")
      result = models["Users"].get_user(username, password)
      print("LOGIN", login_info, result)
      if result:
        userid, name, passwd, _ = result[0]
        h = sha256(f"{userid}&{name}&{passwd}".encode()).hexdigest()
        request.set_cookie("id", str(userid))
        request.set_cookie("check", h)
        return request.redirect("/", is_post=True)
      request.body = Views.render(
          "login.html", {"error-msg": "Wrong username or password"})
    request.set_header("Content-Type", "text/html")

  @app.route("/", methods=("GET", "POST"))
  def homepage(request):
    servers = [col[1] for col in request.header["Controlled-Servers"]]
    scan_result = ""
    other_users = ""
    if request.header["Request-Type"] == "POST":
      if request.rbody.get("ip", ""):
        if "base64" in request.rbody["ip"]:
          request.rbody["ip"] = b64_to_list(request.rbody["ip"])
        server_ip = request.rbody["ip"].split()
        for ip in server_ip:
          scandata = b64encode(scan_host(ip)).decode()
          models["Server"].insert_server(
              request.header["Current-User"][0], ip, scandata)
      elif request.rbody.get("delete", ""):
        models["Server"].delete_server(
            request.header["Current-User"][0], request.rbody["delete"])

      # admin right
      elif request.rbody.get("delete-user", ""):
        models["Users"].delete_user(request.rbody["delete-user"])
      elif request.rbody.get("delete-ip", ""):
        user = models["Users"].get_user_by_name(request.rbody["user"])
        models["Server"].delete_server(
            str(user[0][0]), request.rbody["delete-ip"])
      return request.redirect("/", is_post=True)

    if request.header.get("Params", None):
      h = request.header["Params"].get("get-result", "")
      if h:
        if h == "*":
          scan_result = []
          for ip in servers:
            result = models["Server"].get_scan_result(
                request.header["Current-User"][0], ip)[0][0]
            scan_result.append(b64decode(result).decode())
        else:
          scan_result = b64decode(models["Server"].get_scan_result(
              request.header["Current-User"][0], h)[0][0]).decode()
    # is admin
    if request.header["Current-User"][3]:
      other_users = {}
      for user in models["Users"].get_users():
        if user[0] != request.header["Current-User"][0]:
          other_users[user[1]] = [col[1]
                                  for col in models["Server"].get_user_servers(user[0])]
    request.body = Views.render(
        "index.html", {"username": request.header["Current-User"][1], "servers": servers, "result": scan_result, "other_user": other_users})


if __name__ == "__main__":
  # Populate data for testing
  # models["Users"].insert_user("admin", "root")
  # models["Users"].insert_user("john", "password")
  # models["Users"].insert_user("test", "1234")
  # models["Users"]._set_admin("admin", "root")

  main()
  app.start()
