const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8001";

async function handle(res) {
  if (!res.ok) {
    let detail = `發生錯誤 (${res.status})`;
    try {
      const data = await res.json();
      if (data && data.detail) detail = data.detail;
    } catch {
      // 忽略非 JSON 回應
    }
    throw new Error(detail);
  }
  return res.json();
}

export async function createJob(url) {
  const res = await fetch(`${API_BASE}/api/jobs`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url }),
  });
  return handle(res);
}

export async function getJob(jobId) {
  const res = await fetch(`${API_BASE}/api/jobs/${jobId}`);
  return handle(res);
}

export function trackUrl(videoId, track) {
  return `${API_BASE}/api/songs/${videoId}/audio/${track}`;
}

export function thumbnailUrl(videoId) {
  return `${API_BASE}/api/songs/${videoId}/thumbnail`;
}
