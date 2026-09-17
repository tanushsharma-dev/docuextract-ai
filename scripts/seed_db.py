from __future__ import annotations

from sqlalchemy import text

from app.core.database import engine


def seed_database() -> None:
    with engine.begin() as connection:
        connection.execute(text("SELECT 1"))
    print("Database check passed.")


if __name__ == "__main__":
    seed_database()
