import { useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import type { GroupSearchResult } from "../types";

export function GroupsPage() {
  const [q, setQ] = useState("blockchain startup");
  const [results, setResults] = useState<GroupSearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [manualId, setManualId] = useState("group_12345");

  const search = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.searchGroups(q);
      setResults(data.slice(0, 50));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Search failed");
    } finally {
      setLoading(false);
    }
  };

  const addManual = async () => {
    try {
      await api.addFeed(manualId);
      alert("Added to feed (if group ID is valid).");
    } catch (e) {
      alert(e instanceof Error ? e.message : "Invalid group ID");
    }
  };

  return (
    <div>
      <h2 className="page-title">Groups</h2>
      <div className="card">
        <label className="label">Search groups...</label>
        <div className="row">
          <input className="input" value={q} onChange={(e) => setQ(e.target.value)} />
          <button type="button" className="btn btn-primary" onClick={() => void search()} disabled={loading}>
            Search
          </button>
        </div>
      </div>
      <div className="card">
        <label className="label">Group ID (manual)</label>
        <div className="row">
          <input className="input" value={manualId} onChange={(e) => setManualId(e.target.value)} />
          <button type="button" className="btn btn-primary" onClick={() => void addManual()}>
            Add to Feed
          </button>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
      {results.map((g) => (
        <div key={g.id} className="card">
          <strong>{g.name}</strong>
          <div className="muted">@{g.username} · {g.member_count.toLocaleString()} members</div>
          <p>{g.description}</p>
          <div>
            {g.categories.map((c) => (
              <span key={c} className="badge">
                {c}
              </span>
            ))}
          </div>
          <p>Relevance: {g.relevance}%</p>
          <div className="row">
            <Link className="btn btn-ghost" to={`/groups/${g.id}`}>
              Open
            </Link>
            <Link className="btn btn-ghost" to={`/groups/${g.id}?analyze=1`}>
              Analyze
            </Link>
            <button
              type="button"
              className="btn btn-primary"
              onClick={() => void api.addFeed(g.id).then(() => alert("Added to feed"))}
            >
              Add to Feed
            </button>
          </div>
        </div>
      ))}
    </div>
  );
}
