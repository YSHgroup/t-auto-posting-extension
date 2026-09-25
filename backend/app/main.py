from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlmodel import Field, Session, SQLModel, create_engine, select


def now() -> datetime:
    return datetime.now(timezone.utc)


class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    telegram_id: str = Field(index=True)
    name: str
    handle: str
    members: int = 0
    category: str = "General"
    joined: bool = False
    score: int = 0
    status: str = "Discovered"
    analysis: Optional[str] = None
    risk: Optional[str] = None
    last_scanned: Optional[datetime] = None


class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    body: str
    tone: str = "Professional"
    created_at: datetime = Field(default_factory=now)
    updated_at: datetime = Field(default_factory=now)


class Feed(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    post_id: Optional[int] = None
    enabled: bool = True
    auto_mode: bool = False
    interval_minutes: int = 120
    window_start: str = "09:00"
    window_end: str = "20:00"
    workdays: str = "Mon,Tue,Wed,Thu,Fri"
    post_count: int = 0
    last_posted: Optional[datetime] = None
    replies: int = 0


class Message(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(index=True)
    external_id: str
    author: str
    body: str
    created_at: datetime = Field(default_factory=now)
    is_ours: bool = False


class GroupCreate(BaseModel):
    telegram_id: str
    name: str
    handle: str
    members: int = 0
    category: str = "General"


class PostInput(BaseModel):
    title: str
    body: str
    tone: str = "Professional"


class FeedInput(BaseModel):
    group_id: int
    post_id: Optional[int] = None
    auto_mode: bool = False
    interval_minutes: int = 120
    window_start: str = "09:00"
    window_end: str = "20:00"
    workdays: str = "Mon,Tue,Wed,Thu,Fri"


class ActionInput(BaseModel):
    action: str


engine = create_engine("sqlite:///automation.db", connect_args={"check_same_thread": False})
app = FastAPI(title="Independent Telegram Automation API", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


@app.on_event("startup")
def startup() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        if not session.exec(select(Group)).first():
            session.add_all([
                Group(telegram_id="-1002048101", name="Remote Builders", handle="@remote_builders", members=18420, category="Startups", score=92, status="Analysed", analysis="Founders exchange launch feedback, hiring leads, and practical growth advice.", risk="Avoid unsolicited links and repeated pitches. Introduce yourself before proposing a partnership."),
                Group(telegram_id="-1002048102", name="Indie Hackers Europe", handle="@indiehackers_eu", members=8320, category="SaaS", score=87, status="Ready", analysis="Product builders share launches, tooling, and collaboration opportunities.", risk="Keep promotional posts tied to a specific discussion. Do not automate replies."),
                Group(telegram_id="-1002048103", name="Design & Dev Jobs", handle="@design_dev_jobs", members=22100, category="Jobs", score=78, status="Ready", analysis="A high-volume board for freelance and full-time design and engineering roles.", risk="Follow the group format exactly. Never scrape private contact information."),
            ])
            session.commit()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/groups")
def list_groups(search: str = Query(default=""), limit: int = Query(default=50, le=50)) -> list[Group]:
    with Session(engine) as session:
        groups = session.exec(select(Group)).all()
        if search:
            needle = search.lower()
            groups = [g for g in groups if needle in f"{g.name} {g.handle} {g.category}".lower()]
        return groups[:limit]


@app.post("/api/groups", response_model=Group)
def create_group(payload: GroupCreate) -> Group:
    with Session(engine) as session:
        group = Group.model_validate(payload)
        session.add(group)
        session.commit()
        session.refresh(group)
        return group


@app.post("/api/groups/{group_id}/analyse", response_model=Group)
def analyse_group(group_id: int) -> Group:
    with Session(engine) as session:
        group = session.get(Group, group_id)
        if not group:
            raise HTTPException(404, "Group not found")
        group.analysis = "Members discuss practical opportunities, exchange resources, and respond best to concise, relevant proposals."
        group.risk = "Respect the group's posting rules, avoid repeated messages, and never send unsolicited bulk DMs."
        group.status = "Analysed"
        group.score = max(group.score, 74)
        group.last_scanned = now()
        session.add(group)
        session.commit()
        session.refresh(group)
        return group


@app.get("/api/posts")
def list_posts() -> list[Post]:
    with Session(engine) as session:
        return list(session.exec(select(Post).order_by(Post.updated_at.desc())).all())


@app.post("/api/posts", response_model=Post)
def create_post(payload: PostInput) -> Post:
    with Session(engine) as session:
        post = Post.model_validate(payload)
        session.add(post)
        session.commit()
        session.refresh(post)
        return post


@app.put("/api/posts/{post_id}", response_model=Post)
def update_post(post_id: int, payload: PostInput) -> Post:
    with Session(engine) as session:
        post = session.get(Post, post_id)
        if not post:
            raise HTTPException(404, "Post not found")
        post.title, post.body, post.tone, post.updated_at = payload.title, payload.body, payload.tone, now()
        session.add(post)
        session.commit()
        session.refresh(post)
        return post


@app.get("/api/feeds")
def list_feeds() -> list[Feed]:
    with Session(engine) as session:
        return list(session.exec(select(Feed)).all())


@app.post("/api/feeds", response_model=Feed)
def create_feed(payload: FeedInput) -> Feed:
    with Session(engine) as session:
        feed = Feed.model_validate(payload)
        session.add(feed)
        session.commit()
        session.refresh(feed)
        return feed


@app.post("/api/feeds/{feed_id}/action")
def feed_action(feed_id: int, payload: ActionInput) -> Feed:
    with Session(engine) as session:
        feed = session.get(Feed, feed_id)
        if not feed:
            raise HTTPException(404, "Feed not found")
        if payload.action == "toggle":
            feed.enabled = not feed.enabled
        elif payload.action == "post":
            feed.post_count += 1
            feed.last_posted = now()
        session.add(feed)
        session.commit()
        session.refresh(feed)
        return feed