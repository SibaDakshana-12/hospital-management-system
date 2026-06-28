import json
import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")


def send_email(to_address, subject, body):
    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_address

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, [to_address], msg.as_string())


def send_email_handler(event, context):
    body = json.loads(event.get("body", "{}"))

    trigger_type = body.get("type")
    recipient = body.get("recipient")
    data = body.get("data", {})

    if trigger_type == "SIGNUP_WELCOME":
        subject = "Welcome to HMS!"
        message = f"Hi {data.get('username', '')}, welcome to the Hospital Management System!"

    elif trigger_type == "BOOKING_CONFIRMATION":
        subject = "Your Appointment is Confirmed"
        message = (
            f"Hi {data.get('username', '')},\n\n"
            f"Your appointment on {data.get('date')} at {data.get('start_time')} "
            f"with {data.get('other_party')} is confirmed."
        )

    else:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": f"Unknown trigger type: {trigger_type}"}),
        }

    try:
        send_email(recipient, subject, message)
    except Exception as e:
        print(f"[ERROR] Failed to send email: {e}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)}),
        }

    return {
        "statusCode": 200,
        "body": json.dumps({"status": "sent", "type": trigger_type}),
    }