import { useEffect, useState } from "react";
import { api } from "../lib/api";
import CharacterCard from "../components/CharacterCard";

export default function Characters() {
  const [tab, setTab] = useState("my"); // "my" | "create"
  const [list, setList] = useState([]);
  const [personas, setPersonas] = useState([]);

  // create form
  const [name, setName] = useState("");
  const [personaId, setPersonaId] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => api.getCharacters().then(setList).catch(()=>setList([]));

  useEffect(() => {
    refresh();
    api.getPersonas().then(setPersonas).catch(()=>setPersonas([]));
  }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!file || !name.trim()) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("name", name.trim());
      if (personaId) fd.append("personaId", personaId);
      fd.append("file", file);
      await api.createCharacter(fd);
      setName(""); setPersonaId(""); setFile(null);
      setTab("my");
      refresh();
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Characters</h1>
        <div className="flex gap-2">
          <button onClick={()=>setTab("my")} className={`btn btn-sm ${tab==="my"?"btn-primary":"btn-ghost"}`}>My characters</button>
          <button onClick={()=>setTab("create")} className={`btn btn-sm ${tab==="create"?"btn-primary":"btn-ghost"}`}>Create character</button>
        </div>
      </div>

      {tab === "create" ? (
        <div className="card">
          <form onSubmit={onSubmit} className="card-pad space-y-4">
            <div>
              <div className="text-sm font-medium mb-1">Name</div>
              <input
                className="w-full rounded-xl border border-gray-200 p-2 text-sm"
                value={name}
                onChange={(e)=>setName(e.target.value)}
                placeholder="e.g., Maya"
              />
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Persona (optional)</div>
              <select
                className="w-full rounded-xl border border-gray-200 p-2 text-sm"
                value={personaId}
                onChange={(e)=>setPersonaId(e.target.value)}
              >
                <option value="">(None)</option>
                {personas.map(p => <option key={p.id} value={p.id}>{p.name} — {p.id}</option>)}
              </select>
            </div>
            <div>
              <div className="text-sm font-medium mb-1">Image file</div>
              <input
                type="file"
                accept="image/png,image/jpeg,image/webp"
                onChange={(e)=>setFile(e.target.files?.[0] || null)}
                className="block"
              />
              <div className="text-xs text-gray-500 mt-1">Accepted: PNG/JPG/WebP</div>
            </div>
            <div className="flex gap-2">
              <button disabled={busy || !file || !name.trim()} className="btn btn-md btn-primary disabled:opacity-50">
                {busy ? "Creating…" : "Create"}
              </button>
              <button type="button" onClick={()=>{ setName(""); setPersonaId(""); setFile(null); }} className="btn btn-md btn-ghost">
                Reset
              </button>
            </div>
          </form>
        </div>
      ) : (
        <>
          {list.length === 0 ? (
            <div className="card card-pad text-sm text-gray-500">No characters yet. Create one to see it here.</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {list.map(c => <CharacterCard key={c.id} c={c} onChanged={refresh} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
}
