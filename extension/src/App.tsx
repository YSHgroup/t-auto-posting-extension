import { Route, Routes } from "react-router-dom";
import { AppLayout } from "./layouts/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";
import { FeedPage } from "./pages/FeedPage";
import { GroupDetailPage } from "./pages/GroupDetailPage";
import { GroupsPage } from "./pages/GroupsPage";
import { NotificationsPage } from "./pages/NotificationsPage";
import { OpportunitiesPage } from "./pages/OpportunitiesPage";
import { PostsPage } from "./pages/PostsPage";
import { SchedulerPage } from "./pages/SchedulerPage";
import { HistoryPage } from "./pages/HistoryPage";
import { SettingsPage } from "./pages/SettingsPage";
import { ProfilePage } from "./pages/ProfilePage";
import { useSettingsStore } from "./stores/settingsStore";
import { useState, type FormEvent } from "react";

export function App() {
  const telegramUsername = useSettingsStore((state) => state.telegramUsername);
  const setTelegramUsername = useSettingsStore((state) => state.setTelegramUsername);
  const [username, setUsername] = useState(telegramUsername);
  const [error, setError] = useState<string | null>(null);

  if (!telegramUsername) {
    const saveUsername = async (event: FormEvent<HTMLFormElement>) => {
      event.preventDefault();
      const normalized = username.trim().replace(/^@/, "");
      if (!/^[A-Za-z0-9_]{5,32}$/.test(normalized)) {
        setError("Enter a Telegram username with 5–32 letters, numbers, or underscores.");
        return;
      }
      try {
        await setTelegramUsername(normalized);
        setError(null);
      } catch (saveError) {
        setError(saveError instanceof Error ? saveError.message : "Could not save username.");
      }
    };

    return (
      <main className="main">
        <div className="card">
          <h1>Set up your account</h1>
          <p>Enter your Telegram username to open the extension. It is entered by you and is not read from Telegram.</p>
          <form onSubmit={(event) => void saveUsername(event)}>
            <label className="label" htmlFor="initial-telegram-username">Telegram username</label>
            <input
              id="initial-telegram-username"
              className="input"
              value={username}
              onChange={(event) => setUsername(event.target.value)}
              placeholder="@your_username"
              autoComplete="username"
              autoFocus
            />
            {error && <p className="error">{error}</p>}
            <button type="submit" className="btn btn-primary" style={{ marginTop: 12 }}>
              Continue
            </button>
          </form>
          <p className="muted">The username separates application data but is not a verified login. Do not use this as authentication for a public service.</p>
        </div>
      </main>
    );
  }

  return (
    <Routes>
      <Route element={<AppLayout />}>
        <Route index element={<DashboardPage />} />
        <Route path="groups" element={<GroupsPage />} />
        <Route path="groups/:id" element={<GroupDetailPage />} />
        <Route path="feed" element={<FeedPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="posts" element={<PostsPage />} />
        <Route path="scheduler" element={<SchedulerPage />} />
        <Route path="history" element={<HistoryPage />} />
        <Route path="notifications" element={<NotificationsPage />} />
        <Route path="opportunities" element={<OpportunitiesPage />} />
        <Route path="settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
