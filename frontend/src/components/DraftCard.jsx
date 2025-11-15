import { api } from "../lib/api";

export default function DraftCard({ d, workingId, setWorkingId, refresh }) {
  const approve = async () => {
    setWorkingId(d.id);
    try { await api.approveDraft(d.id); refresh(); } finally { setWorkingId(null); }
  };

  const del = async () => {
    setWorkingId(d.id);
    try { await api.deleteDraft(d.id); refresh(); } finally { setWorkingId(null); }
  };

  const regenCap = async () => {
    setWorkingId(d.id);
    try { await api.regenCaption(d.id); refresh(); } finally { setWorkingId(null); }
  };

  const busy = workingId === d.id;

  return (
    <div className="card">
      <div className="card-pad flex items-center justify-between gap-3">
        <div className="font-semibold truncate">{d.title}</div>
        {d.category ? (
          <span className="px-2 py-0.5 rounded-full text-xs border border-gray-300 text-gray-700 bg-white whitespace-nowrap">
            {d.category}
          </span>
        ) : null}
      </div>

      {/* Instagram mock */}
      {d.previewUrl && (
        <div className="insta">
          <div className="insta-header">
            <div className="insta-avatar" />
            <div className="insta-username">Szakdolgozat</div>
          </div>

          <img
            key={d.filename || d.previewUrl}
            src={d.previewUrl}
            alt={d.title || "preview"}
            className="insta-img"
            style={{
              width: "100%",
              aspectRatio: "1 / 1",
              objectFit: "cover",
              display: "block",
            }}
            onError={(e) => {
              e.currentTarget.style.objectFit = "cover";
              e.currentTarget.style.background = "#222";
            }}
          />


          {/* Icons */}
          <div className="insta-actions flex items-center gap-3 px-3 py-2">
            <svg aria-label="Like" width="22" height="22" viewBox="0 0 24 24" className="fill-none stroke-2 stroke-gray-800">
              <path d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.6l-1-1a5.5 5.5 0 0 0-7.8 7.8l1 1L12 22l7.8-8.6 1-1a5.5 5.5 0 0 0 0-7.8Z" stroke="currentColor" fill="none" />
            </svg>
            <svg aria-label="Comment" width="22" height="22" viewBox="0 0 24 24" className="fill-none stroke-2 stroke-gray-800">
              <path d="M21 12a8.5 8.5 0 0 1-8.5 8.5H12a8.6 8.6 0 0 1-3.8-.9L3 21l1.4-4.8A8.5 8.5 0 1 1 21 12Z" stroke="currentColor" fill="none" />
            </svg>
            <svg aria-label="Share" width="22" height="22" viewBox="0 0 24 24" className="fill-none stroke-2 stroke-gray-800">
              <path d="M4 12l15-7-4 14-3-6-8-1z" stroke="currentColor" fill="none" />
            </svg>
          </div>

          <div className="insta-body">
            {d.caption ? <p className="mb-1">{d.caption}</p> : null}
            {d.hashtags?.length ? (
              <p className="text-xs text-gray-600">{d.hashtags.map(h => `#${h}`).join(" ")}</p>
            ) : null}
          </div>
        </div>
      )}

      {/* Actions */}
      <div className="card-pad flex flex-wrap gap-2 items-center">
        {d.status === "draft" && (
          <button onClick={approve} disabled={busy} className="btn btn-sm btn-primary disabled:opacity-50">
            {busy ? "Working…" : "Approve"}
          </button>
        )}
        <button onClick={regenCap} disabled={busy} className="btn btn-sm btn-ghost disabled:opacity-50">
          {busy ? "Working…" : "Regenerate caption"}
        </button>
        <button onClick={del} disabled={busy} className="btn btn-sm btn-danger disabled:opacity-50">
          {busy ? "Working…" : "Delete"}
        </button>

      </div>
    </div>
  );
}
