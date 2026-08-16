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
