import type { Analysis, Dashboard, FeedItem, Group, HistoryItem, Notification, Opportunity, Post, Scheduler } from '../types'

const defaultUrl = 'http://localhost:8000'
export const getApiUrl = () => localStorage.getItem('telegram-auto-bot-api-url') || defaultUrl
export const setApiUrl = (url: string) => localStorage.setItem('telegram-auto-bot-api-url', url.replace(/\/$/, ''))

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiUrl()}${path}`, { headers: { 'Content-Type': 'application/json' }, ...options })
  if (!response.ok) throw new Error(`API request failed: ${response.status}`)
  return response.json() as Promise<T>
}

export const api = {
  health: () => request<{ status: string; mode: string }>('/api/health'),
  dashboard: () => request<Dashboard>('/api/dashboard'),
  groups: (query: string) => request<Group[]>(`/api/groups/search?q=${encodeURIComponent(query)}`),
  analyze: (id: string) => request<Analysis>(`/api/groups/${id}/analyze`, { method: 'POST' }),
  feed: () => request<FeedItem[]>('/api/feed'),
  addFeed: (group_id: string) => request<FeedItem>('/api/feed', { method: 'POST', body: JSON.stringify({ group_id }) }),
  updateFeed: (id: string, input: Pick<FeedItem, 'selected_post_id' | 'enabled'>) => request<FeedItem>(`/api/feed/${id}`, { method: 'PUT', body: JSON.stringify({ group_id: '', ...input }) }),
  posts: () => request<Post[]>('/api/posts'),
  createPost: (input: Pick<Post, 'title' | 'post_type' | 'content'>) => request<Post>('/api/posts', { method: 'POST', body: JSON.stringify(input) }),
  updatePost: (id: string, input: Pick<Post, 'title' | 'post_type' | 'content' | 'enabled'>) => request<Post>(`/api/posts/${id}`, { method: 'PUT', body: JSON.stringify(input) }),
  history: () => request<HistoryItem[]>('/api/history'),
  scheduler: () => request<Scheduler>('/api/scheduler'),
  saveScheduler: (settings: Scheduler) => request<Scheduler>('/api/scheduler', { method: 'PUT', body: JSON.stringify(settings) }),
  botStatus: () => request<{ state: string }>('/api/bot/status'),
  bot: (action: 'start' | 'stop') => request<{ state: string }>(`/api/bot/${action}`, { method: 'POST' }),
  opportunities: (groupId: string) => request<Opportunity[]>(`/api/groups/${groupId}/opportunities`, { method: 'POST' }),
  duplicatePost: (id: string) => request<Post>(`/api/posts/${id}/duplicate`, { method: 'POST' }),
  notifications: () => request<Notification[]>('/api/notifications'),
  markNotificationRead: (id: string) => request<Notification>(`/api/notifications/${id}/read`, { method: 'POST' }),
  markAllNotificationsRead: () => request<{ updated: number }>('/api/notifications/read-all', { method: 'POST' }),
}
