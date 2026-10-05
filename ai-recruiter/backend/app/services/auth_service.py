from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import UserRegister
from app.utils.security import get_password_hash, verify_password


class AuthService:
    @staticmethod
    def get_by_email(db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email.lower().strip()).first()

    @staticmethod
    def get_by_id(db: Session, user_id: str) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[User]:
        return db.query(User).offset(skip).limit(limit).all()

    @classmethod
    def register(cls, db: Session, user_in: UserRegister) -> User:
        clean_email = user_in.email.lower().strip()
        existing = cls.get_by_email(db, clean_email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="A user with this email address already exists"
            )

        new_user = User(
            name=user_in.name.strip(),
            email=clean_email,
            password_hash=get_password_hash(user_in.password),
            role=user_in.role.upper()
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user

    @classmethod
    def authenticate(cls, db: Session, email: str, password: str) -> Optional[User]:
        clean_email = email.lower().strip()
        user = cls.get_by_email(db, clean_email)
        if not user:
            return None
        if not verify_password(password, user.password_hash):
            return None
        return user

    @classmethod
    def update_role(cls, db: Session, user_id: str, role: str) -> User:
        user = cls.get_by_id(db, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        if role.upper() not in ["RECRUITER", "ADMIN"]:
            raise HTTPException(status_code=400, detail="Invalid role specified")
        user.role = role.upper()
        db.commit()
        db.refresh(user)
        return user

    @classmethod
    def seed_default_users(cls, db: Session):
        """Seed demo users if they do not exist."""
        changed = False
        if not cls.get_by_email(db, "admin@smartrecruit.ai"):
            admin_user = User(
                name="System Administrator",
                email="admin@smartrecruit.ai",
                password_hash=get_password_hash("Admin@123456"),
                role="ADMIN"
            )
            db.add(admin_user)
            changed = True
        if not cls.get_by_email(db, "recruiter@smartrecruit.ai"):
            recruiter_user = User(
                name="Sarah Jenkins",
                email="recruiter@smartrecruit.ai",
                password_hash=get_password_hash("Recruiter@123456"),
                role="RECRUITER"
            )
            db.add(recruiter_user)
            changed = True
        if changed:
            db.commit()



auth_service = AuthService()
