# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

A static site that visualizes a branching-tree video exploration (298 clips, all
Midjourney-generated) as a clickable/hoverable radial node graph in D3. No build
step, no framework, no package.json — it's `index.html` (D3 v7 loaded from CDN),
`tree.json` (the graph data), and a `videos/` folder of mp4s, served as-is.

## Commands

Run locally:
```
python3 -m http.server 8000
```
then open `http://localhost:8000`.

Rebuild the graph data after adding/changing source clips:
```
python3 scripts/build_tree.py
```
Safe to rerun anytime — it rescans the whole source folder, rewrites `tree.json`
from scratch, and only copies videos into `videos/` that are new or changed. It
prints a summary (parsed/skipped counts) each run.

There is no test suite, linter, or build step in this repo.

## Architecture

**Data pipeline (`scripts/build_tree.py`)**: reads mp4s from a source folder
(`/Users/helen/Downloads/Latent Exploration - Master`, outside this repo) whose
filenames encode tree position, e.g. `0_1_2_1_1.mp4` = branch 1 → 2 → 1 → 1 from
root `0`. The script parses `parentId_childIndex` structure out of each filename,
builds a full parent/child node map (inserting "virtual" placeholder nodes for
any branch point whose own clip wasn't kept, so the tree stays connected), copies
real clips into `videos/<id>.mp4`, and writes `tree.json`:
```
{ "root": "0", "nodes": { "<id>": { id, parent, children[], video|null, label|null, virtual } } }
```
A trailing bit of text in a filename (e.g. `0_4 - TURN LEFT.mp4`) becomes that
node's `label`. Filenames that don't match the numeric pattern at all (e.g.
`bruh seriously.mp4`) are skipped and printed, not added to the tree.

**Frontend (`index.html`)**: single file, all CSS/JS inline, D3 v7 from
`cdn.jsdelivr.net`. Fetches `tree.json`, builds a `d3.hierarchy`, and lays it out
with `d3.tree()` in radial mode (angle/radius, not x/y) via `layoutRadial()`.

Key things to know before touching the graph rendering:
- The root node is rendered at local `(0,0)` and is deliberately **not** given a
  separate manual translate — `g`'s transform is owned entirely by the D3 zoom
  behavior (`svg.call(zoom.transform, t)`). Setting a manual `g.attr("transform", ...)`
  alongside zoom will get silently overwritten the next time `zoom.transform` fires,
  which previously caused the whole graph to render off-center/mis-scaled. Don't
  reintroduce a competing transform.
- Don't set an SVG `viewBox` sized to the diagram's own coordinate space — the
  fit-to-view math (`vw`/`vh` from `#graph-wrap`'s clientWidth/Height) assumes
  1 SVG user unit = 1 CSS pixel, which only holds if there's no viewBox (or one
  matching the element's actual pixel size).
- Node sizing (`nodeRadius()`) scales with a node's child count, except the root,
  which is a fixed larger size handled as a special case throughout (own CSS
  class `.root`, own click/hover handlers for showing `origin_images/1.png`).
- Path-highlight color scheme: cyan (`--path`) for every node between the current
  one and the root, solid white (`--current`) for the root and for whichever node
  is actually selected/hovered — this applies uniformly whether the interaction
  is a click (persistent, via `.selected`/`.on-path` classes) or a hover
  (transient, via `.hover-path` class, cleared on mouseleave). The root gets an
  explicit override rule so it stays white even when it's just an ancestor in
  someone else's path, since without it the generic ancestor-cyan rule would win
  on specificity.
- The sidebar (video player) is collapsed by default and only opens on an actual
  click (`selectNode`/`selectRoot` call `setSidebarOpen(true)`), not on hover.

**Assets**: `origin_images/1.png` is the starting image shown when hovering/
clicking the root node. `screenshots/1.png` is the README hero image.

## Publishing

GitHub Pages, deployed from `main` branch root — no Actions workflow. `.nojekyll`
is present and should stay; this is a plain static site with hundreds of files
and gains nothing from Jekyll processing. Repo is ~870MB (almost entirely video),
which is under GitHub Pages' soft ~1GB site-size guidance but with limited
headroom — be aware of this if adding a large batch of new clips.

The `origin` remote points to `ProgrammingInPoppyFields/latent-exploration.git`.
Push access under some local credentials may 403; if so, that's an auth/access
issue on GitHub's side, not a repo problem — leave commits local and let the user
push from their own environment rather than trying to work around it.

## Tone note

`README.md` is intentionally written in a deadpan/sarcastic voice per the user's
request — don't "fix" it back to a neutral tone in future edits unless asked.
