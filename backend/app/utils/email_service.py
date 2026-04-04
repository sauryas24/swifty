import os
import requests
from dotenv import load_dotenv

load_dotenv()

# Grab the credentials from Render
BREVO_API_KEY = os.getenv("BREVO_API_KEY")
SENDER_EMAIL = os.getenv("SENDER_EMAIL") 

def send_notification_email(to_email: str, subject: str, body: str):
    print("\n" + "="*50)
    print(f"🚀 PREPARING TO SEND EMAIL TO: {to_email}")
    
    if not BREVO_API_KEY:
        print("❌ ERROR: BREVO_API_KEY is missing from environment variables!")
        return False

    url = "https://api.brevo.com/v3/smtp/email"
    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {"email": SENDER_EMAIL, "name": "Swifty App"},
        "to": [{"email": to_email}],
        "subject": subject,
        # We wrap your body text in basic HTML so it formats nicely
        "htmlContent": f"<html><body><p>{body}</p></body></html>" 
    }

    try:
        print("🌐 Connecting to Brevo API over Port 443 (HTTPS)...")
        # Send the web request (Render cannot block this!)
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        # If Brevo replies with an error (like an invalid email), this catches it
        response.raise_for_status() 
        
        print("✅ SUCCESS! Email delivered via API.")
        print("="*50 + "\n")
        return True
        
    except Exception as e:
        print("\n" + "!"*40)
        print("❌ API EMAIL FAILED! EXACT ERROR:")
        print(e)
        # If Brevo sends back a specific error message, print it out
        if hasattr(e, 'response') and e.response is not None:
            print(f"Brevo says: {e.response.text}")
        print("!"*40 + "\n")
        return False