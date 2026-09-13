import argparse

from sqlalchemy import select

from app.core.security import hash_password
from app.db.models import Role, User, UserGamification, UserPreference, UserRole
from app.db.session import SessionLocal

parser = argparse.ArgumentParser()
parser.add_argument("--email", required=True)
parser.add_argument("--password", required=True)
parser.add_argument("--name", default="Administrator")
args = parser.parse_args()

with SessionLocal() as db:
    user = db.scalar(select(User).where(User.email.ilike(args.email)))
    if user is None:
        user = User(email=args.email.lower(), password_hash=hash_password(args.password), full_name=args.name)
        db.add(user); db.flush()
        db.add(UserPreference(user_id=user.id)); db.add(UserGamification(user_id=user.id))
    role = db.scalar(select(Role).where(Role.code == "ADMIN"))
    if role is None:
        role = Role(code="ADMIN", name="Administrator", description="System administrator")
        db.add(role); db.flush()
    if db.get(UserRole, (user.id, role.id)) is None:
        db.add(UserRole(user_id=user.id, role_id=role.id))
    db.commit()
    print(f"Admin ready: id={user.id}, email={user.email}")
