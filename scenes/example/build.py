#!/usr/bin/env python3

"""Reference Onklave scene — the shape every `build.py` follows.

Run it the way the platform does:

    blender -b -P scenes/example/build.py

Outputs (both gitignored):
    out/scene.blend        the built scene — input to a high-definition render
    out/previews/01.png    the preview frame a reviewer sees

Quality is taken from the environment so ONE script serves both the agent's
fast iteration loop and the final render. ONKLAVE_PREVIEW=1 (the default) is
EEVEE at low samples; =0 is Cycles at full samples.
"""

import json
import math
import os
from pathlib import Path

import bpy

# Paths are resolved against the repo root (the CWD the worker runs in), not
# against this file — the platform collects outputs from fixed repo-relative
# locations and a path relative to the script would land them somewhere else
# when the scene moves into a subdirectory.
ROOT = Path.cwd()
OUT = ROOT / "out"
PREVIEWS = OUT / "previews"
PARAMS = Path(__file__).with_name("params.json")

PREVIEW = os.environ.get("ONKLAVE_PREVIEW", "1") == "1"


def load_params() -> dict:
    """Scene inputs. A missing file is a bug, not a default — fail loudly."""
    if not PARAMS.exists():
        raise SystemExit(f"missing scene parameters: {PARAMS}")
    return json.loads(PARAMS.read_text())


def reset() -> None:
    """Start from a known state.

    `blender -b -P` loads the startup file, which carries a default cube, a
    light and a camera. Without this a script behaves differently depending on
    what the startup file happens to contain — and produces a stray cube in
    every render until someone notices.
    """
    bpy.ops.wm.read_factory_settings(use_empty=True)


def plinth(params: dict) -> bpy.types.Object:
    """A named box, sized from the parameters. The whole 'scene' here."""
    w = params["width_mm"] / 1000.0
    d = params["depth_mm"] / 1000.0
    h = params["height_mm"] / 1000.0

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(0.0, 0.0, h / 2.0))
    obj = bpy.context.active_object
    obj.scale = (w, d, h)
    # Named, not `Cube.001`. Names are how a reviewer and the next run find
    # things, and how a cutting list or a diff refers to them.
    obj.name = f"BOX_{params['width_mm']:.0f}x{params['depth_mm']:.0f}"
    return obj


def material(obj: bpy.types.Object, rgba: list) -> None:
    mat = bpy.data.materials.new(name=f"MAT_{obj.name}")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = tuple(rgba)
    bsdf.inputs["Roughness"].default_value = 0.45
    obj.data.materials.append(mat)


def ground() -> None:
    """A floor.

    Not decoration. Without one the object floats in void, casts no shadow,
    and the render gives a reviewer no sense of scale or contact — which is
    most of what they are looking for. Mid-grey, because a white floor next to
    a light object erases the silhouette.
    """
    bpy.ops.mesh.primitive_plane_add(size=12.0, location=(0.0, 0.0, 0.0))
    plane = bpy.context.active_object
    plane.name = "ENV_floor"
    mat = bpy.data.materials.new(name="MAT_floor")
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.22, 0.22, 0.23, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.8
    plane.data.materials.append(mat)


def world() -> None:
    """A dim ambient so unlit faces are dark grey, not pure black."""
    wrld = bpy.data.worlds.new("World")
    wrld.use_nodes = True
    bg = wrld.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.05, 0.055, 0.065, 1.0)
    bg.inputs["Strength"].default_value = 1.0
    bpy.context.scene.world = wrld


def lighting() -> None:
    """A key at an angle and a soft fill. Enough to read form, not more.

    Energies are deliberately low. The first version of this scene used 300W
    and rendered a featureless white slab: every face clipped, so the edges
    between them vanished. A render that is merely BRIGHT carries less
    information than one that is correctly exposed.
    """
    # Off the camera axis on purpose. A key sitting behind the camera lights
    # every face the camera can see equally, so adjacent faces render at the
    # same value and the form goes flat — the edges are geometrically there and
    # visually absent. Raking it round to the side is what separates them.
    bpy.ops.object.light_add(type="AREA", location=(3.2, -0.6, 2.8))
    key = bpy.context.active_object
    key.name = "LGT_key"
    key.data.energy = 90.0
    key.data.size = 1.5
    key.rotation_euler = (math.radians(58), 0.0, math.radians(78))

    bpy.ops.object.light_add(type="AREA", location=(-2.5, 1.5, 1.5))
    fill = bpy.context.active_object
    fill.name = "LGT_fill"
    fill.data.energy = 25.0
    fill.data.size = 3.0
    fill.rotation_euler = (math.radians(65), 0.0, math.radians(-120))


def camera(target: bpy.types.Object) -> None:
    bpy.ops.object.camera_add(location=(2.2, -2.6, 1.6))
    cam = bpy.context.active_object
    cam.name = "CAM_hero"
    cam.data.lens = 50.0
    # Aimed with a constraint rather than hand-computed Euler angles, so the
    # framing survives a change to the object's size.
    track = cam.constraints.new(type="TRACK_TO")
    track.target = target
    track.track_axis = "TRACK_NEGATIVE_Z"
    track.up_axis = "UP_Y"
    bpy.context.scene.camera = cam


def eevee_engine() -> str:
    """The real-time engine's id, which is not stable across Blender majors.

    4.2–4.5 call it `BLENDER_EEVEE_NEXT` (the rewrite shipped alongside the
    legacy `BLENDER_EEVEE`). 5.x dropped the legacy engine and the rewrite
    reclaimed the plain `BLENDER_EEVEE` id. Assigning the wrong one is a hard
    `TypeError`, not a fallback, so ask the enum rather than guessing: the
    platform image pins 4.5.3 but a contributor's local Blender is whatever
    they installed.
    """
    available = bpy.types.RenderSettings.bl_rna.properties["engine"].enum_items
    for candidate in ("BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"):
        if candidate in available:
            return candidate
    raise SystemExit(
        "no EEVEE engine in this Blender build; available: "
        + ", ".join(i.identifier for i in available)
    )


def render_settings() -> None:
    scene = bpy.context.scene
    scene.render.image_settings.file_format = "PNG"
    scene.render.filepath = str(PREVIEWS / "01")

    if PREVIEW:
        # Seconds, not minutes. This is the agent's feedback loop.
        scene.render.engine = eevee_engine()
        scene.render.resolution_x = 960
        scene.render.resolution_y = 540
    else:
        # The human-requested final render, run in its own pod.
        scene.render.engine = "CYCLES"
        scene.cycles.device = "CPU"
        scene.cycles.samples = 1024
        scene.cycles.use_denoising = True
        scene.render.resolution_x = 1920
        scene.render.resolution_y = 1080

    # AgX keeps highlights from clipping to white, which is what makes an
    # untouched Blender render read as "CG".
    scene.view_settings.view_transform = "AgX"


def main() -> None:
    params = load_params()
    PREVIEWS.mkdir(parents=True, exist_ok=True)

    reset()
    box = plinth(params)
    material(box, params["colour_rgba"])
    ground()
    world()
    lighting()
    camera(box)
    render_settings()

    # Save BEFORE rendering: the .blend is the input to the high-definition
    # render, and a render that fails must not also cost us the scene.
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "scene.blend"))
    bpy.ops.render.render(write_still=True)

    print(f"[scene] built {box.name} -> {PREVIEWS / '01.png'}", flush=True)


if __name__ == "__main__":
    main()
