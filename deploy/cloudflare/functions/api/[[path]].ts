// functions/api/[[path]].ts — proxy /api/* ke backend FastAPI via Cloudflare Tunnel
// Retry 530 (same-zone subrequest loop-protection) — request tidak pernah sampai
// backend saat 530, jadi aman di-retry untuk semua method.
const BACKEND = "https://api.qoramedical.com"; // named tunnel -> VPS FastAPI :8000

async function fetchWithRetry(url: string, init: RequestInit): Promise<Response> {
  let last: Response | null = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      const res = await fetch(url, init);
      if (res.status !== 530 && !(res.status >= 500 && ["GET", "HEAD"].includes(init.method || "GET"))) {
        return res;
      }
      last = res;
    } catch (e) {
      last = null;
      if (attempt === 2) throw e;
    }
    await new Promise((r) => setTimeout(r, 150 * (attempt + 1)));
  }
  return last!;
}

export async function onRequest(context: { request: Request }): Promise<Response> {
  const url = new URL(context.request.url);
  const target = `${BACKEND}${url.pathname}${url.search}`;
  const body =
    context.request.method === "GET" || context.request.method === "HEAD"
      ? undefined
      : await context.request.arrayBuffer();
  const upstream = await fetchWithRetry(target, {
    method: context.request.method,
    headers: context.request.headers,
    body,
  });
  const headers = new Headers(upstream.headers);
  headers.delete("content-encoding");
  headers.set("Cache-Control", "no-store"); // API responses never cached (auth/session data)
  return new Response(upstream.body, { status: upstream.status, headers });
}
