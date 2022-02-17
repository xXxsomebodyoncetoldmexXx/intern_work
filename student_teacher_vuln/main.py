import json
import os
from http import HTTPStatus
from Server import SimpleServer
from pathlib import Path
from base64 import b64encode, b64decode
from uuid import uuid4 as uid

from Utils import guess_file_type, get_err_msg, h1, h2, h3
from db import Users, Message, Problem, Answer, Challenge
from template import Views

HOST = "0.0.0.0"
PORT = 8080
STATIC_FILE_EXT = (".js", ".css", ".txt", ".jpg", ".jpeg", ".png")
AUTH_PATH = (
    "/",
    "/index.html",
    "/user",
    "/problem",
    "/challenge",
    "/message",
    "/update-challenge",
    "/delete-challenge",
)
CHALL_PATH = "./chall"

app = SimpleServer(host=HOST, port=PORT)

models = {
    "User": Users.User(),
    "Message": Message.Message(),
    "Problem": Problem.Problem(),
    "Answer": Answer.Answer(),
    "Challenge": Challenge.Challenge(),
}


def parse_user(data):
    field = [
        "userid",
        "username",
        "password",
        "fullname",
        "email",
        "phone",
        "is_teacher",
    ]
    return dict(zip(field, data))


def parse_message(data):
    field = ["messageid", "content", "fromuser", "touser"]
    return dict(zip(field, data))


def parse_problem(data):
    field = ["problemid", "problemname", "content"]
    return dict(zip(field, data))


def parse_answer(data):
    field = ["answerid", "userid", "username", "problemid", "problemname", "content"]
    return dict(zip(field, data))


def parse_unsolve_problem(data):
    field = ["problemid", "problemname"]
    return dict(zip(field, data))


def parse_challenge(data):
    field = ["challname", "hint"]
    return dict(zip(field, data))


def get_challenges():
    challenges = []
    chall_root = Path(CHALL_PATH)
    for child in chall_root.iterdir():
        if child.is_file:
            with open(child, "r") as f:
                content = f.read()
            h = h3(f"{child.name}&{content}")
            chall = models["Challenge"].get_chall(h)
            if chall:
                chall = parse_challenge(chall)
                challenges.append(
                    {
                        "hash": h,
                        "challengename": chall["challname"],
                        "challengehint": chall["hint"],
                        "challangeanswer": child.name,
                        "content": content,
                    }
                )
    return challenges


def check_challenge(name):
    if exists_challenge(name):
        with open(Path(CHALL_PATH, name), "r") as f:
            content = f.read()
        return content


def exists_challenge(name):
    challpath = Path(CHALL_PATH, name)
    if challpath.exists and challpath.is_file():
        return True
    return False


def save_chall(name, content):
    p = Path(CHALL_PATH, name)
    with open(p, "wb") as f:
        f.write(content)


def delete_local_chall(hash):
    chall_root = Path(CHALL_PATH)
    for child in chall_root.iterdir():
        if child.is_file:
            with open(child, "r") as f:
                content = f.read()
            h = h3(f"{child.name}&{content}")
            if h == hash:
                os.remove(child)
                return True
    return False


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
            request.body = Views.render("error.html", get_err_msg(HTTPStatus.NOT_FOUND))
            request.set_header("Content-Type", guess_file_type("template/error.html"))
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
    if (
        request.header.get("Content-Type", "")
        and request.header["Content-Type"] == "application/json"
    ):
        request.rbody = json.loads(request.rbody)


@app.middleware
def form_data(request):
    if (
        request.header.get("Content-Type", "")
        and request.header["Content-Type"] == "application/x-www-form-urlencoded"
        and request.rbody
    ):
        # hacky
        _, request.rbody, _ = request._process_params("?" + request.rbody)


@app.middleware
def Authentication(request):
    cookies = request.header.get("Cookie", "")
    if request.header["File-Path"] in AUTH_PATH:
        if cookies and cookies.get("id", "") and cookies.get("hash", ""):
            result = models["User"].get_user(cookies["id"])
            if result:
                user = parse_user(result)
                hash = h2(f"{user['userid']}&{user['username']}&{user['password']}")
                if hash == cookies["hash"]:
                    request.header["Current-User"] = user
                    return False
        request.redirect("/login")
        return True


@app.route("/login", methods=("GET", "POST"))
def login(request):
    err_msg = ""
    if request.header["Request-Type"] == "POST":
        login_info = request.rbody
        username = login_info.get("username", "")
        password = h1(login_info.get("password", ""))
        result = models["User"].check_user(username, password)
        if result:
            user = parse_user(result[0])
            hash = h2(f"{user['userid']}&{user['username']}&{user['password']}")
            request.set_cookie("id", str(user["userid"]))
            request.set_cookie("hash", hash)
            return request.redirect("/", is_post=True)
        err_msg = "Wrong username or password"
    request.body = Views.render("login.html", {"error-msg": err_msg})


@app.route("/", methods=("GET", "POST"))
def homepage(request):
    args = request.header["Current-User"]
    if args["is_teacher"]:
        args["Other-User"] = [
            parse_user(u)
            for u in models["User"].get_users()
            if u[0] != request.header["Current-User"]["userid"]
        ]

    if request.header["Request-Type"] == "POST" and request.rbody:
        if request.rbody.get("id", ""):
            if request.rbody["id"] == "new-user":
                if request.header["Current-User"]["is_teacher"]:
                    new_username = request.rbody.get("username", "")
                    new_fullname = request.rbody.get("fullname", "")
                    new_password = request.rbody.get("password", "")
                    new_email = request.rbody.get("email", "")
                    new_phone = request.rbody.get("phone", "")
                    if all(
                        (new_username, new_fullname, new_password, new_email, new_phone)
                    ):
                        models["User"].insert_user(
                            new_username,
                            h1(new_password),
                            new_fullname,
                            new_email,
                            new_phone,
                        )
                        return request.redirect("/", is_post=True)
                    else:
                        args[
                            "error-msg-update"
                        ] = "User information field can not be empty"
                else:
                    args[
                        "error-msg-update"
                    ] = "User don't have permission to add new user"
            else:
                userid = request.rbody["id"]
                if (
                    userid != str(request.header["Current-User"]["userid"])
                    and not request.header["Current-User"]["is_teacher"]
                ):
                    args[
                        "error-msg-update"
                    ] = "User don't have permission to change other user information"
                else:
                    if not models["User"].get_user(userid):
                        args["error-msg-update"] = "User don't exists"
                    elif not request.header["Current-User"]["is_teacher"] and (
                        request.rbody.get("username", "")
                        or request.rbody.get("fullname", "")
                    ):
                        args[
                            "error-msg-update"
                        ] = "User don't have permission to change this information"
                    else:
                        old_user = parse_user(models["User"].get_user(userid))
                        new_username = request.rbody.get("username", "")
                        new_username = (
                            new_username if new_username else old_user["username"]
                        )
                        new_fullname = request.rbody.get("fullname", "")
                        new_fullname = (
                            new_fullname if new_fullname else old_user["fullname"]
                        )
                        new_email = request.rbody.get("email", "")
                        new_email = new_email if new_email else old_user["email"]
                        new_phone = request.rbody.get("phone", "")
                        new_phone = new_phone if new_phone else old_user["phone"]
                        new_password = request.rbody.get("password", "")
                        if new_password:
                            new_password = h1(new_password)
                        else:
                            new_password = old_user["password"]
                        result = models["User"].update_user(
                            userid,
                            new_username,
                            new_password,
                            new_fullname,
                            new_email,
                            new_phone,
                        )
                        if result:
                            return request.redirect("/", is_post=True)
                        args["error-msg-update"] = "Error update user information"
        elif request.rbody.get("delete-id", ""):
            bef, aft = models["User"].delete_user(request.rbody["delete-id"])
            if bef:
                if not aft:
                    return request.redirect("/", is_post=True)
                args["error-msg-delete"] = "Fail to delete user"
            else:
                args["error-msg-delete"] = "User not exists"
        else:
            args["error-msg-update"] = args["error-msg-delete"] = "User not selected"

    request.body = Views.render("index.html", args)


@app.route("/logout")
def logout(request):
    request.set_cookie("id", "''; expires=Thu, 01 Jan 1970 00:00:00 GMT")
    request.set_cookie("hash", "''; expires=Thu, 01 Jan 1970 00:00:00 GMT")
    request.redirect("/login")


@app.route("/user", methods=("GET", "POST"))
def check_users(request):
    args = {}
    if request.header["Params"].get("id", ""):
        args["user-info"] = models["User"].get_user(request.header["Params"]["id"])
        args["user-info"] = parse_user(args["user-info"])
        args["send-message"] = [
            parse_message(m)
            for m in models["Message"].get_send_message(
                request.header["Current-User"]["userid"], request.header["Params"]["id"]
            )
        ]
        for m in args["send-message"]:
            try:
                m["content"] = b64decode(m["content"]).decode()
            except:
                pass
        args["error-msg"] = request.header["Params"].get("error-msg", "")
    else:
        args["user-info"] = [
            parse_user(u)
            for u in models["User"].get_users()
            if u[0] != request.header["Current-User"]["userid"]
        ]

    if request.header["Request-Type"] == "POST" and request.rbody:
        if request.rbody.get("id", ""):
            if request.rbody.get("deleteid", ""):
                msg = models["Message"].get_message(request.rbody["deleteid"])
                if msg:
                    msg = parse_message(msg)
                    if msg["fromuser"] == request.header["Current-User"]["userid"]:
                        bef, aft = models["Message"].delete_message(
                            request.rbody["deleteid"]
                        )
                        if bef:
                            if not aft:
                                return request.redirect(
                                    f"/user?id={request.rbody['id']}", is_post=True
                                )
                            args["error-msg"] = "Fail to delete message"
                        else:
                            args["error-msg"] = "Cannot find message"
                    else:
                        args["error-msg"] = "User can not delete other user message"
                else:
                    args["error-msg"] = "Message not found"
            elif request.rbody.get("messageid", ""):
                sendid = request.header["Current-User"]["userid"]
                recvid = request.rbody["id"]
                msg = request.rbody.get("content", "")
                msg = b64encode(msg.encode()).decode()
                if request.rbody["messageid"] == "new-message":
                    result = models["Message"].insert_message(msg, sendid, recvid)
                    return request.redirect(f"/user?id={recvid}", is_post=True)
                else:
                    old_msg = models["Message"].get_message(request.rbody["messageid"])
                    if old_msg:
                        old_msg = parse_message(old_msg)
                        if old_msg["fromuser"] == sendid:
                            models["Message"].update_message(old_msg["messageid"], msg)
                            return request.redirect(f"/user?id={recvid}", is_post=True)
                        args["error-msg"] = "User can not modify other user message"
                    else:
                        args["error-msg"] = "Message not found"
            return request.redirect(
                f"/user?id={request.rbody['id']}&error-msg={args['error-msg']}",
                is_post=True,
            )
    request.body = Views.render("user.html", args)


@app.route("/message")
def message_handle(request):
    args = {}
    args["messages"] = models["Message"].get_user_message(
        request.header["Current-User"]["userid"]
    )
    for i in range(len(args["messages"])):
        args["messages"][i] = (
            args["messages"][i][0],
            b64decode(args["messages"][i][1]).decode(),
        )
    request.body = Views.render("message.html", args)


@app.route("/problem", methods=("GET", "POST"))
def do_problem(request):
    args = {}
    args["problem-list"] = [parse_problem(p) for p in models["Problem"].get_problems()]
    args["is_admin"] = request.header["Current-User"]["is_teacher"]

    if args["is_admin"]:
        args["answer-list"] = [parse_answer(a) for a in models["Answer"].get_answers()]
    else:
        args["answer-list"] = [
            parse_answer(a)
            for a in models["Answer"].get_user_answers(
                request.header["Current-User"]["userid"]
            )
        ]
    # args["unsolve-list"] = [parse_unsolve_problem(p)
    #                         for p in models["Problem"].get_unsolve_problems(request.header["Current-User"]["userid"])]
    args["unsolve-list"] = args["problem-list"]

    # Download section
    if request.header["Params"].get("pid", ""):
        p = models["Problem"].get_problem(request.header["Params"]["pid"])
        if p:
            p = parse_problem(p)
            request.body = b64decode(p["content"])
            return request.set_header("Content-Type", "application/octet-stream")
        args["error-msg"] = "Problem not found"
    elif request.header["Params"].get("aid", ""):
        a = models["Answer"].get_answer(request.header["Params"]["aid"])
        if a:
            a = parse_answer(a)
            if a["userid"] == request.header["Current-User"]["userid"] or (
                args["is_admin"]
            ):
                request.body = b64decode(a["content"])
                return request.set_header("Content-Type", "application/octet-stream")
            args["error-msg"] = "Only admin or owner can get the answer"
        else:
            args["error-msg"] = "Answer not found"

    if request.header["Request-Type"] == "POST" and request.rbody:
        problemid = request.rbody.get("problemid", "")
        answerid = request.rbody.get("answerid", "")
        if answerid:
            if answerid == "new-answer":
                problemid = request.rbody.get("answer-problemid", "")
                content = request.rbody.get("answer-content", "").split(",", 1)
                if not problemid:
                    args["error-msg"] = "User hasn't selected problem to answer"
                elif len(content) < 2:
                    args["error-msg"] = "Answer content is empty"
                elif not models["Problem"].get_problem(problemid):
                    args["error-msg"] = "Problem do not exist"
                else:
                    content = content[1]
                    models["Answer"].insert_answer(
                        request.header["Current-User"]["userid"], problemid, content
                    )
                    return request.redirect("/problem", is_post=True)
            else:
                a = models["Answer"].get_answer(answerid)
                if a:
                    a = parse_answer(a)
                    if a["userid"] == request.header["Current-User"]["userid"] or (
                        args["is_admin"]
                    ):
                        problemid = request.rbody.get("answer-problemid", "")
                        content = request.rbody.get("answer-content", "").split(",", 1)
                        if not models["Problem"].get_problem(problemid):
                            args["error-msg"] = "New problem do not exist"
                        else:
                            problemid = problemid if problemid else a["problemid"]
                            content = content[1] if len(content) == 2 else a["content"]
                            if models["Answer"].update_answer(
                                a["answerid"], problemid, content
                            ):
                                return request.redirect("/problem", is_post=True)
                            args["error-msg"] = "Fail to update answer"
                    else:
                        args["error-msg"] = "User can not update other user answer"
                else:
                    args["error-msg"] = "Answer do not exist"
        elif request.rbody.get("adeleteid", ""):
            a = models["Answer"].get_answer(request.rbody["adeleteid"])
            if a:
                a = parse_answer(a)
                if a["userid"] == request.header["Current-User"]["userid"] or (
                    args["is_admin"]
                ):
                    _, aft = models["Answer"].delete_answer(a["answerid"])
                    if not aft:
                        return request.redirect("/problem", is_post=True)
                    args["error-msg"] = "Fail to delete answer"
                else:
                    args["error-msg"] = "User can not delete other user answer"
            else:
                args["error-msg"] = "Answer do not exist"
        elif args["is_admin"]:
            if problemid:
                if problemid == "new-problem":
                    problemname = request.rbody.get("problemname", "")
                    content = request.rbody.get("problem-content", "").split(",", 1)
                    if not problemname:
                        args["error-msg"] = "Problem name is empty"
                    elif len(content) < 2:
                        args["error-msg"] = "Problem content is empty"
                    else:
                        content = content[1]
                        models["Problem"].insert_problem(problemname, content)
                        return request.redirect("/problem", is_post=True)
                else:
                    old_problem = models["Problem"].get_problem(problemid)
                    if old_problem:
                        old_problem = parse_problem(old_problem)
                        problemname = request.rbody.get("problemname", "")
                        problemname = (
                            problemname if problemname else old_problem["problemname"]
                        )
                        content = request.rbody.get("problem-content", "").split(",", 1)
                        content = (
                            content[1] if len(content) == 2 else old_problem["content"]
                        )
                        result = models["Problem"].update_problem(
                            problemid, problemname, content
                        )
                        if result:
                            return request.redirect("/problem", is_post=True)
                        args["error-msg"] = "Update problem fail"
                    else:
                        args["error-msg"] = "Problem not found"
            elif request.rbody.get("pdeleteid", ""):
                bef, aft = models["Problem"].delete_problem(request.rbody["pdeleteid"])
                if bef:
                    if not aft:
                        return request.redirect("/problem", is_post=True)
                    args["error-msg"] = "Delete problem fail"
                else:
                    args["error-msg"] = "Problem not found"
            else:
                args["error-msg"] = "No problem selected"

    request.body = Views.render("problem.html", args)


@app.route("/challenge", methods=("GET", "POST"))
def do_challege(request):
    args = {}
    args["challenge-list"] = get_challenges()
    args["is_admin"] = request.header["Current-User"]["is_teacher"]
    if request.header["Params"].get("error", ""):
        args["error-msg"] = request.header["Params"]["error"]

    if request.header["Request-Type"] == "POST" and request.rbody:
        if args["is_admin"]:
            name = request.rbody.get("challengename", "")
            hint = request.rbody.get("challengehint", "")
            answer = request.rbody.get("upload", "")
            content = request.rbody.get("challenge-content", "").split(",", 1)
            if not name:
                args["error-msg"] = "Problem name can not be empty"
            elif not answer:
                args["error-msg"] = "Problem file not found"
            elif len(content) != 2:
                args["error-msg"] = "Problem file is empty"
            else:
                content = b64decode(content[1])
                h = h3(f"{answer}&{content.decode()}")
                if models["Challenge"].get_chall(h):
                    args["error-msg"] = "Challenge already upload"
                else:
                    save_chall(answer, content)
                    models["Challenge"].insert_chall(h, name, hint)
                    request.redirect("/challenge", is_post=True)
        else:
            hash = request.rbody.get("challengeid", "")
            answer = request.rbody.get("challengeanswer", "")
            if not hash:
                args["error-msg"] = "Challenge can not be empty"
            else:
                content = check_challenge(answer)
                if content:
                    args["ok-msg"] = "Correct answer"
                    args["challenge-content"] = content
                else:
                    if exists_challenge(answer):
                        args["error-msg"] = "Wrong answer"
                    else:
                        args["error-msg"] = "Challenge not found"

    request.body = Views.render("challenge.html", args)


@app.route("/update-challenge", methods=("POST",))
def update_chall(request):
    errmsg = ""
    if request.header["Current-User"]["is_teacher"]:
        h = request.rbody.get("updatehash", "")
        name = request.rbody.get("challengename", "")
        hint = request.rbody.get("challengehint", "")
        old_chall = models["Challenge"].get_chall(h)
        if old_chall:
            old_chall = parse_challenge(old_chall)
            name = name if name else old_chall["challname"]
            hint = hint if hint else old_chall["hint"]
            models["Challenge"].update_chall(h, name, hint)
        else:
            errmsg = "Challenge not found"
    else:
        errmsg = "Only teacher can update challenge"
    request.redirect(
        "/challenge" + (f"?error={errmsg}" if errmsg else ""), is_post=True
    )


@app.route("/delete-challenge", methods=("POST",))
def delete_chall(request):
    errmsg = ""
    if request.header["Current-User"]["is_teacher"]:
        h = request.rbody.get("deletehash", "")
        bef, aft = models["Challenge"].delete_chall(h)
        if not aft:
            if bef:
                if not delete_local_chall(h):
                    errmsg = "Fail to delete challenge"
            else:
                errmsg = "Challenge not found"
        else:
            errmsg = "Fail to delete challenge"
    else:
        errmsg = "Only teacher can delete challenge"
    request.redirect(
        "/challenge" + (f"?error={errmsg}" if errmsg else ""), is_post=True
    )


if __name__ == "__main__":
    # populate data
    # models["User"].insert_user("admin", h1(
    #     "password"), "administrator", "admin@localhost", "0123456789")
    # models["User"].set_teacher(1)
    app.start()
