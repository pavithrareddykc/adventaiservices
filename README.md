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

## AI Email Agent (Backend)

The backend now supports sending an email to configured recipients when a contact form is submitted. It will use OpenAI to craft a clear subject/body when `OPENAI_API_KEY` is set; otherwise it falls back to a deterministic format.

### Environment variables
- `MAIL_FROM` (required): sender address, e.g. `noreply@example.com`
- `MAIL_RECIPIENTS` (optional): comma-separated recipient emails, e.g. `ops@example.com,sales@example.com`
- `SMTP_HOST` (optional): SMTP host to send real emails. If omitted, emails print to stdout.
- `SMTP_PORT` (optional, default `587`)
- `SMTP_USER` / `SMTP_PASS` (optional): SMTP credentials if required
- `SMTP_USE_TLS` (optional, default `true`)
- `OPENAI_API_KEY` (optional): enables AI-crafted subject/body
- `OPENAI_MODEL` (optional, default `gpt-4o-mini`)
- `ALLOW_SUBMITTER_AS_FROM` (optional, default `false`): if true, use the submitter's email as the visible From.

### Install backend dependencies
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### Run backend locally
```bash
cd backend
MAIL_FROM="noreply@example.com" MAIL_RECIPIENTS="owner@example.com" python3 app.py
```

When `SMTP_HOST` is not set, emails will be printed to the console and not actually sent.

### Background email queue
Emails are enqueued and sent in a background thread with retries and exponential backoff. The API responds quickly (201) even if the email send later fails; failures are logged to stdout. To disable actual SMTP delivery, omit `SMTP_HOST` to use the stdout fallback.

### Abuse prevention
- Per-IP rate limiting: configurable via env vars
  - `RATE_LIMIT_MAX_REQUESTS` (default `10`)
  - `RATE_LIMIT_WINDOW_SECONDS` (default `60`)
- Honeypot field: the frontend includes a hidden `company` input; if filled, the backend accepts but ignores the submission (no DB insert or email).

### Observability
- Structured JSON logs to stdout (set `LOG_LEVEL` if needed)
- Minimal audit trail in SQLite table `audit_events` recording submissions and email events

### Email headers
- Reply-To is set to the submitter's email so recipients can reply directly.
- To use the submitter's email as the visible From, set `ALLOW_SUBMITTER_AS_FROM=true` (ensure your SMTP/provider/DKIM policies allow this). Otherwise `MAIL_FROM` is used as From.

### Persistent configuration
Create `backend/.env` using `backend/.env.example` as a template. Values in `.env` are loaded automatically on server start.

```bash
cp backend/.env.example backend/.env
# edit backend/.env with your values
cd backend && python3 app.py
```
