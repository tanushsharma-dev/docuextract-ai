from __future__ import annotations

from app.core.database import Base, engine
from app.models import document, extraction, review  # noqa: F401


def initialize_database() -> None:
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized.")


if __name__ == "__main__":
    initialize_database()
