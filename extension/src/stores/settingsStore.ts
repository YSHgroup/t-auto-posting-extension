import { create } from "zustand";

const STORAGE_KEY = "telegram_auto_bot_settings";

interface SettingsState {
  apiBaseUrl: string;
  connectionOk: boolean | null;
  load: () => Promise<void>;
  setApiBaseUrl: (url: string) => Promise<void>;
  testConnection: () => Promise<boolean>;
}

async function readStorage(): Promise<string> {
  return new Promise((resolve) => {
    chrome.storage.local.get([STORAGE_KEY], (result) => {
      const data = result[STORAGE_KEY] as { apiBaseUrl?: string } | undefined;
      resolve(data?.apiBaseUrl || "http://localhost:8000");
    });
  });
}

async function writeStorage(apiBaseUrl: string): Promise<void> {
  return new Promise((resolve) => {
    chrome.storage.local.set({ [STORAGE_KEY]: { apiBaseUrl } }, () => resolve());
  });
}

export const useSettingsStore = create<SettingsState>((set, get) => ({
  apiBaseUrl: "http://localhost:8000",
  connectionOk: null,
  load: async () => {
    const url = await readStorage();
    set({ apiBaseUrl: url });
  },
  setApiBaseUrl: async (url: string) => {
    await writeStorage(url);
    set({ apiBaseUrl: url, connectionOk: null });
  },
  testConnection: async () => {
    try {
      const base = get().apiBaseUrl.replace(/\/$/, "");
      const res = await fetch(`${base}/api/health`);
      const ok = res.ok;
      set({ connectionOk: ok });
      return ok;
    } catch {
      set({ connectionOk: false });
      return false;
    }
  },
}));
