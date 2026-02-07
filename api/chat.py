import json
from http.server import BaseHTTPRequestHandler

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        try:
            data = json.loads(body.decode())
        except Exception:
            data = {}

        message = data.get("message", "").lower()

        if "dbms" in message:
            reply = "DBMS is taught by your DBMS faculty."
        else:
            reply = "I am still learning about your classroom."

        response = json.dumps({"reply": reply})

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(response.encode())

    def do_GET(self):
        self.send_response(405)
        self.end_headers()
