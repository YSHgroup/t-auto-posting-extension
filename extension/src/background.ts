chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => undefined);

const SETTINGS_KEY = "telegram_auto_bot_settings";
const INSTALLATION_KEY = "telegram_auto_bot_installation_id";

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	if (!sender.url?.startsWith("https://web.telegram.org/")) return false;
	if (message?.type !== "telegram-auto-bot-intake") return false;

	void (async () => {
		const stored = await chrome.storage.local.get([SETTINGS_KEY, INSTALLATION_KEY]);
		let installationId = stored[INSTALLATION_KEY] as string | undefined;
		if (!installationId) {
			installationId = crypto.randomUUID();
			await chrome.storage.local.set({ [INSTALLATION_KEY]: installationId });
		}
		const settings = stored[SETTINGS_KEY] as { apiBaseUrl?: string } | undefined;
		const base = (settings?.apiBaseUrl || "http://localhost:8000").replace(/\/$/, "");
		const path = typeof message.path === "string" ? message.path : "";
		if (path !== "/api/groups/intake" && !path.startsWith("/api/groups/intake-status/")) {
			sendResponse({ ok: false, error: "Unsupported request" });
			return;
		}
		const response = await fetch(`${base}${path}`, {
			method: message.body ? "POST" : "GET",
			headers: {
				"X-Installation-ID": installationId,
				...(message.body ? { "Content-Type": "application/json" } : {}),
			},
			...(message.body ? { body: JSON.stringify(message.body) } : {}),
		});
		const content = await response.text();
		sendResponse({ ok: response.ok, content });
	})().catch((error: unknown) => {
		sendResponse({ ok: false, error: error instanceof Error ? error.message : "Request failed" });
	});
	return true;
});
