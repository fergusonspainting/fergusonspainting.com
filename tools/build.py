"""Build the site: turns site-src/ page bodies into public/**/index.html in English, Spanish and Portuguese.

Usage (from anywhere):  python tools/build.py
  site-src/bodies/      English page bodies (source of truth)
  site-src/bodies-es/   Spanish bodies (same filenames, same "path")
  site-src/bodies-pt/   Brazilian Portuguese bodies
  site-src/captions-en.json, captions-es.json, captions-pt.json   photo captions and gallery category names

Each body starts with a JSON line: {"path": "about/", "title": ..., "desc": ..., "nav": ..., "crumb": ..., "service": ...}
Shortcodes: [[img cat/name "alt" eager|wide]], [[gallery]], [[process]]
Spanish pages are written under /es/, Portuguese under /pt-br/. Internal links in translated bodies are
rewritten to the same language when that page exists, otherwise they fall back to English.
"""
import json
import re
import sys
from html import escape
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "site-src"
PUB = ROOT / "public"
IMG = PUB / "assets" / "img" / "gallery"
SITE = "https://fergusonspainting.com"
TODAY = "2026-10-22"

_en = json.loads((GEN / "captions-en.json").read_text(encoding="utf-8"))
CAT_NAMES = _en.pop("_cats")
_en.pop("_all", None)
CAPTIONS_EN = _en

PHONE = "(321) 202-7225"
TEL = "tel:+13212027225"
SMS = "sms:+13212027225"
MAIL = "mailto:derwin@fergusonspainting.com?subject=Quote%20request"

AREA_LINKS = [("/areas/", "Orlando"), ("/areas/kissimmee/", "Kissimmee"), ("/areas/celebration/", "Celebration"),
              ("/areas/reunion/", "Reunion"), ("/areas/championsgate/", "ChampionsGate"),
              ("/areas/davenport/", "Davenport"), ("/areas/windermere/", "Windermere"), ("/areas/lake-mary/", "Lake Mary")]
SERVICE_PATHS = ["/services/exterior-painting/", "/services/interior-painting/", "/services/popcorn-ceiling-removal/",
                 "/services/stucco-repair/", "/services/handyman/", "/services/carpentry/", "/services/remodeling/",
                 "/services/pressure-washing/", "/services/vacation-rental-painting/", "/commercial/"]

L = {
    "en": dict(
        prefix="", html="en", og="en_US", name="English", short="EN",
        skip="Skip to content", small="Orlando &amp; Central Florida", menu="Menu",
        nav=["Services", "Our work", "Reviews", "About", "Contact"], free_quote="Free quote",
        cta_h="Ready for a fresh coat?", cta_p="Tell us about the job and we'll set up a free estimate.",
        call=f"Call {PHONE}", text_us="Text us", email="Email Derwin", request="Request a quote",
        tagline="Always a professional, neat and clean service.", logo_alt="Ferguson's Painting &amp; Cleaning, Inc. logo",
        contact_h="Contact", hours="Monday–Friday, 8am–5pm", reply=None,
        services_h="Services", services=["Exterior painting", "Interior painting", "Popcorn ceiling removal", "Stucco repair",
                                         "Handyman &amp; repairs", "Pool decks &amp; carpentry", "Remodeling", "Pressure washing",
                                         "Vacation rental painting", "Commercial &amp; HOA/POA"],
        areas_h="Service area", all_areas="All service areas", guides="Homeowner guides",
        legal="© 2026 Ferguson's Painting &amp; Cleaning, Inc. Serving Central Florida since 2012. Fully insured.",
        bar=["Call", "Text", "Email", "Quote"],
        crumbs={"home": "Home", "services": "Services", "areas": "Service areas", "guides": "Guides"},
        process_h="How a job goes",
        process=[("Free estimate", '<a href="/about/">Derwin</a> comes out, looks at the job and gives you a clear written price.'),
                 ("Schedule", "We book a start date that works for you and keep you posted."),
                 ("Prep and protect", "Floors, plants and furniture get covered before any work starts."),
                 ("Do the work", "Repairs first, then finish work, done right the first time."),
                 ("Walkthrough and cleanup", "We walk the job with you and leave the site clean.")],
        filter_label="Filter photos", all_work="All work", lang_label="Language", related_h="More from Ferguson's", related=[("about/", "About Derwin"), ("services/", "All services"), ("areas/", "Service areas"), ("guides/", "Homeowner guides"), ("reviews/", "Reviews"), ("gallery/", "Our work")], byline="From the team at Ferguson's Painting &amp; Cleaning, Orlando. Updated October 2026.", main_nav="Main", search="Search", close="Close", home_label="Ferguson's Painting & Cleaning, home",
        biz_desc="Owner-run painting, carpentry, home repair, remodeling and pressure washing company serving Orlando and Central Florida since 2012.",
        form_note=None,
    ),
    "es": dict(
        prefix="/es", html="es", og="es_US", name="Español", short="ES",
        skip="Saltar al contenido", small="Orlando y Florida Central", menu="Menú",
        nav=["Servicios", "Nuestro trabajo", "Reseñas", "Nosotros", "Contacto"], free_quote="Cotización gratis",
        cta_h="¿Listo para una nueva capa de pintura?", cta_p="Cuéntenos sobre el trabajo y coordinamos un estimado gratis.",
        call=f"Llamar al {PHONE}", text_us="Envíenos un texto", email="Escríbale a Derwin", request="Pedir cotización",
        tagline="Siempre un servicio profesional, ordenado y limpio.", logo_alt="Logo de Ferguson's Painting &amp; Cleaning, Inc.",
        contact_h="Contacto", hours="Lunes a viernes, 8am–5pm",
        reply="Nuestro equipo responde en inglés. Puede escribirnos en español.",
        services_h="Servicios", services=["Pintura exterior", "Pintura interior", "Remoción de techos de popcorn", "Reparación de estuco",
                                          "Handyman y reparaciones", "Decks de piscina y carpintería", "Remodelación", "Lavado a presión",
                                          "Pintura de casas vacacionales", "Comercial y HOA/POA"],
        areas_h="Área de servicio", all_areas="Todas las áreas de servicio", guides="Guías para propietarios",
        legal="© 2026 Ferguson's Painting &amp; Cleaning, Inc. Al servicio de Florida Central desde 2012. Totalmente asegurados.",
        bar=["Llamar", "Texto", "Email", "Cotizar"],
        crumbs={"home": "Inicio", "services": "Servicios", "areas": "Áreas de servicio", "guides": "Guías"},
        process_h="Cómo funciona un trabajo",
        process=[("Estimado gratis", '<a href="/about/">Derwin</a> va, revisa el trabajo y le da un precio claro por escrito.'),
                 ("Programación", "Fijamos una fecha de inicio que le convenga y lo mantenemos informado."),
                 ("Preparar y proteger", "Cubrimos pisos, plantas y muebles antes de empezar."),
                 ("Hacer el trabajo", "Primero las reparaciones, luego el acabado, bien hecho desde la primera vez."),
                 ("Revisión final y limpieza", "Revisamos el trabajo con usted y dejamos todo limpio.")],
        filter_label="Filtrar fotos", all_work="Todos los trabajos", lang_label="Idioma", related_h="Más de Ferguson's", related=[("about/", "Sobre Derwin"), ("services/", "Todos los servicios"), ("areas/", "Áreas de servicio"), ("guides/", "Guías para propietarios"), ("reviews/", "Reseñas"), ("gallery/", "Nuestro trabajo")], byline="Del equipo de Ferguson's Painting &amp; Cleaning, Orlando. Actualizado en octubre de 2026.", main_nav="Principal", search="Buscar", close="Cerrar", home_label="Ferguson's Painting & Cleaning, inicio",
        biz_desc="Empresa de pintura, carpintería, reparaciones, remodelación y lavado a presión, dirigida por su dueño, al servicio de Orlando y Florida Central desde 2012.",
        form_note="Nuestro equipo responde en inglés. Puede escribir su mensaje en español y lo traduciremos.",
    ),
    "pt": dict(
        prefix="/pt-br", html="pt-BR", og="pt_BR", name="Português", short="PT",
        skip="Pular para o conteúdo", small="Orlando e Flórida Central", menu="Menu",
        nav=["Serviços", "Nossos trabalhos", "Avaliações", "Sobre nós", "Contato"], free_quote="Orçamento grátis",
        cta_h="Pronto para uma pintura nova?", cta_p="Conte sobre o serviço e marcamos um orçamento grátis.",
        call=f"Ligar {PHONE}", text_us="Enviar mensagem", email="E-mail para o Derwin", request="Pedir orçamento",
        tagline="Sempre um serviço profissional, organizado e limpo.", logo_alt="Logo da Ferguson's Painting &amp; Cleaning, Inc.",
        contact_h="Contato", hours="Segunda a sexta, 8h às 17h",
        reply="Nossa equipe responde em inglês. Você pode escrever em português.",
        services_h="Serviços", services=["Pintura externa", "Pintura interna", "Remoção de teto popcorn", "Reparo de stucco",
                                         "Faz-tudo e reparos", "Decks de piscina e carpintaria", "Reforma", "Lavagem com alta pressão",
                                         "Pintura de casas de temporada", "Comercial e HOA/POA"],
        areas_h="Área de atendimento", all_areas="Todas as áreas atendidas", guides="Guias para proprietários",
        legal="© 2026 Ferguson's Painting &amp; Cleaning, Inc. Atendendo a Flórida Central desde 2012. Com seguro completo.",
        bar=["Ligar", "Mensagem", "E-mail", "Orçamento"],
        crumbs={"home": "Início", "services": "Serviços", "areas": "Áreas atendidas", "guides": "Guias"},
        process_h="Como funciona o serviço",
        process=[("Orçamento grátis", '<a href="/about/">O Derwin</a> vai até você, avalia o serviço e entrega um preço claro por escrito.'),
                 ("Agendamento", "Marcamos uma data de início que funcione para você e mantemos você informado."),
                 ("Preparar e proteger", "Pisos, plantas e móveis são cobertos antes de começar."),
                 ("Executar o serviço", "Primeiro os reparos, depois o acabamento, bem feito da primeira vez."),
                 ("Vistoria e limpeza", "Revisamos o serviço com você e deixamos tudo limpo.")],
        filter_label="Filtrar fotos", all_work="Todos os trabalhos", lang_label="Idioma", related_h="Mais da Ferguson's", related=[("about/", "Sobre o Derwin"), ("services/", "Todos os serviços"), ("areas/", "Áreas atendidas"), ("guides/", "Guias para proprietários"), ("reviews/", "Avaliações"), ("gallery/", "Nossos trabalhos")], byline="Da equipe da Ferguson's Painting &amp; Cleaning, Orlando. Atualizado em outubro de 2026.", main_nav="Principal", search="Buscar", close="Fechar", home_label="Ferguson's Painting & Cleaning, página inicial",
        biz_desc="Empresa de pintura, carpintaria, reparos, reformas e lavagem com alta pressão, comandada pelo dono, atendendo Orlando e a Flórida Central desde 2012.",
        form_note="Nossa equipe responde em inglês. Pode escrever sua mensagem em português, e nós traduzimos.",
    ),
}
NAV_KEYS = [("services", "/services/"), ("gallery", "/gallery/"), ("reviews", "/reviews/"), ("about", "/about/"), ("contact", "/contact/")]
BODY_DIRS = {"en": GEN / "bodies", "es": GEN / "bodies-es", "pt": GEN / "bodies-pt"}

# ---------- captions ----------
CAPTIONS = {"en": CAPTIONS_EN}
CATS = {"en": dict(CAT_NAMES)}
for lang in ("es", "pt"):
    f = GEN / f"captions-{lang}.json"
    data = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
    CAPTIONS[lang] = {c: {**CAPTIONS_EN[c], **data.get(c, {})} for c in CAPTIONS_EN}
    CATS[lang] = {**CAT_NAMES, **data.get("_cats", {})}
    if data.get("_all"):
        L[lang]["all_work"] = data["_all"]


def caption(key, lang):
    cat, name = key.split("/")
    return CAPTIONS[lang][cat][name]


VARIANTS = ("-w400", "-sm", "-w750", "-md", "")
SIZES = {
    "eager": "(max-width: 820px) 100vw, 50vw",                              # hero
    "wide": "(max-width: 820px) calc(100vw - 2rem), 560px",                 # half of a two-column split
    "thumb": "(max-width: 600px) calc(50vw - 1.5rem), 260px",               # photo grids / gallery
    "": "(max-width: 560px) calc(100vw - 2rem), (max-width: 900px) 45vw, 380px",  # cards, pairs, steps
}


def srcset(key):
    parts = []
    for v in VARIANTS:
        f = IMG / f"{key}{v}.webp"
        if f.exists():
            parts.append((Image.open(f).size[0], f"/assets/img/gallery/{key}{v}.webp"))
    return ", ".join(f"{u} {w}w" for w, u in sorted(set(parts)))


def img(key, lang, alt=None, mode=""):
    sm = Image.open(IMG / f"{key}-sm.webp").size
    alt = escape(alt or caption(key, lang), quote=True)
    load = 'fetchpriority="high"' if mode == "eager" else 'loading="lazy" decoding="async"'
    return (f'<img src="/assets/img/gallery/{key}-sm.webp" srcset="{srcset(key)}" sizes="{SIZES.get(mode, SIZES[""])}" '
            f'width="{sm[0]}" height="{sm[1]}" alt="{alt}" {load}>')


def gallery(lang):
    s = L[lang]
    out = [f'<div class="filters" role="group" aria-label="{s["filter_label"]}">',
           f'<button type="button" data-filter="all" aria-pressed="true">{escape(s["all_work"])}</button>']
    out += [f'<button type="button" data-filter="{c}" aria-pressed="false">{escape(CATS[lang][c])}</button>' for c in CAT_NAMES]
    out.append('</div>\n<div class="grid-photos" data-gallery>')
    for cat in CAT_NAMES:
        for name in CAPTIONS_EN[cat]:
            key = f"{cat}/{name}"
            out.append(f'<a href="/assets/img/gallery/{key}.webp" data-cat="{cat}" data-caption="{escape(caption(key, lang), quote=True)}">{img(key, lang, mode="thumb")}</a>')
    out.append('</div>')
    return "\n".join(out)


def process(lang):
    s = L[lang]
    items = "\n".join(f"      <li><strong>{t}</strong>{d}</li>" for t, d in s["process"])
    return f"""<section class="section section--primer">
  <div class="wrap">
    <h2>{s["process_h"]}</h2>
    <ol class="process">
{items}
    </ol>
  </div>
</section>"""


def expand(body, lang):
    # Images inside photo grids are small thumbnails: give them the "thumb" sizes hint
    body = re.sub(r'<div class="grid-photos">.*?</div>\n',
                  lambda m: re.sub(r'\[\[img (\S+)( "[^"]*")?\]\]', r'[[img \1\2 thumb]]', m[0]), body, flags=re.S)
    body = body.replace("[[gallery]]", gallery(lang)).replace("[[process]]", process(lang))
    return re.sub(r'\[\[img (\S+)(?: "([^"]*)")?(?: (eager|wide|thumb))?\]\]', lambda m: img(m[1], lang, m[2], m[3] or ""), body)


import hashlib
CSS_V = hashlib.sha256((PUB / "assets/css/site.css").read_bytes()).hexdigest()[:10]
JS_V = hashlib.sha256((PUB / "assets/js/site.js").read_bytes()).hexdigest()[:10]

# ---------- page index ----------
PAGES = {lang: {} for lang in L}
for lang, d in BODY_DIRS.items():
    if not d.exists():
        continue
    for f in sorted(d.glob("*.html")):
        meta_line, body = f.read_text(encoding="utf-8").split("\n", 1)
        meta = json.loads(meta_line)
        PAGES[lang][meta["path"]] = (meta, body)


def norm(path):
    """'/services/x/' -> 'services/x/' as used in meta['path']; '/' -> ''."""
    return path.lstrip("/")


def lang_url(lang, path):
    """Absolute site path for page `path` (meta-style) in `lang`, falling back to English if missing."""
    if lang != "en" and path in PAGES[lang]:
        return f'{L[lang]["prefix"]}/{path}'
    return f"/{path}"


def localize_links(html, lang):
    if lang == "en":
        return html

    def fix(m):
        target = m[1]
        p = norm(target.split("#")[0])
        if p.startswith(("assets/", "api/", "cdn-cgi/")) or p.endswith((".webp", ".jpg", ".png", ".xml", ".txt", ".ico")):
            return m[0]
        return f'href="{lang_url(lang, p)}{"#" + target.split("#", 1)[1] if "#" in target else ""}"'
    return re.sub(r'href="(/[^"]*)"', fix, html)


# ---------- head / header / footer ----------
def head(lang, meta, url, alternates, extra, preload=""):
    s = L[lang]
    robots = '<meta name="robots" content="noindex">\n' if meta.get("noindex") else ""
    alt_links = "".join(f'<link rel="alternate" hreflang="{h}" href="{u}">\n' for h, u in alternates)
    og_alt = "".join(f'<meta property="og:locale:alternate" content="{L[x]["og"]}">\n' for x in L if x != lang)
    title = escape(meta["title"])
    desc = escape(meta["desc"], quote=True)
    return f"""<!doctype html>
<html lang="{s["html"]}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
{alt_links}{robots}<meta property="og:type" content="website">
<meta property="og:site_name" content="Ferguson's Painting &amp; Cleaning, Inc.">
<meta property="og:locale" content="{s["og"]}">
{og_alt}<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{SITE}/assets/img/og-image.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#000000">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<link rel="preload" href="/assets/fonts/barlow-condensed-800-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="preload" href="/assets/fonts/barlow-400-latin.woff2" as="font" type="font/woff2" crossorigin>
{preload}<link rel="stylesheet" href="/assets/css/site.css?v={CSS_V}">
<script src="/assets/js/site.js?v={JS_V}" defer></script>
{extra}</head>
"""


def header(lang, meta):
    s = L[lang]
    pre = s["prefix"]
    nav = "\n".join(
        f'      <a href="{lang_url(lang, norm(href))}"' + (' aria-current="page"' if meta.get("nav") == key else "") + f'>{label}</a>'
        for (key, href), label in zip(NAV_KEYS, s["nav"]))
    langs = "".join(
        f'<a href="{lang_url(x, meta["path"]) if meta["path"] in PAGES[x] else L[x]["prefix"] + "/"}" hreflang="{L[x]["html"]}" lang="{L[x]["html"]}"'
        + (' aria-current="true"' if x == lang else "") + f' title="{L[x]["name"]}">{L[x]["short"]}</a>'
        for x in L)
    return f"""<body>
<a class="skip" href="#main">{s["skip"]}</a>
<header class="site-header">
  <div class="wrap">
    <a class="brand" href="{pre}/" aria-label="{escape(s["home_label"], quote=True)}">
      <img src="/assets/img/logo-120.webp" width="60" height="60" alt="">
      <span><strong>Ferguson's Painting &amp; Cleaning</strong><small>{s["small"]}</small></span>
    </a>
    <a class="header-phone" href="{TEL}">{PHONE}</a>
    <nav class="langs" aria-label="{s["lang_label"]}">{langs}</nav>
    <button class="search-toggle" type="button" aria-haspopup="dialog" aria-label="{s["search"]}" title="{s["search"]}" data-search-open>
      <svg width="22" height="22" viewBox="0 0 24 24" aria-hidden="true" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round"><circle cx="10.5" cy="10.5" r="6.5"/><path d="m15.5 15.5 5 5"/></svg>
    </button>
    <button class="nav-toggle" type="button" aria-expanded="false" aria-controls="site-nav" data-menu="{s["menu"]}" data-close="{s["close"]}">{s["menu"]}</button>
    <nav class="nav" id="site-nav" aria-label="{s["main_nav"]}">
{nav}
      <a class="btn btn--orange" href="{lang_url(lang, "contact/")}">{s["free_quote"]}</a>
    </nav>
  </div>
</header>
<dialog class="search-dialog" aria-label="{s["search"]}">
  <div class="search-dialog__bar"><strong>{s["search"]}</strong><button type="button" class="btn btn--black" data-search-close>{s["close"]}</button></div>
  <div id="site-search"></div>
</dialog>
<main id="main"{" data-pagefind-body" if not meta.get("noindex") else ""}>
"""


def footer(lang):
    s = L[lang]
    svc = "\n".join(f'        <li><a href="{lang_url(lang, norm(p))}">{label}</a></li>' for p, label in zip(SERVICE_PATHS, s["services"]))
    areas = "\n".join(f'        <li><a href="{lang_url(lang, norm(p))}">{label}</a></li>' for p, label in AREA_LINKS)
    reply = f'\n        <li>{s["reply"]}</li>' if s["reply"] else ""
    return f"""<section class="cta-band" data-pagefind-ignore>
  <div class="wrap">
    <div>
      <h2>{s["cta_h"]}</h2>
      <p>{s["cta_p"]}</p>
    </div>
    <div class="btn-row">
      <a class="btn btn--black" href="{TEL}">{s["call"]}</a>
      <a class="btn btn--black" href="{SMS}">{s["text_us"]}</a>
      <a class="btn btn--black" href="{MAIL}">{s["email"]}</a>
      <a class="btn btn--black" href="{lang_url(lang, "contact/")}">{s["request"]}</a>
    </div>
  </div>
</section>
</main>
<footer class="site-footer">
  <div class="wrap">
    <div>
      <img src="/assets/img/logo-256.webp" width="120" height="120" alt="{s["logo_alt"]}" loading="lazy">
      <p>{s["tagline"]}</p>
    </div>
    <div>
      <h2>{s["contact_h"]}</h2>
      <ul>
        <li><a href="{TEL}">{PHONE}</a></li>
        <li><a href="mailto:derwin@fergusonspainting.com">derwin@fergusonspainting.com</a></li>
        <li>{s["hours"]}</li>{reply}
        <li><a href="https://www.facebook.com/FergusonsPaintingCleaningAndHomeRepair/" rel="noopener">Facebook</a></li>
      </ul>
    </div>
    <div>
      <h2>{s["services_h"]}</h2>
      <ul>
{svc}
      </ul>
    </div>
    <div>
      <h2>{s["areas_h"]}</h2>
      <ul>
{areas}
        <li><a href="{lang_url(lang, "areas/")}">{s["all_areas"]}</a></li>
        <li><a href="{lang_url(lang, "guides/")}">{s["guides"]}</a></li>
      </ul>
    </div>
    <p class="legal">{s["legal"]}</p>
  </div>
</footer>
<div class="callbar">
  <a href="{TEL}">{s["bar"][0]}</a>
  <a href="{SMS}">{s["bar"][1]}</a>
  <a href="{MAIL}">{s["bar"][2]}</a>
  <a href="{lang_url(lang, "contact/")}">{s["bar"][3]}</a>
</div>
</body>
</html>
"""


# ---------- structured data ----------
BIZ_ID = SITE + "/#business"
AREAS = [("City", "Orlando, FL"), ("City", "Kissimmee, FL"), ("City", "Celebration, FL"), ("Place", "Reunion, FL"),
         ("Place", "Reunion West, FL"), ("Place", "ChampionsGate, FL"), ("City", "Davenport, FL"), ("City", "Windermere, FL"),
         ("Place", "Lake Butler, Windermere, FL"), ("Place", "Golden Oak, FL"), ("Place", "Dr. Phillips, FL"),
         ("Place", "Horizon West, FL"), ("City", "Winter Garden, FL"), ("City", "Winter Park, FL"), ("City", "Maitland, FL"),
         ("City", "Altamonte Springs, FL"), ("City", "Longwood, FL"), ("Place", "Hunter's Creek, FL"), ("City", "Lake Mary, FL")]
AREA_SERVED = [{"@type": t, "name": n} for t, n in AREAS]


def business(lang):
    return {
        "@context": "https://schema.org", "@type": ["HousePainter", "HomeAndConstructionBusiness"], "@id": BIZ_ID,
        "name": "Ferguson's Painting & Cleaning, Inc.", "alternateName": "Ferguson's Painting, Cleaning and Home Repair",
        "description": L[lang]["biz_desc"], "url": SITE + L[lang]["prefix"] + "/",
        "logo": SITE + "/assets/img/logo-512.png", "image": SITE + "/assets/img/og-image.jpg",
        "telephone": "+1-321-202-7225", "email": "derwin@fergusonspainting.com", "priceRange": "$$",
        "founder": {"@type": "Person", "name": "Derwin Ferguson"}, "foundingDate": "2012-08-27",
        "areaServed": AREA_SERVED,
        "address": {"@type": "PostalAddress", "addressLocality": "Orlando", "addressRegion": "FL", "addressCountry": "US"},
        "openingHoursSpecification": [{"@type": "OpeningHoursSpecification",
                                       "dayOfWeek": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                                       "opens": "08:00", "closes": "17:00"}],
        "knowsLanguage": "en",
        "sameAs": ["https://www.facebook.com/FergusonsPaintingCleaningAndHomeRepair/"],
    }


def ld(obj):
    return '<script type="application/ld+json">\n' + json.dumps(obj, ensure_ascii=False) + "\n</script>\n"


def strip_tags(s):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", s)).strip()


def schema(lang, meta, body, url):
    if meta.get("noindex"):
        return ""
    s = L[lang]
    out = []
    if meta["path"] == "":
        out.append(ld(business(lang)))
        faqs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", body, re.S)
        if faqs:
            out.append(ld({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": s["html"], "mainEntity": [
                {"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
                for q, a in faqs]}))
        return "".join(out)
    h1 = strip_tags(re.search(r"<h1[^>]*>(.*?)</h1>", body, re.S)[1])
    home = SITE + s["prefix"] + "/"
    crumbs = [(s["crumbs"]["home"], home)]
    parts = meta["path"].strip("/").split("/")
    if len(parts) > 1 and parts[0] in ("services", "areas", "guides"):
        crumbs.append((s["crumbs"][parts[0]], SITE + lang_url(lang, parts[0] + "/")))
    elif parts[0] == "house-painting-cost-orlando":
        crumbs.append((s["crumbs"]["guides"], SITE + lang_url(lang, "guides/")))
    if (len(parts) > 1 and parts[0] == "guides") or parts[0] == "house-painting-cost-orlando":
        out.append(ld({"@context": "https://schema.org", "@type": "Article", "headline": h1, "description": meta["desc"],
                       "inLanguage": s["html"], "url": url, "image": SITE + "/assets/img/og-image.jpg",
                       "dateModified": TODAY, "author": {"@id": BIZ_ID}, "publisher": {"@id": BIZ_ID}}))
    crumbs.append((meta.get("crumb", h1), url))
    out.append(ld({"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
        {"@type": "ListItem", "position": i, "name": n, "item": u} for i, (n, u) in enumerate(crumbs, 1)]}))
    if meta.get("service"):
        out.append(ld({"@context": "https://schema.org", "@type": "Service", "name": meta["service"],
                       "serviceType": meta["service"], "url": url, "description": meta["desc"], "provider": {"@id": BIZ_ID},
                       "areaServed": [{"@type": "Place", "name": meta["city"]}] if meta.get("city") else AREA_SERVED}))
    faqs = re.findall(r"<details><summary>(.*?)</summary><p>(.*?)</p></details>", body, re.S)
    if faqs:
        out.append(ld({"@context": "https://schema.org", "@type": "FAQPage", "inLanguage": s["html"], "mainEntity": [
            {"@type": "Question", "name": strip_tags(q), "acceptedAnswer": {"@type": "Answer", "text": strip_tags(a)}}
            for q, a in faqs]}))
    return "".join(out)


# ---------- quote form localization ----------
def localize_form(body, lang):
    if 'data-quote-form' not in body:
        return body
    s = L[lang]
    attrs = f'data-quote-form data-lang="{lang}" data-thanks="{lang_url(lang, "thanks/")}"'
    hidden = f'\n      <input type="hidden" name="lang" value="{lang}">'
    note = f'\n      <p class="form-note">{s["form_note"]}</p>' if s["form_note"] else ""
    return body.replace("data-quote-form>", attrs + ">" + hidden + note, 1)


def related_block(lang, meta, page_body):
    """Short 'More from Ferguson's' links on service, area and guide pages; byline on guides."""
    st = L[lang]
    path = meta["path"]
    parts = path.strip("/").split("/")
    is_guide = (parts[0] == "guides" and len(parts) > 1) or parts[0] == "house-painting-cost-orlando"
    if is_guide:
        byline = f'<p class="byline">{st["byline"]}</p>'
        page_body = re.sub(r"(</section>)", r"\1\n" + byline.replace("\\", "\\\\"), page_body, count=1)
    if not (parts[0] in ("services", "areas", "commercial") or is_guide) or path in ("services/", "areas/"):
        return page_body
    links = "".join(f'<li><a href="{lang_url(lang, p)}">{label}</a></li>' for p, label in st["related"] if p != path)
    block = f"""<section class="section section--primer related" data-pagefind-ignore>
  <div class="wrap">
    <h2>{st["related_h"]}</h2>
    <ul class="areas">{links}</ul>
  </div>
</section>
"""
    return page_body + block


# ---------- build ----------
def out_path(lang, path):
    base = PUB / L[lang]["prefix"].strip("/") if lang != "en" else PUB
    return base / path if path.endswith(".html") else base / path / "index.html"


def build(lang, path):
    meta, body = PAGES[lang][path]
    url = SITE + lang_url(lang, path)
    alternates = []
    if not meta.get("noindex"):
        for x in L:
            if path in PAGES[x]:
                alternates.append((L[x]["html"], SITE + lang_url(x, path)))
        alternates.append(("x-default", SITE + "/" + path))
    page_body = localize_links(localize_form(expand(body, lang), lang), lang)
    page_body = related_block(lang, meta, page_body)
    page_body = page_body.replace('<span class="stars" aria-label=', '<span class="stars" role="img" aria-label=')
    if lang != "en":  # review quotes stay in their original English: tell screen readers (WCAG 3.1.2)
        page_body = page_body.replace('<blockquote class="quote"', '<blockquote class="quote" lang="en"')
    hero = re.search(r'<img src="[^"]+" srcset="([^"]+)" sizes="([^"]+)"[^>]*fetchpriority="high"', page_body)
    preload = (f'<link rel="preload" as="image" imagesrcset="{hero[1]}" imagesizes="{hero[2]}" fetchpriority="high">\n'
               if hero else "")
    html = (head(lang, meta, url, alternates, meta.get("extra", "") + schema(lang, meta, body, url), preload)
            + header(lang, meta) + page_body + footer(lang))
    out = out_path(lang, path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8", newline="\n")
    return out


def sitemap():
    rows = []
    for path, (meta, _) in PAGES["en"].items():
        if meta.get("noindex") or path.endswith(".html"):
            continue
        langs = [x for x in L if path in PAGES[x] and not PAGES[x][path][0].get("noindex")]
        alts = "".join(f'<xhtml:link rel="alternate" hreflang="{L[x]["html"]}" href="{SITE + lang_url(x, path)}"/>' for x in langs)
        for x in langs:
            rows.append(f'  <url><loc>{SITE + lang_url(x, path)}</loc><lastmod>{TODAY}</lastmod>{alts}</url>')
    (PUB / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" '
        'xmlns:xhtml="http://www.w3.org/1999/xhtml">\n' + "\n".join(rows) + "\n</urlset>\n", encoding="utf-8", newline="\n")
    return len(rows)


if __name__ == "__main__":
    counts = {}
    for lang in L:
        for path in PAGES[lang]:
            build(lang, path)
        counts[lang] = len(PAGES[lang])
    print("built", counts, "| sitemap urls:", sitemap())
    # Rebuild the search index (pip install "pagefind[bin]")
    import subprocess
    try:
        r = subprocess.run([sys.executable, "-m", "pagefind", "--site", str(PUB)], capture_output=True, text=True, check=True)
        print("search index:", " | ".join(l.strip() for l in r.stdout.splitlines() if "Indexed" in l and ("pages" in l or "languages" in l)))
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print("WARNING: search index not rebuilt. Install it with: pip install \"pagefind[bin]\"", e)
