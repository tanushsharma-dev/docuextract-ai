import requests
import jwt
from datetime import datetime, timedelta

from app.core.database import SessionLocal
from app.models import Document, User
from app.core.config import settings


def main():
    db = SessionLocal()

    print("=" * 70)
    print("STEP 1: USERS WITH DOCUMENT COUNTS")
    print("=" * 70)

    users = db.query(User).all()
    for u in users:
        c = db.query(Document).filter(Document.user_id == u.id).count()
        print(f"{u.email} | id={u.id} | docs={c}")

    print()
    print("=" * 70)
    print("STEP 2: API RESPONSE FOR EACH USER (with fresh token)")
    print("=" * 70)

    for u in users:
        if not u.is_verified:
            continue

        token = jwt.encode(
            {
                "sub": str(u.id),
                "email": u.email,
                "type": "access",
                "exp": datetime.utcnow() + timedelta(hours=1),
            },
            settings.JWT_SECRET,
            algorithm="HS256",
        )

        try:
            r = requests.get(
                "http://127.0.0.1:8000/api/v1/analytics/overview",
                headers={"Authorization": "Bearer " + token},
                timeout=5,
            )
            if r.status_code == 200:
                d = r.json()
                total = d.get("total_documents")
                extracted = d.get("auto_approved")
                review = d.get("needs_review")
                failed = d.get("failed")
                print(
                    f"{u.email} -> total={total}, "
                    f"extracted={extracted}, "
                    f"review={review}, "
                    f"failed={failed}"
                )
            else:
                print(f"{u.email} -> ERROR {r.status_code}: {r.text[:200]}")
        except Exception as e:
            print(f"{u.email} -> EXCEPTION: {type(e).__name__}: {e}")

    db.close()

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)


if __name__ == "__main__":
    main()