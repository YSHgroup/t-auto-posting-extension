import { useEffect, useState } from "react";
import { api } from "../services/api";
import type { BotStatus, SchedulerSettings } from "../types";

const DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];

export function SchedulerPage() {
  const [sched, setSched] = useState<SchedulerSettings | null>(null);
  const [bot, setBot] = useState<BotStatus | null>(null);

  const load = async () => {
    setSched(await api.getScheduler());
    setBot(await api.botStatus());
  };

  useEffect(() => {
    void load();
  }, []);

  const save = async () => {
    if (!sched) return;
    await api.updateScheduler(sched);
    alert("Scheduler saved");
  };

  const toggleDay = (dayIndex: number) => {
    if (!sched) return;
    const days = new Set(sched.working_days);
    if (days.has(dayIndex)) days.delete(dayIndex);
    else days.add(dayIndex);
    setSched({ ...sched, working_days: [...days].sort() });
  };

  if (!sched) return <p>Loading...</p>;

  return (
    <div>
      <h2 className="page-title">Scheduler</h2>
      <div className="card">
        <label>
          <input
            type="checkbox"
            checked={sched.auto_mode}
            onChange={(e) => setSched({ ...sched, auto_mode: e.target.checked })}
          />{" "}
          Auto Mode
        </label>
        <div className="row" style={{ marginTop: 12 }}>
          {DAYS.map((d, i) => (
            <label key={d}>
              <input type="checkbox" checked={sched.working_days.includes(i)} onChange={() => toggleDay(i)} /> {d}
            </label>
          ))}
        </div>
        <label className="label">Start</label>
        <input className="input" value={sched.start_time} onChange={(e) => setSched({ ...sched, start_time: e.target.value })} />
        <label className="label">End</label>
        <input className="input" value={sched.end_time} onChange={(e) => setSched({ ...sched, end_time: e.target.value })} />
        <label className="label">Interval (minutes)</label>
        <input
          className="input"
          type="number"
          value={sched.posting_interval_minutes}
          onChange={(e) => setSched({ ...sched, posting_interval_minutes: Number(e.target.value) })}
        />
        <label className="label">Minimum messages</label>
        <input
          className="input"
          type="number"
          value={sched.minimum_messages}
          onChange={(e) => setSched({ ...sched, minimum_messages: Number(e.target.value) })}
        />
        <label className="label">Maximum posts per day</label>
        <input
          className="input"
          type="number"
          value={sched.maximum_posts_per_day}
          onChange={(e) => setSched({ ...sched, maximum_posts_per_day: Number(e.target.value) })}
        />
        <button type="button" className="btn btn-primary" style={{ marginTop: 12 }} onClick={() => void save()}>
          Save Settings
        </button>
      </div>
      <div className="card">
        <h3>BOT STATUS</h3>
        <p className={bot?.state === "RUNNING" ? "status-running" : "status-stopped"}>
          {bot?.state === "RUNNING" ? "● RUNNING" : "○ STOPPED"}
        </p>
        <div className="row">
          <button type="button" className="btn btn-primary" onClick={() => void api.startBot().then(setBot)}>
            ▶ START BOT
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => void api.stopBot().then(setBot)}>
            ■ STOP BOT
          </button>
        </div>
      </div>
    </div>
  );
}
