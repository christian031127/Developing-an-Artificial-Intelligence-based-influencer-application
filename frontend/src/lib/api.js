const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";
async function json(r){ if(!r.ok) throw new Error(`${r.status} ${r.statusText}`); return r.json(); }

const FRONTEND_SEED = [
  "AI tools for students","thesis writing tips","time management","note-taking apps","study motivation",
  "latest AI trends","blockchain news","startup ideas","green tech","digital marketing",
  "budget travel","hidden gems Europe","remote work lifestyle","coffee culture","local food experiences",
  "mental health awareness","sustainable fashion","personal branding","career change","work-life balance",
];

export const api = {
  health: () => fetch(`${BASE}/api/healthz`).then(json),
  getIdeas: () => fetch(`${BASE}/api/ideas`).then(json),
  getDrafts: () => fetch(`${BASE}/api/drafts`).then(json),
  getFeed: () => fetch(`${BASE}/api/feed`).then(json),

    deleteFeedPost: (id) =>
    fetch(`${BASE}/api/feed/${id}`, {
      method: "DELETE",
    }).then(json),


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

  agentCritique: (postId) =>
    fetch(`${BASE}/api/agent/critique/${postId}`, { method: "POST" }).then(json),
  agentGet: (postId) =>
    fetch(`${BASE}/api/agent/insights/${postId}`).then(json),
  agentApply: (postId) =>
    fetch(`${BASE}/api/agent/apply/${postId}`, { method: "POST" }).then(json),

  getAnalytics: () => fetch(`${BASE}/api/analytics`).then(json),

  // (Régi characters végpontok maradhatnak érintetlenül, de nem használjuk)
  getCharacters: () => fetch(`${BASE}/api/characters`).then(json),
  createCharacter: (formData) => fetch(`${BASE}/api/characters`, { method: "POST", body: formData }).then(json),
  updateCharacter: (id, patch) =>
    fetch(`${BASE}/api/characters/${id}`, { method: "PATCH", headers: { "Content-Type": "application/json" }, body: JSON.stringify(patch) }).then(json),
  deleteCharacter: (id) => fetch(`${BASE}/api/characters/${id}`, { method: "DELETE" }).then(json),

  // 🔧 NORMALIZÁLT trends: mindig { keywords: string[] }-t adunk vissza
  async getTrends({ geo = "HU", window = "90d" } = {}) {
    // 1) query param verzió
    try {
      const r = await fetch(`${BASE}/api/trends?geo=${encodeURIComponent(geo)}&window=${encodeURIComponent(window)}`);
      if (r.ok) {
        const d = await r.json();
        const arr = Array.isArray(d.keywords) ? d.keywords : [];
        if (arr.length) return { keywords: arr };
      }
    } catch (e) {
      console.debug("trends (query) failed:", e);
    }

    // 2) path param verzió
    try {
      const r = await fetch(`${BASE}/api/trends/${encodeURIComponent(geo)}/${encodeURIComponent(window)}`);
      if (r.ok) {
        const d = await r.json();
        const arr = Array.isArray(d.keywords) ? d.keywords : [];
        if (arr.length) return { keywords: arr };
      }
    } catch (e) {
      console.debug("trends (path) failed:", e);
    }

    // 3) végső fallback – sose legyen üres a UI
    console.warn("Using frontend seed trends fallback.");
    return { keywords: FRONTEND_SEED.slice(0, 20) };
  },

  getPersonas: () => fetch(`${BASE}/api/personas`).then(json),
  createPersona: (formData) => fetch(`${BASE}/api/personas`, { method:"POST", body: formData }).then(json),
  updatePersona: (id, patch) => fetch(`${BASE}/api/personas/${id}`, { method:"PATCH", headers:{ "Content-Type":"application/json" }, body: JSON.stringify(patch) }).then(json),
  deletePersona: (id) => fetch(`${BASE}/api/personas/${id}`, { method:"DELETE" }).then(json),

  // 🔒 Persona kötelező a draft generálásához – ha nincs, hibát dobunk
  createDraftsFromKeywords: async ({ keywords = [], customText = "", personaId = ""}) => {
    if (!personaId) throw new Error("personaId is required to generate drafts");
    const payloads = keywords.map((kw) => ({
      ideaId: null,
      title: kw,
      category: "lifestyle",
      caption: "",
      hashtags: [],
      customText,
      personaId,
    }));
    await Promise.all(
      payloads.map((p) =>
        fetch(`${BASE}/api/drafts`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(p),
        }).then(async (r) => {
          if (!r.ok) {
            const msg = await r.text().catch(()=>`${r.status} ${r.statusText}`);
            throw new Error(msg);
          }
        })
      )
    );
  },
};
