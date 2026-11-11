"""Contract tests for the scene template.

Deliberately stdlib-only and Blender-free, so they run anywhere in under a
second: `python3 -m unittest discover -s test`.

What they CANNOT tell you is whether the render looks right — only Blender can,
and CI's render job does exactly that. These guard the contract around it: that
the inputs parse, the script compiles, and it still writes where Onklave
collects from. Those are the failures that look fine locally and break the
review loop silently.
"""

import ast
import json
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCENE = REPO / "scenes" / "example"
BUILD = SCENE / "build.py"
PARAMS = SCENE / "params.json"

# The paths Onklave collects from. Changing either means changing the repo's
# configured ONKLAVE_PREVIEW_DIR / ONKLAVE_SCENE_PATH to match — so a silent
# edit here is a silent break of the review strip.
PREVIEW_DIR = "previews"
SCENE_OUTPUT = "scene.blend"


class TestParams(unittest.TestCase):
    def test_params_parse(self):
        self.assertTrue(PARAMS.exists(), f"missing {PARAMS}")
        json.loads(PARAMS.read_text())

    def test_params_carry_every_key_the_build_reads(self):
        params = json.loads(PARAMS.read_text())
        for key in ("width_mm", "depth_mm", "height_mm", "colour_rgba"):
            self.assertIn(key, params, f"params.json is missing '{key}'")

    def test_dimensions_are_positive_numbers(self):
        params = json.loads(PARAMS.read_text())
        for key in ("width_mm", "depth_mm", "height_mm"):
            value = params[key]
            self.assertIsInstance(value, (int, float), f"{key} must be numeric")
            self.assertGreater(value, 0, f"{key} must be positive")

    def test_colour_is_rgba(self):
        colour = json.loads(PARAMS.read_text())["colour_rgba"]
        self.assertEqual(len(colour), 4, "colour_rgba must be [r, g, b, a]")
        for channel in colour:
            self.assertGreaterEqual(channel, 0.0)
            self.assertLessEqual(channel, 1.0)


class TestBuildScript(unittest.TestCase):
    def setUp(self):
        self.source = BUILD.read_text()

    def test_build_script_compiles(self):
        # Catches a syntax error without needing bpy, which only exists inside
        # Blender. A broken script otherwise fails minutes into a sandbox run.
        ast.parse(self.source)

    def test_writes_to_the_collected_output_paths(self):
        self.assertIn(
            PREVIEW_DIR,
            self.source,
            "build.py no longer references the preview directory Onklave collects from",
        )
        self.assertIn(
            SCENE_OUTPUT,
            self.source,
            "build.py no longer saves the scene a high-quality render needs",
        )

    def test_resets_to_factory_settings(self):
        # Without this the startup file's default cube lands in every render,
        # and the scene differs between machines.
        self.assertIn(
            "read_factory_settings",
            self.source,
            "build.py must start from factory settings",
        )

    def test_render_quality_comes_from_the_environment(self):
        # One script has to serve both the fast preview and the full render;
        # forking it into two files is how they drift apart.
        self.assertIn(
            "ONKLAVE_PREVIEW",
            self.source,
            "build.py must take its render quality from ONKLAVE_PREVIEW",
        )


if __name__ == "__main__":
    unittest.main()
