from app.db.models.user import User
from app.db.session import SessionLocal


def main():
    with SessionLocal() as session:
        user = session.query(User).filter(User.email == "demo@travelmind.local").first()
        if not user:
            user = User(email="demo@travelmind.local", full_name="Demo User")
            session.add(user)
            session.commit()
            session.refresh(user)
            print(f"Created demo user id={user.id}")
        else:
            print(f"Demo user already exists id={user.id}")


if __name__ == "__main__":
    main()