export default function IdeaCard({ idea, onCreate, busy }) {
  return (
    <div className="card card-pad">
      <div className="text-xs uppercase text-gray-500">{idea.category}</div>
      <div className="font-semibold mt-1">{idea.title}</div>
      <button
        onClick={() => onCreate(idea)}
        disabled={busy}
        className="btn btn-sm btn-ghost mt-3 disabled:opacity-50"
      >
        {busy ? "Creating..." : "Create draft"}
      </button>
    </div>
  );
}
