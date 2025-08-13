# Rockland Design Factory — Static Site

This is a fast, SEO-first static site scaffold implementing:
- Core pages, breadcrumbs, descriptive URLs
- robots.txt and XML sitemap
- Canonical tags, meta titles/descriptions
- JSON-LD: WebSite, Organization, LocalBusiness, Service, BreadcrumbList, FAQPage
- Minimal CSS, deferred JS for good Core Web Vitals

## Build

Requires Python 3.8+.

```bash
cd /workspace/rdf-site
python3 build.py
```

Output is written to `dist/`.

## Serve locally (Python)

```bash
cd dist
python3 -m http.server 8080
```

Open http://localhost:8080/

## Notes
- Update NAP, hours, and links in `_includes/footer.html` for production.
- Submit `sitemap.xml` in Search Console and fix any crawl errors.
- Replace placeholder OG image URLs with real assets.