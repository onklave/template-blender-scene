# Skills provenance

Fifteen of the sixteen skills in `.claude/skills/` are vendored verbatim from a
third-party repository. Recorded here so the licence position is a stated fact
and a re-sync is a reviewable diff.

| | |
|---|---|
| **Upstream** | https://github.com/arjun988/blender-skills |
| **Commit** | `904f095d8f36a6e72adaebb08d07f884a074743d` |
| **Vendored** | 2026-11-11 |
| **Licence** | MIT — `.claude/skills/LICENSE-vendored-skills` |
| **Content** | Markdown only; no executable code. |

## Vendored

```
archviz                 geometry-nodes          rendering
asset-optimization      hard-surface            scene-assembly
blender-director        lighting                texture-workflow
blender-modeler         materials               uv-workflow
camera-cinematography   procedural-modeling     realistic-style
```

Upstream ships 95 skills; these fifteen are the ones that bear on building and
rendering a scene. The rest are game-genre and art-style guides. They cost
nothing to add — every skill's name and description loads into the agent's
context, so the omission is about keeping routing sharp, not about licensing.

## Ours

`onklave-blender-scene` is written by Onklave and is MIT like the rest of this
template, so a generated project owns it outright.

## Verbatim is deliberate

No vendored file is edited. The upstream skills tell an agent to execute "via
MCP", which is **not** how this template runs — but that correction lives in
`onklave-blender-scene`, which the director routes through first, rather than in
fifteen hand-patched files that would turn the next upstream sync into a merge
conflict.

## Re-syncing

```bash
git clone --depth 1 https://github.com/arjun988/blender-skills.git /tmp/bs
# copy the fifteen directories above from /tmp/bs/.claude/skills/ over
# .claude/skills/, then update the commit SHA in this file.
```

Review the diff: these files are instructions an agent follows, so an upstream
change is a change to agent behaviour.
