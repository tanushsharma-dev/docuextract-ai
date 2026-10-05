import sys
import os

# Path fix: app module ko accessible banao
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import text
from app.core.database import engine

email = "tanushsharma052@gmail.com"

with engine.connect() as conn:
    result = conn.execute(
        text("DELETE FROM app_users WHERE email = :email"),
        {"email": email}
    )
    conn.commit()
    print(f"Deleted {result.rowcount} account(s) for {email}")

print("Ab naya signup karo — purana data clean ho gaya!")