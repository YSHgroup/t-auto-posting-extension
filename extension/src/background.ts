chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch(() => undefined);

const SETTINGS_KEY = "telegram_auto_bot_settings";
const INSTALLATION_KEY = "telegram_auto_bot_installation_id";
const NAVIGATION_KEY_PREFIX = "telegram_auto_bot_navigation:";
const NAVIGATION_ALARM = "telegram-auto-bot-group-navigation";
const LOCAL_NAVIGATION_ALARM = "telegram-auto-bot-local-navigation";

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

function navigationKey(telegramUsername: string): string {
	return `${NAVIGATION_KEY_PREFIX}${telegramUsername}`;
}

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

async function runNavigationTick(forceLocal = false): Promise<void> {
	let identity: Awaited<ReturnType<typeof loadIdentity>>;
	try {
		identity = await loadIdentity();
	} catch {
		return;
	}
	const key = navigationKey(identity.telegramUsername);
	const stored = await chrome.storage.local.get([key]);
	const state = stored[key] as NavigationState | undefined;
	if (!state?.enabled) return;

	// When invoked by the local/frontend alarm, bypass backend schedule time-window checks
	let scheduler: { posting_interval_minutes: number; timezone?: string } | null = null;
	try {
		scheduler = await apiRequest<{ posting_interval_minutes: number; timezone?: string }>("/scheduler");
	} catch {
		scheduler = null;
	}

	if (!forceLocal) {
		// server-controlled scheduling: validate working days and time window when possible
		try {
			const full = await apiRequest<{
				start_time: string;
				end_time: string;
				working_days: number[];
				posting_interval_minutes: number;
				timezone: string;
			}>("/scheduler");
			const { weekday, minutes } = localScheduleParts(new Date(), full.timezone || "UTC");
			const [startHour, startMinute] = full.start_time.split(":").map(Number);
			const [endHour, endMinute] = full.end_time.split(":").map(Number);
			const start = startHour * 60 + startMinute;
			const end = endHour * 60 + endMinute;
			if (!full.working_days.includes(weekday) || minutes < start || minutes > end) return;

			const now = Date.now();
			const lastRun = state.lastRunAt ? Date.parse(state.lastRunAt) : NaN;
			if (Number.isFinite(lastRun) && now - lastRun < Math.max(1, full.posting_interval_minutes) * 60_000) return;
		} catch {
			// if scheduler fetch fails, continue conservatively
		}
	}

	const feed = await apiRequest<ScheduledFeedItem[]>("/feed");
	const items = feed.filter((item) => item.enabled).sort((a, b) => a.order_index - b.order_index);
	if (!items.length) {
		await chrome.storage.local.set({ [key]: { ...state, lastRunAt: new Date(now).toISOString() } });
		await notify("Telegram group navigation", "No enabled groups are currently in your feed.");
		return;
	}

	const now = Date.now();

	// Find next feed item with a valid Telegram URL, scanning up to items.length entries.
	let attempts = 0;
	let currentIndex = state.cursor % items.length;
	let item: ScheduledFeedItem | null = null;
	while (attempts < items.length) {
		const candidate = items[currentIndex];
		if (candidate.group_telegram_url) {
			item = candidate;
			break;
		}
		// skip and advance cursor
		await notify("Telegram group needs a link", `${candidate.group_name || "Feed group"} has no saved Telegram URL. Skipping.`);
		currentIndex = (currentIndex + 1) % items.length;
		attempts++;
	}

	if (!item) {
		// no valid items
		const nextState: NavigationState = {
			...state,
			cursor: state.cursor % items.length,
			lastRunAt: new Date(now).toISOString(),
		};
		await chrome.storage.local.set({ [key]: nextState });
		await notify("Telegram group navigation", "No enabled feed groups have a valid Telegram URL.");
		return;
	}

	// advance stored cursor past the selected item
	const selectedIndex = currentIndex;
	const nextState: NavigationState = {
		...state,
		cursor: (selectedIndex + 1) % items.length,
		lastRunAt: new Date(now).toISOString(),
	};
	await chrome.storage.local.set({ [key]: nextState });

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

		// Open or update a tab and keep a reference to the opened tab object so we can message it later.
		let openedTab: chrome.tabs.Tab | null = null;
		const existingTabs = await chrome.tabs.query({ url: ["https://web.telegram.org/*", "https://t.me/*"] });
		if (existingTabs[0]?.id !== undefined) {
			// update the first matching tab
			openedTab = await chrome.tabs.update(existingTabs[0].id, { url: target.toString(), active: true });
			if (existingTabs[0].windowId !== undefined) await chrome.windows.update(existingTabs[0].windowId, { focused: true });
		} else {
			openedTab = await chrome.tabs.create({ url: target.toString(), active: true });
		}

		// If the bot is running on the server, attempt a live post via the content script.
		try {
			const botStatus = await apiRequest<{ state: string }>(`/bot/status`);
			if (botStatus?.state === "RUNNING") {
				// Fetch fresh feed info to get selected_post_id
				const feed = await apiRequest<Array<{ id: string; selected_post_id?: string }>>(`/feed`);
				const current = feed.find((f) => f.id === item.id);
				if (current?.selected_post_id) {
					// get post content
					try {
						const post = await apiRequest<{ content: string }>(`/posts/${encodeURIComponent(current.selected_post_id)}`);
						const tabId = openedTab?.id;
						if (tabId !== undefined) {
							// attempt to send a perform_post request to the content script with retries
							const maxTries = 6;
							let performed = false;
							for (let attempt = 0; attempt < maxTries && !performed; attempt++) {
								try {
												const resp = await new Promise<any>((resolve, reject) => {
													console.debug("[background] sending perform_post to tab", tabId, { minMessages: scheduler.minimum_messages });
													chrome.tabs.sendMessage(tabId, { type: "telegram-auto-bot-action", action: "perform_post", content: post.content, minMessages: scheduler.minimum_messages }, (r) => {
														if (chrome.runtime.lastError) {
															console.error("[background] sendMessage error", chrome.runtime.lastError.message);
															return reject(new Error(chrome.runtime.lastError.message));
														}
														console.debug("[background] received response from content script", r);
														resolve(r);
													});
												});
									if (resp && resp.ok) {
										performed = true;
										// record the manual post in the backend and notify UI listeners
										try {
											const resp = await fetch(`${identity.base}/api/feed/${encodeURIComponent(item.id)}/record-manual-post`, {
												method: "POST",
												headers: {
													"X-Installation-ID": identity.installationId,
													"X-Telegram-Username": identity.telegramUsername,
													"Content-Type": "application/json",
												},
											});
											if (resp.ok) {
												const record = await resp.json();
												void notify("Posted to group", `${item.group_name || "Group"} — post recorded.`);
												try {
													chrome.runtime.sendMessage({ type: "telegram-auto-bot-posted", posted_at: record.posted_at });
												} catch {
													// ignore messaging errors
												}
											} else {
												void notify("Posted to group", `${item.group_name || "Group"} — posted but could not record.`);
											}
										} catch {
											void notify("Posted to group", `${item.group_name || "Group"} — posted but could not record.`);
										}
										break;
									} else if (resp && resp.reason === "not_enough_messages") {
										const count = resp.details?.count ?? 0;
										void notify("Skipped group (not enough messages)", `${item.group_name || "Group"}: ${count} < ${scheduler.minimum_messages}`);
										performed = true; // treat as handled
										break;
									}
								} catch (err) {
									console.warn("[background] perform_post attempt failed", attempt, err instanceof Error ? err.message : err);
									// wait then retry
									await new Promise((r) => setTimeout(r, 1000 * (attempt + 1)));
								}
							}
												if (!performed) {
													void notify("Posting failed", `Could not perform post to ${item.group_name || "Group"}. Ensure Telegram is open and the content script is active.`);
												}
						}
						} catch (e) {
							console.error("[background] error fetching post content", e);
							// ignore post fetch errors and continue to the imported count notification below
						}
				}
			}
		} catch {
				console.warn("[background] bot status check failed");
				// ignore bot status check errors and continue
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
		void runNavigationTick(false).catch((error: unknown) => {
			void notify("Scheduled navigation failed", error instanceof Error ? error.message : "Could not open the next group.");
		});
	}
	if (alarm.name === LOCAL_NAVIGATION_ALARM) {
		// Local frontend-controlled alarm should trigger an immediate navigation tick
		void runNavigationTick(true).catch((error: unknown) => {
			void notify("Local navigation failed", error instanceof Error ? error.message : "Could not open the next group.");
		});
	}
});

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
	if (message?.type === "telegram-auto-bot-local") {
		void (async () => {
			const action = (message.action as string) || "";
			const identity = await loadIdentity();
			// helper to get posting interval
			let postingInterval = 1;
			try {
				const sched = await apiRequest<{ posting_interval_minutes: number }>("/scheduler");
				postingInterval = Math.max(1, sched.posting_interval_minutes || 1);
			} catch {
				postingInterval = 1;
			}

			const key = navigationKey(identity.telegramUsername);

			if (action === "start") {
				// enable navigation state and schedule first run after 15s
				const now = Date.now();
				await chrome.storage.local.set({ [key]: { enabled: true, cursor: 0, lastRunAt: null } });
				chrome.alarms.clear(LOCAL_NAVIGATION_ALARM);
				chrome.alarms.create(LOCAL_NAVIGATION_ALARM, { when: now + 15000, periodInMinutes: postingInterval });
				sendResponse({ ok: true });
				return;
			}

			if (action === "stop") {
				// capture remaining time until next alarm and clear it
				chrome.alarms.get(LOCAL_NAVIGATION_ALARM, (alarm) => {
					const now = Date.now();
					const remaining = alarm?.scheduledTime ? Math.max(0, (alarm.scheduledTime as number) - now) : postingInterval * 60_000;
					chrome.storage.local.get([key]).then((stored) => {
						const s = stored[key] as (NavigationState & { pausedRemainingMs?: number }) | undefined;
						const ns: any = { ...(s || { enabled: false, cursor: 0, lastRunAt: null }) };
						ns.enabled = false;
						ns.pausedRemainingMs = remaining;
						chrome.storage.local.set({ [key]: ns }).then(() => {
							chrome.alarms.clear(LOCAL_NAVIGATION_ALARM, () => sendResponse({ ok: true }));
						});
					});
				});
				return true;
			}

			if (action === "resume") {
				// read pausedRemainingMs and schedule alarm accordingly
				const stored = await chrome.storage.local.get([key]);
				const s = stored[key] as NavigationState & { pausedRemainingMs?: number } | undefined;
				const remaining = (s && (s as any).pausedRemainingMs) || postingInterval * 60_000;
				const when = Date.now() + Number(remaining || postingInterval * 60_000);
				await chrome.storage.local.set({ [key]: { ...(s || { enabled: false, cursor: 0, lastRunAt: null }), enabled: true } });
				chrome.alarms.clear(LOCAL_NAVIGATION_ALARM);
				chrome.alarms.create(LOCAL_NAVIGATION_ALARM, { when, periodInMinutes: postingInterval });
				sendResponse({ ok: true });
				return;
			}

			if (action === "reset") {
				// reset cursor and timer to start fresh
				const now = Date.now();
				await chrome.storage.local.set({ [key]: { enabled: true, cursor: 0, lastRunAt: null } });
				chrome.alarms.clear(LOCAL_NAVIGATION_ALARM);
				chrome.alarms.create(LOCAL_NAVIGATION_ALARM, { when: now + 15000, periodInMinutes: postingInterval });
				sendResponse({ ok: true });
				return;
			}
			sendResponse({ ok: false, error: "unknown_action" });
		})().catch((err) => sendResponse({ ok: false, error: err instanceof Error ? err.message : String(err) }));
		return true;
	}
	if (sender.id === chrome.runtime.id && message?.type === "telegram-auto-bot-navigation") {
		void (async () => {
			if (message.action === "start") {
				const identity = await loadIdentity();
				await chrome.storage.local.set({
					[navigationKey(identity.telegramUsername)]: {
						enabled: true,
						cursor: 0,
						lastRunAt: null,
					} satisfies NavigationState,
				});
				ensureNavigationAlarm();
				// run immediately so the user sees activity right away
				void runNavigationTick();
				sendResponse({ ok: true, enabled: true });
				return;
			}
			const identity = await loadIdentity();
			const key = navigationKey(identity.telegramUsername);
			const stored = await chrome.storage.local.get([key]);
			const current = stored[key] as NavigationState | undefined;
			await chrome.storage.local.set({ [key]: { ...(current || {}), enabled: false } });
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
