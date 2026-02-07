import json
from http.server import BaseHTTPRequestHandler
import os
from PyPDF2 import PdfReader
from openai import OpenAI

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

BASE_DIR = os.path.dirname(os.path.dirname(__file__))

def load_classroom_data():
    try:
        with open(os.path.join(BASE_DIR, "classroom_data.txt"), "r", encoding="utf-8") as f:
            return f.read()
    except:
        return ""

def load_pdfs():
    text = ""
    pdf_dir = os.path.join(BASE_DIR, "pdfs")

    if not os.path.exists(pdf_dir):
        return ""

    for file in os.listdir(pdf_dir):
        if file.endswith(".pdf"):
            reader = PdfReader(os.path.join(pdf_dir, file))
            for page in reader.pages:
                if page.extract_text():
                    text += page.extract_text() + "\n"

    return text

def main(request):
    if request.method != "POST":
        return {
            "statusCode": 405,
            "body": json.dumps({"error": "Method not allowed"})
        }

    body = json.loads(request.body or "{}")
    question = body.get("message", "")

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

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": context},
            {"role": "user", "content": question}
        ]
    )

    reply = response.choices[0].message.content

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({"reply": reply})
    }
