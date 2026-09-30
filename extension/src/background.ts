chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => undefined);

const SETTINGS_KEY = "telegram_auto_bot_settings";
const INSTALLATION_KEY = "telegram_auto_bot_installation_id";
const NAVIGATION_KEY = "telegram_auto_bot_navigation";
const NAVIGATION_ALARM = "telegram-auto-bot-group-navigation";

type NavigationState = {
	enabled: boolean;
	cursor: number;
	lastRunAt: string | null;
};

type ScheduledFeedItem = {
	id: string;
	enabled: boolean;
	order_index: number;
	group_name?: string;
	group_telegram_url?: string | null;
};

async function loadIdentity(): Promise<{ base: string; installationId: string; telegramUsername: string }> {
	const stored = await chrome.storage.local.get([SETTINGS_KEY, INSTALLATION_KEY]);
	let installationId = stored[INSTALLATION_KEY] as string | undefined;
	if (!installationId) {
		installationId = crypto.randomUUID();
		await chrome.storage.local.set({ [INSTALLATION_KEY]: installationId });
	}
	const settings = stored[SETTINGS_KEY] as { apiBaseUrl?: string; telegramUsername?: string } | undefined;
	const telegramUsername = (settings?.telegramUsername || "").trim().replace(/^@/, "").toLowerCase();
	if (!telegramUsername) throw new Error("Enter your Telegram username in extension Settings first.");
	return {
		base: (settings?.apiBaseUrl || "http://localhost:8000").replace(/\/$/, ""),
		installationId,
		telegramUsername,
	};
}

async function apiRequest<T>(path: string): Promise<T> {
	const identity = await loadIdentity();
	const response = await fetch(`${identity.base}/api${path}`, {
		headers: {
			"X-Installation-ID": identity.installationId,
			"X-Telegram-Username": identity.telegramUsername,
		},
	});
	if (!response.ok) throw new Error(await response.text());
	return response.json() as Promise<T>;
}

function localScheduleParts(now: Date, timezone: string): { weekday: number; minutes: number } {
	const parts = new Intl.DateTimeFormat("en-US", {
		timeZone: timezone,
		weekday: "short",
		hour: "2-digit",
		minute: "2-digit",
		hourCycle: "h23",
	}).formatToParts(now);
	const values = Object.fromEntries(parts.map((part) => [part.type, part.value]));
	const weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].indexOf(values.weekday || "");
	return { weekday, minutes: Number(values.hour) * 60 + Number(values.minute) };
}

async function notify(title: string, message: string): Promise<void> {
	await chrome.notifications.create({
		type: "basic",
		iconUrl: chrome.runtime.getURL("notification-icon.svg"),
		title,
		message,
	});
}

async function runNavigationTick(): Promise<void> {
	const stored = await chrome.storage.local.get([NAVIGATION_KEY]);
	const state = stored[NAVIGATION_KEY] as NavigationState | undefined;
	if (!state?.enabled) return;

	const scheduler = await apiRequest<{
		start_time: string;
		end_time: string;
		working_days: number[];
		posting_interval_minutes: number;
		timezone: string;
	}>("/scheduler");
	const { weekday, minutes } = localScheduleParts(new Date(), scheduler.timezone || "UTC");
	const [startHour, startMinute] = scheduler.start_time.split(":").map(Number);
	const [endHour, endMinute] = scheduler.end_time.split(":").map(Number);
	const start = startHour * 60 + startMinute;
	const end = endHour * 60 + endMinute;
	if (!scheduler.working_days.includes(weekday) || minutes < start || minutes > end) return;

	const now = Date.now();
	const lastRun = state.lastRunAt ? Date.parse(state.lastRunAt) : NaN;
	if (Number.isFinite(lastRun) && now - lastRun < Math.max(1, scheduler.posting_interval_minutes) * 60_000) return;

	const feed = await apiRequest<ScheduledFeedItem[]>("/feed");
	const items = feed.filter((item) => item.enabled).sort((a, b) => a.order_index - b.order_index);
	if (!items.length) {
		await chrome.storage.local.set({ [NAVIGATION_KEY]: { ...state, lastRunAt: new Date(now).toISOString() } });
		await notify("Telegram group navigation", "No enabled groups are currently in your feed.");
		return;
	}

	const index = state.cursor % items.length;
	const item = items[index];
	const nextState: NavigationState = {
		...state,
		cursor: (index + 1) % items.length,
		lastRunAt: new Date(now).toISOString(),
	};
	await chrome.storage.local.set({ [NAVIGATION_KEY]: nextState });

	if (!item.group_telegram_url) {
		await notify("Telegram group needs a link", `${item.group_name || "Feed group"} has no saved Telegram URL.`);
		return;
	}
	let target: URL;
	try {
		target = new URL(item.group_telegram_url);
	} catch {
		await notify("Invalid Telegram group link", `${item.group_name || "Feed group"} has an invalid saved URL.`);
		return;
	}
	if (target.protocol !== "https:" || !["web.telegram.org", "t.me", "www.t.me"].includes(target.hostname)) {
		await notify("Invalid Telegram group link", "Only HTTPS links to Telegram are allowed for scheduled navigation.");
		return;
	}

	const tabs = await chrome.tabs.query({ url: ["https://web.telegram.org/*", "https://t.me/*"] });
	if (tabs[0]?.id !== undefined) {
		await chrome.tabs.update(tabs[0].id, { url: target.toString(), active: true });
		if (tabs[0].windowId !== undefined) await chrome.windows.update(tabs[0].windowId, { focused: true });
	} else {
		await chrome.tabs.create({ url: target.toString(), active: true });
	}

	let importedCountText = "Imported message count unavailable.";
	try {
		const count = await apiRequest<{
			imported_message_count: number;
			basis: string;
		}>(`/feed/${encodeURIComponent(item.id)}/imported-message-count`);
		importedCountText = `${count.imported_message_count} manually imported messages since the last recorded manual send. This is not a live Telegram count.`;
	} catch {
		// Navigation should proceed even when the backend count request is unavailable.
	}
	await notify(`Opened ${item.group_name || "Telegram group"}`, importedCountText);
}

function ensureNavigationAlarm(): void {
	void chrome.alarms.create(NAVIGATION_ALARM, { periodInMinutes: 1 });
}

chrome.runtime.onStartup.addListener(ensureNavigationAlarm);
chrome.runtime.onInstalled.addListener(ensureNavigationAlarm);
ensureNavigationAlarm();
chrome.alarms.onAlarm.addListener((alarm) => {
	if (alarm.name === NAVIGATION_ALARM) {
		void runNavigationTick().catch((error: unknown) => {
			void notify("Scheduled navigation failed", error instanceof Error ? error.message : "Could not open the next group.");
		});
	}
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	if (sender.id === chrome.runtime.id && message?.type === "telegram-auto-bot-navigation") {
		void (async () => {
			if (message.action === "start") {
				await loadIdentity();
				await chrome.storage.local.set({ [NAVIGATION_KEY]: { enabled: true, cursor: 0, lastRunAt: null } satisfies NavigationState });
				ensureNavigationAlarm();
				sendResponse({ ok: true, enabled: true });
				return;
			}
			const stored = await chrome.storage.local.get([NAVIGATION_KEY]);
			const current = stored[NAVIGATION_KEY] as NavigationState | undefined;
			await chrome.storage.local.set({ [NAVIGATION_KEY]: { ...(current || {}), enabled: false } });
			sendResponse({ ok: true, enabled: false });
		})().catch((error: unknown) => sendResponse({ ok: false, error: error instanceof Error ? error.message : "Navigation control failed" }));
		return true;
	}
	if (!sender.url?.startsWith("https://web.telegram.org/")) return false;
	if (message?.type !== "telegram-auto-bot-intake") return false;

	void (async () => {
		const identity = await loadIdentity();
		const path = typeof message.path === "string" ? message.path : "";
		if (path !== "/api/groups/intake" && !path.startsWith("/api/groups/intake-status/")) {
			sendResponse({ ok: false, error: "Unsupported request" });
			return;
		}
		const response = await fetch(`${identity.base}${path}`, {
			method: message.body ? "POST" : "GET",
			headers: {
				"X-Installation-ID": identity.installationId,
				"X-Telegram-Username": identity.telegramUsername,
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
