import { useEffect, useState } from "react";
import { api } from "../lib/api";
import IdeaCard from "../components/IdeaCard";
import DraftCard from "../components/DraftCard";
import EmptyState from "../components/EmptyState";
import TrendChips from "../components/TrendChips";

export default function Dashboard({ health }) {
  const [ideas, setIdeas] = useState([]);
  const [drafts, setDrafts] = useState([]);
  const [loadingIdeas, setLoadingIdeas] = useState(false);
  const [creatingId, setCreatingId] = useState(null);
  const [workingDraftId, setWorkingDraftId] = useState(null);

  // trends / selection
  const [trends, setTrends] = useState([]);
  const [selected, setSelected] = useState([]);
  const [customText, setCustomText] = useState("");
  const [genBusy, setGenBusy] = useState(false);

  // personas + image style
  const [personas, setPersonas] = useState([]);
  const [personaId, setPersonaId] = useState("");
  const [imageStyle, setImageStyle] = useState("clean"); // clean | gradient | polaroid

  const refreshDrafts = () => api.getDrafts().then(setDrafts).catch(() => setDrafts([]));

  useEffect(() => {
    refreshDrafts();
    api.getTrends({ geo: "HU", window: "90d" })
      .then((d) => setTrends(d.keywords || []))
      .catch(() => setTrends([]));
    api.getPersonas()
      .then(setPersonas)
      .catch(() => setPersonas([]));
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
        caption: "",
        hashtags: [],
        personaId,
        imageStyle,
      });
      refreshDrafts();
    } finally { setCreatingId(null); }
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
      await api.createDraftsFromKeywords({ keywords, customText, personaId, imageStyle });
      setSelected([]); setCustomText("");
      refreshDrafts();
    } finally { setGenBusy(false); }
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

      {/* Persona & Image Style */}
      <div className="card">
        <div className="card-pad grid grid-cols-1 md:grid-cols-3 gap-3 items-end">
          <div>
            <div className="text-sm font-medium mb-1">Persona</div>
            <select
              className="w-full rounded-xl border border-gray-200 p-2 text-sm"
              value={personaId}
              onChange={(e) => setPersonaId(e.target.value)}
            >
              <option value="">(None)</option>
              {personas.map(p => (
                <option key={p.id} value={p.id}>{p.name} — {p.id}</option>
              ))}
            </select>
          </div>
          <div>
            <div className="text-sm font-medium mb-1">Image style</div>
            <select
              className="w-full rounded-xl border border-gray-200 p-2 text-sm"
              value={imageStyle}
              onChange={(e) => setImageStyle(e.target.value)}
            >
              <option value="clean">clean</option>
              <option value="gradient">gradient</option>
              <option value="polaroid">polaroid</option>
            </select>
          </div>
          <div className="text-xs text-gray-500">
            Persona affects caption tone & watermark; Image style controls the composite preset.
          </div>
        </div>
      </div>

      {/* Trends & custom text */}
      <div className="card">
        <div className="card-pad space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="font-semibold">Trends & Keywords</div>
              <div className="text-sm text-gray-500">Pick trending keywords or type your own text, then generate drafts.</div>
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
