from __future__ import annotations

from datetime import UTC, datetime
from contextlib import asynccontextmanager
import logging
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from app.schemas import BotStatus, Dashboard, FeedItem, GroupAnalysis, HistoryItem, Opportunity, Post, SchedulerSettings
from app.services.store import DemoStore
from app.workers.scheduler import SchedulerWorker
from app.database.init_db import init_db
from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

store = DemoStore()
worker = SchedulerWorker(store)

@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        init_db()
    except Exception as error:
        logger.warning("Database unavailable; continuing in mock memory mode: %s", error)
    worker.start()
    yield
    worker.stop()

app = FastAPI(title="Telegram Auto Bot API", version="0.1.0", description="Independent automation server. No Telegram integration.", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")], allow_credentials=False, allow_methods=["*"], allow_headers=["*"])

class PostInput(BaseModel):
    title: str
    post_type: str
    content: str
    enabled: bool = True

class FeedInput(BaseModel):
    group_id: str
    selected_post_id: str | None = None
    enabled: bool = True

@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": settings.ai_provider}

@app.get("/api/dashboard", response_model=Dashboard)
def dashboard() -> Dashboard:
    return store.dashboard()

@app.get("/api/groups/search")
def search_groups(q: str = Query(default="")) -> list[dict]:
    return [group.model_dump() for group in store.data.search_groups(q)]

@app.get("/api/groups/{group_id}")
def get_group(group_id: str) -> dict:
    group = store.data.get_group(group_id)
    if group is None:
        raise HTTPException(404, "Group not found")
    return group.model_dump()

@app.get("/api/groups/{group_id}/messages")
def get_messages(group_id: str, limit: int = Query(default=500, le=500)) -> list[dict]:
    if store.data.get_group(group_id) is None:
        raise HTTPException(404, "Group not found")
    return [message.model_dump(mode="json") for message in store.data.get_messages(group_id, limit)]

@app.post("/api/groups/{group_id}/analyze", response_model=GroupAnalysis)
async def analyze_group(group_id: str) -> GroupAnalysis:
    group = store.data.get_group(group_id)
    if group is None:
        raise HTTPException(404, "Group not found")
    analysis = await store.ai.analyze_group(group)
    store.analyses[group_id] = analysis
    return analysis

@app.get("/api/feed", response_model=list[FeedItem])
def get_feed() -> list[FeedItem]:
    return store.feed

@app.post("/api/feed", response_model=FeedItem)
def add_feed(input: FeedInput) -> FeedItem:
    try:
        item = store.add_to_feed(input.group_id)
    except ValueError as error:
        raise HTTPException(404, str(error)) from error
    item.enabled = input.enabled
    if input.selected_post_id:
        item.selected_post_id = input.selected_post_id
    return item

@app.put("/api/feed/{feed_id}", response_model=FeedItem)
def update_feed(feed_id: str, input: FeedInput) -> FeedItem:
    item = next((entry for entry in store.feed if entry.id == feed_id), None)
    if item is None:
        raise HTTPException(404, "Feed item not found")
    item.enabled = input.enabled
    item.selected_post_id = input.selected_post_id
    return item

@app.delete("/api/feed/{feed_id}")
def delete_feed(feed_id: str) -> dict[str, bool]:
    store.feed = [item for item in store.feed if item.id != feed_id]
    return {"ok": True}

@app.get("/api/posts", response_model=list[Post])
def get_posts() -> list[Post]:
    return list(store.posts.values())

@app.post("/api/posts", response_model=Post)
def create_post(input: PostInput) -> Post:
    post = Post(id=__import__("uuid").uuid4().hex, title=input.title, post_type=input.post_type, content=input.content, enabled=input.enabled, created_at=datetime.now(UTC))
    store.posts[post.id] = post
    return post

@app.put("/api/posts/{post_id}", response_model=Post)
def update_post(post_id: str, input: PostInput) -> Post:
    if post_id not in store.posts:
        raise HTTPException(404, "Post not found")
    post = store.posts[post_id].model_copy(update=input.model_dump())
    store.posts[post_id] = post
    return post

@app.delete("/api/posts/{post_id}")
def delete_post(post_id: str) -> dict[str, bool]:
    store.posts.pop(post_id, None)
    return {"ok": True}

@app.get("/api/scheduler", response_model=SchedulerSettings)
def get_scheduler() -> SchedulerSettings:
    return store.scheduler

@app.put("/api/scheduler", response_model=SchedulerSettings)
def update_scheduler(settings: SchedulerSettings) -> SchedulerSettings:
    store.scheduler = settings
    return settings

@app.get("/api/bot/status", response_model=BotStatus)
def bot_status() -> BotStatus:
    return store.bot

@app.post("/api/bot/start", response_model=BotStatus)
def start_bot() -> BotStatus:
    store.bot = store.bot.model_copy(update={"state": "RUNNING", "updated_at": datetime.now(UTC)})
    store.run_once()
    return store.bot

@app.post("/api/bot/stop", response_model=BotStatus)
def stop_bot() -> BotStatus:
    store.bot = store.bot.model_copy(update={"state": "STOPPED", "updated_at": datetime.now(UTC)})
    return store.bot

@app.get("/api/history", response_model=list[HistoryItem])
def history() -> list[HistoryItem]:
    return store.history

@app.post("/api/groups/{group_id}/opportunities", response_model=list[Opportunity])
async def analyze_opportunities(group_id: str) -> list[Opportunity]:
    group = store.data.get_group(group_id)
    if group is None:
        raise HTTPException(404, "Group not found")
    messages = store.data.get_messages(group_id, 500)
    opportunities = await store.ai.analyze_opportunities(group, [message.content for message in messages])
    store.opportunities = [item for item in store.opportunities if item.group_id != group_id] + opportunities
    return opportunities

@app.get("/api/opportunities", response_model=list[Opportunity])
def opportunities() -> list[Opportunity]:
    return store.opportunities
