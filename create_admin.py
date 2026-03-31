"""
create_admin.py
───────────────
Creates or resets an admin account in MySQL.
Run: python create_admin.py
"""

import sys, os, hashlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from database.db import get_db_connection

def hash_pw(pw):
    return hashlib.sha256(pw.encode()).hexdigest()

def main():
    print("\n  ◈  SDIS — Admin Account Setup (MySQL)\n")

    username = input("  Username  [admin]        : ").strip() or "admin"
    email    = input("  Email     [admin@sdis.com]: ").strip() or "admin@sdis.com"

    while True:
        pw = input("  Password  (8+ chars, 1 uppercase, 1 digit): ").strip()
        if len(pw)>=8 and any(c.isupper() for c in pw) and any(c.isdigit() for c in pw):
            break
        print("  ✕  Too weak. Try again.\n")

    conn = get_db_connection()
    cur  = conn.cursor(dictionary=True)
    cur.execute("SELECT id FROM users WHERE username=%s", (username,))
    existing = cur.fetchone()

    if existing:
        cur.execute(
            "UPDATE users SET password=%s, role='admin', email=%s, is_active=1 WHERE username=%s",
            (hash_pw(pw), email, username)
        )
        print(f"\n  ✓  '{username}' updated → role=admin, password reset.")
    else:
        cur.execute(
            "INSERT INTO users (username, email, password, role) VALUES (%s,%s,%s,'admin')",
            (username, email, hash_pw(pw))
        )
        print(f"\n  ✓  Admin '{username}' created.")

    conn.commit()
    cur.close()
    conn.close()

    print(f"\n  Username : {username}")
    print(f"  Email    : {email}")
    print(f"  Role     : admin")
    print(f"\n  Run: python app.py  →  http://localhost:5000/auth/login\n")

if __name__ == "__main__":
    main()
