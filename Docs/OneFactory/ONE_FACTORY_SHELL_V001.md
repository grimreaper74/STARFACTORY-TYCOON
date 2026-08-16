# Moorcross Works One Factory shell v001

Status: **INCIDENT V002 FIX FROZEN — GUARDED RETRY NOT YET EXECUTED**  
Frozen: 2026-08-15  
Destination: `/Game/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001`

## Outcome

The frozen one-shot creates a new basic, non-World-Partition shell map for the
single continuous Moorcross Works factory. It does not duplicate, migrate or
load an existing department map. It leaves the global/default map on protected
Press v913 and applies `/Script/LineBossCarFactory.LBOneFactoryGameMode` only as
this map's local `WorldSettings.default_game_mode` override.

The saved map contains exactly one native `LBOneFactoryBootstrap`, exactly one
deliberately map-authored native `LBPressShopBuildAuthority`, and zero
production machines, cells, stations, robots, vehicles or WIP actors. The
bootstrap validates and binds the existing authority; it never spawns or
mutates one.

## Frozen geometry and presentation

- Factory envelope: centre `(0, 0, 1500)` cm; full size
  `(62000, 31000, 3000)` cm.
- Native procedural presentation: 10 generic map-authored Actors, each with
  exactly one `UHierarchicalInstancedStaticMeshComponent`.
- HISM inventory: 200 floor slabs, 3 cutaway walls, 22 columns, 13 open-roof
  frame members, 932 one-metre grid lines, 20 bay/logistics safety lines and 4
  painted department-floor instances; **1,194 instances total**.
- Management cutaway: no south wall and no roof panels. The north/west/east
  lower walls, columns and open roof frame retain the scale of one large hall
  while preserving an unobstructed management view.
- Lighting: exactly one movable 5000 K Rect Light authority and exactly one
  unbound fixed-exposure authority (`AEM_BASIC`, min/max 1.0, bias 0.0).
- Navigation/player context: one factory-envelope NavMesh bounds volume, one
  management PlayerStart and one 16:9 overview camera. On save/reload Unreal
  deterministically materializes exactly one engine navigation-data actor
  labelled `RecastNavMesh-Default`, classed
  `/Script/NavigationSystem.RecastNavMesh`, with empty tags, identity transform,
  no owner/attachment and the same persistent-level outer as the exact
  bootstrap. The relationship is proven by comparing the two exposed actor
  outers; it does not reflect the unavailable UE 5.8 `World.persistent_level`.
- Exact map-authored non-foundation actor count: **25**.
- Exact fresh-reload non-foundation actor count: **26** = 25 map-authored + 1
  exact engine-generated Recast navigation actor. No engine actor family is
  broadly ignored.

## Canonical department bays

The Press authority arrays are authored in this strict order. Transforms are
yaw zero and unit scale.

| Order | ID | Department | Centre cm | Half extent cm |
|---:|---|---|---|---|
| 1 | `OF_BAY_PRESS_01` | Press | `(-14500, 8000, 1000)` | `(16000, 6500, 1000)` |
| 2 | `OF_BAY_BODY_01` | Body/Weld | `(-11000, -8500, 1000)` | `(9000, 5000, 1000)` |
| 3 | `OF_BAY_PAINT_01` | Paint | `(10000, -8500, 1000)` | `(11000, 5000, 1000)` |
| 4 | `OF_BAY_ASSEMBLY_01` | Assembly | `(16500, 8500, 1000)` | `(14000, 6000, 1000)` |

Each bay has a separate exact TargetPoint datum and a native painted-floor HISM
actor tagged with its department, stable bay ID and `LB.OneFactory.Grid.100cm`.

## Shared spines

| Role | ID | Centre / protected half extent cm | Start → end cm | Reach cm |
|---|---|---|---|---:|
| Logistics | `OF_SPINE_LOGISTICS_EW_01` | `(0,0,200)` / `(30500,600,200)` | `(-30500,0,0)` → `(30500,0,0)` | 1200 access |
| Service | `OF_SPINE_SERVICE_EW_01` | `(0,-14500,200)` / `(30500,300,200)` | `(-30500,-14500,0)` → `(30500,-14500,0)` | 30000 connection |

The 30,000 cm shared service reach is intentional: one south service backbone
can authorize every department bay without baking separate department utility
actors into the shell. `StorageBays` is exactly empty.

## Exact native authority contract

- GameMode: `/Script/LineBossCarFactory.LBOneFactoryGameMode`
- Pawn: `/Script/LineBossCarFactory.LBManagementPawn`
- HUD: `/Script/LineBossCarFactory.LBControlRoomHUD`
- Bootstrap: `/Script/LineBossCarFactory.LBOneFactoryBootstrap`
- Press authority: `/Script/LineBossCarFactory.LBPressShopBuildAuthority`
- Bootstrap tags exactly:
  `{LB.OneFactory.Bootstrap.v001, LB.Provenance.NativeOnly}`
- Press authority tags exactly:
  `{LB.OneFactory.MapAuthored.PressBuildAuthority.v001, LB.Provenance.NativeOnly}`
- Both authority actors are at identity, unowned, unattached and in the same
  persistent level.
- The bootstrap's canonical `ShellLayout` validates the map-authored Press
  arrays; it does not seed stations or legacy factory content.
- The builder deliberately does not call `ValidateAndLockShell` before saving,
  so a successful editor-time audit is never serialized as a pre-validated
  map. It runs only after the saved map is freshly reloaded; the independent
  validator repeats that audit in a second process and neither process saves
  the post-validation actor state.

## Preservation boundary

The builder, validator and PowerShell runner all pin these protected anchors:

| Protected map | SHA-256 |
|---|---|
| Press v913 | `26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6` |
| Restored full Press v001 | `D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5` |
| Body prototype v001 | `8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F` |
| Paint prototype v001 | `2296FEE6FAF5AECB5B424E1E413B4324D1F9D3C4AF0172D7F83BC2440CE17069` |

In addition, every file recursively below `Config/` and every file recursively
below `Saved/SaveGames/` is snapshotted before creation and compared after map
save/reload and again after the independent fresh-process validator. Therefore
`Config/DefaultEngine.ini`, the default game map and campaign/department saves
must remain byte-identical. The ordinary builder/validator/runner never delete,
overwrite, rename or quarantine an existing asset. The separate incident
recovery script is allowed to move only the byte-exact failed destination
described below, from its exact Content path into its exact archive below
`Saved`; it contains no delete step.

If the destination map or either stable receipt already exists, the one-shot
refuses to run. If any stage fails after an output is created, the output is
preserved for inspection and must be reviewed/quarantined deliberately; the
tooling never silently removes it.

## Failed run 20260815T005506Z and smallest truthful fix

The first live one-shot saved and fresh-reloaded the new map, then correctly
failed closed before writing either stable receipt or a PASS marker. The fresh
reload contained the engine-created actor `RecastNavMesh-Default`, while the
original label cardinality expected only the 25 map-authored actors. Evidence:

- Failed run: `Saved/Audits/OneFactory/v001/Runs/20260815T005506Z`
- `editor_build.log`: 1,052 bytes,
  `20C3082F4F0EAFC638C3BEE02BA9DEB1F837B2758963207C19230A1161684025`
- `shell_create.log`: 342,196 bytes,
  `2CDC949B47D3A2615EAD791146D878B4E1F53071324F6602731CF7BDDC25C05D`
- Failed destination map: 272,679 bytes,
  `0E461BC18927B369C112BC11E36F91542F1686C4B18D3E5EBF6C0DE788BD7AC2`
- Creation receipt: absent. Validation receipt: absent. PASS marker: absent.
- Protected Press v913/restored Press/Body/Paint hashes remained exact; all
  `Config/` and `Saved/SaveGames/` snapshots remained protected.

The fix is narrow: the builder allows zero or one *exact* Recast actor only in
the pre-save world, requires exactly one after fresh reload, and checks its
exact label/class/tags/transform/relationship. The independent validator always
requires the exact 26-actor fresh-load contract. HISM counts, department arrays,
authorities and the zero-production/WIP rule are unchanged.

## First incident preservation and failed retry

`recover_one_factory_shell_failed_run_20260815_v001.ps1` refused every state
except the incident above. It pins the failed map's path, size and hash; the
failed run's exact two-file inventory, sizes and hashes; all patched tooling
hashes; the four protected map anchors; all `Config/` files; and all
`Saved/SaveGames/` files. It also requires no stable receipts, no active Unreal
process, and exactly one file in the destination Maps directory.

On its one allowed execution it:

1. copies the exact failed run evidence to
   `Saved/Quarantine/OneFactory/ShellV001/Incident_20260815T005506Z/FailedRunEvidence`;
2. moves—not deletes—the exact failed map from Content to that incident's
   `FailedDestinationMap` directory and verifies the archived bytes;
3. writes a pre-retry evidence receipt under the same incident directory;
4. invokes the frozen ordinary runner exactly once; and
5. on PASS, would write an incident retry summary. The archive-exists guard
   makes the recovery script one-use only.

The v001 recovery executed once. Its evidence copy, failed-map move and
pre-retry receipt succeeded and remain exact below
`Saved/Quarantine/OneFactory/ShellV001/Incident_20260815T005506Z`. Its one clean
retry then failed closed in run `20260815T011006Z` after saving/reloading,
because UE 5.8 Python does not expose
`world.get_editor_property("persistent_level")`. No stable receipt, PASS marker
or v001 retry summary was written.

## Failed run 20260815T011006Z and v002 recovery

Attempt two preserved the correct exact Recast actor contract, but the
persistent-level proof used the unavailable World reflection property. The
reflected-safe fix compares `RecastNavMesh-Default.get_outer()` with the exact
bootstrap's `get_outer()` after bootstrap cardinality has passed. The existing
Press authority already uses this exposed, stable same-level seam. Evidence:

- Failed run: `Saved/Audits/OneFactory/v001/Runs/20260815T011006Z`
- `editor_build.log`: 22,518 bytes,
  `DBCFEEB71A0F587BECA8BAE5B68DE0593BD4C21AE987CDE5D7615A83876681EA`
- `shell_create.log`: 684,810 bytes,
  `A9FA2E2967355964C823A5BCA24F085C73624C5A3FE4C25B3D8328DAB02A254A`
- Second failed map: 272,679 bytes,
  `44E082B43719CA8B44E453ACBC9BF9BF018572102DABAA26D2EDF93E9B6A5B52`
- Creation receipt: absent. Validation receipt: absent. PASS marker: absent.

`recover_one_factory_shell_failed_run_20260815_v002.ps1` is bound only to this
second incident. In addition to the ordinary protected snapshots, it pins the
second map and two logs by exact path/size/hash, pins the patched
builder/validator/runner, and proves the v001 recovery was already consumed by
requiring its historical script hash and exact four-file prior archive—with no
v001 retry summary. It copies the second run evidence, moves—not deletes—the
second map to a distinct `Incident_20260815T011006Z` archive, writes its
pre-retry receipt and invokes the ordinary runner exactly once. Its own archive
guard prevents reuse.

## Frozen tooling hashes

| File | SHA-256 |
|---|---|
| `Scripts/create_one_factory_shell_v001.py` | `4EE0A437A9BCC3A5431C39B2D27BB05067FA74F1A6A586B5C2DF05E412131728` |
| `Scripts/validate_one_factory_shell_v001.py` | `2043ED396DFD366CB857F208A38054EE9CCE4906A04EA53C4ABD86ADF1CB5E61` |
| `Scripts/run_one_factory_shell_validation_v001.ps1` | `1A19CF7E4FE1DDB1F150CD3AC96382D8AA2FEB097C3FDC20E184A739855DDF5F` |
| `Scripts/recover_one_factory_shell_failed_run_20260815_v001.ps1` | `654EC6892C474D9934B196C6C2DED0A3508802AECF7CB55497D92AC5C932CB46` |
| `Scripts/recover_one_factory_shell_failed_run_20260815_v002.ps1` | `7178EA3854A7046F0B59D1988C93E4CD96BC5CE9F7015EAC2665669E7993C5C2` |
| `Scripts/tests/test_one_factory_shell_contract_v001.py` | `2568E23C81B7607FD7A126FA6BE37D41C2421A8EB35BBF3A65F7F4D23E3DD494` |
| `Scripts/tests/test_one_factory_shell_safety_v001.py` | `8BB3AF5901B6069791DED03A1A622518D2FDF44E21616BE34CB5068E0BB9C39C` |

The independent validator embeds the frozen builder hash. The runner embeds
both frozen Python hashes and refuses drift before compiling or launching the
editor.

## Static evidence completed

- Both Python files compile/parse successfully.
- PowerShell parser reports no syntax errors.
- 19 focused pure-Python tests pass.
- Builder and validator independently generate identical 1,194 ordered HISM
  transforms and identical canonical Press-authority arrays.
- The second failed destination map remains present at its exact Content path,
  272,679-byte size and `44E082...A5B52` hash until the v002 guarded recovery
  command below is explicitly run. The first failed map/run remain preserved
  in their prior archive.
- Creation and validation receipts remain absent.
- The incident-fix work itself did not launch Unreal or edit `Content`,
  `Config`, `Source`, any map or any save. It changed only scripts, focused
  tests and this document.

## Exact future command

For the exact second failed incident, run only when no Unreal Editor/build
process is open:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\recover_one_factory_shell_failed_run_20260815_v002.ps1"
```

The command first verifies the consumed v001 incident, preserves the second
failed evidence and moves the exact second failed map under `Saved`, then calls
the normal runner exactly once. That runner builds
`LineBossCarFactoryEditor`, creates the map in one headless process, validates
it in a second fresh headless process, checks exact PASS markers and receipts,
and emits a timestamped run summary under
`Saved/Audits/OneFactory/v001/Runs/`.
