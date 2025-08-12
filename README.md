## Advent AI Services — Website

A single-page website for Advent AI training and consulting. The frontend uses Formspree for contact submissions by default; a minimal Python backend is included for self-hosted submissions persisted to SQLite.

### Features
- **Responsive UI**: Tailwind CSS via CDN
- **Smooth navigation** and **mobile menu toggle**
- **Contact form**: Progressive enhancement with inline validation, ARIA live regions, and a Retry button when network fails. Submits to Formspree by default (HTML form), and is enhanced to submit via the backend API when JavaScript is enabled.
- **Backend API**: Health check, submit contact, list contacts
- **SQLite persistence** with auto-migration (table created on first run)
- **Branding assets**: Favicon/app icons and header branding via `logo.png`

### Project Structure
- `index.html`: Main single-page site (hero, services, contact, footer)
- `thanks.html`: Thank-you page for successful contact submissions
- `logo.png`: Favicon, app icons, and header logo
- `CNAME`: Custom domain config for GitHub Pages
- `backend/`
  - `app.py`: Standalone HTTP server (Python stdlib) with CORS enabled
  - `contacts.db`: SQLite database file (auto-created)
  - `requirements.txt`: Legacy (Flask not used by current server)
  - `tests/test_backend.py`: Integration tests that exercise the running server
- `frontend/tests/test_frontend.py`: Optional E2E tests that assume backend (fetch) submission

### Tech Stack
- Frontend: HTML5, Tailwind CSS (CDN), Inter (Google Fonts), Vanilla JavaScript
- Backend: Python 3 standard library (`http.server`, `sqlite3`), CORS headers
- Database: SQLite (file `backend/contacts.db`)

## Code Overview & Documentation

- **Backend (`backend/app.py`)**
  - Module- and function-level docstrings describe endpoints, control flow, and database usage.
  - Key constants: `DB_PATH` (SQLite file), `HOST` (bind address), `PORT` (default `5000`).
  - `initialize_database()`: Creates the `contacts` table on first run.
  - `ContactRequestHandler`: Implements `GET /health`, `GET /api/contacts`, and `POST /api/contact`.
  - `main()`: Initializes the DB and starts a threaded HTTP server.
- **Frontend (`index.html`)**
  - Inline comments explain the page structure and the JavaScript that enhances the contact form with validation and accessible messaging.
  - The `fetch` call targets `https://adventaiservices.com/api/contact` by default. See below to point it at a local backend.
- **Tests**
  - Backend tests (`backend/tests/test_backend.py`) include docstrings and run the server automatically if needed.
  - Frontend Playwright tests (`frontend/tests/test_frontend.py`) mock the network and validate the UX behaviors.

## Run Locally

### Backend
1. Open a terminal and start the backend server:
   ```bash
   cd backend
   python3 app.py
   ```
   - Binds on `0.0.0.0:5000`
   - Creates `contacts.db` and table `contacts` if missing

### Frontend
- Option 1: Open directly
  - Open `index.html` in your browser.
- Option 2: Serve over a local HTTP server (recommended)
  ```bash
  python3 -m http.server 8000
  # open http://localhost:8000/
  ```

## Connect the Frontend Form to the Backend

By default, `index.html` posts to Formspree via a plain HTML form. With JavaScript enabled, the page intercepts submission and sends it to the backend (`/api/contact`), providing inline validation, accessible announcements, and a Retry button on failure.

If you want to wire a different backend URL, update the `fetch` call inside `index.html`. For local development against the included Python server, change the URL to:

```javascript
// index.html (inside submitPayload)
const response = await fetch('http://localhost:5000/api/contact', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(payload),
});
```

Remember to revert this to your production endpoint when deploying.

## API Reference (Backend)

- Base URL: `https://adventaiservices.com`
- CORS: `Access-Control-Allow-Origin: *`

### Health
- `GET /health` → `200 OK`
  ```json
  { "status": "ok" }
  ```

### Submit Contact
- `POST /api/contact` → `201 Created`
- Request headers: `Content-Type: application/json`
- Request body:
  ```json
  { "name": "Your Name", "email": "you@example.com", "message": "Hello" }
  ```
- Responses:
  - `201`: `{ "message": "Contact submitted successfully" }`
  - `400`: `{ "error": "All fields are required" }`
  - `400`: `{ "error": "Invalid JSON" }`

### List Contacts
- `GET /api/contacts` → `200 OK`
- Response body:
  ```json
  {
    "contacts": [
      {
        "id": 1,
        "name": "CI Tester",
        "email": "ci@example.com",
        "message": "Hello from tests ...",
        "created_at": "2025-01-01 12:34:56"
      }
    ]
  }
  ```

## Testing

Integration tests are in `backend/tests/test_backend.py`. They will start the server automatically if it is not already running.

From the project root:

```bash
python3 -m unittest discover -s backend/tests -v
```

## Front-end tests (Playwright - Python)

Prerequisites:
- Python 3.10+

Install and run:

```bash
pip install playwright
python -m playwright install chromium
python -m unittest discover -s frontend/tests -v
```

Note: These E2E tests assume the frontend uses the backend (fetch) submission flow. If you are using the default Formspree integration, switch to the backend flow as described above before running these tests.

This suite mocks calls to `https://adventaiservices.com/api/contact` to cover:
- Successful submission shows the success message
- Validation error displays server error text
- Network failure displays a fetch failure message

## Database
- File: `backend/contacts.db`