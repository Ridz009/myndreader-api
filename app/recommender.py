from sqlalchemy.orm import Session
from typing import List, Dict, Set, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter, defaultdict
import json
import random

from .models import User, Book, Reading, Genre, Author
from .schemas import ComfortLevel, RecommendationRequest, BookRecommendation


class BookRecommender:
    def __init__(self, db: Session):
        self.db = db
        
    def get_user_reading_history(self, user_id: int) -> List[Reading]:
        """Get user's reading history, prioritizing completed and highly rated books."""
        return self.db.query(Reading).filter(
            Reading.user_id == user_id,
            Reading.status.in_(["completed", "reading"])
        ).all()
    
    def extract_user_preferences(self, readings: List[Reading]) -> Dict:
        """Extract user preferences from reading history."""
        if not readings:
            return {}
        
        # Extract genres
        genre_counts = Counter()
        author_counts = Counter()
        ratings = []
        page_counts = []
        languages = []
        
        for reading in readings:
            book = reading.book
            
            # Count genres
            for genre in book.genres:
                weight = 1.0
                if reading.rating and reading.rating >= 4.0:
                    weight = 2.0  # Higher weight for highly rated books
                elif reading.rating and reading.rating <= 2.0:
                    weight = 0.5  # Lower weight for poorly rated books
                genre_counts[genre.name] += weight
            
            # Count authors
            for author in book.authors:
                weight = 1.0
                if reading.rating and reading.rating >= 4.0:
                    weight = 2.0
                elif reading.rating and reading.rating <= 2.0:
                    weight = 0.5
                author_counts[author.name] += weight
            
            if reading.rating:
                ratings.append(reading.rating)
            if book.page_count:
                page_counts.append(book.page_count)
            if book.language:
                languages.append(book.language)
        
        return {
            'genres': dict(genre_counts),
            'authors': dict(author_counts),
            'avg_rating': np.mean(ratings) if ratings else 3.0,
            'avg_page_count': np.mean(page_counts) if page_counts else None,
            'languages': Counter(languages),
            'total_books': len(readings)
        }
    
    def calculate_comfort_level_weights(self, comfort_level: ComfortLevel) -> Dict[str, float]:
        """Calculate weights for different recommendation factors based on comfort level."""
        weights = {
            ComfortLevel.SAME_OLD: {
                'genre_similarity': 0.9,
                'author_similarity': 0.8,
                'rating_similarity': 0.7,
                'page_count_similarity': 0.6,
                'novelty_penalty': 0.9,  # High penalty for new/different books
                'randomness': 0.1
            },
            ComfortLevel.COMFORT_ZONE: {
                'genre_similarity': 0.7,
                'author_similarity': 0.6,
                'rating_similarity': 0.5,
                'page_count_similarity': 0.4,
                'novelty_penalty': 0.6,
                'randomness': 0.2
            },
            ComfortLevel.BALANCED: {
                'genre_similarity': 0.5,
                'author_similarity': 0.4,
                'rating_similarity': 0.4,
                'page_count_similarity': 0.3,
                'novelty_penalty': 0.3,
                'randomness': 0.3
            },
            ComfortLevel.ADVENTUROUS: {
                'genre_similarity': 0.3,
                'author_similarity': 0.2,
                'rating_similarity': 0.3,
                'page_count_similarity': 0.2,
                'novelty_penalty': 0.1,
                'randomness': 0.5
            },
            ComfortLevel.COMPLETELY_NEW: {
                'genre_similarity': 0.1,
                'author_similarity': 0.1,
                'rating_similarity': 0.2,
                'page_count_similarity': 0.1,
                'novelty_penalty': -0.3,  # Negative penalty = bonus for new books
                'randomness': 0.7
            }
        }
        return weights[comfort_level]
    
    def score_book_similarity(self, book: Book, user_prefs: Dict, weights: Dict[str, float]) -> Tuple[float, List[str]]:
        """Score how similar a book is to user preferences."""
        score = 0.0
        reasons = []
        
        # Genre similarity
        if book.genres and user_prefs.get('genres'):
            genre_matches = 0
            total_genre_weight = sum(user_prefs['genres'].values())
            
            for genre in book.genres:
                if genre.name in user_prefs['genres']:
                    genre_weight = user_prefs['genres'][genre.name] / total_genre_weight
                    genre_matches += genre_weight
                    reasons.append(f"Matches your favorite genre: {genre.name}")
            
            genre_score = genre_matches * weights['genre_similarity']
            score += genre_score
        
        # Author similarity
        if book.authors and user_prefs.get('authors'):
            author_matches = 0
            total_author_weight = sum(user_prefs['authors'].values())
            
            for author in book.authors:
                if author.name in user_prefs['authors']:
                    author_weight = user_prefs['authors'][author.name] / total_author_weight
                    author_matches += author_weight
                    reasons.append(f"By author you've enjoyed: {author.name}")
            
            author_score = author_matches * weights['author_similarity']
            score += author_score
        
        # Rating similarity
        if book.average_rating and user_prefs.get('avg_rating'):
            rating_diff = abs(book.average_rating - user_prefs['avg_rating'])
            rating_score = (1 - rating_diff / 5) * weights['rating_similarity']
            score += rating_score
            
            if book.average_rating >= 4.0:
                reasons.append("Highly rated book")
        
        # Page count similarity
        if book.page_count and user_prefs.get('avg_page_count'):
            page_diff = abs(book.page_count - user_prefs['avg_page_count'])
            max_diff = max(book.page_count, user_prefs['avg_page_count'])
            page_score = (1 - page_diff / max_diff) * weights['page_count_similarity']
            score += page_score
        
        # Novelty factor (penalize/reward based on comfort level)
        novelty_score = 0
        if book.genres and user_prefs.get('genres'):
            # Check if book introduces new genres
            new_genres = [g.name for g in book.genres if g.name not in user_prefs['genres']]
            if new_genres:
                novelty_score = weights['novelty_penalty'] * len(new_genres) / len(book.genres)
                if weights['novelty_penalty'] < 0:  # Bonus for new books
                    reasons.append(f"Explores new genres: {', '.join(new_genres)}")
        
        score += novelty_score
        
        # Add randomness factor
        randomness_score = random.random() * weights['randomness']
        score += randomness_score
        
        return max(0, score), reasons
    
    def get_candidate_books(self, user_id: int, request: RecommendationRequest) -> List[Book]:
        """Get candidate books for recommendation."""
        query = self.db.query(Book)
        
        # Exclude books user has already read
        if request.exclude_read:
            read_book_ids = self.db.query(Reading.book_id).filter(
                Reading.user_id == user_id,
                Reading.status.in_(["completed", "reading", "abandoned"])
            ).subquery()
            query = query.filter(~Book.id.in_(read_book_ids))
        
        # Apply filters
        if request.min_rating:
            query = query.filter(Book.average_rating >= request.min_rating)
        
        if request.max_page_count:
            query = query.filter(Book.page_count <= request.max_page_count)
        
        if request.preferred_genres:
            query = query.join(Book.genres).filter(
                Genre.name.in_(request.preferred_genres)
            )
        
        return query.all()
    
    def recommend_books(self, user_id: int, request: RecommendationRequest) -> List[BookRecommendation]:
        """Generate book recommendations based on user's reading history and comfort level."""
        
        # Get user's reading history
        readings = self.get_user_reading_history(user_id)
        
        if not readings:
            # For new users, recommend popular books
            return self._recommend_for_new_user(request)
        
        # Extract user preferences
        user_prefs = self.extract_user_preferences(readings)
        
        # Get comfort level weights
        weights = self.calculate_comfort_level_weights(request.comfort_level)
        
        # Get candidate books
        candidates = self.get_candidate_books(user_id, request)
        
        # Score each candidate
        scored_books = []
        for book in candidates:
            score, reasons = self.score_book_similarity(book, user_prefs, weights)
            scored_books.append(BookRecommendation(
                book=book,
                score=score,
                reasons=reasons
            ))
        
        # Sort by score and return top recommendations
        scored_books.sort(key=lambda x: x.score, reverse=True)
        return scored_books[:request.limit]
    
    def _recommend_for_new_user(self, request: RecommendationRequest) -> List[BookRecommendation]:
        """Recommend books for users with no reading history."""
        query = self.db.query(Book).filter(
            Book.average_rating >= 4.0,
            Book.ratings_count >= 100
        )
        
        if request.preferred_genres:
            query = query.join(Book.genres).filter(
                Genre.name.in_(request.preferred_genres)
            )
        
        books = query.order_by(Book.average_rating.desc()).limit(request.limit).all()
        
        return [
            BookRecommendation(
                book=book,
                score=book.average_rating / 5.0,
                reasons=["Popular and highly rated book", "Great for discovering new preferences"]
            )
            for book in books
        ]
    
    def get_recommendation_explanation(self, comfort_level: ComfortLevel, similarity_score: float) -> str:
        """Generate an explanation for the recommendation."""
        explanations = {
            ComfortLevel.SAME_OLD: f"These recommendations are very similar to your previous reads (similarity: {similarity_score:.1%}). Perfect for when you want more of what you love!",
            ComfortLevel.COMFORT_ZONE: f"These books stay close to your preferences (similarity: {similarity_score:.1%}) while introducing some gentle variety.",
            ComfortLevel.BALANCED: f"A balanced mix of familiar and new (similarity: {similarity_score:.1%}). These books match some of your preferences while encouraging exploration.",
            ComfortLevel.ADVENTUROUS: f"These recommendations venture into new territory (similarity: {similarity_score:.1%}) while still connecting to your interests.",
            ComfortLevel.COMPLETELY_NEW: f"Time to explore something completely different! These books (similarity: {similarity_score:.1%}) will expand your literary horizons."
        }
        return explanations[comfort_level]