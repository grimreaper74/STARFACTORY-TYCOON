# Body Shop native robot clean Unreal import lane v001

## State

`CLEAN_IMPORT_LANE_FROZEN__PARENT_REVIEW_REQUIRED__NO_CLEAN_IMPORT_UE_RUN_YET`

This lane has not launched Unreal or UBT. It is an incident-bound, one-shot
clean import. It does not recover, reuse, overwrite, delete, promote, bind,
compile, or edit a map. Before Unreal may start, an offline step must preserve
both failed attempts and the exact eight invalid packages, then recoverably move
the complete invalid namespace out of Content with one same-volume directory
rename.

## Superseding source authority

The corrected high-elbow source is frozen at
`SourceAssets/Candidate/WeldShop/BodyShopRobotNative_v001`:

- FROZEN: `C11F95D4EC8B57C2D2D89AD63D44589C8A46FF0A6169DD37E733A25C0AA7C3CB`
- manifest: `2797633628F0D295850A62319BB4D3E84ABA87BEB3C2B303C26FE7E17DBF1D4E`
- Blender authority: `91DC4262FEA06C63B49A2E457ACB30F2E70576CEC92B2EA4D6FF2FC7F7C55E3B`
- contact/FK audit: `29A0DCB9EF64191E7558B9E79562540CF1DFC98F1BC7D95CDAC25D3B4F6FA963`
- geometry audit: `8B334351E194F61033F269FBFB2BF45686AD4A3AC28C58536A04E2E3A1B61E82`
- 50-roundtrip audit: `FA784FB2D05781CDD5DA54D5E168225CB0D000A48E6F5CCCECB3A6E1F84CE9DB`

All eight assets now satisfy strict `LOD0 > LOD1 > LOD2`. Base is
`468 / 372 / 228` triangles; aggregate counts are
`2,628 / 1,964 / 1,356`. Base LOD1 retains all four semantic slots, including
SafetyYellow, using zero-bevel guards. All 24 asset/LOD meshes have exactly one
`UVMap`. Dimensions, local origins/pivots, slot order, and the high-elbow rig
contract are preserved.

The contact/clearance audit remains 18/18 PASS: maximum contact error
10.000016 cm, minimum direction dot 0.999999978, minimum floor clearance
64 cm, minimum J3 rise above shoulder 52.698883 cm, and centre-process elbow
height above wrist 31.344131 cm. All 50 FBX/GLB roundtrips pass.

The contradictory pre-monotonic Blender transcript was preserved byte-for-byte
as `Audit/SupersededEvidence/pre_monotonic_blender_generation_stdout.log`. It is
explicitly excluded from the 63-row current authority freeze and separately
pinned by the import baseline; it is not current source evidence.

## Bound incidents and invalid packages

The disposition contract recursively hash-binds both immutable failed run roots:

| Incident | Run root | Files | Recursive inventory SHA-256 |
| --- | --- | ---: | --- |
| Screen-size failure | `20260814T191133Z-7adb326b` | 7 | `F25A877C4F0388F7468E848FFE60CD1D8F627D215FF219004E0FBD7CA6DE04BA` |
| UV precondition failure | `20260814T193800Z-f02f2baa` | 27 | `5AD7F15B28E41B8FC4023B6E5EECD48ECBDC0E20951AC930B5C3E56029111C3E` |

Both live under
`Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/`. The second tree
includes its prior seven-file archive and exact pre-recovery package copies.
No file in either tree may change.

The invalid namespace resolves exactly to:

`C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Content\LineBoss\Candidates\WeldShop\BodyShopRobotNative_v001`

Its complete file inventory is the following eight packages:

| Key | Bytes | SHA-256 |
| --- | ---: | --- |
| Base | 249391 | `7E1DB3F376CF83B245AD6C55718F7B6076D3A7EC53B5D34177BA46EE3C7E8B49` |
| J1 | 27162 | `D08CC68E2073C9247E59BC596D5EA8563A49869568EAA17613F00C4E6D6C9AD3` |
| J2 | 24694 | `8DE689EB5BB2087EC08570E23E7D1BA18E1591DE37A534EE1EB0B2664D1300B2` |
| J3 | 23880 | `4FA06895F71B11572DC4798E31B7D666F55A96CF81F48F69D5329D57E8718F39` |
| J4 | 21099 | `CCBF85A3C3F3DEB3EACADC9E056D8853663A58E90DCA7F8EB85E13C296E1994B` |
| J5 | 19559 | `9630E512D7BED3DA0A6670952E4745C8BA1DD907B5EE436764BD80C7A8CF6FF0` |
| J6 | 21521 | `FCF17F4485A698E5FBBB92639123D78A01A5F01BE0ABF7A543CADF7B95A34326` |
| Open C-gun | 29064 | `E66AC3DAD4AA8C35D9052F281D208EA6481D78305E5B896FAA0331848946D64A` |

The offline disposition step, before any Unreal process:

1. Revalidates the baseline, both failed run trees, all eight invalid packages,
   Content outside the namespace, and the exact installed UE 5.8 evidence.
2. Exclusively copies all 34 failed-run files beneath
   `failed_runs_byte_archive/`, preserving each recursive path.
3. Exclusively copies all eight invalid packages beneath
   `invalid_namespace_byte_archive/Content/...`.
4. Rehashes all source and archive files, marks archive copies read-only, and
   refuses any pre-existing output.
5. Atomically renames the complete invalid Content directory to
   `invalid_namespace_recoverable_move/BodyShopRobotNative_v001` in the same
   new `Saved/Audits` run, rehashes the moved packages, and marks them read-only.
6. Requires the original Content path to be absent. No file is deleted.

If any step fails, exclusive copies, a moved namespace if the atomic rename had
already completed, process logs, a failure receipt, and the lane summary remain
for review. There is no cleanup or automatic retry.

## UE 5.8 LOD and screen-size correction

Installed engine source is itself pinned in the disposition contract:

- `StaticMesh.cpp` SHA
  `19AA05147F931D774F68BB3F4A921D5B659677D34B5DB821291E12788FAD3871`:
  `UStaticMesh::GetNumTexCoords(LODIndex)` reads the requested render LOD.
- `FbxMeshUtils.cpp` SHA
  `8776725B682A1355C8CEF2C49C757BAD5E4203E3C66136D4908E1D3F49E76D4E`:
  `ImportStaticMeshLOD` selects Interchange when the source is translatable and
  otherwise runs the legacy FBX custom-LOD branch.
- `InterchangeFbxTranslator.cpp` SHA
  `D93D22384C6E55AF1A4EC1FF2B3F5E55936697A943820F9437ED4B5F922DD250`:
  `Interchange.FeatureFlags.Import.FBX=0` removes FBX from supported formats.
- `StaticMeshEditorSubsystem.cpp` SHA
  `8C9E71501320F6EF9CB4A3D6AB668EEE6184230A2F85A8B9E3748E1831CA6760`:
  `SetLodScreenSizes` disables automatic computation and writes RenderData and
  SourceModel screen sizes.
- the generated Python stub SHA
  `213EB7BDD30D2E2DAE622A23A01D0BB519C6B87CC65035E46DE0D2C1FD3B1D25`.

The clean importer requires the namespace and all eight object paths absent,
then creates exactly eight LOD0 packages with explicit `FbxFactory`,
`replace_existing=false`, and no reuse. It captures the previous
`Interchange.FeatureFlags.Import.FBX` value, sets it to `0` only around the 16
custom LOD1/LOD2 calls, restores the exact prior value in `finally`, and records
previous/disabled/restored readbacks and all 16 source hashes. Existing LODs
reimported must be zero.

After all LOD, Nanite, collision, material, save, and compilation work, each
mesh receives manual screens `1.0 / 0.55 / 0.25`, is saved and compiled, then
receives the same screens again immediately before its final save. No build is
allowed after the final set. Automatic screen-size computation must remain off.

## Exact output and independent validator gates

Deterministic object paths are Base and J1-J6 under `Robot/`, plus
`SM_LB_BodyShopToolNative_OpenCGun_v001` under `Tools/`, all beneath:

`/Game/LineBoss/Candidates/WeldShop/BodyShopRobotNative_v001`

The importer and a separately launched fresh editor process both require:

- exactly 8 StaticMeshes and 8 `.uasset` files;
- exactly 3 LODs per mesh;
- exact per-LOD triangle counts and strict per-asset monotonicity;
- exactly one UV channel on all 24 LODs;
- exact local bounds and zero pivot within 0.5 cm;
- exact global semantic material slots and per-LOD section mappings;
- protected `Materials_v002` instance bindings;
- screens `1.0 / 0.55 / 0.25` and AutoCompute disabled;
- Nanite disabled, zero simple/convex primitives, and `UseSimpleAsComplex`;
- legacy import settings fixed at 1.0 scale and the frozen scene/pivot policy;
- each fresh-process package size/SHA equal to the importer receipt, with bytes
  unchanged by load;
- both failed runs, all copied/moved archive files, source authority, complete
  `Source`, complete `Config`, save games, Body Shop map, Press v913 map,
  existing Body Shop content, and WeldShop content outside the namespace
  unchanged.

Active `LBBodyShop*` bindings must contain all eight native paths and no
`WeldRobotRuntime_v001` token. Archived legacy source and old Meshy-derived
packages remain preserved and hash-protected.

## Frozen scripts and hashes

| File | SHA-256 |
| --- | --- |
| protected baseline JSON | `D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31` |
| baseline freezer/verifier | `6EF853183079B95EF64DF46E4E7B629273F7F5D4800C2C4EA7360A7AC3EB8CBB` |
| incident disposition contract JSON | `E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3` |
| disposition freezer/verifier | `C3A6A96BE2DB1BAC864291F7A36149F1E3171D454A8A0274BFD3477DBF98165C` |
| offline archive-and-move tool | `5F37A062A7A9EFDF25E856710622C6434543F27890C719CEB04491991C94EC19` |
| Unreal clean importer | `A44FB37410D409BFF7A3DE16E3A069F3A343F1510CAEC52B87CA3010EB02DF2D` |
| independent fresh-load validator | `6E16B96BDE306380EF6CD600337E7C30F6D8B3BDF5381FE50B3E050689AC559C` |
| guarded PowerShell runner | `1B85AD8D0D927B90E100C2FA1B21A53EEF64D85E3D4C5E2997CA802816D87CD7` |

The disposition artifact retains the historical filename
`body_shop_robot_native_unreal_recovery_contract_v001.json` only to avoid
unnecessary file proliferation; its schema, status, token, and policy authorize
clean disposition/import only, never package recovery or reuse.

## Read-only preflight and exact guarded command

Run from `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8`.

These commands are read-only and launch neither Unreal nor UBT:

```powershell
& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  '.\Scripts\freeze_body_shop_robot_native_unreal_import_baseline_v001.py' --verify-existing

& 'C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\ThirdParty\Python3\Win64\python.exe' `
  '.\Scripts\freeze_body_shop_robot_native_unreal_recovery_v001.py' --verify-existing
```

Required markers:

- `PASS__BODYSHOP_ROBOT_NATIVE_V001_EXISTING_BASELINE_MATCHES_SOURCE_AND_PROTECTED_FILES`
- `PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_MATCH_CLEAN_DISPOSITION_CONTRACT`

Only after reviewing this frozen lane, run exactly once:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File `
  '.\Scripts\run_body_shop_robot_native_unreal_import_lane_v001.ps1' `
  -Acknowledgement ARCHIVE_TWO_FAILED_RUNS_MOVE_INVALID_NAMESPACE_AND_CLEAN_IMPORT_HIGH_ELBOW_MONOTONIC_V001_ONCE
```

The runner refuses active Unreal/build processes, a prior PASS receipt, any
hash/inventory drift, or anything other than the exact invalid namespace. It
materializes each native process handle immediately after `Start-Process`,
waits with a timeout, flushes redirected streams, and null-checks the retained
PS5.1 `ExitCode`. It invokes no UBT. The importer and validator are two distinct
full `UnrealEditor.exe` processes with compilation disabled.

Expected PASS receipts are:

- `PASS__TWO_FAILED_RUNS_AND_INVALID_NAMESPACE_ARCHIVED_BYTE_FOR_BYTE__INVALID_NAMESPACE_ATOMICALLY_MOVED__CONTENT_PATH_ABSENT`
- `PASS__INCIDENT_ARCHIVED_AND_INVALID_NAMESPACE_MOVED__FRESH_8_ASSET_3_LOD_HIGH_ELBOW_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001_IMPORT`
- `PASS__INDEPENDENT_FRESH_PROCESS_LOAD__INCIDENT_ARCHIVE_VERIFIED__8_ASSETS_3_LODS_MONOTONIC_ONE_UV_BODYSHOP_ROBOT_NATIVE_V001`
- `PASS__INCIDENT_ARCHIVED_NAMESPACE_MOVED_CLEAN_IMPORT_AND_INDEPENDENT_FRESH_LOAD_BODYSHOP_ROBOT_NATIVE_V001`

Successful technical intake still is not promotion. Real-cell swept collision,
contact/direction, management-view material readability and automatic LOD
selection, packaged performance, actual-player release validation, and
save/restart/load remain separate gates.

## Final executed lane

The guarded clean-import lane completed successfully at
`Saved/Audits/BodyShop/RobotNative_v001/UnrealImportLane/20260814T204134Z-19e41ca7`.
The lane summary SHA is
`B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73`,
the clean import receipt SHA is
`B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF`,
and the independent fresh-load receipt SHA is
`9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA`.
Downstream current validators are pinned to these exact three artifacts and to
the aggregate LOD totals `2628 / 1964 / 1356`; earlier provisional recovery
receipt shapes do not satisfy the current gates.
