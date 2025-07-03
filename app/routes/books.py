from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import Book, Author, Genre
from ..schemas import Book as BookSchema, BookCreate, Author as AuthorSchema, Genre as GenreSchema

router = APIRouter(prefix="/books", tags=["books"])

@router.get("/", response_model=List[BookSchema])
def get_books(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search in title, author, or genre"),
    genre: Optional[str] = Query(None, description="Filter by genre"),
    author: Optional[str] = Query(None, description="Filter by author"),
    min_rating: Optional[float] = Query(None, description="Minimum average rating"),
    max_page_count: Optional[int] = Query(None, description="Maximum page count"),
    db: Session = Depends(get_db)
):
    """Get books with optional filtering and search."""
    query = db.query(Book)
    
    if search:
        query = query.filter(
            Book.title.ilike(f"%{search}%") |
            Book.description.ilike(f"%{search}%")
        )
    
    if genre:
        query = query.join(Book.genres).filter(Genre.name.ilike(f"%{genre}%"))
    
    if author:
        query = query.join(Book.authors).filter(Author.name.ilike(f"%{author}%"))
    
    if min_rating:
        query = query.filter(Book.average_rating >= min_rating)
    
    if max_page_count:
        query = query.filter(Book.page_count <= max_page_count)
    
    books = query.offset(skip).limit(limit).all()
    return books

@router.get("/{book_id}", response_model=BookSchema)
def get_book(book_id: int, db: Session = Depends(get_db)):
    """Get a specific book by ID."""
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    return book

@router.post("/", response_model=BookSchema)
def create_book(book: BookCreate, db: Session = Depends(get_db)):
    """Create a new book."""
    # Check if book with same ISBN already exists
    if book.isbn:
        existing = db.query(Book).filter(Book.isbn == book.isbn).first()
        if existing:
            raise HTTPException(status_code=400, detail="Book with this ISBN already exists")
    
    # Create new book
    db_book = Book(
        title=book.title,
        isbn=book.isbn,
        publication_year=book.publication_year,
        description=book.description,
        page_count=book.page_count,
        average_rating=book.average_rating,
        ratings_count=book.ratings_count,
        language=book.language,
        publisher=book.publisher
    )
    
    # Add authors
    if book.author_ids:
        authors = db.query(Author).filter(Author.id.in_(book.author_ids)).all()
        db_book.authors = authors
    
    # Add genres
    if book.genre_ids:
        genres = db.query(Genre).filter(Genre.id.in_(book.genre_ids)).all()
        db_book.genres = genres
    
    db.add(db_book)
    db.commit()
    db.refresh(db_book)
    return db_book

@router.get("/authors/", response_model=List[AuthorSchema])
def get_authors(
    skip: int = 0,
    limit: int = 100,
    search: Optional[str] = Query(None, description="Search author names"),
    db: Session = Depends(get_db)
):
    """Get authors with optional search."""
    query = db.query(Author)
    
    if search:
        query = query.filter(Author.name.ilike(f"%{search}%"))
    
    authors = query.offset(skip).limit(limit).all()
    return authors

@router.post("/authors/", response_model=AuthorSchema)
def create_author(author: AuthorSchema, db: Session = Depends(get_db)):
    """Create a new author."""
    # Check if author already exists
    existing = db.query(Author).filter(Author.name == author.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Author already exists")
    
    db_author = Author(name=author.name)
    db.add(db_author)
    db.commit()
    db.refresh(db_author)
    return db_author

@router.get("/genres/", response_model=List[GenreSchema])
def get_genres(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get all genres."""
    genres = db.query(Genre).offset(skip).limit(limit).all()
    return genres

@router.post("/genres/", response_model=GenreSchema)
def create_genre(genre: GenreSchema, db: Session = Depends(get_db)):
    """Create a new genre."""
    # Check if genre already exists
    existing = db.query(Genre).filter(Genre.name == genre.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Genre already exists")
    
    db_genre = Genre(name=genre.name)
    db.add(db_genre)
    db.commit()
    db.refresh(db_genre)
    return db_genre