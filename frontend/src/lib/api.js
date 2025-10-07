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

  updateDraft: (id, patch) =>
    fetch(`${BASE}/api/drafts/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(patch),
    }).then(json),

  approveDraft: (id) => fetch(`${BASE}/api/drafts/${id}/approve`, { method: "POST" }).then(json),
  deleteDraft: (id) => fetch(`${BASE}/api/drafts/${id}`, { method: "DELETE" }).then(json),

  getAnalytics: () => fetch(`${BASE}/api/analytics`).then(json),

  getCharacters: () => fetch(`${BASE}/api/characters`).then(json),
  createCharacter: (formData) => fetch(`${BASE}/api/characters`, { method: "POST", body: formData }).then(json),
  updateCharacter: (id, patch) =>
    fetch(`${BASE}/api/characters/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) }).then(json),
  deleteCharacter: (id) => fetch(`${BASE}/api/characters/${id}`, { method: "DELETE" }).then(json),

  getTrends: ({ geo = "HU", window = "90d", seed } = {}) => {
    const params = new URLSearchParams({ geo, window });
    if (seed && seed.length) params.set("seed", seed.join(","));
    return fetch(`${BASE}/api/trends?${params}`).then(json);
  },

  getPersonas: () => fetch(`${BASE}/api/personas`).then(json),
  createPersona: (formData) => fetch(`${BASE}/api/personas`, { method:"POST", body: formData }).then(json),
  updatePersona: (id, patch) => fetch(`${BASE}/api/personas/${id}`, { method:"PATCH", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(patch) }).then(json),
  deletePersona: (id) => fetch(`${BASE}/api/personas/${id}`, { method:"DELETE" }).then(json),

  createDraftsFromKeywords: async ({ keywords = [], customText = "", personaId = ""}) => {
    const payloads = keywords.map((kw) => ({
      ideaId: null,
      title: kw,
      category: "lifestyle",
      caption: "",
      hashtags: [],
      customText,
      personaId,
    }));
    await Promise.all(payloads.map((p) =>
      fetch(`${BASE}/api/drafts`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(p) })
    ));
  },
};
