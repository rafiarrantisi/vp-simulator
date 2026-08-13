// functions/api/[[path]].ts — proxy /api/* ke backend FastAPI via Cloudflare Tunnel
const BACKEND = "https://back-mounts-learn-aspects.trycloudflare.com"; // quick tunnel; ganti ke api.qoramedical.com saat named tunnel

export async function onRequest(context: { request: Request }): Promise<Response> {
  const url = new URL(context.request.url);
  const target = `${BACKEND}${url.pathname}${url.search}`;
  const body =
    context.request.method === "GET" || context.request.method === "HEAD"
      ? undefined
      : await context.request.arrayBuffer();
  const upstream = await fetch(target, {
    method: context.request.method,
    headers: context.request.headers,
    body,
  });
  const headers = new Headers(upstream.headers);
  headers.delete("content-encoding");
  headers.set("Cache-Control", "no-store"); // API responses never cached (auth/session data)
  return new Response(upstream.body, { status: upstream.status, headers });
}
