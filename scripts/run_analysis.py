from app.database import SessionLocal, init_db
from app.main import analyse


def main():
    init_db()
    with SessionLocal() as db:
        result = analyse(db)
    print(result)


if __name__ == "__main__":
    main()

