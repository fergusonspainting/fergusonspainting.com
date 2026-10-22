// POST /api/quote — quote request form handler (called from src/worker.js)
// Env (Worker > Settings > Variables and Secrets):
//   TURNSTILE_SECRET  Cloudflare Turnstile secret key
//   RESEND_API_KEY    Resend API key (sending access only)
//   QUOTE_TO          optional, defaults to derwin@fergusonspainting.com
//   QUOTE_FROM        optional, defaults to quotes@send.fergusonspainting.com

const LIMITS = { name: 100, phone: 30, email: 200, city: 200, service: 60, details: 4000, contact_pref: 10, access: 300, heard: 60 };

// Photos ride along as email attachments (Resend caps a whole email at 40 MB).
const PHOTO_MAX_COUNT = 5;
const PHOTO_MAX_BYTES = 8 * 1024 * 1024;
const PHOTO_MAX_TOTAL = 20 * 1024 * 1024;
const PHOTO_TYPES = /^image\/(jpeg|png|webp|heic|heif|gif)$/;

// Customer-facing messages per site language. The email to Derwin is always English.
const LANGS = {
  en: { name: "English", thanks: "/thanks/" },
  es: { name: "Spanish", thanks: "/es/thanks/" },
  pt: { name: "Portuguese (Brazil)", thanks: "/pt-br/thanks/" },
};
const MSG = {
  unreadable: { en: "We couldn't read that form. Please try again.", es: "No pudimos leer el formulario. Intente de nuevo.", pt: "Não conseguimos ler o formulário. Tente novamente." },
  name: { en: "Add your name so we know who to ask for.", es: "Agregue su nombre para saber por quién preguntar.", pt: "Informe seu nome para sabermos com quem falar." },
  contact: { en: "Add a phone number or an email so we can reach you.", es: "Agregue un teléfono o un email para poder comunicarnos con usted.", pt: "Informe um telefone ou e-mail para entrarmos em contato." },
  email: { en: "That email address doesn't look right. Check it and try again.", es: "Ese email no parece correcto. Revíselo e intente de nuevo.", pt: "Esse e-mail não parece correto. Confira e tente novamente." },
  count: { en: `Attach up to ${PHOTO_MAX_COUNT} photos.`, es: `Adjunte hasta ${PHOTO_MAX_COUNT} fotos.`, pt: `Anexe até ${PHOTO_MAX_COUNT} fotos.` },
  type: { en: (n) => `"${n}" isn't a photo. Attach JPG, PNG, HEIC or WebP images.`, es: (n) => `"${n}" no es una foto. Adjunte imágenes JPG, PNG, HEIC o WebP.`, pt: (n) => `"${n}" não é uma foto. Anexe imagens JPG, PNG, HEIC ou WebP.` },
  big: { en: (n) => `"${n}" is over 8 MB. Attach a smaller photo.`, es: (n) => `"${n}" pesa más de 8 MB. Adjunte una foto más pequeña.`, pt: (n) => `"${n}" tem mais de 8 MB. Anexe uma foto menor.` },
  total: { en: "Those photos add up to more than 20 MB. Attach fewer or smaller photos.", es: "Las fotos suman más de 20 MB. Adjunte menos fotos o más pequeñas.", pt: "As fotos somam mais de 20 MB. Anexe menos fotos ou fotos menores." },
  token: { en: "Complete the security check, then send again.", es: "Complete la verificación de seguridad y envíe de nuevo.", pt: "Conclua a verificação de segurança e envie novamente." },
  verify: { en: "The security check didn't pass. Refresh the page and try again.", es: "La verificación de seguridad no pasó. Actualice la página e intente de nuevo.", pt: "A verificação de segurança falhou. Atualize a página e tente novamente." },
  send: { en: "Your request didn't send. Call (321) 202-7225 or email derwin@fergusonspainting.com.", es: "Su solicitud no se envió. Llame al (321) 202-7225 o escriba a derwin@fergusonspainting.com.", pt: "Sua solicitação não foi enviada. Ligue para (321) 202-7225 ou escreva para derwin@fergusonspainting.com." },
  call: { en: "Please call (321) 202-7225.", es: "Llame al (321) 202-7225.", pt: "Ligue para (321) 202-7225." },
};

// Confirmation sent to the customer (if they gave an email). It deliberately repeats nothing the customer typed,
// so the form can't be used to send someone else arbitrary text. Turn off with env CONFIRM_EMAIL = "off".
const CONFIRM = {
  en: {
    subject: "We got your request – Ferguson's Painting & Cleaning",
    lines: [
      "Hello,",
      "Thank you for contacting Ferguson's Painting & Cleaning. Your quote request (and any photos) reached Derwin.",
      "What happens next: within one business day (we're open 24 hours, Monday–Saturday), Derwin will reach you the way you asked: a call, a text or an email. Requests sent on a Sunday get an answer Monday.",
      "Need us sooner? Call or text (321) 202-7225.",
      "If you didn't send this request, you can ignore this email.",
      "Ferguson's Painting & Cleaning, Inc. · fergusonspainting.com",
    ],
  },
  es: {
    subject: "Recibimos su solicitud – Ferguson's Painting & Cleaning",
    lines: [
      "Hola:",
      "Gracias por comunicarse con Ferguson's Painting & Cleaning. Su solicitud de cotización (y sus fotos, si las envió) le llegó a Derwin.",
      "Qué sigue: en un día hábil (atendemos las 24 horas, de lunes a sábado), Derwin se comunicará con usted como lo pidió: llamada, texto o email. Las solicitudes enviadas el domingo se contestan el lunes. Nuestro equipo responde en inglés.",
      "¿Lo necesita antes? Llame o envíe un texto al (321) 202-7225.",
      "Si usted no envió esta solicitud, puede ignorar este email.",
      "Ferguson's Painting & Cleaning, Inc. · fergusonspainting.com/es/",
    ],
  },
  pt: {
    subject: "Recebemos seu pedido – Ferguson's Painting & Cleaning",
    lines: [
      "Olá,",
      "Obrigado por entrar em contato com a Ferguson's Painting & Cleaning. Seu pedido de orçamento (e as fotos, se enviou) chegou ao Derwin.",
      "Próximos passos: em até um dia útil (atendemos 24 horas, de segunda a sábado), o Derwin vai entrar em contato do jeito que você pediu: ligação, mensagem de texto ou e-mail. Pedidos enviados no domingo são respondidos na segunda-feira. Nossa equipe responde em inglês.",
      "Precisa antes? Ligue ou mande uma mensagem para (321) 202-7225.",
      "Se você não enviou este pedido, pode ignorar este e-mail.",
      "Ferguson's Painting & Cleaning, Inc. · fergusonspainting.com/pt-br/",
    ],
  },
};

function toBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

export async function handleQuote(request, env) {
  const wantsJson = (request.headers.get("Accept") || "").includes("application/json");
  let lang = "en";
  const t = (key, arg) => {
    const m = MSG[key][lang] || MSG[key].en;
    return typeof m === "function" ? m(arg) : m;
  };
  const fail = (status, error) =>
    wantsJson
      ? Response.json({ ok: false, error }, { status })
      : new Response(`${error}\n\n${t("call")}`, { status, headers: { "Content-Type": "text/plain; charset=utf-8" } });
  const done = () => (wantsJson ? Response.json({ ok: true }) : Response.redirect(new URL(LANGS[lang].thanks, request.url), 303));

  let form;
  try {
    form = await request.formData();
  } catch {
    return fail(400, t("unreadable"));
  }
  const requested = (form.get("lang") || "").toString();
  if (LANGS[requested]) lang = requested;

  // Honeypot: real people never fill this in. Pretend success so bots learn nothing.
  if ((form.get("website") || "").toString().trim()) return done();

  const field = (k) => (form.get(k) || "").toString().trim().slice(0, LIMITS[k]);
  const data = Object.fromEntries(Object.keys(LIMITS).map((k) => [k, field(k)]));

  if (!data.name) return fail(400, t("name"));
  if (!data.phone && !data.email) return fail(400, t("contact"));
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) return fail(400, t("email"));

  const photos = form.getAll("photos").filter((f) => typeof f === "object" && f.size > 0);
  if (photos.length > PHOTO_MAX_COUNT) return fail(400, t("count"));
  let photoBytes = 0;
  for (const f of photos) {
    if (!PHOTO_TYPES.test(f.type || "")) return fail(400, t("type", f.name));
    if (f.size > PHOTO_MAX_BYTES) return fail(400, t("big", f.name));
    photoBytes += f.size;
  }
  if (photoBytes > PHOTO_MAX_TOTAL) return fail(400, t("total"));

  // Turnstile
  const token = form.get("cf-turnstile-response");
  if (!token) return fail(400, t("token"));
  const verify = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: new URLSearchParams({
      secret: env.TURNSTILE_SECRET || "",
      response: token.toString(),
      remoteip: request.headers.get("CF-Connecting-IP") || "",
    }),
  }).then((r) => r.json()).catch(() => ({ success: false }));
  if (!verify.success) return fail(400, t("verify"));

  // Email via Resend (always in English for Derwin; flags the customer's language)
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const rows = [
    ["Name", data.name], ["Phone", data.phone], ["Email", data.email], ["City / address", data.city],
    ["Service", data.service], ["Preferred contact", data.contact_pref], ["Details", data.details],
    ["Gate code / access notes", data.access], ["Heard about us", data.heard],
    ["Photos", photos.length ? `${photos.length} attached` : ""],
  ];
  if (lang !== "en") rows.unshift(["Language", `${LANGS[lang].name}: the customer used the ${LANGS[lang].name} site. Their message may be in ${LANGS[lang].name}.`]);
  const html = `<h2>New quote request from fergusonspainting.com</h2><table cellpadding="6" style="border-collapse:collapse">${rows
    .map(([k, v]) => `<tr><th align="left" valign="top">${k}</th><td>${esc(v || "—").replace(/\n/g, "<br>")}</td></tr>`)
    .join("")}</table>`;
  const text = rows.map(([k, v]) => `${k}: ${v || "—"}`).join("\n");

  const tag = lang === "en" ? "" : `[${lang.toUpperCase()}] `;
  const email = {
    from: `Ferguson's Website <${env.QUOTE_FROM || "quotes@send.fergusonspainting.com"}>`,
    to: [env.QUOTE_TO || "derwin@fergusonspainting.com"],
    subject: `${tag}Quote request: ${data.service || "General"} – ${data.name}`,
    html,
    text,
  };
  if (data.email) email.reply_to = data.email;
  if (photos.length) {
    email.attachments = await Promise.all(
      photos.map(async (f, i) => ({ filename: f.name || `photo-${i + 1}.jpg`, content: toBase64(await f.arrayBuffer()) })),
    );
  }

  const sent = await fetch("https://api.resend.com/emails", {
    method: "POST",
    headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify(email),
  }).catch(() => null);

  if (!sent || !sent.ok) {
    console.error("Resend failed", sent && sent.status, sent && (await sent.text()));
    return fail(502, t("send"));
  }

  // Confirmation to the customer. A failure here never fails the request: Derwin already has it.
  if (data.email && env.CONFIRM_EMAIL !== "off") {
    const c = CONFIRM[lang];
    const confirm = {
      from: `Ferguson's Painting & Cleaning <${env.QUOTE_FROM || "quotes@send.fergusonspainting.com"}>`,
      to: [data.email],
      reply_to: env.QUOTE_TO || "derwin@fergusonspainting.com",
      subject: c.subject,
      text: c.lines.join("\n\n"),
      html: c.lines.map((l) => `<p>${esc(l)}</p>`).join(""),
    };
    const ok = await fetch("https://api.resend.com/emails", {
      method: "POST",
      headers: { Authorization: `Bearer ${env.RESEND_API_KEY}`, "Content-Type": "application/json" },
      body: JSON.stringify(confirm),
    }).catch(() => null);
    if (!ok || !ok.ok) console.error("Confirmation email failed", ok && ok.status);
  }

  return done();
}
