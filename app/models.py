from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, Boolean, Table
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base

# Many-to-many relationship between books and genres
book_genres = Table(
    'book_genres',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True),
    Column('genre_id', Integer, ForeignKey('genres.id'), primary_key=True)
)

# Many-to-many relationship between books and authors
book_authors = Table(
    'book_authors',
    Base.metadata,
    Column('book_id', Integer, ForeignKey('books.id'), primary_key=True),
    Column('author_id', Integer, ForeignKey('authors.id'), primary_key=True)
)

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    readings = relationship("Reading", back_populates="user")
    preferences = relationship("UserPreference", back_populates="user", uselist=False)

class Author(Base):
    __tablename__ = "authors"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    
    # Relationships
    books = relationship("Book", secondary=book_authors, back_populates="authors")

class Genre(Base):
    __tablename__ = "genres"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    
    # Relationships
    books = relationship("Book", secondary=book_genres, back_populates="genres")

class Book(Base):
    __tablename__ = "books"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    isbn = Column(String, unique=True, index=True)
    publication_year = Column(Integer)
    description = Column(Text)
    page_count = Column(Integer)
    average_rating = Column(Float)
    ratings_count = Column(Integer)
    language = Column(String)
    publisher = Column(String)
    
    # Relationships
    authors = relationship("Author", secondary=book_authors, back_populates="books")
    genres = relationship("Genre", secondary=book_genres, back_populates="books")
    readings = relationship("Reading", back_populates="book")

class Reading(Base):
    __tablename__ = "readings"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    book_id = Column(Integer, ForeignKey("books.id"))
    rating = Column(Float)  # User's rating (1-5)
    status = Column(String)  # "reading", "completed", "want_to_read", "abandoned"
    start_date = Column(DateTime(timezone=True))
    finish_date = Column(DateTime(timezone=True))
    review = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="readings")
    book = relationship("Book", back_populates="readings")

class UserPreference(Base):
    __tablename__ = "user_preferences"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    preferred_genres = Column(Text)  # JSON string of genre preferences
    preferred_authors = Column(Text)  # JSON string of author preferences
    min_rating = Column(Float, default=3.0)
    max_page_count = Column(Integer)
    min_page_count = Column(Integer)
    preferred_languages = Column(Text)  # JSON string of language preferences
    
    # Relationships
    user = relationship("User", back_populates="preferences")