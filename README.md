## Advent AI Services — Website

A single-page website for Advent AI training and consulting, now with a minimal Python backend for contact submissions persisted to SQLite.

### Features
- **Responsive UI**: Tailwind CSS via CDN
- **Smooth navigation** and **mobile menu toggle**
- **Contact form**: Currently simulates submission on the frontend; a production-ready backend is available under `backend/`
- **Backend API**: Health check, submit contact, list contacts
- **SQLite persistence** with auto-migration (table created on first run)

### Project Structure
- `index.html`: Main single-page site (hero, services, contact, footer)
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
  - Open `Website/index.html` in your browser.
- Option 2: Serve over a local HTTP server (recommended)
  ```bash
  cd Website
  python3 -m http.server 8000
  # open http://localhost:8000
  ```

## API Reference (Backend)

- Base URL: `http://localhost:5000`
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

The current `index.html` simulates submission using `setTimeout`. To use the backend, replace the simulation with a `fetch` call:

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
    const resp = await fetch('http://localhost:5000/api/contact', {
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

## Database
- File: `backend/contacts.db`
- Lifecycle: auto-created on server start
- Schema: table `contacts(id, name, email, message, created_at)`
- Reset: stop the server and delete `backend/contacts.db`

## Notes on Requirements
- The current backend uses only the Python standard library; Flask is not used.
- `backend/requirements.txt` is legacy and not required for running `app.py`.

## Deploy

### Frontend (static hosting)
- GitHub Pages: push and enable Pages (Branch: `main`, Folder: `/root`). If using a custom domain, configure DNS and keep `CNAME` present.
- Any static host (Netlify, Vercel, S3, Nginx): deploy `Website/` as a static site.

### Backend (server)
- Run `python3 backend/app.py` on a VM/container. Expose port `5000`.
- To change host/port, edit `HOST`/`PORT` constants in `backend/app.py`.

## Source
- Original repository: `https://github.com/pavithrareddykc/adventaiservices.git`

## License
Not specified in the original repository.
