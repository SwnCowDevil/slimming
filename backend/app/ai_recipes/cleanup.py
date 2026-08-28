from sqlalchemy.orm import Session

from app.ai_recipes.service import purge_expired_sessions
from app.db.session import get_engine


def main() -> None:
    total = 0
    with Session(get_engine()) as session:
        while True:
            deleted = purge_expired_sessions(session, limit=500)
            total += deleted
            if deleted < 500:
                break
    print(f"expired AI recipe sessions deleted: {total}")


if __name__ == "__main__":
    main()
