# Repository Rules

Rules-as-code for Onklave agents working in this repo. The cloud worker reads
this file at clone time and instructs the agent to follow it.

These are engineering conventions, **subordinate to the project rule book and
platform policy**: where they conflict, the stricter rule wins, and nothing here
grants tools, scopes or paths.

---

## The scene is the script

1. **Never commit build output.** No `.blend`, no rendered image, nothing under
   `out/`. The scene is `scenes/<name>/build.py`; everything Blender produces
   from it is regenerated on demand. A binary in git cannot be reviewed and
   punishes every clone forever.

2. **Edit the script, never a saved `.blend`.** If you find yourself wanting to
   tweak the file Blender wrote, the change belongs in the script that wrote it.

3. **Look at what you made before you finish.** Run the build and Read the
   PNG it produced. Blender exiting 0 means it did not crash — it says nothing
   about whether the camera is inside a wall, the frame is black, or the
   material reads as grey plastic. A run that commits without looking is a run
   that wastes the reviewer's turn.

## Writing a build script

4. **Start from factory settings** — `bpy.ops.wm.read_factory_settings(use_empty=True)`.
   Without it the startup file's default cube appears in renders and the script
   behaves differently on a different machine.

5. **Deterministic.** Same script, same image. Seed any randomness; no wall
   clock, no network fetches during a build.

6. **Parametric over hard-coded.** A dimension a human might change goes in
   `params.json`, not a literal buried in geometry code.

7. **Name every object** — `CARCASS_base_600`, not `Cube.047`. Names are how a
   reviewer, a diff, and the next run refer to things.

8. **Fail loudly.** Raise on missing or invalid input. A script that silently
   renders an empty scene burns a whole review cycle before anyone notices.

## Renders

9. **Preview renders stay cheap** — EEVEE, low samples, reduced resolution.
   They are a feedback loop, not a deliverable.

10. **Do not produce final-quality renders inside a run.** Full-sample Cycles is
    a separate, human-requested step. Attempting it in-run spends the wall clock
    rendering instead of designing, and the output is discarded.

11. **Take quality from the environment** (`ONKLAVE_PREVIEW`) so one script
    serves both paths. Never fork a scene into `build.py` and `build_final.py`.

## Scope

12. **One scene per directory** under `scenes/`. A new scene is a new directory,
    not a branch in an existing script.

13. **Do not add dependencies.** This repo runs on Blender's bundled Python and
    the standard library. If something genuinely needs a package, raise it for a
    human rather than adding a requirements file the sandbox will not install.
