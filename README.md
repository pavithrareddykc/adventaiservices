## Advent AI Services — Website

A single-page website for Advent AI training and consulting. The contact form submits to Formspree for handling form submissions and email notifications.

### Features
- **Responsive UI**: Tailwind CSS via CDN
- **Smooth navigation** and **mobile menu toggle**
- **Contact form**: Plain HTML form that posts to Formspree. Works with or without JavaScript, and redirects to a thank-you page on success.
- **Branding assets**: Favicon/app icons and header branding via `logo.png`

### Project Structure
- `index.html`: Main single-page site (hero, services, contact, footer)
- `logo.png`: Favicon, app icons, and header logo
- `CNAME`: Custom domain config for GitHub Pages
- `frontend/tests/test_frontend.py`: Optional E2E tests 

### Tech Stack
- Frontend: HTML5, Tailwind CSS (CDN), Inter (Google Fonts), Vanilla JavaScript

## Run Locally

- Open `index.html` directly in your browser, or
- Serve over a local HTTP server:
```bash
python3 -m http.server 8000
# open http://localhost:8000/
```

## Testing

Playwright E2E tests are in `frontend/tests/test_frontend.py`. 
