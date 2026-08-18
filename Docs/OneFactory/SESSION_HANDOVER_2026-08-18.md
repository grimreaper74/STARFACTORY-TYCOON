# Session handover — 2026-08-18

Written at the point where autonomous progress stops being useful: the plant's
reusable work is done, and everything remaining needs authored content or an owner
decision.

## Where the plant actually is

Goal in force (owner, 2026-08-17): *"we need to get the plant running fully before we
put the hud and gameplay in"* — i.e. opening
`/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001` should
show a complete works with no console commands.

| Shop | Layout | Roof trusses | Lit gantries | Density (instances) |
| --- | --- | --- | --- | --- |
| Press | Codex's, transplanted | 12 (Codex's) | own crane/structure | **5,089 mesh + 144 light** |
| Body/weld | Re-laid east-opening | 24 | 18 | 597 |
| Paint | 8 stations, one line | 25 | 8 | 119 |
| Assembly | 24 stations, two runs | 42 | 24 | 95 |

**Press meets the goal.** Its content is saved in the map and inspectable with no
commissioned factory. The other three have structure but sparse floors.

Verified state: suite **278/278** (0 failed, 0 notRun), factory commissions
(`BOOTSTRAP_READY`, `BUILD_WHOLE_FACTORY ok=1`), working tree clean, and Codex's
reference map byte-identical to 14 August throughout.

## What landed this session

1. **Press transplanted** — `Tools/transplant_press_shop.py` replaces the lossy
   manifest pipeline. Reads the reference level live to preserve per-slot materials and
   **144 lights** the manifest could never carry. Excludes 106 CameraActors, 10
   stretched robot-arm actors and anything with Meshy provenance.
2. **Weld re-laid** — the 18 positions now run an east-opening serpentine, so the BIW
   handoff sits next to paint instead of 170 m of backhaul away.
3. **103 roof trusses and 50 lit gantries** across weld, paint and assembly, from two
   assets already in the project.
4. **Camera fixes** — the view target no longer sticks to a dev camera; the zoom cap
   went 30,000 → 70,000 cm; framing falls back to authored bays so the plant is
   inspectable without a commissioned factory.
5. **Sun and sky** saved into the map. The exposure and lighting authorities were
   deliberately left untouched.

## Decisions needed from the owner

1. **Cube walls.** There is no authored wall kit anywhere — not in the vendor pack, not
   in Codex's reference. Press's own walls are 44 scaled `Cube` actors and it still
   reads well, because its ~2,800 authored *machine* pieces carry it. So: author a small
   wall kit (cladding panel, eaves, corner — three Blender meshes reused across three
   shops), or accept cube shells consistent with press and spend the effort on density?
   This cuts against the standing "no engine primitives for environment" instruction,
   which is why it is not mine to decide.
2. **Cairnwell 2040 powertrain** — electric, hybrid or ICE? Decides a battery pack
   versus a fuel tank, assembly station 11's content, and what the powertrain dress line
   dresses.
3. **Fab download** — Megascans ground surfaces and Megaplants vegetation are free under
   the Fab Standard License but need the owner's own account. The project has no grass,
   asphalt or vegetation asset of any kind. This is the only genuine gap that cannot be
   worked around.

## Next work, in order

1. **Density** — the largest gap by far, and the thing that makes press read well.
   Weld 28, paint 22, assembly 33 machines on the missing list in
   `PLANT_LAYOUT_PLAN_2026-08-17.md`, each with a proposed `SM_LB_*` name and an
   authoring spec. Recommend authoring **one** machine first and showing it before
   committing to eighty.
2. Mezzanine and marshalling racks — vendor equivalents read wrongly.
3. Paint's process build-out — its 22,000 cm bay holds 11,800 cm of stations in the
   western half, so it reads as half a shop until the ED line and booths are laid out.
4. Wall shell, per decision 1.
5. Then, and only then, the HUD and gameplay work in
   `GAME_STANDARD_ROADMAP_2026-08-17.md` (92 measured gaps), and the site, which
   regenerates from `Tools/build_site_authored.py`.

## Lessons that cost time, recorded so they are not repeated

- **Bounds are not appearance.** Placed 282 fabric actors from measured dimensions;
  they read as a blue ribbon, brackets and fencing. Reverted all 282. Render a contact
  sheet before designing a layout around any asset.
- **Bounds are not geometry.** `SM_FrontWall01` measures 454 x 2357 x 3032 but contains
  a small lattice panel, not a 30 m wall. A large bounding box can hold sparse
  framework.
- **Read asset paths, do not compose them.** An invented truss path cost a run; four
  paths in the plant plan turned out not to exist.
- **A static layout that clears can still be wrong.** The 1800 cm weld pitch satisfied
  the 1700 footprint but the player's "move station 1 m" action consumed all the slack
  and the validator refused it. Check the interactive envelope, not just the placement
  envelope.
- **Never judge density from a capture missing the content commands.** Several turns of
  work went the wrong way because tours omitted `RestoredShop` and `Dressing`.
- **Read the HUD text in the frame before theorising.** Three identical captures were
  diagnosed as geometry, then as a HUD bug; the frame said "no commissioned factory yet"
  the whole time.
- **Roof structure is invisible from overhead by design** — above the 900 cm cutaway
  threshold. Verify it at a low pitch such as `<Shop>@0.14~8`.

## Rollback

- `E:\LineBossValidationOutput\MapBackups\` holds `pre-site`, `with-site` and
  `pre-transplant` copies of the Moorcross map.
- `Content/` and `SourceAssets/` are **not in git** and have no other backup. Copying
  both to E: (about 63 GB of a spare terabyte) remains the single most valuable
  housekeeping job and was offered but not yet authorised.
