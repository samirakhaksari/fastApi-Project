from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy import create_engine, Column, DateTime, String, Integer
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel
import datetime
from datetime import datetime, timedelta
from jose import JWTError, jwt

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# Models for SQLAlchemy
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)


class DBToken(Base):
    __tablename__ = "tokens"
    id = Column(Integer, primary_key=True, index=True)
    token = Column(String, unique=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)


class DBAnnouncement(Base):
    __tablename__ = "announcements"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    content = Column(String)


Base.metadata.create_all(bind=engine)


class User(BaseModel):
    username: str
    password: str
    email: str


class Announcement(BaseModel):
    title: str
    content: str


class Token(BaseModel):
    access_token: str


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Secret key to sign JWT
SECRET_KEY = "samira"
ALGORITHM = "HS256"


def create_jwt_token(data: dict, db: Session):
    to_encode = data.copy()
    expires = datetime.utcnow() + timedelta(minutes=30)
    to_encode.update({"exp": expires})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    # Save the token to the database
    db_token = DBToken(token=encoded_jwt, expires_at=expires)
    db.add(db_token)
    db.commit()

    return encoded_jwt


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# Adjusted function for token validation
def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(status_code=401, detail="Could not validate credentials")

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(DBUser).filter(DBUser.username == username).first()
    if user is None:
        raise credentials_exception

    return user
