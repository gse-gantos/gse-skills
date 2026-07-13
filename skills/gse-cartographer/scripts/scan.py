#!/usr/bin/env python3
"""gse-cartographer scan: sweep or diff the project folder against the map manifest.

Usage:
  python3 scan.py --root <project_root> --diff   # boot scan: report new/changed/missing, no writes
  python3 scan.py --root <project_root> --full   # full sweep: merge into manifest.json (preserves classifications)

The map lives at <root>/Claude/Map/machine/. Classification is NOT done here --
new records enter as status "unmapped" with a hint-based proposed_type for a
human/Claude to confirm (confidence gate, D8). This script never writes outside
Claude/Map/.
"""
import argparse, fnmatch, json, os, re, sys, time
from datetime import date
from pathlib import PurePosixPath

MAP_DIR = "Claude/Map"
OS_PATHS = {"00_START_HERE.md", "SEED_TEMPLATE_BUILD_NOTES.md", ".obsidian"}


def load_json(p):
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def slug(path):
    s = re.sub(r"[^A-Za-z0-9]+", "-", path).strip("-").lower()
    return s[:100]


def segments_match(candidate, pattern):
    """fnmatch per path segment: '*' never crosses '/'. Segment counts must be equal."""
    c, p = candidate.split("/"), pattern.split("/")
    return len(c) == len(p) and all(fnmatch.fnmatch(cs, ps) for cs, ps in zip(c, p))


def batch_dir_for(relpath, batch_patterns):
    """Deepest ancestor DIRECTORY of relpath matching a batch pattern (the file itself is excluded)."""
    parts = PurePosixPath(relpath).parts
    best = None
    for i in range(1, len(parts)):  # ancestors only, never the file itself
        candidate = "/".join(parts[:i])
        for pat in batch_patterns:
            if segments_match(candidate, pat):
                best = candidate  # keep going: deepest match wins
    return best


def hint_classify(relpath, schema):
    """Return (type, confidence) from routing_schema hints. Order: specific before narrative."""
    low = relpath.lower()
    name = PurePosixPath(relpath).name.lower()
    ext = PurePosixPath(relpath).suffix.lower()
    best = ("unknown", "low")
    order = ["app-config", "os-doc", "photos", "payroll-payment", "change-event", "rfi",
             "contract-document", "schedule", "safety-permit", "meeting-record", "takeoff",
             "procurement", "submittal-package", "drawing-set", "spec", "correspondence",
             "reference-data"]
    for t in order:
        hints = schema["content_types"].get(t, {}).get("hints", {})
        path_hit = any(p.lower() in low for p in hints.get("path_patterns", []))
        name_hit = any(p.lower() in name for p in hints.get("name_patterns", []))
        ext_hit = ext in [e.lower() for e in hints.get("extensions", [])]
        if path_hit and (name_hit or ext_hit or not hints.get("name_patterns")):
            return (t, "medium")  # path + corroboration; human still confirms off-convention
        if path_hit or name_hit:
            best = (t, "low") if best[0] == "unknown" else best
    return best


def sweep(root, schema):
    """Walk the tree; return {id: record-shape} of current state (no classification fields)."""
    batch_patterns = schema["batch_rules"]["raw_patterns"] + schema["batch_rules"]["synthesis_patterns"]
    records, batches = {}, {}
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace(os.sep, "/")
        if rel_dir == ".":
            rel_dir = ""
        if rel_dir == MAP_DIR or rel_dir.startswith(MAP_DIR + "/"):
            dirnames[:] = []
            continue
        for fn in filenames:
            rel = f"{rel_dir}/{fn}" if rel_dir else fn
            full = os.path.join(dirpath, fn)
            try:
                st = os.stat(full)
            except OSError:
                continue
            b = batch_dir_for(rel, batch_patterns)
            top = rel.split("/")[0]
            domain = "os" if top in OS_PATHS else ("synthesis" if top == "Claude" else "raw")
            if b:
                bb = batches.setdefault(b, {"size": 0, "count": 0, "mtime": 0.0, "domain": domain})
                bb["size"] += st.st_size
                bb["count"] += 1
                bb["mtime"] = max(bb["mtime"], st.st_mtime)
            else:
                records[slug(rel)] = {
                    "path": rel, "kind": "file", "domain": domain,
                    "size": st.st_size, "mtime": time.strftime("%Y-%m-%d", time.localtime(st.st_mtime)),
                }
    for b, v in batches.items():
        records[slug(b)] = {
            "path": b, "kind": "batch", "domain": v["domain"], "size": v["size"],
            "file_count": v["count"], "mtime": time.strftime("%Y-%m-%d", time.localtime(v["mtime"])),
        }
    return records


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--diff", action="store_true")
    mode.add_argument("--full", action="store_true")
    args = ap.parse_args()

    machine = os.path.join(args.root, MAP_DIR, "machine")
    schema = load_json(os.path.join(machine, "routing_schema.json"))
    manifest_path = os.path.join(machine, "manifest.json")
    manifest = load_json(manifest_path) if os.path.exists(manifest_path) else {"schema_version": "1.0", "records": {}}
    old = manifest["records"]

    cur = sweep(args.root, schema)
    new_ids = [i for i in cur if i not in old]
    missing_ids = [i for i in old if i not in cur and not old[i].get("missing")]
    changed_ids = [i for i in cur if i in old and (
        cur[i]["size"] != old[i].get("size") or cur[i]["mtime"] != old[i].get("mtime")
        or cur[i].get("file_count") != old[i].get("file_count"))]

    if args.diff:
        print(f"DIFF vs manifest ({len(old)} records): {len(new_ids)} new, {len(changed_ids)} changed, {len(missing_ids)} missing")
        for i in new_ids:
            t, c = hint_classify(cur[i]["path"], schema)
            print(f"  NEW      {cur[i]['path']}  [{cur[i]['kind']}]  proposed: {t} ({c})")
        for i in changed_ids:
            print(f"  CHANGED  {cur[i]['path']}")
        for i in missing_ids:
            print(f"  MISSING  {old[i]['path']}")
        return

    # --full: merge, preserving classification fields on existing records
    today = date.today().isoformat()
    for i, r in cur.items():
        if i in old:
            keep = old[i]
            if i in changed_ids and keep.get("status") not in (None, "unmapped"):
                keep["changed_since_classification"] = True
            keep.update({k: r[k] for k in ("size", "mtime") if k in r})
            if "file_count" in r:
                keep["file_count"] = r["file_count"]
            keep.pop("missing", None)
        else:
            t, c = hint_classify(r["path"], schema)
            r.update({"id": i, "type": None, "proposed_type": t, "type_confidence": c,
                      "classified_by": None, "subproject": None, "status": "unmapped",
                      "processed_home": [], "provenance": f"found by full sweep {today}", "notes": ""})
            if r["domain"] == "synthesis":
                r.update({"status": "synthesis", "type": "synthesis", "proposed_type": None,
                          "type_confidence": "high", "classified_by": "auto"})
            old[i] = r
    for i in missing_ids:
        old[i]["missing"] = True
        old[i]["notes"] = (old[i].get("notes", "") + f" [not found on disk {today}]").strip()

    manifest["updated"] = today
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=1, ensure_ascii=False)

    counts = {}
    for r in old.values():
        counts[r["path"].split("/")[0]] = counts.get(r["path"].split("/")[0], 0) + 1
    with open(os.path.join(machine, "scan_state.json"), "w", encoding="utf-8") as f:
        json.dump({"last_full_scan": today, "record_count": len(old), "per_top_folder": counts}, f, indent=1)
    print(f"FULL sweep merged: {len(old)} records ({len(new_ids)} new, {len(changed_ids)} changed, {len(missing_ids)} missing-flagged)")


if __name__ == "__main__":
    main()
