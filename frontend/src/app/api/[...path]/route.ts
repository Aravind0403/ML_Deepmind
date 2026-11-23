import { NextRequest, NextResponse } from "next/server";

const getBackendUrl = () => process.env.INTERNAL_API_URL || "http://backend:8000";

async function proxy(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  const { path } = await params;
  const backendBase = getBackendUrl();
  const search = request.nextUrl.search;
  const targetUrl = `${backendBase}/api/${path.join("/")}${search}`;

  const headers = new Headers(request.headers);
  headers.delete("host");

  const body = ["GET", "HEAD"].includes(request.method)
    ? undefined
    : await request.arrayBuffer();

  try {
    const res = await fetch(targetUrl, {
      method: request.method,
      headers,
      body,
    });

    const responseHeaders = new Headers(res.headers);
    return new NextResponse(res.body, {
      status: res.status,
      headers: responseHeaders,
    });
  } catch (err: any) {
    return NextResponse.json(
      { error: `Backend proxy error: ${err.message}` },
      { status: 502 }
    );
  }
}

export const GET = proxy;
export const POST = proxy;
export const PUT = proxy;
export const DELETE = proxy;
export const PATCH = proxy;
