# Template changelog

Templates are **scaffold-once** — a generated repo forks from this history and
receives nothing afterwards. This file makes a retrofit mechanical: read from
your `.onklave/template.json` version up to the current one and apply what
applies.

Check for drift:

```bash
cat .onklave/template.json                                                # yours
gh api repos/onklave/template-blender-scene/contents/.onklave/template.json \
  --jq '.content' | base64 -d                                             # current
```

---

## 1.0.0 — 2026-11-11

Initial template.

- **A scene is a script.** `scenes/<name>/build.py` is the committed, reviewable
  unit; `out/` (the `.blend` and the rendered images) is build output and is
  gitignored. A binary has no diff, so reviewing a change to one means guessing.
- **`scenes/example/`** — a working reference scene: parametric from
  `params.json`, factory-settings reset, named objects, and render quality taken
  from `ONKLAVE_PREVIEW` so one script serves both the fast preview and the
  full-quality render.
- **`.claude/skills/`** — 16 Blender skills. Fifteen vendored verbatim from
  `arjun988/blender-skills` (MIT, see `SKILLS_PROVENANCE.md`); the sixteenth,
  `onklave-blender-scene`, is the execution contract and overrides their
  instructions about driving Blender through MCP.
- **`.onklave/rules.md`** — rules-as-code the cloud worker reads at clone time.
- **CI** — a Blender-free contract job plus a render job that installs a pinned,
  checksum-verified Blender and asserts the output FILES exist (Blender can
  crash mid-render and still exit 0).
