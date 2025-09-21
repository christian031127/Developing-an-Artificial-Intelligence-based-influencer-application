import { useEffect, useState } from "react";
import { api } from "../lib/api";
import IdeaCard from "../components/IdeaCard";
import DraftCard from "../components/DraftCard";
import EmptyState from "../components/EmptyState";
import TrendChips from "../components/TrendChips";

// Mock trends for now (we'll replace with /api/trends later)
const MOCK_TRENDS = [
  "leg day", "glute workout", "protein breakfast", "meal prep",
  "active rest", "hypertrophy", "budgeting", "ETF", "dividends",
  "morning routine", "productivity", "deep work", "HIIT",
  "mobility", "gut health", "macro tracking", "mindset",
  "study hacks", "minimalism", "home workout"
];

export default function Dashboard({ health }) {
  const [ideas, setIdeas] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [creatingId, setCreatingId] = useState(null);
  const [workingDraftId, setWorkingDraftId] = useState(null);

  // NEW: trends/keywords input
  const [trends, setTrends] = useState(MOCK_TRENDS);
  const [selected, setSelected] = useState([]);
  const [customText, setCustomText] = useState("");
  const [genBusy, setGenBusy] = useState(false);

  const refreshDrafts = () => api.getDrafts().then(setDrafts).catch(() => setDrafts([]));
  useEffect(() => {
    // load drafts
    refreshDrafts();
    // load trends from backend
    api.getTrends({ geo: "HU", window: "90d" })
      .then((d) => setTrends(d.keywords || []))
      .catch(() => setTrends([]));
  }, []);

  const loadIdeas = async () => {
    setLoadingIdeas(true);
    try { setIdeas(await api.getIdeas()); } finally { setLoadingIdeas(false); }
  };

  const createDraftFromIdea = async (idea) => {
    setCreatingId(idea.id);
    try {
      await api.createDraft({
        ideaId: idea.id,
        title: idea.title,
        category: idea.category,
        caption: "",      // backend LLM fills
        hashtags: [],     // backend LLM fills
      });
      refreshDrafts();
    } finally {
      setCreatingId(null);
    }
  };

  const toggleTrend = (t) => {
    setSelected((prev) => (prev.includes(t) ? prev.filter(x => x !== t) : [...prev, t]));
  };

  const selectAll = () => setSelected(trends.slice(0, 20));
  const clearAll = () => setSelected([]);

  const generateFromKeywords = async () => {
    if (selected.length === 0 && !customText.trim()) return;
    setGenBusy(true);
    try {
      const keywords = selected.length ? selected : (customText.trim() ? [customText.trim()] : []);
      await api.createDraftsFromKeywords({ keywords, customText });
      setSelected([]);
      setCustomText("");
      refreshDrafts();
    } finally {
      setGenBusy(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold">Studio</h1>
          <p className="text-sm text-gray-500">Backend health: {health}</p>
        </div>
        <button onClick={loadIdeas} disabled={loadingIdeas} className="btn btn-md btn-primary disabled:opacity-50">
          {loadingIdeas ? "Loading ideas..." : "Load ideas"}
        </button>
      </div>

      {/* NEW: Trends & custom text */}
      <div className="card">
        <div className="card-pad space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">Trends & Keywords</div>
              <div className="text-sm text-gray-500">Pick some trending keywords or type your own text, then generate drafts.</div>
            </div>
            <div className="flex gap-2">
              <button onClick={selectAll} className="btn btn-sm btn-ghost">Select all</button>
              <button onClick={clearAll} className="btn btn-sm btn-ghost">Clear</button>
            </div>
          </div>

          <TrendChips trends={trends} selected={selected} onToggle={toggleTrend} />

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <textarea
              placeholder="Optional freeform text (tone, angle, notes)…"
              className="col-span-2 w-full rounded-xl border border-gray-200 p-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
              rows={3}
              value={customText}
              onChange={(e) => setCustomText(e.target.value)}
            />
            <div className="flex items-start gap-2">
              <button
                onClick={generateFromKeywords}
                disabled={genBusy}
                className="btn btn-md btn-primary disabled:opacity-50"
              >
                {genBusy ? "Generating…" : "Generate drafts"}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Ideas */}
      {ideas.length === 0 ? (
        <EmptyState
          title="No ideas yet"
          subtitle="Click 'Load ideas' or use Trends & Keywords above."
          action={null}
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {ideas.map((i) => (
            <IdeaCard key={i.id} idea={i} onCreate={createDraftFromIdea} busy={creatingId === i.id} />
          ))}
        </div>
      )}

      {/* Drafts */}
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Drafts</h2>
        <button onClick={refreshDrafts} className="btn btn-sm btn-ghost">Refresh</button>
      </div>

      {drafts.length === 0 ? (
        <EmptyState
          title="No drafts yet"
          subtitle="Generate a draft from trends or an idea to see it here."
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {drafts.map((d) => (
            <DraftCard
              key={d.id}
              d={d}
              workingId={workingDraftId}
              setWorkingId={setWorkingDraftId}
              refresh={refreshDrafts}
            />
          ))}
        </div>
      )}
    </div>
  );
}
