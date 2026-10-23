/* Google Analytics 4 (gtag.js). Loaded next to the async gtag script in <head>.
   Events: generate_lead (thanks page), call_click, sms_click, email_click. */
window.dataLayer = window.dataLayer || [];
function gtag() { dataLayer.push(arguments); }
gtag("js", new Date());
gtag("config", "G-DDY4TM97L3");

(function () {
  var path = location.pathname;
  var lang = path.indexOf("/es/") === 0 ? "es" : path.indexOf("/pt-br/") === 0 ? "pt" : path.indexOf("/zh/") === 0 ? "zh" : "en";
  if (/\/thanks\/$/.test(path)) {
    gtag("event", "generate_lead", { method: "quote_form", language: lang });
  }
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("a[href]");
    if (!a) return;
    var href = a.getAttribute("href") || "";
    var name = href.indexOf("tel:") === 0 ? "call_click"
      : href.indexOf("sms:") === 0 ? "sms_click"
      : href.indexOf("mailto:") === 0 ? "email_click" : "";
    if (name) gtag("event", name, { language: lang, link_text: (a.textContent || "").trim().slice(0, 60) });
  });
})();
