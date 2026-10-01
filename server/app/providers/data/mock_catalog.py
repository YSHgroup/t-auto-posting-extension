"""Static catalog of 50+ mock groups for search and validation."""

CATEGORIES = [
    "Blockchain",
    "Startups",
    "Developers",
    "Gaming",
    "Remote Jobs",
    "Investors",
    "Marketing",
    "Entrepreneurs",
    "Freelancers",
    "Technology",
]

MOCK_GROUPS: list[dict] = [
    {
        "id": "group_001",
        "name": "Blockchain Startup Founders",
        "username": "blockchain_founders",
        "description": "Community for blockchain founders and entrepreneurs building Web3 products.",
        "member_count": 18420,
        "categories": ["Blockchain", "Startups", "Entrepreneurs"],
        "keywords": ["blockchain", "startup", "founders", "web3"],
    },
    {
        "id": "group_002",
        "name": "Web3 Developers Hub",
        "username": "web3_devs",
        "description": "Smart contracts, dApps, and developer tooling discussions.",
        "member_count": 22100,
        "categories": ["Blockchain", "Developers", "Technology"],
        "keywords": ["web3", "solidity", "developers"],
    },
    {
        "id": "group_003",
        "name": "Gaming Founders Network",
        "username": "gaming_founders",
        "description": "Indie and studio founders sharing funding and partnership opportunities in gaming.",
        "member_count": 9800,
        "categories": ["Gaming", "Startups", "Entrepreneurs"],
        "keywords": ["gaming", "founders", "partnership"],
    },
    {
        "id": "group_004",
        "name": "Remote Jobs — Tech",
        "username": "remote_jobs_tech",
        "description": "Remote engineering, product, and design job posts worldwide.",
        "member_count": 45200,
        "categories": ["Remote Jobs", "Developers", "Technology"],
        "keywords": ["remote", "jobs", "hiring"],
    },
    {
        "id": "group_12345",
        "name": "Manual Entry Demo Group",
        "username": "manual_demo_group",
        "description": "Example group for manual Group ID entry in the extension.",
        "member_count": 5200,
        "categories": ["Technology", "Startups"],
        "keywords": ["manual", "demo", "group"],
    },
    {
        "id": "group_005",
        "name": "Angel Investors Circle",
        "username": "angel_investors",
        "description": "Early-stage investors discussing deal flow and startup pitches.",
        "member_count": 7600,
        "categories": ["Investors", "Startups"],
        "keywords": ["invest", "angel", "fund"],
    },
]

# Generate additional groups programmatically
_templates = [
    ("{cat} Builders", "{cat} builders sharing launches and feedback.", "{cat}"),
    ("{cat} Marketing Pros", "Growth tactics for {cat} products.", "Marketing"),
    ("{cat} Freelancers", "Freelance gigs and collaboration in {cat}.", "Freelancers"),
    ("{cat} Startup Lounge", "Startup discussions focused on {cat}.", "Startups"),
]

_idx = 6
for cat in CATEGORIES:
    for tpl_name, tpl_desc, extra_cat in _templates:
        if _idx > 60:
            break
        slug = cat.lower().replace(" ", "_")
        MOCK_GROUPS.append(
            {
                "id": f"group_{_idx:03d}",
                "name": tpl_name.format(cat=cat),
                "username": f"{slug}_{_idx}",
                "description": tpl_desc.format(cat=cat),
                "member_count": 3000 + (_idx * 137) % 40000,
                "categories": list({cat, extra_cat}),
                "keywords": [cat.lower(), "community", "network"],
            }
        )
        _idx += 1
