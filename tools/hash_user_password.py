#!/usr/bin/env python3
import sys
import os
import json
from werkzeug.security import generate_password_hash

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_PATH = os.path.join(BASE_DIR, "config", "users.json")

def load_users():
    if not os.path.exists(USERS_PATH):
        return []
    with open(USERS_PATH, "r", encoding="utf-8") as f:
        return json.load(f) or []

def save_users(users):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def usage():
    print("Usage: python tools/hash_user_password.py <username> <plaintext-password>")
    print("Note: This script uses pbkdf2:sha256 hashing for better security.")
    sys.exit(2)

def main():
    if len(sys.argv) != 3:
        usage()
    username = sys.argv[1]
    password = sys.argv[2]

    # Force pbkdf2:sha256 hashing method for consistency with the application
    hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
    print(f"Generated hash: {hashed_password[:30]}...")

    users = load_users()
    for u in users:
        if u.get("username") == username:
            u["password"] = hashed_password
            save_users(users)
            print(f"✅ Updated password for user '{username}' with pbkdf2:sha256 hash.")
            return
    
    # if not found, offer to create
    new = {
        "username": username, 
        "password": hashed_password, 
        "role": "user",
        "main_color": "#4caf50"  # default color
    }
    users.append(new)
    save_users(users)
    print(f"✅ Created new user '{username}' with role 'user' and pbkdf2:sha256 hashed password.")

if __name__ == "__main__":
    main()
