from app.database import SessionLocal, init_db
from app.services.sample_data import seed_demo_data


def main():
    init_db()
    with SessionLocal() as db:
        seed_demo_data(db)
    print("Demo data has been created.")


if __name__ == "__main__":
    main()

