from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..models import User
from ..schemas import (
    RecommendationRequest,
    RecommendationResponse,
    BookRecommendation,
    ComfortLevel,
    Book as BookSchema
)
from ..recommender import BookRecommender

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.post("/{user_id}", response_model=RecommendationResponse)
def get_recommendations(
    user_id: int,
    request: RecommendationRequest,
    db: Session = Depends(get_db)
):
    """Get personalized book recommendations based on user's reading history and comfort level."""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Initialize recommender
    recommender = BookRecommender(db)
    
    # Get recommendations
    recommendations = recommender.recommend_books(user_id, request)
    
    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail="No recommendations found. Try adjusting your filters or comfort level."
        )
    
    # Calculate average similarity score
    avg_similarity = sum(rec.score for rec in recommendations) / len(recommendations)
    
    # Get explanation
    explanation = recommender.get_recommendation_explanation(
        request.comfort_level, 
        avg_similarity
    )
    
    return RecommendationResponse(
        books=[rec.book for rec in recommendations],
        explanation=explanation,
        comfort_level=request.comfort_level,
        similarity_score=avg_similarity
    )

@router.get("/{user_id}/detailed", response_model=List[BookRecommendation])
def get_detailed_recommendations(
    user_id: int,
    comfort_level: ComfortLevel = ComfortLevel.BALANCED,
    limit: int = Query(10, ge=1, le=50),
    exclude_read: bool = True,
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_page_count: Optional[int] = Query(None, ge=1),
    preferred_genres: Optional[List[str]] = Query(None),
    db: Session = Depends(get_db)
):
    """Get detailed recommendations with scores and reasons."""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Create request object
    request = RecommendationRequest(
        comfort_level=comfort_level,
        limit=limit,
        exclude_read=exclude_read,
        min_rating=min_rating,
        max_page_count=max_page_count,
        preferred_genres=preferred_genres
    )
    
    # Initialize recommender
    recommender = BookRecommender(db)
    
    # Get recommendations
    recommendations = recommender.recommend_books(user_id, request)
    
    if not recommendations:
        raise HTTPException(
            status_code=404,
            detail="No recommendations found. Try adjusting your filters or comfort level."
        )
    
    return recommendations

@router.get("/{user_id}/comfort-levels", response_model=List[RecommendationResponse])
def get_recommendations_by_comfort_level(
    user_id: int,
    limit: int = Query(5, ge=1, le=20),
    exclude_read: bool = True,
    db: Session = Depends(get_db)
):
    """Get recommendations for all comfort levels to help users compare."""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Initialize recommender
    recommender = BookRecommender(db)
    
    responses = []
    
    for comfort_level in ComfortLevel:
        request = RecommendationRequest(
            comfort_level=comfort_level,
            limit=limit,
            exclude_read=exclude_read
        )
        
        try:
            recommendations = recommender.recommend_books(user_id, request)
            
            if recommendations:
                # Calculate average similarity score
                avg_similarity = sum(rec.score for rec in recommendations) / len(recommendations)
                
                # Get explanation
                explanation = recommender.get_recommendation_explanation(
                    comfort_level, 
                    avg_similarity
                )
                
                responses.append(RecommendationResponse(
                    books=[rec.book for rec in recommendations],
                    explanation=explanation,
                    comfort_level=comfort_level,
                    similarity_score=avg_similarity
                ))
        except Exception:
            # Skip comfort levels that don't have recommendations
            continue
    
    if not responses:
        raise HTTPException(
            status_code=404,
            detail="No recommendations found for any comfort level."
        )
    
    return responses

@router.get("/{user_id}/similar/{book_id}", response_model=List[BookSchema])
def get_similar_books(
    user_id: int,
    book_id: int,
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get books similar to a specific book."""
    
    # Check if user exists
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Check if book exists
    from ..models import Book
    book = db.query(Book).filter(Book.id == book_id).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    # Find similar books based on genres and authors
    similar_books = db.query(Book).filter(Book.id != book_id)
    
    if book.genres:
        genre_names = [g.name for g in book.genres]
        similar_books = similar_books.join(Book.genres).filter(
            Book.genres.any(Genre.name.in_(genre_names))
        )
    
    if book.authors:
        author_names = [a.name for a in book.authors]
        similar_books = similar_books.join(Book.authors).filter(
            Book.authors.any(Author.name.in_(author_names))
        )
    
    # Exclude books the user has already read
    from ..models import Reading
    read_book_ids = db.query(Reading.book_id).filter(
        Reading.user_id == user_id,
        Reading.status.in_(["completed", "reading", "abandoned"])
    ).subquery()
    
    similar_books = similar_books.filter(~Book.id.in_(read_book_ids))
    
    # Order by rating and limit results
    similar_books = similar_books.order_by(Book.average_rating.desc()).limit(limit).all()
    
    return similar_books