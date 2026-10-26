import argparse

from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.user import User, UserRole


def main():
    parser = argparse.ArgumentParser(description="Create initial administrator")
    parser.add_argument("--name", required=True)
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    args = parser.parse_args()
    if len(args.password) < 12:
        raise SystemExit("Admin paroli kamida 12 belgidan iborat bo'lsin")
    with SessionLocal() as db:
        email = args.email.strip().lower()
        user = db.scalar(select(User).where(User.email == email))
        if user:
            if user.role != UserRole.admin:
                raise SystemExit("Email mavjud, lekin admin emas. Boshqa email tanlang.")
            print(f"Admin mavjud: id={user.id}, email={user.email}")
            return
        user = User(full_name=args.name.strip(), email=email,
                    hashed_password=hash_password(args.password), role=UserRole.admin)
        db.add(user)
        db.commit()
        db.refresh(user)
        print(f"Admin yaratildi: id={user.id}, email={user.email}")

if __name__ == "__main__":
    main()
