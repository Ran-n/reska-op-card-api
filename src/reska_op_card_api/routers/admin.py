#!/usr/bin/env python3
"""
Authors: Ran# <ran.hash@proton.me>
Created: 2026/06/28
"""

import html
import os
import secrets
from urllib.parse import urlencode

import blake3
from fastapi import APIRouter, Depends, Form, HTTPException, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select

from reska_op_card_api.database import get_session
from reska_op_card_api.models import ApiKey

router = APIRouter(prefix="/admin", tags=["admin"])
_basic = HTTPBasic()


def _require_admin(credentials: HTTPBasicCredentials = Depends(_basic)) -> None:
    admin_user = os.environ.get("ADMIN_USERNAME", "")
    admin_pw = os.environ.get("ADMIN_PASSWORD", "")
    if not admin_user or not admin_pw:
        raise HTTPException(status_code=503, detail="ADMIN_USERNAME or ADMIN_PASSWORD not configured")
    user_ok = secrets.compare_digest(credentials.username.encode(), admin_user.encode())
    pw_ok = secrets.compare_digest(credentials.password.encode(), admin_pw.encode())
    if not user_ok or not pw_ok:
        raise HTTPException(
            status_code=401,
            detail="Unauthorized",
            headers={"WWW-Authenticate": 'Basic realm="Admin"'},
        )


def _fmt_ts(ts) -> str:
    if not ts:
        return "—"
    s = html.escape(str(ts))
    if " " in s:
        date, time = s.split(" ", 1)
        return f"{date}<br><span style='opacity:.75'>{time}</span>"
    return s


def _render(
    keys: list[ApiKey],
    new_key: str | None = None,
    new_label: str | None = None,
    error: str | None = None,
    input_label: str | None = None,
    show_deleted: bool = False,
    revoked_count: int | None = None,
) -> str:
    rows = ""
    for k in sorted(keys, key=lambda k: k.label.lower()):
        is_deleted = k.revoked_ts is not None
        row_class = ' class="tr-deleted"' if is_deleted else ""
        if is_deleted:
            perm = "revoked"
            perm_class = "badge-revoked"
        else:
            perm = "edit" if k.can_edit else "read-only"
            perm_class = "badge-edit" if k.can_edit else "badge-read"
        last = _fmt_ts(k.last_used_ts)
        created = _fmt_ts(k.created_ts)
        deleted = _fmt_ts(k.revoked_ts) if k.revoked_ts else ""
        label_esc = html.escape(k.label)
        h = html.escape(k.key)
        key_hash_esc = f"{h[:32]}<wbr>{h[32:]}" if len(h) > 32 else h
        if is_deleted:
            action_cell = f"""
            <form method="post" action="/admin/keys/{k.id}/restore" style="display:contents">
              <button class="btn-sm btn-restore" type="submit">Restore</button>
            </form>
            <form method="post" action="/admin/keys/{k.id}/purge"
                  onsubmit="return confirm('Permanently delete [{label_esc}] and all its logs?')"
                  style="display:contents">
              <button class="btn-sm btn-purge" type="submit">Delete</button>
            </form>"""
        else:
            action_cell = f"""
            <form method="post" action="/admin/keys/{k.id}/delete"
                  onsubmit="return confirm('Revoke key [{label_esc}]?')"
                  style="display:contents">
              <button class="btn-sm btn-danger" type="submit">Revoke</button>
            </form>
            <form method="post" action="/admin/keys/{k.id}/purge"
                  onsubmit="return confirm('Permanently delete [{label_esc}] and all its logs?')"
                  style="display:contents">
              <button class="btn-sm btn-purge" type="submit">Delete</button>
            </form>"""
        revoked_cell = f'<td class="td-ts">{deleted}</td>' if is_deleted else '<td class="td-ts td-empty">—</td>'
        rows += f"""
        <tr{row_class}>
          <td class="td-label">{label_esc}</td>
          <td><span class="badge {perm_class}">{perm}</span></td>
          <td class="td-count">{k.request_count}</td>
          <td class="td-ts">{last}</td>
          <td class="td-ts">{created}</td>
          {revoked_cell}
          <td class="td-hash">{key_hash_esc}</td>
          <td><div class="td-actions">{action_cell}
          </div></td>
        </tr>"""

    new_key_html = ""
    if new_key:
        new_key_html = f"""
        <div class="banner banner-success">
          <div class="banner-title">Key created for <em>{html.escape(new_label or "")}</em>
          — copy it now, it won&#x27;t be shown again</div>
          <div class="key-row">
            <code id="new-key">{html.escape(new_key)}</code>
            <button class="btn-copy" onclick="copyKey(this)">Copy</button>
          </div>
        </div>"""

    error_html = ""
    if error:
        error_html = f'<div class="banner banner-error"><span>✕</span> {html.escape(error)}</div>'

    active_count = sum(1 for k in keys if k.revoked_ts is None)
    shown_revoked = sum(1 for k in keys if k.revoked_ts is not None)
    deleted_count = revoked_count if revoked_count is not None else shown_revoked
    total_count = active_count + deleted_count
    total_requests = sum(k.request_count for k in keys)
    empty_row = '<tr><td colspan="8" class="empty">No keys</td></tr>' if not rows else ""
    label_value = f'value="{html.escape(input_label)}"' if input_label else ""
    toggle_href = "/admin/keys?show_deleted=0" if show_deleted else "/admin/keys"
    toggle_label = "Hide revoked" if show_deleted else f"Show revoked ({deleted_count})"
    toggle_html = f'<a class="toggle-link" href="{toggle_href}">{toggle_label}</a>'

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Key Manager · reska-op-card-api</title>
  <link rel="icon" type="image/svg+xml" href="/static/admin-keys.svg">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}

    :root {{
      --bg: #1d2021;
      --surface: #282828;
      --surface-hi: #32302f;
      --border: #3c3836;
      --border-sub: #32302f;
      --text: #ebdbb2;
      --text-2: #a89984;
      --text-3: #7c6f64;
      --accent: #d79921;
      --violet: #d65d0e;
    }}

    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg);
      color: var(--text);
      min-height: 100vh;
      font-size: 14px;
      line-height: 1.5;
    }}

    /* ── Topbar ── */
    .topbar {{
      background: var(--surface);
      border-bottom: 1px solid var(--border);
      height: 54px;
      padding: 0 2rem;
      display: flex;
      align-items: center;
      gap: .875rem;
    }}
    .logo {{
      width: 30px; height: 30px;
      background: linear-gradient(135deg, var(--accent), var(--violet));
      border-radius: 8px;
      display: flex; align-items: center; justify-content: center;
      font-size: 15px;
      flex-shrink: 0;
    }}
    .brand {{ display: flex; flex-direction: column; gap: 1px; }}
    .brand-name {{
      font-size: .85rem;
      font-weight: 600;
      color: var(--text);
      letter-spacing: -.01em;
      line-height: 1;
    }}
    .brand-sub {{
      font-size: .68rem;
      color: var(--text-2);
      line-height: 1;
    }}
    .topbar-fill {{ flex: 1; }}
    .admin-pill {{
      font-size: .68rem;
      font-weight: 600;
      letter-spacing: .06em;
      text-transform: uppercase;
      color: var(--text-3);
      background: var(--border-sub);
      border: 1px solid var(--border);
      border-radius: 5px;
      padding: 3px 9px;
      text-decoration: none;
      transition: color .15s, border-color .15s;
    }}
    .admin-pill:hover {{ color: var(--text-2); border-color: var(--text-3); }}

    /* ── Page ── */
    .page {{
      max-width: 1400px;
      margin: 0 auto;
      padding: 1.75rem 2rem;
    }}

    /* ── Stats row ── */
    .stats {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: .875rem;
      margin-bottom: 1.5rem;
    }}
    .stat {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: .875rem 1.25rem;
    }}
    .stat-label {{
      font-size: .68rem;
      font-weight: 500;
      color: var(--text-2);
      text-transform: uppercase;
      letter-spacing: .06em;
      margin-bottom: .3rem;
    }}
    .stat-value {{
      font-size: 1.6rem;
      font-weight: 700;
      color: var(--text);
      letter-spacing: -.025em;
      font-variant-numeric: tabular-nums;
      line-height: 1;
    }}

    /* ── Cards ── */
    .card {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 12px;
      overflow: hidden;
      margin-bottom: 1.25rem;
    }}
    .card-header {{
      padding: .75rem 1.5rem;
      border-bottom: 1px solid var(--border-sub);
      display: flex;
      align-items: center;
      gap: .65rem;
    }}
    .card-title {{
      font-size: .82rem;
      font-weight: 600;
      color: var(--text);
      letter-spacing: .01em;
    }}
    .pill {{
      font-size: .68rem;
      font-weight: 600;
      background: var(--border-sub);
      color: var(--text-2);
      border-radius: 9999px;
      padding: 2px 8px;
    }}
    .card-body {{ padding: 1.25rem 1.5rem; }}

    /* ── Table ── */
    table {{ width: 100%; border-collapse: collapse; }}
    th {{
      text-align: left;
      padding: .5rem 1rem;
      font-size: .68rem;
      text-transform: uppercase;
      letter-spacing: .08em;
      color: var(--text-3);
      border-bottom: 1px solid var(--border);
      font-weight: 500;
      white-space: nowrap;
    }}
    th[data-col] {{
      cursor: pointer;
      user-select: none;
    }}
    th[data-col]:hover {{ color: var(--text-2); }}
    th[data-col]::after {{ content: ' '; }}
    th[data-col].sort-asc::after {{ content: ' ↑'; color: var(--accent); }}
    th[data-col].sort-desc::after {{ content: ' ↓'; color: var(--accent); }}
    td {{
      padding: .6rem 1rem;
      border-bottom: 1px solid var(--border-sub);
      vertical-align: middle;
    }}
    tr:last-child td {{ border-bottom: none; }}
    tbody tr {{ transition: background .1s; }}
    tbody tr:hover td {{ background: var(--surface-hi); }}

    .td-label {{ font-weight: 500; color: var(--text); }}
    .td-count {{ color: var(--text-2); font-variant-numeric: tabular-nums; font-size: .88rem; }}
    .td-ts {{ color: var(--text-3); font-size: .78rem; line-height: 1.35; }}
    .td-hash {{
      font-family: 'Consolas', 'Fira Code', 'JetBrains Mono', monospace;
      font-size: .68rem;
      color: var(--text-3);
      word-break: break-all;
      max-width: 220px;
    }}
    .empty {{ color: var(--text-3); text-align: center; padding: 3rem; font-size: .85rem; }}
    .td-empty {{ color: var(--border); }}
    .td-actions {{ display: flex; align-items: center; gap: .35rem; white-space: nowrap; }}

    /* ── Badges ── */
    .badge {{
      display: inline-flex;
      align-items: center;
      gap: 5px;
      padding: 2px 8px;
      border-radius: 9999px;
      font-size: .68rem;
      font-weight: 600;
      letter-spacing: .03em;
      white-space: nowrap;
    }}
    .badge::before {{ content: ''; width: 5px; height: 5px; border-radius: 50%; flex-shrink: 0; }}
    .badge-edit    {{ background: rgba(131,165,152,.1); color: #83a598; border: 1px solid rgba(131,165,152,.22); }}
    .badge-edit::before    {{ background: #83a598; }}
    .badge-read    {{ background: rgba(184,187,38,.08); color: #b8bb26; border: 1px solid rgba(184,187,38,.18); }}
    .badge-read::before    {{ background: #b8bb26; }}
    .badge-revoked {{ background: rgba(251,73,52,.07); color: #fb4934; border: 1px solid rgba(251,73,52,.18); }}
    .badge-revoked::before {{ background: #fb4934; }}

    .tr-deleted td {{ opacity: .85; color: var(--text-3); }}
    .tr-deleted .td-label {{ text-decoration: line-through; color: var(--text-2); }}

    .toggle-link {{
      margin-left: auto;
      font-size: .72rem;
      color: var(--text-3);
      text-decoration: none;
      transition: color .15s;
    }}
    .toggle-link:hover {{ color: var(--text-2); }}

    /* ── Create form ── */
    .form-row {{ display: flex; gap: .875rem; align-items: flex-end; flex-wrap: wrap; }}
    .field {{ display: flex; flex-direction: column; gap: .35rem; }}
    .field-label {{
      font-size: .68rem;
      font-weight: 500;
      color: var(--text-2);
      text-transform: uppercase;
      letter-spacing: .05em;
    }}
    input[type=text] {{
      background: var(--bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: .45rem .85rem;
      font-size: .88rem;
      color: var(--text);
      width: 240px;
      outline: none;
      font-family: inherit;
      transition: border-color .15s, box-shadow .15s;
    }}
    input[type=text]::placeholder {{ color: var(--text-3); }}
    input[type=text]:focus {{
      border-color: var(--accent);
      box-shadow: 0 0 0 3px rgba(215,153,33,.18);
    }}
    .check-label {{
      display: flex;
      align-items: center;
      gap: .5rem;
      cursor: pointer;
      font-size: .88rem;
      color: var(--text-2);
      height: 36px;
    }}
    input[type=checkbox] {{
      accent-color: var(--accent);
      width: 15px; height: 15px;
      cursor: pointer;
    }}

    /* ── Buttons ── */
    button {{ cursor: pointer; font-family: inherit; border: none; transition: opacity .15s, background .15s; }}

    .btn-primary {{
      background: linear-gradient(135deg, var(--accent), var(--violet));
      color: #1d2021;
      border-radius: 8px;
      padding: .46rem 1.1rem;
      font-size: .88rem;
      font-weight: 700;
      letter-spacing: .01em;
      box-shadow: 0 1px 8px rgba(215,153,33,.25);
    }}
    .btn-primary:hover {{ opacity: .88; box-shadow: 0 2px 14px rgba(215,153,33,.38); }}

    .btn-sm {{
      border-radius: 6px;
      padding: .2rem .7rem;
      font-size: .75rem;
      font-weight: 500;
    }}
    .btn-danger {{
      background: transparent;
      border: 1px solid rgba(214,93,14,.28);
      color: #fe8019;
    }}
    .btn-danger:hover {{ background: rgba(214,93,14,.1); border-color: rgba(214,93,14,.5); }}
    .btn-purge {{
      background: rgba(251,73,52,.1);
      border: 1px solid rgba(251,73,52,.28);
      color: #fb4934;
    }}
    .btn-purge:hover {{ background: rgba(251,73,52,.2); border-color: rgba(251,73,52,.5); }}
    .btn-restore {{
      background: transparent;
      border: 1px solid rgba(184,187,38,.2);
      color: #b8bb26;
    }}
    .btn-restore:hover {{ background: rgba(184,187,38,.08); border-color: rgba(184,187,38,.38); }}

    /* ── Banners ── */
    .banner {{
      border-radius: 10px;
      padding: .875rem 1.25rem;
      margin-bottom: 1.25rem;
      display: flex;
      flex-direction: column;
      gap: .6rem;
    }}
    .banner-success {{
      background: rgba(215,153,33,.06);
      border: 1px solid rgba(215,153,33,.22);
    }}
    .banner-success .banner-title {{
      font-size: .82rem;
      font-weight: 600;
      color: #fabd2f;
    }}
    .banner-error {{
      background: rgba(251,73,52,.06);
      border: 1px solid rgba(251,73,52,.2);
      color: #fb4934;
      font-size: .85rem;
      flex-direction: row;
      align-items: center;
      gap: .6rem;
    }}
    .key-row {{ display: flex; align-items: center; gap: .75rem; }}
    .key-row code {{
      font-family: 'Consolas', 'Fira Code', monospace;
      font-size: .8rem;
      background: rgba(0,0,0,.3);
      border: 1px solid rgba(215,153,33,.18);
      color: #fabd2f;
      padding: .4rem .875rem;
      border-radius: 7px;
      flex: 1;
      word-break: break-all;
    }}
    .btn-copy {{
      background: rgba(215,153,33,.1);
      color: #fabd2f;
      border: 1px solid rgba(215,153,33,.24);
      border-radius: 7px;
      padding: .38rem 1rem;
      font-size: .8rem;
      font-weight: 600;
      white-space: nowrap;
    }}
    .btn-copy:hover {{ background: rgba(215,153,33,.18); }}

    .topbar-brand-link {{
      display: flex; align-items: center; gap: .875rem;
      text-decoration: none; color: inherit;
      align-self: stretch;
      padding: 0 .5rem 0 0;
      transition: opacity .15s;
    }}
    .topbar-brand-link:hover {{ opacity: .75; }}
  </style>
</head>
<body>

  <header class="topbar">
    <a class="topbar-brand-link" href="/admin">
      <div class="logo">🗝️</div>
      <div class="brand">
        <span class="brand-name">Key Manager</span>
        <span class="brand-sub">reska-op-card-api</span>
      </div>
    </a>
    <div class="topbar-fill"></div>
    <a class="admin-pill" href="/admin">Admin</a>
  </header>

  <div class="page">

    {new_key_html}
    {error_html}

    <div class="stats">
      <div class="stat">
        <div class="stat-label">Total Keys</div>
        <div class="stat-value">{total_count}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Active Keys</div>
        <div class="stat-value">{active_count}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Revoked</div>
        <div class="stat-value">{deleted_count}</div>
      </div>
      <div class="stat">
        <div class="stat-label">Total Requests</div>
        <div class="stat-value">{total_requests}</div>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Create Key</h2>
      </div>
      <div class="card-body">
        <form method="post" action="/admin/keys">
          <div class="form-row">
            <div class="field">
              <label class="field-label" for="label-input">Label</label>
              <input id="label-input" type="text" name="label" placeholder="e.g. ci-runner" required {label_value}>
            </div>
            <div class="field">
              <label class="field-label">Permissions</label>
              <label class="check-label">
                <input type="checkbox" name="can_edit"> Allow writes
              </label>
            </div>
            <button class="btn-primary" type="submit">+ Create</button>
          </div>
        </form>
      </div>
    </div>

    <div class="card">
      <div class="card-header">
        <h2 class="card-title">Keys</h2>
        <span class="pill">{active_count} active</span>
        {toggle_html}
      </div>
      <div style="overflow-x:auto">
      <table>
        <thead>
          <tr>
            <th data-col="0" data-type="text">Label</th>
            <th data-col="1" data-type="text">Status</th>
            <th data-col="2" data-type="num">Requests</th>
            <th data-col="3" data-type="text">Last Used</th>
            <th data-col="4" data-type="text">Created</th>
            <th data-col="5" data-type="text">Revoked</th>
            <th data-col="6" data-type="text">Hash</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {rows}{empty_row}
        </tbody>
      </table>
      </div>
    </div>

  </div>

  <script>
    function copyKey(btn) {{
      const key = document.getElementById('new-key').textContent;
      navigator.clipboard.writeText(key).then(() => {{
        btn.textContent = '✓ Copied';
        setTimeout(() => btn.textContent = 'Copy', 2000);
      }});
    }}

    (function () {{
      let sortCol = null, sortAsc = true;
      const ths = document.querySelectorAll('th[data-col]');
      const tbody = document.querySelector('tbody');
      const origOrder = Array.from(tbody.querySelectorAll('tr'));

      function applySort(col, type, asc) {{
        const rows = Array.from(tbody.querySelectorAll('tr'));
        rows.sort((a, b) => {{
          const av = a.cells[col] ? a.cells[col].textContent.trim().replace(/\s+/g, ' ') : '';
          const bv = b.cells[col] ? b.cells[col].textContent.trim().replace(/\s+/g, ' ') : '';
          let cmp = type === 'num' ? (+av || 0) - (+bv || 0)
                                   : av.localeCompare(bv, undefined, {{sensitivity: 'base', numeric: true}});
          return asc ? cmp : -cmp;
        }});
        rows.forEach(r => tbody.appendChild(r));
      }}

      function clearSort() {{
        sortCol = null;
        ths.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
        origOrder.forEach(r => tbody.appendChild(r));
      }}

      ths.forEach(th => {{
        th.addEventListener('click', () => {{
          const col = +th.dataset.col;
          const type = th.dataset.type;
          if (sortCol === col) {{ sortAsc = !sortAsc; }} else {{ sortCol = col; sortAsc = true; }}
          ths.forEach(h => h.classList.remove('sort-asc', 'sort-desc'));
          th.classList.add(sortAsc ? 'sort-asc' : 'sort-desc');
          applySort(col, type, sortAsc);
        }});
        th.addEventListener('contextmenu', e => {{
          if (sortCol === +th.dataset.col) {{ e.preventDefault(); clearSort(); }}
        }});
      }});
    }})();
  </script>
</body>
</html>"""


_SERVICES = [
    {
        "name": "Key Manager",
        "desc": "Create and revoke API keys",
        "href": "/admin/keys",
        "icon": (
            '<svg xmlns="http://www.w3.org/2000/svg" width="28" height="28" viewBox="0 0 24 24"'
            ' fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
            '<circle cx="7.5" cy="15.5" r="5.5"/>'
            '<path d="m21 2-9.6 9.6"/>'
            '<path d="m15.5 7.5 3 3L22 7l-3-3"/>'
            "</svg>"
        ),
    },
]


def _render_dashboard() -> str:
    tiles = ""
    for svc in _SERVICES:
        tiles += (
            f'<a class="tile" href="{svc["href"]}">'
            f'<div class="tile-icon">{svc["icon"]}</div>'
            f'<div class="tile-body">'
            f'<div class="tile-name">{svc["name"]}</div>'
            f'<div class="tile-desc">{svc["desc"]}</div>'
            f"</div></a>"
        )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Admin \xb7 reska-op-card-api</title>
  <link rel="icon" type="image/svg+xml" href="/static/admin-favicon.svg">
  <style>
    *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    :root {{
      --bg: #1d2021; --surface: #282828; --surface-hi: #32302f;
      --border: #3c3836; --border-sub: #32302f;
      --text: #ebdbb2; --text-2: #a89984; --text-3: #7c6f64;
      --accent: #d79921; --violet: #d65d0e;
    }}
    body {{
      font-family: system-ui, -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
      background: var(--bg); color: var(--text);
      min-height: 100vh; font-size: 14px; line-height: 1.5;
    }}
    .topbar {{
      background: var(--surface); border-bottom: 1px solid var(--border);
      height: 54px; padding: 0 2rem;
      display: flex; align-items: center; gap: .875rem;
    }}
    .logo {{
      width: 30px; height: 30px;
      background: linear-gradient(135deg, var(--accent), var(--violet));
      border-radius: 8px; display: flex; align-items: center; justify-content: center; flex-shrink: 0;
    }}
    .logo svg {{ width: 16px; height: 16px; stroke: #fff; }}
    .brand {{ display: flex; flex-direction: column; gap: 1px; }}
    .brand-name {{ font-size: .85rem; font-weight: 600; color: var(--text); letter-spacing: -.01em; line-height: 1; }}
    .brand-sub {{ font-size: .68rem; color: var(--text-2); line-height: 1; }}
    .topbar-fill {{ flex: 1; }}
    .admin-pill {{
      font-size: .68rem; font-weight: 600; letter-spacing: .06em; text-transform: uppercase;
      color: var(--text-3); background: var(--border-sub); border: 1px solid var(--border);
      border-radius: 5px; padding: 3px 9px;
    }}
    .page {{ max-width: 860px; margin: 0 auto; padding: 2.5rem 2rem; }}
    .page-heading {{
      font-size: 1.35rem; font-weight: 700; letter-spacing: -.02em;
      color: var(--text); margin-bottom: .35rem;
    }}
    .page-sub {{ font-size: .85rem; color: var(--text-2); margin-bottom: 2rem; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }}
    .tile {{
      display: flex; flex-direction: column; gap: 1rem;
      background: var(--surface); border: 1px solid var(--border); border-radius: 14px;
      padding: 1.5rem 1.25rem; text-decoration: none; color: inherit;
      transition: border-color .15s, background .15s, transform .1s; cursor: pointer;
    }}
    .tile:hover {{ background: var(--surface-hi); border-color: rgba(215,153,33,.4); transform: translateY(-2px); }}
    .tile:hover .tile-icon {{ background: rgba(215,153,33,.18); color: #fabd2f; }}
    .tile-icon {{
      width: 52px; height: 52px; background: rgba(215,153,33,.12); border-radius: 12px;
      display: flex; align-items: center; justify-content: center;
      color: #d79921; transition: background .15s, color .15s; flex-shrink: 0;
    }}
    .tile-icon svg {{ width: 26px; height: 26px; }}
    .tile-name {{ font-size: .95rem; font-weight: 600; color: var(--text); letter-spacing: -.01em; }}
    .tile-desc {{ font-size: .78rem; color: var(--text-2); margin-top: .15rem; line-height: 1.4; }}
  </style>
</head>
<body>
  <header class="topbar">
    <div class="logo">
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none"
           stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/>
        <path d="M7 11V7a5 5 0 0 1 10 0v4"/>
      </svg>
    </div>
    <div class="brand">
      <span class="brand-name">Admin</span>
      <span class="brand-sub">reska-op-card-api</span>
    </div>
    <div class="topbar-fill"></div>
    <span class="admin-pill">Admin</span>
  </header>
  <div class="page">
    <h1 class="page-heading">Control Panel</h1>
    <p class="page-sub">Select a service to manage.</p>
    <div class="grid">{tiles}</div>
  </div>
</body>
</html>"""


@router.get("", response_class=HTMLResponse)
@router.get("/", response_class=HTMLResponse)
def admin_dashboard(_: None = Depends(_require_admin)):
    return _render_dashboard()


@router.get("/keys", response_class=HTMLResponse)
def list_keys(
    show_deleted: bool = Query(default=True),
    new_key: str | None = Query(default=None),
    new_label: str | None = Query(default=None),
    error: str | None = Query(default=None),
    input_label: str | None = Query(default=None),
    _: None = Depends(_require_admin),
    session: Session = Depends(get_session),
):
    stmt = select(ApiKey) if show_deleted else select(ApiKey).where(ApiKey.revoked_ts == None)  # noqa: E711
    keys = list(session.exec(stmt).all())
    revoked_count = session.exec(
        select(func.count()).select_from(ApiKey).where(ApiKey.revoked_ts != None)  # noqa: E711
    ).one()
    return _render(
        keys,
        new_key=new_key,
        new_label=new_label,
        error=error,
        input_label=input_label,
        show_deleted=show_deleted,
        revoked_count=revoked_count,
    )


@router.post("/keys")
def create_key(
    label: str = Form(...),
    can_edit: bool = Form(default=False),
    _: None = Depends(_require_admin),
    session: Session = Depends(get_session),
):
    raw_key = secrets.token_urlsafe(32)
    key_hash = blake3.blake3(raw_key.encode()).hexdigest()
    record = ApiKey(key=key_hash, can_edit=can_edit, label=label)
    session.add(record)
    try:
        session.commit()
    except IntegrityError:
        session.rollback()
        qs = urlencode({"error": f"Label '{label}' is already in use.", "input_label": label})
        return RedirectResponse(f"/admin/keys?{qs}", status_code=303)

    qs = urlencode({"new_key": raw_key, "new_label": label})
    return RedirectResponse(f"/admin/keys?{qs}", status_code=303)


@router.post("/keys/{key_id}/delete")
def delete_key(
    key_id: int,
    _: None = Depends(_require_admin),
    session: Session = Depends(get_session),
):
    record = session.get(ApiKey, key_id)
    if not record or record.revoked_ts is not None:
        raise HTTPException(status_code=404, detail="Key not found")
    record.revoked_ts = func.strftime("%Y-%m-%d %H:%M:%f", "now")
    session.add(record)
    session.commit()
    return RedirectResponse("/admin/keys", status_code=303)


@router.post("/keys/{key_id}/restore")
def restore_key(
    key_id: int,
    _: None = Depends(_require_admin),
    session: Session = Depends(get_session),
):
    record = session.get(ApiKey, key_id)
    if not record or record.revoked_ts is None:
        raise HTTPException(status_code=404, detail="Key not found or not revoked")
    record.revoked_ts = None
    session.add(record)
    session.commit()
    return RedirectResponse("/admin/keys", status_code=303)


@router.post("/keys/{key_id}/purge")
def purge_key(
    key_id: int,
    _: None = Depends(_require_admin),
    session: Session = Depends(get_session),
):
    record = session.get(ApiKey, key_id)
    if not record:
        raise HTTPException(status_code=404, detail="Key not found")
    session.delete(record)
    session.commit()
    return RedirectResponse("/admin/keys", status_code=303)
