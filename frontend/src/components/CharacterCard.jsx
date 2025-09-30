import { useState } from "react";
import { api } from "../lib/api";

export default function CharacterCard({ c, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(c.name);
  const [saving, setSaving] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const save = async () => {
    setSaving(true);
    try {
      await api.updateCharacter(c.id, { name: name.trim() });
      setEditing(false);
      onChanged?.();
    } finally { setSaving(false); }
  };

  const del = async () => {
    if (!confirm("Delete this character?")) return;
    setDeleting(true);
    try {
      await api.deleteCharacter(c.id);
      onChanged?.();
    } finally { setDeleting(false); }
  };

  return (
    <div className="card overflow-hidden">
      <img src={c.imageUrl} alt={c.name} className="w-full aspect-square object-cover" />
      <div className="card-pad space-y-2">
        {editing ? (
          <input
            className="w-full rounded-xl border border-gray-200 p-2 text-sm"
            value={name}
            onChange={(e)=>setName(e.target.value)}
          />
        ) : (
          <div className="font-semibold">{c.name}</div>
        )}
        <div className="text-xs text-gray-500">
          {c.personaId ? `Persona: ${c.personaId}` : "No persona"}
        </div>
        <div className="flex gap-2">
          {editing ? (
            <>
              <button onClick={save} disabled={saving} className="btn btn-sm btn-primary">
                {saving ? "Saving…" : "Save"}
              </button>
              <button onClick={()=>{ setEditing(false); setName(c.name); }} className="btn btn-sm btn-ghost">
                Cancel
              </button>
            </>
          ) : (
            <button onClick={()=>setEditing(true)} className="btn btn-sm btn-ghost">Rename</button>
          )}
          <button onClick={del} disabled={deleting} className="btn btn-sm btn-danger">
            {deleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}
