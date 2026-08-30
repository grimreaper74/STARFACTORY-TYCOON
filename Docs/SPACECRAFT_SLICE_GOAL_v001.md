# PERSISTENT GOAL — spacecraft vertical slice, autonomous build v001

**Goal:** finish the vertical slice defined in
`SPACECRAFT_VERTICAL_SLICE_CONTRACT_v001.md`: one factory the player builds
on the grid, one Scout-01 contract, a serial line that runs on the clock,
the hover test, dispatch, money — playable, saved, and evidenced.

**Status: OPEN — being worked autonomously.** Every item lands with a green
`LineBoss.Spacecraft.*` suite (indexed report) before it is ticked. Owner
check-ins can redirect at any time.

## Done (evidence in Saved/Automation/*, all green)
- [x] Production vocabulary: data-driven stage table, component BOM,
      Scout-01 recipe with craft envelope
- [x] Grid build authority: 100 cm snap, overlap/bounds, commissioning,
      route derived from placement, validate-before-restore
- [x] Production ledger: contract offer→accept, demand-driven units,
      WIP cap, hover-test quality gate, dispatch settlement, deadlines
- [x] Runtime coordinator: cycle-time flow, occupancy holds, auto/manual
      hover test, route-topology-checked runtime saves
- [x] Game mode + LB.Spacecraft.* console commands + WIP presenter
      (placeholder blocks; craft mesh from Assembly; mirror-only)
- [x] Craft-size ladder law: Mk1 station capacities refuse bigger craft
      with "LARGER STATION MARK REQUIRED" (Scout is the SMALLEST craft)
- [x] `LB_SpacecraftFactory_v001` map + headless -game journey to revenue
      (`Saved/Logs/sc_game_journey_v002.log`)

## Remaining, in order
- [x] **Save/load** DONE: `FLBSpacecraftSavePipeline` (one slot, schema
      versioned, refuses to save invalid state, rollback-safe load),
      LB.Spacecraft.Save/Load commands; mid-flight round trip restores
      exactly and the loaded factory runs on to complete its contract.
      Suite 22 green (`Saved/Automation/SpacecraftSaveLoad_v001`).
- [x] **Dispatch fly-away + hover-bob** DONE: at Testing the craft rises
      600 cm off the rig and bobs (the hover test, visibly); on dispatch it
      climbs and flies out of the building over 4 s instead of blinking
      away. Proven by LineBoss.Spacecraft.Presentation.HoverBobAndDispatchFlyAway.
      Suite 23 green (`Saved/Automation/SpacecraftFlightPresentation_v002`).
- [x] **Minimal HUD** DONE: `ULBSpacecraftTopBarWidget` — native UMG top
      bar (cash / active contract progress / sim clock / line status),
      logic in pure testable statics, honest empty states ("£--",
      "NO FACTORY") when authorities are absent, spawned by the game mode
      only where a real viewport exists. Suite 25 green
      (`Saved/Automation/SpacecraftHUD_v001`).
- [x] **Phase-1 Nanite-vs-LOD measurement** DONE (PRELIMINARY): identical
      30-instance maps, 900-frame CSV captures, RTX 4070 SUPER. Raw Nanite
      masters (32.5M source tris in view) cost the SAME GPU time as the
      decimated LOD0 scene (3.51 vs 3.50 ms mean; Lane A p95 smoother).
      "Models too big" is quantitatively unsupported on dev hardware.
      Receipt: `Saved/Audits/Phase1NanitePerf_v001/`. Outstanding: min-spec
      + packaged confirmation, mover/VSM probe.
- [x] **Meshy guard reversal**: EXECUTED 2026-08-24 — 17 files, build green,
      196 tests pass (touched suites all green; 8 pre-existing car-era
      failures documented), OneFactory boots to PREBUILT_READY. Receipt:
      `Saved/Audits/MeshyProvenanceReversal_v001/RECEIPT_v001.md`.
- [x] **Packaged journey**: DONE 2026-08-24 — BuildCookRun Development
      package, journey green headless AND rendered (D3D12/RTX 4070S).
      "Packaged playable" for the dev-command journey at this revision.
      Receipt: `Saved/Audits/SpacecraftPackagedJourney_v001/RECEIPT_v001.md`.
      Still open: player-input journey, Shipping config, packaged save/load.
- [x] **Phase-2 seam 1 — item/inventory ledger**: DONE 2026-08-24 —
      `ALBSpacecraftInventoryAuthority` + 35-item Phase-2 catalogue
      (6 raw / 8 processed / 15 sub-parts / 6 assembled components
      mirroring the BOM). Atomic fail-closed mutations, validate-
      before-restore snapshots. 28/28 LineBoss.Spacecraft green:
      `Saved/Automation/SpacecraftInventory_v001/index.json`.
- [x] **Phase-2 seam 2 — multi-recipe stations**: DONE 2026-08-24 —
      `ALBSpacecraftCraftingAuthority` + 29-recipe chain across 9 station
      families (slice 5 + RollingMill, CircuitFab, ElectronicsStation,
      PowerCellPlant, PropulsionStation, SubAssemblyRobot). Table validated
      for CHAIN COMPLETENESS (every non-raw item producible, raw never
      craftable); class-matched selection; atomic craft cycles with
      same-store freed-volume accounting; integration test walks raw ore
      to an assembled Hull component. 32/32 green:
      `Saved/Automation/SpacecraftCrafting_v001/index.json`.
      Still open: recipes are data-only until the runtime coordinator and
      build authority adopt the new station families (placement defs,
      cycle ticking, presenter blocks).
- [x] **Phase-2 seam 3 — power draw/budget**: DONE 2026-08-24 —
      `ALBSpacecraftPowerAuthority`: honest integer-kW budget, no brownout
      simulation - over-budget loads and load-stranding supply removals are
      REFUSED with named reasons. 34/34 green:
      `Saved/Automation/SpacecraftPower_v001/index.json`.
- [x] **Phase-2 seam 4 — one research branch**: DONE 2026-08-24 —
      `ALBSpacecraftResearchAuthority`: 4-tier Manufacturing branch gating
      the six new station families (slice five stay free); content-only
      unlocks per the owner's plan; prerequisite-closure-validated saves.
      36/36 green: `Saved/Automation/SpacecraftResearch_v001/index.json`.
- [x] **Phase-2 integration (core)**: DONE 2026-08-24 — game mode spawns
      all seven authorities and binds the research placement gate into the
      build authority; save schema v2 carries all seven snapshots
      (FLBSpacecraftSaveContext, incomplete contexts refused, rollback
      restores everything); the catalogue splits five route families
      (0 kW, envelope law) from six crafting families (real kW draw, zero
      envelope, bRouteRequired=false so the slice still commissions);
      PlaceStationPowered removes a station whose draw cannot connect;
      five new dev commands (Power/Grant/Research/Deposit/Craft).
      39/39 green (`Saved/Automation/SpacecraftPhase2_v003/index.json`);
      live -game loop proves power->research->deposit->craft and the
      honest lock refusal (`Saved/Logs/sc_phase2_journey_v001.log`).
- [x] **Phase-2 integration (rest, part 1)**: DONE 2026-08-24 —
      CARGO-01 recipe in the canonical catalogue (21 x 11.2 x 5.8 m
      placeholder pending the owner's tier sizes; Mk1 route refuses it
      with LARGER STATION MARK REQUIRED - the honest EA state until Mk2
      marks); HUD top bar shows PWR draw/supply and RSC points/unlocks
      (honest placeholders when authorities are absent); TickCrafting
      gives stations sim-time cycles - progress accrues ONLY while the
      exchange is payable, items move at completion, stalls are named,
      remainder carries, impossible cycle clocks refuse to restore.
      41/41 green: `Saved/Automation/SpacecraftPhase2Rest_v002/index.json`.
- [x] **Phase-2 integration (rest, part 2)**: DONE 2026-08-24 (night) —
      PowerPlant (1500 kW supply) and StorageRack (2000-unit store,
      "Store.<StationId>") as research-free infrastructure definitions;
      static PlaceStationPowered/RemoveStationPowered wire supply, store
      and draw in order and UNWIND whole on any failure (no half-connected
      stations; stranding-supply and stocked-rack removals refused);
      RemoveStation only de-commissions when a ROUTE station leaves;
      inventory gains fail-closed RemoveStore; SelectStationRecipe is
      record-derived and research-gated; TickCraftingStations runs every
      selected station on the sim clock inside LB.Spacecraft.Run; new
      LB.Spacecraft.Place/Select commands; presenter mirrors crafting
      stations (assertion added). 43/43 green:
      `Saved/Automation/SpacecraftPhase2Part2_v001/index.json`; live
      chained floor (plant->research->mill; steel->plate; 8 cycles while
      the Scout dispatched): `Saved/Logs/sc_phase2_journey_v003.log`.
- [x] **Mk2 station marks + Cargo flow**: DONE 2026-08-24 (night) —
      `StageClassId` on definitions: commissioning, routing and the save
      validator accept ANY mark of a stage class, and the capacity law
      reads the PLACED mark; five Mk2 route definitions (envelopes fit the
      21 m Cargo placeholder; self-powered like all route marks pending an
      owner decision) gated behind `Research.Mfg.Mk2` (prereq T2);
      coordinator now spawns the recipe of the OLDEST accepted contract
      with demand (a Cargo contract on an Mk1 line never spawns and never
      halts); `StartRecipeContract` prices from the recipe;
      `LB.Spacecraft.Start [qty] [recipeId]` + new `LB.Spacecraft.Commission`.
      45/45 green: `Saved/Automation/SpacecraftMk2_v001/index.json`.
      LIVE: player-built all-Mk2 line dispatches CARGO-01-000001 for
      12,000,000 pence — `Saved/Logs/sc_cargo_journey_v001.log`.
- [x] **Repackage + dual packaged journeys**: DONE 2026-08-24 (late) —
      `Builds/SpacecraftSlice_v002`; Scout canonical AND player-built Mk2
      Cargo journeys both green inside the packaged exe (5,000,000 /
      12,000,000 pence, exit 0). "Packaged playable" for both journeys at
      this revision. Receipt:
      `Saved/Audits/SpacecraftPackagedJourney_v002/RECEIPT_v001.md`.
- [x] Tier size DECIDED (owner, 2026-08-25): Cargo-01 = 1.5x Scout
      (21.0 x 11.2 x 5.8 m) - the shipped numbers stand.
## Day batch 2026-08-25 — real station meshes into the game
Owner ran Meshy on the first three concept renders (RollingMill,
PowerPlant, StorageRack — intaken and hashed in
`SourceAssets/Candidate/Spacecraft/StationModels_MeshyIntake_v001/`) and
asked for autonomous continuation. The goal for today:

- [x] Concept renders for all 8 Phase-2 buildings (batch 1 + 2 delivered);
      Meshy prompts delivered; 3 model blends intaken with sha256 +
      read-only inspection.
- [x] **Derivative pass**: DONE — 6 FBX (LOD0 ~120k / LOD1 ~40k), scale
      baked, grounded, textures embedded; report
      `station_runtime_export_v001.json`.
- [x] **Unreal import**: DONE — 6 meshes with materials/textures, all
      bounds `fits=True` in-engine; cook root added both trees.
- [x] **Presenter meshes**: DONE — real mesh binds per DefinitionId
      (PowerPlant/RollingMill/StorageRack), honest one-line placeholder
      fallback for families without models.
- [x] Build green; 45/45 suite (`StationMeshFallback_v001`) + presenter
      suites 10/10 zero-warning post-import (`StationMeshBound_v001`);
      receipt `Saved/Audits/StationMeshes_v001/RECEIPT_v001.md`; staged.
- [x] **Station animations** (owner request, from work): code-driven
      ambient accents on real-mesh stations — the PowerPlant wears a slow
      rotating, pulsing energy ring; crafting stations get a status beacon
      that PULSES only while a recipe is actually selected (read from the
      crafting authority, never invented) and glows dim when idle; accents
      are swept with their stations. Pure animation maths unit-tested.
      46/46 zero-warning: `Saved/Automation/StationAccents_v001/index.json`.
- [x] **Chicane departure** (owner request, from work): after the hover
      test the dispatched craft flies one S-weave chicane (banking through
      the turns), then goes full pelt (quadratic acceleration) down the
      length of the factory line and exits. Deterministic pure-maths
      trajectory (`ComputeDepartureOffsetCm`) unit-tested: weave crosses
      both ways and returns to centreline, sprint is accelerating and
      clears the factory length. 46/46 zero-warning:
      `Saved/Automation/ChicaneDeparture_v001/index.json`.
- [x] **Runway + red strobes** (owner request, from work): every placed
      test rig lays a 100 m runway down the sprint's -Y axis — white edge
      lines, centreline dashes, threshold piano keys, and 8 pairs of RED
      strobes chasing toward the exit (aviation warning language, not a
      brand colour). Mirror-only, swept with its rig. Strobe chase maths
      pure and unit-tested (exactly one hot pair, advancing exit-ward).
      47/47 zero-warning: `Saved/Automation/RunwayStrobes_v001/index.json`.
      Refined same day (owner): strobes are an EVENT — dark until 0.8 s
      before throttle-up, chase through the sprint, dark after the flight
      (`ComputeStrobeArmClock`, unit-tested; `StrobeArm_v001` 47/47).
- [x] **Fitting drones + charging docks** (owner request, from work):
      every crafting station gets two worker drones, each with its own
      charging dock at a station corner. Drones fly a breathing fitting
      orbit (half a turn apart, hover bob) ONLY while the station has an
      active recipe, ease back to their docks over 1.4 s when it idles,
      and a dock pulses warm orange while its drone charges on it.
      Mirror-only, crafting families only (plants/racks/route stations
      excluded), swept with their station. Orbit maths pure and
      unit-tested. 48/48 zero-warning:
      `Saved/Automation/FittingDrones_v001/index.json`.
- [x] **Chassis derivative** (owner request, from work): the Scout-01
      bottom skin cut from the same master with the same transform bake
      (aligned to the full ship), 60k/25k LODs, imported and bounds-checked
      (12.6 x 4.3 x 1.16 m). The WIP form ladder is now crate ->
      CHASSIS at Hull Fabrication (wearing the hull material) -> full
      craft at Assembly, with honest crate fallbacks. Live log proves
      "chassis mesh bound". 48/48 zero-warning:
      `Saved/Automation/ChassisForm_v001/index.json`.
- [x] **Full build-form ladder** (owner request, from work): the Meshy
      PART-SEGMENTATION master was classified by geometry (hull, three
      symmetric pairs = wings/fins/pods, canopy = top unpaired part) and
      composed into cumulative forms aligned to the ship's exact box:
      Airframe (hull+pairs, 90k/35k) and Fitted (all but canopy,
      110k/40k). The WIP ladder is now crate -> chassis -> airframe ->
      fitted -> full craft, each rung falling DOWN honestly. All three
      forms verified bound in-engine. 48/48 zero-warning:
      `Saved/Automation/BuildForms_v001/index.json`; export report
      `Scout01_RuntimeDerivative_v001/Evidence/buildforms_export_v001.json`.
- [x] **Drone designs + drone power** (owner request, from work): four
      concept renders delivered for Meshy (Spray, Assembly, Heavy
      Transport with clamped crate, Lift with winch-suspended part).
      NEW `ALBSpacecraftDroneFleetAuthority`: two drones per crafting
      station with 0..1 batteries — flight drains (180 s per charge),
      reserve at 15% recalls them, docking charges (60 s full) and each
      charging dock is a REAL 25 kW grid load; no headroom = no charge
      (honest stall, proven by test). Save schema v3 carries the fleet;
      presenter mirrors battery-aware flying state; LB.Spacecraft.Run
      ticks the fleet; Status reports flying/charging. 51/51 zero-warning:
      `Saved/Automation/DroneFleet_v001/index.json`.
- [x] **Player UI v1** (owner request, from work): the game is now
      playable WITHOUT the console. `ALBSpacecraftPlayerPawn` (proven 2.5D
      camera contract: pitch -35, FOV 48, zoom clamps, WASD/rotate; mouse
      cursor; grid-snapped placement ghost, F rotates, Home cancels;
      cursor->floor picking is pure maths, no collision needed) +
      `ULBSpacecraftCommandPanelWidget` (native UMG, code-only: BUILD tab
      lists research-unlocked stations with price/kW and arms placement;
      clicking a placed station opens its recipe list + remove; CONTRACTS
      tab commissions the line and accepts Scout/Cargo offers; RESEARCH
      tab spends points on nodes). Every fail-closed refusal string is
      surfaced verbatim as the toast - the authorities ARE the feedback.
      The game mode now ticks production/crafting/drones on REAL time, so
      a live session plays without LB.Spacecraft.Run; the top bar was
      re-rooted in a canvas (no more full-screen tint risk). Pure snapping
      /picking/label maths unit-tested. 52/52 zero-warning:
      `Saved/Automation/SpacecraftUI_v001/index.json`; live boot smoke
      `Saved/Logs/ui_smoke_v001.log`.
      NOT yet in the UI: station costs are DISPLAYED but not charged
      (needs the owner's starting-capital decision); no save/load menu
      (console Save/Load still work); contract offers are the two fixed
      recipes, not a generated offer board (see contract ideas doc).
- [x] **Localization groundwork** (owner directive, 2026-08-25: "the
      game must be translated into the main languages"): the whole current
      player-facing surface (HUD top bar, command panel, pawn hints) is
      now LOCTEXT-based with FText::Format for parameterised strings
      (locale-aware number grouping); 11 cultures staged in
      DefaultGame.ini (en source + fr/it/de/es/pt-BR/pl/ru/ja/ko/zh-Hans).
      52/52 zero-warning: `Saved/Automation/Localization_v002/index.json`.
      REMAINING (tracked): GatherText commandlet run + PO generation +
      first-pass translations; catalogue display names (stations, recipes,
      research nodes) to string tables; fail-closed refusal strings to
      reason codes so the toast localizes while logs stay greppable
      English; a language picker in the UI.
- [x] **Blue thruster flames + RCS-to-mains handover** (owner request,
      from work): the live craft now burns flames — four belly RCS cones
      during the hover test and through the chicane (using the test bay's
      authored blue afterburner plume material, blue-shape fallback), and
      three rear MAIN engine cones that spool 0.4 s before throttle-up
      and take over as speed builds while the belly fades out by a
      quarter of the sprint (`ComputeThrusterMix`, pure, unit-tested).
      Flames flicker, ride the craft through bank and bob, transfer from
      hover into the departure, and are swept with the flight. 52/52
      zero-warning: `Saved/Automation/ThrusterFlames_v001/index.json`.
      (The test-bay map's static plumes were already authored blue.)
- [x] **Money loop v1** (vision priority 1, owner-endorsed): the game
      has stakes. PROVISIONAL starting capital 600,000 GBP (labelled for
      owner retuning); ledger-backed placements charge the catalogue
      price FAIL-CLOSED before anything is placed (every wiring failure
      refunds whole; "INSUFFICIENT FUNDS" is the toast); contract
      settlements pay into cash; removal refunds a PROVISIONAL 50%;
      the HUD shows cash, not raw revenue; ledger validation forbids
      negative cash; save schema v4. Dev/test paths without a ledger stay
      free (rigs unchanged). 53/53 zero-warning:
      `Saved/Automation/MoneyLoop_v001/index.json`.
- [x] **Contract depth v1** (vision priority 2, owner-endorsed):
      DEFECT PENALTIES - each failed hover test deducts 10% from that
      unit's settlement, capped 30% (PROVISIONAL; retest test proves the
      90% payout); REPUTATION - new ALBSpacecraftReputationAuthority
      (+2 points per completed contract, credited exactly once, tiers
      1-4 at 0/10/25/50, all PROVISIONAL), recipes carry MinReputationTier
      (Scout 1, Cargo 2) enforced fail-closed on player-facing contract
      acceptance with a remedy-naming refusal ("DELIVER CONTRACTS TO
      BUILD YOUR NAME"); synced on the live tick and in Run; in Status;
      saved in schema v4 with once-only-credit validation. 54/54
      zero-warning: `Saved/Automation/ContractDepth_v001/index.json`.
- [x] **Resource orders v1** (vision priority 3, first half): raw
      materials are BOUGHT, not conjured — six purchasable raws with
      PROVISIONAL prices (iron 4,000 pence .. titanium 12,000), orders
      charge cash fail-closed up front (refund on any refusal), arrive on
      the sim clock (30 s + 2 s/10 units), and a full store HOLDS the
      delivery until space frees (goods never vanish). SUPPLY section on
      the contracts tab (order buttons + pending list with countdowns),
      `LB.Spacecraft.Order` command, saved in the inventory snapshot with
      full validation. 55/55 zero-warning:
      `Saved/Automation/ResourceOrders_v001/index.json`.
      Remaining half of priority 3 (noted): the transport-drone DELIVERY
      VISUAL flying dock->store on arrival.
- [x] Remaining buildings intake (2026-08-25 evening session): Circuit
      Fab, Power Cell Plant, Propulsion Station and the twin-robot
      Sub-Assembly cell all intaken, exported, imported fits=True and
      presenter-bound — SEVEN of eight station slots carry real Meshy
      meshes. Only ElectronicsStation (12 x 9 m) remains.
- [x] Drone model intake AND runtime pass (2026-08-25): four masters
      (one Meshy batch), NEW split-and-tilt lane removes concept base
      plates and carves fan pods with centre pivots (CargoLift is a
      hexacopter: 6 pods; quads: 4). 22 assets imported, envelope
      checks green; fitting drones now render the real Assembly body
      with four pods tilting into flight (pure ComputeFanTiltDeg,
      tested). PROVISIONAL sizes: Assembly/Spray 1.2 m, Winch 1.5 m,
      CargoLift 3.0 m. CargoLift reserved for the transport-logistics
      visual. 55/55 zero-warning:
      `Saved/Automation/DroneMeshes_v001/index.json`.

- [x] 2026-08-25 evening/night mega-batch (owner live + remote):
      textures root-caused and fixed (deterministic material pass, 36
      assignments), drones at EVERY station (owner: "needs the lot"),
      pause menu (Esc), readable UI, 240 m floor + walls + dock apron +
      sky, auto-connect conveyor visuals, six-game research workflow ->
      Docs/CONVEYORS_SCALE_PLAYABILITY_RESEARCH_v001.md, owner approved
      implementing it: ALBSpacecraftTransportAuthority (supply belts,
      fail-closed, 1.4x belted crafting, drone-pace fallback), starter
      spine boot, save schema v5 (+ fixed the v4 live-save regression),
      Scout parts list (31 models) ->
      Docs/SCOUT01_PARTS_LIST_v001.md. Suite 56/56 zero-warning
      (`Saved/Automation/TransportBelts_v002`). Ship part-segmentation
      intaken: build forms v002 assemble from real part boundaries.
- [x] PALETTE DECIDED (2026-08-25 night): B Cold Steel; factory
      neutral, ships wear customer liveries. No conveyors on station
      models. Internals shared across tiers.
- [x] **QA/rework loop LANDED 2026-08-27** (autonomous night): the hover
      test can now FAIL on workmanship the craft collected from
      understaffed stations, and a failure opens rework in the same act
      so the line can never deadlock at the gate. The craft is delivered
      late and 10% cheaper. The owner's quad-carry to a rework bay is
      still deferred - rework currently happens in place, and the
      Winch/CargoLift drones remain the intended transport when the bay
      exists. Suite 74/74; see Docs/AUTONOMOUS_NIGHT_2026-08-27_v001.md.
- [ ] Owner decisions pending: title, route-mark power draw, old-map
      deletion plan, camera verdict (2.5D + cinematic launch cameras
      recommended), belt v003 click-to-click port routing.

## Autonomous night 2026-08-27 - loop-blockers cleared

Six read-only audits against the early-access scope, each surviving gap
adversarially re-checked, then fixed in order of how badly they broke the
loop. Research points can be earned, a Cargo order no longer bricks the
line, a craft costs the components it is made of, an idle factory earns
nothing, buying a third drone no longer makes the game unsaveable, and
the packaged build finally boots into this game. Full account with
evidence and open questions: `AUTONOMOUS_NIGHT_2026-08-27_v001.md`.

## Release scope (owner directive, 2026-08-24, refined)
**The wishlist / early-release build targets PHASE-2 SCALE content: ~15
buildings, ~30 chain items, Scout + Cargo tiers, storage/AGV logistics,
power system, one research branch.** Path: Phase-1 measurement → Meshy
guard reversal → Phase-2 engine seams (item/inventory ledger, power,
research content, multi-recipe stations) → Phase-2 content + models →
palette chosen → packaged journey → wishlist material. The full ~32
building catalogue stays post-early-access.

## Content scale (owner directive, 2026-08-24)
The slice catalogue is NOT the game's scope. The full-game plan is
`SPACECRAFT_CONTENT_CATALOGUE_v001.md`: ~32 building types (with Mk1-Mk3
marks), ~70-item production chain, 6 craft tiers — phased in after the
slice, through the existing data seams (recipe registry, stage table,
station catalogue, component BOM, capacity marks).

## Waiting on the owner (not blocking the above)
- Palette choice (P1–P4); title/brand; tier craft sizes (Cargo…Experimental)
- Meshy station models (4 prompts delivered) → swap into the presenter

## Standing rules for the autonomous run
Supersede-never-edit; fail closed with named reasons; suite green with an
indexed report before any tick; sync worktree→main tree before building;
honest status vocabulary; no Unreal editor left running after a step.
