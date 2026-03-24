import sqlite3

try:
    # Connect to your database
    conn = sqlite3.connect('swifty.db')
    cursor = conn.cursor()
    
    # Fetch all users
    cursor.execute("SELECT email_id, role FROM users")
    users = cursor.fetchall()
    
    print("--- USERS IN DATABASE ---")
    for user in users:
        print(f"Email: {user[0]} | Role: '{user[1]}'")
    print("-------------------------")
    
except Exception as e:
    print(f"Error reading database: {e}")