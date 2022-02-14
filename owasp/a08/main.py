import secrets
import os
import cow
import pickle
from flask import Flask, request, redirect, url_for, render_template_string, make_response, flash
from base64 import b64decode, b64encode
from db import User

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)
__VERSION__ = {
    "Major": 1,
    "Minor": 0,
    "Patch": 0
}
SECRET_CHECK = b"\xff\xfe"

os.environ["WERKZEUG_DEBUG_PIN"] = "off"

db = User()

form = """<form action="/login" method="post">
  <label for="username"><b>Username</b></label>
  <input type="text" placeholder="Enter Username" name="username" required>
  <br>
  <label for="password"><b>Password</b></label>
  <input type="password" placeholder="Enter Password" name="password" required>
  <br>
  <button type="submit">Login</button>
</form>
<a href="/register">Create new account</a>
{% if error %}
  <p style="color:red"><strong>Error:</strong> {{ error }}</p>
{% endif %}
<h5>Version {{ Major }}.{{ Minor }}.{{ Patch }}</h5>
"""

register_form = """<form action="/register" method="post">
  <label for="username"><b>Username</b></label>
  <input type="text" placeholder="Enter Username" name="username" required>
  <br>
  <label for="password"><b>Password</b></label>
  <input type="password" placeholder="Enter Password" name="password" required>
  <br>
  <label for="password2"><b>Retype password</b></label>
  <input type="password" placeholder="Retype password" name="password2" required>
  <br>
  <label for="fullname"><b>Full name</b></label>
  <input type="text" placeholder="Enter fullname" name="fullname">
  <br>
  <label for="phone"><b>Phone</b></label>
  <input type="text" placeholder="Enter phone number" name="phone">
  <br>
  <label for="email"><b>Email</b></label>
  <input type="text" placeholder="Enter email" name="email">
  <br>
  <button type="submit">Submit</button>
</form>
{% if error %}
  <p style="color:red"><strong>Error:</strong> {{ error }}</p>
{% endif %}
<h5>Version {{ Major }}.{{ Minor }}.{{ Patch }}</h5>
"""

info_page = """
<h1>Hello {{ username }} </h1>
<form action="/logout" method="post"><button type="submit">Logout</button></form>
<hr>
<h3>User information:</h3>
<p><b>Password</b>: {{ password }}</p>
<p><b>Full name</b>: {{ fullname }}</p>
<p><b>Phone</b>: {{ phone }}</p>
<p><b>Email</b>: {{ email }}</p>
<hr>
<form action="/update" method="post" enctype=multipart/form-data>
  <input type=file name=file>
  <button type=submit value=Upload>Update</button>
</form>
<hr>
<form action="/{{ id }}" method="post">
  <input type="text" placeholder="Random cow say" name="cowsay">
  <button type="submit">Send</button>
</form>
{% if msg %}
  <pre>{{ msg }}</pre>
{% endif %}
<h5>Version {{ Major }}.{{ Minor }}.{{ Patch }}</h5>
"""


def add_user(username, password, fullname, phone, email):
  password = b64encode(password.encode()).decode()
  db.insert_user(username, password, fullname, phone, email)


def parse_user(data):
  field = ["id", "username", "password", "fullname", "phone", "email"]
  return dict(zip(field, data))


@app.route("/login", methods=["GET", "POST"])
def login():
  error = None
  if request.method == "POST":
    username = request.form["username"]
    password = request.form["password"]
    user = db.check_user(username)
    if not user:
      error = "User not found"
    else:
      user = parse_user(user)
      user["password"] = b64decode(user["password"]).decode()
      if user["password"] != password:
        if user["password"].startswith(password):
          error = "Try again"
        else:
          error = "Wrong password"
      else:
        resp = make_response(redirect(url_for("homepage", id=user["id"])))
        resp.set_cookie("id", str(user["id"]))
        return resp
  return render_template_string(form, error=error, **__VERSION__)


@app.route("/register", methods=["GET", "POST"])
def register():
  error = None
  if request.method == "POST":
    uname = request.form.get("username")
    passwd = request.form.get("password")
    passwd2 = request.form.get("password2")
    fullname = request.form.get("fullname")
    phone = request.form.get("phone")
    email = request.form.get("email")
    if not uname:
      error = "User name must not be empty"
    elif not passwd:
      error = "Password must not be empty"
    elif not passwd2:
      error = "Please retype password"
    elif passwd != passwd2:
      error = "Retype password is not the same as password"
    elif len(passwd) < 5:
      error = "Password must be longer than 5 character"
    else:
      add_user(uname, passwd, fullname, phone, email)
      return redirect(url_for("login"))
  return render_template_string(register_form, error=error, **__VERSION__)


@app.route("/", defaults={"id": -1})
@app.route("/<int:id>", methods=["GET", "POST"])
def homepage(id):
  msg = None
  if not request.cookies.get("id"):
    return redirect(url_for("login"))
  if request.method == "POST":
    msg = request.form.get("cowsay")
    msg = cow.milk_random_cow(msg)
  user_info = db.get_user(id)
  if not user_info:
    return "<h1 style='color: red'>User not found</h1>", 404
  user_info = parse_user(user_info)
  return render_template_string(info_page, **user_info, msg=msg, **__VERSION__)


@app.route("/update", methods=["POST"])
def update_app():
  if "file" in request.files:
    file = request.files["file"]
    if file and file.filename:
      content = file.stream.read()
      if content[:2] == SECRET_CHECK:
        global __VERSION__
        content = pickle.loads(content[2:])
        if isinstance(content, dict):
          if "Major" in content:
            __VERSION__["Major"] = content["Major"]
          if "Minor" in content:
            __VERSION__["Minor"] = content["Minor"]
          if "Patch" in content:
            __VERSION__["Patch"] = content["Patch"]
  return redirect(request.referrer)


@app.route("/logout", methods=["POST"])
def logout():
  resp = make_response(redirect(url_for("login")))
  resp.set_cookie("id", "", expires=0)
  return resp


if __name__ == "__main__":
  # uncomment then run ONCE then comment
  # add_user("john", "12345", "johnson baby", 12341234, "john@gmail.com")
  # add_user("steve", "password", "steven univer", 55435345, "steve@hotmail.com")
  # add_user("hana", "11111", "Hasta La Vista Baby", 88889999, "hana@yahoo.com")
  # add_user("cow", "aaaaaa", "cowsay", 12341234, "cow@gmail.com")
  app.run("0.0.0.0", port=8888, debug=True)
