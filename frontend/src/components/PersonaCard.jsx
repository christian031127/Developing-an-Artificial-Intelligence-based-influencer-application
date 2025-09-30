import { useState } from "react";
import { api } from "../lib/api";

export default function PersonaCard({ p, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(p.name);
  const [brand, setBrand] = useState(p.brand_tag || "");
  const [wm, setWm] = useState(p.watermark || "");
  const [tone, setTone] = useState(p.tone || "");
  const [style, setStyle] = useState(p.default_image_style || "");
  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await api.updatePersona(p.id, {
        name: name.trim(),
        brand_tag: brand.trim() || null,
        watermark: wm.trim() || null,
        tone: tone.trim() || null,
        default_image_style: style || null,
      });
      setEditing(false);
      onChanged?.();
    } finally { setBusy(false); }
  };

  const del = async () => {
    if (!confirm("Delete this persona?")) return;
    setDeleting(true);
    try {
      await api.deletePersona(p.id);
      onChanged?.();
    } finally { setDeleting(false); }
  };

  return (
    <div className="card overflow-hidden">
      <img src={p.imageUrl} alt={p.name} className="w-full aspect-square object-cover" />
      <div className="card-pad space-y-3">
        {editing ? (
          <>
            <input className="w-full rounded-xl border p-2 text-sm" value={name} onChange={e=>setName(e.target.value)} />
            <input className="w-full rounded-xl border p-2 text-sm" placeholder="brand_tag (optional)" value={brand} onChange={e=>setBrand(e.target.value)} />
            <input className="w-full rounded-xl border p-2 text-sm" placeholder="watermark (optional)" value={wm} onChange={e=>setWm(e.target.value)} />
            <input className="w-full rounded-xl border p-2 text-sm" placeholder="tone (optional)" value={tone} onChange={e=>setTone(e.target.value)} />
            <select className="w-full rounded-xl border p-2 text-sm" value={style} onChange={e=>setStyle(e.target.value)}>
              <option value="">(no default)</option>
              <option value="clean">clean</option>
              <option value="gradient">gradient</option>
              <option value="polaroid">polaroid</option>
            </select>
          </>
        ) : (
          <>
            <div className="font-semibold">{p.name}</div>
            <div className="text-xs text-gray-500 space-y-1">
              <div>brand_tag: {p.brand_tag || "—"}</div>
              <div>watermark: {p.watermark || "—"}</div>
              <div>tone: {p.tone || "—"}</div>
              <div>default style: {p.default_image_style || "—"}</div>
            </div>
          </>
        )}

        <div className="flex gap-2">
          {editing ? (
            <>
              <button onClick={save} disabled={busy} className="btn btn-sm btn-primary">{busy ? "Saving…" : "Save"}</button>
              <button onClick={()=>{ setEditing(false); setName(p.name); setBrand(p.brand_tag||""); setWm(p.watermark||""); setTone(p.tone||""); setStyle(p.default_image_style||""); }} className="btn btn-sm btn-ghost">Cancel</button>
            </>
          ) : (
            <button onClick={()=>setEditing(true)} className="btn btn-sm btn-ghost">Edit</button>
          )}
          <button onClick={del} disabled={deleting} className="btn btn-sm btn-danger">{deleting ? "Deleting…" : "Delete"}</button>
        </div>
      </div>
    </div>
  );
}
