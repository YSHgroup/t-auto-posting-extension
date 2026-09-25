"""Seed mock groups, messages, posts, replies, and singleton settings."""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.database.session import SessionLocal, engine
from app.models.entities import (
    AISettings,
    AppSettings,
    BotState,
    Group,
    GroupMessage,
    Notification,
    Opportunity,
    Post,
    PostAssignment,
    FeedItem,
    Reply,
    SchedulerSettings,
    User,
)
from app.providers.data.mock_catalog import MOCK_GROUPS

MOCK_USERNAMES = ["alex", "maria_dev", "founder_joe", "investor_sam", "company_owner", "dev_nina"]
INVEST_MSG = "I invest in early-stage gaming startups."
PARTNER_MSG = "Looking for gaming platforms to integrate with."


def _clear(db: Session) -> None:
    from app.models.entities import FeedItem, GroupAnalysis, PostAssignment, PostHistory

    for model in (
        PostHistory,
        PostAssignment,
        FeedItem,
        Notification,
        Opportunity,
        Reply,
        GroupAnalysis,
        GroupMessage,
        Post,
        Group,
        User,
        BotState,
        SchedulerSettings,
        AISettings,
        AppSettings,
    ):
        db.query(model).delete()
    db.commit()


def run_seed(db: Session | None = None, reset: bool = False) -> None:
    own_session = db is None
    db = db or SessionLocal()
    try:
        if reset:
            _clear(db)

        if db.query(Group).count() > 0 and not reset:
            return

        users = []
        for i, uname in enumerate(MOCK_USERNAMES):
            u = User(external_id=f"user_{i+1:03d}", username=uname, display_name=uname.replace("_", " ").title())
            db.add(u)
            users.append(u)
        db.flush()

        groups: list[Group] = []
        for raw in MOCK_GROUPS:
            g = Group(
                external_id=raw["id"],
                name=raw["name"],
                username=raw["username"],
                description=raw["description"],
                member_count=raw["member_count"],
                categories=raw["categories"],
                keywords=raw.get("keywords", []),
                joined=False,
            )
            db.add(g)
            groups.append(g)
        db.flush()

        # Seed messages for first 10 groups (60+ msgs each for eligibility tests)
        templates = [
            "Great discussion today about product market fit.",
            "Anyone building on Ethereum L2?",
            "Sharing our launch metrics from last week.",
            INVEST_MSG,
            PARTNER_MSG,
            "Hiring remote backend engineers.",
            "What stack do you use for realtime chat?",
        ]
        for g in groups[:10]:
            seq = 0
            for i in range(65):
                seq += 1
                uname = random.choice(MOCK_USERNAMES)
                content = templates[i % len(templates)]
                if i == 10:
                    # Simulated previous app post at sequence 10
                    db.add(
                        GroupMessage(
                            group_id=g.id,
                            external_message_id=f"msg_{g.external_id}_{seq}",
                            user_id="app_user",
                            username="you",
                            content="Previous partnership post (demo).",
                            is_app_post=True,
                            sequence_num=seq,
                            created_at=datetime.utcnow() - timedelta(hours=48),
                        )
                    )
                    continue
                db.add(
                    GroupMessage(
                        group_id=g.id,
                        external_message_id=f"msg_{g.external_id}_{seq}",
                        user_id=f"user_{random.randint(1, 6):03d}",
                        username=uname,
                        content=content,
                        sequence_num=seq,
                        created_at=datetime.utcnow() - timedelta(minutes=65 - i),
                    )
                )

        sample_post = Post(
            title="Strategic Partnership",
            post_type="Partnership",
            content="We're looking for strategic partners to collaborate on a gaming and technology platform.",
            status="Active",
            enabled=True,
        )
        db.add(sample_post)
        db.flush()

        g0 = groups[0]
        db.add(
            Reply(
                group_id=g0.id,
                post_id=sample_post.id,
                user_id="user_001",
                username="alex",
                message="I'm interested in learning more about the partnership.",
                read=False,
            )
        )
        db.add(
            Notification(
                group_id=g0.id,
                user_id="user_001",
                username="alex",
                message="I'm interested in learning more about the partnership.",
                related_post_id=sample_post.id,
                read=False,
            )
        )
        db.add(
            Opportunity(
                group_id=g0.id,
                user_id="user_001",
                username="alex",
                category="investment",
                evidence=INVEST_MSG,
                evidence_level="explicit",
                confidence=0.86,
            )
        )

        if not db.query(FeedItem).filter(FeedItem.group_id == g0.id).first():
            feed_item = FeedItem(group_id=g0.id, order_index=0, enabled=True)
            db.add(feed_item)
            db.flush()
            db.add(PostAssignment(feed_item_id=feed_item.id, post_id=sample_post.id, selected_by="seed"))
        db.add(
            Opportunity(
                group_id=g0.id,
                user_id="user_005",
                username="company_owner",
                category="partnership",
                evidence=PARTNER_MSG,
                evidence_level="explicit",
                confidence=0.81,
            )
        )

        if not db.query(SchedulerSettings).filter(SchedulerSettings.id == 1).first():
            db.add(
                SchedulerSettings(
                    id=1,
                    auto_mode=True,
                    working_days=[0, 1, 2, 3, 4, 5, 6],
                    minimum_messages=20,
                )
            )
        if not db.query(BotState).filter(BotState.id == 1).first():
            db.add(BotState(id=1, state="STOPPED", current_feed_index=0))
        if not db.query(AISettings).filter(AISettings.id == 1).first():
            db.add(AISettings(id=1))
        if not db.query(AppSettings).filter(AppSettings.id == 1).first():
            db.add(AppSettings(id=1, data_mode="mock"))

        db.commit()
    finally:
        if own_session:
            db.close()


if __name__ == "__main__":
    from app.database.session import Base

    Base.metadata.create_all(bind=engine)
    run_seed(reset=False)
    print("Seed complete.")
