// Ferguson's Painting & Cleaning — small progressive enhancements. The site works without JS.

// Mobile menu
const toggle = document.querySelector(".nav-toggle");
const nav = document.getElementById("site-nav");
if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
    toggle.textContent = open ? "Close" : "Menu";
  });
}

// Gallery filter
const filters = document.querySelectorAll(".filters button");
const items = document.querySelectorAll("[data-gallery] [data-cat]");
filters.forEach((btn) => {
  btn.addEventListener("click", () => {
    const cat = btn.dataset.filter;
    filters.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
    items.forEach((el) => { el.hidden = cat !== "all" && el.dataset.cat !== cat; });
  });
});

// Gallery lightbox
const box = document.querySelector("dialog.lightbox");
if (box && typeof box.showModal === "function") {
  const boxImg = box.querySelector("img");
  const boxCap = box.querySelector("p");
  items.forEach((link) => {
    link.addEventListener("click", (e) => {
      e.preventDefault();
      boxImg.src = link.href;
      boxImg.alt = link.dataset.caption || "";
      boxCap.textContent = link.dataset.caption || "";
      box.showModal();
    });
  });
  box.querySelector("[data-close]").addEventListener("click", () => box.close());
  box.addEventListener("click", (e) => { if (e.target === box) box.close(); });
}

// Quote form: submit with fetch so errors show inline; falls back to a normal POST without JS
const form = document.querySelector("[data-quote-form]");
if (form) {
  const status = form.querySelector(".form-status");
  const button = form.querySelector("button[type=submit]");
  const show = (msg) => { status.textContent = msg; status.hidden = false; };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.phone.value.trim() && !form.email.value.trim()) {
      show("Add a phone number or an email so we can reach you.");
      form.phone.focus();
      return;
    }
    const photos = form.photos ? [...form.photos.files] : [];
    const big = photos.find((f) => f.size > 8 * 1024 * 1024);
    if (photos.length > 5 || big || photos.reduce((n, f) => n + f.size, 0) > 20 * 1024 * 1024) {
      show(big ? `"${big.name}" is over 8 MB. Attach a smaller photo.` : "Attach up to 5 photos, 20 MB total.");
      form.photos.focus();
      return;
    }
    button.disabled = true;
    button.textContent = "Sending…";
    try {
      const res = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        window.location.href = "/thanks/";
        return;
      }
      show(data.error || "Your request didn't go through. Call (321) 202-7225 or email derwin@fergusonspainting.com.");
    } catch {
      show("Your request didn't go through. Check your connection, or call (321) 202-7225.");
    }
    if (window.turnstile) window.turnstile.reset();
    button.disabled = false;
    button.textContent = "Send my quote request";
  });
}
