# Star Factory Tycoon documentation index

This is the starting point for current implementation and release status.
The standing-rules section below is current as of **2026-08-30**; the
release-status entries are a snapshot of the working tree on
**2026-08-11**, and being listed here does not turn a source asset,
passing unit test, or editor preview into a packaged-playable feature.

The game was named **STAR FACTORY TYCOON** on 2026-08-28. *Line Boss* is
the working title and now prior art; the module, target and `.uproject`
keep the `LineBossCarFactory` spelling deliberately (see `CLAUDE.md`).

## Standing rules

**Read first:** [Spacecraft pivot authority](SPACECRAFT_PIVOT_AUTHORITY_v001.md)
— what the game is now (a 2.5D spacecraft factory), the reversed
generated-asset policy, and what the pivot does *not* change. **Its
brand/colour section is superseded:** a palette was adopted on
2026-08-29 (`BRAND_PALETTE_ADOPTION_v001.md`), so art is graded to it
rather than picked by eye. The wordmark is still open; the palette holds. It wins over any older doc about what the game is or what
art is allowed; older release-gate and evidence rules still stand.

Supporting: [Visual standard v002](LINE_BOSS_FACTORY_VISUAL_STANDARD_v002.md)
and [Meshy provenance reversal plan](MESHY_PROVENANCE_REVERSAL_PLAN_v001.md)
(the code guards are still live and must be lifted together).

**Where models come from, as of 2026-08-30.** Meshy-sourced models are
switched off in the game behind one flag and stand as blockouts until
replaced — see the [blockout punch-list](MESHY_BLOCKOUT_PUNCHLIST_v001.md)
for exactly what is and is not affected, including the same-day
correction where a folder-name sweep wrongly caught five things that were
never Meshy. New models are commissioned through **Claude Design**, and
every brief carries the rules the Scout commission proved necessary
([Scout craft design](SCOUT_CRAFT_DESIGN_v001.md)): agree a **2D concept
first**, state dimensions as **measurements**, and state how the
**export must be structured**. Older docs that describe commissioning
"through the Meshy lane" describe the previous route, not the current one.

Superseded, retained as evidence: `BRAND_IDENTITY_AUTHORITY.md`,
`LINE_BOSS_FACTORY_VISUAL_STANDARD_v001.md`,
`CODEX_PROJECT_HANDOVER_2026-08-21.md`.

## Spacecraft era — working documents

Everything written since the 2026-08-24 pivot. None of it overrides the
release gate or the pivot authority; it is where the current work is
described. (Docs not listed anywhere in this index are car-era history.)

**What we are building**

- [Vertical slice contract](SPACECRAFT_VERTICAL_SLICE_CONTRACT_v001.md) —
  the agreed slice: one factory, one craft, one contract, whole loop.
- [Slice goal](SPACECRAFT_SLICE_GOAL_v001.md) — the standing goal an
  autonomous run works toward.
- [Content catalogue](SPACECRAFT_CONTENT_CATALOGUE_v001.md) — the
  full-game scale plan (~30 buildings), explicitly beyond the slice.
- [Parts catalogue — the hundred parts](SPACECRAFT_PARTS_CATALOGUE_v001.md)
  — the owner's "same number of parts as car manufacturer" target, with
  their count measured (117 categories / 99 concrete) and ours listed
  out. Planned; nothing implemented.
- [Scout-01 parts list](SCOUT01_PARTS_LIST_v001.md) — every physical item
  in the shipped production chain; doubles as the model shopping list.
- [Station parts allocation](STATION_PARTS_ALLOCATION_DESIGN_v001.md) —
  planned, not implemented.

**Design and calibration**

- [Production line model](PRODUCTION_LINE_MODEL_v001.md) — SETTLED
  (owner 2026-08-28): military-aircraft PULSE mechanics with Car
  Manufacture interaction. Rules out a continuously-moving line, and
  names what to take from aircraft plants later.
- [Contract design ideas](CONTRACT_DESIGN_IDEAS_v001.md)
- [Economy calibration from Production Line](ECONOMY_CALIBRATION_PRODUCTION_LINE_v001.md)
  — read-only mine of the installed game's shipped CSVs.
- [Conveyors, scale and playability](CONVEYORS_SCALE_PLAYABILITY_RESEARCH_v001.md)
- [How Car Manufacture builds stations and conveyors](CONVEYOR_LINE_CONSTRUCTION_RESEARCH_v001.md)
- [Car Manufacture mechanics notes](CAR_MANUFACTURE_MECHANICS_NOTES_v001.md)

> The three reference documents above are **mechanics and naming
> reference only**. Those games' assets are off limits, and nothing in
> them is a licence to copy content.

**Presentation, input and audio**

- [Building generation prompt v002](MESHY_BUILDING_PROMPT_v002.md) —
  the FUTURISTIC language the owner chose, with scale anchors expressed
  in it. Carries the three constraints that keep being violated and the
  full intake sequence. (`_v001` is the superseded grounded-industrial
  version, kept as evidence.)
- [Site scenery audit](SITE_SCENERY_AUDIT_v001.md) — what the project
  already owns for a full site map (a 759-piece industrial kit, measured),
  what was built from it, and the only gaps worth shopping for.
- [Surface material authority](SURFACE_MATERIAL_AUTHORITY_v001.md) —
  STANDING RULE (owner 2026-08-28): Meshy gives geometry, Unreal gives
  surfaces. One master, one palette, and the two failures that turn a
  material black.
- [Visual asset ledger](VISUAL_ASSET_LEDGER_v001.md) — visual authority,
  tracked separately from functional authority.
- [Meshy blockout punch-list](MESHY_BLOCKOUT_PUNCHLIST_v001.md) — **read
  before commissioning any replacement art.** Meshy-sourced models are
  switched off behind one flag (`bBlockoutMeshyContent`) and stand as
  blockouts until Design replaces them; this names exactly what is a
  blockout and what is not. Carries a same-day **correction**: the first
  sweep classified by content-path folder name and wrongly caught five
  things that were never Meshy, including a paint booth that was already
  correct. `Candidates/` means "not yet promoted", not "from Meshy".
- [Scout craft design](SCOUT_CRAFT_DESIGN_v001.md) — the chosen Scout
  silhouette (concept Option 3) and why it was chosen against the game's
  needs rather than on looks. Records the two failures every model brief
  must now carry: state dimensions as **measurements**, and state how the
  **export must be structured** (six named objects, not 1,741 loose ones).
- [Site hub scene v006](SITE_HUB_SCENE_v006.md) — the live site picture,
  and the lesson that a picture asked for as "the same but sharper" is
  still a new picture until its hotspots are measured again.
- [Input map and the settings stack](INPUT_MAP_CM_ADOPTION_v001.md)
- [Sound spec](SOUND_SPEC_v001.md) — the audio shopping list in wiring
  order. The game is otherwise silent.
- [Drone rotor audio](DRONE_ROTOR_AUDIO_v001.md) — the rotor-speed model
  that drives both the blade spin and the pitch, and the synthesised
  placeholder loop. Validation-only; nobody has heard it.
- [Localization readiness](LOCALIZATION_READINESS_v001.md) — the standing
  translation mandate and the outstanding debt.

**Session records and findings**

- [New chat handover, 2026-08-30](NEW_CHAT_HANDOVER_2026-08-30.md) —
  **start here after a context break.** Where the project stands, which
  packaged build to trust (v009, not v008), why two tests fail on
  purpose, and the asset-classification mistake that must not be
  repeated.

- [Autonomous night, 2026-08-27](AUTONOMOUS_NIGHT_2026-08-27_v001.md)
- [Autonomous night, 2026-08-27, second session](AUTONOMOUS_NIGHT_2026-08-27_v002.md)
  — the economic arc runs unattended (import, earn fabrication,
  fabricate), six real logistics bugs found by starvation dumps and
  fixed, and the make-vs-buy floor constraint measured.
- [Re-audit, 2026-08-27](REAUDIT_2026-08-27_v001.md) — reads its own
  self-bias caveat first, and should.
- [The headless `-game` "stall" — retracted](HEADLESS_GAME_RUN_STALL_v001.md)
  — there was no stall. `-ExecCmds` splits on **commas, not
  semicolons**, so a semicolon-joined command list silently runs nothing
  and never quits. Worth reading for the correct invocation, and for how
  an absence of log output got mistaken for a hang.
- [Sighted unattended runs](SIGHTED_UNATTENDED_RUNS_v001.md) — the
  screenshot loop that gives an unattended run eyes, and its traps:
  UI must be requested, captures armed at whole multiples of 5 s land
  deterministically on panel-rebuild frames (a one-frame artifact that
  two captures in a row "confirmed" as a standing garble), and one
  screenshot is one frame — burst before diagnosing.
- [What the automated player measured](AUTOPLAY_ECONOMY_MEASUREMENT_v001.md)
  — the soak that first proved the core loop closes from the console,
  and a **retraction**: the 68.4% import margin it reported does not
  survive a direct check (one craft's six components cost 119,600 cr
  against 150,000 cr revenue — the documented ~20%). Records what the
  player-facing economy was proven to do correctly, an unexplained
  spend gap bounded to the dev supply path, and why `SetupEconomy` must
  not be re-run to restock: it is idempotent about the dock and racks,
  **not** about the machines.
- [Packaged journey receipt v003](SPACECRAFT_PACKAGED_JOURNEY_v003.md) — the
  first packaged journey fed **through the supply chain** (dock → rack →
  hauler → stockpile) rather than by `Deposit` into station stores, which is
  why v002 passed while the hauler clock was broken. Records the precise
  scope of that fault: a human playing a packaged build was never affected;
  every automated path was, which is why the loop could not be proven.
- [Packaged journey receipt v004](SPACECRAFT_PACKAGED_JOURNEY_v004.md) —
  supersedes v003. The Scout journey against `StarFactoryTycoon_v007`,
  plus what that revision carries: the site hub, the pre-placed ship
  factory, bulk buying, the hall shell and floor, and the interface
  graded to the adopted palette.
- [Packaged journey receipt v005](SPACECRAFT_PACKAGED_JOURNEY_v005.md) —
  supersedes v004, and records why **v008 must not be used to judge the
  game's look**: it was packaged 22 minutes before the asset-gate
  correction and contains the known-wrong blockout. `v009` is the same
  code with the gate fixed.
- [Reviewer notes](REVIEWER_NOTES_v001.md) — the guide that ships beside
  the build in `Builds/`, versioned here because `Builds/` is gitignored.
  Covers the first two minutes, what to do when the factory stops after
  its one free craft, and the real route to fabrication (parts factory →
  slots → research).

## Release authority

Read these files in order:

1. [Current gameplay status](ReleaseGate/CURRENT_GAMEPLAY_STATUS.md) — what is
   playable, validation-only, source-only, or planned.
2. [Controls and management UI](ReleaseGate/CONTROLS_AND_MANAGEMENT_UI.md) —
   current bindings and the management-screen target.
3. [Save compatibility](ReleaseGate/SAVE_COMPATIBILITY.md) — the checked-in v17
   topology/management contract, v13-v16 migration rules, and the validation
   still required before any compatibility claim.
4. [Asset provenance and promotion](ReleaseGate/ASSET_PROVENANCE_AND_PROMOTION.md)
   — source ownership, private Meshy generations, AI disclosure, and promotion
   states.
5. [Validation evidence](ReleaseGate/VALIDATION_EVIDENCE.md) — exact green and
   red reports plus the last proven Windows package.
6. [Unreal MCP editor operations](ReleaseGate/UNREAL_MCP_OPERATIONS.md) — the
   experimental localhost editor integration, safe operating procedure, schema
   workaround, and live diagnostic results.
7. [Localization and audio](ReleaseGate/LOCALIZATION_AND_AUDIO.md) — no current
   voice acting, localization blockers, and the staged language target.
8. [Feature-finish checklist](ReleaseGate/FEATURE_FINISH_CHECKLIST.md) — the
   mandatory definition of done.
9. [Modular factory asset development standard](ReleaseGate/MODULAR_FACTORY_ASSET_DEVELOPMENT_STANDARD.md) —
   construction, material, LOD, generated-source and promotion rules for robots,
   tools, fixtures, machines and reusable factory modules.

## Status vocabulary

| Status | Meaning |
|---|---|
| **Packaged playable** | The named journey was exercised in the named packaged build. The claim applies only to that package revision. |
| **Validation-only** | Code or content exists and has focused editor/source evidence, but the latest integrated journey has not passed in a fresh package. |
| **Source candidate** | Editable source/export exists; it is not an approved Unreal runtime asset. |
| **Planned** | Direction or contract only. It must not be presented as implemented. |

The strongest evidence wins. A later failing integration test overrides an older
green component test until the failure is fixed and rerun.

## Other authorities

Design intent remains in documents such as
[Press Trains implementation authority](PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md),
[PR-010 implementation authority](PR010_IMPLEMENTATION_AUTHORITY.md), and
[brand identity authority](BRAND_IDENTITY_AUTHORITY.md). Historical handovers
and dated audits are context, not current completion evidence. In particular,
the large `PROJECT_HANDOFF.md` and `NEW_CHAT_HANDOVER_2026-08-03.md` files must
not be used to overrule the release-gate status above.
