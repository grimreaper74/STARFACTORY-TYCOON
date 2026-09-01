# Overnight run, 2026-09-01 — the game becomes packaged-playable

The mandate for the night: "keep going to get it finished" — stranger
journey, crane on camera, save/reload soak, packaged build as the
capstone. This doc is the honest ledger of what happened, with the
receipts named. Eight package cycles were built; the archive at
`Builds/Overnight_2026_09_01` holds the final one.

## The status claim, in release-gate vocabulary

**Packaged playable** for the scripted stranger journey INCLUDING a
mid-session save/load: in the archived Development package, the journey
built the line, accepted a contract, produced a Scout at 4x, delivered
it, was paid, unlocked conveyor belts, saved mid-production, rolled
back mid-session via load, ran the restored line to a SECOND delivery,
and exited cleanly. Evidence: `Saved/Audits/PackagedJourney_2026_09_01_*`
(screenshots + logs per run) and the w6_* capture set. The launch
itself was never caught in a timed frame (the ~12 s departure window
drifts between runs); the owner films that live at 1x anyway.

**Validation-only** beyond that scripted path — nobody has free-played
the package end-to-end by hand yet.

## What broke and what fixed it (in order found)

1. **Every cook died on an engine assert** ("index 2 into an array of
   size 1"). Five runs of misdirection — the log's last line blamed an
   innocent material. Config bisection + single-package cooks named the
   real culprits: the two site lane-paint MIs, parented to the car-era
   FrontEnd painted-concrete master whose five texture samplers all
   went null when its vendor textures were deleted. New texture-free
   site-paint master; MIs re-parented. Full receipt:
   Docs/COOK_CRASH_SITE_PAINT_MI_v001.md.
2. **~280 materials rendered as grey default in the package only** —
   Interchange glTF MICs share the engine plugin's M_Default base,
   which carries no usage flags and cannot be edited in place (v001 of
   the fix accidentally wrote to the engine install; v002 undid that).
   All re-parented onto a project-owned duplicate with ISM+Nanite
   flags (fix_nanite_usage_flags_v001-v003; v003 is the registry-wide
   sweep to re-run after any future glTF import).
3. **Drone crews and pallet loads were placeholder blocks in the
   package** — DroneBatch_v001 and PalletLoads_v001 are soft-loaded by
   path and were never in DirectoriesToAlwaysCook.
4. **The site kit (floor/walls/runway deck) was dead in every build**
   — the Meshy blockout gate default-denied every Site.* key, though
   the kit is procedural Blender work the owner asked for. Allowlisted;
   this also returned the runway part count to its original ledger'd 85
   (the morning's 107 re-pin had measured the gate-broken fallback).
5. **A factory buying grid power could not save** — the power
   validator treated draw > owned supply as corruption, though the
   mains feed is a legal billed state. Every pre-power-plant player
   was locked out of saving. ValidateSnapshot now takes the feed.
6. **Two crash classes on mid-session load**, both stale-pointer:
   the departure animation's raw component caches (now TWeakObjectPtr
   + a flush on load), and six Scout mesh caches missing UPROPERTY so
   GC purged the meshes out from under the latch (now UPROPERTY, plus
   the four Cargo caches with the same latent hole).
7. **The site skyline was restorable, not lost** — the 2026-08-28
   car-era archive moved the bought Factory Environment Collection out
   of Content; its own receipt predicted the runtime-string-load blind
   spot. The five SM_Background* props and their material chain are
   restored from ArchivedCarEraContent and /Game/Meshes is cooked.
8. **The owner's commissioned Meshy site scenery was self-blocked** —
   LoadOurs returned null under the blanket blockout, and the whole
   outdoor build (fence, gate, yard, masts) gated on it. Unblocked
   after the owner re-opened the Meshy lane; the blockout still stands
   for the station bodies it was aimed at.

## Also shipped tonight

- **Sentence-case sweep** across ~250 player-facing strings (six
  delegated agents, all output verified); headers keep their caps.
- **LB.Spacecraft.After <seconds> <command>** — deferred exec for
  scripted journeys (everything in -ExecCmds fires at frame 0), plus
  Enter learned an optional delay and fire-time resolution.
- **Our own MCP toolset** (owner: "make your own mcp commands for the
  bridge"): new editor module `LineBossCarFactoryEditor` registers
  `LineBossCarFactoryEditor.LBSpacecraftDevToolset` with two tools,
  verified live over the wire — GetSpacecraftFactoryStatus (the whole
  sim as one JSON document) and RunSpacecraftConsoleCommand. VibeUE
  remains an unmodified upstream clone.
- Video shot list corrected (Docs/VIDEO_SHOT_LIST_v001.md) — no
  paint-transform promise, runway-view launch, no captured game audio
  exists to rely on.

## Standing state

- Suite: 135/135 green across five runs (latest:
  Saved/Automation/McpScenery_2026_09_01).
- Meshy credits refresh ~the 4th; the skyline no longer needs them.
  Fab re-downloads and free packs are owner-sanctioned.
- Stray find: a staged LineBossCarFactory package sits inside
  `C:\Program Files\Epic Games\UE_5.8\$archive\Windows` — an
  accidental archive target from some earlier run; delete when
  convenient.

## Honest gaps / next

- The scenery BUILDS in the final package (its log line "LBSiteScenery
  dressed: our props on the plot, the bought kit in the district"
  fires, and no SkipPackage warnings remain) — but the default site
  camera frames the building cluster tightly, so no timed capture
  shows the fence, yard, masts or district towers. The mixed
  bought-kit/white-futuristic read still needs a human pan-and-zoom
  look; judge it on your first live session before anything else.
- Launch-on-camera: film live at 1x rather than chasing timed frames.
- Audit backlog unchanged: badge refresh caching, min-fit enlarge
  clamp, spray-rig leftovers, StationLiftRamRestZ map leak, flame-cone
  scale.
- Free-play the package by hand; the scripted journey is not a person.
