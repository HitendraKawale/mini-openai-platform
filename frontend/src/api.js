const BASE = "/api";

class ApiError extends Error {
  constructor(status, detail) {
    super(detail);
    this.status = status;
  }
}

async function request(path, { apiKey, ...options } = {}) {
  const headers = { ...(options.headers || {}) };
  if (apiKey) {
    headers["Authorization"] = `Bearer ${apiKey}`;
  }

  const response = await fetch(`${BASE}${path}`, { ...options, headers });

  let body = null;
  try {
    body = await response.json();
  } catch {
    // non-JSON error body
  }

  if (!response.ok) {
    const detail =
      (body && body.detail) || `Request failed with status ${response.status}`;
    throw new ApiError(response.status, detail);
  }

  return body;
}

export function getHealth() {
  return request("/health");
}

export function chatCompletion({ apiKey, content, model = "auto" }) {
  return request("/v1/chat/completions", {
    apiKey,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      model,
      messages: [{ role: "user", content }],
      max_tokens: 256,
    }),
  });
}

export function ragQuery({ apiKey, query, topK = 3 }) {
  return request("/v1/rag/query", {
    apiKey,
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, top_k: topK }),
  });
}

export function uploadDocument({ apiKey, file }) {
  const form = new FormData();
  form.append("file", file);
  return request("/v1/documents/upload", {
    apiKey,
    method: "POST",
    body: form,
  });
}
