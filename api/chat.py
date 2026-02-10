import json
from http.server import BaseHTTPRequestHandler
import os
from PyPDF2 import PdfReader
from openai import OpenAI

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable is not set")
    return OpenAI(api_key=api_key)


def load_classroom_data():
    try:
        with open(os.path.join(BASE_DIR, "classroom_data.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def load_pdfs():
    text = ""
    pdf_dir = os.path.join(BASE_DIR, "pdfs")

    if not os.path.exists(pdf_dir):
        return ""

    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            try:
                reader = PdfReader(os.path.join(pdf_dir, file))
                for page in reader.pages:
                    if page.extract_text():
                        text += page.extract_text() + "\n"
            except Exception:
                continue

    return text


def _send_cors_headers(self):
    self.send_header("Access-Control-Allow-Origin", "*")
    self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
    self.send_header("Access-Control-Allow-Headers", "Content-Type")


def _send_json(self, status, data):
    body = json.dumps(data).encode("utf-8")
    self.send_response(status)
    self.send_header("Content-Type", "application/json")
    _send_cors_headers(self)
    self.send_header("Content-Length", str(len(body)))
    self.end_headers()
    self.wfile.write(body)


class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        _send_cors_headers(self)
        self.end_headers()

    def do_POST(self):
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            body_bytes = self.rfile.read(content_length) if content_length else b""
            body_str = body_bytes.decode("utf-8") if body_bytes else "{}"
            body = json.loads(body_str)
        except (ValueError, json.JSONDecodeError):
            _send_json(self, 400, {"error": "Invalid JSON body"})
            return

        question = body.get("message", "").strip()
        if not question:
            _send_json(self, 400, {"error": "message is required"})
            return

        try:
            client = get_client()
        except ValueError as e:
            _send_json(self, 500, {"error": str(e)})
            return

        classroom_text = load_classroom_data()
        pdf_text = load_pdfs()

        context = f"""
You are a classroom assistant.
Answer ONLY using the following classroom material.
If the answer is not found, say "I don't know based on the provided data".

CLASSROOM DATA:
{classroom_text}

PDF DATA:
{pdf_text}
"""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": context},
                    {"role": "user", "content": question},
                ],
            )
            reply = response.choices[0].message.content
        except Exception as e:
            _send_json(self, 500, {"error": f"OpenAI request failed: {str(e)}"})
            return

        _send_json(self, 200, {"reply": reply})
