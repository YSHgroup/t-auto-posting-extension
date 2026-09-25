export interface GroupSearchResult {
  id: string;
  name: string;
  username: string;
  description: string;
  member_count: number;
  categories: string[];
  joined: boolean;
  relevance: number;
}

export interface GroupDetail {
  id: string;
  external_id: string;
  name: string;
  username: string;
  description: string;
  member_count: number;
  categories: string[];
  joined: boolean;
}

export interface GroupMessage {
  id: string;
  username: string | null;
  content: string;
  created_at: string;
  is_app_post: boolean;
}

export interface GroupAnalysis {
  id: string;
  summary: string;
  member_types: string[];
  activities: string[];
  partnership_status: string;
  partnership_reason: string;
  partnership_confidence: number;
  job_status: string;
  job_reason: string;
  job_confidence: number;
  posting_style: string[];
  risks: { text: string; source: string }[];
  created_at: string;
}

export interface Post {
  id: string;
  title: string;
  post_type: string;
  content: string;
  status: string;
  usage_count: number;
  enabled: boolean;
  created_at: string;
}

export interface FeedItem {
  id: string;
  group_id: string;
  order_index: number;
  enabled: boolean;
  post_count: number;
  last_posted_at: string | null;
  group_name?: string;
  group_external_id?: string;
  selected_post_id?: string | null;
  selected_post_title?: string | null;
}

export interface Dashboard {
  total_groups: number;
  active_feed_groups: number;
  total_posts: number;
  posts_today: number;
  skipped_posts: number;
  replies: number;
  unread_notifications: number;
  potential_investors: number;
  potential_partners: number;
}

export interface BotStatus {
  state: string;
  current_feed_index: number;
  last_error?: string | null;
}

export interface SchedulerSettings {
  auto_mode: boolean;
  start_time: string;
  end_time: string;
  working_days: number[];
  posting_interval_minutes: number;
  minimum_messages: number;
  maximum_posts_per_day: number;
  timezone: string;
}

export interface NotificationItem {
  id: string;
  username?: string;
  message: string;
  read: boolean;
  created_at: string;
}

export interface OpportunityItem {
  id: string;
  group_name: string;
  username: string;
  category: string;
  evidence: string;
  evidence_level: string;
  confidence: number;
}

export interface PostHistoryItem {
  id: string;
  group_name: string;
  post_title?: string;
  status: string;
  reason?: string;
  posted_at: string;
}
