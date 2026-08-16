# OneFactory Press starter v001

## Outcome

`ALBOneFactoryPressStarterLayoutAuthority` is the smallest truthful Press
starter-layout authority that can be added without touching the protected Press
maps, the empty OneFactory map, campaign saves, content, config or the native-AGV
workstream.

It is deliberately a presentation-free runtime data authority. Creating it does
not spawn machines, vehicles, inventory or WIP. A future New Factory action may
create it only after `ALBOneFactoryBootstrap` has validated and locked the empty
map shell. This preserves the existing no-seeding startup contract.

## Stable starter responsibilities

| Stable station ID | Responsibility | Player-selectable job |
|---|---|---|
| `OF_PRESS_INBOUND_RECEIVING_001` | Receive wrapped coils from the native inbound source | No |
| `OF_PRESS_WRAPPED_COIL_STORE_001` | Buffer identified wrapped coils | No |
| `OF_PRESS_BLANK_PREP_001` | Compact weigh/identify/de-pack/cut-to-blank package | Yes |
| `OF_PRESS_PREPARED_BLANK_BUFFER_001` | Buffer prepared blanks for the selected panel | Follows selected job |
| `OF_PRESS_TRAIN_001` | Stamp one selected Cairnwell 2040 panel programme | Yes |
| `OF_PRESS_PANEL_INSPECTION_001` | Inspect the selected stamped panel | Yes |
| `OF_PRESS_PANEL_DISPATCH_001` | Dispatch like panels in WIP stillages | Follows selected job |

The player may select Blank Prep, Press Train or Panel Inspection and choose any
approved stamped-panel job already present in `LBCairnwell2040PanelCatalog`.
Changing a job is one transaction: blank preparation, blank buffer, die, Press,
inspection and dispatch all change together. A mismatched or partial chain is
never committed. Any active or reserved WIP blocks configuration and movement.

The canonical layout starts on `HOOD_PANEL`; it contains exactly seven stations,
six material routes and zero WIP. It fits wholly inside `OF_BAY_PRESS_01`. Station
movement is transactional, preserves stable identities and the exact six-route
graph, and rejects out-of-bay, overlapping or over-length layouts without
mutating the prior state.

## Exact NativeOnly profile

Profile ID: `MOORCROSS_PRESS_NATIVE_ONLY_V001`

Allowed runtime classes (exact; subclasses are not implicitly accepted):

- `/Script/LineBossCarFactory.LBOneFactoryPressStarterLayoutAuthority`
- `/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor`
- `/Script/LineBossCarFactory.LBFactoryAGVInfrastructure`

Allowed asset roots (exact prefixes):

- `/Script/LineBossCarFactory.`
- `/Engine/BasicShapes/`
- `/Engine/EngineMaterials/`
- `/Game/LineBoss/Factory/OneFactory/v001/Native/Press/`

Forbidden source tokens:

- `Meshy`
- `RuntimeGLB`
- `ExternalGenerated`
- `OriginalHighPoly`
- `/Downloads/`
- `/Developer/Validation/`
- `/Candidates/`
- `/Runtime/PressShop/`
- `/Stations/Press/`

Both the exact runtime class and exact asset-root prefix must pass, in addition
to the shared `ELBOneFactoryProvenancePolicy::NativeOnly` provenance check.
Changing the order or contents of the profile itself fails closed.

## Provenance audit

No historic Press presentation root is admitted by v001. The retained process
logic and the Cairnwell panel catalogue are native C++ data, but the current
presentation-bearing runtime classes cannot truthfully materialise this profile:

- `ALBFactoryBuildMachine` hard-references a PR005 Meshy HMI, RuntimeGLB PR002
  art and mixed historic Press roots in its constructor.
- `ALBPressTrainAStation` hard-references complete-train assets whose source and
  object names include `MeshyMaster`, plus developer-validation roots.
- `ALBPressShopStorageZone` hard-references imported wrapped-coil/stillage assets
  and even documents imported Meshy stillage grounding.
- `ULBPressTrainIdentitySubsystem::PlaceTrain` requires the current complete
  presentation to enable successfully, so it cannot be used as a logic-only
  NativeOnly placement seam.

`ALBFactoryAGVInfrastructure` is admitted because its presentation uses Engine
basic shapes and native procedural floor markings only. The new generic machine
move/remove and transport disconnect APIs are transactionally sound, but their
machine side is currently typed to `ALBFactoryBuildMachine`; using it would pull
the mixed presentation constructor into this milestone.

This is intentionally stricter than accepting assets solely because they predate
the recent Meshy detour. Existing logic may be retained; an old visual asset is
accepted only after a separate source receipt proves it and the asset is promoted
under the dedicated OneFactory native Press root.

## Atomic save contract

`FLBOneFactoryPressStarterLayoutState` version 1 captures:

- stable layout ID and revision;
- explicit commissioning state;
- every station transform, footprint, responsibility, recipe and active/reserved
  unit identity;
- every exact route endpoint, material class and maximum reach.

Restore validates the complete candidate before a single assignment commit.
Duplicate IDs, invalid recipes, mismatched responsibilities, overlapping/out-of-
bay footprints, duplicate WIP identities, missing/extra routes and routes beyond
their authored reach all reject without changing the live snapshot.

Focused tests:

- `LineBoss.OneFactory.PressStarter.NativeOnlyProfileAndCanonicalTopology`
- `LineBoss.OneFactory.PressStarter.AtomicProgrammeCaptureRestoreAndWIPGate`
- `LineBoss.OneFactory.PressStarter.TransactionalMovePreservesGraphAndRollsBack`

## Materialisation blockers and next safe step

The authority is ready for compilation and automation, but it does not claim a
visible or producing Press shop yet. Materialisation should be a separate change:

1. Add a native procedural `ALBOneFactoryPressStationActor` that uses only Engine
   shapes/native components, or promote independently proven Blender-native art
   into `/Game/LineBoss/Factory/OneFactory/v001/Native/Press/`.
2. Keep station actors presentation-only; bind their stable IDs to this authority
   and to a presentation-free process endpoint interface.
3. Generalise the transactional builder from concrete `ALBFactoryBuildMachine`
   ownership to that endpoint interface, retaining its current WIP/reservation,
   exact-link snapshot and rollback gates.
4. Create the authority and station actors from the player's New Factory action,
   after the empty shell bootstrap is Ready. Do not place them in the map and do
   not enable `bSeedStationsOnBeginPlay`.
5. Add this state to the next append-only campaign save format and include it in
   the existing whole-campaign preflight/rollback transaction.
6. Bind the separately developed native inbound-AGV source mode to
   `OF_PRESS_INBOUND_RECEIVING_001` after its own provenance gate passes.

Until those steps land, `Commission()` explicitly reports that production still
requires native station materialisation. This avoids presenting a data topology
as a finished visual/gameplay implementation.
