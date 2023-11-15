from models import *
import logging
from logging.handlers import RotatingFileHandler

log_filename = 'main.log'
max_log_size = 5 * 1024 * 1024
log_handler = RotatingFileHandler(log_filename, maxBytes=max_log_size, backupCount=3)
log_handler.setLevel(logging.DEBUG)

# Create a logger and add the handler
logger = logging.getLogger('')
logger.addHandler(log_handler)

# Set the log message format
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
log_handler.setFormatter(formatter)

# SQLAlchemy setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./users.db"  # Use your database URL
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()


@app.get("/")
def read_root():
    return {"message": "Welcome to the homepage"}


@app.post("/api/sign-up/", response_model=dict)
def sign_up(user: User, db: Session = Depends(get_db)):
    db_user = DBUser(**user.model_dump())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return {"message": "User successfully registered"}


# Modified login endpoint with proper token generation
@app.post("/api/login/", response_model=Token)
def login(user: User, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.username == user.username).first()
    if db_user and db_user.password == user.password:
        # Generate and save a proper JWT token
        access_token = create_jwt_token(data={"sub": user.username}, db=db)
        return {"access_token": access_token}
    raise HTTPException(status_code=401, detail="Invalid credentials")


# Modified get_profile endpoint with Authorization header
@app.get("/api/profile/", response_model=dict, dependencies=[Depends(get_current_user)])
def get_profile(
        current_user: DBUser = Depends(get_current_user),
        authorization: str = Header(..., description="Access token in Authorization header"),
):
    # Validate the access token, you can also use Depends(get_current_user) instead
    if authorization != current_user.token:
        raise HTTPException(status_code=401, detail="Invalid access token")

    return {"username": current_user.username, "email": current_user.email}


@app.post("/api/announcements/", response_model=dict, dependencies=[Depends(get_current_user)])
def insert_announcement(announcement: Announcement, db: Session = Depends(get_db)):
    db_announcement = DBAnnouncement(**announcement.model_dump())
    db.add(db_announcement)
    db.commit()
    db.refresh(db_announcement)
    return {"message": "Announcement successfully created", "announcement_id": db_announcement.id}


@app.put("/api/announcements/{announcement_id}/", response_model=dict, dependencies=[Depends(get_current_user)])
def update_announcement(announcement_id: int, new_announcement: Announcement, db: Session = Depends(get_db)):
    db_announcement = db.query(DBAnnouncement).filter(DBAnnouncement.id == announcement_id).first()
    if db_announcement:
        db_announcement.title = new_announcement.title
        db_announcement.content = new_announcement.content
        db.commit()
        db.refresh(db_announcement)
        return {"message": "Announcement successfully updated", "announcement_id": db_announcement.id}
    raise HTTPException(status_code=404, detail="Announcement not found")


# Delete Announcement API
@app.delete("/api/announcements/{announcement_id}/", response_model=dict, dependencies=[Depends(get_current_user)])
def delete_announcement(announcement_id: int, db: Session = Depends(get_db)):
    db_announcement = db.query(DBAnnouncement).filter(DBAnnouncement.id == announcement_id).first()
    if db_announcement:
        db.delete(db_announcement)
        db.commit()
        return {"message": "Announcement successfully deleted"}
    raise HTTPException(status_code=404, detail="Announcement not found")


# List Announcements API
@app.get("/api/announcements/", response_model=list)
def list_announcements(db: Session = Depends(get_db)):
    announcements = db.query(DBAnnouncement).all()
    if announcements:
        return announcements
    raise HTTPException(status_code=404, detail="Announcement not found")


# Search Announcements API
@app.get("/api/announcements/search/", response_model=list)
def search_announcements(query: str, db: Session = Depends(get_db)):
    matching_announcements = db.query(DBAnnouncement).filter(
        DBAnnouncement.title.contains(query) | DBAnnouncement.content.contains(query)).all()
    return matching_announcements


# Number of Views API
@app.get("/api/announcements/{announcement_id}/views/", response_model=dict)
def get_number_of_views(announcement_id: int, db: Session = Depends(get_db)):
    db_announcement = db.query(DBAnnouncement).filter(DBAnnouncement.id == announcement_id).first()
    if db_announcement:
        return {"announcement_id": db_announcement.id, "views": db_announcement.views}
    raise HTTPException(status_code=404, detail="Announcement not found")


@app.get("/api/my-announcements/", response_model=list, dependencies=[Depends(get_current_user)])
def get_my_announcements(current_user: DBUser = Depends(get_current_user), db: Session = Depends(get_db)):
    user_announcements = db.query(DBAnnouncement).filter(DBAnnouncement.author_id == current_user.id).all()
    return user_announcements
