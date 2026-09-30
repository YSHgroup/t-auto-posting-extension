import { useState } from "react";
import { api } from "../services/api";

export function GroupsPage() {
  const [error, setError] = useState<string | null>(null);
  const [manualId, setManualId] = useState("");

  const addManual = async () => {
    try {
      const match = manualId.match(/(?:https?:\/\/)?t\.me\/(?:s\/)?([^/?#]+)/i);
      const groupId = match?.[1] || manualId.trim();
      <h2 className="page-title">Groups</h2>
      <div className="card">
          <p className="muted">Paste a Telegram group ID or URL, or open a group in Telegram Web and use the Add/Skip prompt. Search is not connected to Telegram.</p>
        <div className="row">
          <input className="input" value={q} onChange={(e) => setQ(e.target.value)} />
          <button type="button" className="btn btn-primary" onClick={() => void search()} disabled={loading}>
            Search
          </button>
        </div>
      </div>
      <div className="card">
        <label className="label">Add Telegram group manually</label>
        <p className="muted">Paste a group ID or t.me URL. On Telegram Web, choose Add or Skip when prompted.</p>
        <div className="row">
          <input className="input" value={manualId} onChange={(e) => setManualId(e.target.value)} />
          <button type="button" className="btn btn-primary" onClick={() => void addManual()}>
            Add to Feed
          </button>
        </div>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  );
}
