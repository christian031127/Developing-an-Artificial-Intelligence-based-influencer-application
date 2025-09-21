const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
async function json(r){ if(!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.json(); }

export const api = {
  health: () => fetch(`${BASE}/api/healthz`).then(json),

  getIdeas: () => fetch(`${BASE}/api/ideas`).then(json),

  getDrafts: () => fetch(`${BASE}/api/drafts`).then(json),
  createDraft: (payload) =>
    fetch(`${BASE}/api/drafts`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    }).then(json),
  approveDraft: (id) =>
    fetch(`${BASE}/api/drafts/${id}/approve`, { method: "POST" }).then(json),
  deleteDraft: (id) =>
    fetch(`${BASE}/api/drafts/${id}`, { method: "DELETE" }).then(json),
  exportDraft: (id) => window.location.assign(`${BASE}/api/drafts/${id}/export`),
  regenCaption: (id) =>
    fetch(`${BASE}/api/drafts/${id}/regen_caption`, { method: "POST" }).then(json),

  // NEW: Trends
  getTrends: ({ geo = "HU", window = "90d", seed } = {}) => {
    const params = new URLSearchParams({ geo, window });
    if (seed && seed.length) params.set("seed", seed.join(","));
    return fetch(`${BASE}/api/trends?${params}`).then(json);
  },

  // NEW: batch create drafts from selected keywords (send customText now)
  createDraftsFromKeywords: async ({ keywords = [], customText = "" }) => {
    const payloads = keywords.map((kw) => ({
      ideaId: null,
      title: kw,
      category: "lifestyle",
      caption: "",
      hashtags: [],
      customText,             // now used by backend
    }));
    await Promise.all(
      payloads.map((p) =>
        fetch(`${BASE}/api/drafts`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(p),
        })
      )
    );
  },
};
