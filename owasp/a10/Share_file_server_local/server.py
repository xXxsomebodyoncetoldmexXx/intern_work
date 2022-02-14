import http.server
import socketserver

HOST = "localhost"
PORT = 8989

Handler = http.server.SimpleHTTPRequestHandler

with socketserver.TCPServer((HOST, PORT), Handler) as httpd:
  print("serving at port", PORT)
  httpd.serve_forever()
