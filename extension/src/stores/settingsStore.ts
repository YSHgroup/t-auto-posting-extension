import { create } from "zustand";

const STORAGE_KEY = "telegram_auto_bot_settings";
const INSTALLATION_KEY = "telegram_auto_bot_installation_id";

interface SettingsState {
  apiBaseUrl: string;
  installationId: string;
  connectionOk: boolean | null;
  load: () => Promise<void>;
  getInstallationId: () => Promise<string>;
  setApiBaseUrl: (url: string) => Promise<void>;
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

async function readSettings(): Promise<string> {
  const data = await storageGet<{ apiBaseUrl?: string }>(STORAGE_KEY);
  return data?.apiBaseUrl || "http://localhost:8000";
}

async function writeSettings(apiBaseUrl: string): Promise<void> {
  await storageSet(STORAGE_KEY, { apiBaseUrl });
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  apiBaseUrl: "http://localhost:8000",
  installationId: "",
  connectionOk: null,
  load: async () => {
    const [url, installationId] = await Promise.all([readSettings(), getInstallationId()]);
    set({ apiBaseUrl: url, installationId });
  },
  getInstallationId,
  setApiBaseUrl: async (url: string) => {
    await writeSettings(url);
    set({ apiBaseUrl: url, connectionOk: null });
  },
  testConnection: async () => {
    try {
      const [base, installationId] = await Promise.all([
        Promise.resolve(get().apiBaseUrl.replace(/\/$/, "")),
        getInstallationId(),
      ]);
      const res = await fetch(`${base}/api/health`, {
        headers: { "X-Installation-ID": installationId },
      });
      const ok = res.ok;
      set({ connectionOk: ok, installationId });
      return ok;
    } catch {
      set({ connectionOk: false });
      return false;
    }
  },
}));
