import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useSettingsStore } from "../stores/settingsStore";

export function SettingsPage() {
  const {
    apiBaseUrl,
    telegramUsername,
    setApiBaseUrl,
    setTelegramUsername,
    testConnection,
    connectionOk,
    load,
  } = useSettingsStore();
  const [url, setUrl] = useState(apiBaseUrl);
  const [username, setUsername] = useState(telegramUsername);
  const [settings, setSettings] = useState<Record<string, unknown>>({});

  useEffect(() => {
    void load();
    void api.getSettings().then(setSettings).catch(() => undefined);
  }, [load]);

  useEffect(() => setUrl(apiBaseUrl), [apiBaseUrl]);
  useEffect(() => setUsername(telegramUsername), [telegramUsername]);

  return (
    <div>
      <h2 className="page-title">Settings</h2>
      <div className="card">
        <h3>Account scope</h3>
        <label className="label">Telegram username (you enter this)</label>
        <input
          className="input"
          value={username}
          onChange={(event) => setUsername(event.target.value)}
          placeholder="@your_username"
          autoComplete="username"
        />
        <p className="muted">This username is used to separate this app's data. It is not automatically read from Telegram and does not verify Telegram account ownership.</p>
        <button
          type="button"
          className="btn btn-primary"
          disabled={!/^[A-Za-z0-9_]{5,32}$/.test(username.trim().replace(/^@/, ""))}
          onClick={() => void setTelegramUsername(username)}
        >
          Save username
        </button>
      </div>
      <div className="card">
        <h3>Backend</h3>
        <p className="muted">A private installation identity is used to keep this browser profile's data separate.</p>
        <label className="label">API Server URL</label>
        <input className="input" value={url} onChange={(e) => setUrl(e.target.value)} />
        <div className="row" style={{ marginTop: 8 }}>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => void setApiBaseUrl(url)}
          >
            Save URL
          </button>
          <button type="button" className="btn btn-ghost" onClick={() => void testConnection()}>
            Test Connection
          </button>
          {connectionOk === true && <span className="status-running">Connected</span>}
          {connectionOk === false && <span className="error">Failed</span>}
        </div>
      </div>
      <div className="card">
        <h3>AI provider (server-side API key required)</h3>
        <label className="label">Provider</label>
        <select
          className="select"
          value={(settings.ai_provider as string) || "openai"}
          onChange={(e) => void api.updateSettings({ ai_provider: e.target.value }).then(setSettings)}
        >
          <option value="openai">OpenAI</option>
          <option value="anthropic">Claude</option>
        </select>
      </div>
      <div className="card">
        <h3>Data</h3>
        <p>Telegram Web integration: user-confirmed group intake only. Message import, sending, and deletion are manual; the extension does not control Telegram.</p>
        <p>Data source: manually entered groups and user-copied messages. Demo/mock seed, search, and reset are disabled.</p>
      </div>
    </div>
  );
}
