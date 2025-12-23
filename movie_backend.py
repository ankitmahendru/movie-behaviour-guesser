from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import MinMaxScaler
import kagglehub
import os

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # This lets our frontend talk to the backend without issues

# Store our movie data and user preferences here
# movies_df will hold all the movie information from the dataset
movies_df = None

# Track what the user likes - gets smarter as they use the app
user_profile = {
    'genres': {},      # counts how many times they search each genre
    'decades': {},     # tracks their preferred time periods
    'languages': {}    # keeps track of language preferences
}

def load_dataset():
    """Load the IMDB dataset from Kaggle"""
    global movies_df
    
    try:
        # Try to download the dataset from Kaggle
        # This might take a minute the first time you run it
        path = kagglehub.dataset_download("harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows")
        
        # The dataset could be anywhere in the downloaded folder, so we need to find it
        csv_file = None
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith('.csv'):
                    csv_file = os.path.join(root, file)
                    break
        
        if csv_file:
            # Found it! Load the CSV into a pandas dataframe
            movies_df = pd.read_csv(csv_file)
            print(f"Dataset loaded successfully from {csv_file}")
            print(f"Total movies: {len(movies_df)}")
            
            # Clean up the data so it's easier to work with
            prepare_data()
        else:
            # Couldn't find the CSV file, use backup data
            print("CSV file not found. Using sample data.")
            create_sample_data()
            
    except Exception as e:
        # Something went wrong with Kaggle download - no biggie, we have backup data
        print(f"Error loading dataset: {e}")
        print("Using sample data instead.")
        create_sample_data()

def create_sample_data():
    """Create sample movie data for demonstration"""
    global movies_df
    
    # Just some classic movies I know everyone loves
    # This is our fallback if Kaggle download doesn't work
    sample_movies = [
        {"Series_Title": "The Shawshank Redemption", "Released_Year": "1994", "Genre": "Drama", "IMDB_Rating": 9.3, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZmRlYWMwMWFmXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg"},
        {"Series_Title": "The Godfather", "Released_Year": "1972", "Genre": "Crime", "IMDB_Rating": 9.2, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg"},
        {"Series_Title": "The Dark Knight", "Released_Year": "2008", "Genre": "Action", "IMDB_Rating": 9.0, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_SX300.jpg"},
        {"Series_Title": "Pulp Fiction", "Released_Year": "1994", "Genre": "Crime", "IMDB_Rating": 8.9, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg"},
        {"Series_Title": "Forrest Gump", "Released_Year": "1994", "Genre": "Drama", "IMDB_Rating": 8.8, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_SX300.jpg"},
        {"Series_Title": "Inception", "Released_Year": "2010", "Genre": "Sci-Fi", "IMDB_Rating": 8.8, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_SX300.jpg"},
        {"Series_Title": "The Matrix", "Released_Year": "1999", "Genre": "Sci-Fi", "IMDB_Rating": 8.7, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg"},
        {"Series_Title": "Goodfellas", "Released_Year": "1990", "Genre": "Crime", "IMDB_Rating": 8.7, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BY2NkZjEzMDgtN2RjYy00YzM1LWI4ZmQtMjIwYjFjNmI3ZGEwXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_SX300.jpg"},
        {"Series_Title": "Interstellar", "Released_Year": "2014", "Genre": "Sci-Fi", "IMDB_Rating": 8.6, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZkNWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_SX300.jpg"},
        {"Series_Title": "The Silence of the Lambs", "Released_Year": "1991", "Genre": "Thriller", "IMDB_Rating": 8.6, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BNjNhZTk0ZmEtNjJhMi00YzFlLWE1MmEtYzM1M2ZmMGMwMTU4XkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg"},
        {"Series_Title": "Parasite", "Released_Year": "2019", "Genre": "Thriller", "IMDB_Rating": 8.5, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BYWZjMjk3ZTItODQ2ZC00NTY5LWE0ZDYtZTI3MjcwN2Q5NTVkXkEyXkFqcGdeQXVyODk4OTc3MTY@._V1_SX300.jpg"},
        {"Series_Title": "Gladiator", "Released_Year": "2000", "Genre": "Action", "IMDB_Rating": 8.5, "Poster_Link": "https://m.media-amazon.com/images/M/MV5BMDliMmNhNDEtODUyOS00MjNlLTgxODEtN2U3NzIxMGVkZTA1L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_SX300.jpg"},
    ]
    
    movies_df = pd.DataFrame(sample_movies)
    prepare_data()

def prepare_data():
    """Prepare and clean the movie data"""
    global movies_df
    
    # Different datasets might have different column names
    # Let's standardize them so we always know what we're working with
    column_mapping = {
        'Series_Title': 'title',
        'Released_Year': 'year',
        'Genre': 'genre',
        'IMDB_Rating': 'rating',
        'Poster_Link': 'poster'
    }
    
    # Rename columns if they exist in the dataset
    for old_name, new_name in column_mapping.items():
        if old_name in movies_df.columns:
            movies_df.rename(columns={old_name: new_name}, inplace=True)
    
    # Clean up the year column - sometimes it has weird characters
    if 'year' in movies_df.columns:
        movies_df['year'] = pd.to_numeric(movies_df['year'], errors='coerce')
        movies_df = movies_df.dropna(subset=['year'])  # drop rows with invalid years
        movies_df['year'] = movies_df['year'].astype(int)
    
    # Calculate which decade each movie is from (e.g., 1990 -> 1990s)
    movies_df['decade'] = (movies_df['year'] // 10) * 10
    movies_df['decade_str'] = movies_df['decade'].astype(str) + 's'
    
    # If language isn't in the dataset, assume English
    if 'language' not in movies_df.columns:
        movies_df['language'] = 'English'
    
    # Some movies have multiple genres like "Action, Drama" - just take the first one
    if 'genre' in movies_df.columns:
        movies_df['genre'] = movies_df['genre'].apply(lambda x: str(x).split(',')[0].strip() if pd.notna(x) else 'Unknown')
    
    # Make sure rating is a number we can actually use
    if 'rating' in movies_df.columns:
        movies_df['rating'] = pd.to_numeric(movies_df['rating'], errors='coerce')
        movies_df = movies_df.dropna(subset=['rating'])
    
    # If there's no poster URL, use a placeholder
    if 'poster' not in movies_df.columns:
        movies_df['poster'] = 'https://via.placeholder.com/300x450?text=No+Poster'
    
    print(f"Data prepared. Columns: {movies_df.columns.tolist()}")

def get_decade_from_year(year):
    """Convert year to decade string"""
    # Simple helper function - turns 1994 into "1990s"
    return f"{(year // 10) * 10}s"

def update_user_profile(genre, decade, language):
    """Update user profile with ML-based tracking"""
    global user_profile
    
    # This is where the "learning" happens!
    # Every time someone searches, we remember what they looked for
    # Later we can use this to recommend similar stuff
    user_profile['genres'][genre] = user_profile['genres'].get(genre, 0) + 1
    user_profile['decades'][decade] = user_profile['decades'].get(decade, 0) + 1
    user_profile['languages'][language] = user_profile['languages'].get(language, 0) + 1
    
    return user_profile

def calculate_similarity_score(movie_row, profile):
    """Calculate similarity score using ML techniques"""
    score = 0
    
    # This is the recommendation algorithm!
    # We give different weights to different features based on importance
    
    # Genre match is most important (3x weight)
    # If they've searched for this genre before, they probably like it
    if movie_row['genre'] in profile['genres']:
        score += profile['genres'][movie_row['genre']] * 3
    
    # Decade preference matters but not as much (2x weight)
    if movie_row['decade_str'] in profile['decades']:
        score += profile['decades'][movie_row['decade_str']] * 2
    
    # Language preference also counts (2x weight)
    if movie_row['language'] in profile['languages']:
        score += profile['languages'][movie_row['language']] * 2
    
    # Higher rated movies get a small boost regardless (0.5x weight)
    # Everyone likes good movies!
    score += movie_row['rating'] * 0.5
    
    return score

def generate_recommendations(profile, limit=6):
    """Generate movie recommendations using collaborative filtering"""
    global movies_df
    
    # If the user hasn't searched for anything yet, just show them the best movies
    if not profile['genres']:
        top_movies = movies_df.nlargest(limit, 'rating')
    else:
        # Calculate how well each movie matches the user's preferences
        # This is content-based filtering in action!
        movies_df['similarity_score'] = movies_df.apply(
            lambda row: calculate_similarity_score(row, profile), axis=1
        )
        
        # Get the movies with the highest similarity scores
        top_movies = movies_df.nlargest(limit, 'similarity_score')
    
    # Return just the columns we need for the frontend
    return top_movies[['title', 'year', 'genre', 'rating', 'language', 'poster']].to_dict('records')

@app.route('/filters', methods=['GET'])
def get_filters():
    """Get available filter options"""
    global movies_df
    
    # Send back all the unique genres, decades, and languages
    # The frontend uses these to populate the dropdown menus
    genres = sorted(movies_df['genre'].unique().tolist())
    decades = sorted(movies_df['decade_str'].unique().tolist(), reverse=True)  # newest first
    languages = sorted(movies_df['language'].unique().tolist())
    
    return jsonify({
        'genres': genres,
        'decades': decades,
        'languages': languages
    })

@app.route('/search', methods=['POST'])
def search_movies():
    """Search movies based on filters"""
    global movies_df
    
    # Get the search criteria from the frontend
    data = request.json
    genre = data.get('genre')
    decade = data.get('decade')
    language = data.get('language')
    
    # Filter the dataset to match what they're looking for
    filtered = movies_df[
        (movies_df['genre'] == genre) &
        (movies_df['decade_str'] == decade) &
        (movies_df['language'] == language)
    ]
    
    # Sort by rating and grab the top 10
    top_movies = filtered.nlargest(10, 'rating')
    
    # Remember what they searched for - this helps us learn their preferences
    update_user_profile(genre, decade, language)
    
    # Convert to a format the frontend can easily work with
    movies_list = top_movies[['title', 'year', 'genre', 'rating', 'language', 'poster']].to_dict('records')
    
    return jsonify({
        'movies': movies_list,
        'count': len(movies_list)
    })

@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Get personalized recommendations"""
    global user_profile
    
    # Generate recommendations based on what the user has been searching for
    recommendations = generate_recommendations(user_profile)
    
    return jsonify({
        'movies': recommendations
    })

@app.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile"""
    global user_profile
    
    # Send back the user's preference data so the frontend can display it
    return jsonify(user_profile)

@app.route('/reset', methods=['POST'])
def reset_profile():
    """Reset user profile"""
    global user_profile
    
    # Clear everything - start fresh
    # Useful if someone wants to reset their recommendations
    user_profile = {
        'genres': {},
        'decades': {},
        'languages': {}
    }
    
    return jsonify({'message': 'Profile reset successfully'})

if __name__ == '__main__':
    # This runs when you start the server
    print("Loading movie dataset...")
    load_dataset()
    print("Starting Flask server...")
    # debug=True means the server will auto-reload when you change code
    app.run(debug=True, port=5000)