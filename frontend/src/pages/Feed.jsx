import { useEffect, useState } from "react";
import { api } from "../lib/api";
import FeedStatsCard from "../components/FeedStatsCard";

function PostPreview({ post, onDelete }) {
  const category = post.category || "uncategorized";

  return (
    <div className="card overflow-hidden">
      {/* HEADER */}
      <div className="card-pad pb-3">
        <div className="flex items-start justify-between gap-3">
          {/* Title + date */}
          <div className="min-w-0">
            <div className="font-semibold truncate">
              {post.title || "Untitled post"}
            </div>
            <div className="text-xs text-gray-500">
              {post.publishedAt
                ? new Date(post.publishedAt).toLocaleString()
                : ""}
            </div>
          </div>

          {/* Category + X button egy sorban, nem egymáson */}
          <div className="flex items-center gap-2">
            <span className="px-2 py-0.5 rounded-full bg-gray-100 text-xs text-gray-700 whitespace-nowrap">
              {category}
            </span>
            {onDelete && (
              <button
                type="button"
                onClick={onDelete}
                className="h-7 w-7 rounded-full border border-gray-300 bg-white/90
                           flex items-center justify-center text-gray-600
                           hover:bg-red-50 hover:text-red-600 hover:border-red-200 transition"
                aria-label="Delete post from feed"
              >
                ×
              </button>
            )}
          </div>
        </div>
      </div>

      {/* IMAGE – fix négyzet crop, nincs több felső/alsó sáv */}
      {post.imageUrl && (
        <div className="w-full bg-black">
          <div className="relative w-full aspect-square overflow-hidden">
            <img
              src={post.imageUrl}
              alt={post.title || "post"}
              className="absolute inset-0 w-full h-full object-cover"
              onError={(e) => {
                e.currentTarget.style.objectFit = "contain";
                e.currentTarget.style.background = "#222";
              }}
            />
          </div>
        </div>
      )}

      {/* “Instagram-szerű” alsó rész */}
      <div className="p-4">
        <div className="flex items-center gap-3 mb-3">
          <div className="h-8 w-8 rounded-full bg-gray-200" />
          <div className="text-sm font-medium">
            Szakdolgozat{" "}
            <span className="text-gray-400">• Following</span>
          </div>
        </div>

        {post.caption && (
          <p className="mb-2 text-sm whitespace-pre-line">
            {post.caption}
          </p>
        )}

        {post.hashtags?.length > 0 && (
          <p className="text-xs text-gray-600">
            {post.hashtags.map((h) => `#${h}`).join(" ")}
          </p>
        )}
      </div>
    </div>
  );
}

export default function Feed() {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = async () => {
    setLoading(true);
    try {
      const res = await api.getFeed();
      setItems(res.items || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
  }, []);

  const handleDelete = async (id) => {
    if (!window.confirm("Remove this post from the feed simulation?")) return;
    try {
      await api.deleteFeedPost(id);
      await load();
    } catch (e) {
      console.error(e);
      alert("Failed to delete post from feed.");
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Feed (Simulation)</h1>
        <button className="btn btn-sm btn-ghost" onClick={load}>
          Refresh
        </button>
      </div>

      {loading ? (
        <div className="card card-pad">Loading feed…</div>
      ) : items.length === 0 ? (
        <div className="card card-pad">
          No posts yet. Approve a draft to publish it.
        </div>
      ) : (
        <div className="flex flex-col gap-6">
          {items.map((p) => (
            <div
              key={p.id}
              className="grid grid-cols-1 md:grid-cols-[1fr_320px] gap-4"
            >
              <PostPreview
                post={p}
                onDelete={() => handleDelete(p.id)}
              />
              <FeedStatsCard post={p} onRefresh={load} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
