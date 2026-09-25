export type Page = 'Dashboard' | 'Groups' | 'Feed' | 'Posts' | 'Scheduler' | 'Notifications' | 'Opportunities' | 'Settings'
export type BotState = 'RUNNING' | 'STOPPED'
export type PostType = 'Partnership' | 'Job' | 'Investment' | 'Business' | 'General' | 'Custom'

export interface Group { id: string; name: string; username: string; description: string; member_count: number; category: string; keywords: string[]; joined: boolean }
export interface Post { id: string; title: string; post_type: PostType; content: string; enabled: boolean; usage_count: number; created_at: string }
export interface FeedItem { id: string; group: Group; position: number; enabled: boolean; selected_post_id: string | null; last_posted: string | null; post_count: number; next_scheduled_time: string }
export interface HistoryItem { id: string; group_id: string; group_name: string; post_id: string | null; post_title: string | null; status: 'success' | 'skipped' | 'failed'; reason: string; message_id: string | null; posted_at: string }
export interface Opportunity { id: string; group_id: string; group_name: string; username: string; category: 'investment' | 'partnership'; evidence: string; evidence_level: string; confidence: number }
export interface Notification { id: string; group_name: string; username: string; message: string; post_id: string; created_at: string; read: boolean }
export interface Dashboard { groups: number; active_feed: number; total_posts: number; posts_today: number; skipped_posts: number; replies: number; unread_notifications: number; investors: number; partners: number }
export interface Analysis { activities: string[]; member_types: string[]; partnership: { status: string; reason: string; confidence: number }; job: { status: string; reason: string; confidence: number }; posting_style: string[]; risks: string[] }
export interface Scheduler { auto_mode: boolean; start_time: string; end_time: string; working_days: string[]; posting_interval: number; minimum_messages: number; maximum_posts_per_day: number; timezone: string }
