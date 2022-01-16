from Server import SimpleServer

HOST = "0.0.0.0"
PORT = 8080
app = SimpleServer(host=HOST, port=PORT)


def main():
  pass


if __name__ == "__main__":
  main()
  app.start()
