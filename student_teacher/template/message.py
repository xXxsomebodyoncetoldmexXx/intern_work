def parse_options(options):
  if options["messages"]:
    options["data"] = []
    for m in options["messages"]:
      options["data"].append("<hr />")
      options["data"].append("<div class='container'>")
      options["data"].append(f"<h4>From user: {m[0]}</h4>")
      options["data"].append(f"<p>{m[1]}</p>")
      options["data"].append("</div>")
    options["data"] = '\n'.join(options["data"])
  else:
    options["data"] = "<hr />\n<h3>Message inbox is empty</h3>"
  return options
