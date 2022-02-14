from flask import Flask, request, redirect, url_for, render_template_string, make_response
from base64 import b64encode

app = Flask(__name__)

db = []

form = """<form action="/login" method="post">
  <label for="username"><b>Username</b></label>
  <input type="text" placeholder="Enter Username" name="username" required>
  <br>
  <label for="password"><b>Password</b></label>
  <input type="password" placeholder="Enter Password" name="password" required>
  <br>
  <button type="submit">Login</button>
</form>
"""

info_page = """
<h1>Hello {{ username }} </h1>
<hr>
<h3>User information:</h3>
<p><b>Password</b>: {{ password }}</p>
<p><b>Full name</b>: {{ fullname }}</p>
<p><b>Phone</b>: {{ phone }}</p>
<p><b>Email</b>: {{ email }}</p>
"""


def add_user(username, password, fullname, phone, email):
  global db
  db.append({
      "username": username,
      "password": b64encode(password.encode()).decode(),
      "fullname": fullname,
      "phone": phone,
      "email": email
  })


@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    for id, user in enumerate(db):
      if user["username"] == request.form["username"] and user["password"] == b64encode(request.form["password"].encode()).decode():
        resp = make_response(redirect(url_for("homepage", id=id)))
        resp.set_cookie("id", str(id))
        return resp
  return form


@app.route("/", defaults={"id": -1})
@app.route("/<int:id>")
def homepage(id):
  if not request.cookies.get("id"):
    return redirect(url_for("login"))
  if id < 0 or id >= len(db):
    return "<h1>User not found</h1>", 404
  return render_template_string(info_page, **db[id])


if __name__ == "__main__":
  add_user("john", "1234", "johnson baby", 12341234, "john@gmail.com")
  add_user("steve", "password", "steven univer", 55435345, "steve@hotmail.com")
  add_user("hana", "1111", "Hasta La Vista Baby", 88889999, "hana@yahoo.com")
  add_user("cow", "798789", "cowsay", 12341234, "cow@gmail.com")
  app.run("0.0.0.0", port=8888, debug=True)
