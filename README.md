# Blender scene — Onklave project template

An **Onklave project template** for 3D work: your scenes are Python scripts,
agents iterate them under review, and the renders come back for you to approve.

Generate a project from this template in Onklave, or click **Use this template**
on GitHub.

## Run locally

Requires [Blender](https://www.blender.org/download/) 4.2 or newer on your PATH.
Nothing else — no `npm install`, no virtualenv.

```bash
blender -b -P scenes/example/build.py
```

That writes:

```
out/scene.blend        the built scene
out/previews/01.png    the preview image
```

Open `out/previews/01.png`. A grey box on a floor means everything works.

## Test

```bash
python3 -m unittest discover -s test -v
```

Checks the contract this repo has to keep: the parameters parse, the build
script compiles, and it writes to the documented output paths. The *real* test
is the render above — CI runs both.

## The idea: a scene is a script

**`scenes/<name>/build.py` is the scene.** The `.blend` and the images are build
outputs; they are gitignored and never committed.

That is deliberate. A `.blend` is a binary with no diff, so reviewing a change to
one means looking at a picture and guessing what moved. A script is text — it
diffs, reviews, blames and merges like any other source file, and "what changed
in this scene" has an exact answer.

```
scenes/example/
  build.py        committed — builds the scene and renders the preview
  params.json     committed — the scene's inputs
out/              gitignored — everything the build produces
```

## How Onklave runs it

This template is **not a deployable service**: there is no Dockerfile, no port
and no `onklave.yaml`, because the repo's output is renders rather than a
running app. Instead it plugs into the agent review loop:

1. An agent edits `build.py`, runs Blender in its sandbox, and **looks at the
   preview it produced** before deciding it is done.
2. It commits the script and opens a pull request.
3. Onklave re-runs the preview command **after** the commit — so the images you
   review are the images the committed source produces, not whatever the agent
   left behind mid-iteration — and shows them on the work item.
4. You approve or decline. Declining sends guidance back and the agent updates
   the same PR.
5. From the same screen you can ask for a **high-quality render** (Cycles, full
   samples), which runs separately and is published as a versioned release.

To enable that, set the repo's **preview command** in the project's repo
settings:

```
blender -b -P scenes/example/build.py
```

It is gated like a test command: if the render fails, no PR opens — a scene that
cannot render is a scene nobody can review.

### Output paths

Onklave collects whatever it finds at these paths. Override them per repo with
`ONKLAVE_PREVIEW_DIR` / `ONKLAVE_SCENE_PATH`.

| Path | Used for |
|---|---|
| `out/previews/*.png` | the review strip — first 8, sorted by filename |
| `out/scene.blend` | input to a high-quality render; no file → no render offered |

## Writing scenes

`.claude/skills/` ships 16 Blender skills an agent reads automatically. Start
with `onklave-blender-scene` — it is the execution contract, and it overrides
the other skills' instructions about driving Blender through MCP (this
repo runs Blender headless instead).

The conventions that matter, all enforced by habit rather than tooling:

- **Start from factory settings.** `bpy.ops.wm.read_factory_settings(use_empty=True)`
  — otherwise the startup file's default cube turns up in your renders.
- **Deterministic.** Same script, same image. Seed any randomness.
- **Parametric.** A dimension someone might change belongs in `params.json`.
- **Name your objects.** `CARCASS_base_600`, not `Cube.047`.
- **Fail loudly.** Raise on missing input rather than rendering an empty scene.

`scenes/example/build.py` demonstrates all of it, including taking render
quality from the environment so one script serves both the fast preview and the
final render.

## Attribution

`.claude/skills/` contains fifteen skills vendored verbatim from
[arjun988/blender-skills](https://github.com/arjun988/blender-skills) (MIT) —
see [`SKILLS_PROVENANCE.md`](SKILLS_PROVENANCE.md) and
`.claude/skills/LICENSE-vendored-skills`. The `onklave-blender-scene` skill and
the example scene are Onklave's.
