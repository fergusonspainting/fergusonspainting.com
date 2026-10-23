// Ferguson's Painting & Cleaning — small progressive enhancements. The site works without JS.

// Mobile menu
const toggle = document.querySelector(".nav-toggle");
const nav = document.getElementById("site-nav");
if (toggle && nav) {
  toggle.addEventListener("click", () => {
    const open = nav.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(open));
    toggle.textContent = open ? toggle.dataset.close || "Close" : toggle.dataset.menu || "Menu";
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && nav.classList.contains("is-open")) {
      nav.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
      toggle.textContent = toggle.dataset.menu || "Menu";
      toggle.focus();
    }
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
const MSG = {
  en: {
    contact: "Add a phone number or an email so we can reach you.",
    big: (n) => `"${n}" is over 8 MB. Attach a smaller photo.`,
    many: "Attach up to 5 photos, 20 MB total.",
    sending: "Sending…",
    send: "Send my quote request",
    failed: "Your request didn't go through. Call (321) 202-7225 or email derwin@fergusonspainting.com.",
    offline: "Your request didn't go through. Check your connection, or call (321) 202-7225.",
  },
  es: {
    contact: "Agregue un teléfono o un email para poder comunicarnos con usted.",
    big: (n) => `"${n}" pesa más de 8 MB. Adjunte una foto más pequeña.`,
    many: "Adjunte hasta 5 fotos, 20 MB en total.",
    sending: "Enviando…",
    send: null,
    failed: "Su solicitud no se envió. Llame al (321) 202-7225 o escriba a derwin@fergusonspainting.com.",
    offline: "Su solicitud no se envió. Revise su conexión o llame al (321) 202-7225.",
  },
  pt: {
    contact: "Informe um telefone ou e-mail para entrarmos em contato.",
    big: (n) => `"${n}" tem mais de 8 MB. Anexe uma foto menor.`,
    many: "Anexe até 5 fotos, 20 MB no total.",
    sending: "Enviando…",
    send: null,
    failed: "Sua solicitação não foi enviada. Ligue para (321) 202-7225 ou escreva para derwin@fergusonspainting.com.",
    offline: "Sua solicitação não foi enviada. Verifique sua conexão ou ligue para (321) 202-7225.",
  },
  zh: {
    contact: "请留下电话或邮箱，方便我们联系您。",
    big: (n) => `"${n}" 超过 8 MB，请换一张更小的照片。`,
    many: "最多可附上 5 张照片，总大小 20 MB。",
    sending: "正在发送…",
    send: null,
    failed: "您的请求未能发送。请致电 (321) 202-7225 或发邮件至 derwin@fergusonspainting.com。",
    offline: "您的请求未能发送。请检查网络连接，或致电 (321) 202-7225。",
  },
};
const form = document.querySelector("[data-quote-form]");
if (form) {
  const t = MSG[form.dataset.lang] || MSG.en;
  const status = form.querySelector(".form-status");
  const button = form.querySelector("button[type=submit]");
  const label = button.textContent;
  const show = (msg) => { status.textContent = msg; status.hidden = false; };

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!form.phone.value.trim() && !form.email.value.trim()) {
      show(t.contact);
      form.phone.focus();
      return;
    }
    const photos = form.photos ? [...form.photos.files] : [];
    const big = photos.find((f) => f.size > 8 * 1024 * 1024);
    if (photos.length > 5 || big || photos.reduce((n, f) => n + f.size, 0) > 20 * 1024 * 1024) {
      show(big ? t.big(big.name) : t.many);
      form.photos.focus();
      return;
    }
    button.disabled = true;
    button.textContent = t.sending;
    try {
      const res = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok && data.ok) {
        window.location.href = form.dataset.thanks || "/thanks/";
        return;
      }
      show(data.error || t.failed);
    } catch {
      show(t.offline);
    }
    if (window.turnstile) window.turnstile.reset();
    button.disabled = false;
    button.textContent = label;
  });
}

// Site search: Pagefind UI, loaded the first time the dialog opens
const searchDialog = document.querySelector(".search-dialog");
if (searchDialog && typeof searchDialog.showModal === "function") {
  let loaded = false;
  const load = () => {
    if (loaded) return;
    loaded = true;
    const css = document.createElement("link");
    css.rel = "stylesheet";
    css.href = "/pagefind/pagefind-ui.css";
    document.head.append(css);
    const script = document.createElement("script");
    script.src = "/pagefind/pagefind-ui.js";
    script.onload = () => {
      new PagefindUI({ element: "#site-search", showSubResults: true, showImages: false, resetStyles: false });
      searchDialog.querySelector("input")?.focus();
    };
    document.head.append(script);
  };
  document.querySelectorAll("[data-search-open]").forEach((b) =>
    b.addEventListener("click", () => {
      searchDialog.showModal();
      load();
      searchDialog.querySelector("input")?.focus();
    }),
  );
  searchDialog.querySelector("[data-search-close]").addEventListener("click", () => searchDialog.close());
  searchDialog.addEventListener("click", (e) => { if (e.target === searchDialog) searchDialog.close(); });
  document.addEventListener("keydown", (e) => {
    if (e.key === "/" && !/^(INPUT|TEXTAREA|SELECT)$/.test(document.activeElement.tagName)) {
      e.preventDefault();
      searchDialog.showModal();
      load();
    }
  });
}
