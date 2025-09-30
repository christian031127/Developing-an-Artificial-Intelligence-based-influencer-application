import { useEffect, useState } from "react";
import { api } from "../lib/api";
import PersonaCard from "../components/PersonaCard";

export default function Personas() {
  const [tab, setTab] = useState("create"); // "my" | "create"
  const [list, setList] = useState([]);

  // create form
  const [name, setName] = useState("");
  const [brand, setBrand] = useState("");
  const [wm, setWm] = useState("");
  const [tone, setTone] = useState("");
  const [style, setStyle] = useState("");
  const [file, setFile] = useState(null);
  const [busy, setBusy] = useState(false);

  const refresh = () => api.getPersonas().then(setList).catch(()=>setList([]));
  useEffect(() => { refresh(); }, []);

  const onSubmit = async (e) => {
    e.preventDefault();
    if (!file || !name.trim()) return;
    setBusy(true);
    try {
      const fd = new FormData();
      fd.append("name", name.trim());
      if (brand) fd.append("brand_tag", brand.trim());
      if (wm) fd.append("watermark", wm.trim());
      if (tone) fd.append("tone", tone.trim());
      if (style) fd.append("default_image_style", style);
      fd.append("file", file);
      await api.createPersona(fd);
      setName(""); setBrand(""); setWm(""); setTone(""); setStyle(""); setFile(null);
      setTab("my");
      refresh();
    } finally { setBusy(false); }
  };

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Personas</h1>
        <div className="flex gap-2">
          <button onClick={()=>setTab("my")} className={`btn btn-sm ${tab==="my"?"btn-primary":"btn-ghost"}`}>My personas</button>
          <button onClick={()=>setTab("create")} className={`btn btn-sm ${tab==="create"?"btn-primary":"btn-ghost"}`}>Create persona</button>
        </div>
      </div>

      {tab === "create" ? (
        <div className="card">
          <form onSubmit={onSubmit} className="card-pad space-y-4">
            <div>
              <div className="text-sm font-medium mb-1">Name</div>
              <input className="w-full rounded-xl border p-2 text-sm" value={name} onChange={e=>setName(e.target.value)} placeholder="e.g., Maya" />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <div className="text-sm font-medium mb-1">brand_tag (optional)</div>
                <input className="w-full rounded-xl border p-2 text-sm" value={brand} onChange={e=>setBrand(e.target.value)} placeholder="e.g., mybrand" />
              </div>
              <div>
                <div className="text-sm font-medium mb-1">watermark (optional)</div>
                <input className="w-full rounded-xl border p-2 text-sm" value={wm} onChange={e=>setWm(e.target.value)} placeholder="e.g., Maya • Studio" />
              </div>
              <div>
                <div className="text-sm font-medium mb-1">tone (optional)</div>
                <input className="w-full rounded-xl border p-2 text-sm" value={tone} onChange={e=>setTone(e.target.value)} placeholder="e.g., friendly, concise" />
              </div>
              <div>
                <div className="text-sm font-medium mb-1">default image style (optional)</div>
                <select className="w-full rounded-xl border p-2 text-sm" value={style} onChange={e=>setStyle(e.target.value)}>
                  <option value="">(none)</option>
                  <option value="clean">clean</option>
                  <option value="gradient">gradient</option>
                  <option value="polaroid">polaroid</option>
                </select>
              </div>
            </div>

            <div>
              <div className="text-sm font-medium mb-1">Portrait image</div>
              <input type="file" accept="image/png,image/jpeg,image/webp" onChange={e=>setFile(e.target.files?.[0] || null)} />
              <div className="text-xs text-gray-500 mt-1">Accepted: PNG/JPG/WebP</div>
            </div>

            <div className="flex gap-2">
              <button disabled={busy || !file || !name.trim()} className="btn btn-md btn-primary disabled:opacity-50">{busy ? "Creating…" : "Create"}</button>
              <button type="button" onClick={()=>{ setName(""); setBrand(""); setWm(""); setTone(""); setStyle(""); setFile(null); }} className="btn btn-md btn-ghost">Reset</button>
            </div>
          </form>
        </div>
      ) : (
        <>
          {list.length === 0 ? (
            <div className="card card-pad text-sm text-gray-500">No personas yet. Create one to see it here.</div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {list.map(p => <PersonaCard key={p.id} p={p} onChanged={refresh} />)}
            </div>
          )}
        </>
      )}
    </div>
  );
}
