# OneFactory native Press presentation v001

## Outcome

`ALBOneFactoryPressStarterPresentationActor` is the cheap, clean, quirky Press
starter visual for the unified Moorcross Works factory. It consumes one complete
`FLBOneFactoryPressStarterLayoutState` from the authority documented in
`ONE_FACTORY_PRESS_STARTER_V001.md`; every primitive is derived from the seven
stable station IDs and their world transforms.

The actor is presentation only. It has no process port, recipe authority,
inventory, reservation, production WIP, SaveGame state, collision, navigation,
replication or tick. A failed layout, provenance, asset-resolution or count check
clears all prior instances and remains invisible.

## Readable department silhouette

The management view gets explicit low-detail cues for the complete starter flow:

- empty native-procedural AGV and wrapped-coil unload arch;
- six-place wrapped-coil store;
- decoiler/feed/cut blank-preparation package;
- prepared-blank stacks and a separate three-die rack;
- seven visibly separate configurable Press stages;
- a 9.1 m-high Press gantry/crane silhouette;
- scanner-style panel inspection;
- three empty dispatch stillages and an empty dispatch AGV;
- seven station outlines/status markers and all six material routes.

The teal, graphite, pale-steel, safety-yellow, green-status and amber-route
semantics deliberately match the retained factory language. They are runtime
tints of the Engine Basic Shape material, avoiding a dependency on a department-
specific or imported material root.

## Frozen efficiency contract

The complete department is 268 Engine primitives in exactly eight HISM batches.

| Batch | Instances |
|---|---:|
| Graphite cube | 32 |
| Teal structure cube | 88 |
| Pale-steel cube | 34 |
| Safety-yellow cube | 38 |
| Green status cube | 18 |
| Graphite cylinder | 16 |
| Pale-steel cylinder | 8 |
| Amber floor/route cube | 34 |
| **Total** | **268** |

Stable role lookup is also frozen:

| Starter responsibility | Instances |
|---|---:|
| Inbound coil receiving | 18 |
| Wrapped coil storage | 37 |
| Blank preparation | 31 |
| Prepared blank and die buffer | 34 |
| Configurable seven-stage Press train | 89 |
| Panel inspection | 19 |
| Panel stillage dispatch | 40 |

## Exact provenance boundary

The local presentation contract admits only:

- class `/Script/LineBossCarFactory.LBOneFactoryPressStarterPresentationActor`;
- `/Engine/BasicShapes/Cube.Cube`;
- `/Engine/BasicShapes/Cylinder.Cylinder`;
- `/Engine/BasicShapes/BasicShapeMaterial.BasicShapeMaterial`.

It first validates the frozen Press NativeOnly profile, then checks its exact
class/path inventory, every forbidden source token, and the shared OneFactory
NativeCode/NativeProcedural provenance policy. Meshy, candidate, runtime-GLB,
download, developer-validation, mixed historic Press and substituted class/path
references fail closed.

The layout authority's exact class allowlist must separately admit this class
before the player-facing materialisation transaction is enabled. This admission
does not broaden any asset root.

## Player New Factory transaction

The OneFactory map remains empty. The player action should:

1. validate the empty-map bootstrap;
2. create the canonical Press layout authority;
3. create this visual actor and call `ConfigureFromLayout(CaptureLayout())`;
4. commit both actors only when both data and presentation validate;
5. destroy both actors if materialisation fails.

Moving or reconfiguring a station remains authoritative in the layout actor.
After a successful data transaction, the presentation is rebuilt from the new
captured revision; stable station IDs preserve management selection/highlighting.

Focused automation:

- `LineBoss.OneFactory.PressStarter.Presentation.NativeContractCountsAndRoleLookup`
- `LineBoss.OneFactory.PressStarter.Presentation.FailClosedMaterialisationAndRebind`

No protected map, historic Press asset, content package, config file or campaign
save is changed by this presentation milestone.

