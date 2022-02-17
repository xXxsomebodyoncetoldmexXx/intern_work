problem_row = """<tr>
  <th scope="row">{problemid}</th>
  <td>{problemname}</td>
  <td><form action="/problem"><button type='submit' name='pid' value={problemid}>download</button></form></td>
  <td><form action="/problem" method="post"><button type='submit' name='pdeleteid' value={problemid} disabled>delete</button></form></td>
</tr>"""

answer_row = """<tr>
  <th scope="row">{answerid}</th>
  <td>{username}</td>
  <td>{problemname}</td>
  <td><form action="/problem"><button type='submit' name='aid' value={answerid}>download</button></form></td>
  <td><form action="/problem" method="post"><button type='submit' name='adeleteid' value={answerid}>delete</button></form></td>
</tr>"""

problem_form = """<hr />
    <div class="card">
      <div class="container">
        <form action="/problem" method="post">
          <div class="form-group" style="margin-top:10px;">
            <select class="custom-select" name="problemid">
              <option value="" disabled selected>Select problem to update or add new problem</option>
              <option value='new-problem'>&lt;Add new problem&gt;</option>
              {problem-id-control}
            </select>
          </div>
          <div class="form-group">
            <input type="text" class="form-control" name="problemname" placeholder="problem name" />
          </div>
          <div class="form-group">
            <input type="file" class="form-control" name="upload" placeholder="file" onchange="prepfile('problem-upload', 'problem-content-placeholder')" id="problem-upload"/>
            <input type="hidden" name="problem-content" id="problem-content-placeholder" />
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


answer_form = """<hr />
    <div class="card">
      <div class="container">
        <form action="/problem" method="post">
          <div class="form-group" style="margin-top:10px;">
            <select class="custom-select" name="answerid">
              <option value="" disabled selected>Select answer to update or add new answer</option>
              <option value='new-answer'>&lt;Add new answer&gt;</option>
              {answer-id-control}
            </select>
          </div>
          <div class="form-group">
            <select class="custom-select" name="answer-problemid">
              <option value="" disabled selected>Select problem to answer</option>
              {unsolve-id-control}
            </select>
          </div>
          <div class="form-group">
            <input type="file" class="form-control" name="upload" placeholder="file" onchange="prepfile('answer-upload', 'answer-content-placeholder')" id="answer-upload"/>
            <input type="hidden" name="answer-content" id="answer-content-placeholder" />
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
    options["problem-add-update-form"] = ""
    options["answer-add-update-form"] = ""
    problem_table_content = []
    answer_table_content = []
    problem_id_option = []
    answer_id_option = []
    unsolve_id_option = []
    row_template = problem_row

    if options["is_admin"] == 1:
        row_template = row_template.replace("disabled", "")
    for p in options["problem-list"]:
        problem_table_content.append(row_template.format(**p))
        problem_id_option.append(
            "<option value={problemid}>{problemname}</option>".format(**p)
        )
    options["problem-table-content"] = "\n".join(problem_table_content)
    if options["is_admin"] == 1:
        problem_id_option = "\n".join(problem_id_option)
        options["problem-add-update-form"] = problem_form.format(
            **{"problem-id-control": problem_id_option}
        )

    row_template = answer_row
    for a in options["answer-list"]:
        answer_table_content.append(row_template.format(**a))
        answer_id_option.append(
            "<option value={answerid}>{answerid}</option>".format(**a)
        )

    if options["unsolve-list"]:
        for u in options["unsolve-list"]:
            unsolve_id_option.append(
                "<option value={problemid}>{problemname}</option>".format(**u)
            )
        answer_id_option = "\n".join(answer_id_option)
        unsolve_id_option = "\n".join(unsolve_id_option)
        options["answer-add-update-form"] = answer_form.format(
            **{
                "answer-id-control": answer_id_option,
                "unsolve-id-control": unsolve_id_option,
            }
        )

    options["answer-table-content"] = "\n".join(answer_table_content)
    return options
