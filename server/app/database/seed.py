"""The demo seed command is intentionally disabled for real-data operation."""


def run_seed(*_args, **_kwargs) -> None:
    raise RuntimeError(
        "Demo/mock seeding is disabled. Add groups and message evidence through the user-driven API/UI."
    )


if __name__ == "__main__":
    raise SystemExit(
        "Demo/mock seeding is disabled. Apply migrations, then add groups and copied message evidence manually."
    )
