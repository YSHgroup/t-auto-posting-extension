import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { BotStatus, Dashboard } from "../types";

export function DashboardPage() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [bot, setBot] = useState<BotStatus | null>(null);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    try {
      setError(null);
      const [d, b] = await Promise.all([api.dashboard(), api.botStatus()]);
      setDash(d);
      setBot(b);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load dashboard");
    }
  };

  useEffect(() => {
    void refresh();
    const t = setInterval(() => void refresh(), 15000);
    return () => clearInterval(t);
  }, []);

  const toggleBot = async (start: boolean) => {
    const b = start ? await api.startBot() : await api.stopBot();
    setBot(b);
    await refresh();
  };

  return (
    <div>
      <h2 className="page-title">Dashboard</h2>
      {error && <p className="error">{error}</p>}
      {dash && (
        <div className="grid-stats">
          {[
            ["Groups", dash.total_groups],
            ["Active Feed", dash.active_feed_groups],
            ["Total Posts", dash.total_posts],
            ["Posts Today", dash.posts_today],
            ["Skipped", dash.skipped_posts],
            ["Replies", dash.replies],
            ["Unread", dash.unread_notifications],
            ["Investors", dash.potential_investors],
            ["Partners", dash.potential_partners],
          ].map(([label, value]) => (
            <div key={label as string} className="stat">
              <div className="stat-label">{label}</div>
              <div className="stat-value">{value}</div>
            </div>
          ))}
        </div>
      )}
      <div className="card" style={{ marginTop: 16 }}>
        <h3>Bot Status</h3>
        <p className={bot?.state === "RUNNING" ? "status-running" : "status-stopped"}>
          {bot?.state === "RUNNING" ? "● RUNNING" : "○ STOPPED"}
        </p>
        <div className="row">
          <button type="button" className="btn btn-primary" onClick={() => void toggleBot(true)}>
            START BOT
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => void toggleBot(false)}>
            STOP BOT
          </button>
        </div>
      </div>
    </div>
  );
}
