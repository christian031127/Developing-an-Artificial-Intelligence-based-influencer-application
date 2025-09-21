import { cacheBust } from "../lib/format";
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
  const exportZip = () => api.exportDraft(d.id);
  const regenCap = async () => {
    setWorkingId(d.id);
    try { await api.regenCaption(d.id); refresh(); } finally { setWorkingId(null); }
  };

  return (
    <div className="card">
      <div className="card-pad">
        <div className="text-xs uppercase text-gray-500">{d.category}</div>
        <div className="font-semibold truncate">{d.title}</div>
      </div>

      {/* Instagram-like preview */}
      {d.previewUrl && (
        <div className="insta">
          <div className="insta-header">
            <div className="insta-avatar" />
            <div className="insta-username">fit_ai • Following</div>
          </div>
          <img
            key={d.filename || d.previewUrl}
            src={cacheBust(d.previewUrl)}
            alt={d.title || "preview"}
            className="insta-img"
            onError={(e) => { e.currentTarget.style.objectFit = "contain"; e.currentTarget.style.background = "#222"; }}
          />
          <div className="insta-actions">
            <span>♡</span><span>💬</span><span>↗</span>
          </div>
          <div className="insta-body">
            {d.caption ? <p className="mb-1">{d.caption}</p> : null}
            {d.hashtags?.length ? (
              <p className="text-xs text-gray-600">{d.hashtags.map(h => `#${h}`).join(" ")}</p>
            ) : null}
          </div>
        </div>
      )}

      <div className="card-pad flex flex-wrap gap-2">
        {d.status === "draft" && (
          <button onClick={approve} disabled={workingId === d.id} className="btn btn-sm btn-primary disabled:opacity-50">
            {workingId === d.id ? "Working..." : "Approve"}
          </button>
        )}
        <button onClick={regenCap} disabled={workingId === d.id} className="btn btn-sm btn-ghost disabled:opacity-50">
          {workingId === d.id ? "Working..." : "Regenerate caption"}
        </button>
        <button onClick={exportZip} className="btn btn-sm btn-ghost">Export ZIP</button>
        <button onClick={del} disabled={workingId === d.id} className="btn btn-sm btn-danger disabled:opacity-50">
          {workingId === d.id ? "Working..." : "Delete"}
        </button>
      </div>
    </div>
  );
}
