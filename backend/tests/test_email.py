import sys
import os
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.utils.email_service import send_notification_email


load_dotenv()

my_email = os.getenv("SENDER_EMAIL") 

print(f"Attempting to send a test email to: {my_email}...")

success = send_notification_email(
    to_email=my_email,
    subject="Swifty Test Email 🚀",
    body="If you are reading this, your IITK email integration is working perfectly!"
)

if success:
    print("✅ SUCCESS: The email was handed off to the IITK SMTP server.")
    print("Go check your inbox (and your spam folder just in case)!")
else:
    print("❌ FAILED: Something went wrong. Check the error message above.")