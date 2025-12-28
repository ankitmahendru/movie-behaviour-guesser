# 🎥 Movie Behaviour Guesser

---

> *Because deep down, we all know the protagonist won't die in the first ten minutes, no matter how many explosions occur.*

<div align="center">

</div>

---

## 🧐 What is this?

**Movie Behaviour Guesser** is a specialized tool designed to analyze film scenarios and predict what happens next. Whether it's a horror movie character deciding to investigate a strange noise in the basement or a rom-com lead running through an airport, this engine uses a backend of "cinematic logic" to guess the outcome.

It serves as a playground for testing how predictable (or occasionally subversive) modern storytelling can be when processed through a structured behavioral engine.

---

## ✨ Key Features

* **Character Logic Parsing**: Analyzes character archetypes to determine their most likely (and often most foolish) next move.
* **Dual-Version Architecture**:
* **V1**: A streamlined Python backend paired with a functional HTML frontend for core logic testing.
* **V2**: An enhanced interactive experience with a polished UI, dedicated styling, and modular JavaScript.


* **Trope Awareness**: Recognizes standard movie patterns to provide "educated" guesses on plot twists.
* **Interactive Web Interface**: Simple, browser-based controls to input scenarios and receive behavioral predictions instantly.

---

## 📂 Project Structure

Behold the evolution of a character's bad decisions:

```bash
movie-behaviour-guesser/
├── v1/                      # The "Original Cut" (Core Logic)
│   ├── movie_backend.py     # Python logic for behavioral guessing
│   └── frontend.html        # Simple interface for V1
├── v2/                      # The "Special Edition" (Enhanced UI)
│   ├── app.py               # Flask-based backend server
│   ├── index.html           # Structured modern frontend
│   ├── script.js            # Interactive UI logic
│   └── style.css            # Custom cinematic styling
└── README.md                # This script.

```

---

## 🛠 Tech Stack

| Component | Technology | Why? |
| --- | --- | --- |
| **Logic Engine** | Python | For processing complex "if-they-do-this-they-die" logic. |
| **Web Server** | Flask | To bridge the gap between Python scripts and your browser. |
| **Frontend** | HTML5 / CSS3 | Making predictable outcomes look aesthetically pleasing. |
| **Interactivity** | JavaScript | For real-time updates without refreshing the page. |

---

## 💿 Installation & Setup

Ready to start judging fictional characters? Choose your version:

### 1. Clone the Repo

```bash
git clone https://github.com/ankitmahendru/movie-behaviour-guesser.git
cd movie-behaviour-guesser

```

### 2. Run Version 2 (Recommended)

```bash
cd v2
python app.py

```

*Open your browser and navigate to the local host address provided in the terminal.*

---

## 🎮 How to Use

1. **Enter a Scenario**: Type in a classic movie setup (e.g., "The group decides to split up in the haunted woods").
2. **Analyze**: Let the backend process the sheer level of trope-cliché involved.
3. **The Result**: Receive a prediction of the character's behavior and their likely survival rate.

---

## 🤝 Contribution Guide

Think you've found a trope I missed? Or maybe you have a better survival algorithm for the "final girl"?

1. **Fork it.**
2. **Branch it** (`git checkout -b feature/new-trope`).
3. **Commit it** (Keep the humor intact).
4. **Push it.**
5. **PR it.**

---

<div align="center">

**Made with love (and too many movie marathons) by PadhoAI** ❤️

</div>
