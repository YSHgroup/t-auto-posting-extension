import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { Post } from "../types";

const POST_TYPES = ["Partnership", "Job", "Investment", "Business", "General", "Custom"];

export function PostsPage() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [editing, setEditing] = useState<Partial<Post> | null>(null);

  const load = async () => setPosts(await api.listPosts());

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    if (!editing?.title || !editing.content) return;
    if (editing.id) {
      await api.updatePost(editing.id, editing);
    } else {
      await api.createPost({
        title: editing.title,
        post_type: editing.post_type || "Partnership",
        content: editing.content,
        status: editing.status || "Active",
        enabled: editing.enabled ?? true,
      });
    }
    setEditing(null);
    await load();
  };

  return (
    <div>
      <h2 className="page-title">Posts</h2>
      <button
        type="button"
        className="btn btn-primary"
        onClick={() => setEditing({ title: "", post_type: "Partnership", content: "", status: "Active" })}
      >
        Create Post
      </button>
      {editing && (
        <div className="card">
          <label className="label">Title</label>
          <input className="input" value={editing.title || ""} onChange={(e) => setEditing({ ...editing, title: e.target.value })} />
          <label className="label">Type</label>
          <select
            className="select"
            value={editing.post_type || "Partnership"}
            onChange={(e) => setEditing({ ...editing, post_type: e.target.value })}
          >
            {POST_TYPES.map((t) => (
              <option key={t}>{t}</option>
            ))}
          </select>
          <label className="label">Content</label>
          <textarea className="textarea" value={editing.content || ""} onChange={(e) => setEditing({ ...editing, content: e.target.value })} />
          <label className="label">Status</label>
          <input className="input" value={editing.status || "Active"} onChange={(e) => setEditing({ ...editing, status: e.target.value })} />
          <div className="row">
            <button type="button" className="btn btn-primary" onClick={() => void save()}>
              Save
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => setEditing(null)}>
              Cancel
            </button>
          </div>
        </div>
      )}
      {posts.map((p) => (
        <div key={p.id} className="card">
          <strong>{p.title}</strong>
          <p>
            Type: {p.post_type} · Status: {p.status} · Used: {p.usage_count} times
          </p>
          <p>Created: {new Date(p.created_at).toLocaleDateString()}</p>
          <div className="row">
            <button type="button" className="btn btn-ghost" onClick={() => setEditing(p)}>
              Edit
            </button>
            <button type="button" className="btn btn-ghost" onClick={() => void api.duplicatePost(p.id).then(load)}>
              Duplicate
            </button>
            <button type="button" className="btn btn-danger" onClick={() => void api.deletePost(p.id).then(load)}>
              Delete
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={() => void api.updatePost(p.id, { enabled: !p.enabled }).then(load)}
            >
              {p.enabled ? "Disable" : "Enable"}
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
