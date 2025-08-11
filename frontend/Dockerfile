# syntax=docker/dockerfile:1
FROM nginx:1.27-alpine

# Copy site content (relative to build context root)
COPY ../index.html /usr/share/nginx/html/index.html
COPY ../CNAME /usr/share/nginx/html/CNAME

# Hardened nginx config for a simple static site
RUN rm -f /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/site.conf

EXPOSE 80

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD wget -qO- http://127.0.0.1/ | grep -q "Advent AI" || exit 1