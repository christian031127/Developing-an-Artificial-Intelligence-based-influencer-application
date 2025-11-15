import { useState } from "react";
import { api } from "../lib/api";

export default function PersonaCard({ p, onChanged }) {
  const [editing, setEditing] = useState(false);
  const [name, setName] = useState(p.name);
  const [identity, setIdentity] = useState(p.identity_hint || "");
  const [style, setStyle] = useState(p.style || "photo_realistic");
  const [mood, setMood] = useState(p.mood || "neutral");
  const [bg, setBg] = useState(p.bg || "studio_gray");

  const [busy, setBusy] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const save = async () => {
    setBusy(true);
    try {
      await api.updatePersona(p.id, {
        name: name.trim(),
        identity_hint: identity.trim() || null,
        style,
        mood,
        bg,
      });
      setEditing(false);
      onChanged?.();
    } finally {
      setBusy(false);
    }
  };

  const del = async () => {
    if (!confirm("Are you sure you want to delete this persona?")) return;
    setDeleting(true);
    try {
      await api.deletePersona(p.id);
      onChanged?.();
    } finally {
      setDeleting(false);
    }
  };

  return (
    <div className="card overflow-hidden">
      <img
        src={p.ref_image_url}
        alt={p.name}
        className="w-full aspect-square object-cover"
        onError={(e) => {
          e.currentTarget.style.objectFit = "contain";
          e.currentTarget.style.background = "#222";
        }}
      />

      <div className="card-pad space-y-3">
        {editing ? (
          <>
            <input
              className="w-full rounded-xl border p-2 text-sm"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Name"
            />

            <input
              className="w-full rounded-xl border p-2 text-sm"
              value={identity}
              onChange={(e) => setIdentity(e.target.value)}
              placeholder='Identity hint (e.g. "male, 20s")'
            />

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
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
          </>
        ) : (
          <>
            <div className="font-semibold">{p.name}</div>

            <div className="text-xs text-gray-500 space-y-1">
              <div><b>Identity hint:</b> {p.identity_hint || "—"}</div>
              <div><b>Style:</b> {p.style}</div>
              <div><b>Mood:</b> {p.mood}</div>
              <div><b>Background:</b> {p.bg}</div>
            </div>
          </>
        )}

        <div className="flex gap-2">
          {editing ? (
            <>
              <button onClick={save} disabled={busy} className="btn btn-sm btn-primary">
                {busy ? "Saving…" : "Save"}
              </button>
              <button
                onClick={() => {
                  setEditing(false);
                  setName(p.name);
                  setIdentity(p.identity_hint || "");
                  setStyle(p.style || "photo_realistic");
                  setMood(p.mood || "neutral");
                  setBg(p.bg || "studio_gray");
                }}
                className="btn btn-sm btn-ghost"
              >
                Cancel
              </button>
            </>
          ) : (
            <button onClick={() => setEditing(true)} className="btn btn-sm btn-ghost">
              Edit
            </button>
          )}

          <button onClick={del} disabled={deleting} className="btn btn-sm btn-danger">
            {deleting ? "Deleting…" : "Delete"}
          </button>
        </div>
      </div>
    </div>
  );
}
