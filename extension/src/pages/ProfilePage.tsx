import { useState, useEffect } from "react";
import { useSettingsStore } from "../stores/settingsStore";
import { api } from "../services/api";

export function ProfilePage() {
  const [username, setUsername] = useState("");
  const [status, setStatus] = useState<string | null>(null);

  useEffect(() => {
    void (async () => {
      const u = await useSettingsStore.getState().getTelegramUsername();
      setUsername(u || "");
    })();
  }, []);

  const save = async () => {
    setStatus(null);
    try {
      await useSettingsStore.getState().setTelegramUsername(username);
      setStatus("Saved username");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e));
    }
  };

  const clearData = async () => {
    setStatus(null);
    try {
      await api.clearData();
      setStatus("Cleared local account data (histories preserved)");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e));
    }
  };

  const removeAccount = async () => {
    setStatus(null);
    try {
      await api.removeAccount();
      // clear local username stored in extension
      await useSettingsStore.getState().setTelegramUsername("");
      setStatus("Account removed (histories preserved). Username cleared locally.");
    } catch (e) {
      setStatus(e instanceof Error ? e.message : String(e));
    }
  };

  return (
    <div>
      <h2 className="page-title">Profile</h2>
      <div className="card">
        <label className="label">Telegram Username</label>
        <input className="input" value={username} onChange={(e) => setUsername(e.target.value)} />
        <div style={{ marginTop: 8 }}>
          <button className="btn btn-primary" onClick={() => void save()}>
            Save
          </button>
        </div>
      </div>

      <div className="card">
        <h3>Account actions</h3>
        <p className="muted">Clear your account data for this installation. Histories will be preserved.</p>
        <div className="row">
          <button className="btn btn-ghost" onClick={() => void clearData()}>
            Clear Data
          </button>
          <button className="btn btn-danger" onClick={() => void removeAccount()}>
            Remove Account
          </button>
        </div>
        {status && <p className="muted">{status}</p>}
      </div>
    </div>
  );
}

export default ProfilePage;
