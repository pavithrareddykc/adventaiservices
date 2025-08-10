# Advent AI Services — Website

A lightweight single-page website for Advent AI training and consulting. Built with semantic HTML, Tailwind CSS via CDN, Google Fonts, and minimal vanilla JavaScript.

## Features
- Responsive layout using Tailwind CSS CDN
- Smooth scrolling navigation
- Mobile menu toggle
- Contact form with simulated submission (no backend)
- Simple fade-in animations

## Project Structure
- `index.html`: Main single-page site (hero, services, contact, footer)
- `CNAME`: Custom domain config for GitHub Pages

## Tech Stack
- HTML5
- Tailwind CSS (CDN)
- Inter font (Google Fonts)
- Vanilla JavaScript

## Run Locally
- Option 1: Open directly
  - Double-click `index.html` or open it in your browser.
- Option 2: Serve over a local HTTP server (recommended)
  - Using Python 3:
    ```bash
    cd Website
    python3 -m http.server 8000
    ```
    Then open `http://localhost:8000` in your browser.

## Development Notes
- Tailwind is loaded via CDN and configured inline via `tailwind.config` in `index.html` (custom colors and fonts).
- Basic animations are defined in a `<style>` block.
- The contact form simulates an API call with `setTimeout`. To integrate a real backend, replace the simulation with a `fetch` call to your API endpoint and handle success/error states accordingly.

## Deploy
- GitHub Pages
  - Push contents to a GitHub repository.
  - In repository Settings → Pages, enable Pages (Branch: `main`, Folder: `/root`).
  - Optional: Use a custom domain. The `CNAME` file is already present—configure your DNS to point to GitHub Pages per GitHub docs.
- Any static host (Netlify, Vercel, AWS S3, Nginx)
  - Deploy the folder contents as a static site.

## Source
- Original repository: `https://github.com/pavithrareddykc/adventaiservices.git`

## License
Not specified in the original repository.
