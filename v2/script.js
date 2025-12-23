// Change port from 5000 to 5001 to match backend
const API_URL = "http://localhost:5001";

// --- Initialization ---
document.addEventListener('DOMContentLoaded', () => {
    fetchFilters();
    fetchRecommendations();
    fetchProfile();
});

// --- Navigation Logic ---
function showView(viewId) {
    // Hide all views
    document.querySelectorAll('.view').forEach(el => el.classList.remove('active'));
    // Show requested view
    const target = document.getElementById(viewId + '-view');
    if (target) target.classList.add('active');
    
    // Update Nav State
    document.querySelectorAll('.nav-links button').forEach(btn => btn.classList.remove('active-nav'));
    // (Simple logic to highlight home/search buttons based on viewId)
    if(viewId === 'home') document.querySelector("button[onclick=\"showView('home')\"]").classList.add('active-nav');
    if(viewId === 'search') document.querySelector("button[onclick=\"showView('search')\"]").classList.add('active-nav');
}

// --- Data Fetching Functions ---

// 1. Fetch Filters for Dropdowns
async function fetchFilters() {
    try {
        const res = await fetch(`${API_URL}/filters`);
        
        // 1. Check if the server responded with OK (200)
        if (!res.ok) {
            throw new Error(`Server Error: ${res.status} ${res.statusText}`);
        }

        // 2. Read text first to debug if it's not JSON
        const text = await res.text();
        
        // 3. Try to parse it
        try {
            const data = JSON.parse(text);
            
            // If success, proceed as normal
            populateDropdown('genre-select', data.genres);
            populateDropdown('decade-select', data.decades);
            
            const ratingSel = document.getElementById('rating-select');
            ratingSel.innerHTML = '<option value="0">All Ratings</option>'; // Clear previous
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
        // Show a visual warning to the user
        document.querySelector('.hero p').textContent = 
            "⚠️ Error: Cannot connect to Backend. Is 'app.py' running on Port 5001?";
        document.querySelector('.hero p').style.color = "#ff6b6b";
    }
}

// 2. Fetch Personalized Recommendations
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

// 3. Fetch User Profile Stats
async function fetchProfile() {
    try {
        const res = await fetch(`${API_URL}/profile`);
        const data = await res.json();
        
        // Only show stats panel if user has history
        const hasHistory = Object.keys(data.searched_genres).length > 0;
        const statsPanel = document.getElementById('user-stats');
        
        if (hasHistory) {
            statsPanel.style.display = 'block';
            
            // Get top genre
            const topGenre = Object.entries(data.searched_genres)
                .sort((a,b) => b[1] - a[1])[0][0];
            
            // Get top decade
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

// 4. Handle Search
async function handleSearch(e) {
    e.preventDefault();
    const genre = document.getElementById('genre-select').value;
    const decade = document.getElementById('decade-select').value;
    const rating = document.getElementById('rating-select').value;
    
    console.log("🔍 Search params:", { genre, decade, rating }); // Debug log
    
    const payload = { genre, decade, min_rating: rating };
    
    // Switch to results view and show loading
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
        console.log("📦 Received movies:", movies); // Debug log
        console.log("📊 Number of movies:", movies.length); // Debug log
        
        if (!movies || movies.length === 0) {
            grid.innerHTML = '<div class="loading">No movies found matching criteria. Try different filters! 🤷‍♂️</div>';
            return;
        }
        
        renderMovies(movies, grid);
        
        // Refresh profile stats in background since search updates history
        fetchProfile(); 
        // Refresh home recommendations for next time
        fetchRecommendations();
    } catch (err) {
        console.error("❌ Search error:", err);
        grid.innerHTML = '<div class="loading">❌ Search failed: ' + err.message + '</div>';
    }
}

// 5. Reset Profile
async function resetProfile() {
    if(confirm("Clear your taste profile? This resets recommendations.")) {
        await fetch(`${API_URL}/reset`, { method: 'POST' });
        location.reload();
    }
}

// --- Helper: Render Cards ---
function renderMovies(movies, container) {
    container.innerHTML = '';
    
    if (movies.length === 0) {
        container.innerHTML = '<div class="loading">No movies found matching criteria. 🤷‍♂️</div>';
        return;
    }
    
    movies.forEach(movie => {
        // Create movie card with poster and info
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

function populateDropdown(id, items) {
    const sel = document.getElementById(id);
    items.forEach(item => {
        const opt = document.createElement('option');
        opt.value = item;
        opt.textContent = item;
        sel.appendChild(opt);
    });
}