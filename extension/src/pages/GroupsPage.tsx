import { useState } from "react";
import { api } from "../services/api";

export function GroupsPage() {
  const [error, setError] = useState<string | null>(null);
  const [manualId, setManualId] = useState("");
  const [loading, setLoading] = useState(false);

  const addManual = async () => {
    setError(null);
    const value = manualId.trim();
    const match = value.match(/(?:https?:\/\/)?t\.me\/(?:s\/)?([^/?#]+)/i);
    const groupId = match?.[1] || value;
    const groupUrl = match ? `https://t.me/${match[1]}` : "";
    if (!groupId) {
      setError("Enter a Telegram group ID or URL.");
      return;
    }

    setLoading(true);
    try {
      await api.addFeed(groupId, groupUrl);
      setManualId("");
      alert("Group added to your feed.");
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not add group.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 className="page-title">Groups</h2>
      <div className="card">
        <label className="label" htmlFor="telegram-group-id">Add Telegram group manually</label>
        <p className="muted">
          Enter a group ID or t.me URL, or open a group in Telegram Web and use the Add/Skip prompt.
          Live Telegram search is not connected.
        </p>
        <div className="row">
          <input
            id="telegram-group-id"
            className="input"
            value={manualId}
            onChange={(event) => setManualId(event.target.value)}
            placeholder="Group ID or https://t.me/group"
          />
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void addManual()}
            disabled={loading}
          >
            {loading ? "Adding…" : "Add to Feed"}
          </button>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
