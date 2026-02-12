import json
from http.server import BaseHTTPRequestHandler
import os
from PyPDF2 import PdfReader

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _get_provider():
    """Choose provider: gemini (free), groq (free), or openai. Prefers free providers when keys are set."""
    # Explicit choice (e.g. LLM_PROVIDER=gemini in Vercel)
    forced = os.environ.get("LLM_PROVIDER", "").strip().lower()
    if forced in ("gemini", "groq", "openai"):
        if forced == "gemini" and os.environ.get("GEMINI_API_KEY"):
            return "gemini"
        if forced == "groq" and os.environ.get("GROQ_API_KEY"):
            return "groq"
        if forced == "openai" and os.environ.get("OPENAI_API_KEY"):
            return "openai"
    # Prefer free providers when multiple keys exist (so Gemini/Groq win over exhausted OpenAI)
    if os.environ.get("GEMINI_API_KEY"):
        return "gemini"
    if os.environ.get("GROQ_API_KEY"):
        return "groq"
    if os.environ.get("OPENAI_API_KEY"):
        return "openai"
    return None


def _call_openai(context, question):
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def _call_gemini(context, question):
    import google.generativeai as genai
    genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
    # Use a current model ID (gemini-1.5-flash was retired; 2.0/2.5 are available)
    model = genai.GenerativeModel("gemini-2.0-flash")
    full_prompt = f"{context}\n\nQuestion: {question}"
    response = model.generate_content(full_prompt)
    return response.text or ""


def _call_groq(context, question):
    from groq import Groq
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": question},
        ],
    )
    return response.choices[0].message.content


def get_reply(context, question):
    provider = _get_provider()
    if not provider:
        raise ValueError(
            "No LLM API key set. Add one of: OPENAI_API_KEY, GEMINI_API_KEY (free), or GROQ_API_KEY (free). "
            "Get Gemini key at aistudio.google.com/apikey or Groq at console.groq.com"
        )
    if provider == "openai":
        return _call_openai(context, question)
    if provider == "gemini":
        return _call_gemini(context, question)
    if provider == "groq":
        return _call_groq(context, question)
    raise ValueError(f"Unknown provider: {provider}")


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
            provider = _get_provider()
            if not provider:
                _send_json(
                    self,
                    500,
                    {
                        "error": "No LLM API key set. Add GEMINI_API_KEY (free at aistudio.google.com/apikey) or GROQ_API_KEY (free at console.groq.com)"
                    },
                )
                return
            reply = get_reply(context, question)
        except ValueError as e:
            _send_json(self, 500, {"error": str(e)})
            return
        except Exception as e:
            err_str = str(e)
            provider_name = _get_provider() or "unknown"
            if "429" in err_str or "insufficient_quota" in err_str or "quota" in err_str.lower():
                if provider_name == "openai":
                    _send_json(
                        self,
                        429,
                        {
                            "error": f"[{provider_name.upper()}] Quota exceeded. Check billing at platform.openai.com/account/billing. Or switch to free: set GEMINI_API_KEY or GROQ_API_KEY instead.",
                        },
                    )
                elif provider_name == "gemini":
                    _send_json(
                        self,
                        429,
                        {
                            "error": f"[{provider_name.upper()}] Quota exceeded. Check your Gemini API usage at aistudio.google.com. You may need to wait or upgrade your plan.",
                        },
                    )
                elif provider_name == "groq":
                    _send_json(
                        self,
                        429,
                        {
                            "error": f"[{provider_name.upper()}] Rate limit reached. Check your Groq usage at console.groq.com. Free tier has daily limits.",
                        },
                    )
                else:
                    _send_json(
                        self,
                        429,
                        {
                            "error": f"[{provider_name.upper()}] Quota exceeded. Check your API provider's billing/usage page.",
                        },
                    )
            else:
                _send_json(self, 500, {"error": f"[{provider_name.upper()}] Request failed: {err_str}"})
            return

        _send_json(self, 200, {"reply": reply})
