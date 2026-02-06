import json
import os
from openai import OpenAI
import PyPDF2

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def read_classroom_data():
    with open("classroom_data.txt", "r") as f:
        return f.read()

def read_pdfs():
    text = ""
    if os.path.exists("pdfs"):
        for file in os.listdir("pdfs"):
            if file.endswith(".pdf"):
                with open(os.path.join("pdfs", file), "rb") as f:
                    reader = PyPDF2.PdfReader(f)
                    for page in reader.pages:
                        text += page.extract_text() or ""
    return text

def handler(request):
    body = json.loads(request.body)
    user_msg = body.get("message", "")

    prompt = f"""
You are a classroom chatbot.

Classroom Info:
{read_classroom_data()}

PDF Content:
{read_pdfs()}

Question:
{user_msg}
"""

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "reply": response.choices[0].message.content
        })
    }
