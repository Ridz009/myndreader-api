# MyndReader API

A personalized book recommendation API with innovative comfort level controls that let users choose how similar or different their next read should be from their previous books.

## 🚀 Features

- **Comfort Level Recommendations**: Choose from 5 comfort levels:
  - `same_old` - Very similar to your previous reads
  - `comfort_zone` - Somewhat similar with gentle variety
  - `balanced` - Mix of familiar and new
  - `adventurous` - Venturing into new territory
  - `completely_new` - Completely different experiences

- **Personalized Recommendations**: Based on your reading history, ratings, and preferences
- **Advanced Filtering**: Filter by genre, author, rating, page count, and more
- **Reading Progress Tracking**: Track books you're reading, completed, or want to read
- **User Preferences**: Set preferred genres, authors, and reading constraints

## 🛠 Setup

### Prerequisites

- Python 3.8+
- PostgreSQL database
- pip

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd myndreader-api
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

5. Set up the database:
```bash
# Create PostgreSQL database
createdb myndreader

# Run the application to create tables
python -m app.main
```

6. (Optional) Load sample data:
```bash
# You can load the sample books from data/books.csv
python scripts/load_sample_data.py
```

## 🚀 Running the Application

```bash
# Development
uvicorn app.main:app --reload

# Production
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## 📖 API Documentation

Once running, visit:
- **Interactive API docs**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## 🔧 Environment Variables

Create a `.env` file in the root directory:

```env
DATABASE_URL=postgresql://username:password@localhost/myndreader
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

## 📊 Database Schema

### Core Tables
- **Users**: User accounts and authentication
- **Books**: Book information with genres and authors
- **Readings**: User's reading history and ratings
- **UserPreferences**: User's reading preferences

### Relationships
- Books ↔ Authors (Many-to-Many)
- Books ↔ Genres (Many-to-Many)
- Users ↔ Readings (One-to-Many)
- Users ↔ UserPreferences (One-to-One)

## 🎯 Key Endpoints

### Books
- `GET /books/` - Search and filter books
- `POST /books/` - Add new books
- `GET /books/{book_id}` - Get book details
- `GET /books/authors/` - Get authors
- `GET /books/genres/` - Get genres

### Users
- `POST /users/` - Create user account
- `GET /users/{user_id}` - Get user profile
- `GET /users/{user_id}/readings` - Get reading history
- `POST /users/{user_id}/readings` - Add book to reading list
- `GET /users/{user_id}/preferences` - Get user preferences

### Recommendations
- `POST /recommendations/{user_id}` - Get personalized recommendations
- `GET /recommendations/{user_id}/detailed` - Get detailed recommendations with scores
- `GET /recommendations/{user_id}/comfort-levels` - Compare all comfort levels
- `GET /recommendations/{user_id}/similar/{book_id}` - Get books similar to a specific book

## 🧠 How the Comfort Level System Works

The recommendation algorithm considers multiple factors:

1. **Genre Similarity**: How closely the recommended books match your preferred genres
2. **Author Similarity**: Recommendations from authors you've enjoyed
3. **Rating Patterns**: Books with ratings similar to what you typically enjoy
4. **Page Count Preferences**: Books that match your typical reading length
5. **Novelty Factor**: Introduces new elements based on your comfort level

### Comfort Level Weights

Each comfort level applies different weights to these factors:

- **Same Old**: High weight on genre/author similarity, penalty for new content
- **Comfort Zone**: Moderate similarity weights, slight variety
- **Balanced**: Equal weight on similarity and exploration
- **Adventurous**: Lower similarity weights, encourages new genres/authors
- **Completely New**: Minimal similarity weights, bonus for novel content

## 🔄 Example Usage

### Create a User
```bash
curl -X POST "http://localhost:8000/users/" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "reader@example.com",
    "username": "bookworm",
    "password": "securepassword"
  }'
```

### Add a Book to Reading List
```bash
curl -X POST "http://localhost:8000/users/1/readings" \
  -H "Content-Type: application/json" \
  -d '{
    "book_id": 42,
    "status": "reading",
    "rating": 5
  }'
```

### Get Recommendations
```bash
curl -X POST "http://localhost:8000/recommendations/1" \
  -H "Content-Type: application/json" \
    -d '{
    "comfort_level": "balanced",
    "genre": "fantasy",
    "author": "J.K. Rowling",
    "min_rating": 4,
    "max_page_count": 500
    }'
```
