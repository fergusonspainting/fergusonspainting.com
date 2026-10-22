// Cloudflare Worker entry point. Static files in public/ are served by the
// assets binding; this script only runs for /api/* (see wrangler.jsonc).
import { handleQuote } from "./quote.js";

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);

    if (pathname === "/api/quote") {
      if (request.method === "POST") return handleQuote(request, env);
      return new Response("Method not allowed", { status: 405, headers: { Allow: "POST" } });
    }

    return env.ASSETS.fetch(request);
  },
};
