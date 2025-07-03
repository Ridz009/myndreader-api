from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from passlib.context import CryptContext
from ..database import get_db
from ..models import User, Reading, UserPreference
from ..schemas import (
    User as UserSchema, 
    UserCreate, 
    Reading as ReadingSchema,
    ReadingCreate,
    UserPreference as UserPreferenceSchema,
    UserPreferenceCreate
)
import json

router = APIRouter(prefix="/users", tags=["users"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

@router.post("/", response_model=UserSchema)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.email == user.email) | (User.username == user.username)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="User with this email or username already exists"
        )
    
    # Create new user
    db_user = User(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password)
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@router.get("/{user_id}", response_model=UserSchema)
def get_user(user_id: int, db: Session = Depends(get_db)):
    """Get a specific user by ID."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}/readings", response_model=List[ReadingSchema])
def get_user_readings(
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    status: str = None,
    db: Session = Depends(get_db)
):
    """Get user's reading history."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    query = db.query(Reading).filter(Reading.user_id == user_id)
    
    if status:
        query = query.filter(Reading.status == status)
    
    readings = query.offset(skip).limit(limit).all()
    return readings

@router.post("/{user_id}/readings", response_model=ReadingSchema)
def add_reading(
    user_id: int,
    reading: ReadingCreate,
    db: Session = Depends(get_db)
):
    """Add a book to user's reading list."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if book exists
    from ..models import Book
    book = db.query(Book).filter(Book.id == reading.book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Check if reading already exists
    existing_reading = db.query(Reading).filter(
        Reading.user_id == user_id,
        Reading.book_id == reading.book_id
    ).first()
    
    if existing_reading:
        raise HTTPException(
            status_code=400,
            detail="Reading entry for this book already exists"
        )
    
    # Create new reading
    db_reading = Reading(
        user_id=user_id,
        book_id=reading.book_id,
        rating=reading.rating,
        status=reading.status,
        start_date=reading.start_date,
        finish_date=reading.finish_date,
        review=reading.review
    )
    
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading

@router.put("/{user_id}/readings/{reading_id}", response_model=ReadingSchema)
def update_reading(
    user_id: int,
    reading_id: int,
    reading_update: ReadingCreate,
    db: Session = Depends(get_db)
):
    """Update a reading entry."""
    # Get existing reading
    db_reading = db.query(Reading).filter(
        Reading.id == reading_id,
        Reading.user_id == user_id
    ).first()
    
    if not db_reading:
        raise HTTPException(status_code=404, detail="Reading not found")
    
    # Update fields
    for field, value in reading_update.dict(exclude_unset=True).items():
        setattr(db_reading, field, value)
    
    db.commit()
    db.refresh(db_reading)
    return db_reading

@router.get("/{user_id}/preferences", response_model=UserPreferenceSchema)
def get_user_preferences(user_id: int, db: Session = Depends(get_db)):
    """Get user's preferences."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    preferences = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if not preferences:
        # Return default preferences
        return UserPreferenceSchema(
            id=0,
            user_id=user_id,
            preferred_genres=[],
            preferred_authors=[],
            min_rating=3.0,
            max_page_count=None,
            min_page_count=None,
            preferred_languages=[]
        )
    
    # Parse JSON fields
    result = UserPreferenceSchema(
        id=preferences.id,
        user_id=preferences.user_id,
        preferred_genres=json.loads(preferences.preferred_genres or "[]"),
        preferred_authors=json.loads(preferences.preferred_authors or "[]"),
        min_rating=preferences.min_rating,
        max_page_count=preferences.max_page_count,
        min_page_count=preferences.min_page_count,
        preferred_languages=json.loads(preferences.preferred_languages or "[]")
    )
    
    return result

@router.post("/{user_id}/preferences", response_model=UserPreferenceSchema)
def create_or_update_preferences(
    user_id: int,
    preferences: UserPreferenceCreate,
    db: Session = Depends(get_db)
):
    """Create or update user preferences."""
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if preferences already exist
    existing_prefs = db.query(UserPreference).filter(
        UserPreference.user_id == user_id
    ).first()
    
    if existing_prefs:
        # Update existing preferences
        existing_prefs.preferred_genres = json.dumps(preferences.preferred_genres or [])
        existing_prefs.preferred_authors = json.dumps(preferences.preferred_authors or [])
        existing_prefs.min_rating = preferences.min_rating
        existing_prefs.max_page_count = preferences.max_page_count
        existing_prefs.min_page_count = preferences.min_page_count
        existing_prefs.preferred_languages = json.dumps(preferences.preferred_languages or [])
        
        db.commit()
        db.refresh(existing_prefs)
        
        return UserPreferenceSchema(
            id=existing_prefs.id,
            user_id=existing_prefs.user_id,
            preferred_genres=json.loads(existing_prefs.preferred_genres or "[]"),
            preferred_authors=json.loads(existing_prefs.preferred_authors or "[]"),
            min_rating=existing_prefs.min_rating,
            max_page_count=existing_prefs.max_page_count,
            min_page_count=existing_prefs.min_page_count,
            preferred_languages=json.loads(existing_prefs.preferred_languages or "[]")
        )
    else:
        # Create new preferences
        db_prefs = UserPreference(
            user_id=user_id,
            preferred_genres=json.dumps(preferences.preferred_genres or []),
            preferred_authors=json.dumps(preferences.preferred_authors or []),
            min_rating=preferences.min_rating,
            max_page_count=preferences.max_page_count,
            min_page_count=preferences.min_page_count,
            preferred_languages=json.dumps(preferences.preferred_languages or [])
        )
        
        db.add(db_prefs)
        db.commit()
        db.refresh(db_prefs)
        
        return UserPreferenceSchema(
            id=db_prefs.id,
            user_id=db_prefs.user_id,
            preferred_genres=json.loads(db_prefs.preferred_genres or "[]"),
            preferred_authors=json.loads(db_prefs.preferred_authors or "[]"),
            min_rating=db_prefs.min_rating,
            max_page_count=db_prefs.max_page_count,
            min_page_count=db_prefs.min_page_count,
            preferred_languages=json.loads(db_prefs.preferred_languages or "[]")
        )