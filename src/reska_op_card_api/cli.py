#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28
"""

import os
import secrets
import sys

from dotenv import load_dotenv

load_dotenv()

_HTTPS_PORT = int(os.environ.get("PORT", "8443"))


def api():
    import uvicorn

    certfile = os.environ.get("SSL_CERTFILE")
    keyfile = os.environ.get("SSL_KEYFILE")

    # Resolve relative cert paths against CWD before reload forks change directory
    if certfile:
        certfile = str(os.path.abspath(certfile))
    if keyfile:
        keyfile = str(os.path.abspath(keyfile))

    if certfile and keyfile and os.path.isfile(certfile) and os.path.isfile(keyfile):
        print(f"TLS enabled — https://localhost:{_HTTPS_PORT}")
        uvicorn.run(
            "reska_op_card_api.main:app",
            host="127.0.0.1",
            port=_HTTPS_PORT,
            ssl_certfile=certfile,
            ssl_keyfile=keyfile,
            reload=True,
        )
    else:
        if certfile or keyfile:
            print("WARNING: SSL cert/key file(s) not found — running on plain HTTP")
        else:
            print("WARNING: SSL_CERTFILE/SSL_KEYFILE not set — running on plain HTTP")
        uvicorn.run("reska_op_card_api.main:app", reload=True)


def create_key():
    """Generate and store a new API key.

    Usage:
        create-key --label LABEL [--edit]

    Flags:
        --label LABEL   Human-readable label for the key (required, must be unique)
        --edit          Key will have edit permissions (default: read-only)
    """
    args = sys.argv[1:]
    can_edit = "--edit" in args
    if "--label" not in args:
        print("error: --label is required", file=sys.stderr)
        sys.exit(1)
    idx = args.index("--label")
    try:
        label = args[idx + 1]
    except IndexError:
        print("error: --label requires a value", file=sys.stderr)
        sys.exit(1)
    if not label or label.startswith("--"):
        print("error: --label requires a non-empty value", file=sys.stderr)
        sys.exit(1)

    from reska_op_card_api.database import DATABASE_URL, init_db
    from reska_op_card_api.models import ApiKey

    init_db()

    from sqlmodel import Session, create_engine

    engine = create_engine(DATABASE_URL)
    import blake3

    key = secrets.token_urlsafe(32)
    key_hash = blake3.blake3(key.encode()).hexdigest()
    record = ApiKey(key=key_hash, can_edit=can_edit, label=label)
    from sqlalchemy.exc import IntegrityError

    with Session(engine) as session:
        session.add(record)
        try:
            session.commit()
        except IntegrityError:
            print(f"error: label '{label}' is already in use", file=sys.stderr)
            sys.exit(1)

    kind = "edit" if can_edit else "read-only"
    print(f"Created {kind} key [{label}]:")
    print(key)


def delete_key():
    """Delete an API key by its label.

    Usage:
        delete-key --label LABEL
    """
    args = sys.argv[1:]
    if "--label" not in args:
        print("error: --label is required", file=sys.stderr)
        sys.exit(1)
    idx = args.index("--label")
    try:
        label = args[idx + 1]
    except IndexError:
        print("error: --label requires a value", file=sys.stderr)
        sys.exit(1)
    if not label or label.startswith("--"):
        print("error: --label requires a non-empty value", file=sys.stderr)
        sys.exit(1)

    from reska_op_card_api.database import DATABASE_URL, init_db
    from reska_op_card_api.models import ApiKey

    init_db()

    from sqlmodel import Session, create_engine, select

    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        record = session.exec(select(ApiKey).where(ApiKey.label == label)).first()
        if record is None:
            print(f"error: no key with label '{label}'", file=sys.stderr)
            sys.exit(1)
        session.delete(record)
        session.commit()

    print(f"Deleted key [{label}]")


def list_keys():
    """List all API keys.

    Usage:
        list-keys
    """
    from reska_op_card_api.database import DATABASE_URL, init_db
    from reska_op_card_api.models import ApiKey

    init_db()

    from sqlmodel import Session, create_engine, select

    engine = create_engine(DATABASE_URL)
    with Session(engine) as session:
        records = session.exec(select(ApiKey).order_by(ApiKey.label)).all()

    if not records:
        print("No keys found.")
        return

    for r in records:
        kind = "edit" if r.can_edit else "read-only"
        last_used = r.last_used_ts or "never"
        print(f"[{r.label}]  {kind}  requests={r.request_count}  last_used={last_used}  created={r.created_ts}")
