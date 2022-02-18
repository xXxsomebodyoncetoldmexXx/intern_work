import re

challenge_table = """<div class="container" style="max-width: 2400px">
      <table class="table">
        <thead>
          <tr>
            <th scope="col" style="width: 20%">Challenge id</th>
            <th scope="col" style="width: 40%">Challenge name</th>
            <th scope="col" style="width: 30%">Hint</th>
            <th scope="col" style="width: 5%">#</th>
            <th scope="col" style="width: 5%">#</th>
          </tr>
        </thead>
        <tbody>
          {challenge-table-content}
        </tbody>
      </table>
    </div>
    """

challenge_row = """<tr>
  <form id="update-form" action="/update-challenge" method="post"><input type="hidden" name="csrf_token" value={csrf_token}></form>
  <form id="delete-form" action="/delete-challenge" method="post"><input type="hidden" name="csrf_token" value={csrf_token}></form>
  <th scope="row">{hash}</th>
  <td><input type='text' name='challengename' placeholder={challengename} form='update-form' disabled></td>
  <td><input type='text' name='challengehint' placeholder={challengehint} form='update-form' disabled></td>
  <td><button type='submit' name='updatehash' value={hash} form='update-form' disabled>update</button></td>
  <td><button type='submit' name='deletehash' value={hash} form='delete-form' disabled>delete</button></td>
</tr>"""

add_form = """<div class="card">
      <div class="container">
        <form action="/challenge" method="post">
          <input type="hidden" name="csrf_token" value={csrf_token}>
          <div class="form-group" style="margin-top:10px;">
            <input type="text" class="form-control" name="challengename" placeholder="Challenge name" />
          </div>
          <div class="form-group">
            <input type="text" class="form-control" name="challengehint" placeholder="Challenge hint" />
          </div>
          <div class="form-group">
            <input type="file" class="form-control" name="upload" placeholder="file" onchange="prepfile('challenge-upload', 'challenge-content-placeholder')" id="challenge-upload"/>
            <input type="hidden" name="challenge-content" id="challenge-content-placeholder" />
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

answer_form = """<div class="card">
      <div class="container">
        <form action="/challenge" method="post">
          <input type="hidden" name="csrf_token" value={csrf_token}>
          <div class="form-group" style="margin-top:10px;">
            <select class="custom-select" name="challengeid">
              <option value="" disabled selected>Select challenge to answer</option>
              {challenge-id-control}
            </select>
          </div>
          <div class="form-group">
            <input type="text" class="form-control" name="challengeanswer" placeholder="Answer" />
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


def _fix_nl(msg):
    return re.sub(r"(?:\r\n|\n|\r(?!\n))", "<br />", msg)


def parse_options(options):
    options["error-msg"] = options.get("error-msg", "")
    options["ok-msg"] = options.get("ok-msg", "")
    options["challenge-content"] = _fix_nl(options.get("challenge-content", ""))
    chall_rows = []
    chall_id_list = []
    challenge_row_template = challenge_row
    if options["is_admin"]:
        challenge_row_template = challenge_row_template.replace("disabled", "")

    for c in options["challenge-list"]:
        chall_rows.append(challenge_row_template.format(**c))
        chall_id_list.append(
            "<option value={hash}>{challengename}</option>".format(**c)
        )
    chall_rows = "\n".join(chall_rows)
    chall_id_list = "\n".join(chall_id_list)

    options["challenge-table"] = challenge_table.format(
        **{"challenge-table-content": chall_rows}
    )

    options["challenge-answer-form"] = ""

    if options["is_admin"]:
        options["title"] = "Managed challenge"

        options["challenge-add-form"] = add_form
    else:
        options["title"] = "Challenge list"
        options["challenge-add-form"] = ""

        if chall_id_list:
            options["challenge-answer-form"] = answer_form.format(
                **{"challenge-id-control": chall_id_list}
            )
    return options
