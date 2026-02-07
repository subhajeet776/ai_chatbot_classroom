import json

def handler(request):
    if request.method != "POST":
        return {
            "statusCode": 405,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"error": "Method not allowed"})
        }

    try:
        body = json.loads(request.body or "{}")
    except Exception:
        body = {}

    message = body.get("message", "").lower()

    if "dbms" in message:
        reply = "DBMS is taught by your DBMS faculty."
    else:
        reply = "I am still learning about your classroom."

    return {
        "statusCode": 200,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps({"reply": reply})
    }
