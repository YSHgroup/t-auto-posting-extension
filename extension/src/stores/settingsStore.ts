import { create } from "zustand";

const STORAGE_KEY = "telegram_auto_bot_settings";
const INSTALLATION_KEY = "telegram_auto_bot_installation_id";

interface SettingsState {
  apiBaseUrl: string;
  installationId: string;
  telegramUsername: string;
  connectionOk: boolean | null;
  load: () => Promise<void>;
  getInstallationId: () => Promise<string>;
  setApiBaseUrl: (url: string) => Promise<void>;
  setTelegramUsername: (username: string) => Promise<void>;
  getTelegramUsername: () => Promise<string>;
  testConnection: () => Promise<boolean>;
}

function storageGet<T>(key: string): Promise<T | undefined> {
  return new Promise((resolve) => {
    chrome.storage.local.get([key], (result) => resolve(result[key] as T | undefined));
  });
}

function storageSet(key: string, value: unknown): Promise<void> {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [key]: value }, resolve);
  });
}

export async function getInstallationId(): Promise<string> {
  const current = await storageGet<string>(INSTALLATION_KEY);
  if (current) return current;
  const created = crypto.randomUUID();
  await storageSet(INSTALLATION_KEY, created);
  return created;
}

async function readSettings(): Promise<{ apiBaseUrl: string; telegramUsername: string }> {
  const data = await storageGet<{ apiBaseUrl?: string; telegramUsername?: string }>(STORAGE_KEY);
  return {
    apiBaseUrl: data?.apiBaseUrl || "http://localhost:8000",
    telegramUsername: data?.telegramUsername || "",
  };
}

async function writeSettings(patch: { apiBaseUrl?: string; telegramUsername?: string }): Promise<void> {
  const data = await storageGet<{ apiBaseUrl?: string; telegramUsername?: string }>(STORAGE_KEY);
  await storageSet(STORAGE_KEY, { ...data, ...patch });
}

export async function getTelegramUsername(): Promise<string> {
  const data = await storageGet<{ telegramUsername?: string }>(STORAGE_KEY);
  return (data?.telegramUsername || "").trim().replace(/^@/, "").toLowerCase();
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  apiBaseUrl: "http://localhost:8000",
  installationId: "",
  telegramUsername: "",
  connectionOk: null,
  load: async () => {
    const [stored, installationId] = await Promise.all([readSettings(), getInstallationId()]);
    set({ apiBaseUrl: stored.apiBaseUrl, telegramUsername: stored.telegramUsername, installationId });
  },
  getInstallationId,
  setApiBaseUrl: async (url: string) => {
    await writeSettings({ apiBaseUrl: url });
    set({ apiBaseUrl: url, connectionOk: null });
  },
  setTelegramUsername: async (value: string) => {
    const username = value.trim().replace(/^@/, "").toLowerCase();
    await writeSettings({ telegramUsername: username });
    set({ telegramUsername: username, connectionOk: null });
  },
  getTelegramUsername,
  testConnection: async () => {
    try {
      const [base, installationId, telegramUsername] = await Promise.all([
        Promise.resolve(get().apiBaseUrl.replace(/\/$/, "")),
        getInstallationId(),
        getTelegramUsername(),
      ]);
      if (!telegramUsername) throw new Error("Enter your Telegram username in Settings first.");
      const res = await fetch(`${base}/api/health`, {
        headers: {
          "X-Installation-ID": installationId,
          "X-Telegram-Username": telegramUsername,
        },
      });
      const ok = res.ok;
      set({ connectionOk: ok, installationId, telegramUsername });
      return ok;
    } catch {
      set({ connectionOk: false });
      return false;
    }
  },
}));
