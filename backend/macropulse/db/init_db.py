from macropulse.db.base import Base
from macropulse.db.session import engine
import macropulse.models  # noqa: F401


def init_db():
    """Create all tables in the database if they do not exist."""
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    init_db()
    print("Database tables initialized successfully.")
