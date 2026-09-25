import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { FeedItem, Post } from "../types";

export function FeedPage() {
  const [items, setItems] = useState<FeedItem[]>([]);
  const [posts, setPosts] = useState<Post[]>([]);
  const [recommendations, setRecommendations] = useState<Record<string, { post_id: string; reason: string; confidence: number }[]>>({});

  const load = async () => {
    const [feed, ps] = await Promise.all([api.listFeed(), api.listPosts()]);
    setItems(feed.sort((a, b) => a.order_index - b.order_index));
    setPosts(ps);
  };

  useEffect(() => {
    void load();
  }, []);

  const move = async (index: number, dir: -1 | 1) => {
    const next = [...items];
    const j = index + dir;
    if (j < 0 || j >= next.length) return;
    [next[index], next[j]] = [next[j], next[index]];
    const payload = next.map((it, i) => ({ id: it.id, order_index: i }));
    setItems(next.map((it, i) => ({ ...it, order_index: i })));
    await api.reorderFeed(payload);
  };

  const toggle = async (item: FeedItem) => {
    await api.updateFeed(item.id, { enabled: !item.enabled });
    await load();
  };

  const remove = async (id: string) => {
    await api.deleteFeed(id);
    await load();
  };

  const selectPost = async (feedId: string, postId: string) => {
    await api.updateFeed(feedId, { post_id: postId, selected_by: "user" });
    await load();
  };

  const loadRec = async (feedId: string) => {
    const res = await api.recommendPost(feedId);
    setRecommendations((prev) => ({ ...prev, [feedId]: res.recommendations }));
  };

  return (
    <div>
      <h2 className="page-title">Feed</h2>
      {items.map((item, index) => (
        <div key={item.id} className="card">
          <div className="row">
            <strong>#{index + 1}</strong>
            <span>{item.group_name}</span>
            <span className="badge">{item.enabled ? "Enabled" : "Disabled"}</span>
          </div>
          <p>
            Selected: {item.selected_post_title || "None"} · Posts: {item.post_count} · Last:{" "}
            {item.last_posted_at ? new Date(item.last_posted_at).toLocaleString() : "—"}
          </p>
          <div className="row">
            <button type="button" className="btn btn-ghost" onClick={() => void move(index, -1)}>
              Move Up
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => void move(index, 1)}>
              Move Down
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => void toggle(item)}>
              {item.enabled ? "Disable" : "Enable"}
            </button>
            <button type="button" className="btn btn-danger" onClick={() => void remove(item.id)}>
              Remove
            </button>
            <button type="button" className="btn btn-primary" onClick={() => void loadRec(item.id)}>
              AI Recommendation
            </button>
          </div>
          <div>
            <p className="label">Select post (user must choose)</p>
            {posts.map((p, pi) => (
              <label key={p.id} style={{ display: "block", marginBottom: 4 }}>
                <input
                  type="radio"
                  name={`post-${item.id}`}
                  checked={item.selected_post_id === p.id}
                  onChange={() => void selectPost(item.id, p.id)}
                />{" "}
                Post #{pi + 1} — {p.title}
              </label>
            ))}
          </div>
          {recommendations[item.id] && (
            <div>
              <h4>AI Recommendation</h4>
              {recommendations[item.id].map((r) => (
                <div key={r.post_id}>
                  ○ Post {posts.findIndex((p) => p.id === r.post_id) + 1} — {r.confidence}% — {r.reason}
                </div>
              ))}
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
