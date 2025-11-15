import { useEffect, useState } from "react";
import { api } from "../lib/api";
import PersonaCard from "../components/PersonaCard";

export default function Personas() {
  const [tab, setTab] = useState("my"); // "my" | "create"
  const [list, setList] = useState([]);

  // --- Form fields ---
  const [name, setName] = useState("");
  const [identity, setIdentity] = useState("");
  const [style, setStyle] = useState("photo_realistic");
  const [mood, setMood] = useState("neutral");
  const [bg, setBg] = useState("studio_gray");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => api.getPersonas().then(setList).catch(() => setList([]));
  useEffect(() => { refresh(); }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!name.trim()) return;
    if (!file) { alert("Please upload a portrait image."); return; }
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("name", name.trim());
      if (identity) fd.append("identity_hint", identity.trim());
      fd.append("style", style);
      fd.append("mood", mood);
      fd.append("bg", bg);
      fd.append("file", file);
      await api.createPersona(fd);

      setName("");
      setIdentity("");
      setStyle("photo_realistic");
      setMood("neutral");
      setBg("studio_gray");
      setFile(null);

      setTab("my");
      refresh();
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* HEADER */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Personas</h1>
        <div className="flex gap-2">
          <button
            onClick={() => setTab("my")}
            className={`btn btn-sm ${tab === "my" ? "btn-primary" : "btn-ghost"}`}
          >
            My personas
          </button>
          <button
            onClick={() => setTab("create")}
            className={`btn btn-sm ${tab === "create" ? "btn-primary" : "btn-ghost"}`}
          >
            Create new
          </button>
        </div>
      </div>

      {/* CREATE NEW */}
      {tab === "create" ? (
        <div className="card">
          <form onSubmit={onSubmit} className="card-pad space-y-4">

            <div>
              <div className="text-sm font-medium mb-1">Name</div>
              <input
                className="w-full rounded-xl border p-2 text-sm"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Maya"
              />
            </div>

            {/* META */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium mb-1">Identity hint (optional)</div>
                <input
                  className="w-full rounded-xl border p-2 text-sm"
                  value={identity}
                  onChange={(e) => setIdentity(e.target.value)}
                  placeholder='e.g. "female, 30s"'
                />
              </div>

              <div>
                <div className="text-sm font-medium mb-1">Style</div>
                <select
                  className="w-full rounded-xl border p-2 text-sm"
                  value={style}
                  onChange={(e) => setStyle(e.target.value)}
                >
                  <option value="photo_realistic">Photo realistic</option>
                  <option value="editorial">Editorial</option>
                  <option value="fitness">Fitness</option>
                  <option value="streetwear">Streetwear</option>
                  <option value="business_casual">Business casual</option>
                </select>
              </div>

              <div>
                <div className="text-sm font-medium mb-1">Mood</div>
                <select
                  className="w-full rounded-xl border p-2 text-sm"
                  value={mood}
                  onChange={(e) => setMood(e.target.value)}
                >
                  <option value="neutral">Neutral</option>
                  <option value="friendly_smile">Friendly smile</option>
                  <option value="confident">Confident</option>
                  <option value="energetic">Energetic</option>
                </select>
              </div>

              <div>
                <div className="text-sm font-medium mb-1">Background</div>
                <select
                  className="w-full rounded-xl border p-2 text-sm"
                  value={bg}
                  onChange={(e) => setBg(e.target.value)}
                >
                  <option value="studio_gray">Studio gray</option>
                  <option value="soft_gradient">Soft gradient</option>
                  <option value="outdoor_urban">Outdoor urban</option>
                  <option value="indoor_minimal">Indoor minimal</option>
                </select>
              </div>
            </div>

            {/* PORTRAIT FILE */}
            <div>
              <div className="text-sm font-medium mb-1">Portrait image (required)</div>
              <input
                required
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e) => setFile(e.target.files?.[0] || null)}
              />
              <div className="text-xs text-gray-500 mt-1">
                Accepted formats: PNG / JPG / WebP
              </div>
            </div>

            <div className="flex gap-2">
              <button
                disabled={busy || !name.trim() || !file}
                className="btn btn-md btn-primary disabled:opacity-50"
              >
                {busy ? "Creating…" : "Create persona"}
              </button>
              <button
                type="button"
                onClick={() => {
                  setName("");
                  setIdentity("");
                  setStyle("photo_realistic");
                  setMood("neutral");
                  setBg("studio_gray");
                  setFile(null);
                }}
                className="btn btn-md btn-ghost"
              >
                Reset
              </button>
            </div>
          </form>
        </div>
      ) : (
        <>
          {list.length === 0 ? (
            <div className="card card-pad text-sm text-gray-500">
              No personas yet. Create your first one!
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {list.map((p) => (
                <PersonaCard key={p.id} p={p} onChanged={refresh} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  );
}
