# Validation evidence

Snapshot: **2026-08-12**. This file records the latest working-session evidence;
the documentation update itself did not rerun Unreal, UBT, cook or packaging and
does not upgrade editor evidence to packaged-playable status.

## Current Shipping build milestone

The exact current revision successfully produced:

`Builds/PlayerBuildable_v1031/Windows/LineBossCarFactory.exe`

The full Shipping BuildCookRun passed and the first isolated runtime observation
found no TCP listener, UDP endpoint or new firewall rule. The visible firewall
dialog was preserved stale v1030 Development state. Exact hashes, timestamps and
limitations are recorded in [the v1031 Shipping handoff](V1031_SHIPPING_HANDOFF.md)
and [the firewall runtime audit](../../Saved/Audits/ReleaseGate/v1031/Shipping_Firewall_Runtime_Audit.md).

This proves compile/cook/package/archive and the listener surface only. It does
not yet prove the complete new-game, populated-factory, save/restart,
accessibility or performance journeys.

## Prior interactive packaged proof

The latest package with preserved completed automation-bridge interaction is:

`Builds/PlayerBuildable_v1029/Windows/LineBossCarFactory.exe`

The package's automation-bridge state proves, for **v1029 only**:

- map `LB_PressShop_RebuildFromLorry_v20260810_v913` loaded;
- six player-built machine authorities, one press train and three storage zones;
- an active 40-panel production order;
- persistent machine/order/alert state and camera/selection projection;
- four docked support-fleet units; and
- coil-AGV telemetry.

Evidence:

- [`state.ready`](../../Builds/PlayerBuildable_v1029/Windows/LineBossCarFactory/Saved/AutomationBridge/state.ready)
- [selected-machine screenshot](../../Builds/PlayerBuildable_v1029/Windows/LineBossCarFactory/Saved/AutomationBridge/sessions/20260811T123203Z-31716-2C102408/screenshots/03-selected-machine.png)
- [selected-storage screenshot](../../Builds/PlayerBuildable_v1029/Windows/LineBossCarFactory/Saved/AutomationBridge/sessions/20260811T123203Z-31716-2C102408/screenshots/04-selected-storage.png)

That package predates the latest livery, stillage-FLT and management-authority
work. It is not evidence for those changes and is not the current release
candidate.

## Archived focused editor reports

| Report | Result | What it proves / does not prove |
|---|---:|---|
| [`ManagementAuthorityCombined`](../../Saved/Automation/ManagementAuthorityCombined/index.json) | 3 passed, 0 failed | Exact finance/research/upgrade atomicity, quality/maintenance/OEE calculations and management-state validation/migration at that revision. Does not prove the later v17 campaign or seven-page UI integration. |
| [`StillageFLTCombined_v3`](../../Saved/Automation/StillageFLTCombined_v3/index.json) | 4 passed, 0 failed | Component rear steering, stacking/fleet/save contracts covered by that archived suite. The later live repaired gate also passed these four tests and the exact physical handoff, but has not yet been exported as an indexed report. |
| [`PanelStillageThreeHighCombined`](../../Saved/Automation/PanelStillageThreeHighCombined/index.json) | 1 passed with 4 synthetic-world teardown warnings | Three-high storage contract. Warnings must be eliminated or formally accepted before release. |
| [`FactoryBrandFinal_20260811`](../../Saved/Automation/FactoryBrandFinal_20260811/index.json) | 2 passed, 0 failed | Branding save/livery logic in editor. Not packaged. |
| [`Management_v1029_final`](../../Saved/Automation/Management_v1029_final/index.json) | 8 passed, 0 failed | The older v1029 management HUD/interaction scope. It does not cover the source-present seven-page management layer. |
| [`AutomationBridge_v1029_final`](../../Saved/Automation/AutomationBridge_v1029_final/index.json) | 5 passed, 0 failed | Automation protocol/commands for v1029 source. |
| [`PhysicalStillageFLTExactHandoffCollisionTrace_v4`](../../Saved/Automation/PhysicalStillageFLTExactHandoffCollisionTrace_v4/index.json) | **1 failed (historical)** | This archived run collided with hidden `InboundCraneRunwayVisual`; weld intake received zero. The repaired current source later passed the exact handoff through live MCP. Keep this report as regression history, not as the current-source diagnosis. |
| [`WholeShopV16Combined`](../../Saved/Automation/WholeShopV16Combined/index.json) | **1 failed (historical)** | The v16 campaign round trip, purchased FLT capacity/jobs, disk load and legacy v15 migration failed at that revision. The final live five-test gate passed both v17 campaign round trips; a new indexed report is still required. |

`Saved/Automation/CoilFLTRearSteerCombined` contains no machine-readable
`index.json`; its directory name is not a pass.

## Live Unreal MCP editor results

The UE 5.8 experimental MCP integration is documented in
[Unreal MCP editor operations](UNREAL_MCP_OPERATIONS.md). The initial handshake
is preserved in [`UnrealMCP.log`](../../Saved/Logs/UnrealMCP.log); repaired-gate
and runtime evidence is in
[`UnrealMCP_Rerun2.log`](../../Saved/Logs/UnrealMCP_Rerun2.log) and
[`UnrealMCP_Rerun3.log`](../../Saved/Logs/UnrealMCP_Rerun3.log). The final
management/campaign capability session is preserved in
[`UnrealCapabilityEnablement.log`](../../Saved/Logs/UnrealCapabilityEnablement.log),
and the final startup, Live Coding, AGV and support-robot session is preserved in
[`UnrealCapabilityFinal.log`](../../Saved/Logs/UnrealCapabilityFinal.log).

### Latest full compile, broad regression and live UI evidence

The latest complete `LineBossCarFactoryEditor Win64 Development` build succeeded:
**18 actions in 55.65 seconds**. This supersedes the earlier 13-action compile as
the current compile result. It is still not a cook, package, packaged journey or
archived release-build transcript.

The earlier 13-action build (52.12 seconds) and subsequent fixture-only Live
Coding compile remain historical evidence for the AGV repair described below.

| Latest live selection | Result | What it proves / does not prove |
|---|---:|---|
| Focused successor/UI/material-flow gate | **9/9 passed** | Responsive HUD readability, manual save/load double confirmation, actionable placement geometry/reasons, authorised empty-campaign camera framing, visual-tuning contract, train autostart safety and three inbound-delivery/player-built flow cases. Editor evidence only. |
| Broad `LineBoss.Management` | **24/24 passed** | Current management authority, runtime bridges, responsive UI and input/save confirmation contracts. No current package covers this revision. |
| Broad `LineBoss.FactoryBuilder` | **24/24 passed** | Current builder, routing, placement and material-flow regression scope. It emitted one RHI virtual-allocation warning and six synthetic-world no-context teardown warnings; these remain unresolved release evidence. |

The exact focused tests were:

- `LineBoss.Management.HUD.ResponsiveReadability720p1080p`;
- `LineBoss.Management.HUD.ManualCampaignSaveLoadDoubleConfirm`;
- `LineBoss.Management.PlacementPreview.StatusGeometryAndActionableReasons`;
- `LineBoss.Management.Camera.EmptyCampaignFramesAuthorisedBuildBay`;
- `LineBoss.VisualTuning.RuntimeContract`;
- `LineBoss.FactoryBuilder.ConsoleFreeRuntime.TrainAutostartSafety`;
- `LineBoss.FactoryBuilder.MaterialFlow.InboundDeliveryVisibleFourCoilUnload`;
- `LineBoss.FactoryBuilder.MaterialFlow.InboundDeliveryContinuousCycle`; and
- `LineBoss.FactoryBuilder.MaterialFlow.PlayerBuiltModularInboundUnload`.

Five current live PIE captures at 1280x672 are preserved under
[`Saved/Audits/UIUX/20260812_live_pie_successor_v002`](../../Saved/Audits/UIUX/20260812_live_pie_successor_v002).
They prove readable factory identity/livery, improved HUD/catalogue, valid
placement, named invalid obstruction guidance and immediate return to valid
without a stale warning. At that captured revision they exposed distant framing,
missing catalogue imagery/recognisable ghosts and harsh broad shadow bands.
Later source now contains tested authorised-bay framing, hierarchy-based ghosts
and richer decision cards; these later changes still need packaged acceptance.

A bounded follow-up changed only the scoped clean-shell directional-light softness,
then passed an incremental Editor Development build (**5 actions in 20.03 seconds**)
and `LineBoss.VisualTuning.RuntimeContract` (**1/1**, no warnings/errors). The live
1280x720 follow-up is preserved as
[`06_softened_directional_shadow_followup_1280x720.jpg`](../../Saved/Audits/UIUX/20260812_live_pie_successor_v002/06_softened_directional_shadow_followup_1280x720.jpg).
It materially reduces the dark-band dominance, but is still Editor PIE evidence
on a sparse first-build floor rather than populated packaged-factory acceptance.

| Live selection | Result | What it proves / does not prove |
|---|---:|---|
| Repaired press/stillage gate | **11 succeeded, 0 failed** | Six press-train tests, all four `LineBoss.WeldShop.StillageFLT` tests and `PhysicalStillageFLTExactHandoff` passed in `UnrealMCP_Rerun2.log`. This directly supersedes the earlier live 11/13 failure diagnosis for current source. |
| Management runtime bridge, first run | **1 succeeded, 1 failed** | The exact-once restore test exposed that an incomplete order containing rejected panels was rejected by the production save-state validator. The validator was fixed; this failed run is retained as defect evidence. |
| Management runtime bridge, repaired rerun | **2 succeeded, 0 failed** | Both `DeliveredPanelOrderExactOnceAcrossRestore` and `RealStateQualityFaultAndWearBridge` passed in `UnrealMCP_Rerun3.log`. |
| All `LineBoss.Management` tests (earlier selection) | **20 succeeded, 0 failed, 0 warnings/errors** | Historical focused current-editor evidence including four runtime-bridge tests, management authority, seven-page layout/controller parity, persistent HUD, console-free catalogue and UI projection. The later broad 24/24 result above is the current selection. |
| Campaign/material-flow selection | **5 succeeded, 0 failed, 0 warnings/errors** | `InboundCoilToWeldShopStillage`, `PhysicalStillageFLTExactHandoff`, `PlayerBuiltModularInboundUnload`, `PlayerBuiltV17ManagementRoundTrip` and `WholeShopCampaignRoundTrip` all passed in `UnrealCapabilityEnablement.log`. |
| AGV/routes/save selection | **9 succeeded, 0 failed, 0 warnings/errors** | Automatic inbound routing/profile ownership, demo alignment, mixed-profile rebinding, strict player placement/persistence, approved coil-AGV presentation, protected route, runtime and legacy restore all passed in the final runs in `UnrealCapabilityFinal.log`. |
| Support robots/natural motion/docks | **6 succeeded, 0 failed, 0 warnings/errors** | Natural cornering, player-built envelope clearance, automatic charging, CR01 runtime, MR01 runtime and guarded service-dock restore all passed in the final run in `UnrealCapabilityFinal.log`. |

The older 11/11 press/stillage session emitted context-less
`UWorld::DestroyActor` teardown warnings from
`LineBoss.PressShop.PressTrains.Identity.NextAvailablePersistence`. Keep that
warning record as historical evidence for that earlier selection. The four
final 2026-08-12 selections listed above (20 management, 5 campaign/material,
9 AGV and 6 support-robot results) completed with zero test warnings or errors.

Therefore current v17, stillage logistics, press-train, seven-page management
and builder work has fresh **live editor** green evidence. It still lacks standalone
`Saved/Automation/.../index.json` reports and packaged proof. The older indexed
red reports remain valuable regression history, but no longer describe the
latest source outcome.

### Historical AGV failure and current repair

An earlier AGV automation attempt crashed because a stale test world had no
registered world context or build-floor authority. The failed PR002 placement
then reached an unconditional null `CastChecked`. The fixture now owns a scoped
RAII game-world context and valid build authority, and it uses guarded casts and
early returns instead of crashing on a failed placement.

The test exposed a separate production rule conflict: an automatically generated
route endpoint can legitimately touch either machine it connects, while the
public player infrastructure placement path must continue rejecting machine
overlap. The builder now has a private automatic-placement path that exempts only
the route's two connected endpoint machines. The public player path remains
strict for machines, floors, storage and unrelated obstacles. A final fixture
distance correction brought PR002 back inside its valid predecessor-link range;
`LineBoss.FactoryBuilder.AGVInfrastructure.AutomaticInboundRoute` then passed,
followed by the complete 9/9 AGV selection.

`UnrealCapabilityFinal.log` deliberately preserves an intermediate pre-fix
`AutomaticInboundRoute` failure before the Live Coding success and later green
runs. Read the log chronologically; the earlier failure is regression history,
not the final result.

### Historical Editor/tooling handoff state

At the earlier tooling handoff, Unreal Editor PID `2752` was responsive, the MCP listener was bound
to `127.0.0.1:8000`, and 53 toolsets were discoverable. Startup in
[`UnrealCapabilityFinal.log`](../../Saved/Logs/UnrealCapabilityFinal.log) contains
no Game Features startup error after adding the editor-only `GameFeatureData`
Asset Manager scan rule. The one-unsaved-item note applied to that earlier
session only; it is not a claim about the current Editor process or current
asset-save state.

The runtime management analytics store is still append-only and uses linear
history scans. Add a retention/rollup policy before treating long multi-year
factory sessions as scale-proved.

## Evidence hierarchy

For a feature, archive all applicable layers:

1. source/manifest validation;
2. focused automation;
3. affected-system regression suites;
4. full campaign/save regression;
5. cook/package result for the exact revision;
6. packaged new-game journey with screenshots/video and log;
7. packaged save/restart/load/continue journey;
8. performance capture at representative factory scale.

A green component report cannot override a red downstream journey. A package
from an older revision cannot validate later source. A live MCP log is useful
diagnostic evidence, but it must be converted into an indexed, reproducible
report before serving as a release gate.

## Next package gate

The next candidate needs a unique build ID and source/content manifest. At
minimum, preserve:

- build command/result and executable hash;
- automation report bundle with zero unexpected failures/warnings;
- new campaign and factory-profile setup;
- machine/storage/logistics placement with invalid-placement feedback;
- one order from inbound material through physical panel-stillage delivery;
- save, exit, restart, load and continued order completion;
- maintenance due/hold/service and one research/upgrade/purchase/revenue path;
- mouse, keyboard and controller UI journeys;
- 720p/1080p/4K readability captures;
- CPU/GPU/frame-time, memory, actor/draw-call and navigation/pathing stress data;
- crash-free log with no missing runtime assets or fallback substitution.

Only after those artifacts are linked from this file may “packaged playable” be
moved to the new revision.

## 2026-08-24 Press Shop 2126 overhead candidate evidence

This addendum is current for the isolated 2126 overhead candidate only.  It does
not promote the candidate, supersede protected OneFactory authority or upgrade
any package/Steam claim.

### Install and preservation receipt

The v006 installation receipt is
[`install_receipt_v001.json`](../../Saved/Audits/PressShop2126/OverheadPresentation_v006/install_receipt_v001.json),
119,477 bytes, SHA-256
`c0b76461edabd0a455e2a4b2bb47774e797d1817d2c38f3ca4d17054934d380c`.
It records:

- source v005 map: 1,694,902 bytes, SHA-256
  `4d3ce8973cc7bede00f0204a1e653117935cfc9f120fac8b6a939510ad01fe4b`;
- target v006 map: 1,702,094 bytes, SHA-256
  `34840087dad80312c8d7d1e010489fcb277bebfee3597f831aa53d89349ef9ec`;
- 302 source and final actors, 140 source and final presentation actors, 120
  machinery layers plus 26 cargo layers = 146 preserved visual layers;
- zero source actors created/removed, zero machine/cargo transform mutations,
  zero new machinery/cargo geometry, no roof created and no collision enabled
  on presentation geometry;
- identical before/after semantic hashes for machinery
  (`2ff2fd18f353f03676fd3f927e9418ced6bae8d485febbd7988dbaf41a1d0b8f`),
  cargo
  (`8cb3a921423bd8db26bac58f9279f27111e7246aa296d1796ee6fcb6bc01edcc`)
  and all visual-layer actors
  (`ce2b2eb55905bef234f08f2a28e68ce67a4f743deaa4d502a534ea6e72baf86c`).

The protected map hashes matched before and after installation.  The exact-PIE
receipt rechecked the same map set unchanged; the later live-HUD capture again
held target v006, builder v438, legacy v002, OneFactory, playable v001, cargo
v003 and presentation v002 stable:

| Protected package | Stable SHA-256 |
|---|---|
| Builder authority v438 | `5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8` |
| Legacy Steam v002 | `cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0` |
| OneFactory authority | `f4e97b33cdfb1f242b2c606a16b4caa05b74b298fdf1b1263d4a4c46d50e8d5c` |
| Overhead playable v001 | `43020cb3ea7d18a49319da68a04ae1b96d5af0d535c705e947f81d5c005ba7ce` |
| Overhead cargo v003 | `5eae51f2a7d3e1c72deb4fd455d57a6339dee061840b7d062c5ddf680ab6100f` |
| Overhead presentation v002 | `58fe57f3af0dfcf4021d6bbcd3a52d7d66de22187b561fb2db41becd83023275` |
| Source overhead presentation v005 | `4d3ce8973cc7bede00f0204a1e653117935cfc9f120fac8b6a939510ad01fe4b` |

The install receipt's own status deliberately says fresh capture/PIE were
pending at installation time.  The downstream receipts below supply those later
technical results; the install receipt was not rewritten retroactively.

### Exact regular-PIE lifecycle PASS

[`exact_map_pie_receipt_v003.json`](../../Saved/Audits/PressShop2126/ExactMapPIE_v006/exact_map_pie_receipt_v003.json)
is 35,621 bytes, SHA-256
`9c286b5d77dc3cebc0729b9e46d3cd2d07a4e859fa94618c277b22ce757bcf13`.
Its exact status is
`PASS_EXACT_MAP_REGULAR_PIE_NATIVE_PLAYER_ACTIVATION__V002_PRESS_INSPECTION_HOLD_PASS_RELEASE__PALLETISING_OUTBOUND_VISUAL_LIFECYCLE`.
The corresponding engine log is
[`PressShop2126_ExactRegularPIE_v006_v004.log`](../../Saved/Logs/PressShop2126_ExactRegularPIE_v006_v004.log).

The receipt proves regular PIE on the exact v006 map with one native
`LBOneFactoryPlayerController`, one runtime coordinator, the native-player
activation contract, topology `OF_RUNTIME_TOPOLOGY_V002_B326EE78`, all 57 route
steps and the seven-step Press route prefix.  Eleven visual checkpoints cover
inbound lorry unload, coil AGV transfer, wrapped storage, depack, preparation,
S01 transfer, S04 contact, S06-to-inspection transfer, S07 inspection,
palletising and outbound stillage transfer.  The quality gate held the same unit
at `PENDING` with an amber `WAITING` beacon, accepted evidence ID
`OVERHEAD_PRESS_PANEL_INSPECTION_PASS_V002`, and released that same unit to
`OF_PRESS_PANEL_DISPATCH_001` without duplicated WIP.  It also proves 146 bound
visual layers, 26 cargo layers, 14 authored motion ranges, machine-beacon
bindings and post-quality palletising/outbound presentation.

Before/after fingerprints and the dirty-package set were unchanged;
`project_content_mutated=false` and no save/package API was called.  The receipt
explicitly leaves packaged build, performance, Steam capture and human visual
approval false.

### Runtime visual-layer retention repair

The runtime curation fix in
[`LBOneFactoryPlayerBuilderSubsystem.cpp`](../../Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp)
exempts only `ALBPressShopOverheadVisualLayerActor` from legacy candidate-mesh
retirement.  The dedicated current visual layers therefore survive; a generic
candidate actor cannot bypass retirement merely by carrying overhead tags.

The indexed focused report
[`PressShopOverheadRetention_v001/index.json`](../../Saved/TestReports/PressShopOverheadRetention_v001/index.json)
is 2,093 bytes, SHA-256
`6c732cec42cacaa14cb8fba40c41b41e17c3e36eef661336dc8305a6a19f1711`.
`LineBoss.OneFactory.PlayerBuilder.RetiresLegacyPressTrainBeforeNativePresentation`
completed successfully (1/1, 0 failed) and explicitly checks both retention of
the dedicated layer and retirement of the tagged generic actor.  It is
`succeededWithWarnings=1`: two synthetic-world `UWorld::DestroyActor: World has
no context` teardown warnings remain recorded, so this is not a zero-warning
release bundle.
The full run log is
[`PressShopOverheadRetention_v001.log`](../../Saved/Logs/PressShopOverheadRetention_v001.log).

### Live-HUD capture chronology

Five runs are preserved: four failed attempts followed by one technical PASS.
No failed receipt was overwritten or promoted.

| Run | Receipt result | Exact outcome |
|---|---|---|
| [`v001`](../../Saved/Logs/PressShop2126_LiveHUD_SteamCapture_v006_v001.log) / `20260824T023958110789Z` | **FAIL** | The checker wrongly required widget visibility to equal `VISIBLE`; the real top bar and flow strip intentionally use the valid `SELF_HIT_TEST_INVISIBLE` state. This was a checker false fail; no PNG. |
| [`v002`](../../Saved/Logs/PressShop2126_LiveHUD_SteamCapture_v006_v002.log) / `20260824T024648804844Z` | **FAIL** | Probe used unavailable Python `is_hidden` on `LBPressShopOverheadVisualLayerActor`; no PNG. |
| [`v003`](../../Saved/Logs/PressShop2126_LiveHUD_SteamCapture_v006_v003.log) / `20260824T025232849456Z` | **FAIL** | View switch used unavailable Python `set_view_target`; no PNG. |
| [`v004`](../../Saved/Logs/PressShop2126_LiveHUD_SteamCapture_v006_v004.log) / `20260824T025650103440Z` | **FAIL, diagnostic image only** | The loading flush re-entered the registered tick after the first global native request was submitted. Later re-entrant calls saw that request pending and returned false, making the outer path report `native restricted 1920x1080 UI screenshot request was refused`; the bridge did not submit the screenshot twice. A 1920x1080 PNG was nevertheless emitted (2,189,599 bytes; SHA-256 `6fcceb0f879f935286bab5dbb32be85bb65ae22ea2a18016b70c21d79e775034`), but the [receipt](../../Saved/Audits/PressShop2126/OverheadPresentation_v006/LiveHUDSteamCapture/Runs/20260824T025650103440Z/live_hud_steam_capture_receipt_v001.json) screenshot field is null and the overall receipt remains FAIL. |
| [`v005`](../../Saved/Logs/PressShop2126_LiveHUD_SteamCapture_v006_v005.log) / `20260824T030925104578Z` | **Technical PASS** | Explicit `REQUESTING_CAPTURE` re-entry guard; exactly one native request; regular PIE, real RHI, native HUD, one player order and natural S04 `DESCENDING` press state. |

The re-entry repair publishes `REQUESTING_CAPTURE` before
`finish_loading_before_screenshot()` can pump Slate, and nested ticks are a
no-op.  The focused Python contract file
`Scripts/tests/test_capture_pressshop_2126_overhead_presentation_v006_live_hud_pie.py`
passes **24/24**, including a model of the loading-flush re-entry and the
exactly-one-request assertion.

The current technical-PASS receipt is
[`live_hud_steam_capture_receipt_v001.json`](../../Saved/Audits/PressShop2126/OverheadPresentation_v006/LiveHUDSteamCapture/Runs/20260824T030925104578Z/live_hud_steam_capture_receipt_v001.json),
24,200 bytes, SHA-256
`b1f1cf716fdae5111d88588b5101f0b9da4fcecdc67acb499982213de449f660`.
It records `regular_pie=true`, `simulated_editor_session=false`,
`real_rhi=true`, `scene_capture_2d_used=false`, one player `PlaceOrder`, one
native UI screenshot request and zero map/content saves, imports, builds, cooks
or visibility/actor-property mutations.  The top bar and flow strip were owned
by the player and visible.  At capture the natural S04 state was `PRESSING`,
frame `DESCENDING`, with 146 bound visual layers.  The target-map hash remained
`34840087dad80312c8d7d1e010489fcb277bebfee3597f831aa53d89349ef9ec`
and the install-receipt hash remained
`c0b76461edabd0a455e2a4b2bb47774e797d1817d2c38f3ca4d17054934d380c`
before and after.

The corresponding
[`PressShop2126_LiveHUD_SteamHero_1920x1080_v006.png`](../../Saved/Audits/PressShop2126/OverheadPresentation_v006/LiveHUDSteamCapture/Runs/20260824T030925104578Z/PressShop2126_LiveHUD_SteamHero_1920x1080_v006.png)
is exactly 1920x1080, 2,331,974 bytes, SHA-256
`2c062279d1324432e14a6748be41e3ea5cfe7e7a77b1c4ac5bd1260ee192e624`.

### Strongest current blocker — human visual gate FAIL

The latest PNG proves the real capture mechanism and native HUD, but it is not
acceptable Steam art.  An opaque building roof/upper-shell surface occupies the
live camera and hides the Press Shop machines and material-flow story.  This
contradicts the 2126 roofless authority.  The receipt correctly retains
`steam_visual_quality_human_approved=false`.

Required next evidence is a scoped roof/upper-shell removal or runtime-hide in
the isolated candidate lane, followed by a fresh exact-map regular-PIE live-HUD
capture showing the machines and material flow.  Cook, packaged behavior,
performance, Shipping validation and human Steam-art approval are still absent.
The candidate is **not Steam-ready**.

### Roofless runtime correction and successor live run

The runtime envelope now consumes the existing saved semantic marker
`LB.PressShop.RooflessPresentation.v002`.  The explicit roof policy suppresses
only the four per-department roof-deck actors.  The focused automation
`LineBoss.OneFactory.ActualPlayer.RooflessPresentationSkipsOnlyRoofDecks`
passed 1/1; the marked/unmarked worlds produced 0/4 roof decks respectively,
with equal wall, dado, clerestory and site-slab counts.  Editor build succeeded.

The successor live-HUD evidence is under
`Saved/Audits/PressShop2126/OverheadPresentation_v006/LiveHUDSteamCapture/Runs/20260824T032352721491Z/`.
Its receipt is SHA-256
`bcb9db8d2d3aafbd56719c6cbbe1fcca919b29523de91b3df6896999a49801fd`;
the 1920x1080, 2,429,434-byte PNG is SHA-256
`7fc7376f5ae019df5a973da347e6418686269dc1109370ecb45d217a6fd97a68`.
The receipt status is
`PASS_REGULAR_PIE_NATIVE_PLAYER_LIVE_HUD__NATURAL_S04_PRESS_STROKE__STEAMHERO_1920X1080_V006`,
with exactly one native screenshot request, 146 bound visual layers, natural
S04 `DESCENDING`, and the target map unchanged at
`34840087dad80312c8d7d1e010489fcb277bebfee3597f831aa53d89349ef9ec`.

Visual inspection proves the roof is absent but still rejects the frame: the
detailed machine sprites are missing while pads, labels and limited structural
strips remain.  No exact depth/material/visibility diagnosis was completed
before shutdown, so this document deliberately records the symptom rather than
an inferred cause.  Steam visual approval, cook, package, performance and
Shipping evidence remain open.
