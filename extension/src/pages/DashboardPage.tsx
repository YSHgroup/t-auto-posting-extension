import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useSettingsStore } from "../stores/settingsStore";
import type { BotStatus, Dashboard } from "../types";

export function DashboardPage() {
  const [dash, setDash] = useState<Dashboard | null>(null);
  const [bot, setBot] = useState<BotStatus | null>(null);
  const [lastPostedAt, setLastPostedAt] = useState<Date | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [localEnabled, setLocalEnabled] = useState<boolean>(false);
  const [pausedRemainingMs, setPausedRemainingMs] = useState<number | null>(null);
  const [postingIntervalMinutes, setPostingIntervalMinutes] = useState<number | null>(null);
  const [remainingMs, setRemainingMs] = useState<number | null>(null);

  const refresh = async () => {
    try {
      setError(null);
      const [d, b] = await Promise.all([api.dashboard(), api.botStatus()]);
      setDash(d);
      setLastPostedAt(d.last_posted_at ? new Date(d.last_posted_at) : null);
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

  // fetch scheduler interval to drive countdown resets
  useEffect(() => {
    void (async () => {
      try {
        const sched = await api.getScheduler();
        setPostingIntervalMinutes(Math.max(1, sched.posting_interval_minutes || 1));
      } catch {
        setPostingIntervalMinutes(1);
      }
    })();
  }, []);

  useEffect(() => {
    // helper to read local navigation state and compute remaining time
    const refreshLocalState = async () => {
      try {
        const username = await useSettingsStore.getState().getTelegramUsername();
        if (!username) return;
        const key = `telegram_auto_bot_navigation:${username}`;
        const stored = await new Promise<any>((resolve) => chrome.storage.local.get([key], (s) => resolve(s)));
        const s = stored[key] as any;
        setLocalEnabled(Boolean(s?.enabled));
        const paused = s?.pausedRemainingMs ? Number(s.pausedRemainingMs) : null;
        setPausedRemainingMs(paused);
        if (paused && !s?.enabled) setRemainingMs(paused);
        if (s?.enabled) {
          try {
            const alarm = await new Promise<any>((resolve) => chrome.alarms.get("telegram-auto-bot-local-navigation", (a) => resolve(a)));
            const now = Date.now();
            const scheduled = (alarm && alarm.scheduledTime) || (now + (postingIntervalMinutes || 1) * 60_000);
            setRemainingMs(Math.max(0, Number(scheduled) - now));
          } catch {
            // ignore
          }
        }
      } catch {
        // ignore
      }
    };

    void refreshLocalState();
    const onStorage = (_changes: { [key: string]: chrome.storage.StorageChange }, areaName: string) => {
      if (areaName !== "local") return;
      // refresh when local navigation state changes
      void refreshLocalState();
    };
    try {
      chrome.storage.onChanged.addListener(onStorage);
    } catch {
      /* ignore */
    }
    return () => {
      try {
        chrome.storage.onChanged.removeListener(onStorage as any);
      } catch {
        /* ignore */
      }
    };
  }, []);

  // update live counter and countdown every second
  useEffect(() => {
    const id = setInterval(() => {
      setLastPostedAt((d) => (d ? new Date(d.getTime()) : d));
      setRemainingMs((r) => (r !== null && localEnabled ? Math.max(0, r - 1000) : r));
    }, 1000);
    return () => clearInterval(id);
  }, []);

  // listen for background post events to update immediately
  useEffect(() => {
    const handler = (message: any) => {
      if (message?.type === "telegram-auto-bot-posted" && message.posted_at) {
        try {
          setLastPostedAt(new Date(message.posted_at));
          // reset countdown to full interval when a post occurs
          if (postingIntervalMinutes) setRemainingMs(postingIntervalMinutes * 60_000);
        } catch {
          /* ignore invalid dates */
        }
      }
    };
    try {
      chrome.runtime.onMessage.addListener(handler);
    } catch {
      // not available in some environments
    }
    return () => {
      try {
        chrome.runtime.onMessage.removeListener(handler as any);
      } catch {
        /* ignore */
      }
    };
  }, []);

  if (!dash) return <p>Loading dashboard…</p>;

  const toggleBot = async (start: boolean) => {
    try {
      setError(null);
      // Use frontend/local bot control instead of backend start/stop
      const action = start ? "start" : "stop";
      await new Promise<void>((resolve, reject) => {
        try {
          chrome.runtime.sendMessage({ type: "telegram-auto-bot-local", action }, (resp) => {
            if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
            resolve();
          });
        } catch (e) {
          reject(e);
        }
      });
      // refresh local navigation state and dashboard
      try {
        const username = await useSettingsStore.getState().getTelegramUsername();
        if (username) {
          const key = `telegram_auto_bot_navigation:${username}`;
          const stored = await new Promise<any>((resolve) => chrome.storage.local.get([key], (s) => resolve(s)));
          const s = stored[key] as any;
          setLocalEnabled(Boolean(s?.enabled));
          const paused = s?.pausedRemainingMs ? Number(s.pausedRemainingMs) : null;
          setPausedRemainingMs(paused);
          if (s?.enabled) {
            const alarm = await new Promise<any>((resolve) => chrome.alarms.get("telegram-auto-bot-local-navigation", (a) => resolve(a)));
            const now = Date.now();
            const scheduled = (alarm && alarm.scheduledTime) || (now + (postingIntervalMinutes || 1) * 60_000);
            setRemainingMs(Math.max(0, Number(scheduled) - now));
          }
        }
      } catch {
        // ignore
      }
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Bot action failed");
    }
  };

  const resumeLocal = async () => {
    try {
      await new Promise<void>((resolve, reject) => {
        try {
          chrome.runtime.sendMessage({ type: "telegram-auto-bot-local", action: "resume" }, (r) => {
            if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
            resolve();
          });
        } catch (e) {
          reject(e);
        }
      });
      // refresh local state and dashboard
      try {
        const username = await useSettingsStore.getState().getTelegramUsername();
        if (username) {
          const key = `telegram_auto_bot_navigation:${username}`;
          const stored = await new Promise<any>((resolve) => chrome.storage.local.get([key], (s) => resolve(s)));
          const s = stored[key] as any;
          setLocalEnabled(Boolean(s?.enabled));
          const alarm = await new Promise<any>((resolve) => chrome.alarms.get("telegram-auto-bot-local-navigation", (a) => resolve(a)));
          const now = Date.now();
          const scheduled = (alarm && alarm.scheduledTime) || (now + (postingIntervalMinutes || 1) * 60_000);
          setRemainingMs(Math.max(0, Number(scheduled) - now));
        }
      } catch {
        /* ignore */
      }
      await refresh();
    } catch {
      /* ignore */
    }
  };

  const resetLocal = async () => {
    try {
      await new Promise<void>((resolve, reject) => {
        try {
          chrome.runtime.sendMessage({ type: "telegram-auto-bot-local", action: "reset" }, (r) => {
            if (chrome.runtime.lastError) return reject(new Error(chrome.runtime.lastError.message));
            resolve();
          });
        } catch (e) {
          reject(e);
        }
      });
      // refresh local state and dashboard
      try {
        const username = await useSettingsStore.getState().getTelegramUsername();
        if (username) {
          const key = `telegram_auto_bot_navigation:${username}`;
          const stored = await new Promise<any>((resolve) => chrome.storage.local.get([key], (s) => resolve(s)));
          const s = stored[key] as any;
          setLocalEnabled(Boolean(s?.enabled));
          const paused = s?.pausedRemainingMs ? Number(s.pausedRemainingMs) : null;
          setPausedRemainingMs(paused);
          if (s?.enabled) {
            const alarm = await new Promise<any>((resolve) => chrome.alarms.get("telegram-auto-bot-local-navigation", (a) => resolve(a)));
            const now = Date.now();
            const scheduled = (alarm && alarm.scheduledTime) || (now + (postingIntervalMinutes || 1) * 60_000);
            setRemainingMs(Math.max(0, Number(scheduled) - now));
          }
        }
      } catch {
        /* ignore */
      }
      await refresh();
    } catch {
      /* ignore */
    }
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
        {(() => {
          const isRunning = localEnabled || bot?.state === "RUNNING";
          return (
            <p className={isRunning ? "status-running" : "status-stopped"}>
              {isRunning ? "● RUNNING" : "○ STOPPED"}
            </p>
          );
        })()}
        <div style={{ marginTop: 8 }}>
          <strong>Time since last post:</strong>
          <div>
            {lastPostedAt ? (
              (() => {
                const diff = Math.max(0, Date.now() - lastPostedAt.getTime());
                const s = Math.floor(diff / 1000) % 60;
                const m = Math.floor(diff / 1000 / 60) % 60;
                const h = Math.floor(diff / 1000 / 3600);
                return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
              })()
            ) : (
              <span className="muted">No posts recorded yet</span>
            )}
          </div>
          {lastPostedAt && (
            <div className="muted" style={{ marginTop: 4 }}>
              Last posted at: {lastPostedAt.toLocaleString()}
            </div>
          )}
          {remainingMs !== null && (
            <div style={{ marginTop: 8 }}>
              <strong>Reversal counter:</strong>
              <div>
                {(() => {
                  const r = Math.max(0, remainingMs || 0);
                  const s = Math.floor(r / 1000) % 60;
                  const m = Math.floor(r / 1000 / 60) % 60;
                  const h = Math.floor(r / 1000 / 3600);
                  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
                })()}
              </div>
            </div>
          )}
        </div>
        <p className="muted">Start the bot to enable scheduled navigation and extension-assisted posting. The extension will perform posts in your browser and record them back to the server.</p>
        <div className="row">
          {!localEnabled ? (
            <button type="button" className="btn btn-primary" onClick={() => void toggleBot(true)}>
              START BOT
            </button>
          ) : (
            <button type="button" className="btn btn-ghost" onClick={() => void toggleBot(false)}>
              STOP BOT
            </button>
          )}
          {!localEnabled && pausedRemainingMs ? (
            <button type="button" className="btn btn-secondary" onClick={() => void resumeLocal()}>
              RESUME
            </button>
          ) : null}
          <button type="button" className="btn btn-ghost" onClick={() => void resetLocal()}>
            RESET
          </button>
        </div>
      </div>
    </div>
  );
}
