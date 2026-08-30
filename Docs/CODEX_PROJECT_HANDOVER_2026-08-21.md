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

## 2026-08-24 addendum — Press Shop 2126 overhead candidate

Status is **validation-only and not Steam-ready**.  The exact current release
record is in
[`ReleaseGate/CURRENT_GAMEPLAY_STATUS.md`](ReleaseGate/CURRENT_GAMEPLAY_STATUS.md)
and the hashes and receipts are in
[`ReleaseGate/VALIDATION_EVIDENCE.md`](ReleaseGate/VALIDATION_EVIDENCE.md).

Passed technical evidence:

- The isolated v006 map is
  `/Game/LineBoss/Candidates/PressShop/PressShop2126_OverheadPresentation_v006/Maps/LB_MoorcrossWorks_PressShop2126_OverheadPresentation_v006`,
  SHA-256
  `34840087dad80312c8d7d1e010489fcb277bebfee3597f831aa53d89349ef9ec`.
  Its install receipt is SHA-256
  `c0b76461edabd0a455e2a4b2bb47774e797d1817d2c38f3ca4d17054934d380c`;
  the v005 source map and every protected authority/candidate map retained its
  before/after hash.
- Exact regular PIE passed the native-player 57-route lifecycle through 11
  visual checkpoints: inbound and preparation, S04 contact, S06 transfer,
  inspection hold, explicit quality PASS, palletising and outbound.  All 146
  visual layers remained bound, the same unit identity was retained, and no
  project content or dirty-package set changed.
- Runtime legacy-press curation now exempts only the dedicated
  `ALBPressShopOverheadVisualLayerActor`, so the real overhead layers survive
  while a generic candidate actor cannot evade retirement with tags.  The
  focused indexed test passed 1/1 with two retained synthetic-world teardown
  warnings.
- Four failed live-HUD attempts (`v001`–`v004`) remain preserved.  The fourth
  produced a diagnostic 1920x1080 PNG but its receipt correctly remains FAIL:
  the screenshot-loading flush re-entered the tick after the first request was
  submitted; later re-entrant calls saw that request pending, returned false and
  made the outer path report a false refusal.  The explicit `REQUESTING_CAPTURE`
  guard is covered by 24/24 Python contract tests.
- Successor `v005` is a technical capture PASS: regular PIE, real RHI, native
  player/UMG, one player `PlaceOrder`, exactly one restricted UI screenshot
  request, natural S04 `DESCENDING` press state and unchanged map/install
  hashes.  The PNG is 1920x1080, 2,331,974 bytes, SHA-256
  `2c062279d1324432e14a6748be41e3ea5cfe7e7a77b1c4ac5bd1260ee192e624`;
  its receipt is SHA-256
  `b1f1cf716fdae5111d88588b5101f0b9da4fcecdc67acb499982213de449f660`.

Open blocker: the live `v005` frame fails the human visual gate.  An opaque
building roof/upper shell fills the camera and hides the Press Shop machinery,
contrary to the
[`true-overhead visual authority`](PressShop/PRESS_SHOP_2126_TRUE_OVERHEAD_VISUAL_AUTHORITY_v001.md).
Remove or runtime-hide that occluder in the scoped candidate lane and recapture
before visual approval.  No current evidence proves cook, package, performance,
Shipping behavior or Steam-art acceptance.

### 2026-08-24 same-session successor — roof removed, sprite visibility still open

The roof blocker above has now been corrected in native runtime code.  A saved
actor carrying `LB.PressShop.RooflessPresentation.v002` makes the runtime
envelope omit only its four department roof decks; legacy maps without that
marker still receive four.  The focused native test
`LineBoss.OneFactory.ActualPlayer.RooflessPresentationSkipsOnlyRoofDecks`
passed 1/1 and proves walls, dado, clerestory and the site slab are unchanged.

The next live-HUD run (`20260824T032352721491Z`, log suffix `v006`) technically
passed again with one native request, 146 bound layers, natural S04
`DESCENDING`, a 1920x1080 PNG and unchanged map hash.  Receipt SHA-256 is
`bcb9db8d2d3aafbd56719c6cbbe1fcca919b29523de91b3df6896999a49801fd`;
PNG SHA-256 is
`7fc7376f5ae019df5a973da347e6418686269dc1109370ecb45d217a6fd97a68`.
Human review still fails: the roof is gone, but the detailed machinery sprites
do not render in the live frame; pads, labels and a few structural strips are
visible.  The exact remaining depth/material/visibility cause was not proven
before shutdown.  Resume with a read-only regular-PIE layer/depth audit; do not
promote this frame or guess at the cause.
