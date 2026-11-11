---
name: onklave-blender-scene
description: How to build and render a 3D scene in an Onklave project — the committed corpus is a bpy script, execution is headless `blender -b -P`, and previews go to out/previews/. Read this FIRST, before any other Blender skill; it overrides their MCP execution instructions.
license: MIT
metadata:
  author: Onklave
  version: '1.0.0'
  domain: blender
  role: contract
  triggers: scene, blend, render, preview, bpy, build.py, 3D
---

# Onklave scenes: the execution contract

The other Blender skills in this project are good domain knowledge — topology
standards, PBR material setup, sampling tables, camera conventions. **Their
execution instructions do not apply here.** They assume a live Blender driven
over MCP with a human watching the viewport. You have neither.

Read this first. When another skill says "execute in Blender via MCP" or "take
a viewport screenshot", substitute the workflow below.

## What is committed, and what is not

**The scene is a Python script.** That is the whole design: a `.blend` is a
binary with no diff, so a human reviewing an agent's change to one could only
ever look at a picture and guess. A script is text — it reviews, diffs, blames
and merges like any other source file.

```
scenes/<name>/
  build.py          # COMMITTED — builds the scene and renders the previews
  params.json       # COMMITTED — the scene's inputs, if it takes any
out/
  scene.blend       # build output — NEVER commit
  previews/*.png    # build output — NEVER commit
```

`out/` is gitignored. Do not add it, do not force-add anything inside it, and
do not commit a `.blend` "so the reviewer can open it" — the reviewer gets
rendered frames automatically.

## The loop

1. **Edit `build.py`.** Everything about the scene lives here: geometry,
   materials, lights, camera, render settings.
2. **Run it.** `blender -b -P scenes/<name>/build.py`
3. **Look at what you made.** Read `out/previews/01.png` with the Read tool.
   It is an image; you can see it. This is the step that makes the rest work —
   do not skip it and assume the script did what you intended.
4. **Fix and repeat.** Iterate on the script, not on a saved `.blend`.
5. **Commit the script.** The platform re-runs your preview command after the
   commit and shows those frames to a human for approval.

Step 3 is not optional. A script that runs without error can still produce a
black frame, a camera inside a wall, or a material that reads as grey plastic.
Exit code 0 means Blender did not crash; it says nothing about whether the
image is right.

## Preview renders vs the final render

Your in-loop previews are **cheap and fast** — EEVEE, low samples, one frame,
small resolution. They exist so you can iterate in seconds.

```python
scene.render.engine = 'BLENDER_EEVEE_NEXT'
scene.render.resolution_percentage = 50
```

The high-definition render is **not your job**. A human asks for it from the
review screen, and it runs Cycles at full samples in a dedicated pod. Do not
try to produce a final-quality render inside your run: you will spend the whole
wall clock rendering instead of designing, and the result is thrown away.

What this means practically: make `build.py` take its quality settings from the
environment, so the same script serves both.

```python
import os
preview = os.environ.get('ONKLAVE_PREVIEW', '1') == '1'
scene.render.engine = 'BLENDER_EEVEE_NEXT' if preview else 'CYCLES'
scene.cycles.samples = 64 if preview else 1024
```

## Where the outputs must go

The platform collects what it finds at these paths. They are configurable per
repo, but unless the repo says otherwise:

| Path | What |
|---|---|
| `out/previews/*.png` | Preview frames, sorted by filename. Name them `01.png`, `02.png`, … so the order is stable. |
| `out/scene.blend` | The built scene. Save it (`bpy.ops.wm.save_as_mainfile`) — it is the input to the high-definition render. Without it no final render can be offered. |

Up to 8 preview images are captured. More than that are ignored, so lead with
the frames that show the change.

## Writing a build script

Start from `scenes/example/build.py` in this repo. The shape that matters:

```python
import bpy

# ALWAYS start from a known state. A script that assumes an empty scene
# behaves differently when run twice, and `blender -b -P` keeps the startup
# file's default cube unless you clear it.
bpy.ops.wm.read_factory_settings(use_empty=True)

# ... build geometry, materials, lights, camera ...

bpy.ops.wm.save_as_mainfile(filepath='out/scene.blend')
bpy.ops.render.render(write_still=True)
```

Rules that save runs:

- **Deterministic.** Same script, same output. No `random` without a seed, no
  wall-clock, no network fetches.
- **Idempotent from factory settings.** Never depend on what a previous run
  left in the file.
- **Parametric over hard-coded.** A dimension that a human might change belongs
  in `params.json`, not buried in a literal.
- **Named objects.** `obj.name = 'CARCASS_base_600'`, not `Cube.047`. Names are
  how a reviewer and the next run find things.
- **Fail loudly.** If a required input is missing, raise. A script that silently
  renders an empty scene wastes the whole review cycle.

## What to do when the render fails

The preview command gates the PR, exactly like the test command. A failing
render escalates to a human with no PR — which is correct: there is nothing to
approve. So fix it inside your run rather than committing and hoping:

- Read the Blender stderr. `bpy` errors name the operator that failed.
- Check the camera actually frames something: an empty render is usually a
  camera or a missing-object problem, not a lighting one.
- EEVEE needs a GL stack; if it misbehaves in a way Cycles does not, say so in
  your summary rather than silently switching engines — that is a platform
  image problem and a human needs to know.
