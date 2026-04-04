import os
import smtplib
import traceback  # <--- 1. Import traceback
from email.message import EmailMessage
from dotenv import load_dotenv

# 2. Fix the dotenv loading! 
# Using load_dotenv() without a path automatically finds the .env locally, 
# and safely ignores it on Render (where you should use the Dashboard Environment variables).
load_dotenv() 

SMTP_SERVER = os.getenv("SMTP_SERVER")
print(f"DEBUG - My SMTP Server is: {SMTP_SERVER}")
SMTP_PORT = int(os.getenv("SMTP_PORT", 465))
SENDER_EMAIL = os.getenv("SENDER_EMAIL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")

def send_notification_email(to_email: str, subject: str, body: str):
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = SENDER_EMAIL
    msg['To'] = to_email

    try:
        print(f"Attempting SMTP_SSL connection to {SMTP_SERVER} on port {SMTP_PORT}...")
        server = smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT)
        server.login(SENDER_EMAIL, SENDER_PASSWORD)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        print("\n" + "!"*40)
        print("EMAIL SENDING FAILED! HERE IS THE EXACT ERROR:")
        traceback.print_exc()  # <--- 3. This prints the exact system error!
        print("!"*40 + "\n")
        return False