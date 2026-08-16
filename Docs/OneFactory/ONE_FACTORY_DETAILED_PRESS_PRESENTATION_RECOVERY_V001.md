# OneFactory detailed Press presentation recovery v001

## Outcome and boundary

The visual complaint is valid and measurable. The current OneFactory Press view is
the 268-primitive native blockout, while the protected pre-Meshy v438 Train A is a
337-visual-actor industrial Press train with seven tagged stages, transfer gear,
tooling, guards, utilities, controls and discharge equipment.

This tranche prepares recovery without changing runtime code or Content. It does
not load Unreal, save a map, create an asset, or alter the current OneFactory
authority. The protected v438, restored v001 and current v913 maps remain inputs
only. `ALBPressTrainAStation` is identity evidence only: its present-day native
constructor contains later art and must never be used to reconstruct v438.

## Pinned evidence

| Evidence | Exact result |
|---|---|
| Protected source map | `/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438` |
| v438 map SHA-256 | `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8` |
| Train A scope | exact tag `LB.PressTrain.Installed.TRAIN_A` |
| Inventory | 338 actors: 336 `StaticMeshActor`, 1 `TextRenderActor`, 1 legacy `LBPressTrainAStation` |
| Materializable visuals | 337; the legacy authority is excluded |
| Exact 338 signature | `954C64F6428AC1FFA05AC2B06314373D33E466499903D11E661F686A0378423E` |
| Exact 337 visual signature | `179B83D8029BB9FBBC5BAA3C5647CDDB06B57293C7D6999738E1BC2097A21120` |
| Train datum | world centimetres `[3850.0, -4300.0, 0.0]` |
| Restored detail screenshot | SHA-256 `907BFFE910876E33415BD8E579C8ADD6BF637267515C1547D5D32667A8098486` |
| Current OneFactory blockout screenshot | SHA-256 `7645637C24E077BF6B0F61BAEC1C70A15467913EA0882ACE27D7C23532AEC1FA` |

The exact actor evidence is
`Saved/Audits/PressShopIntegration/press_shop_capture_layout_v452.json`, itself
pinned at SHA-256
`376B88B3B5F1D5BFAEDCBD317DF4D14652228EB76CEE683436B7A55DAFCA20E0`.
Its canonical signature covers each label, class, location, bounds and complete
tag list, so the 337-source inventory cannot silently drift.

There is also a valuable fidelity shortcut made before the later asset route:

- mesh
  `/Game/LineBoss/PressTrains/RuntimeVisual_v449/SM_CA_MW_PressTrain_CompleteRuntimeVisual_v449`;
- mesh SHA-256
  `4344B058F78D66F178095201E13D824CAD017C827DF7AFCBA369193DCA73931E`;
- 306 material slots using exactly 13 pinned v086/v383 materials;
- local transform relative to the Train A datum: location
  `[9.25, 2367.5, 0.0]`, rotation zero, scale `[100.0, 100.0, 100.0]`;
- receipt
  `Saved/Audits/PressTrains/press_train_complete_runtime_visual_build_v449.json`,
  SHA-256
  `CF09E3F1EE7623501BCEB79318A264712DEC17303107E27573552A7BAAA74148`.

The offline contract pins the v449 mesh and all 13 source material package hashes.
It rejects `Meshy`, vendor roots, developer/developer-validation roots, downloads,
paths outside `/Game/LineBoss`, and every revision token `v700` or later.

## Tooling prepared

`Scripts/one_factory_detailed_press_v001_contract.py` is pure offline Python. It:

1. re-hashes the protected map, actor evidence, v448/v449 receipts, v449 mesh,
   all 13 known material assets and both visual proof screenshots;
2. validates a future rich extraction manifest as exactly 338 actors and 337
   eligible visual actors;
3. requires exact transforms for every actor, scene component and every source
   ISM/HISM instance;
4. requires a SHA-256 and size receipt for every referenced project asset;
5. rejects forbidden or `v700+` references before producing any plan;
6. converts protected-map or transient dynamic materials into clone descriptors
   containing only their reusable parent and captured parameter values;
7. groups immutable visuals by exact mesh plus exact material signature for HISM,
   while preserving mover/robot/tool/workpiece/HMI visuals as individual static
   components and the identity sign as native text;
8. emits a deterministic, visual-only, no-collision, navigation-neutral, no-save,
   zero-WIP materialization plan and refuses to overwrite a prior output.

`Scripts/audit_one_factory_detailed_press_v438_source_v001.py` is the future
Unreal read-only extractor. It is deliberately not run in this tranche. It:

- verifies all three protected map hashes before loading v438;
- reads only actors with the exact Train A tag;
- records actor and component class, tags, visibility, mobility, collision,
  shadow/navigation flags, mesh, resolved materials, text/font and world/datum-
  relative transforms;
- records every ISM/HISM instance in world and datum-relative coordinates;
- snapshots material parent and scalar/vector/texture parameters;
- hashes the complete referenced project-asset closure;
- records the one legacy authority without reading its current components;
- re-hashes protected maps after extraction, never calls a map/asset save, and
  writes a one-shot receipt only under `Saved/Audits`.

`Scripts/tests/test_one_factory_detailed_press_v001.py` covers evidence drift,
exact inventory, forbidden provenance, legacy-authority exclusion, transient and
map-owned material cloning, exact ISM transforms, dependency-closure receipts,
deterministic grouping and static no-mutation checks.

## Runtime integration design

### Compatibility shell

Keep `ALBOneFactoryPressStarterPresentationActor` as the exact paired
presentation class. Both `ULBOneFactoryPlayerBuilderSubsystem` and the save
subsystem discover that exact type; adding a subclass or a second presentation
actor would fail the current exact-pair contract. The new implementation is a
fresh internal presentation revision named
`OneFactoryDetailedPressPresentation_v001`, not a replacement gameplay
authority.

The current `ALBOneFactoryPressStarterLayoutAuthority` remains the sole source of
layout, assignments, commission state and process/WIP decisions. The detailed
presentation holds no ports, recipe, inventory, reservations, replication,
SaveGame properties or campaign data. It retains `RepresentsProcessWIP() ==
false` and `LB.NotProcessWIP`. Save/load persists layout state only and rebuilds
the presentation from the committed layout snapshot.

The 268 deterministic items may remain as private logical/coherence metadata for
the seven OneFactory responsibilities, but their Engine cube/cylinder batches
must no longer render. The detailed train is anchored to the committed
`ConfigurablePressTrain` station transform. A presentation root is placed at
that station transform; every recovered transform is local to the pinned v438
Train A datum. All seven station transforms are still retained for the existing
pair-coherence API.

### Preferred renderer and fidelity fallback

The preferred renderer is the compiled 337-source plan:

- immutable actors with the same mesh and complete material signature become
  one HISM component with exact local instances;
- source ISM/HISM instances are expanded and preserved exactly;
- query-mover, moving-slide/die, carried-workpiece, runtime robot/tool and HMI
  roles remain independently addressable static components;
- the source TextRender actor becomes a native `UTextRenderComponent`;
- every component is `NoCollision`, cannot affect navigation, and is visual only.

This gives selection/highlight and future animation seams without importing the
legacy authority. Its exact group/component counts are intentionally not guessed;
they become constants only after the read-only extractor and offline compiler
pass.

If the grouped form cannot reproduce the restored screenshot exactly, use the
v449 complete runtime visual for the first fidelity release. It is one large
static mesh with 306 sections, so it is less efficient and less individually
addressable, but it is already pinned directly to v438 and is the lowest-risk
way to recover the user's accepted look. The grouped representation can replace
it later behind the same actor API.

### Owned content and provenance

Runtime must not load the historic Candidate/Station paths directly because the
current Press NativeOnly profile intentionally rejects those roots. After the
manifest is accepted, a separate, reviewable promotion tool should create an
owned dependency closure beneath:

`/Game/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/`

Suggested owned entry point:

`SM_OneFactoryDetailedPressPresentation_v001`

for the v449 fallback, or
`DA_OneFactoryDetailedPressPresentation_v001` plus owned mesh/material
dependencies for the grouped form. Promotion must be copy-and-rebind, never a
rename or move: it duplicates the accepted source, clones all required material
parents/parameters, rebinds slots, saves only the new root, reloads it
independently, and produces a source-package/hash to owned-package/hash receipt.
No protected map object or transient material may remain in the dependency graph.
`VerifiedPreMeshyNative` is already an accepted shared provenance enum, while the
dedicated OneFactory Native Press root is already allowlisted.

### Atomic configure, rebuild and rollback

`ConfigureFromLayout` should be changed from clear-first to a two-phase commit:

1. validate the incoming layout and its 268 logical/coherence items without
   touching the visible presentation;
2. validate the exact owned class/path/hash receipt and resolve every dependency;
3. build candidate component descriptors and transforms in memory;
4. create/register hidden staging components with collision/navigation disabled;
5. validate exact component/group/instance counts, material slots, layout ID,
   revision and the configurable-train anchor;
6. atomically reveal the staging set and retire the former committed set;
7. on any failure, destroy staging objects and leave the former committed
   presentation and snapshot unchanged.

Explicit destroy removes only presentation components/actor. It never destroys
the layout authority except through the existing paired PlayerBuilder
transaction. Save-load presentation rebuild follows the same staging path; a
failed rebuild restores the prior committed presentation, matching the existing
all-authority rollback contract. Commission and WIP gates remain in the layout,
PlayerBuilder and production-flow authorities; presentation rebuild never
creates or clears WIP.

## Current integration collision

The existing seams are intentionally rigid:

- PlayerBuilder requires
  `Presentation->GetClass() == ALBOneFactoryPressStarterPresentationActor::StaticClass()`;
- it validates the presentation tag, zero-WIP flag, required asset list, batch
  count, visible count and all seven configured station transforms;
- the save subsystem holds the same concrete type and preflights its static
  presentation contract;
- current presentation provenance requires exactly Cube, Cylinder and
  BasicShapeMaterial from Engine Basic Shapes and advertises 8/268.

Therefore a new standalone actor cannot be integrated silently. The bounded
runtime change should preserve the exact class and public lifecycle, update only
its detailed rendering internals/count contract and focused tests, and touch
PlayerBuilder/save code only if a later compile/static proof identifies a hard
contract blocker. Current relevant file hashes at this audit were:

| File | SHA-256 |
|---|---|
| `LBOneFactoryPressStarterPresentationActor.h` | `293FE7E78DAAD0BA46D6379034B64D43A85C1106C4FD8D44A5075B5D7E43A63B` |
| `LBOneFactoryPressStarterPresentationActor.cpp` | `AC40D7AFCC00A285DCC6D9C35D2A007A52CE7C70C738512C917E421FCD6BA062` |
| `LBOneFactoryPlayerBuilderSubsystem.h` | `E59CD6BAE69933C3222CFF32D7CFEC5C58037BA96A4B921CB667C61D8908A9C0` |
| `LBOneFactoryPlayerBuilderSubsystem.cpp` | `388DCD652217AA5DE7E67114FD0319438738A8151B5E31999561D6FA8C8A229B` |
| `LBOneFactorySaveSubsystem.cpp` | `F2C81FFB63996270C5BD6A0DCC8CB4A49E8EA228E07A665F1469A6E368C0CEE6` |

## Exact gated commands

The only command executed in this tranche is offline:

```powershell
Set-Location -LiteralPath 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8'
python Scripts\one_factory_detailed_press_v001_contract.py --project-root .
python -m unittest Scripts.tests.test_one_factory_detailed_press_v001 -v
```

After an explicit Unreal read-only green light, with no editor/build process
active, run the extractor once using forward slashes in `ExecutePythonScript`:

```powershell
$Project = 'C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/LineBossCarFactory.uproject'
$Editor = 'C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor-Cmd.exe'
$Script = 'C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Scripts/audit_one_factory_detailed_press_v438_source_v001.py'
& $Editor $Project "-ExecutePythonScript=$Script" -unattended -nop4 -nosplash -nosound -NullRHI -NoAutoSave -NoSaveOnExit -stdout -FullStdOutLogOutput
```

Expected one-shot output:

`Saved/Audits/OneFactory/DetailedPressPresentation_v001/v438_train_a_source_manifest_v001.json`

Then compile the deterministic plan offline. The output path must not already
exist:

```powershell
python Scripts\one_factory_detailed_press_v001_contract.py `
  --project-root . `
  --manifest Saved\Audits\OneFactory\DetailedPressPresentation_v001\v438_train_a_source_manifest_v001.json `
  --output Saved\Audits\OneFactory\DetailedPressPresentation_v001\materialization_plan_v001.json
```

Stop after this command. The Content promoter/materializer must not be written or
run until the manifest has proved exact UE 5.8 component/material APIs and the
group count, dependency closure and map-owned-material population are reviewed.

## Promotion and runtime acceptance gates

The later write-enabled tranche is accepted only when all of the following pass:

1. the protected v438, restored v001 and current v913 hashes are unchanged;
2. exact 338/337 inventory and canonical signatures still pass;
3. zero Meshy/vendor/developer/v700+ references and zero protected-map/transient
   dependencies exist in the owned asset closure;
4. an isolated new validation map materializes exactly one layout authority and
   one exact Press presentation actor;
5. configure, move, programme/assignment, commission, destroy, save rebuild and
   forced-failure rollback tests preserve the committed layout and presentation;
6. WIP rejection remains explicit and presentation proxies never enter a save;
7. fresh-load validation passes after all editor processes exit;
8. screenshots from the same camera/lighting prove the detailed OneFactory Press
   matches the restored v438 Train A silhouette and materials;
9. the full `LineBoss.OneFactory` automation queue remains green.

No current Press map, restored map, protected source map, HUD/Canvas, PlayerBuilder,
ProductionFlow, Config or save slot is modified by the preparation documented here.
