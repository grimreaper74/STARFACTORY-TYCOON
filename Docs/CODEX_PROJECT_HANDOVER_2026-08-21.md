# Codex project handover - 2026-08-21

You are the surfacing and 2D-art partner on **Line Boss: Car Factory**.
This is the complete orientation: what the project is, where it stands,
what your lane is, and which documents are authoritative for what.

## The project in one paragraph

Line Boss is an Unreal 5.8 management sim. The player runs **Moorcross
Works**, a fully robotic lights-out car plant building one vehicle, the
electric **Cairnwell 2040**, through the real journey: coils arrive by
lorry, press stamps panels, body weld joins them, paint dips and sprays
and cures, assembly marries the battery and powertrain and fits the
car out, dispatch sends finished vehicles away. Four separate shop
buildings on one landscaped site; management camera; the whole plant is
saved content in the map, present on open. Steam fee is paid and the
page is awaiting verification (~late September); current work is
wishlist-page readiness.

## Hard rules that are never negotiable

- **Clean room.** The game has no connection to any real car company.
  No real brands, badges, model names or liveries anywhere - in art,
  filenames, decals, capsule text, anything.
- **No people.** Moorcross is lights-out robotic. No operators, PPE,
  break rooms, walkway markings for humans, or human-scale furniture
  dressing. Signage speaks machine-to-machine (status pillars, line
  boards, andon).
- **No Meshy-provenance assets.** Bootstrap guards reject the word
  'Meshy' in package paths and certain legacy labels. Never route
  anything through Meshy or name anything after it.
- **Brand palette** is the Cairnwell scheme used across every machine:
  emerald green (0.028/0.155/0.116), foundry charcoal, machined steel,
  warm white/cream, safety yellow, sparing signal red. The owner holds
  official design-pack sheets that define this; BRAND_IDENTITY_AUTHORITY
  in Docs is the written authority.
- **Realistic industrial, never low-poly stylised.** Chamfered edges,
  true proportions, modelled mechanisms. The press trains are the bar.

## Where the project stands tonight

- All four shops are rebuilt as coherent process lines and the site
  around them exists (fences, yards, roads, vegetation, transporters).
- **Every machine mesh in the game is high-detail.** Claude rebuilt the
  full paint (33), assembly (32 incl. audited pieces), weld (26) and
  intake kits over the last two days; your earlier 50-mesh uplift wave
  is in. Same drop-in contract throughout.
- **Placement QA is green**: 3,679 placed machine actors, zero
  interpenetrations, zero floaters/sinkers, verified by tool
  (Tools/Diagnostics/placement_qa.py), not by eye.
- Player UI v2 plus seven v2.1 refinements are live (rate graphs,
  alert memory, tooltips, camera bookmarks, bottleneck tag, orders
  dropdown, day summary).
- Tonight the owner removed the decorative light-gantry arches and
  added sweeping inspection lasers (ScanKit) at the EOL arch, vision
  gate and quality light tunnel.
- Suite state: 288 automation tests, 0 failed - and that gate runs
  before every commit. Keep it that way.

## Your lane

Geometry is Claude's; **surfacing, colourways, decals, LODs, texture
sets and Steam capsule art are yours**, layered over the locked
geometry without breaking the drop-in contract:

- **Same package path, same pivots, same scale, same material slot
  names, footprint within ~5%.** Re-imports go over the original asset
  so 3,679 placements survive untouched.
- Texture sets: per semantic slot (CairnwellGreen, FoundryCharcoal,
  MachinedSteel, WarmWhite, SafetyYellow, SignalRed, Tire, Glass),
  BaseColor/Normal/Roughness, 2048, delivered under your workspace's
  SourceAssets/Candidate/DetailUplift_v001/Textures/<MeshName>/.
- Your current work-day batch (colourways, capsules, textures for 14
  staged meshes, LODs, decal atlas) is **held at your own QA gate** -
  Final_Asset_Batch_QA_v001.json says FAIL. Fix to PASS before any of
  it is integrated; nothing gets pulled while the manifest fails.
- **One package of yours is permanently dropped**:
  LB_WeldRobot_SharedBase_LOD0_v001. Its geometry differs from the
  validated runtime art and it once overwrote the contract mesh
  (frozen bounds 90x66x186). Do not redeliver it; the shared base is
  not yours to touch.
- Delivery flow: stage in your workspace, report done; integration
  into the game project is done from this side with a scoped include
  list, never a blanket import.

## The documents - what is authoritative for what

Root `Docs/`:

- **PROJECT_HANDOFF.md / NEW_CHAT_HANDOVER_2026-08-03.md** - deep
  project history. Background only; superseded on current state by
  this file and the OneFactory day reports.
- **BRAND_IDENTITY_AUTHORITY.md** - the brand: names, palette,
  typography intent. Authoritative for anything player-facing or
  Steam-facing you draw.
- **LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md** - the visual bar for
  factory art (density, materials, lighting intent).
- **MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md** - how machine guarding
  and enclosures are designed.
- **VISUAL_ASSET_LEDGER_v001.md / AssetCatalog/** - what assets exist
  and where they came from.
- **UNREAL_PROJECT_BOUNDARY.md / UNREAL_MIGRATION_MANIFEST.md** -
  what belongs inside the Unreal project versus source assets.
- **VENDOR_ASSET_AUDIT_2026-08-01.md** - the owned Fab packs audit
  (seven packs incl. the 869-mesh factory collection).
- Shop folders (PressShop/, BodyShop/, PaintShop/, AssemblyShop/) and
  the various *_AUTHORITY / *_IMPORT_LANE docs - per-subsystem detail
  from the build-out; consult when touching that subsystem.

`Docs/OneFactory/` (the live game - most current material):

- **DAY_REPORT_2026-08-20_EVENING.md** - the latest full status
  report. Read this first after this handover.
- **SESSION_HANDOVER / UNATTENDED_SESSION docs** - dated working
  handovers; newer date wins.
- **PLANT_LAYOUT_PLAN_2026-08-17.md and SITE_PLAN_2026-08-19.md
  (+ .svg)** - where everything on the site and in the shops is and
  why. Authoritative for placement questions.
- **UI_RESEARCH_2026-08-20.md / UI_V2_DESIGN_2026-08-20.md** - the
  UI's locked grammar and one-status-model rule. Authoritative for
  any HUD-adjacent art (colours are Okabe-Ito tokens; do not invent
  new status colours in capsules or mockups).
- **CODEX_BRIEF_2026-08-19.md** - your earlier brief; still valid
  where it does not conflict with this file.
- **ONE_FACTORY_*_V001 docs** - runtime architecture (production
  flow, coordinator, save system, shell). Background for you.
- **CAIRNWELL_2040_* docs** - the vehicle meshes' import/recovery
  history; the BodyAuthority_v005 LOD exports are the current vehicle
  source you texture against.
- **GAMEPLAY_RESEARCH / GAMEPLAY_PARITY docs** - design context.
- **ReleaseGate/, Captures/** - evidence trails from past gates.

Also: **GAME_STANDARD_ROADMAP_2026-08-17.md** exists as a gap
inventory only - its ordering was overruled by the owner (plant
before HUD/gameplay); do not treat it as a plan.

## Working rhythm

Batch your work; self-check with previews; report a batch done only
when your own QA passes; honesty about what is unverified beats a
smooth report. The owner delegates decisions - decide, record in your
worklog, proceed - but the hard rules above are his and fixed. When a
delivery lands, say exactly which files changed so integration can be
scoped; blanket refreshes are how we corrupted a mesh this week, and
they are gone for good.
