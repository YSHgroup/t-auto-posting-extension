import type {
  BotStatus,
  Dashboard,
  FeedItem,
  GroupAnalysis,
  GroupDetail,
  GroupMessage,
  GroupSearchResult,
  NotificationItem,
  OpportunityItem,
  Post,
  PostHistoryItem,
  SchedulerSettings,
} from "../types";
import { useSettingsStore } from "../stores/settingsStore";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const base = useSettingsStore.getState().apiBaseUrl.replace(/\/$/, "");
  const res = await fetch(`${base}/api${path}`, {
    headers: { "Content-Type": "application/json", ...(init?.headers || {}) },
    ...init,
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || res.statusText);
  }
  return res.json() as Promise<T>;
}

export const api = {
  health: () => request<{ status: string }>("/health"),
  dashboard: () => request<Dashboard>("/dashboard"),
  searchGroups: (q: string) => request<GroupSearchResult[]>(`/groups/search?q=${encodeURIComponent(q)}`),
  getGroup: (id: string) => request<GroupDetail>(`/groups/${id}`),
  getGroupMessages: (id: string, limit = 100) =>
    request<GroupMessage[]>(`/groups/${id}/messages?limit=${limit}`),
  simulateReply: (id: string, username: string, message: string, post_id?: string) =>
    request<GroupMessage>(`/groups/${id}/simulate-reply`, {
      method: "POST",
      body: JSON.stringify({ username, message, post_id }),
    }),
  analyzeGroup: (id: string) =>
    request<GroupAnalysis>(`/groups/${id}/analyze`, { method: "POST" }),
  listAnalysis: (id: string) => request<GroupAnalysis[]>(`/groups/${id}/analysis`),
  listFeed: () => request<FeedItem[]>("/feed"),
  addFeed: (group_id: string) => request<FeedItem>("/feed", { method: "POST", body: JSON.stringify({ group_id }) }),
  updateFeed: (id: string, body: Record<string, unknown>) =>
    request<FeedItem>(`/feed/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deleteFeed: (id: string) => request<{ ok: boolean }>(`/feed/${id}`, { method: "DELETE" }),
  reorderFeed: (items: { id: string; order_index: number }[]) =>
    request<FeedItem[]>("/feed/reorder", { method: "POST", body: JSON.stringify({ items }) }),
  listPosts: () => request<Post[]>("/posts"),
  createPost: (body: Partial<Post>) => request<Post>("/posts", { method: "POST", body: JSON.stringify(body) }),
  updatePost: (id: string, body: Partial<Post>) =>
    request<Post>(`/posts/${id}`, { method: "PUT", body: JSON.stringify(body) }),
  deletePost: (id: string) => request<{ ok: boolean }>(`/posts/${id}`, { method: "DELETE" }),
  duplicatePost: (id: string) => request<Post>(`/posts/${id}/duplicate`, { method: "POST" }),
  recommendPost: (feed_item_id: string) =>
    request<{ recommendations: { post_id: string; reason: string; confidence: number }[] }>(
      "/posts/recommend",
      { method: "POST", body: JSON.stringify({ feed_item_id }) },
    ),
  getScheduler: () => request<SchedulerSettings>("/scheduler"),
  updateScheduler: (body: Partial<SchedulerSettings>) =>
    request<SchedulerSettings>("/scheduler", { method: "PUT", body: JSON.stringify(body) }),
  startBot: () => request<BotStatus>("/bot/start", { method: "POST" }),
  stopBot: () => request<BotStatus>("/bot/stop", { method: "POST" }),
  botStatus: () => request<BotStatus>("/bot/status"),
  history: () => request<PostHistoryItem[]>("/history"),
  notifications: (filter: string) => request<NotificationItem[]>(`/notifications?filter=${filter}`),
  markRead: (id: string) => request<{ ok: boolean }>(`/notifications/${id}/read`, { method: "POST" }),
  markAllRead: () => request<{ ok: boolean }>("/notifications/read-all", { method: "POST" }),
  scanOpportunities: (groupId: string) =>
    request<unknown[]>(`/groups/${groupId}/opportunities`, { method: "POST" }),
  listOpportunities: () => request<OpportunityItem[]>("/opportunities"),
  getSettings: () => request<Record<string, unknown>>("/settings"),
  updateSettings: (body: Record<string, unknown>) =>
    request<Record<string, unknown>>("/settings", { method: "PUT", body: JSON.stringify(body) }),
  testConnection: () => request<{ ok: boolean; message: string }>("/settings/test-connection", { method: "POST" }),
  resetDemo: () => request<{ ok: boolean }>("/settings/reset-demo", { method: "POST" }),
};
