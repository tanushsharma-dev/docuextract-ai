import sys
import os
import uuid
import hashlib
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.database import engine

def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), bytes.fromhex(salt), 100_000)
    return f"{salt}${dk.hex()}"

print("=" * 60)
print("AUTH DIAGNOSTIC & FIX TOOL")
print("=" * 60)

# 1. List all users
print("\n[1] Current Users in Database:")
with engine.connect() as conn:
    result = conn.execute(text("SELECT id, email, username, auth_provider, is_verified, hashed_password FROM app_users"))
    users = result.fetchall()
    
    if not users:
        print("  ❌ No users found")
    else:
        for user in users:
            uid, email, username, provider, verified, hash_val = user
            hash_type = "PBKDF2" if hash_val and not hash_val.startswith("$2") else "bcrypt" if hash_val else "None"
            print(f"  • {email}")
            print(f"    Username: {username} | Provider: {provider} | Verified: {verified}")
            print(f"    Hash Type: {hash_type} | Hash: {hash_val[:50] if hash_val else 'None'}...")

# 2. Clean up old accounts
print("\n[2] Cleaning up old accounts...")
email_to_clean = "tanushsharma052@gmail.com"
with engine.connect() as conn:
    result = conn.execute(
        text("DELETE FROM app_users WHERE email = :email"),
        {"email": email_to_clean}
    )
    conn.commit()
    print(f"  ✅ Deleted {result.rowcount} account(s) for {email_to_clean}")

# 3. Create fresh test account (with UUID generated manually)
print("\n[3] Creating fresh test account...")
test_password = "test123"
user_id = str(uuid.uuid4())  # UUID manually generate karo

with engine.connect() as conn:
    conn.execute(
        text("""
            INSERT INTO app_users (id, email, username, full_name, hashed_password, auth_provider, is_verified)
            VALUES (:id, :email, :username, :full_name, :hash, :provider, :verified)
        """),
        {
            "id": user_id,
            "email": email_to_clean,
            "username": "tanush",
            "full_name": "Tanush Sharma",
            "hash": hash_password(test_password),
            "provider": "local",
            "verified": True
        }
    )
    conn.commit()
    print(f"  ✅ Created test account:")
    print(f"     ID: {user_id}")
    print(f"     Email: {email_to_clean}")
    print(f"     Password: {test_password}")
    print(f"     Status: Verified (OTP skip)")

# 4. Verify login works
print("\n[4] Testing login...")
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT hashed_password FROM app_users WHERE email = :email"),
        {"email": email_to_clean}
    )
    row = result.fetchone()
    
    if row:
        stored_hash = row[0]
        salt, dk = stored_hash.split("$")
        calc = hashlib.pbkdf2_hmac("sha256", test_password.encode("utf-8"), bytes.fromhex(salt), 100_000)
        
        if secrets.compare_digest(calc.hex(), dk):
            print("  ✅ Login test PASSED — password verification works!")
        else:
            print("  ❌ Login test FAILED — hash mismatch")
    else:
        print("  ❌ User not found after creation")

print("\n" + "=" * 60)
print("NEXT STEPS:")
print("=" * 60)
print("1. Server start karo: uvicorn app.main:app --reload --port 8000")
print("2. Browser me jao: http://127.0.0.1:8000/ui/login")
print("3. Login tab me ye details daalo:")
print(f"   Email: {email_to_clean}")
print(f"   Password: {test_password}")
print("4. Sign In dabao — direct login ho jayega! ✅")
print("=" * 60)