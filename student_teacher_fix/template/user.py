form = """<hr />
    <div class="card">
      <div class="container">
        <form action="/user" method="post">
          <input type="hidden" name="csrf_token" value={csrf_token}>
          <div class="form-group" style="margin-top:10px;">
            <select class="custom-select" name="messageid">
              <option value="" disabled selected>Select message to update or add new message</option>
              <option value='new-message'>&lt;Add new message&gt;</option>
              {message-id-control}
            </select>
          </div>
          <input type="hidden" name="id" value={userid} />
          <div class="form-group">
            <input type="text" class="form-control" name="content" placeholder="nội dung tin nhắn" />
          </div>
          <div class="form-group">
            <button type="submit" class="btn btn-primary btn-block">
              Submit
            </button>
          </div>
          <br />
        </form>
      </div>
    </div>"""


def parse_options(options):
    options["error-msg"] = options.get("error-msg", "")
    options["add-update-form"] = ""
    options["error"] = ""
    message_id_control = ""
    if options["error-msg"]:
        options[
            "error"
        ] = f"""<hr />
    <div class="response">
      <h3 id="error-msg">Error: {options["error-msg"]}</h3>
    </div>"""

    if isinstance(options["user-info"], list):
        options["title"] = "<h1>List of users</h1>"
        options["show-info"] = [
            '<div class="container float-left">',
            '<form action="/user">',
            '<ul class="list-group" style="position: relative;">',
        ]
        for u in options["user-info"]:
            options["show-info"].append(
                '<li class="list-group-item"><button type="submit" name="id" value={userid}>{username}</button></li>'.format(
                    **u
                )
            )
        options["show-info"].append("</ul></form></div>")
        options["show-info"] = "\n".join(options["show-info"])
    else:
        if not options["user-info"]:
            options["title"] = "<h1>User not found</h1>"
            options["show-info"] = ""
        else:
            u = options["user-info"]
            options["title"] = "<h1>Show information of user {username}</h1>".format(
                **u
            )
            options[
                "show-info"
            ] = """<div class="card">
      <div class="container">
        <p><b>Full name:</b> {fullname}</p>
        <p><b>Email:</b> {email}</p>
        <p><b>Sdt:</b> {phone}</p>
      </div>
    </div>""".format(
                **u
            )
        options["add-update-form"] = form

    if options.get("send-message", ""):
        table_content = []
        message_id_control = []
        for m in options["send-message"]:
            table_content.append(
                """<tr>
              <th scope="row">{messageid}</th>
              <td>{content}</td>
              <td><button type='submit' name='deleteid' value={messageid}>delete</button></td>
            </tr>""".format(
                    **m
                )
            )
            message_id_control.append(
                "<option value={messageid}>{messageid}</option>".format(**m)
            )
        table_content = "\n".join(table_content)
        message_id_control = "\n".join(message_id_control)
        options[
            "message-table"
        ] = f"""<hr />
    <div class="container" style="max-width: 2400px">
      <form action="/user" method="post">
        <input type="hidden" name="csrf_token" value={options["csrf_token"]}>
        <input type='hidden' name='id' value={options["user-info"]["userid"]} />
        <h3>Message send to user {options["user-info"]["username"]}</h3>
        <table class="table">
          <thead>
            <tr>
              <th scope="col" style="width: 5%">Message id</th>
              <th scope="col" style="width: 90%">Content</th>
              <th scope="col" style="width: 5%">#</th>
            </tr>
          </thead>
          <tbody>
            {table_content}
          </tbody>
        </table>
      </form>
    </div>"""
    else:
        options["message-table"] = ""

    if options["add-update-form"]:
        options["add-update-form"] = options["add-update-form"].format(
            **{
                "message-id-control": message_id_control,
                "userid": options["user-info"]["userid"],
            }
        )

    return options
