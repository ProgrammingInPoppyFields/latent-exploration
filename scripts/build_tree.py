#!/usr/bin/env python3
"""
Parses the flat directory of branching-exploration mp4s into a tree structure,
copies cleanly-named videos into videos/, and writes tree.json for the viz.

Source filenames encode the branch path, e.g. 0_1_2_1_1.mp4 is the node reached
by picking branch 1, then 2, then 1, then 1 from the root "0". Missing
intermediate ids (where a node was branched from but the clip itself wasn't
kept) become "virtual" placeholder nodes with no video.
"""
import json
import re
import shutil
from pathlib import Path

SOURCE_DIR = Path("/Users/helen/Downloads/Latent Exploration - Workspace/ORIGIN - 0")
REPO_DIR = Path(__file__).resolve().parent.parent
VIDEOS_OUT = REPO_DIR / "videos"
TREE_JSON_OUT = REPO_DIR / "tree.json"

FILENAME_RE = re.compile(r"^([\d]+(?:_[\d]+)*)(.*?)\.mp4(?:\.mp4)?$", re.IGNORECASE)


def parse_source_files():
    parsed = {}  # id -> (source_path, label)
    skipped = []
    for f in sorted(SOURCE_DIR.glob("*.mp4")):
        m = FILENAME_RE.match(f.name)
        if not m:
            skipped.append(f.name)
            continue
        node_id, suffix = m.groups()
        label = suffix.strip(" -_.") or None
        parsed[node_id] = (f, label)
    return parsed, skipped


def build_tree(parsed):
    real_ids = set(parsed.keys())
    all_ids = set(real_ids)
    for nid in real_ids:
        parts = nid.split("_")
        for i in range(1, len(parts)):
            all_ids.add("_".join(parts[:i]))
    all_ids.add("0")

    nodes = {}
    for nid in all_ids:
        parts = nid.split("_")
        parent = "_".join(parts[:-1]) if len(parts) > 1 else None
        source, label = parsed.get(nid, (None, None))
        nodes[nid] = {
            "id": nid,
            "parent": parent,
            "children": [],
            "video": f"videos/{nid}.mp4" if source else None,
            "label": label,
            "virtual": source is None,
        }

    for nid, node in nodes.items():
        if node["parent"] is not None:
            nodes[node["parent"]]["children"].append(nid)

    def sort_key(cid):
        return int(cid.split("_")[-1])

    for node in nodes.values():
        node["children"].sort(key=sort_key)

    return nodes


def copy_videos(parsed):
    VIDEOS_OUT.mkdir(exist_ok=True)
    for nid, (source, _label) in parsed.items():
        dest = VIDEOS_OUT / f"{nid}.mp4"
        if not dest.exists() or dest.stat().st_size != source.stat().st_size:
            shutil.copy2(source, dest)


def main():
    parsed, skipped = parse_source_files()
    print(f"Parsed {len(parsed)} video nodes, skipped {len(skipped)}: {skipped}")

    nodes = build_tree(parsed)
    real = sum(1 for n in nodes.values() if not n["virtual"])
    virtual = sum(1 for n in nodes.values() if n["virtual"])
    print(f"Tree: {len(nodes)} total nodes ({real} real, {virtual} virtual placeholders)")

    copy_videos(parsed)
    print(f"Copied {len(parsed)} videos into {VIDEOS_OUT}")

    sorted_nodes = dict(sorted(nodes.items()))
    TREE_JSON_OUT.write_text(json.dumps({"root": "0", "nodes": sorted_nodes}, indent=2))
    print(f"Wrote {TREE_JSON_OUT}")


if __name__ == "__main__":
    main()
