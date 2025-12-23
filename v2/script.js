// Backend runs on port 5001 - make sure its actualy running before complaining it doesnt work
const API_URL = "http://localhost:5001";

// --- Setup when page loads ---
document.addEventListener('DOMContentLoaded', () => {
    fetchFilters();           // load dropdown options
    fetchRecommendations();   // get initial movie suggestions
    fetchProfile();           // check if user has any search history
});

// --- Switching between pages ---
function showView(viewId) {
    // Hide everything first
    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
    // Show the page we want
    const target = document.getElementById(viewId + '-view');
    if (target) target.classList.add('active');
    
    // Update which nav button is highlighted
    document.querySelectorAll('.nav-links button').forEach(btn => btn.classList.remove('active-nav'));
    // This could probably be done better but it works so whatever
    if(viewId === 'home') document.querySelector("button[onclick=\"showView('home')\"]").classList.add('active-nav');
    if(viewId === 'search') document.querySelector("button[onclick=\"showView('search')\"]").classList.add('active-nav');
}

// --- Getting data from the backend ---

// Load the dropdown filter options
async function fetchFilters() {
    try {
        const res = await fetch(`${API_URL}/filters`);
        
        // Make sure server actually responded
        if (!res.ok) {
            throw new Error(`Server Error: ${res.status} ${res.statusText}`);
        }

        // Read the response as text first incase its not JSON
        const text = await res.text();
        
        // Try to parse as JSON
        try {
            const data = JSON.parse(text);
            
            // Populate the dropdowns with the data
            populateDropdown('genre-select', data.genres);
            populateDropdown('decade-select', data.decades);
            
            // Rating dropdown needs special formatting
            const ratingSel = document.getElementById('rating-select');
            ratingSel.innerHTML = '<option value="0">All Ratings</option>';
            data.ratings.forEach(r => {
                const opt = document.createElement('option');
                opt.value = r;
                opt.textContent = `${r}+ Stars`;
                ratingSel.appendChild(opt);
            });

        } catch (e) {
            console.error("Server returned non-JSON response:", text);
            throw new Error("Invalid JSON response from server");
        }

    } catch (err) {
        console.error("Failed to load filters:", err);
        // Show error message to user cuz connection failed
        document.querySelector('.hero p').textContent = 
            "⚠️ Error: Cannot connect to Backend. Is 'app.py' running on Port 5001?";
        document.querySelector('.hero p').style.color = "#ff6b6b";
    }
}

// Get personalized recommendations from the backend
async function fetchRecommendations() {
    const grid = document.getElementById('recommendations-grid');
    grid.innerHTML = '<div class="loading">Thinking... (Crunching numbers) 🧠</div>';
    
    try {
        const res = await fetch(`${API_URL}/recommendations`);
        const movies = await res.json();
        renderMovies(movies, grid);
    } catch (err) {
        grid.innerHTML = `<div class="loading">⚠️ Error loading recommendations. Is Backend running?</div>`;
    }
}

// Get the user's preference profile
async function fetchProfile() {
    try {
        const res = await fetch(`${API_URL}/profile`);
        const data = await res.json();
        
        // Only show the stats panel if they actualy searched for stuff
        const hasHistory = Object.keys(data.searched_genres).length > 0;
        const statsPanel = document.getElementById('user-stats');
        
        if (hasHistory) {
            statsPanel.style.display = 'block';
            
            // Figure out thier top genre
            const topGenre = Object.entries(data.searched_genres)
                .sort((a,b) => b[1] - a[1])[0][0];
            
            // And their favorite decade
            const topDecade = Object.entries(data.searched_decades)
                .sort((a,b) => b[1] - a[1])[0][0];
                
            document.getElementById('top-genres').textContent = topGenre;
            document.getElementById('top-decades').textContent = topDecade + "s";
        } else {
            statsPanel.style.display = 'none';
        }
    } catch (err) {
        console.log("No profile data yet");
    }
}

// Handle when user searches for movies
async function handleSearch(e) {
    e.preventDefault();
    const genre = document.getElementById('genre-select').value;
    const decade = document.getElementById('decade-select').value;
    const rating = document.getElementById('rating-select').value;
    
    console.log("🔍 Search params:", { genre, decade, rating });
    
    const payload = { genre, decade, min_rating: rating };
    
    // Switch to results view and show loading spinner
    showView('results');
    const grid = document.getElementById('results-grid');
    grid.innerHTML = '<div class="loading">🔍 Searching database...</div>';
    
    try {
        const res = await fetch(`${API_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        const movies = await res.json();
        console.log("📦 Received movies:", movies);
        console.log("📊 Number of movies:", movies.length);
        
        // Check if we actualy got results
        if (!movies || movies.length === 0) {
            grid.innerHTML = '<div class="loading">No movies found matching criteria. Try different filters! 🤷‍♂️</div>';
            return;
        }
        
        renderMovies(movies, grid);
        
        // Refresh the profile and recommendations in background
        fetchProfile(); 
        fetchRecommendations();
    } catch (err) {
        console.error("❌ Search error:", err);
        grid.innerHTML = '<div class="loading">❌ Search failed: ' + err.message + '</div>';
    }
}

// Reset the user's profile
async function resetProfile() {
    if(confirm("Clear your taste profile? This resets recommendations.")) {
        await fetch(`${API_URL}/reset`, { method: 'POST' });
        location.reload();  // just reload the page, easiest way
    }
}

// --- Display the movie cards ---
function renderMovies(movies, container) {
    container.innerHTML = '';
    
    if (movies.length === 0) {
        container.innerHTML = '<div class="loading">No movies found matching criteria. 🤷‍♂️</div>';
        return;
    }
    
    movies.forEach(movie => {
        // Create a card for each movie
        const card = document.createElement('div');
        card.className = 'movie-card';
        card.innerHTML = `
            <div class="poster-wrapper">
                <img src="${movie.Poster_Link}" alt="${movie.Series_Title}" onerror="this.src='https://via.placeholder.com/300x450?text=No+Image'">
            </div>
            <div class="card-info">
                <div class="card-header">
                    <h3 class="movie-title">${movie.Series_Title}</h3>
                    <span class="rating">☆ ${movie.IMDB_Rating}</span>
                </div>
                <div class="meta">
                    <span>${movie.Released_Year}</span>
                    <span>${movie.Runtime || ''}</span>
                </div>
                <div class="genre-tag">${movie.Genre.split(',')[0]}</div>
            </div>
        `;
        container.appendChild(card);
    });
}

// Helper function to populate dropdowns
function populateDropdown(id, items) {
    const sel = document.getElementById(id);
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item;
        sel.appendChild(opt);
    });
}