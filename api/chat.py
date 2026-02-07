import json

def handler(event, context):
    # Allow only POST
    if event.get("httpMethod") != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }

    # Parse request body
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        body = {}

    message = body.get("message", "").lower()

    # Simple classroom logic
    if "dbms" in message:
        reply = "DBMS is taught by your DBMS faculty."
    elif "teacher" in message:
        reply = "Your classroom has different subject teachers."
    else:
        reply = "I am still learning about your classroom."

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({"reply": reply})
    }
