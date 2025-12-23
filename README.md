# CineMatch AI - Movie Recomendation System

A machine learning powered movie recommendation app that learns your taste and suggests stuff you'll actualy want to watch (hopefully).

## What it does

- Gives you personalized movie recomendations using some fancy ML algorithms
- Search movies by genre, decade, and minimum IMDB rating
- Tracks what you like and gets better over time (kinda creepy but usefull)
- High quality movie posters cuz those tiny blurry ones are annoying
- Modern UI that doesnt look like it was made in 2005
- Updates recomendations in real-time as you search

## Tech stuff

**Backend (the boring part):**
- Python 3.x
- Flask for the API
- Pandas for data wrangling
- scikit-learn for the "AI" (its not really AI but sounds cooler)
- Kaggle Hub to download movie data

**Frontend (the pretty part):**
- HTML5
- CSS3 with that glassmorphism effect everyone loves
- Vanilla JavaScript cuz we dont need React for everything
- Fetch API for talking to backend

## How to get it running

### What you need first

- Python 3.7 or newer (check with `python --version`)
- pip (should come with Python)
- OMDB API key - get one free at https://www.omdbapi.com/apikey.aspx (takes like 2 minutes)

### Actualy setting it up

1. Clone this thing
```bash
git clone https://github.com/yourusername/cinematch-ai.git
cd cinematch-ai
```

2. Install the Python packages
```bash
pip install flask flask-cors pandas numpy scikit-learn kagglehub requests
```

If that doesnt work try `pip3` instead of `pip`

3. Add your OMDB API key

Open `app.py` and find this line:
```python
OMDB_API_KEY = "faeba269"
```
Replace that with your actual key from OMDB

4. Start the backend
```bash
python app.py
```

You should see something like "Movie Recommendation Backend Running on http://localhost:5001"

5. Open the frontend

Just double-click `index.html` or right-click and open with your browser. Or if you want to be fancy:
```bash
python -m http.server 8000
```
Then go to http://localhost:8000

## How to use it

### Home Page
- See movie recomendations based on what you searched before
- Check your "taste profile" (what genres and decades you search for most)

### Search
- Pick a genre, decade, and minimum rating
- Get the top 10 movies that match
- Each search helps the app learn what you like

### Reset Profile
- Clears your search history and starts fresh
- Usefull if you let your friend use it and now all the recomendations are weird

## Folder structure
```
cinematch-ai/
│
├── app.py              # Backend server
├── index.html          # Main page
├── style.css           # Makes it look pretty
├── script.js           # Frontend logic
└── README.md           # You are here
```

## The "AI" explained

The recomendation system uses weighted content-based filtering (fancy words for matching stuff you searched before):

- Genre Match: 3x weight (most important)
- Decade Match: 2x weight
- Rating Preference: 2x weight  
- Base Rating Boost: 0.5x weight (everyone likes good movies)

It learns from your searches and gets better at recommending stuff over time.

## API endpoints (for nerds)

### GET /filters
Gets available genres, decades, and ratings for dropdowns

### POST /search
Search for movies
```json
{
  "genre": "Drama",
  "decade": "1990",
  "min_rating": 8.0
}
```

### GET /recommendations
Get personalized recomendations based on search history

### GET /profile
See what the system knows about your preferences

### POST /reset
Clear everything and start over

## About the data

Uses IMDB Top 1000 Movies from Kaggle:
https://www.kaggle.com/datasets/harshitshankhdhar/imdb-dataset-of-top-1000-movies-and-tv-shows

If Kaggle download fails it uses backup data so app still works.

## Changing stuff

### Use a different port

In `app.py`:
```python
app.run(debug=True, port=5001)  # change this number
```

In `script.js`:
```javascript
const API_URL = "http://localhost:5001";  # match the port
```

### Turn off high quality posters

If you dont have an OMDB key or hit the rate limit, just leave it blank:
```python
OMDB_API_KEY = ""
``