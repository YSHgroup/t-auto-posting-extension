import { useEffect, useState } from "react";
import { api } from "../services/api";
import { useSettingsStore } from "../stores/settingsStore";

export function SettingsPage() {
  const { apiBaseUrl, setApiBaseUrl, testConnection, connectionOk, load } = useSettingsStore();
  const [url, setUrl] = useState(apiBaseUrl);
  const [settings, setSettings] = useState<Record<string, unknown>>({});

  useEffect(() => {
    void load();
    void api.getSettings().then(setSettings).catch(() => undefined);
  }, [load]);

  useEffect(() => setUrl(apiBaseUrl), [apiBaseUrl]);

  return (
    <div>
      <h2 className="page-title">Settings</h2>
      <div className="card">
        <h3>Backend</h3>
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
        <h3>AI (server-side keys)</h3>
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
        <p>Data Mode: ● Mock ○ External (External not implemented)</p>
        <button type="button" className="btn btn-danger" onClick={() => void api.resetDemo().then(() => alert("Demo data reset"))}>
          Reset demo data
        </button>
      </div>
    </div>
  );
}
