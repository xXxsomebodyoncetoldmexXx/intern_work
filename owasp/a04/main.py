import secrets

from flask import Flask, request, redirect, url_for, render_template_string, make_response, flash
from base64 import b64decode, b64encode
from db import User

app = Flask(__name__)
app.secret_key = secrets.token_bytes(32)

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
{% if error %}
    <p style="color:red"><strong>Error:</strong> {{ error }}</p>
{% endif %}
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
  return render_template_string(form, error=error)


@app.route("/", defaults={"id": -1})
@app.route("/<int:id>")
def homepage(id):
  if not request.cookies.get("id"):
    return redirect(url_for("login"))
  user_info = db.get_user(id)
  if not user_info:
    return "<h1>User not found</h1>", 404
  user_info = parse_user(user_info)
  return render_template_string(info_page, **user_info)


@app.route("/logout", methods=["POST"])
def logout():
  resp = make_response(redirect(url_for("login")))
  resp.set_cookie("id", "", expires=0)
  return resp


if __name__ == "__main__":
  # uncomment then run ONCE then comment
  # add_user("john", "1234", "johnson baby", 12341234, "john@gmail.com")
  # add_user("steve", "password", "steven univer", 55435345, "steve@hotmail.com")
  # add_user("hana", "1111", "Hasta La Vista Baby", 88889999, "hana@yahoo.com")
  # add_user("cow", "798789", "cowsay", 12341234, "cow@gmail.com")
  app.run("0.0.0.0", port=8888, debug=True)
