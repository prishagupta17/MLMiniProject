# The Forgetting Engine — setup

Two independent apps in this folder:
- `backend/`  — Python (FastAPI) + the ML model
- `frontend/` — React (Vite)

You run both at the same time, in two separate terminal windows, while working on this.

---

## 0. One-time installs (skip anything you already have)

- **Python 3.10+** — https://www.python.org/downloads/ (on install, tick "Add Python to PATH")
- **Node.js 18+** — https://nodejs.org (installs `node` and `npm` together)
- **A code editor** — VS Code is not required, but it's the easiest option for a beginner:
  https://code.visualstudio.com — install it, then File → Open Folder → pick this project folder.
  Its built-in terminal (Terminal → New Terminal) is where you'll run the commands below.

---

## 1. Backend setup (run once)

Open a terminal in the `backend/` folder, then:

```
python -m venv venv
```
This creates a private Python environment just for this project (so its packages don't clash with anything else on your machine).

Activate it:
- Mac/Linux: `source venv/bin/activate`
- Windows: `venv\Scripts\activate`

You'll know it worked because your terminal prompt will now show `(venv)` at the start.

Install everything the backend needs:
```
pip install -r requirements.txt
```

Run test suite:
```
pytest tests/ -v
```

Train the model (also auto-generates a synthetic bootstrap dataset the first time):
```
python -m app.train
```

**(Optional) Run the simulation manually** to regenerate or inspect simulated student histories:
```
python - << 'EOF'
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.app.models import Base
from backend.app.seed_loader import load_all_seeds
from backend.app.synthetic_data import simulate_students, SimulationConfig

engine = create_engine("sqlite:///forgetting_engine.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
db = Session()
load_all_seeds(db)
simulate_students(db, SimulationConfig(n_students=30, random_seed=42))
print("Done.")
EOF
```

> **Note**: Simulated data is flagged `is_simulated=True`. It does not represent real students and must not be cited as accuracy evidence.

**(Optional) Add your API key** — only needed for real LLM-based topic enrichment:
1. Copy `.env.example` to a new file named `.env` (same folder)
2. Open `.env`, replace the placeholder with your real key
Skip this for now — the app works without it, just with a rougher fallback.

Run the server:
```
uvicorn app.main:app --reload
```
Leave this terminal running. It's serving at `http://localhost:8000`.

---

## 2. Frontend setup (run once)

Open a **second** terminal, in the `frontend/` folder:

```
npm install
npm run dev
```
Leave this running too. It'll print a URL — usually `http://localhost:5173` — open that in your browser.

---

## 3. Day-to-day (after the first setup)

Every time you come back to work on this:
1. Terminal 1 → `backend/` → `source venv/bin/activate` (or the Windows line) → `uvicorn app.main:app --reload`
2. Terminal 2 → `frontend/` → `npm run dev`
3. Open the printed localhost URL in your browser

You do **not** need to redo the `pip install` / `npm install` / `python -m venv` steps again — those are one-time.

---

## Folder map

```
backend/
  app/
    models.py           — database schema
    synthetic_data.py   — bootstrap dataset generator
    features.py          — feature engineering
    train.py             — trains + saves the ML model
    predict.py            — live prediction for a user/topic
    explainability.py     — local, topic-specific prediction explanations
    topic_enrichment.py  — LLM difficulty + confusable-topics note
    difficulty_refine.py — crowd-sourced difficulty blending
    main.py               — the API itself
  requirements.txt
  .env.example            — copy to .env and add your key when ready

frontend/
  src/
    App.jsx               — app shell + navigation
    components/            — Landing, Dashboard, Study, Self-check, Manage
    api.js                 — talks to the backend
```
