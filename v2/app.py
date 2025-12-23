import os
import json
import math
import pandas as pd
import kagglehub
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from functools import lru_cache

# Add your OMDB API key here
OMDB_API_KEY = "faeba269"  # Replace with your actual key

app = Flask(__name__)
# Enable Cross-Origin Resource Sharing so our separate frontend can talk to this API
CORS(app)

# --- Global Constants & State ---
DATASET_FILE = "imdb_top_1000.csv"
FALLBACK_POSTER = "https://via.placeholder.com/300x450?text=No+Poster"

# In-memory user profile to track preferences for the ML algorithm
# In a real app, this would be a database model linked to a User ID
user_profile = {
    "searched_genres": {},   # Frequency map: {'Drama': 5, 'Action': 2}
    "searched_decades": {},  # Frequency map: {1990: 3}
    "rating_history": []     # List of minimum ratings user has searched for
}

# --- Data Loading & Processing ---

def load_data():
    """
    Attempts to download data from Kaggle. 
    If it fails (auth issues/connection), loads a robust fallback sample.
    """
    df = None
    try:
        # helpful comment: kagglehub downloads to a specific cache directory
        print("⬇️ Attempting to download dataset from Kaggle...")
        path = kagglehub.dataset_download("harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows")
        csv_path = os.path.join(path, DATASET_FILE)
        
        # Check if file exists inside the downloaded path
        # Note: The actual filename in the dataset might vary, we search for the .csv
        for root, dirs, files in os.walk(path):
            for file in files:
                if file.endswith(".csv"):
                    df = pd.read_csv(os.path.join(root, file))
                    break
        
        if df is None:
            raise FileNotFoundError("CSV not found in downloaded path.")
            
        print("✅ Kaggle dataset loaded successfully.")

    except Exception as e:
        print(f"⚠️ Kaggle load failed ({str(e)}). Using fallback data.")
        # Fallback data so the app always works
        data = {
            'Series_Title': ['The Shawshank Redemption', 'The Godfather', 'The Dark Knight', 'Pulp Fiction', 'Forrest Gump', 'Inception', 'Matrix', 'Interstellar', 'Parasite', 'Spirited Away'],
            'Released_Year': [1994, 1972, 2008, 1994, 1994, 2010, 1999, 2014, 2019, 2001],
            'Genre': ['Drama', 'Crime,Drama', 'Action,Crime,Drama', 'Crime,Drama', 'Drama,Romance', 'Action,Adventure,Sci-Fi', 'Action,Sci-Fi', 'Adventure,Drama,Sci-Fi', 'Comedy,Drama,Thriller', 'Animation,Adventure,Family'],
            'IMDB_Rating': [9.3, 9.2, 9.0, 8.9, 8.8, 8.8, 8.7, 8.6, 8.6, 8.6],
            'Poster_Link': [
                'https://m.media-amazon.com/images/M/MV5BMDFkYTc0MGEtZmNhMC00ZDIzLWFmNTEtODM1ZmRlYWMwMWFmXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BM2MyNjYxNmUtYTAwNi00MTYxLWJmNWYtYzZlODY3ZTk3OTFlXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BMTMxNTMwODM0NF5BMl5BanBnXkFtZTcwODAyMTk2Mw@@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BNGNhMDIzZTUtNTBlZi00MTRlLWFjM2ItYzViMjE3YzI5MjljXkEyXkFqcGdeQXVyNzkwMjQ5NzM@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BNWIwODRlZTUtY2U3ZS00Yzg1LWJhNzYtMmZiYmEyNmU1NjMzXkEyXkFqcGdeQXVyMTQxNzMzNDI@._V1_UY98_CR1,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BMjAxMzY3NjcxNF5BMl5BanBnXkFtZTcwNTI5OTM0Mw@@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BNzQzOTk3OTAtNDQ0Zi00ZTVkLWI0MTEtMDllZjNkYzNjNTc4L2ltYWdlXkEyXkFqcGdeQXVyNjU0OTQ0OTY@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BZjdkOTU3MDktN2IxOS00OGEyLWFmMjktY2FiMmZkNWIyODZiXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BYWZjMjk3ZTItODQ2ZC00NTY5LWE0ZDYtZTI3MjcwN2Q5NTVkXkEyXkFqcGdeQXVyODk4OTc3MTY@._V1_UX67_CR0,0,67,98_AL_.jpg',
                'https://m.media-amazon.com/images/M/MV5BMjlmZmI5MDctNDE2YS00YWE0LWE5ZWItZDBhYWQ0NTcxNWRhXkEyXkFqcGdeQXVyMTMxODk2OTU@._V1_UX67_CR0,0,67,98_AL_.jpg'
            ]
        }
        df = pd.DataFrame(data)

    # --- Data Cleaning ---
    # 1. Round Ratings: Round to nearest 0.5 (e.g., 8.3 -> 8.5)
    df['clean_rating'] = df['IMDB_Rating'].apply(lambda x: round(float(x) * 2) / 2)
    
    # 2. Extract Year and Calculate Decade
    df['Released_Year'] = pd.to_numeric(df['Released_Year'], errors='coerce')
    df = df.dropna(subset=['Released_Year'])
    df['decade'] = df['Released_Year'].apply(lambda x: int(x // 10 * 10))
    
    # 3. Clean Genres - remove spaces after commas
    df['Genre'] = df['Genre'].astype(str).str.replace(' ', '')
    
    # 4. Ensure Poster Link exists
    if 'Poster_Link' not in df.columns:
        df['Poster_Link'] = FALLBACK_POSTER
    
    return df

# Initialize Data
movies_df = load_data()

# --- Helper Functions ---

def update_user_profile(genres_list, decade, rating):
    """Updates the global user profile based on search terms."""
    # Update Genres
    for g in genres_list:
        user_profile['searched_genres'][g] = user_profile['searched_genres'].get(g, 0) + 1
    
    # Update Decade
    if decade:
        user_profile['searched_decades'][decade] = user_profile['searched_decades'].get(decade, 0) + 1
        
    # Update Rating preference
    user_profile['rating_history'].append(float(rating))

def get_weighted_recommendations(df, limit=6):
    """
    ML Algorithm: Content-Based Filtering with Weighted Scoring
    Formula: Score = (GenreMatch * 3) + (DecadeMatch * 2) + (RatingPref * 2) + (BaseBoost * 0.5)
    """
    # If profile is empty, return top rated movies
    if not user_profile['searched_genres'] and not user_profile['searched_decades']:
        return df.sort_values(by='IMDB_Rating', ascending=False).head(limit).to_dict('records')

    # 1. Determine User Preferences
    sorted_genres = sorted(user_profile['searched_genres'].items(), key=lambda x: x[1], reverse=True)
    top_genres = [g[0] for g in sorted_genres[:3]]
    
    sorted_decades = sorted(user_profile['searched_decades'].items(), key=lambda x: x[1], reverse=True)
    top_decades = [d[0] for d in sorted_decades[:2]]
    
    avg_pref_rating = sum(user_profile['rating_history']) / len(user_profile['rating_history']) if user_profile['rating_history'] else 8.0

    # 2. Calculate Score for every movie
    def calculate_score(row):
        score = 0
        
        # Genre Match (Weight: 3x)
        movie_genres = row['Genre'].split(',')
        common_genres = set(movie_genres) & set(top_genres)
        score += len(common_genres) * 3
        
        # Decade Match (Weight: 2x)
        if row['decade'] in top_decades:
            score += 2
            
        # Rating Preference Match (Weight: 2x)
        if row['clean_rating'] >= avg_pref_rating:
            score += 2
            
        # Base Rating Boost (Weight: 0.5x)
        score += (row['IMDB_Rating'] / 10.0) * 0.5
        
        return score

    rec_df = df.copy()
    rec_df['score'] = rec_df.apply(calculate_score, axis=1)
    
    results = rec_df.sort_values(by=['score', 'IMDB_Rating'], ascending=[False, False]).head(limit)
    return results.to_dict('records')

# --- API Endpoints ---

@lru_cache(maxsize=1000)  # Cache results to avoid repeated API calls
def get_high_quality_poster(title, year):
    """Fetch high-quality poster from OMDB API."""
    try:
        # Clean the title - remove special characters that might break the API call
        clean_title = title.replace("'", "").replace('"', '')
        
        url = f"http://www.omdbapi.com/?t={clean_title}&y={int(year)}&apikey={OMDB_API_KEY}"
        response = requests.get(url, timeout=3)
        data = response.json()
        
        if data.get('Response') == 'True' and data.get('Poster') != 'N/A':
            return data['Poster']
        return None
    except Exception as e:
        print(f"⚠️ Could not fetch poster for {title}: {str(e)}")
        return None

@app.route('/filters', methods=['GET'])
def get_filters():
    """Returns available genres, decades and rating steps for dropdowns."""
    unique_genres = set()
    for g_str in movies_df['Genre']:
        for g in str(g_str).split(','):
            if g:  # Skip empty strings
                unique_genres.add(g)
            
    unique_decades = sorted(movies_df['decade'].unique().tolist())
    
    return jsonify({
        'genres': sorted(list(unique_genres)),
        'decades': unique_decades,
        'ratings': [round(x * 0.5, 1) for x in range(10, 21)]
    })

@app.route('/search', methods=['POST'])
def search_movies():
    """Filters movies and updates user profile."""
    try:
        data = request.json
        print(f"📥 Received search request: {data}")
        
        genre = data.get('genre', '')
        decade = data.get('decade', '')
        min_rating = float(data.get('min_rating', 0))

        genre_list = [genre] if genre else []
        update_user_profile(genre_list, int(decade) if decade else None, min_rating)

        filtered = movies_df.copy()
        
        if genre:
            filtered = filtered[filtered['Genre'].str.contains(genre, case=False, na=False)]
            print(f"After genre filter: {len(filtered)} movies")
        
        if decade:
            filtered = filtered[filtered['decade'] == int(decade)]
            print(f"After decade filter: {len(filtered)} movies")
        
        if min_rating > 0:
            filtered = filtered[filtered['clean_rating'] >= min_rating]
            print(f"After rating filter: {len(filtered)} movies")
            
        results = filtered.sort_values(by='IMDB_Rating', ascending=False).head(10)
        results_list = results.to_dict('records')
        
        # Enhance with high-quality posters
        cleaned_results = []
        for movie in results_list:
            cleaned_movie = {}
            for key, value in movie.items():
                if pd.isna(value) or value is None:
                    cleaned_movie[key] = ""
                elif isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
                    cleaned_movie[key] = ""
                else:
                    cleaned_movie[key] = value
            
            # Try to get high-quality poster
            if OMDB_API_KEY != "YOUR_API_KEY_HERE":
                hq_poster = get_high_quality_poster(
                    cleaned_movie.get('Series_Title', ''),
                    cleaned_movie.get('Released_Year', 2000)
                )
                if hq_poster:
                    cleaned_movie['Poster_Link'] = hq_poster
                    print(f"✅ Got HQ poster for {cleaned_movie.get('Series_Title')}")
            
            cleaned_results.append(cleaned_movie)
        
        print(f"✅ Returning {len(cleaned_results)} movies")
        return jsonify(cleaned_results)
        
    except Exception as e:
        print(f"❌ Error in search: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

@app.route('/recommendations', methods=['GET'])
def get_recommendations():
    """Returns personalized recommendations."""
    try:
        recs = get_weighted_recommendations(movies_df)
        
        cleaned_recs = []
        for movie in recs:
            cleaned_movie = {}
            for key, value in movie.items():
                if pd.isna(value) or value is None:
                    cleaned_movie[key] = ""
                elif isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
                    cleaned_movie[key] = ""
                else:
                    cleaned_movie[key] = value
            
            # Try to get high-quality poster
            if OMDB_API_KEY != "YOUR_API_KEY_HERE":
                hq_poster = get_high_quality_poster(
                    cleaned_movie.get('Series_Title', ''),
                    cleaned_movie.get('Released_Year', 2000)
                )
                if hq_poster:
                    cleaned_movie['Poster_Link'] = hq_poster
            
            cleaned_recs.append(cleaned_movie)
        
        return jsonify(cleaned_recs)
    except Exception as e:
        print(f"❌ Error in recommendations: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify([])

@app.route('/profile', methods=['GET'])
def get_profile():
    """Returns the raw user profile data."""
    return jsonify(user_profile)

@app.route('/reset', methods=['POST'])
def reset_profile():
    """Resets the ML tracking."""
    global user_profile
    user_profile = { "searched_genres": {}, "searched_decades": {}, "rating_history": [] }
    return jsonify({"message": "Profile reset"})

@app.route('/', methods=['GET'])
def home():
    return "<h1>Backend is running!</h1><p>Open 'index.html' to view the app.</p>"

if __name__ == '__main__':
    print("🎬 Movie Recommendation Backend Running on http://localhost:5001")
    app.run(debug=True, port=5001)
