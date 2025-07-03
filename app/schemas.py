from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ReadingStatus(str, Enum):
    READING = "reading"
    COMPLETED = "completed"
    WANT_TO_READ = "want_to_read"
    ABANDONED = "abandoned"

class ComfortLevel(str, Enum):
    SAME_OLD = "same_old"          # Very similar to previous reads
    COMFORT_ZONE = "comfort_zone"  # Somewhat similar
    BALANCED = "balanced"          # Mix of familiar and new
    ADVENTUROUS = "adventurous"    # Somewhat different
    COMPLETELY_NEW = "completely_new"  # Very different

# Base schemas
class AuthorBase(BaseModel):
    name: str

class AuthorCreate(AuthorBase):
    pass

class Author(AuthorBase):
    id: int
    
    class Config:
        from_attributes = True

class GenreBase(BaseModel):
    name: str

class GenreCreate(GenreBase):
    pass

class Genre(GenreBase):
    id: int
    
    class Config:
        from_attributes = True

class BookBase(BaseModel):
    title: str
    isbn: Optional[str] = None
    publication_year: Optional[int] = None
    description: Optional[str] = None
    page_count: Optional[int] = None
    average_rating: Optional[float] = None
    ratings_count: Optional[int] = None
    language: Optional[str] = None
    publisher: Optional[str] = None

class BookCreate(BookBase):
    author_ids: List[int] = []
    genre_ids: List[int] = []

class Book(BookBase):
    id: int
    authors: List[Author] = []
    genres: List[Genre] = []
    
    class Config:
        from_attributes = True

class ReadingBase(BaseModel):
    book_id: int
    rating: Optional[float] = None
    status: ReadingStatus = ReadingStatus.WANT_TO_READ
    start_date: Optional[datetime] = None
    finish_date: Optional[datetime] = None
    review: Optional[str] = None

class ReadingCreate(ReadingBase):
    pass

class Reading(ReadingBase):
    id: int
    user_id: int
    book: Book
    created_at: datetime
    
    class Config:
        from_attributes = True

class UserPreferenceBase(BaseModel):
    preferred_genres: Optional[List[str]] = []
    preferred_authors: Optional[List[str]] = []
    min_rating: Optional[float] = 3.0
    max_page_count: Optional[int] = None
    min_page_count: Optional[int] = None
    preferred_languages: Optional[List[str]] = []

class UserPreferenceCreate(UserPreferenceBase):
    pass

class UserPreference(UserPreferenceBase):
    id: int
    user_id: int
    
    class Config:
        from_attributes = True

class UserBase(BaseModel):
    email: str
    username: str

class UserCreate(UserBase):
    password: str

class User(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    preferences: Optional[UserPreference] = None
    
    class Config:
        from_attributes = True

class RecommendationRequest(BaseModel):
    comfort_level: ComfortLevel = ComfortLevel.BALANCED
    limit: int = 10
    exclude_read: bool = True
    min_rating: Optional[float] = None
    max_page_count: Optional[int] = None
    preferred_genres: Optional[List[str]] = None

class RecommendationResponse(BaseModel):
    books: List[Book]
    explanation: str
    comfort_level: ComfortLevel
    similarity_score: float  # How similar the recommendations are to user's history (0-1)

class BookRecommendation(BaseModel):
    book: Book
    score: float
    reasons: List[str]  # Why this book was recommended