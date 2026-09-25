from datetime import UTC, datetime
from app.database.init_db import init_db
from app.database.models import GroupModel, PostModel
from app.database.session import SessionLocal
from app.main import store

def seed() -> None:
    init_db()
    with SessionLocal.begin() as session:
        for group in store.data.groups:
            if session.get(GroupModel, group.id) is None:
                session.add(GroupModel(id=group.id, name=group.name, username=group.username, description=group.description, member_count=group.member_count, category=group.category, joined=group.joined))
        for post in store.posts.values():
            if session.get(PostModel, post.id) is None:
                session.add(PostModel(id=post.id, title=post.title, post_type=post.post_type, content=post.content, enabled=post.enabled, usage_count=post.usage_count, created_at=post.created_at))

if __name__ == "__main__":
    seed()
    print(f"Seeded {len(store.data.groups)} groups and {len(store.posts)} posts")
