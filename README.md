# Advent AI Services — Website

A professional website for Advent AI, a family-led AI consulting and training studio that provides customized AI solutions and personalized training to help businesses adopt AI confidently.

## About Advent AI

Advent AI is a family-led AI consulting and training studio combining decades of leadership experience with cutting-edge technology to deliver human-first AI solutions. We specialize in:

- **AI Strategy Consulting**: Define clear AI strategies and identify opportunities for business growth
- **Custom AI Model Development**: Develop and deploy tailored AI solutions for unique business challenges  
- **Personalized AI Training**: Equip teams with knowledge and skills through customized training programs
- **Roadmap Audits**: Comprehensive AI health checks for existing implementations

### Our Mission
To make organizations work better with AI and make AI work for people. We believe in Human-First AI - technology that enhances and empowers individuals while seamlessly aligning with both people's needs and business objectives.

### Our Principles
- Build for outcome
- Listen deeply  
- Authentic in every interaction
- Show respect, every time and in every transaction
- Trustable

## Website Features

- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Smooth Navigation**: Intuitive navigation with mobile menu toggle
- **Contact Integration**: Formspree-powered contact form with progressive enhancement
- **SEO Optimized**: Complete meta tags, structured data, sitemap, and robots.txt
- **Cookie Consent**: GDPR-compliant cookie management system
- **Accessibility**: ARIA labels, semantic HTML, and keyboard navigation support

## Project Structure

```
adventaiservices/
├── index.html              # Main homepage (hero, services, contact)
├── about.html              # About page with company story and values
├── what-we-do.html         # Detailed services page
├── logo1.png               # Primary logo and favicon
├── logo2.png               # Alternative logo variant
├── cookies.js              # Cookie consent and utilities
├── CNAME                   # Custom domain for www.adventaiservices.com
├── sitemap.xml             # SEO sitemap
├── robots.txt              # Search engine directives
├── frontend/
│   └── tests/
│       └── test_frontend.py # Playwright E2E tests
└── README.md               # This file
```

## Tech Stack

- **Frontend**: HTML5, Tailwind CSS (CDN), Inter (Google Fonts)
- **JavaScript**: Vanilla JS with progressive enhancement
- **Forms**: Formspree integration with fallback support
- **Testing**: Playwright E2E tests
- **Deployment**: GitHub Pages with custom domain
- **SEO**: Structured data, Open Graph, Twitter Cards

## Development

### Local Setup

1. **Direct Browser**: Open `index.html` directly in your browser
2. **Local Server**: Serve via HTTP server:
   ```bash
   python3 -m http.server 8000
   # Visit http://localhost:8000/
   ```

### Testing

Run the Playwright E2E tests to verify form functionality:
```bash
cd frontend/tests
python test_frontend.py
```

The tests verify:
- Successful form submission and redirect flow
- HTML5 validation preventing invalid submissions
- Progressive enhancement (works with/without JavaScript)

## Deployment

The site is deployed on GitHub Pages at [www.adventaiservices.com](https://www.adventaiservices.com) with:
- Custom domain via `CNAME` file
- SSL certificate (automatic via GitHub Pages)
- CDN distribution for global performance

## Contact & Business

- **Website**: [www.adventaiservices.com](https://www.adventaiservices.com)
- **LinkedIn**: [Advent AI Services](https://www.linkedin.com/company/advent-ai-services/)
- **Services**: AI consulting, custom development, training, and roadmap audits
- **Industries**: Healthcare, automobile, manufacturing, services, and more

---

*Built with ❤️ by the Advent AI team - combining experience with innovation to deliver human-first AI solutions.* 
