from app.services.group_service import GroupService


def test_group_search_max_50(db):
    results = GroupService(db).search("blockchain startup")
    assert len(results) <= 50
    assert any("blockchain" in r.name.lower() or "blockchain" in r.description.lower() for r in results)


def test_joined_groups_excluded(db):
    from app.models.entities import Group

    g = db.query(Group).filter(Group.external_id == "group_001").first()
    g.joined = True
    db.commit()
    results = GroupService(db).search("blockchain")
    assert all(r.id != "group_001" for r in results)
