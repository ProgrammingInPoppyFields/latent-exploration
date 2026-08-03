#!/usr/bin/env python3
"""
Parses the flat directory of branching-exploration mp4s into a tree structure,
copies cleanly-named videos into videos/, and writes tree.json for the viz.

Source filenames encode the branch path, e.g. 0_1_2_1_1.mp4 is the node reached
by picking branch 1, then 2, then 1, then 1 from the root "0". Missing
intermediate ids (where a node was branched from but the clip itself wasn't
kept) become "virtual" placeholder nodes with no video.
"""
import colorsys
import io
import json
import re
import shutil
import subprocess
from pathlib import Path

from PIL import Image

SOURCE_DIR = Path("/Users/helen/Downloads/Latent Exploration - Workspace/ORIGIN - 0")
REPO_DIR = Path(__file__).resolve().parent.parent
VIDEOS_OUT = REPO_DIR / "videos"
TREE_JSON_OUT = REPO_DIR / "tree.json"
COLOR_CACHE_PATH = REPO_DIR / "scripts" / "color_cache.json"
ORIGIN_IMAGE = REPO_DIR / "origin_images" / "1.png"

FILENAME_RE = re.compile(r"^([\d]+(?:_[\d]+)*)(.*?)\.mp4(?:\.mp4)?$", re.IGNORECASE)

FALLBACK_COLOR = "#6ee7ff"  # matches --node-real, used when a frame is essentially grayscale
HUE_BUCKETS = 24


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


def needs_copy(source, dest):
    return not dest.exists() or dest.stat().st_size != source.stat().st_size


def copy_videos(parsed):
    VIDEOS_OUT.mkdir(exist_ok=True)
    for nid, (source, _label) in parsed.items():
        dest = VIDEOS_OUT / f"{nid}.mp4"
        if needs_copy(source, dest):
            shutil.copy2(source, dest)


def get_duration(video_path):
    result = subprocess.run(
        ["ffprobe", "-v", "quiet", "-show_entries", "format=duration", "-of", "csv=p=0", str(video_path)],
        capture_output=True, text=True,
    )
    try:
        return float(result.stdout.strip())
    except ValueError:
        return 0.0


def extract_representative_frame(video_path):
    # Midjourney clips animate outward from their parent's final frame, so
    # frame 0 of a clip looks nearly identical to frame 0 of its siblings
    # and its parent - sampling late in the clip is what actually captures
    # what's distinctive about it.
    duration = get_duration(video_path)
    seek = max(0.1, duration * 0.8) if duration > 1 else 0.0
    args = ["ffmpeg", "-y"]
    if seek > 0:
        args += ["-ss", str(seek)]
    args += ["-i", str(video_path), "-vframes", "1", "-f", "image2pipe", "-vcodec", "png", "-"]
    result = subprocess.run(args, capture_output=True)
    if result.returncode != 0 or not result.stdout:
        return None
    return result.stdout


def extract_dominant_color(image_bytes):
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    img.thumbnail((48, 48))

    # Bucket by hue to find the dominant hue family, but keep each bucket's
    # own weighted-average saturation/value rather than flattening every
    # winning bucket to the same fixed vividness - otherwise most clips in
    # a single-hue-family collection (e.g. lots of blues) end up rendered
    # as the exact same color, which defeats the point of per-node color.
    bucket_weight = [0.0] * HUE_BUCKETS
    bucket_hue_sum = [0.0] * HUE_BUCKETS
    bucket_sat_sum = [0.0] * HUE_BUCKETS
    bucket_val_sum = [0.0] * HUE_BUCKETS

    for r, g, b in img.getdata():
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        weight = s * v
        bucket = int(h * HUE_BUCKETS) % HUE_BUCKETS
        bucket_weight[bucket] += weight
        bucket_hue_sum[bucket] += h * weight
        bucket_sat_sum[bucket] += s * weight
        bucket_val_sum[bucket] += v * weight

    total = sum(bucket_weight)
    if total < 1e-6:
        return FALLBACK_COLOR

    bucket = max(range(HUE_BUCKETS), key=lambda i: bucket_weight[i])
    w = bucket_weight[bucket]
    hue = bucket_hue_sum[bucket] / w
    # Floors are high on purpose: however dim/muted the source frame is, the
    # node color should always read as bright and clearly visible in the UI.
    sat = min(max(bucket_sat_sum[bucket] / w, 0.6), 0.9)
    val = min(max(bucket_val_sum[bucket] / w, 0.85), 0.98)
    r, g, b = colorsys.hsv_to_rgb(hue, sat, val)
    return "#{:02x}{:02x}{:02x}".format(round(r * 255), round(g * 255), round(b * 255))


def load_color_cache():
    if COLOR_CACHE_PATH.exists():
        return json.loads(COLOR_CACHE_PATH.read_text())
    return {}


def compute_colors(parsed, color_cache):
    colors = {}
    changed = False
    for nid, (source, _label) in parsed.items():
        dest = VIDEOS_OUT / f"{nid}.mp4"
        stale = nid not in color_cache or needs_copy(source, dest)
        if stale:
            frame = extract_representative_frame(source)
            color_cache[nid] = extract_dominant_color(frame) if frame else FALLBACK_COLOR
            changed = True
        colors[nid] = color_cache[nid]
    return colors, changed


def compute_root_color():
    if not ORIGIN_IMAGE.exists():
        return FALLBACK_COLOR
    return extract_dominant_color(ORIGIN_IMAGE.read_bytes())


def main():
    parsed, skipped = parse_source_files()
    print(f"Parsed {len(parsed)} video nodes, skipped {len(skipped)}: {skipped}")

    nodes = build_tree(parsed)
    real = sum(1 for n in nodes.values() if not n["virtual"])
    virtual = sum(1 for n in nodes.values() if n["virtual"])
    print(f"Tree: {len(nodes)} total nodes ({real} real, {virtual} virtual placeholders)")

    color_cache = load_color_cache()
    colors, cache_changed = compute_colors(parsed, color_cache)
    for nid, hexcolor in colors.items():
        nodes[nid]["color"] = hexcolor
    root_color = compute_root_color()
    nodes["0"]["color"] = root_color
    if cache_changed:
        COLOR_CACHE_PATH.write_text(json.dumps(dict(sorted(color_cache.items())), indent=2))
    print(f"Computed colors for {len(colors)} real nodes (root: {root_color})")

    copy_videos(parsed)
    print(f"Copied {len(parsed)} videos into {VIDEOS_OUT}")

    sorted_nodes = dict(sorted(nodes.items()))
    TREE_JSON_OUT.write_text(json.dumps({"root": "0", "nodes": sorted_nodes}, indent=2))
    print(f"Wrote {TREE_JSON_OUT}")


if __name__ == "__main__":
    main()
