import json
import os

def handler(request):
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        body = json.loads(request.body)
        user_message = body.get("message", "")

        if not user_message:
            return {
                "statusCode": 400,
                "headers": {"Content-Type": "application/json"},
                "body": json.dumps({"reply": "Please ask a question."})
            }

        # TEMP SIMPLE LOGIC (to confirm it works)
        if "dbms" in user_message.lower():
            reply = "DBMS is taught by your DBMS faculty."
        else:
            reply = "I am still learning about your classroom."

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"reply": reply})
        }

    except Exception as e:
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": str(e)})
        }
