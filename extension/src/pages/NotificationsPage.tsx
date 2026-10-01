import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { NotificationItem } from "../types";

export function NotificationsPage() {
  const [filter, setFilter] = useState("all");
  const [items, setItems] = useState<NotificationItem[]>([]);

  const load = async () => setItems(await api.notifications(filter));

  useEffect(() => {
    void load();
  }, [filter]);

  return (
    <div>
      <h2 className="page-title">Notifications</h2>
      <div className="row">
        {["unread", "read", "all"].map((f) => (
          <button key={f} type="button" className={`btn ${filter === f ? "btn-primary" : "btn-ghost"}`} onClick={() => setFilter(f)}>
            {f.charAt(0).toUpperCase() + f.slice(1)}
          </button>
        ))}
        <button type="button" className="btn btn-ghost" onClick={() => void api.markAllRead().then(load)}>
          Mark all read
        </button>
      </div>
      {items.map((n) => (
        <div key={n.id} className="card">
          <strong>@{n.username}</strong>
          <p>{n.message}</p>
          <p>{new Date(n.created_at).toLocaleString()} · {n.read ? "Read" : "Unread"}</p>
          {!n.read && (
            <button type="button" className="btn btn-ghost" onClick={() => void api.markRead(n.id).then(load)}>
              Mark as read
            </button>
          )}
        </div>
      ))}
    </div>
  );
}
