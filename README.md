# fergusonspainting.com

Website for **Ferguson's Painting & Cleaning, Inc.** (Orlando, FL). It is a static HTML/CSS site hosted on a Cloudflare Worker (static assets), with a small script for the quote form.

See [PLAN.md](PLAN.md) for the full build plan, business facts and launch checklist.

## Layout

| Path | What it is |
|---|---|
| `site-src/bodies/` | **English page content** (one file per page). Line 1 is JSON metadata (path, title, description); the rest is the page body. |
| `site-src/bodies-es/`, `site-src/bodies-pt/` | Spanish and Brazilian Portuguese versions, using the same filenames and `path`. The Spanish and Portuguese home pages (`00-home.html`) are custom landing pages, not translations. |
| `site-src/captions-*.json` | Photo captions (alt text) and gallery category names per language. |
| `tools/build.py` | Builds `public/` from `site-src/`: wraps each body in the shared header, footer and phone bar, adds hreflang tags, structured data and the language switcher, and writes `sitemap.xml`. |
| `public/` | The built website, served as-is by the Worker. `/es/...` is Spanish, `/pt-br/...` is Portuguese. **Don't hand-edit the generated HTML;** edit `site-src/` and rebuild. |
| `public/assets/` | CSS, JS, images (hand-edited). |
| `wrangler.jsonc` | Worker config: serves `public/`, runs `src/worker.js` only for `/api/*`. |
| `src/worker.js`, `src/quote.js` | Quote form: Turnstile check, then an email to derwin@ via Resend. Error messages come back in the visitor's language, and the email is tagged [ES]/[PT]. |
| `images/` | Logo files. Original gallery photos live in `images/gallery/` locally only (git-ignored because they are unblurred). |
| `tools/optimize-images.py` | Turns `images/gallery/**.jpg` into web `.webp` files, blurring house numbers and other businesses' names. |

## Editing

1. Edit the page in `site-src/bodies/` (English). Make the same change in `bodies-es/` and `bodies-pt/`. Keep the HTML structure identical across the three.
2. Run `python tools/build.py`. It needs Python 3 with Pillow and Pagefind (`pip install pillow "pagefind[bin]"`). It also rebuilds the search index in `public/pagefind/`.
3. Preview with `python -m http.server 8080 -d public` and open http://localhost:8080.
4. Commit and push. Cloudflare deploys `main` automatically.

- **Header, footer, phone bar, "How a job goes" and the language strings** all live in `tools/build.py` (the `L` dictionary).
- **New page:** add a body file in all three folders with the same `path`. A page missing from a language falls back to English links automatically.
- **New photos:** add the `.jpg` to `images/gallery/<category>/`, run `python tools/optimize-images.py`, then add captions to the three `captions-*.json` files.
- Shortcodes in bodies: `[[img category/name "alt text" wide]]`, `[[gallery]]`, `[[process]]`.

## Cloudflare Worker settings

- Workers & Pages → Create application → Continue with GitHub → this repo. Cloudflare reads `wrangler.jsonc`, so no build settings are needed (deploy command: `npx wrangler deploy`).
- Worker → Settings → Variables and Secrets: `TURNSTILE_SECRET`, `RESEND_API_KEY` (optional: `QUOTE_TO`, `QUOTE_FROM`)
- Turnstile site key goes in `public/contact/index.html` (`data-sitekey`). Site key: `0x4AAAAAAFgF7yqwi7Slx0f3` (public; widget "Ferguson's quote form").
- `_headers` and `_redirects` in `public/` work on Workers static assets too.
