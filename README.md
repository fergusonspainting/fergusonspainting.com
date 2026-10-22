# fergusonspainting.com

Website for **Ferguson's Painting & Cleaning, Inc.** (Orlando, FL). It is a static HTML/CSS site hosted on Cloudflare Pages, with one Pages Function for the quote form.

See [PLAN.md](PLAN.md) for the full build plan, business facts and launch checklist.

## Layout

| Path | What it is |
|---|---|
| `public/` | The website. Cloudflare Pages serves this folder as-is (no build step). |
| `public/assets/css/site.css` | All styles. Brand colors are at the top (`--orange`, `--black`). |
| `public/assets/js/site.js` | Mobile menu, gallery filter and lightbox, quote form submit. |
| `functions/api/quote.js` | `POST /api/quote`: checks Turnstile, then emails the request to derwin@ through Resend. |
| `images/` | Logo files. Original gallery photos live in `images/gallery/` locally only (git-ignored because they are unblurred). |
| `tools/optimize-images.py` | Turns `images/gallery/**.jpg` into web `.webp` files in `public/assets/img/gallery/`, blurring house numbers and other businesses' names. |

## Editing

- **Text:** edit the page's `index.html` under `public/`. The header and footer are repeated in every page, so a change to the phone number, nav or hours means a find-and-replace across `public/**/*.html`.
- **Adding photos:** drop the `.jpg` into `images/gallery/<category>/`, run `python tools/optimize-images.py`, then reference `/assets/img/gallery/<category>/<name>-sm.webp` (thumbnail) or `<name>.webp` (full size). If a photo shows a house number or another company's name, add a blur box for it in the `BLUR` map first.
- **Preview locally:** `python -m http.server 8080 -d public`, then open http://localhost:8080 (the quote form needs Cloudflare to work).

Pushing to `main` deploys automatically. Other branches get a preview URL.

## Cloudflare Pages settings

- Build command: *(none)* · Output directory: `public`
- Variables and Secrets: `TURNSTILE_SECRET`, `RESEND_API_KEY` (optional: `QUOTE_TO`, `QUOTE_FROM`)
- Turnstile site key goes in `public/contact/index.html` (`data-sitekey`). It currently has Cloudflare's always-pass **test** key.
