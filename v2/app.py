import os
import json
import math
import pandas as pd
import kagglehub
from flask import Flask, jsonify, request
from flask_cors import CORS
import requests
from functools import lru_cache

# Put your OMDB API key here - get it from omdbapi.com if you dont have one yet
OMDB_API_KEY = "YOUR_API_KEY_HERE"

app = Flask(__name__)
# CORS lets the frontend talk to backend without throwing a tantrum
CORS(app)

# --- Global stuff we need ---
DATASET_FILE = "imdb_top_1000.csv"
FALLBACK_POSTER = "https://via.placeholder.com/300x450?text=No+Poster"

# This tracks what the user likes - basically stalking their preferences lol
# In a real app you'd use a database but we're keeping it simple here
user_profile = {
    "searched_genres": {},   # like how many times they searched for Drama vs Action
    "searched_decades": {},  # are they into old movies or new stuff?
    "rating_history": []     # what ratings they usually look for
}

# --- Loading the movie data ---

def load_data():
    """
    Tries to download the dataset from Kaggle
    If that fails (usually does first time), we use backup data so app still works
    """
    df = None
    try:
        # kagglehub downloads stuff to a cache folder somewhere on your computer
        print("⬇️ Attempting to download dataset from Kaggle...")
        path = kagglehub.dataset_download("harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows")
        csv_path = os.path.join(path, DATASET_FILE)
        
        # The file could be anywhere in the folder so we gotta search for it
        # kinda annoying but whatever
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
        # Backup data - just some classic movies everyone knows
        # atleast the app wont crash if kaggle is being difficult
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

    # --- Cleaning up the messy data ---
    # Round ratings to .5 (cuz who needs 8.73 when 8.5 works fine)
    df['clean_rating'] = df['IMDB_Rating'].apply(lambda x: round(float(x) * 2) / 2)
    
    # Extract year and figure out what decade its from
    df['Released_Year'] = pd.to_numeric(df['Released_Year'], errors='coerce')
    df = df.dropna(subset=['Released_Year'])  # drop rows with weird years
    df['decade'] = df['Released_Year'].apply(lambda x: int(x // 10 * 10))
    
    # Remove spaces from genre names bcuz they mess things up later
    df['Genre'] = df['Genre'].astype(str).str.replace(' ', '')
    
    # Make sure theres a poster link, even if its just a placeholder
    if 'Poster_Link' not in df.columns:
        df['Poster_Link'] = FALLBACK_POSTER
    
    return df

# Load the data when server starts
movies_df = load_data()

# --- Helper functions that do the actual work ---

def update_user_profile(genres_list, decade, rating):
    """Keep track of what the user searches for so we can recommend stuff they actualy like"""
    # Count how many times they search each genre
    for g in genres_list:
        user_profile['searched_genres'][g] = user_profile['searched_genres'].get(g, 0) + 1
    
    # Remember what decades they prefer
    if decade:
        user_profile['searched_decades'][decade] = user_profile['searched_decades'].get(decade, 0) + 1
        
    # Keep track of rating preferences
    user_profile['rating_history'].append(float(rating))

def get_weighted_recommendations(df, limit=6):
    """
    The "AI" part - figures out what movies to recommend based on past searches
    Its not actually AI but it sounds cooler that way lol
    Formula: Score = (GenreMatch * 3) + (DecadeMatch * 2) + (RatingPref * 2) + (BaseBoost * 0.5)
    """
    # If user hasnt searched anything yet, just give them the highest rated stuff
    if not user_profile['searched_genres'] and not user_profile['searched_decades']:
        return df.sort_values(by='IMDB_Rating', ascending=False).head(limit).to_dict('records')

    # Figure out what the user actually likes
    sorted_genres = sorted(user_profile['searched_genres'].items(), key=lambda x: x[1], reverse=True)
    top_genres = [g[0] for g in sorted_genres[:3]]  # top 3 genres
    
    sorted_decades = sorted(user_profile['searched_decades'].items(), key=lambda x: x[1], reverse=True)
    top_decades = [d[0] for d in sorted_decades[:2]]  # top 2 decades
    
    # Average rating they usually search for
    avg_pref_rating = sum(user_profile['rating_history']) / len(user_profile['rating_history']) if user_profile['rating_history'] else 8.0

    # Calculate a score for each movie - higher score = better match
    def calculate_score(row):
        score = 0
        
        # Genre matching is most important (3x multiplier)
        movie_genres = row['Genre'].split(',')
        common_genres = set(movie_genres) & set(top_genres)
        score += len(common_genres) * 3
        
        # Decade matching matters too (2x multiplier)
        if row['decade'] in top_decades:
            score += 2
            
        # Prefer movies with ratings they usually search for (2x)
        if row['clean_rating'] >= avg_pref_rating:
            score += 2
            
        # Give a small boost to highly rated movies (0.5x)
        # because everyoen likes good movies right?
        score += (row['IMDB_Rating'] / 10.0) * 0.5
        
        return score

    # Apply scoring to all movies
    rec_df = df.copy()
    rec_df['score'] = rec_df.apply(calculate_score, axis=1)
    
    # Sort by score and return top results
    results = rec_df.sort_values(by=['score', 'IMDB_Rating'], ascending=[False, False]).head(limit)
    return results.to_dict('records')

# --- API endpoints - this is what the frontend calls ---

@lru_cache(maxsize=1000)  # Cache results so we dont spam the API
def get_high_quality_poster(title, year):
    """Grabs better posters from OMDB cuz the dataset ones are tiny and blurry"""
    try:
        # Clean up the title - remove quotes that break the API
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
    """Sends back all available genres, decades and ratings for the dropdowns"""
    # Get unique genres from the dataset
    unique_genres = set()
    for g_str in movies_df['Genre']:
        for g in str(g_str).split(','):
            if g:  # skip empty ones
                unique_genres.add(g)
            
    unique_decades = sorted(movies_df['decade'].unique().tolist())
    
    return jsonify({
        'genres': sorted(list(unique_genres)),
        'decades': unique_decades,
        'ratings': [round(x * 0.5, 1) for x in range(10, 21)]  # 5.0 to 10.0 in .5 steps
    })

@app.route('/search', methods=['POST'])
def search_movies():
    """Main search function - filters movies based on what user wants"""
    try:
        data = request.json
        print(f"📥 Received search request: {data}")
        
        genre = data.get('genre', '')
        decade = data.get('decade', '')
        min_rating = float(data.get('min_rating', 0))

        # Update the user profile with this search
        genre_list = [genre] if genre else []
        update_user_profile(genre_list, int(decade) if decade else None, min_rating)

        # Start filtering the movies
        filtered = movies_df.copy()
        
        if genre:
            # Check if movie has this genre
            filtered = filtered[filtered['Genre'].str.contains(genre, case=False, na=False)]
            print(f"After genre filter: {len(filtered)} movies")
        
        if decade:
            filtered = filtered[filtered['decade'] == int(decade)]
            print(f"After decade filter: {len(filtered)} movies")
        
        if min_rating > 0:
            filtered = filtered[filtered['clean_rating'] >= min_rating]
            print(f"After rating filter: {len(filtered)} movies")
            
        # Get top 10 by rating
        results = filtered.sort_values(by='IMDB_Rating', ascending=False).head(10)
        results_list = results.to_dict('records')
        
        # Try to get better quality posters
        cleaned_results = []
        for movie in results_list:
            cleaned_movie = {}
            for key, value in movie.items():
                # Replace NaN and weird values with empty strings so JSON doesnt break
                if pd.isna(value) or value is None:
                    cleaned_movie[key] = ""
                elif isinstance(value, float) and (math.isinf(value) or math.isnan(value)):
                    cleaned_movie[key] = ""
                else:
                    cleaned_movie[key] = value
            
            # Fetch high quality poster if we have an API key
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
    """Returns personalized recommendations based on user's search histroy"""
    try:
        recs = get_weighted_recommendations(movies_df)
        
        # Clean up the data same as search results
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
            
            # Get better posters for recommendations too
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
    """Returns the user's preference data"""
    return jsonify(user_profile)

@app.route('/reset', methods=['POST'])
def reset_profile():
    """Clears the user profile - usefull if they want to start over"""
    global user_profile
    user_profile = { "searched_genres": {}, "searched_decades": {}, "rating_history": [] }
    return jsonify({"message": "Profile reset"})

@app.route('/', methods=['GET'])
def home():
    return "<h1>Backend is running!</h1><p>Open 'index.html' to view the app.</p>"

if __name__ == '__main__':
    print("🎬 Movie Recommendation Backend Running on http://localhost:5001")
    app.run(debug=True, port=5001)