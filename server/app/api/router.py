from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.feed import FeedItemCreate, FeedItemOut, FeedItemUpdate, FeedReorderRequest
from app.schemas.groups import SimulatedReplyRequest
from app.schemas.posts import PostCreate, PostOut, PostUpdate, RecommendPostRequest, RecommendPostResponse
from app.schemas.scheduler import BotStatusOut, DashboardOut, SchedulerOut, SchedulerUpdate
from app.services.dashboard_service import DashboardService
from app.services.feed_service import FeedService
from app.services.group_service import GroupService
from app.services.history_service import HistoryService
from app.services.notification_service import NotificationService
from app.services.opportunity_service import OpportunityService
from app.services.post_service import PostService
from app.services.scheduler_service import SchedulerService
from app.services.settings_service import SettingsService

api_router = APIRouter(prefix="/api")


@api_router.get("/health")
def health():
    return {"status": "ok"}


@api_router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    return DashboardService(db).get_dashboard()


@api_router.get("/groups/search")
def search_groups(q: str = Query(default=""), db: Session = Depends(get_db)):
    return GroupService(db).search(q)


@api_router.get("/groups/{group_id}")
def get_group(group_id: str, db: Session = Depends(get_db)):
    try:
        return GroupService(db).get_detail(group_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.get("/groups/{group_id}/messages")
def group_messages(group_id: str, limit: int = 100, db: Session = Depends(get_db)):
    return GroupService(db).get_messages(group_id, limit=limit)


@api_router.post("/groups/{group_id}/simulate-reply")
def simulate_reply(
    group_id: str, payload: SimulatedReplyRequest, db: Session = Depends(get_db)
):
    try:
        return GroupService(db).simulate_reply(
            group_id, payload.username, payload.message, str(payload.post_id) if payload.post_id else None
        )
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.post("/groups/{group_id}/analyze")
async def analyze_group(group_id: str, db: Session = Depends(get_db)):
    try:
        return await GroupService(db).analyze(group_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.get("/groups/{group_id}/analysis")
def list_analysis(group_id: str, db: Session = Depends(get_db)):
    try:
        return GroupService(db).list_analyses(group_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.get("/feed", response_model=list[FeedItemOut])
def list_feed(db: Session = Depends(get_db)):
    return FeedService(db).list_feed()


@api_router.post("/feed", response_model=FeedItemOut)
def add_feed(payload: FeedItemCreate, db: Session = Depends(get_db)):
    try:
        return FeedService(db).add(payload)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.put("/feed/{item_id}", response_model=FeedItemOut)
def update_feed(item_id: UUID, payload: FeedItemUpdate, db: Session = Depends(get_db)):
    try:
        return FeedService(db).update(item_id, payload)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.delete("/feed/{item_id}")
def delete_feed(item_id: UUID, db: Session = Depends(get_db)):
    try:
        FeedService(db).delete(item_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.post("/feed/reorder", response_model=list[FeedItemOut])
def reorder_feed(payload: FeedReorderRequest, db: Session = Depends(get_db)):
    return FeedService(db).reorder(payload)


@api_router.get("/posts", response_model=list[PostOut])
def list_posts(db: Session = Depends(get_db)):
    return PostService(db).list_posts()


@api_router.post("/posts", response_model=PostOut)
def create_post(payload: PostCreate, db: Session = Depends(get_db)):
    return PostService(db).create(payload)


@api_router.post("/posts/recommend", response_model=RecommendPostResponse)
async def recommend_post(payload: RecommendPostRequest, db: Session = Depends(get_db)):
    try:
        return await PostService(db).recommend(payload)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.get("/posts/{post_id}", response_model=PostOut)
def get_post(post_id: UUID, db: Session = Depends(get_db)):
    try:
        return PostService(db).get(post_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.put("/posts/{post_id}", response_model=PostOut)
def update_post(post_id: UUID, payload: PostUpdate, db: Session = Depends(get_db)):
    try:
        return PostService(db).update(post_id, payload)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.delete("/posts/{post_id}")
def delete_post(post_id: UUID, db: Session = Depends(get_db)):
    try:
        PostService(db).delete(post_id)
        return {"ok": True}
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.post("/posts/{post_id}/duplicate", response_model=PostOut)
def duplicate_post(post_id: UUID, db: Session = Depends(get_db)):
    try:
        return PostService(db).duplicate(post_id)
    except ValueError as e:
        raise HTTPException(404, str(e)) from e


@api_router.get("/scheduler", response_model=SchedulerOut)
def get_scheduler(db: Session = Depends(get_db)):
    return SchedulerService(db).get_scheduler()


@api_router.put("/scheduler", response_model=SchedulerOut)
def update_scheduler(payload: SchedulerUpdate, db: Session = Depends(get_db)):
    try:
        return SchedulerService(db).update_scheduler(payload)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.post("/bot/start", response_model=BotStatusOut)
def start_bot(db: Session = Depends(get_db)):
    return SchedulerService(db).start_bot()


@api_router.post("/bot/stop", response_model=BotStatusOut)
def stop_bot(db: Session = Depends(get_db)):
    return SchedulerService(db).stop_bot()


@api_router.get("/bot/status", response_model=BotStatusOut)
def bot_status(db: Session = Depends(get_db)):
    return SchedulerService(db).bot_status()


@api_router.get("/history")
def history(db: Session = Depends(get_db)):
    return HistoryService(db).list_history()


@api_router.get("/notifications")
def notifications(filter: str = Query(default="all"), db: Session = Depends(get_db)):
    return NotificationService(db).list_notifications(filter)


@api_router.post("/notifications/{notification_id}/read")
def mark_notification_read(notification_id: UUID, db: Session = Depends(get_db)):
    NotificationService(db).mark_read(notification_id)
    return {"ok": True}


@api_router.post("/notifications/read-all")
def mark_all_notifications(db: Session = Depends(get_db)):
    NotificationService(db).mark_all_read()
    return {"ok": True}


@api_router.post("/groups/{group_id}/opportunities")
async def scan_opportunities(group_id: str, db: Session = Depends(get_db)):
    try:
        return await OpportunityService(db).scan_group(group_id)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.get("/opportunities")
def list_opportunities(category: str | None = None, db: Session = Depends(get_db)):
    return OpportunityService(db).list_all(category)


@api_router.get("/settings")
def get_settings(db: Session = Depends(get_db)):
    return SettingsService(db).get_settings()


@api_router.put("/settings")
def update_settings(payload: dict, db: Session = Depends(get_db)):
    try:
        return SettingsService(db).update_settings(payload)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e


@api_router.post("/settings/test-connection")
def test_connection(db: Session = Depends(get_db)):
    return {"ok": True, "message": "Connected"}


@api_router.post("/settings/reset-demo")
def reset_demo(db: Session = Depends(get_db)):
    from app.database.seed import run_seed

    run_seed(db, reset=True)
    return {"ok": True}
