username_form = """<div class="form-group">
  <input
    type="text"
    class="form-control"
    name="username"
    placeholder="Tên đăng nhập"
  />
</div>
"""

fullname_form = """<div class = "form-group" >
  <input
    type = "text"
    class = "form-control"
    name = "fullname"
    placeholder = "họ tên"
  / >
</div >
"""


def parse_options(options):
  options["error-msg-update"] = options.get("error-msg-update", "")
  options["error-msg-delete"] = options.get("error-msg-delete", "")

  if options["is_teacher"]:
    options["admin-username-control"] = username_form
    options["admin-fullname-control"] = fullname_form
    options["admin-adduser-control"] = "<option value='new-user'>&lt;Add new user&gt;</option>\n"
    ops = []
    for u in options["Other-User"]:
      if u:
        ops.append("<option value={userid}>{username}</option>".format(**u))
    options["admin-otheruser-control"] = '\n'.join(ops)
  else:
    options["admin-username-control"] = ''
    options["admin-fullname-control"] = ''
    options["admin-adduser-control"] = ''
    options["admin-otheruser-control"] = ''
  return options
