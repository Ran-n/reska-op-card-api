import secrets
import sys

import uvicorn


def api():
    import uvicorn.main

    uvicorn.main.main(
        ["reska_op_card_api.main:app", "--reload", *sys.argv[1:]]
    )


def create_key():
    """Generate and store a new API key.

    Usage:
        create-key [--edit] [--label LABEL]

    Flags:
        --edit          Key will have edit permissions (default: read-only)
        --label LABEL   Optional human-readable label for the key
    """
    args = sys.argv[1:]
    can_edit = "--edit" in args
    label: str | None = None
    if "--label" in args:
        idx = args.index("--label")
        try:
            label = args[idx + 1]
        except IndexError:
            print("error: --label requires a value", file=sys.stderr)
            sys.exit(1)

    from reska_op_card_api.database import DATABASE_URL, init_db
    from reska_op_card_api.models import ApiKey

    init_db()

    from sqlmodel import Session, create_engine

    engine = create_engine(DATABASE_URL)
    key = secrets.token_urlsafe(32)
    record = ApiKey(key=key, can_edit=can_edit, label=label)
    with Session(engine) as session:
        session.add(record)
        session.commit()

    kind = "edit" if can_edit else "read-only"
    print(f"Created {kind} key{f' [{label}]' if label else ''}:")
    print(key)
