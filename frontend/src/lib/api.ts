export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiFetch<T = any>(
  path: string,
  options?: RequestInit
): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers || {}),
    },
    cache: "no-store",
  });
  if (!res.ok) {
    let msg = `API Error ${res.status}`;
    try {
      const err = await res.json();
      msg = err.detail || JSON.stringify(err);
    } catch {
      msg = await res.text();
    }
    throw new Error(msg);
  }
  return res.json();
}
