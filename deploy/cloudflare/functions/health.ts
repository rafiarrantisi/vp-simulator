// functions/health.ts — proxy /health ke backend FastAPI via Cloudflare Tunnel
const BACKEND = "https://back-mounts-learn-aspects.trycloudflare.com"; // quick tunnel; ganti ke api.qoramedical.com saat named tunnel

export async function onRequest(context: { request: Request }): Promise<Response> {
  const target = `${BACKEND}/health`;
  const upstream = await fetch(target, {
    method: context.request.method,
    headers: context.request.headers,
  });
  const headers = new Headers(upstream.headers);
  headers.delete("content-encoding");
  headers.set("Cache-Control", "no-store");
  return new Response(upstream.body, { status: upstream.status, headers });
}
