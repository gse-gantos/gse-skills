#!/usr/bin/env python3
"""gse-cartographer: regenerate Claude/Map/views/ from manifest.json. Views are disposable; manifest is canonical.

Usage: python3 render_views.py --root <project_root>
"""
import argparse, json, os
from datetime import date

NO_PROCESS_TYPES = {"photos", "os-doc", "app-config", "reference-data", "synthesis"}


def hsize(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.0f} {u}"
        n /= 1024
    return f"{n:.1f} TB"


def row(r):
    p = r["path"] + ("/" if r["kind"] == "batch" else "")
    extra = f" ({r['file_count']} files)" if r["kind"] == "batch" else ""
    t = r.get("type") or f"*{r.get('proposed_type','?')}?*"
    home = "; ".join(r.get("processed_home", [])) or "—"
    note = (r.get("notes") or "").replace("|", "/")
    return f"| `{p}`{extra} | {t} | {r.get('subproject') or '—'} | {r['status']} | {home} | {note} |"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    args = ap.parse_args()
    machine = os.path.join(args.root, "Claude/Map/machine")
    views = os.path.join(args.root, "Claude/Map/views")
    os.makedirs(views, exist_ok=True)
    m = json.load(open(os.path.join(machine, "manifest.json"), encoding="utf-8"))
    state = json.load(open(os.path.join(machine, "scan_state.json"), encoding="utf-8"))
    recs = [r for r in m["records"].values() if not r.get("missing")]
    today = date.today().isoformat()
    hdr_cols = "| Path | Type | Subproject | Status | Processed home | Notes |\n|---|---|---|---|---|---|"

    # FILE_MAP.md
    raw = sorted([r for r in recs if r["domain"] in ("raw", "os")], key=lambda r: r["path"].lower())
    syn = sorted([r for r in recs if r["domain"] == "synthesis"], key=lambda r: r["path"].lower())
    by_top = {}
    for r in raw:
        by_top.setdefault(r["path"].split("/")[0], []).append(r)
    lines = [
        "# FILE_MAP — Project 824 full catalog",
        f"\n**Regenerated:** {today} · **Last full scan:** {state.get('last_full_scan','?')} · **Records:** {len(recs)}",
        "\n**Wiki:** [[file-map]] · Queue: [UNPROCESSED](UNPROCESSED.md) · Supersessions: [SUPERSEDED](SUPERSEDED.md)",
        "\n> Generated from `machine/manifest.json` — do not hand-edit. Raw files never move; this map records where things ARE.",
        "\n## Official record (raw, read-only)\n",
    ]
    for top, rows in by_top.items():
        lines.append(f"### {top}\n\n{hdr_cols}")
        lines += [row(r) for r in rows]
        lines.append("")
    lines.append(f"## Synthesis layer (`Claude/`)\n\n{hdr_cols}")
    lines += [row(r) for r in syn]
    open(os.path.join(views, "FILE_MAP.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # UNPROCESSED.md
    q = [r for r in raw if r["status"] in ("unmapped", "classified")
         and (r.get("type") or r.get("proposed_type")) not in NO_PROCESS_TYPES]
    q.sort(key=lambda r: ((r.get("type") or r.get("proposed_type") or "zz"), r["path"].lower()))
    lines = [
        "# UNPROCESSED — the work queue",
        f"\n**Regenerated:** {today} · **Queue length:** {len(q)}",
        "\n**Wiki:** [[file-map]]",
        "\n> Everything the OS knows exists but has NOT synthesized. Honest by design — large is expected. Types marked `*name?*` are unconfirmed hint proposals.",
        f"\n| Path | Type | Subproject | Size | Notes |\n|---|---|---|---|---|",
    ]
    for r in q:
        t = r.get("type") or f"*{r.get('proposed_type','?')}?*"
        extra = f" ({r['file_count']} files)" if r["kind"] == "batch" else ""
        lines.append(f"| `{r['path']}`{extra} | {t} | {r.get('subproject') or '—'} | {hsize(r['size'])} | {(r.get('notes') or '').replace('|','/')} |")
    open(os.path.join(views, "UNPROCESSED.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")

    # SUPERSEDED.md
    s = [r for r in recs if r["status"] == "superseded"]
    lines = [
        "# SUPERSEDED — do not build from these",
        f"\n**Regenerated:** {today}",
        "\n**Wiki:** [[file-map]]",
        "\n> Files/sets known to be superseded. Per AGENTS.md §9: confirm the current set before any drawing answer.",
        f"\n{hdr_cols}",
    ]
    lines += [row(r) for r in s] if s else ["*(none recorded)*"]
    open(os.path.join(views, "SUPERSEDED.md"), "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"views regenerated: FILE_MAP ({len(recs)} records), UNPROCESSED ({len(q)}), SUPERSEDED ({len(s)})")


if __name__ == "__main__":
    main()
