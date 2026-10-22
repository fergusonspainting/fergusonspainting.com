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

function toBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.length; i += 0x8000) binary += String.fromCharCode(...bytes.subarray(i, i + 0x8000));
  return btoa(binary);
}

export async function handleQuote(request, env) {
  const wantsJson = (request.headers.get("Accept") || "").includes("application/json");
  const fail = (status, error) =>
    wantsJson
      ? Response.json({ ok: false, error }, { status })
      : new Response(`${error}\n\nPlease call (321) 202-7225.`, { status, headers: { "Content-Type": "text/plain; charset=utf-8" } });

  let form;
  try {
    form = await request.formData();
  } catch {
    return fail(400, "We couldn't read that form. Please try again.");
  }

  // Honeypot: real people never fill this in. Pretend success so bots learn nothing.
  if ((form.get("website") || "").toString().trim()) {
    return wantsJson ? Response.json({ ok: true }) : Response.redirect(new URL("/thanks/", request.url), 303);
  }

  const field = (k) => (form.get(k) || "").toString().trim().slice(0, LIMITS[k]);
  const data = Object.fromEntries(Object.keys(LIMITS).map((k) => [k, field(k)]));

  if (!data.name) return fail(400, "Add your name so we know who to ask for.");
  if (!data.phone && !data.email) return fail(400, "Add a phone number or an email so we can reach you.");
  if (data.email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)) return fail(400, "That email address doesn't look right. Check it and try again.");

  const photos = form.getAll("photos").filter((f) => typeof f === "object" && f.size > 0);
  if (photos.length > PHOTO_MAX_COUNT) return fail(400, `Attach up to ${PHOTO_MAX_COUNT} photos.`);
  let photoBytes = 0;
  for (const f of photos) {
    if (!PHOTO_TYPES.test(f.type || "")) return fail(400, `"${f.name}" isn't a photo. Attach JPG, PNG, HEIC or WebP images.`);
    if (f.size > PHOTO_MAX_BYTES) return fail(400, `"${f.name}" is over 8 MB. Attach a smaller photo.`);
    photoBytes += f.size;
  }
  if (photoBytes > PHOTO_MAX_TOTAL) return fail(400, "Those photos add up to more than 20 MB. Attach fewer or smaller photos.");

  // Turnstile
  const token = form.get("cf-turnstile-response");
  if (!token) return fail(400, "Complete the security check, then send again.");
  const verify = await fetch("https://challenges.cloudflare.com/turnstile/v0/siteverify", {
    method: "POST",
    body: new URLSearchParams({
      secret: env.TURNSTILE_SECRET || "",
      response: token.toString(),
      remoteip: request.headers.get("CF-Connecting-IP") || "",
    }),
  }).then((r) => r.json()).catch(() => ({ success: false }));
  if (!verify.success) return fail(400, "The security check didn't pass. Refresh the page and try again.");

  // Email via Resend
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
  const rows = [
    ["Name", data.name], ["Phone", data.phone], ["Email", data.email], ["City / address", data.city],
    ["Service", data.service], ["Preferred contact", data.contact_pref], ["Details", data.details],
    ["Gate code / access notes", data.access], ["Heard about us", data.heard],
    ["Photos", photos.length ? `${photos.length} attached` : ""],
  ];
  const html = `<h2>New quote request from fergusonspainting.com</h2><table cellpadding="6" style="border-collapse:collapse">${rows
    .map(([k, v]) => `<tr><th align="left" valign="top">${k}</th><td>${esc(v || "—").replace(/\n/g, "<br>")}</td></tr>`)
    .join("")}</table>`;
  const text = rows.map(([k, v]) => `${k}: ${v || "—"}`).join("\n");

  const email = {
    from: `Ferguson's Website <${env.QUOTE_FROM || "quotes@send.fergusonspainting.com"}>`,
    to: [env.QUOTE_TO || "derwin@fergusonspainting.com"],
    subject: `Quote request: ${data.service || "General"} – ${data.name}`,
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
    return fail(502, "Your request didn't send. Call (321) 202-7225 or email derwin@fergusonspainting.com.");
  }

  return wantsJson ? Response.json({ ok: true }) : Response.redirect(new URL("/thanks/", request.url), 303);
}
