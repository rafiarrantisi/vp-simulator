// functions/health.ts — proxy /health ke backend FastAPI via Cloudflare Tunnel
const BACKEND = "https://api.qoramedical.com"; // named tunnel -> VPS FastAPI :8000

export async function onRequest(context: { request: Request }): Promise<Response> {
  let upstream: Response | null = null;
  for (let attempt = 0; attempt < 3; attempt++) {
    try {
      upstream = await fetch(`${BACKEND}/health`, {
        method: context.request.method,
        headers: context.request.headers,
      });
      if (upstream.status !== 530) break;
    } catch (e) {
      if (attempt === 2) throw e;
    }
    await new Promise((r) => setTimeout(r, 150 * (attempt + 1)));
  }
  const headers = new Headers(upstream!.headers);
  headers.delete("content-encoding");
  headers.set("Cache-Control", "no-store");
  return new Response(upstream!.body, { status: upstream!.status, headers });
}
