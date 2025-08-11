## Advent AI Services — Website

A single-page website for Advent AI training and consulting, now with a minimal Python backend for contact submissions persisted to SQLite.

### Features
- **Responsive UI**: Tailwind CSS via CDN
- **Smooth navigation** and **mobile menu toggle**
- **Contact form**: Currently simulates submission on the frontend; a production-ready backend is available under `backend/`
- **Backend API**: Health check, submit contact, list contacts
- **SQLite persistence** with auto-migration (table created on first run)

### Project Structure
- `frontend/index.html`: Main single-page site (hero, services, contact, footer)
- `CNAME`: Custom domain config for GitHub Pages
- `backend/`
  - `app.py`: Standalone HTTP server (Python stdlib) with CORS enabled
  - `contacts.db`: SQLite database file (auto-created)
  - `requirements.txt`: Legacy (Flask not used by current server)
  - `tests/test_backend.py`: Integration tests that exercise the running server

### Tech Stack
- Frontend: HTML5, Tailwind CSS (CDN), Inter (Google Fonts), Vanilla JavaScript
- Backend: Python 3 standard library (`http.server`, `sqlite3`), CORS headers
- Database: SQLite (file `backend/contacts.db`)

## Run Locally

### Backend
1. Open a terminal and start the backend server:
   ```bash
   cd Website/backend
   python3 app.py
   ```
   - Binds on `0.0.0.0:5000`
   - Creates `contacts.db` and table `contacts` if missing

### Frontend
- Option 1: Open directly
  - Open `Website/frontend/index.html` in your browser.
- Option 2: Serve over a local HTTP server (recommended)
  ```bash
  cd Website
  python3 -m http.server 8000
  # open http://localhost:8000/frontend/
  ```

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

## Connect the Frontend Form to the Backend

The current `frontend/index.html` simulates submission using `setTimeout`. To use the backend, replace the simulation with a `fetch` call:

```html
<script>
// ... keep existing setup code
contactForm.addEventListener('submit', async function(e) {
  e.preventDefault();
  submitText.classList.add('hidden');
  loadingSpinner.classList.remove('hidden');
  successMessage.classList.add('hidden');
  errorMessage.classList.add('hidden');
  submitButton.disabled = true;

  try {
    const payload = {
      name: document.getElementById('name').value.trim(),
      email: document.getElementById('email').value.trim(),
      message: document.getElementById('message').value.trim()
    };
    const resp = await fetch('https://adventaiservices.com/api/contact', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });
    if (resp.ok) {
      successMessage.classList.remove('hidden');
      contactForm.reset();
    } else {
      const body = await resp.json().catch(() => ({}));
      errorMessage.textContent = body.error || 'Submission failed';
      errorMessage.classList.remove('hidden');
    }
  } catch (err) {
    errorMessage.textContent = 'Network error';
    errorMessage.classList.remove('hidden');
  } finally {
    submitText.classList.remove('hidden');
    loadingSpinner.classList.add('hidden');
    submitButton.disabled = false;
  }
});
</script>
```

## Testing

Integration tests are in `backend/tests/test_backend.py`. They will start the server automatically if it is not already running.

From the project root (`Website/`):

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

This suite mocks calls to `https://adventaiservices.com/api/contact` to cover:
- Successful submission shows the success message
- Validation error displays server error text
- Network failure displays a fetch failure message

## Database
- File: `backend/contacts.db`