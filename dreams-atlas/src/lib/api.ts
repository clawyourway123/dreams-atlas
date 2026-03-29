const API_URL = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000';
const API_KEY = process.env.NEXT_PUBLIC_API_KEY ?? '';

interface FetchOptions extends Omit<RequestInit, 'headers'> {
  headers?: Record<string, string>;
}

export async function apiFetch<T>(path: string, opts: FetchOptions = {}): Promise<T> {
  const { headers = {}, ...rest } = opts;
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }
  const res = await fetch(`${API_URL}${path}`, { headers, ...rest });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

export async function apiDownload(path: string): Promise<Blob> {
  const headers: Record<string, string> = {};
  if (API_KEY) {
    headers['Authorization'] = `Bearer ${API_KEY}`;
  }
  const res = await fetch(`${API_URL}${path}`, { headers });
  if (!res.ok) {
    throw new Error(`API ${res.status}: ${res.statusText}`);
  }
  return res.blob();
}
