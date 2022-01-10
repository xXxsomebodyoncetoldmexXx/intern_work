from custom_imap import My_IMAP4_SSL
from custom_smtp import My_SMTP, MAIL_BODY_FORMAT
import getpass
import os

G_name = None
G_username = None
G_password = None

GOOGLE_IMAP = ("imap.gmail.com", 993)
GOOGLE_SMTP = ("smtp.gmail.com", 587)

G_smtp = My_SMTP(*GOOGLE_SMTP, encoding="utf-8")
G_imap = My_IMAP4_SSL(*GOOGLE_IMAP)

_MAX_MINI_LEN = 20
ARGS = ""


def prompt(name=""):
  os.system("cls")
  print("""\
______                                  _ _         _ _            _
| ___ \                                (_) |       | (_)          | |
| |_/ /   _ _ __ ___    _ __ ___   __ _ _| |    ___| |_  ___ _ __ | |_
|  __/ | | | '__/ _ \  | '_ ` _ \ / _` | | |   / __| | |/ _ \ '_ \| __|
| |  | |_| | | |  __/  | | | | | | (_| | | |  | (__| | |  __/ | | | |_
\_|   \__,_|_|  \___|  |_| |_| |_|\__,_|_|_|   \___|_|_|\___|_| |_|\__|

                                                              Ver: 1.0\n\n\n""")
  if name:
    print(f"Welcome {name}")


def err(msg):
  print(f"![ERROR]: {msg}")


def die(msg):
  err(msg)
  exit(1)


def login():
  username = input("Enter your Gmail: ").strip()
  password = getpass.getpass(prompt="Enter your password: ")
  name, *domain = username.split("@", maxsplit=1)
  if len(domain) == 0 or domain[0] != "gmail.com":
    die("gmail not valid!")

  # IMAP
  G_imap.login(username, password)

  # SMTP
  G_smtp.starttls()
  G_smtp.login(username, password)
  return (username, password, name)


def default():
  print("Command not valid")


def clear():
  prompt(G_name)
  print("Enter a command below, or '?' or try command 'help' for more information!")


def helper():
  print("""\
    vim:                Compose and send a new mail
    (list, ls):         List all mails
    cat <id>:           Print content of mail with <id>
    get <id>:           Download attachment(s) of mail with <id>
    (clear, cls):       Clear the screen
    (?, help):          Print this help
    exit:               exit the program""")


def f_exit():
  G_imap.close()
  G_imap.logout()
  G_smtp.quit()


def f_list():
  mails = G_imap.get_mails(G_imap.get_mail_indexs())
  print("List of mails:")
  for mail in mails:
    Id = mail["Id"]

    From = mail["From"].ljust(_MAX_MINI_LEN) if len(
        mail["From"]) < _MAX_MINI_LEN else f"{mail['From'][:_MAX_MINI_LEN - 3]}..."

    Subject = mail["Subject"].ljust(_MAX_MINI_LEN) if len(
        mail["Subject"]) < _MAX_MINI_LEN else f"{mail['Subject'][:_MAX_MINI_LEN - 3]}..."

    Body = mail["Body"].replace("\n", "").replace("\r", "")
    Body = Body.ljust(_MAX_MINI_LEN) if len(
        Body) < _MAX_MINI_LEN else f"{mail['Body'][:_MAX_MINI_LEN - 3]}..."

    Date = mail["Date"].strftime("%x")
    print(f"{Id}. {From} - {Subject} - {Body} - {Date}")


def get_id():
  id = ARGS[0]
  if not id:
    err("<Id> not supply!")
    return (None, None)
  try:
    id = int(id)
  except ValueError:
    err(f"Invalid {id=}")
    return (None, None)
  mails = G_imap.get_mails(G_imap.get_mail_indexs())
  if id > len(mails) or id <= 0:
    err(f"Don't have mail that have {id=}")
    return (None, None)
  return (mails[id-1], id)


def cat():
  m = get_id()[0]
  if m:
    print(MAIL_BODY_FORMAT.format(m["From"], m["To"], m["Subject"], m["Body"]))
    if "Attachments" in m:
      attachments = ', '.join(m["Attachments"])
      print(f"**Mail has addition attachment(s): {attachments}")


def get():
  m, id = get_id()
  if m:
    if "Attachments" in m:
      attachments = ', '.join(m["Attachments"])
      print(f"**Mail has addition attachment(s): {attachments}")
      fname = input("What would you like to download? ").strip()
      result = G_imap.get_attachments(
          b'%d' % id, m["Attachments"] if fname == '*' else fname)
      print("[SUCCESS]")
      for file, path in result:
        print(f"file {file} have been save to path {path}")
    else:
      print("**Mail don't have any attachment")


def vim():
  to = input("Send mail to: ").strip()
  subject = input("Email subject: ").strip()
  print("Writing body (press enter when finish):")
  body = list()
  while True:
    line = input()
    body.append(line)
    if not line:
      break
  body = '\n'.join(body)
  G_smtp.sendmail(G_username, to, subject, body)
  print("[SUCCESS]: email have been send")


def main():
  global G_name, G_username, G_password, ARGS
  prompt()
  (G_username, G_password, G_name) = login()
  cmd_table = {
      "vim": vim,
      "cat": cat,
      "get": get,
      "list": f_list,
      "ls": f_list,
      "clear": clear,
      "cls": clear,
      "?": helper,
      "help": helper,
      "exit": f_exit
  }
  clear()
  cmd = ""
  while cmd != "exit":
    try:
      cmd, *ARGS = input("\n>> ").strip().lower().split(" ", maxsplit=1)
      cmd_table.get(cmd, default)()
    except KeyboardInterrupt:
      f_exit()
      break
  print(f"Goodbye {G_name}")


if __name__ == "__main__":
  main()
