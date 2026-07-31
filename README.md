# Latent Exploration

![Behold](screenshots/1.png)

299 nodes. 1 origin. Countless hours that could have been spent doing literally
anything else. This is a website whose entire purpose is to let you click circles
and watch tiny videos, and honestly? It's incredible. Groundbreaking. A triumph
of human-computer interaction that will not appear on your resume.

Somewhere, someone sat down and generated a video, then generated four more videos
*from* that video, then kept going — recursively, compulsively, at 2am, for over a
month — until a folder of mp4s achieved sentience and had to be given a name, a
build script, and a glowing white circle to call home.

## What is this, actually

A branching-tree viewer. Every clip is a decision someone made about what should
happen next, and every decision spawned more decisions, and here we all are. Click
a filled node, it plays. Click the big glowing one in the middle, you get The
Original Image, the one that started this whole cascade, presented with the
reverence of a museum placard.

The path from wherever you clicked back to the beginning lights up cyan, because
apparently we needed to *see* the full weight of how we got here.

## How the tree works (yes, it's just filenames)

Each clip's filename is its own address, e.g. `0_1_2_1_1.mp4` means: from the
start, take branch 1, then 2, then 1, then 1, arrive at your destination, question
nothing. `scripts/build_tree.py` reads this glorified breadcrumb trail, builds
`tree.json`, and copies the clips into `videos/` with names a computer can respect.

A couple of nodes exist only as ghosts — branch points where something was
branched *from* but the clip itself didn't survive to see this README. They show
up as small dashed circles doing their best.

One file, `bruh seriously.mp4`, refused to participate in the naming convention on
principle and has been excommunicated from the graph. We respect its choice.

## Running this locally, a task of unbelievable difficulty

```
python3 -m http.server 8000
```

Then go to `http://localhost:8000` like a person who knows how URLs work.

## Regenerating the tree

Added more chaos to the source folder? Rerun this and let the script sort out your
life choices:

```
python3 scripts/build_tree.py
```

## Publishing to GitHub Pages

1. Push this repo to GitHub. (Godspeed.)
2. Repo settings → Pages → enable for `main`, root.
3. Static site, zero build step, it just works, which is more than can be said for
   most things.
