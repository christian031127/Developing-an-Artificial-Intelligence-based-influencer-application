import { useState } from "react";
import { api } from "../lib/api";

const fmt = (n) => (typeof n === "number" ? n.toLocaleString("en-US") : "-");

export default function FeedStatsCard({ post, onRefresh }) {
  const m = post?.metrics || {};
  const agent = post?.agent;
  const [busy, setBusy] = useState(false);

  const analyze = async () => {
    setBusy(true);
    try {
      await api.agentCritique(post.id);
      await onRefresh?.();
    } finally { setBusy(false); }
  };

  const applyNext = async () => {
    setBusy(true);
    try {
      const res = await api.agentApply(post.id);
      if (res?.id) alert("New draft created from recommendations (with new image).");
    } finally { setBusy(false); }
  };

  return (
    <div className="card">
      <div className="card-pad space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold text-gray-700">Post Analytics</div>
            <div className="text-xs text-gray-500">Quick view</div>
          </div>
          {agent?.score != null && (
            <span className="text-xs px-2 py-1 rounded-full bg-indigo-50 border border-indigo-200 text-indigo-700">
              Score: {agent.score}/100
            </span>
          )}
        </div>

        {/* 4 KPI – egyszerű, jól olvasható kártyák */}
        <div className="grid grid-cols-2 gap-3">
          <div className="rounded-xl bg-white border p-3">
            <div className="text-xs text-gray-500">Impressions</div>
            <div className="text-lg font-semibold">{fmt(m.impressions)}</div>
          </div>
          <div className="rounded-xl bg-white border p-3">
            <div className="text-xs text-gray-500">Reach</div>
            <div className="text-lg font-semibold">{fmt(m.reach)}</div>
          </div>
          <div className="rounded-xl bg-white border p-3">
            <div className="text-xs text-gray-500">Likes</div>
            <div className="text-lg font-semibold">{fmt(m.likes)}</div>
          </div>
          <div className="rounded-xl bg-white border p-3">
            <div className="text-xs text-gray-500">Comments</div>
            <div className="text-lg font-semibold">{fmt(m.comments)}</div>
          </div>
        </div>

        {/* Agent panel */}
        <div className="rounded-xl bg-white border p-3 space-y-3">
          <div className="flex items-center justify-between">
            <div className="text-xs text-gray-500">Agent tips</div>
            <div className="flex gap-2">
              <button onClick={analyze} disabled={busy} className="btn btn-xs btn-primary disabled:opacity-50">
                {busy ? "Working…" : "Analyze now"}
              </button>
              <button onClick={applyNext} disabled={busy || !post?.agent} className="btn btn-xs btn-ghost disabled:opacity-50">
                Create next draft
              </button>
            </div>
          </div>

          {agent ? (
            <>
              {agent.insights?.length ? (
                <div>
                  <div className="text-xs font-medium mb-1">Insights</div>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {agent.insights.map((t, i) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
              ) : null}
              {agent.recommendations?.length ? (
                <div>
                  <div className="text-xs font-medium mb-1">Recommendations</div>
                  <ul className="list-disc pl-5 text-sm space-y-1">
                    {agent.recommendations.map((t, i) => <li key={i}>{t}</li>)}
                  </ul>
                </div>
              ) : null}
            </>
          ) : (
            <div className="text-xs text-gray-500">No tips yet. Click “Analyze now”.</div>
          )}
        </div>
      </div>
    </div>
  );
}
