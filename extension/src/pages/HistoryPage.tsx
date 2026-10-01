import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { PostHistoryItem } from "../types";

export function HistoryPage() {
  const [items, setItems] = useState<PostHistoryItem[]>([]);

  useEffect(() => {
    void api.history().then(setItems);
  }, []);

  return (
    <div>
      <h2 className="page-title">Posting History</h2>
      {items.map((h) => (
        <div key={h.id} className="card">
          <strong>{h.status.toUpperCase()}</strong> · {new Date(h.posted_at).toLocaleString()}
          <p>
            {h.group_name} {h.post_title ? `· ${h.post_title}` : ""}
          </p>
          {h.reason && <p>{h.reason}</p>}
        </div>
      ))}
    </div>
  );
}
