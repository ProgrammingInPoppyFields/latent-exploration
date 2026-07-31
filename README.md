# Latent Exploration

An interactive branching-tree viewer for a latent-space video exploration: 298 clips,
each one a branch taken from a previous generation, laid out as a clickable node graph.

## How the tree works

Each clip's filename encodes its path from the root, e.g. `0_1_2_1_1.mp4` is reached by
picking branch 1, then 2, then 1, then 1. `scripts/build_tree.py` parses those filenames
into `tree.json` (parent/child links) and copies the source clips into `videos/` under
clean id-based names.

A couple of branch points exist where a clip was branched from but the intermediate clip
itself wasn't kept — those show up in the graph as small dashed "virtual" nodes with no
video attached, just to keep the tree connected.

One file, `bruh seriously.mp4`, didn't fit the naming scheme at all and was left out of
the graph entirely.

## Viewing locally

```
python3 -m http.server 8000
```

then open `http://localhost:8000`.

## Regenerating the tree

If the source folder (`/Users/helen/Downloads/Latent Exploration - Master`) changes,
rerun:

```
python3 scripts/build_tree.py
```

This re-copies any new/changed videos into `videos/` and rewrites `tree.json`.

## Publishing to GitHub Pages

1. Push this repo to GitHub.
2. In the repo settings, enable Pages for the `main` branch (root).
3. The site will build automatically since it's static HTML/CSS/JS with no build step.
