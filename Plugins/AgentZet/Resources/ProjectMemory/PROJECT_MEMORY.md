# Project memory — STAR FACTORY TYCOON

You are working inside ONE specific game project. These facts are true and
do not need rediscovering. Trust them; verify anything not listed here.

## What the game is

STAR FACTORY TYCOON: a PC factory-management game about manufacturing
compact SPACECRAFT, built in Unreal Engine 5.8, C++ only (no Blueprint
gameplay logic). The player takes a contract, builds a production line,
manufactures and assembles a craft, delivers it, then upgrades.

The project pivoted from a CAR factory game. Anything you find that talks
about cars, Cairnwell, or press/weld/paint shops is HISTORY, not the
direction. Do not treat it as a guide for new work.

## Names that look wrong but are correct

The module, target and .uproject are called `LineBossCarFactory`. This is
DELIBERATE and must never be "fixed": that name is written into ~17,600
asset files, and the project has no redirectors, so renaming it breaks
everything for no player-visible gain. The player-facing title lives in
`Config/DefaultGame.ini`.

## Where things are

- Gameplay C++: `Source/LineBossCarFactory/` — flat, every type prefixed `LB`.
- Editor Python: `Scripts/*.py` (run inside Unreal, import `unreal`).
- Blender scripts: `Tools/*.py` (run in Blender, NOT in Unreal).
- One-shot lanes: `Scripts/run_*.ps1` and `Scripts/*_v00N.ps1`.
- Docs and rules: `Docs/`. Evidence receipts: `Saved/Audits/`.
- Generated 3D assets: `SourceAssets/Spacecraft/TrellisGenerated_v001/<name>/`.

`Content/` and `SourceAssets/` are NOT in git (too large). A change to
content is invisible to `git status`; record it with a receipt instead.

## Rules you must follow

1. **Never claim success you have not verified.** "It compiled", "the asset
   exists", "the test passed" require evidence you actually saw in a tool
   result. If a tool failed, say so plainly and stop.
2. **Version files, never edit in place.** A superseded lane becomes
   `_v002`; the old one stays as evidence. Same for docs and scripts.
3. **Fail closed.** If a precondition is missing, refuse and explain. Do
   not improvise a workaround that weakens a guard.
4. **One tool per response**, then read the result before the next step.
5. **Never invent a tool name.** If nothing fits, say so in plain text or
   call `attempt_completion`.

## Art and asset rules

- Generated geometry (TRELLIS) is ALLOWED as a source, but every asset
  needs a record: pinned source, sha256, declared size, and measurement.
- Take GEOMETRY from the generator; author MATERIALS in Unreal. Do not
  rely on generated texture maps.
- Generated models are unit-scale: they MUST be scaled to a declared
  real-world size at import. `import_generated_asset` does this and
  verifies it — never bypass that step.
- Never put generated content under a path containing `Meshy`,
  `ExternalGenerated` or `OriginalHighPoly`: runtime guards silently
  reject assets there.
- Never bake text into a texture or icon; the game ships translated.

## The look

Clean futuristic industrial, not grimy sci-fi. Pale industrial surfaces,
graphite machinery, strong clean lighting, blue/white indicators. The
governing rule: no world surface is both bright AND saturated, and only
the machinery carries hue — the interface is hue-free, with red `#EC3013`
reserved for refusal.

## How the factory works (design, settled)

- The production line is ONE repeatable fitting-station type, placed as
  many times as the player likes along a track. Stations FIT parts onto
  the craft; they never fabricate. Fabrication happens in sub-assembly
  cells off the line.
- Parts arrive beside each station on a kit dolly — one per station per
  craft — delivered and handled by DRONES. Nothing on this floor is
  handled by people, so never model human ergonomics into equipment.
- A gantry crane pulses the craft between stations. There is no conveyor.
- Drones are the co-stars: every station hosts them and the factory must
  never look bare.
