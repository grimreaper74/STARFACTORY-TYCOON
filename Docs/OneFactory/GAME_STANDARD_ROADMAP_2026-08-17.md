# Line Boss - roadmap to the gameplay-mockup standard (2026-08-17)

Produced by a 37-agent measured gap analysis against the owner's gameplay
mockup, with adversarial verification of every 'absent' and 'blocker' claim.
77 gaps confirmed; **16 claims were overturned** by verification.

---

## Roadmap

ROOT = `C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8`
SRC = `C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory`

# Line Boss — build roadmap to the gameplay mockup

## 1. Honest assessment

The game is much closer to the mockup than it looks on screen, and much further from it than the codebase suggests — the gap is almost entirely **wiring and framing, not missing features**. Every major element of the mockup already exists somewhere in the build: the six-card production-flow chain with real 3D-rendered machine thumbnails, status dots, green selected-card outline, detail column and green CTA are a working C++-built UMG tree (`ULBManagementRootWidget`); the £2.50m cash figure comes from a genuine 1,185-line double-entry economy in integer pence; the alert queue is a real severity-ranked projection of live machine faults; per-card throughput ("18.0/hr") and a floating alert toast are both rendered right now, just by a *second, cruder Canvas HUD* that overlaps the good one; a proper management camera pawn with pan/orbit/zoom is the map's default pawn; a roof cutaway works and is reversible; the press bay genuinely is packed (~2,860 rendered pieces). What is actually broken is that **the player cannot see or steer any of it**: after pressing B to commission the factory the view target is handed to a transient dev camera and never given back, so the camera controls move an off-screen pawn; the zoom cap (30,000 cm) physically cannot frame a shop on a 610 × 290 m site; there is no pitch axis and no near-isometric lens on the pawn; the whole management shell collapses on the same actions the mockup expects you to perform; two flow rows fight over the bottom 92 px of the screen with different stage models; the game boots to the *legacy press-shop map*, not the map the mockup depicts. Behind that: the economy has no sink at all (no machine has a price anywhere in the project), so the cash readout is decoration; research points accrue and can never be spent; and weld/paint/assembly are 2–7× sparser than press with no reference map to author against. Realistic reading: **the HUD is ~70% there, the camera ~50% but currently 0% usable, the management loop ~60% built and ~20% connected, and shop density is one department done and three not.** Nothing on the critical path needs to be invented from scratch — the first three milestones below are almost entirely deletion, re-parenting and unblocking, which is why they will visibly change the screen fast.

---

## 2. Milestones, in dependency order

Effort is in working sessions (one session ≈ a focused day) and is deliberately conservative because the frozen contracts and provenance guards make small edits expensive (see §6).

---

### M0 — Boot into the game the mockup depicts (blocker, prerequisite for judging anything)

**Deliverable.** The packaged/PIE default is `/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001` under `ALBOneFactoryGameMode`, so a cold launch lands in the four-shop site with the production HUD installed, not on `LB_PressShop_RebuildFromLorry_v20260810_v913` under `ALBGameMode` where the transport buttons are inert and there is no persistent HUD layer at all.

**Files/systems.** `<ROOT>/Config/DefaultEngine.ini:2-4` (`EditorStartupMap`, `GameDefaultMap`, `GlobalDefaultGameMode`); verify against `<SRC>/LBOneFactoryGameMode.cpp:71-72` and `<SRC>/LBGameMode.cpp:220-221`; update `<ROOT>/Docs/ReleaseGate/CURRENT_GAMEPLAY_STATUS.md`.

**Effort.** 0.5 session (the config change is one line; the session is spent confirming nothing on the legacy path was load-bearing).

**Success signal.** A cold PIE with no console commands logs, in order: `LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY layout=... factory="..."` (`<SRC>/LBOneFactoryBootstrap.cpp:79`) and `LINE_BOSS_ONEFACTORY_GAMEMODE` (`LBOneFactoryGameMode.cpp:156`), and `LINE_BOSS_ONEFACTORY_BOOTSTRAP_REJECTED` does **not** appear.

**Uncertainty.** I have not verified that the OneFactory map survives as `GameDefaultMap` in a *packaged* build (its game mode is currently applied as a map-local WorldSettings override, and the shell contract validator is strict). If packaging trips, the fallback is to keep the config default and make the launch path explicit — but do not skip this milestone: everything below is measured on that map.

---

### M1 — Give the player the camera back and let it frame one shop (blocker, highest visible payoff)

**Deliverable.** Five specific fixes, all in the pawn/controller, that convert an existing camera into the mockup's camera:

1. **Return the view target.** `ALBOneFactoryPlayerController::EnsureSitePresentation` ends with `ULBOneFactoryDevFactory::FrameProductionLine(this, "All")`, which spawns a transient `ACameraActor` tagged `LB.OneFactory.DevCamera` and calls `SetViewTargetWithBlend` — the only `SetViewTarget*` call in the module — and never hands back. Replace it with: solve the same pose, **push it into `ALBManagementPawn`** (it already has `SetAutomationCamera` and smoothed `VInterpTo/RInterpTo` at speed 5.5), and keep the pawn as view target.
2. **Raise the zoom ceiling.** `GetMaximumManagementZoomDistance()` = 30,000 cm cannot fit the 310 m bay span (~35,000 cm needed at 48° FOV) let alone the 562 m envelope (~63,000 cm). Raise to ~70,000 cm.
3. **Add pitch.** Lift `ALBPaintShopManagementPawn::OrbitPitch` verbatim (`<SRC>/LBPaintShopManagementPawn.cpp:285-297`, clamp −80…−10°, 70°/s, `bUsePawnControlRotation = true`) onto `ALBManagementPawn`; the `LB_ControlRoomLookPitch` axis already exists at `<ROOT>/Config/DefaultInput.ini:50-52`, so no input config change.
4. **One lens language, near-isometric.** The pawn is 48° and the dev framing camera is 78° — pick one and narrow it to ~28–32° for the mockup's near-parallel read. Do **not** attempt true orthographic: `Orthographic|ProjectionMode|OrthoWidth` appear nowhere in Source or Config, so ortho is new ground and a narrow FOV gets 90% of the look for none of the risk.
5. **Frame a shop, not the campus, and clamp the pan.** Bind a player-facing per-department framing action (the `Press/Body/Paint/Assembly` framing already works, it is just console-only via `LB.OneFactory.View`), re-key `FocusBuiltFactoryInternal` off the OneFactory tags (`LB.OneFactory.*Starter`) instead of the dead legacy `LB.FactoryBuilder.Machine` tags so Home and the FACTORY button stop being no-ops, and clamp the pivot to the site so W does not walk into the void.

Also in scope because they silently sabotage the above: the **Q / R / B key collisions** (`ALBOneFactoryPlayerController::SetupInputComponent` uses raw `BindKey` with default `bConsumeInput = true` and is evaluated *before* the pawn, so a camera orbit passes a quality decision and placement ghosts cannot be rotated), and **camera dead at spawn** (the pawn opens the build catalogue on itself in `BeginPlay`, and `IsManagementOpen()` then zeroes pan and orbit).

**Files/systems.** `<SRC>/LBManagementPawn.cpp` (~lines 930-960, 1046-1152, 1414-1471, 1569-1650, 1910-2007), `<SRC>/LBManagementPawn.h:228-231`, `<SRC>/LBOneFactoryPlayerController.cpp:68-118, 196-230, 401`, `<SRC>/LBOneFactoryDevFactoryCommands.cpp:610-800`, `<SRC>/LBPaintShopManagementPawn.cpp` (source to lift), `<ROOT>/Config/DefaultInput.ini`.

**Effort.** 2–3 sessions.

**Success signal.** A recorded PIE clip: cold boot → B → the view is a high near-isometric shot of the press shop with the roof off → WASD pans, Q/E orbits, Up/Down pitches, wheel zooms out far enough to fit the whole 610 m site and back in to one cell, Home returns to the press-shop frame. Machine-checkable half: `LB.OneFactory.Tour` completes and logs `LINE_BOSS_DEV_TOUR_SHOT <Dept>` for all four departments plus `LINE_BOSS_DEV_TOUR_COMPLETE stops=4` (`LBOneFactoryDevFactoryCommands.cpp:1175, 1186`), and a new assertion that `PlayerController->GetViewTarget() == PlayerController->GetPawn()` after `EnsureSitePresentation`.

---

### M2 — One HUD, always on (blocker)

**Deliverable.** A single UMG surface that never disappears, in this exact order (order matters — deleting the Canvas strip first destroys the only per-card throughput *and* the only alert toast in the game):

1. **Lift before deleting.** Port the Canvas strip's per-card throughput maths (`3600.0f / SlowestCycle[Index]`, `LBOneFactoryProductionHUD.cpp:176-196`) and `DrawAlertToast` (`:431-459`) into the UMG shell. The toast becomes a canvas-slot widget driven by `ProjectWorldLocationToScreen` from `FLBFactoryUIAlertSnapshot::MarkerWorldLocation` — a complete world-projected version with leader line and severity colour already exists as reference inside the retired `#if 0` block at `LBControlRoomHUD.cpp:1045-1101`.
2. **Then delete `DrawFlowStrip`** and stop the two flow rows overlapping in the bottom ~92 px with conflicting seven-stage vs six-stage models. Keep the six mockup stages.
3. **Split the shell.** Hoist `TopStripSizeBox` and `FlowTrayBorder` out of the modal page system into an always-on layer so they survive `bManagementVisible = false`, the M toggle, and placement. Remove the `bManagementVisible = false` on CTA success (`LBControlRoomHUD.cpp:2756, 2781`) — the mockup's "Place next machine" must not dismiss the panel that issued it.
4. **Account for the third and fourth surfaces:** the pawn's Canvas placement card (`LBManagementPawn.cpp:862-916, 1014`) is currently invisible anyway because `ALBControlRoomHUD::DrawHUD` never calls `Super::DrawHUD()` so `AHUD::DrawActorOverlays` never runs and `bShowOverlays` is never set — re-home that card as a UMG widget rather than reviving the overlay pass, and surface the placement success string (`PLACED x WITH n AUTOMATIC LINK(S) … n SERVICE WALKWAY TILES`) which is currently written and then immediately blanked by `ResetPlacementPresentation()`.
5. Anchor the top strip and tray backgrounds to the real viewport so non-16:9 stops letterboxing the whole shell (`UpdateResponsiveLayout()` is currently comments only).

**Files/systems.** `<SRC>/LBManagementRootWidget.cpp/.h` (build at 325-870, refresh at 940-1200), `<SRC>/LBOneFactoryProductionHUD.cpp/.h` (retire), `<SRC>/LBControlRoomHUD.cpp:1209-1245, 1474-1487, 2729-2783`, `<SRC>/LBManagementPawn.cpp:862-1041`, `<SRC>/LBManagementRootWidgetTests.cpp`.

**Effort.** 3–4 sessions.

**Success signal.** A single 1920×1080 capture in which: exactly one production-flow row is visible; each of the six cards shows thumbnail + dot + state + a `x.x/hr` figure; a world-anchored alert toast points at the offending machine; and the same capture repeated after pressing M, after clicking a card, and after starting a placement is *identical in the top strip and flow tray*. Test side: `LBManagementRootWidgetTests.cpp` grows assertions that the top strip and flow tray remain `Visible` across all three page contexts, and `grep DrawFlowStrip <SRC>` returns nothing.

---

### M3 — Fill in the mockup's readouts and iconography

**Deliverable.** Everything the mockup shows that the shell does not yet say. Data-model changes first, then styling:

- Add `ThroughputPerHour`, `WaitingCount`/`Occupancy` and `Capacity` to `FLBFactoryUIProductionStageSnapshot` (`<SRC>/LBFactoryUIStateSubsystem.h:150-163`) and to `FLBManagementStagePresentation` (`LBManagementRootWidget.h:60-82`). The counts already exist upstream — the subsystem formats `%d / %d blanks` and `%d / %d stillages` from `Zone->GetOccupancy()/GetCapacity()` at `LBFactoryUIStateSubsystem.cpp:461` — they just never reach a card. This unlocks per-card `Waiting: 2`, the per-stage `14.2 panels/hr` in the detail panel (today it shows one factory-wide figure that does not change with selection), and the detail panel's `Blank buffer: 8` via an upstream-stage relation.
- `1x` speed readout: one `UTextBlock` bound to `LastSnapshot.EffectiveSimulationRate` — but it stays stuck at 1.0 until M4 fixes the rate source (see below), so ship them together.
- Split the merged `CAIRNWELL 2040   0 / 0 issued` label into a model badge pill + an order chip, so the model identity stops vanishing on `NO ACTIVE ORDER`.
- Chip/pill backgrounds behind cash, orders and alerts; raise nav labels from 10pt and drop the fully-transparent resting brush so the nav row is legible at the mockup's framing; arrowheads on the 24×2 px connectors.
- Make the alert count a button that calls the existing `JumpToTopFactoryAlert()`.
- **Icon library** (the root cause behind seven separate "missing icon" gaps): `Content/LineBoss/UI` contains only the twelve flow thumbnails and there are zero font assets in the project. Author ~13 flat monochrome UI icons (hamburger, factory, clipboard, chart, trophy, gear, cash, bell, warning triangle, gauge, layers, chevron, transport glyphs) and import them as UI textures via the existing `Scripts/` Python path. Add the FACTORY/overview button (its handler `OnFactoryDestinationClicked()` exists and is never bound) and a trophy slot that can be dark until M6.
- Wrap the shell in `LOCTEXT` while touching every string anyway — the Canvas HUD it replaced was properly wrapped; the UMG one is 100% raw literals with a hardcoded `£`.

**Files/systems.** `<SRC>/LBFactoryUIStateSubsystem.cpp/.h`, `<SRC>/LBManagementRootWidget.cpp/.h`, `<SRC>/LBManagementRootWidgetTests.cpp`, `<ROOT>/Content/LineBoss/UI/Icons/v001/*` (new), `<ROOT>/Scripts/`.

**Effort.** 3–4 sessions (icons are the long pole; if the owner supplies a licensed set, 2).

**Success signal.** Side-by-side of the mockup and a capture, element-by-element, with every one of the mockup's fourteen named HUD elements present and reading live values. Test side: `LBManagementRootWidgetTests.cpp` asserts a non-zero per-stage rate renders on the selected card, that the icon set loads (mirroring the existing `HasCompleteThumbnailSet` pattern which already load-tests all six 384×240 thumbnails), and that the speed readout matches the requested rate.

---

### M4 — Make the loop bite: prices, costs, vehicle revenue, working time controls (blocker for the game *being* a management game)

**Deliverable.** Four connections into an economy that is already built and already correct:

1. **Machine prices.** There is no price for any machine anywhere in the project — `CostPence`/`PricePence` appear only inside `LBFactoryManagementSubsystem` and its tests. Add a price catalogue keyed by machine/storage type; have `ULBFactoryMachineBuilderSubsystem::PlaceMachine` (`:1778`) call the existing, unused `TryPurchaseCapitalAsset`, and `CanPlaceMachine` (`:882`) gate on affordability alongside its process-chain rules. Until this lands, the £2.50m readout is decoration and the build flow contains no decision.
2. **Operating costs.** `TryChargeOperatingCost` exists with a ledger category and has zero non-test callers. Charge wages/energy/coil per sim hour so cash can go down.
3. **Vehicle revenue.** Today revenue is a pressed-panel contract (£250/panel, honestly commented as *not* claiming a vehicle exists). Add a completed-`CAIRNWELL_2040` revenue event at end-of-line/dispatch.
4. **Time controls.** Two independent defects: the handler returns early unless `IsOneFactoryOperationsWorld()` (M0 fixes the map half of this), and `SetSimulationRate` writes `Coordinator->RuntimeTimeScale` while the snapshot reads `AWorldSettings::GetEffectiveTimeDilation()` — so the readout can never move. Make one of them authoritative.

**Files/systems.** `<SRC>/LBFactoryManagementSubsystem.cpp:176-230`, `<SRC>/LBFactoryMachineBuilderSubsystem.cpp:882, 1778`, `<SRC>/LBFactoryManagementRuntimeSubsystem.cpp:677-714`, `<SRC>/LBOneFactoryOperationsSubsystem.cpp:529`, `<SRC>/LBFactoryUIStateSubsystem.cpp:201`, `<SRC>/LBControlRoomHUD.cpp:1611-1620`, new price data table.

**Effort.** 3 sessions.

**Success signal.** A logged play session in which the cash readout **falls** on a placement and **rises** on a dispatch: `LINE_BOSS_PLAYER_SPEED 2.00x` (`LBOneFactoryPlayerController.cpp:253`) appears and the HUD reads `2x`; a new automation test asserts `CashBalancePence` strictly decreases across `PlaceMachine` and that placement is refused when cash < price.

---

### M5 — Density and floor paint in weld, paint and assembly

**Deliverable.** Bring the three sparse shops toward the press bar (press ~0.069 inst/m²; weld ~0.034, paint ~0.0094, assembly ~0.013). Three sub-pieces, in order:

1. **Unfreeze the contracts first, or every later step costs five file edits.** Press 268 / weld 597 / paint 119 / assembly 95 are hard-coded literals re-asserted in per-batch tables, per-role tables *and* the tests; the handover records weld being re-frozen three times (469→489→597). Convert the presentation contracts from "assert this literal total" to "assert the total equals the sum of the declarative layout table", so a prop can be added by editing data. This is the single change that makes density iterable by eye rather than by commit.
2. **Green painted cell and walkway zones.** `ULBFactoryFloorMarkingComponent` is complete and tested — 8 semantics including a green `StorageFill` (2D7D55), outlines, hatching, dashed lines — and **no One Factory class includes the header**. Wire it into the four `LBOneFactory*StarterPresentationActor` classes. Today's floor paint is 20 yellow boundary strips, one whole-bay tint per department, and green route stripes.
3. **Spend the Fab pack.** `Content/Meshes` holds 785 static meshes, of which exactly 21 are used. The unused 764 are precisely the mockup's missing vocabulary: `SM_IndustrialPlatform`/`SM_PlatformGrill`/`SM_PlatformRailing`/`SM_FloorStairs` (**mezzanines — currently zero anywhere in the project**), `SM_HeavyArch`/`SM_LampArch` (shop-scale gantries; weld/paint/assembly have only 3–6 m per-machine arches under a bare 22 m wall), `SM_StorageShelves*` (only the *Bottom* piece of a four-piece family is wired), the modular pipe sets, `SM_ElectricalPanel`/`SM_Switchboard` (service cabinets), `SM_LargeWindowFramed` (the clerestory), `SM_PaintBox*` (a paint booth kit). Fill the implausible 56–60 m mid-bay voids between the parallel weld and assembly rows, and copy the weld per-station service pattern (HMI pedestal + guard + cabinet at every station) into paint and assembly, which currently get one cabinet and a fence run.
4. **Make the four press rows real, or stop showing them.** Rows B–D are collision-disabled decoration in the OneFactory route, while the *press-shop* game mode has a fully tested four-train stack (identity `TRAIN_A..D`, protected envelopes, per-train AGV handoff, HUD surface, persistence). Either wire real stations into the OneFactory route or accept them as set dressing — but decide, because the mockup's "multiple parallel cells" currently reads as one live line plus three props.

**Note on method** (owner's standing direction, pinned): press density is editor-authored — `LB_PressShop_FullFactoryRestored_v001.umap` (11.3 MB, ~4,060 labelled actors) baked into a 2,804-row manifest, so press is art-directed by moving meshes in the editor and re-baking. **There is no equivalent reference map for weld, paint or assembly** (only two small Experimental prototypes and a single-robot gate), and the manifest loader is hard-anchored to the press train datum and fails without it. So the honest cost here is *authoring three reference maps in the editor*, not writing three C++ tables — which is both what the owner asked for and the larger number.

**Files/systems.** `<SRC>/LBOneFactory{BodyWeld,Paint,Assembly}StarterPresentationActor.cpp` + their layouts + their tests, `<SRC>/LBFactoryFloorMarkingComponent.h/.cpp`, `<SRC>/LBOneFactoryDevStationDressingActor.cpp:39-49` (the Kinds table registers only 10 of 785 pack meshes), `<SRC>/LBOneFactoryDevRestoredShopActor.cpp` (generalise off the press anchor), new reference maps under `<ROOT>/Content/LineBoss/Reference/`.

**Effort.** 8–12 sessions, and the widest error bar in this document. The contract unfreeze is 2; floor paint is 1–2; each authored reference map is 2–3 and needs the owner's eye.

**Success signal.** Per-department instance density logged and captured: weld/paint/assembly each ≥ 0.03 inst/m² (i.e. within ~2× of press) with the counts reported in the existing dressing/presentation log lines; four captures at the M1 framing showing green per-cell zones, marked walkways, occupied mid-bay strips and at least one mezzanine per shop; and the presentation test suite green with the counts now derived rather than literal.

---

### M6 — Progression that can actually be spent

**Deliverable.** Research points already accrue at 5 per fulfilled order and the unlock/upgrade API is complete and idempotent — and `HasResearchUnlock`'s only non-test caller is `TryPurchaseMachineUpgrade` in the same file. Nothing in the game unlocks anything. Give the Research page real actions, gate a handful of machines/capabilities behind unlocks in `CanPlaceMachine`, and turn orders into contracts (offers with due dates, penalties, reputation) rather than the current self-issued work order from hardcoded model/panel arrays. Awards/trophy last — it is the only item in the mockup with literally zero substrate (`grep -i "achievement\|award\|trophy" <SRC>` returns nothing).

**Files/systems.** `<SRC>/LBFactoryManagementSubsystem.cpp:256-300`, `<SRC>/LBControlRoomHUD.cpp:1917, 3289`, `<SRC>/LBPlayerBuiltPressFlowController.h:95-199`, `<SRC>/LBFactoryMachineBuilderSubsystem.cpp:882`. Also add autosave/named slots (the save mechanism is complete; the lifecycle is one hardcoded slot with no autosave, no save-on-quit and no front end).

**Effort.** 5–7 sessions.

**Success signal.** A save/reload session in which a research unlock is purchased, a previously-refused machine becomes placeable, and the ledger shows the spend; `0 / 16 issued` comes from an externally-issued contract with a deadline rather than the player's own quantity spinner.

---

### M7 — Environment, lighting and site polish (LAST, deliberately)

**Deliverable.** In this order: persist a sun/sky into the level so the clerestory can actually admit daylight (the map on disk holds ~24 actors and **no** DirectionalLight, SkyLight, SkyAtmosphere or fog — the readable rig is spawned at runtime by a class its own header calls developer-only, and is never saved); glaze the clerestory (it is currently a scaled `/Engine/BasicShapes/Cube` band tinted E8F0FA, opaque and non-translucent, with `SM_LargeWindowFramed` sitting unused); replace the runtime cube envelope with authored geometry saved in the editor (its own header says "A permanent envelope belongs in the map… This exists so the factory can be looked at and judged now"); extend the roof cutaway so the 2200 cm walls that start at Z 0 stop showing their back faces at high angles; add per-shop trusses and crane runways to weld/paint/assembly; Megascans ground materials and vegetation (see §5); then shipping-hardening — move roof/lighting/framing out of `ULBOneFactoryDevFactory` into player-facing systems, since in a packaged Shipping build the player's camera, cutaway and lighting are all currently supplied by dev tooling with no `UE_BUILD_SHIPPING` guard, and the runtime `RecaptureSky()` is the exact call `LBGameMode.cpp:544` warns can cause a D3D12 device loss before the first playable frame.

**Effort.** 6–10 sessions. **Do not start any of it before M5 is signed off.**

**Success signal.** The map opens in the editor already lit and enveloped (no B press required); a luma probe of the press floor band ≥ 40/255 mean with < 20% dark fraction (the current audit measures 37.4 and 39.2%); zero `/Engine/BasicShapes/` references in the shipped envelope path.

---

## 3. Sequencing rationale

The owner's frustration is with effort that did not show up on screen, so the ordering is chosen by **visible change per session**, not by architectural tidiness:

- **M0–M1 are the largest visible change available anywhere in this project for the least work.** The mockup's headline is a framing, and the framing is one broken view-target hand-off, one number (`30000`), one lifted pitch function and one FOV away. The press bay behind that camera is *already* at reference density (~2,860 pieces, overhead crane, 12 trusses, 81 pipe runs). So M1 alone turns "we have systems" into "that is the picture" — with no new art, no new geometry, no contract edits, and no provenance risk.
- **M2 next because it is mostly deletion.** Retiring one of two duplicated flow rows and un-gating a shell that is already built makes the screen cleaner and more mockup-like by *removing* code. Doing M2 before M3 also prevents polishing a widget that is about to be re-parented.
- **M3 before M4** because the readouts are cheap and highly visible, but note the `1x` readout and the per-stage throughput are the two places where HUD work depends on loop work — hence M4 immediately after, not later.
- **M4 before M5** because the mockup's £2.50m and the whole "management game" claim are currently fiction: no machine has a price, so cash only ever goes up. This is a small change with an enormous felt difference, and it makes the build flow — which is genuinely excellent already, with ghost preview, auto-connect, service walkways and Manhattan AGV routing — into a decision rather than a formality.
- **M5 is fifth, not first, despite "packed floor" being in the mockup**, because the mockup frames *the press shop*, and press is already there. Weld/paint/assembly density is the biggest single block of work in this document and needs three authored reference maps; putting it earlier means many sessions before the screen changes.
- **M6 is deferred** because progression is invisible until there is something to spend on and a reason to care.
- **M7 is last by instruction and by logic**: the lighting rig, envelope and site dressing are the things most likely to be redone once the camera, HUD and density are settled, and doing them first would mean polishing an environment framed by a camera that does not work.

---

## 4. The single highest-value next action

**Fix the view-target hand-off in `ALBOneFactoryPlayerController::EnsureSitePresentation` (`<SRC>/LBOneFactoryPlayerController.cpp:224`) and raise `GetMaximumManagementZoomDistance()` (`<SRC>/LBManagementPawn.h:228`).**

Why: it is a few lines, it is the only `SetViewTarget*` call in the entire module, and it is the reason every camera control in the game currently appears broken. After commissioning — the normal and only way to get a factory — WASD, Q/E, the wheel and Home all still drive the pawn correctly while the screen never moves, because a transient dev `ACameraActor` holds the view for the rest of the session and `AutoManageActiveCameraTarget` only re-evaluates on possess/restart. The pose that dev camera picks is already roughly the mockup's (≈34° down-pitch, solved fit); it simply cannot be moved. Un-sticking it plus lifting the zoom cap converts a mass of already-built, already-tested camera machinery — pan, orbit, smoothed focus, framing contracts, a working per-world roof cutaway — from invisible to playable in a single sitting, and it is the prerequisite for judging every other milestone by eye.

---

## 5. Needs the owner's own account or decision (cannot be done autonomously)

1. **Fab / Quixel account — ground materials and vegetation.** Megascans surfaces for the yard and shop floor, and Megaplants vegetation, require the owner's own Fab account. The project has **no** tree, bush, hedge or grass mesh anywhere, in any of the seven owned packs (confirmed 2026-08-17). Site greenery cannot be delivered without either their account or Blender-authored trees.
2. **Fab account — any additional pack.** If mezzanine/gantry/window coverage from the existing Factory Environment Collection proves insufficient (it looks sufficient: the platform, arch, racking, pipe, switchboard, window and paint-booth families are all present and unused), any new pack needs their download.
3. **A UI icon set and a brand typeface.** I can author flat monochrome icons and import them, but if the owner has a licensed icon set or the Cairnwell typeface from the design-pack sheets, that is better and cheaper. All HUD text currently uses engine Roboto; there are zero font assets in the project.
4. **The brand logo mark.** The supplied print logo was deliberately dropped by a previous session as "an unreadable smudge on a dark operations shell". The texture is still on disk and `GetBrandLogoPath()` still resolves it. Owner decision: re-commission a legible dark-UI mark, or ship the text wordmark.
5. **Four judgement calls I should not make alone.**
   (a) M0's map switch — is `LB_MoorcrossWorks_OneFactory_v001` the shipping game, and can the legacy press-shop map's four-train builder be left behind?
   (b) Is the target frame *one shop filling the screen* (my reading of the mockup) or the whole 610 m site?
   (c) Should press rows B–D become real stations (the four-train stack exists and is capped at 4) or stay as dressing?
   (d) M5 needs their eye on three authored reference maps, because the done-bar is their judgement of density, not a number.
6. **Retrieval of the pre-site backup** at `E:\LineBossValidationOutput\MapBackups\...pre-site.umap` if M7 needs the 5,049-actor site pass that was reset — I should not assume that external drive is available.

---

## 6. Risks

**R1 — The provenance guard, and why it is the most dangerous thing in this plan.** `ALBOneFactoryBootstrap::ActorUsesForbiddenProvenance` (`<SRC>/LBOneFactoryBootstrap.cpp:124-171`) rejects any actor whose **name, actor label, any tag, any static-mesh path, or any material path** on any `UStaticMeshComponent` contains `Meshy` or `ExternalGenerated`, case-insensitively (`:15-19`). `ActorIsForbiddenLegacyFixture` (`:91-122`) additionally rejects `LB.Meshy`/`LB.Legacy`/`LB.VisualQA` tag prefixes and the substrings `FallbackFloor`, `VisualQA`, `Meshy`, `Lorry` in the name or label. On violation, `BeginPlay` logs `LINE_BOSS_ONEFACTORY_BOOTSTRAP_REJECTED reason=…` at Error and **returns** (`:72-77`) — the shell is never validated or locked, so the factory does not commission, and **nothing crashes and no test fails**, because the 278 test-macro declarations across 85 files exercise the validators against synthetic strings rather than the live world. This bites M5 hardest: the project is full of legitimately-approved Meshy-derived art (`SM_CA_MW_PR005_dHMI_Meshy_v001`, the approved Meshy coil-handler chassis, `SM_LB_BodyWeld_FramingFixture` tooling derived from a Meshy SpotRobot). **Mitigation, non-negotiable, before every commit that adds an asset reference:** grep the added mesh/material paths for `Meshy|ExternalGenerated|Lorry|VisualQA|FallbackFloor`, and confirm a cold PIE logs `LINE_BOSS_ONEFACTORY_BOOTSTRAP_READY` and not `..._REJECTED`. Add that log assertion to CI if it is not already there — `LBOneFactoryTests.cpp:445` references the rejection string, so the hook exists.

**R2 — Frozen presentation contracts make small density edits expensive and easy to get half-right.** Each department asserts a literal total (press 268 logical items + `ExpectedVisualBatchCount 1` / `ExpectedRenderedAggregateCount 1`; weld 597; paint 119; assembly 95) *plus* per-batch and per-role tables, and the tests re-assert the same literals. Adding one prop means editing builder + total + per-batch table + per-role table + tests in one commit, or the layout is rejected at commission. This is why paint and assembly have stagnated at 119 and 95. M5 step 1 (derive the totals) is therefore not optional refactoring — it is the precondition for iterating density at all.

**R3 — Press is doubly locked.** `MakeNativeOnlyProfile` restricts press presentation assets to four package roots and lists `/Candidates/`, `/Runtime/PressShop/` and `/Stations/Press/` as forbidden tokens, so the press presentation is *structurally barred* from referencing the authored press kits, the IndustrialKit or the Fab pack — which is why its content arrives as a single baked 14 MB, 306-material-slot aggregate mesh (which the player controller then *hides* at runtime, so the press bay you see is actually the manifest plus dressing). Raising in-contract press density means re-exporting that aggregate, and I have not verified the source `.blend` authority is reachable. Prefer widening the allowlist over re-baking, and get that decision made explicitly.

**R4 — Deleting the Canvas HUD in the wrong order loses working features.** `DrawFlowStrip` carries the only per-card throughput figure in the game and `DrawAlertToast` the only alert toast. Lift both into UMG and verify on screen *before* deletion (M2 step ordering).

**R5 — Retired code looks alive.** ~1,300 lines of `ALBControlRoomHUD` Canvas HUD sit behind four `#if 0` blocks and are not declared in the header. They are excellent *reference* (the world-projected alert callout especially) and completely unreachable. Do not "fix" them; port from them.

**R6 — Shipping-build exposure.** The player's camera, roof cutaway and lighting all run through `ULBOneFactoryDevFactory`, a `UBlueprintFunctionLibrary` whose header calls itself developer-only, with no `UE_BUILD_SHIPPING` guard, and one of its calls (`RecaptureSky()`) is the exact operation `LBGameMode.cpp:544` warns can cause a D3D12 device loss before the first playable frame. M1 should move the framing solver out on the way past; M7 finishes the job.

**R7 — Uncertainties I have not resolved.** (a) Whether the OneFactory map works as the packaged default (M0). (b) Whether "278 tests" is a run count — I measured 278 automation-test *macro declarations* across 85 files, which is the likely source of the figure, but I did not execute the suite. (c) Whether the press aggregate's `.blend` authority is available. (d) Whether a narrow-FOV perspective camera reads as "near-isometric" to the owner's eye, or whether true orthographic (zero prior art in this project) is actually required — that is a look-at-it-and-say call after M1, not a decision to make in advance.

---

## Claims corrected by adversarial verification

These were originally reported as absent or blocking and proved wrong.
Do NOT plan work from the original claims.

### hud / HUD persistence — the whole shell is gated behind a toggle (was: partial)

HUD persistence — partial, but for the opposite reason: a persistent chrome layer already exists; it is the wrong half of the mockup.

Two layers are already separated by class. The persistent layer is Canvas drawing in ALBOneFactoryProductionHUD::DrawHUD (LBOneFactoryProductionHUD.cpp:271-305), which never reads bManagementVisible — `grep bManagementVisible LBOneFactoryProductionHUD.cpp` returns nothing. It always draws the bottom "PRODUCTION FLOW" tray (DrawFlowStrip, 308-429: seven stage cards with label, station count, "QA GATE" flag, mean-progress bar, state + unit count, "{0}/hr" throughput, green ">" arrows at 423), the ON LINE / DISPATCHED / ALERTS summary (328-334), and floating alert toasts (DrawAlertToast, 431-459). It is installed by LBOneFactoryGameMode.cpp:72 on LB_MoorcrossWorks_OneFactory_v001.umap, the only map referencing that game mode, confirmed authoritative at Docs/ReleaseGate/CURRENT_GAMEPLAY_STATUS.md:8-9.

The gated layer is the UMG shell, ULBManagementRootWidget, collapsed by SyncModernOverviewWidget() (LBControlRoomHUD.cpp:1474-1487) whenever IsModernManagementActive() (1241-1245) is false, with bManagementVisible defaulting to false (LBControlRoomHUD.h:236). That layer is where the mockup's TOP BAR actually lives — CashLabel, AlertLabel and the pause/play/fast-forward SimulationRateButtons are widget bindings at LBManagementRootWidget.h:303, 306, 312-314 — plus the selection detail panel. So M (LBManagementPawn.cpp:1142, DefaultInput.ini:12) and the CTA's own bManagementVisible = false (LBControlRoomHUD.cpp:2756, 2781) dismiss the top bar, cash, alert count, transport controls and detail panel, while the flow tray and toasts stay on screen.

The real gaps against the mockup are therefore:
1. Wrong layer assignment. Company mark, "CAIRNWELL AUTOMOTIVE", nav icons, "CAIRNWELL 2040" badge, "0 / 16 issued", "£2.50m", pause/play/FF + "1x", "2 alerts" and the right detail panel are all in the modal layer and vanish on M. They belong in the persistent layer. Conversely the flow tray exists in both layers simultaneously and will double-draw at the bottom of the screen whenever the UMG shell is open, since DrawFlowStrip is unconditional.
2. The CTA is self-defeating: ActivateProductionFlowPrimaryAction (LBControlRoomHUD.cpp:2729-2783) hides the shell on success (2756, 2781), so the mockup's "Place next machine" removes the panel that issued it.
3. The persistent layer is Canvas-only and cannot reach the mockup's fidelity: flat DrawRect cards with no rendered 3D thumbnails, no per-card status dot (state is a 3px left stripe at 362 plus coloured text at 396-405), and combined "Running 3 units" text rather than the mockup's separate "Waiting: 2" dot label.
4. Under LBGameMode (LBGameMode.cpp:221) — DefaultEngine.ini:4's GlobalDefaultGameMode, still pointed at the legacy press-shop map at DefaultEngine.ini:2-3 — there genuinely is no persistent layer at all: ALBControlRoomHUD::DrawHUD (4034-4038) draws nothing and the old Canvas top bar is dead code behind `#if 0` (858-1159). That configuration, not the gameplay map, is what the prior analysis measured.

### hud / Default launch state hides the production flow (was: partial)

The default launch state does NOT hide the production flow — it draws two competing flow surfaces and lets the newer one cover the older one.

On the live playable map (`/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`, whose map-local GameMode override is `ALBOneFactoryGameMode`, per the single `LBOneFactoryGameMode` reference in the .umap and `Docs/OneFactory/ONE_FACTORY_ACTUAL_PLAYER_PIE_V001.md:9-19`), the installed HUD is `ALBOneFactoryProductionHUD` (`LBOneFactoryGameMode.cpp:72`), not bare `ALBControlRoomHUD`. Its `DrawHUD()` (`LBOneFactoryProductionHUD.cpp:271-305`) calls `DrawFlowStrip` and `DrawAlertToast` with no `ManagementPage` or `bManagementVisible` gate — only a valid Canvas and a coordinator + production authority, both created at BeginPlay by `ALBOneFactoryGameMode::EnsureRuntimeBackbone` (`LBOneFactoryGameMode.cpp:145-146, 167-180`). So a bottom "PRODUCTION FLOW" strip with per-stage cards, station counts, colour-coded state + unit counts, `x.x/hr` throughput and `>` flow arrows (`LBOneFactoryProductionHUD.cpp:308-425`) plus `ON LINE / DISPATCHED / ALERTS` counters (`:325-334`) renders from frame one, regardless of the page state.

The claim's mechanism is nonetheless real and its four cited lines all check out: `LBManagementPawn.cpp:993` and `:1038` do call `OpenFactoryBuild()` on a console-free map, `LBControlRoomHUD.cpp:2212` does set `ManagementPage = FactoryBuild`, and `LBManagementRootWidget.cpp:903-913` does collapse `FlowTrayBorder` (taking the six UMG stage cards, their 3D thumbnails and the right detail panel with it, since `BuildDetailPanel` is a child of `TrayContent` inside that border — `:619-652`).

The accurate finding is a Z-order collision, not an absence. `ContextBorder` is bottom-anchored with offsets `(32, -40, 32, 344)` (`LBManagementRootWidget.cpp:357-360`) and a near-opaque `Ink` fill (alpha 0.985, `:34`) at ZOrder 50 (`LBControlRoomHUD.cpp:1223`), spanning y≈696-1040 at 1080p; the Canvas strip spans y≈948-1080 (`LBOneFactoryProductionHUD.cpp:319-320`). Slate draws over the HUD canvas, so the Build panel masks roughly the top 70% of the strip — the per-stage state/unit and throughput text at y≈1046 (`:395-414`) peeks out beneath it, and the alert toast at y≈900-934 (`:445`) is completely buried behind the panel. So what the mockup wants (flow chain + right detail panel + a visible alert toast) is present in two half-finished pieces that are fighting for the same screen real estate, and the mockup's 3D thumbnails and detail panel exist only in the collapsed UMG tray.

The navigation half of the claim is correct and worth keeping: `OnFactoryDestinationClicked()` is defined (`LBManagementRootWidget.cpp:1269`) but never `AddDynamic`-bound; the top strip wires only BUILD/PRODUCTION/ANALYTICS/SETTINGS (`:499-528`), so `[` / `]` (`Config/DefaultInput.ini:14,16`, gamepad shoulders `:15,17`) are the only way to reach Overview — and `M` actively cannot, because `ToggleManagement` re-forces FactoryBuild on any console-free map (`LBControlRoomHUD.cpp:2204-2208`). The `-LineBossAutoProductionHUD` Overview path (`LBGameMode.cpp:433-441`) is command-line-gated inside `#if !UE_BUILD_SHIPPING` and is not player-reachable.

### hud / Per-card throughput figure ("18.0/hr") (was: absent)

CORRECTED STATE: partially present — implemented, rendered and covered by tests in the Canvas production-flow strip, absent only from the UMG shell's stage cards.

The mockup's per-card throughput figure exists in the exact requested format. LBOneFactoryProductionHUD.cpp:407-415 draws LOCTEXT("ThroughputPerHour", "{0}/hr") on each production-flow card, formatted to one decimal place by RateFormat (LBOneFactoryProductionHUD.cpp:98-102) — i.e. "18.0/hr". The value is a per-group bottleneck rate, 3600.0f / SlowestCycle[Index] (LBOneFactoryProductionHUD.cpp:191-196), where SlowestCycle is the maximum NominalCycleSeconds across the stations the configured route assigns to that group (:176-189). The card also carries the state dot/stripe (:362), the "Running / Waiting: N" style state-and-units label (:396-405), a mean-progress bar (:383-392), and green ">" flow arrows between cards (:423) — four more mockup elements in the same strip.

This is the live HUD, not dead code. LBOneFactoryGameMode.cpp:72 sets HUDClass = ALBOneFactoryProductionHUD::StaticClass(); LB_MoorcrossWorks_OneFactory_v001.umap overrides WorldSettings DefaultGameMode to LBOneFactoryGameMode; LBOneFactoryProductionHUD.h:50-52 states "The game mode installs this directly, so no console swap is needed"; and LBOneFactoryTests.cpp:235-242 asserts the HUDClass under a comment dating the change to 2026-08-16. A console path also exists: "LB.OneFactory.HUD" at LBOneFactoryDevFactoryCommands.cpp:1694-1726.

The prior analysis conflated this with genuinely retired code. ALBControlRoomHUD::DrawProductionFlowHUD is the retired one, dead behind #if 0 at LBControlRoomHUD.cpp:2785-2788; ALBControlRoomHUD::DrawHUD (LBControlRoomHUD.cpp:4034-4038) draws no Canvas at all.

WHAT IS ACTUALLY WRONG (state this instead of "absent"):
1. Duplicated flow strip. ALBOneFactoryProductionHUD derives from ALBControlRoomHUD (LBOneFactoryProductionHUD.h:55-56) and calls Super::DrawHUD() (LBOneFactoryProductionHUD.cpp:273), which creates the UMG shell (LBControlRoomHUD.cpp:1209-1210). The UMG "Production flow" tray is bottom-anchored (LBManagementRootWidget.cpp:610-616) and the Canvas strip draws at Height - StripH (LBOneFactoryProductionHUD.cpp:317-319). Both occupy the bottom of the same frame: the rich UMG cards (thumbnails, selection border, click-through to the detail panel) carry no rate, while the crude Canvas cards underneath carry the rate. One frame, two competing versions of the same panel.
2. No per-stage rate in the UI-state projection. FLBFactoryUIProductionStageSnapshot (LBFactoryUIStateSubsystem.h:150-163) and FLBManagementStagePresentation (LBManagementRootWidget.h:60-82) both lack a throughput field, so RefreshStageCard (LBManagementRootWidget.cpp:982-1035) has nothing to render.
3. The two on-screen numbers are different quantities. The Canvas per-card figure is a nominal design rate from authored cycle times; the UMG detail panel's "FACTORY GOOD OUTPUT %.1f units/hr" (LBManagementRootWidget.cpp:1094-1103) is measured, from Management.ThroughputGoodUnitsPerHour (LBFactoryUIStateSubsystem.cpp:589, LifetimeKPIs). The shell also guards the measured figure behind HasTruthfulThroughput (LBManagementRootWidget.cpp:209-212) so zero is never presented as data — a convention any lifted per-stage rate must respect.

CORRECT SEQUENCE: add a per-stage rate to FLBFactoryUIProductionStageSnapshot and FLBManagementStagePresentation, populate it in the subsystem projection (reusing the 3600/slowest-cycle derivation, and labelling it as a nominal rate wherever it sits beside the measured factory figure), render it in RefreshStageCard, verify both strips on screen, and only then delete the Canvas DrawFlowStrip — carrying DrawAlertToast (LBOneFactoryProductionHUD.cpp:431-439) into UMG first, since that is the mockup's alert toast and it lives in the same doomed file. Deleting the Canvas strip before that lift removes the only working per-card throughput and the only alert toast in the game.

### camera / camera pitch / tilt control (was: absent)

Camera pitch / tilt control: PARTIALLY EXISTS, not absent.

Absent only in the specific place that matters for the mockup — the OneFactory management pawn. ALBManagementPawn (the OneFactory DefaultPawnClass, LBOneFactoryGameMode.cpp:71) binds no pitch axis (LBManagementPawn.cpp:1131-1152), rotates yaw-only in Tick (`AddActorWorldRotation(FRotator(0.0f, RotateInput * 48.0f * DeltaSeconds, 0.0f))`), never sets bUsePawnControlRotation on its boom (ctor :933-938), and hard-assigns the boom pitch to -35 deg in five places (:938, :1419, :1442, :1637, :1967) plus -32 deg via the framing contract (LBManagementPawn.h:104, set at LBManagementPawn.cpp:1471, applied :1613). SetAutomationCamera takes yaw and zoom but no pitch (LBManagementPawn.h:227).

But the capability is already built twice in this module and can be lifted rather than invented:
- ALBPaintShopManagementPawn::OrbitPitch (LBPaintShopManagementPawn.cpp:285-297) is a finished clamped management-camera pitch orbit: -80 to -10 deg clamp (:26-27), 70 deg/s rate (:29), -32 deg default boom (:24, :51-53), bUsePawnControlRotation = true (:55), bound to the existing LB_ControlRoomLookPitch axis (:97-98) with LB_CameraReset restoring framing (:101-102). It is the DefaultPawnClass at LBPaintShopPrototypeGameMode.cpp:19.
- ALBBodyShopManagementPawn also binds LB_ControlRoomLookPitch (:117-118, impl :280-283) with a pitch-following boom (:62), so the "bound only by ALBControlRoomPawn" statement is incorrect; ALBControlRoomPawn's clamped +/-35 deg version is at LBControlRoomPawn.cpp:159-162 / :228-231 with the clamp as an EditDefaultsOnly UPROPERTY (LBControlRoomPawn.h:87).
- The axis mappings already exist project-wide (Config/DefaultInput.ini:50-52, Up/Down/Gamepad_RightY), so no input config change is needed.
- On the OneFactory path, pitch is already settable from the console: `LB.OneFactory.View <Dept>@<distanceScale>~<pitchDegrees>` and `LB.OneFactory.Tour ... Press@0.25~16` parse and clamp pitch to 2-88 deg (LBOneFactoryDevFactoryCommands.cpp:610, :617-625), build the eye from it (:738-742) and set the spawned camera as view target (:795).

Genuinely absent with zero prior art: any orthographic / near-isometric projection. Grep for Orthographic, ProjectionMode, OrthoWidth, SetOrtho across Source/LineBossCarFactory and Config returns no hits, so the mockup's near-isometric look can currently only be approximated by narrowing FOV (management camera is 48 deg at LBManagementPawn.cpp:943; the dev framing camera uses 78 deg at LBOneFactoryDevFactoryCommands.cpp:704).

### camera / map lighting authority (one RectLight) vs a daylit shop (was: partial)

Corrected state: PARTIAL, but for different reasons than the claim gives. The map file is not the lighting authority — it is a deliberately minimal container, and the shop's lighting is built in C++ at runtime and is executed on every commission and every load.

What actually exists and runs:
- EnsureDevLighting (LBOneFactoryDevFactoryCommands.cpp:436-585): movable 5000 K DirectionalLight key at (0,0,20000)/(-48,35,0); per-department PointLight grids from the live route at Z=1400, 68,000 lm, ~one lamp per 18 m bay, 2..12 per axis, a quarter shadow-casting; SkyLight at Z=8000, 1.5, SLS_CapturedScene + RecaptureSky. Idempotent under tag LB.OneFactory.DevLighting.
- Invoked automatically at intensity 9.0 from LBOneFactoryPlayerController.cpp:210 via EnsureSitePresentation, driven by CommissionFactory on the B key (:67-68, :118) and by LoadFactory (:401); console alias LB.OneFactory.Light at LBOneFactoryDevFactoryCommands.cpp:1308-1322.
- 28 authored SM_Lamp01 fixtures each get a 15,000 lm / 2,200 cm no-shadow point light (LBOneFactoryDevRestoredShopActor.cpp:241-256).
- Fixed exposure bias -0.50 is applied on the management camera lens itself, blend weight 1.0 (LBOneFactoryDevFactoryCommands.cpp:781-792), so the map's unbound volume is a floor, not the sole control.
- The mockup's clerestory window band is built: a 420 cm E8F0FA glazing band with 0.2 emissive running unbroken under the eaves (LBOneFactoryDevEnvelopeActor.cpp:36, :198, :329-338; .h:68-70).
- Tools/build_site_lighting.py authors a calibrated sun (5800 K, pitch -42, yaw -35, intensity 2.2-3.0 tuned against the pinned exposure, 4 cascades to 900 m), SkyAtmosphere, real-time-capture SkyLight and ExponentialHeightFog, plus 28 yard masts with spots off by default; Tools/Diagnostics/probe_map_lighting.py is the probe that found the two map authorities and the script refuses to save if either is disturbed.

What is genuinely still short of the mockup's daylit shop:
- The sun/sky pass is not currently persisted in the shipped package: the umap contains no LB.Site.Lighting, DirectionalLight, SkyLight, SkyAtmosphere or fog actors and only ~24 actor descriptors, so neither the sun nor the 5,049 site actors are in the level on disk. That is consistent with the same doc's 2026-08-17 "start from scratch with empty buildings, populate press first" direction change (SITE_AUTHORED_IN_EDITOR_2026-08-17.md:164-176) and the pre-site backup kept at E:\LineBossValidationOutput\MapBackups\...pre-site.umap (:232-236). So it is a deliberate reset, not an absent capability — but as the game stands the clerestory band is emissive geometry with no daylight actually entering through it.
- The interior read is point-light pools, not the mockup's even soft daylight: the floor band measures 37.4/255 against the audit's own 40 target with 39.2% dark fraction (PRESS_SHOP_RELEASE_AUDIT_2026-08-16.md:60-62).
- The frozen 32-RectLight v002 contract (8x4 grid, 48,000 lm, 5000 K, 6000 cm attenuation, 4200x700 cm faces, DirectionalLight 0.30 / SkyLight 0.20) remains unexecuted and Content/LineBoss/Factory/OneFactory/v002 does not exist — that part of the claim stands, but it was superseded by the landed point-light rig rather than left as the only plan.
- The whole rig is runtime-spawned and never saved, so opening the map or starting without pressing B leaves the shop lit only by the single RectLight. That, not an absent lighting system, is the real gap: the lighting is not authored into the level, and the mockup's daylight needs a persisted sun plus glazing that transmits it.

### loop / persistent top bar (whole HUD shell) (was: partial)

ELEMENT: persistent top bar (whole HUD shell)
CORRECTED STATE: partial — but for a different reason than claimed.

WRONG: "bManagementVisible defaults to false ... A fresh game therefore shows NO HUD at all until the player presses M." The shell opens itself at boot. ALBManagementPawn::BeginPlay calls HUD->OpenFactoryBuild() whenever the map has no legacy operations console (LBManagementPawn.cpp:989-995), backed by a one-shot Tick bootstrap for the packaged case where the pawn beats the HUD into existence (LBManagementPawn.cpp:1025-1041, comment: "so the clean game always opens with a visible mouse catalogue"). OpenFactoryBuild sets bManagementVisible = true (LBControlRoomHUD.cpp:2212-2214). Both game modes use that pawn (LBGameMode.cpp:220, LBOneFactoryGameMode.cpp:71). A passing automation test asserts it: LBManagementHUDTests.cpp:294 "Clean player-builder opens its catalogue on boot", with the fixture first proving zero operations consoles in the world (LBManagementHUDTests.cpp:283-289). M is a toggle, not the only way in.

ALSO WRONG: the implication that the top strip is page-gated. SetManagementContext collapses only FlowTrayBorder and ContextBorder (LBManagementRootWidget.cpp:908-913); TopStripSizeBox is built once (LBManagementRootWidget.cpp:429-442) and never appears in any SetVisibility call. So on the FactoryBuild landing page the top strip is on screen and the flow tray is the part that is collapsed.

WHAT IS ACTUALLY TRUE (the real gap): the shell is one monolithic widget whose lifetime is bound to the modal page system, so it vanishes on two ordinary interactions rather than never appearing.
 - Single widget, single visibility switch: created and collapsed at LBControlRoomHUD.cpp:1223-1228; driven wholesale by SyncModernOverviewWidget (LBControlRoomHUD.cpp:1474-1487) off IsModernManagementActive (LBControlRoomHUD.cpp:1241-1245).
 - It closes on player action: LBControlRoomHUD.cpp:2756 (selecting an installed stage's actor), 2781 (starting placement from a stage card), and 3150/3158/3174 (starting machine/storage/infrastructure placement from the catalogue in the live ConfirmManagementAction). This is deliberate and tested — LBManagementHUDTests.cpp:305 "Catalogue closes for practical floor placement" — so during placement the top bar, cash, order counter, speed controls and alert bell all disappear, leaving only the pawn's Canvas placement card (LBManagementPawn.cpp:862-918).
 - It also closes on the M toggle (LBControlRoomHUD.cpp:2199) and CloseManagement (LBControlRoomHUD.cpp:2245), with no Canvas fallback: the entire Canvas persistent strip carrying HEALTH / ALERTS counters is dead code inside #if 0 (LBControlRoomHUD.cpp:858-1159), and ALBControlRoomHUD::DrawHUD is two calls with no drawing (LBControlRoomHUD.cpp:4034-4037).

SEPARATE ALWAYS-ON SURFACE THAT DOES EXIST (easy to miss): ALBOneFactoryProductionHUD, installed by ALBOneFactoryGameMode (LBOneFactoryGameMode.cpp:72) and swappable at runtime via console LB.OneFactory.HUD (LBOneFactoryDevFactoryCommands.cpp:1709-1725), derives from ALBControlRoomHUD and draws a bottom production-flow strip plus alert toasts every frame with no bManagementVisible check (LBOneFactoryProductionHUD.cpp:271-305; strip 308-424; toasts 431-457; no-factory top banner 288-299). That is genuinely persistent, but it is Canvas-drawn placeholder art (engine small/large fonts, no thumbnails, "ON LINE / DISPATCHED / ALERTS" at LBOneFactoryProductionHUD.cpp:329-336) and it duplicates rather than feeds the UMG shell.

WORK REQUIRED: split the top strip and the flow tray out of ULBManagementRootWidget's modal page system into a separately-visible always-on layer, so they persist through placement, selection and the M toggle; and retire the parallel Canvas strip in ALBOneFactoryProductionHUD in favour of that layer instead of running two flow presentations side by side.

### loop / cash / issued / sim-rate top strip (dead implementation) (was: partial)

ELEMENT: cash / issued / sim-rate top strip
CORRECTED STATE: still partial, but for entirely different reasons — the Canvas code cited is deliberately retired, not stranded, and its content is already live in UMG.

What actually exists (live, compiled, wired):
- ULBManagementRootWidget::BuildTopCommandStrip (LBManagementRootWidget.cpp:427) builds a real top strip: nav buttons BUILD/PRODUCTION/ANALYTICS/SETTINGS (:499-529), an order pill "MODEL  n / n issued" (:530-537, refreshed :949-958), a cash readout formatted £x.xxm (:540-547, FormatMoney :130-137, refreshed :960-962), PAUSE/PLAY/2X transport buttons (:580-594), and an alert counter that turns amber (:597-603, refreshed :963-970).
- The transport buttons are functional, not decorative: RequestSimulationRate (:1252-1254) → OnSimulationRateRequested → ALBControlRoomHUD::HandleModernSimulationRateRequested (LBControlRoomHUD.cpp:1611-1620) → ULBOneFactoryOperationsSubsystem::SetSimulationRate.
- A separate always-on Canvas layer does exist, drawn by the subclass HUD that the OneFactory game mode installs (LBOneFactoryGameMode.cpp:72; LBOneFactoryProductionHUD.cpp:271-311, alert toast :431-457).

The real remaining gaps against the mockup:
1. Not persistent. The whole UMG shell — cash, issued, transport, alerts — is gated on `bManagementVisible`, which defaults to false (LBControlRoomHUD.h:236) and is only flipped by ToggleManagement (LBControlRoomHUD.cpp:2199) bound to LB_ToggleManagement (LBControlRoomPawn.cpp:194, LBManagementPawn.cpp:1142); SyncModernOverviewWidget collapses the widget whenever management is closed (LBControlRoomHUD.cpp:1476-1490, gate at :1243-1245). The mockup's strip is always on over the world. The always-on Canvas layer that IS drawn (ALBOneFactoryProductionHUD) contains no cash, no issued counter and no sim-rate figure — only "ON LINE / DISPATCHED / ALERTS" (LBOneFactoryProductionHUD.cpp:331-333). So the fix is to surface the cash/issued/rate block outside the management gate, not to resurrect the `#if 0` block.
2. No numeric speed readout. The mockup shows a "1x" figure beside the transport buttons; the UMG strip has only three discrete buttons labelled PAUSE/PLAY/2X (LBManagementRootWidget.cpp:582-594) and nothing anywhere displays `Snapshot.EffectiveSimulationRate` in a live path — the "SIM %.1fx" text exists only inside the dead block (LBControlRoomHUD.cpp:990-1001).
3. No iconography. Every strip element is a text label or text button: no company mark, no hamburger, no factory/clipboard/chart/trophy/gear glyphs, no bell icon on the alert counter.
4. No progress bar on the issued counter in the strip; the issued progress bar exists only on the Orders page (LBManagementRootWidget.cpp:1107-1115), whereas the retired Canvas strip had one inline (LBControlRoomHUD.cpp:980-983).
5. The retired block also carried a world-space alert marker projected from `TopAlert->MarkerWorldLocation` (LBControlRoomHUD.cpp:1046-1060) that has no UMG equivalent; if that pointer-into-the-world behaviour is wanted it must be rebuilt, since the source is fenced out and undeclared.

Correct framing for planning: treat LBControlRoomHUD.cpp:827-854 and 858-1159 as deleted-in-place reference material (they cannot be called — no header declarations), and scope the work as (a) hoisting the existing UMG strip out from behind `bManagementVisible`, (b) adding a live rate readout, icons and an inline issued progress bar to BuildTopCommandStrip, and (c) optionally re-implementing the world-space alert marker.

### loop / alert toast over the world (was: absent)

CORRECTED STATE: partially present — a working world-space alert toast ships on the current integration-target map, but not on the configured default map, and it falls short of the mockup's fidelity in three specific ways.

What exists and is reachable today:
- `ALBOneFactoryProductionHUD::DrawAlertToast` (LBOneFactoryProductionHUD.cpp:431-459) draws stacked toasts over the 3D view: 470x34 units scaled, anchored bottom-right at `X = Width - ToastW - 20*Scale`, `Y = Height - 132*Scale - 14*Scale - ToastH` (lines 445-448), i.e. immediately above the production-flow strip; deep-charcoal panel at 0.94 opacity with a 3px yellow left stripe (lines 454-455); newest-first, capped at three (line 450-451).
- It is installed two ways, not one. (i) `ALBOneFactoryGameMode` ctor, HUDClass at LBOneFactoryGameMode.cpp:72 — and that game mode IS referenced by a map: `LB_MoorcrossWorks_OneFactory_v001.umap` applies it as a local WorldSettings override, documented at CLAUDE.md:129-131 and confirmed by `LBOneFactoryGameMode` + `DefaultGameMode` in the map's import table. (ii) `LB.OneFactory.HUD` console command, LBOneFactoryDevFactoryCommands.cpp:1692-1727, which swaps it into any running world.
- It composes with the management shell rather than replacing it: `ALBOneFactoryProductionHUD : public ALBControlRoomHUD` (LBOneFactoryProductionHUD.h:55-57) and `Super::DrawHUD()` at LBOneFactoryProductionHUD.cpp:272 keeps `ULBManagementRootWidget` drawing underneath.
- Locked by test: LBOneFactoryTests.cpp:236-238 asserts the HUD class, with the comment at 231-235 recording the 2026-08-16 contract change that removed the need for a console swap.

Real gaps against the mockup (the actionable residue):
1. Default-map coverage. DefaultEngine.ini:2-4 boots Press v913 under `LBGameMode`, whose HUDClass is the plain `ALBControlRoomHUD` (LBGameMode.cpp:221). On that path the only alert surface is the "n alerts" text label (LBManagementRootWidget.cpp:597-604, 963-971) — no toast. The ControlRoom HUD's own world-marker alert callout, which had severity colour, a leader line and a title/id label, is dead code under `#if 0` (LBControlRoomHUD.cpp:858-1101), as is the click-to-jump handler (826-853), even though `ALBManagementPawn::JumpToTopFactoryAlert` is still live (LBManagementPawn.cpp:1991-2007).
2. No severity, despite the data existing. The toast signature takes `TArray<FString>` (LBOneFactoryProductionHUD.h:77); `CollectGroups` synthesises those strings from the coordinator/ledger (LBOneFactoryProductionHUD.cpp:225-252) and never touches `FLBFactoryUIAlertSnapshot`, whose Severity/Title/Detail/MarkerWorldLocation fields sit unused by this renderer at LBFactoryUIStateSubsystem.h:26-35. The stripe is hardcoded `Yellow` (line 455), so a Critical alert looks identical to Information.
3. No warning-triangle glyph — the mockup's icon is substituted by a 3px rect (line 455) — and text is hard-truncated at 78 characters (line 456), so the mockup's "Panel stillages waiting for transfer press." style message survives but longer coordinator reasons clip.

Net: this element should be graded "partially present, wrong default path, severity unwired", not "absent". The cited evidence at LBOneFactoryProductionHUD.cpp:431, LBFactoryUIStateSubsystem.h:27 and LBManagementRootWidget.cpp:601 is accurate; the inference drawn from LBOneFactoryGameMode.cpp:72 ("no map or config references it, so it never ships") is contradicted by the project's own CLAUDE.md and by the map package itself.

### loop / placement feedback surface (was: absent)

Correct state: PARTIAL — authored and tested, but disabled by two engine-contract breaks, not by missing work.

What exists (live, non-debug, shipping-compiled):
- Full placement feedback card with Title / state marker / CAUSE / NEXT corrective action / controls hint / accent colour, fed by every placement OutReason. FLBPlacementCardData LBManagementPawn.h:57-70; BuildPlacementPreviewStyle LBManagementPawn.cpp:270-330 (prerequisite pass-through at :320-323); BuildPlacementCardData :432-462; DrawPlacementCard :862-916; per-frame refresh at :2265, :2342, :2249/2369/2448/2570.
- Delivered via HUD actor overlay (AddPostRenderedActor LBManagementPawn.cpp:996 and :1034 -> PostRenderFor :1014-1019), which is orthogonal to bManagementVisible, so hiding the shell during placement is by design, not the defect.
- Ghost tint red/amber/green (:778-798) and world-space tick/cross glyph (:180-210) already give non-textual state feedback.
- Covered by automation tests, LBManagementPawnPreviewTests.cpp:120-140.

Why nothing appears on screen (the real, two-line defect):
1. AHUD::DrawActorOverlays is the only caller of PostRenderFor and is gated on bShowOverlays — C:/Program Files/Epic Games/UE_5.8/Engine/Source/Runtime/Engine/Private/HUD.cpp:646. bShowOverlays is never assigned anywhere in Source/ or Config/, so it stays false.
2. ALBControlRoomHUD::DrawHUD (LBControlRoomHUD.cpp:4034-4038) overrides without calling Super::DrawHUD(), so AHUD::DrawHUD never runs. ALBOneFactoryProductionHUD derives from ALBControlRoomHUD (LBOneFactoryProductionHUD.h:55-57), so its Super::DrawHUD() at LBOneFactoryProductionHUD.cpp:273 terminates at that override. Under both installed HUDs the overlay pass is unreachable. (Same override also skips AHUD::DrawHUD's HitBoxMap.Reset().)

What genuinely is absent, narrowed:
- Success text never surfaces. ConfirmPressTrainPlacement (LBManagementPawn.cpp:2174-2188) writes the "PLACED ... WITH N AUTOMATIC LINK(S); ...; N SERVICE WALKWAY TILES" string (LBFactoryMachineBuilderSubsystem.cpp:1981-1984) into PressTrainPlacementReason, then immediately calls ResetPlacementPresentation() at :2185, which blanks the card at :803. There is no post-build confirmation surface.
- The modern shell has no reason field of its own: ULBManagementRootWidget.h declares no placement/reason member, and the only shell code that ever fed an unavailable reason into a detail card (LBControlRoomHUD.cpp:3047, :3069-3071) and drew Inspector.Reason (:1142) sits inside dead #if 0 blocks at :2787-3116 and :858-1159. The pawn card is therefore the only live surface.
- LBControlRoomHUD.cpp:2777-2778 discards the CanPlaceMachine reason when a stage click cannot start placement, so a refusal at click time produces no message at all.

### loop / per-card throughput figure ("18.0/hr") (was: absent)

ELEMENT: per-card throughput figure ("18.0/hr")
CORRECTED STATE: **partial** (not absent) — the figure is rendered per card on the default HUD, but on a different flow row than the mockup-named one.

Two production-flow rows exist and both draw simultaneously in `ALBOneFactoryGameMode`, because `ALBOneFactoryProductionHUD::DrawHUD` calls `Super::DrawHUD()` first (`LBOneFactoryProductionHUD.cpp:273`) and then adds its own strip (line 303):

1. HAS the per-card rate — the seven-group flow strip in `ALBOneFactoryProductionHUD::DrawFlowStrip`. Each card carries a left state stripe, label, station count + "QA GATE", a mean-progress bar, "Running / Waiting / Hold / Idle + n units", and the right-aligned "{0}/hr" bottleneck rate (`LBOneFactoryProductionHUD.cpp:353-425`, rate at 405-413), joined by ">" arrows (line 421). Its groups are Coil intake / Press / Panel stillages / Body weld / Paint / Assembly / Dispatch (`LBOneFactoryProductionHUD.cpp:39-51`).

2. LACKS the per-card rate — the six mockup-named cards in `ALBControlRoomHUD::DrawProductionFlowHUD` (`LBControlRoomHUD.cpp:2788`, reached from the Overview management page at `LBControlRoomHUD.cpp:3766-3771`). These are the cards that actually match the mockup: COIL_INTAKE / BLANK_BUFFER / TRANSFER_PRESS / PANEL_STILLAGES / BODY_WELD / ED_COAT (`LBControlRoomHUD.cpp:2879-2884`), with a real rendered thumbnail via `ResolveProductionFlowThumbnail` (line 2929), a state colour top stripe, selection border, state text and wrapped detail (`LBControlRoomHUD.cpp:3000-3011`). Per card they draw index+name, thumbnail, `Stage.State`, `Stage.Detail` — and no rate, because `FLBFactoryUIProductionStageSnapshot` has no throughput field (`LBFactoryUIStateSubsystem.h:150-163`).

So the accurate gap is narrower and different from what was claimed: the rate is not missing from the game, it is missing from the *mockup-shaped* card set, and the two rows disagree about how many stages the flow has (7 coarse groups vs the mockup's 6 named cards). The real work is not "invent per-card throughput" but "carry the existing bottleneck rate onto `FLBFactoryUIProductionStageSnapshot` and reconcile the two competing flow rows into one" — the maths at `LBOneFactoryProductionHUD.cpp:176-195` is reusable as-is, keyed by `GroupIndexForStage` (`LBOneFactoryProductionHUD.cpp:74-86`) rather than the six stage ids.

Also note for the parent survey: the detail-panel throughput claim IS sound. `LBManagementRootWidget.cpp:1094-1103` shows only a factory-wide `FACTORY GOOD OUTPUT %.1f units/hr` from `Management.ThroughputGoodUnitsPerHour`, Collapsed unless `HasTruthfulThroughput` passes (`LBManagementRootWidget.cpp:209-212`, `LBManagementRootWidget.cpp:826-832`); nothing anywhere prints the mockup's per-selection "14.2 panels/hr". `ALBControlRoomHUD` likewise shows the factory figure or "NO DATA" (`LBControlRoomHUD.cpp:3994`). That sub-element is genuinely absent — but the per-*card* one is not.

### density / packed floor — rendered instance density per department (was: partial)

ELEMENT: packed floor — rendered instance density per department. STATE: partial (verdict unchanged; measurement and cause corrected).

Press is the densest bay, but the gap is roughly 2-7x, not 12-24x, and it is not true that the other three bays are "near-empty" or that press density comes only from a dev manifest actor.

Actual rendered content per bay, from the measured build (Saved/Logs/LineBossCarFactory-backup-2026.08.17-09.13.36.log:1794-1819):
- Press, 41,600 m2: 2,804 manifest instances (log:1794) + ~54 route-dressing instances + 4 complete v449 press-train components placed by the route dressing (LBOneFactoryDevStationDressingActor.cpp:357; log:1795) = ~2,862, or 0.069/m2.
- Body/weld, 18,000 m2: 597 frozen presentation instances (LBOneFactoryBodyWeldStarterPresentationActor.cpp:16) + 18 control cabinets + 2 closure turntables + its share of 393 conveyor sections = ~617+, or ~0.034/m2 (~2x sparser than press).
- Paint, 22,000 m2: 119 presentation instances (LBOneFactoryPaintStarterPresentationActor.cpp:14) + 8 cabinets + ~80 fence panels + conveyor share = ~207+, or ~0.0094/m2 (~7x sparser, not 12x).
- Assembly, 33,600 m2: 95 presentation instances (LBOneFactoryAssemblyStarterPresentationActor.cpp:12) + 24 cabinets + ~240 fence panels + 12 robots + 13 benches + 20 wheel racks + 11 parts carts + 10 lift platforms + 1 EOL arch + 1 alignment bed (LBOneFactoryDevStationDressingActor.cpp:658-698; log:1798-1812) + conveyor share = ~428+, or ~0.013/m2 (~5x sparser, not 24x).

On top of all four bays: 2,261 envelope pieces forming four separate shop buildings with a per-segment clerestory glazing band (LBOneFactoryDevEnvelopeActor.cpp:309-341; log:1818-1819), plus map-authored per-bay floor slabs, columns, roof frame, painted department floor plates and bay safety lines (Scripts/create_one_factory_shell_v001.py:218-296).

The real shortfalls against "the floor is PACKED" are qualitative, not the arithmetic in the original claim:
(a) Composition, not count. The added density in assembly and paint is overwhelmingly perimeter fence and conveyor sections — 721 of the 960 dressing instances are Conveyor 393 + Fence 328 (log:1796-1797) — i.e. linear guarding and track, not the mockup's "multiple parallel cells in organised rows". There is exactly one line per department, never parallel cells.
(b) Paint and Body are deliberately barred from added machinery. The Paint branch places nothing at all (LBOneFactoryDevStationDressingActor.cpp:627-644) and the Body branch places only the closure turntable (:584-626), both by design to avoid z-fighting the frozen presentations. Those two bays are therefore frozen at their contract counts by policy, and raising their density requires a versioned presentation v002, not a dressing change.
(c) Only press has a reference-density source. The manifest path Content/LineBoss/Reference/RestoredShop/shop_manifest.json (LBOneFactoryDevRestoredShopActor.cpp:80-82) exists for press alone; there is no equivalent reference manifest for weld, paint or assembly.
(d) Green painted floor zones exist but only as route stripes and bay boundary lines (route stripes at LBOneFactoryDevStationDressingActor.cpp:855-915; bay lines at Scripts/create_one_factory_shell_v001.py:286-296) — not the mockup's per-cell and per-walkway zoning.

Also correct the paint station-footprint figure: the codebase's own measurement is ~14% of the bay ("paint's bay is nearly seven times its station footprint", LBOneFactoryDevEnvelopeActor.cpp:157-158), not 3.7%.

### density / assembly shop content (24 stations) (was: partial)

ELEMENT: assembly shop content (24 stations)
CLAIMED STATE: partial (state stands; the density accounting behind it does not)

The frozen presentation contract is exactly as described: 10 HISM batches, 95 instances, 24 stations (LBOneFactoryAssemblyStarterPresentationActor.cpp:11-12, per-batch table :491-502, enforced :401-408 and :706-712, tested LBOneFactoryAssemblyStarterPresentationActorTests.cpp:28-32). BuildExpectedPresentationItems (:599-690) adds nothing beyond one skillet carrier, one operation fixture and one status cube per station plus 23 route cubes. All eight AssemblyLineNativeKit_v001 meshes exist and all eight are referenced, so the kit is exhausted.

But 95 is not what the assembly floor renders. ALBOneFactoryDevStationDressingActor is built automatically during normal play, not only from a console command — LBOneFactoryPlayerController.cpp:158-175 spawns it and calls BuildFromRoute from the commission path at :118. Counting its output, the assembly department carries roughly 559 mesh instances, about 23 per station:

- ~130 floor conveyor sections (SM_AssemblyLine01, 240 cm) forming a continuous run between all 24 positions — LBOneFactoryDevStationDressingActor.cpp:758-810; 5 sections per 2200 cm in-row leg (pitch from LBOneFactoryAssemblyStarterLayout.cpp:143-151) plus 20 on the 6000 cm row-turn leg. The prior analysis omitted this entirely; it is the largest single element in the shop.
- 240 SM_Fence_02 guard panels: CellHalf = 520 for every assembly station (:313-314), PanelsPerSide = floor(520 × 1.6 / 143) = 5 (:727-730), both sides (:731) = 10 per station.
- 24 SM_AssemblyLineControl01 HMI cabinets, one per station (:716-718).
- 69 per-stage props from the switch at :656-699 — 33 across the 11 trim stations (robot, bench, parts cart), 1 bench at marriage (position 12), 30 across the 10 rolling-chassis stations (lift platform plus two wheel/tyre racks), 2 at EOL (alignment bed, inspection arch), 3 at dispatch (robot, bench, storage rack). Stage assignment: LBOneFactoryRuntimeCoordinator.cpp:383-400 with marriage at 12 and final inspection at 23 (LBOneFactoryAssemblyStarterLayout.cpp:36,47).
- 1 overhead lamp ramp at the position-23 quality gate (:748-752).
- 23 green painted flow-route stripes in brand green 2F8A5F (:863-931) and one light concrete department apron slab (:819-861).

Corrected list of what is genuinely absent, versus what was wrongly called absent:

Genuinely absent — no mezzanine anywhere in the project (`grep -rni mezzanine Source/` returns nothing); no overhead/inverted carrier conveyor (the run is floor-level); no parallel cells or organised rows (assembly is one serpentine of two 12-station rows); no racking rows comparable to press (one storage rack at position 24 only, :696); no green painted cell or walkway ZONES — ULBFactoryFloorMarkingComponent already defines VehicleLane, PedestrianCrossing, KeepClearHatch and StorageFill (LBFactoryFloorMarkingComponent.h:19-30) but is wired only into LBBodyWeldLineActor, LBECoatLineActor, LBFactoryAGVInfrastructure, LBFactoryBuildMachine and LBPressShopStorageZone, never the OneFactory assembly path. That unwired component is the cheapest route to the mockup's floor zoning.

Wrongly called absent — conveyor runs exist (~130 sections); aisle/route definition partly exists (green flow stripes, department apron, and a 240-panel guard line at ±1222 cm bounding every cell); per-station service/HMI cabinets exist (24). The authored SM_LB_ServiceCabinet_1800_v001 also exists but never reaches assembly: ALBFactoryEnvelopeSideDressingActor is hard-pinned to the old press clean-shell frame, X -9000 to +9000 at 2000 cm pitch, Y ±5810 (LBFactoryEnvelopeSideDressingActor.cpp:20-21, 114-152), while assembly sits at X 4000-28200, Y 5500 and 11500.

Remediation framing also corrected: extra density needs neither new commissions nor a new import. Content/Meshes already holds 869 pack meshes and the dressing Kinds table (LBOneFactoryDevStationDressingActor.cpp:40-49) registers only 10 of them.

### density / paint shop content (8 stations) (was: partial)

ELEMENT: paint shop content (8 stations)
STATE: partial

The frozen paint presentation renders exactly 119 instances across 22 visible batches out of 24 components (LBOneFactoryPaintStarterPresentationActor.cpp:12-14, enforced :785-791 and :1169-1174) inside a 220 x 100 m bay (LBOneFactoryTypes.cpp:160-162, X -1000..21000, Y -13500..-3500). All eight stations sit on the single line Y = -8500 at X = 0 / 1700 / 3400 / 4800 / 6600 / 8800 / 10500 / 11800 (LBOneFactoryPaintStarterLayout.cpp:63-86): a 118 m ribbon roughly 12 m deep, leaving ~92 m of bay past the last station, ~10 m before the first, and the 100 m bay depth essentially untouched. No parallel cells, no second line, no cross-aisle content.

But 119 is not the whole shop. The dressing skips only paint PROCESS modules (LBOneFactoryDevStationDressingActor.cpp:627-643, "Deliberately no process modules here"); its `break` leaves the switch at :701 and every paint station then receives the shared dressing at :703-812 — a control cabinet (:716), a two-sided fence run of 5 panels per side at the paint pitch (:725-744 with CellHalf clamped to 520 at :313), a lamp ramp at the paint quality gate (:748-752), and conveyor sections to the next station (:758-810) — plus the Paint department apron (:815-861) and the green route stripes (:863-931). Paint supplies 8 route steps at the canonical transforms (LBOneFactoryRuntimeCoordinator.cpp:319-356), so that is ~105 further instances, built on the normal player commission path (LBOneFactoryPlayerController.cpp:158-176), with ~55 bay point lights over Paint from the dev lighting grid (LBOneFactoryDevFactoryCommands.cpp:500-556). Real occupancy is therefore roughly double the 119 figure, though it is dominated by 80 thin fence panels and 60 rail cubes, so the bay still reads sparse.

Binding is also not complete: PretreatmentWashTunnel and FlashOffTunnel are assigned to batches (:702-703) but contracted to 0 instances (:877-878) — the reason only 22 of 24 batches are visible — so the station called PretreatmentWash shows dip tanks and rails, never a wash tunnel.

The unused remainder is far larger than 6 blockouts plus 2 stairs: ~21 authored meshes, including the commissioned SM_LB_Paint_EDDipTunnel_v001 (reachable only via LB.OneFactory.PaintEDPreview, LBOneFactoryDevFactoryCommands.cpp:1467-1523, and a never-placed dressing kind at LBOneFactoryDevStationDressingActor.cpp:74-76), 3 overhead-carrier blockouts, 4 beacon parts, oven fan/door/light, 2 floor-marking guides, 4 oven modules, ProxyBIW and NoRail_Middle_v002. Those blockouts are the asset set of ALBECoatLineActor (LBECoatLineActor.cpp:149-169), a complete 189 m 15-bay ED line with carriers, beacons and markings (LBECoatLineActor.h:425-436) sold in the control-room build HUD as "COMPLETE 189 m ED / E-COAT LINE" (LBControlRoomHUD.cpp:742) — a denser implementation that exists and runs, but which OneFactory bars from the Moorcross map as a map-owned production class (LBOneFactoryTypes.cpp:482; asserted absent at LBOneFactoryTests.cpp:384).

Gap to the mockup: the mockup's packed parallel cells, racking rows, mezzanines and cross-aisles are absent in Paint; what exists is one centred line with generic fencing, plus a richer ED line implementation parked outside this map.

### density / multiple parallel press cells in organised rows (was: absent)

ELEMENT: multiple parallel press cells in organised rows
CORRECTED STATE: partially exists (visually present and player-reachable; simulated per-cell only in the press-shop game mode, not in the OneFactory route)

DETAIL: The "absent / no data path" verdict is wrong twice over.

Visually, four complete parallel press train rows already stand in the OneFactory world on the normal player path. LBOneFactoryDevStationDressingActor.cpp:357 loops `TrainIndex < 4`, placing the complete v449 train-row mesh (path at :51-52) at `FVector(-2200.0 * TrainIndex, 0, 0)` from the ConfigurablePressTrain datum (:366-369); the comment at :345-347 says so explicitly, and cites the reference 2200 cm grid (identity plates at Y 0/2200/4400/6600). Reached by pressing B: LBOneFactoryPlayerController.cpp:68 binds B to CommissionFactory → :118 EnsureSitePresentation → :172 `Dressing->BuildFromRoute` (plus the 2,804-instance manifest at :191). No console command and no shipping guard involved. Three lanes of four stillages are laid between the row lines at :405-418.

As a commissioning path, four press cells are a first-class, tested feature: LBFactoryMachineBuilderSubsystem.cpp:942-959 permits four and refuses only the fifth ("THE FOUR AUTHORED PRESS TRAINS A-D ARE ALREADY INSTALLED", :959); PlaceMachine :1789-1798 → ULBPressTrainIdentitySubsystem::PlaceTrain (LBPressTrainIdentitySubsystem.cpp:332), which allocates TRAIN_A..TRAIN_D (:37-46, :20-25) and rejects overlapping protected envelopes (:386-393), forcing separated parallel bays. The 1500 x 7284 cm envelope (LBPressTrainAStation.cpp:49-55) is exactly what makes a 2200 cm row pitch work four times. Player input is bound: LBManagementPawn.cpp:1148 (`LB_BuildPressTrain`) with Config/DefaultInput.ini:24 mapping it to B, ghost preview :696-711, validity :2295-2296, commit :2174-2181. Supporting systems are all multi-train: HUD count and "SELECT NEXT AVAILABLE PRESS TRAIN" (LBControlRoomHUD.cpp:3919-3934), per-train AGV handoff index 0-3 (LBFactoryMachineBuilderSubsystem.cpp:1127-1145, :1097; LBCoilAGVController.h:79), whole-set save/restore (LBPressTrainIdentitySubsystem.cpp:135-160), console train selection (LBControlRoomOperationsConsole.cpp:211-260). Tests: LBFactoryMachineBuilderSubsystemTests.cpp:851-859, LBPressTrainIdentitySubsystemTests.cpp:167, and LBFactoryConnectionSubsystemTests.cpp:21-22 (`LineBoss.FactoryBuilder.Transport.FourPressTrainsPhysicalBranchedFlow`).

And this is the project's default entry point, not a side branch: Config/DefaultEngine.ini:2-4 boots LB_PressShop_RebuildFromLorry_v20260810_v913 under LBGameMode, which installs ALBManagementPawn + ALBControlRoomHUD (LBGameMode.cpp:220-221). That map ships four authored row datums LB_CLEAN_DATUM_TRAIN_A..D (tags LB.ReferenceDatum.TRAIN_A..D); LB_PressShop_FullFactoryRestored_v001.umap ships four live actors PersistentLevel.LBPressTrainAStation_0..3 with PRESS_TRAIN_A..D_BAY build bays, PRESS_TRAIN_A..D_UTILITY spines, four identity boards and per-train lighting. LBPressTrainAStation.cpp:1512-1513: "A combined Press Shop contains four copies of that presentation".

One factual error in the original evidence: the manifest does not contain four trains. Parsing shop_manifest.json (2,804 actors), the only train-family meshes are the four identity plates SM_CA_MW_PressTrainIdentity_A/B/C/D_v396 at Y 0/2200/4400/6600. The visible train bodies come from the dressing actor's v449 loop.

THE REAL GAP (what the original claim was groping at, stated accurately): the four rows visible in the OneFactory frame are inert. Rows B-D are UStaticMeshComponents with collision disabled and navigation off (LBOneFactoryDevStationDressingActor.cpp:373-376) — no station, no throughput, no state. The OneFactory route commissions exactly one ConfigurablePressTrain (LBOneFactoryPressStarterLayout.cpp:274) and ValidateStarterLayout is frozen at 7 stations / 6 routes (:311). LBOneFactoryProductionHUD.cpp contains no reference to trains at all, and LBOneFactoryTests.cpp:377-378 asserts the OneFactory world seeds zero ALBPressTrainAStation. So the correct finding is not "build a multi-cell press feature" — that feature exists, capped at four, with identity, logistics routing, HUD surface, persistence and tests — it is "the OneFactory route and its HUD do not use it": rows B-D need real stations wired into the OneFactory station route and flow HUD, or the OneFactory route needs to adopt the press-shop builder's four-train stack.

### density / shop content is spawned at runtime, not authored as actors in the editor (was: absent)

PARTLY CORRECT ON FACTS, WRONG ON CONCLUSION. Corrected finding: the playable map is shell-only, but the press shop's density is editor-authored as real saved actors in a separate reference map, and the runtime spawn is a replay of that authoring - not a code-defined substitute for it.

What holds. LB_MoorcrossWorks_OneFactory_v001.umap (Content/LineBoss/Factory/OneFactory/v001/Maps/, 272,679 bytes) saves exactly: ten HISM shell actors (FloorSlabs, CutawayWalls, Columns, OpenRoofFrame, Grid100cm, SafetyLines, and four per-department floors), LB_OF_ENV_LightingAuthority_5000K_v001, LB_OF_ENV_FixedExposureAuthority_v001, LB_OF_PlayerStart_Management_v001, LB_OF_ManagementCamera_Overview_v001, LB_OF_NavBounds_FactoryEnvelope_v001, six bay/spine datum TargetPoints plus LB_OF_INTERFACE_CoilReceiving_v001 and LB_OF_INTERFACE_FinishedVehicleDispatch_v001, LB_OneFactoryBootstrap_v001, LB_OneFactory_PressBuildAuthority_v001. No station, machine or presentation actor is saved. No __ExternalActors__ directory exists under Content, so nothing is hidden in One-File-Per-Actor form. The shell-only rule is enforced twice: ALBOneFactoryGameMode::ValidateBootstrapContract at Source/LineBossCarFactory/LBOneFactoryGameMode.cpp:88 (the claim cited :84), and the authoring script itself - Scripts/create_one_factory_shell_v001.py:785-819 pins an exact actor-label set, :897-905 rejects any /Script/LineBossCarFactory. actor except the bootstrap and press authority, :909-916 rejects any label or tag containing "WIP", "Machine", "Station", "Robot" or "CellActor". Runtime spawning is real: Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:121 (EnsureSitePresentation) and Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp:1401 (SpawnActor for the press presentation) are both accurate citations.

What does not hold: "editor authoring is absent" and "density cannot be art-directed by eye - only by editing C++ tables".
- Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap is 11,284,166 bytes, with 7,286 "StaticMeshActor" occurrences and ~4,060 distinct LB_-prefixed actor labels - individually placed coil barcode plates (LB_COIL_BARCODE_V039_*), coil trace panels, HMI text panels, crane girders, guarding. That is the press shop at full density, authored and saved as real actors in the editor.
- Content/LineBoss/Reference/RestoredShop/shop_manifest.json is a bake of that map: "map": "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001", "datum": [3850.0, -4300.0, 0.0], 2,804 actor rows across 1,139 unique mesh paths, each row carrying its own per-slot "mats" overrides. The 2,804 instances the claim attributes to code are these rows.
- Source/LineBossCarFactory/LBOneFactoryDevRestoredShopActor.cpp:37 (BuildFromManifest) loads that JSON at :84-85 and batches it; the comment at :131-133 states "the reference map authors per-actor overrides - aged RAL1023 on the crane girders, brand smooth/layered sets on the guarding".
- Docs/OneFactory/ONE_FACTORY_CONTINUOUS_BUILDING_DECISION_2026-08-16.md:18-41 records this as the deliberate lane: the reference map is "a protected authored input" and "a one-time, read-only editor pass extracted every non-train static-mesh actor" into the manifest. So the press art-direction loop is: open LB_PressShop_FullFactoryRestored_v001, move meshes by eye, re-bake the manifest. No C++ edit.

Narrower true version of the C++ claim: it applies to the other three shops, not press. Weld, paint and assembly layouts are hardcoded native tables - Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterLayout.cpp (854 lines), LBOneFactoryPaintStarterLayout.cpp (763), LBOneFactoryAssemblyStarterLayout.cpp (616) - with FVector literals in their presentation actors (press 180, paint 24, weld 21, assembly 5). The mockup depicts the press shop, which is the one shop whose density is editor-authored.

Also worth separating from the density question: the building envelope genuinely is runtime engine primitives and is documented as a stopgap. Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.h:21-25 - "Everything below is engine primitives sized from the live station route, spawned at runtime and never saved... A permanent envelope belongs in the map or in an authored native kit. This exists so the factory can be looked at and judged now." LBOneFactoryDevEnvelopeActor.cpp:15 loads /Engine/BasicShapes/Cube. The two most recent commits (2d901c7 "Stand press, weld, paint and assembly as separate shop buildings", b4714bb "Size each shop from its authored buildable bay") kept that runtime-cube approach while switching to per-department bays. That is the real gap against the owner's authored-in-editor direction - the walls and roof of the four shops, not the shop-floor density.

Two other claimed details are slightly off: the shell has 20 safety-line strips, not 24 (Scripts/create_one_factory_shell_v001.py:286-303 - four bays x four edges, plus four spine strips), and neither of the two shell-only reference maps is a counterexample: LB_PressShop_RebuildFromLorry_v20260810_v913.umap (the GameDefaultMap per Config/DefaultEngine.ini:2-3) saves only floor, four walls, 24 perimeter columns, 12 roof beams, walkways, 20 lights and four train datums, and Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap saves only LB_BS_ENV_* shell geometry, grid, lights, two interface datums and LB_BodyShop_PrototypeBootstrap_v001.

### density / mezzanines and gantries (was: absent)

CORRECTED STATE: mezzanines are absent; gantries and overhead structure are PRESENT in all four departments, though thin and machine-scoped outside the press bay.

MEZZANINES — genuinely absent. Zero occurrences of "mezzanine" in any source, script, doc or data file. No occupiable elevated deck, no stairs to one, in any department. The Fab platform kit that would build one is present and 100% unused: SM_IndustrialPlatform (5 variants), SM_HeavyPlatform, SM_PlatformGrill, SM_PlatformRailing (7), SM_PlatformPillar, SM_FloorStairs, SM_Ladder (2), SM_HeavyArch (4) in Content/Meshes — 0 references in Source/, 0 in shop_manifest.json. The nearest thing to an elevated walk surface is machine-mounted, not architectural: 4 x SM_CA_MW_PR010_ServiceWalkwayRailSection_v102 at Z=195 with 4 access hatches at Z=222 on the PR010 shuttle roof, and the 0.62 m stepped service platforms baked into SM_LB_BWF_ServicePlatforms_v001 inside the weld framing fixture.

GANTRIES / OVERHEAD STRUCTURE — present, and richer than the prior analysis found:

PRESS (dense, release-grade): ALBOneFactoryDevRestoredShopActor stands 382 manifest actors above 4 m — 12 x 40 m wide-span trusses at Z=1740, a complete overhead travelling crane (42 bridge girders at Z=1500, 4 runway beams at Z=1435, 4 end trucks, 2 trolleys, 30 T hoist, hook block, powered C-hook), 14 metal beams, 81 overhead pipe runs, 28 high-bay lamps. This is deliberately exempted from the roof-hide toggle (LBOneFactoryDevFactoryCommands.cpp:865-877) and the shop walls were raised to 2200 cm eaves to contain it (LBOneFactoryPlayerController.cpp:151-155). It stands automatically on the gameplay path, not via console.

PAINT: 6 ED carrier gantry bays, one over each dip tank, described in code as "the carrier gantry the bodies hang from" (LBOneFactoryPaintStarterPresentationActor.cpp:69-78, 289-293, 898-901).

ASSEMBLY: 3 heavy marriage gantries + 3 EOL inspection arches (LBOneFactoryAssemblyStarterPresentationActor.cpp:495-497), the arch spanning the line at end-of-line (LBOneFactoryDevStationDressingActor.cpp:688-689).

WELD: 2 overhead tooling bridges at Z=3.30 m baked into every framing fixture instance (SM_LB_BWF_OverheadBridge_Front/Rear inside SM_LB_BodyWeld_FramingFixture_v001; imported bounds reach Z=404 cm).

CROSS-DEPARTMENT: SM_AssemblyLineLampRamp (5.88 m tall, 7.88 m span) at every quality gate — which fires in weld, paint and assembly but never in press, since press stations pass bQualityGate=false.

THE REAL GAP against the mockup, restated accurately: it is not that overhead structure is missing, it is that it is UNEVEN. The press bay reads as a real high-bay shop with trusses and a crane at 15-17 m; weld, paint and assembly have only per-machine gantries and arches at 3-6 m under a bare 22 m wall with a flat unarticulated roof deck (ALBOneFactoryDevEnvelopeActor builds walls, dado, clerestory and one solid deck per shop — no trusses, no purlins, no crane rails, no roof frame). So the three downstream shops lack SHOP-SCALE overhead steelwork and any crane, and no department anywhere has a mezzanine. The fix is to extend the per-department bounds the envelope actor already computes into per-shop truss/crane-runway grids, and to spend the idle Fab platform kit on mezzanines over the service edges.

