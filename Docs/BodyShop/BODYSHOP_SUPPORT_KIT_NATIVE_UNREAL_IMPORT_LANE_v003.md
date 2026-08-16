# Body Shop native support kit v002 — guarded Unreal import lane v003

Status: `PASS__IMPORTED__FRESH_LOAD_VALIDATED__RUNTIME_BOUND__RELEASE_CHAIN_STATIC_GATES_READY`

The guarded one-shot import completed on 2026-08-14. The source freeze remains
immutable; no second import is authorised.

This lane replaces the failed v002 execution without rewriting its history. The
v001 provisional lane remains byte-for-byte preserved. The failed v002 run logs
and receipts remain immutable, while its twelve partial v001 packages must be
copied to an exact-hash archive and moved to a recoverable quarantine before the
new destination is created. No file deletion or overwrite is authorised.

## Frozen source and isolated result

The independently validated source is
`SourceAssets/Candidate/WeldShop/BodyShopSupportKitNative_v002`. Its 90-row
freeze proves exactly 12 clean-room procedural assets, 36 explicitly
triangulated LOD meshes and 72/72 exact FBX/GLB round-trips. Every LOD has one
`UVMap`, identity transforms, an XY-centred floor pivot and a healthy strictly
decreasing triangle chain. Aggregate triangles are 20,408 / 7,580 / 1,780.

The only new Content write root is:

`/Game/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002`

It must be absent before execution and may contain exactly 12 StaticMesh
packages assembled from exactly 36 FBX sources:

- Logistics: empty/full panel stillages, empty-return cart, component-service
  pallet, open small-parts crate and open small-parts bin.
- Controls: electrical cabinet and HMI pedestal.
- Safety: 2 m guard panel and 2 m interlocked guard gate.
- Services: utility pedestal and weld-extraction pedestal.

## Protected project state

The baseline pins the project descriptor, the complete `Source` and `Config`
trees, campaign saves, every existing Content file outside the new destination,
the eight current native robot packages, Press v913, the restored full Press map
and the Body Shop map. The three protected map hashes are:

| Authority | SHA-256 |
|---|---|
| Press v913 | `26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6` |
| restored full Press map | `D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5` |
| Body Shop map | `8CB6976C532F5C06635ADC8ED00BB50CAF39FFCE2F15826C3456C6EDF4CACE8F` |

## Import and independent validation contract

- LOD0 uses legacy `FbxFactory`; replacement, material/texture import,
  generated lightmap UVs, generated collision, degeneracy removal and Nanite
  are disabled.
- `Interchange.FeatureFlags.Import.FBX` is disabled only around the 24 custom
  LOD1/LOD2 imports and its exact prior value is restored in `finally`.
- Nine semantic material slots bind only to existing hash-protected Body Shop
  presentation materials. No material or texture package is created.
- Every asset receives one deterministic AABB box, zero convex hulls and
  `CTF_USE_DEFAULT`; Nanite remains disabled.
- Manual LOD screens are exactly `[1.0, 0.45, 0.18]`, written twice only after
  all LOD, material, collision and Nanite edits have completed.
- A second full UnrealEditor process independently and read-only rechecks all
  12 packages, all 3 LODs, exact triangles, one UV channel, section/material
  order, bounds/pivots, collision, Nanite, screens and package hashes.

The PowerShell 5.1 runner retains the native process handle, performs timed and
flushing `WaitForExit` calls, refreshes the process and rejects a missing or
non-zero exit code. It starts exactly two hidden full `UnrealEditor.exe`
processes with `-NoCompile`, and never invokes UBT, AutomationTool or
`UnrealEditor-Cmd`.

## One-shot recovery

Before Unreal starts, the runner verifies the exact twelve partial v001 package
hashes and seven failed v002 evidence hashes. It creates independent archive
copies of both sets, verifies every copied byte, then moves the original partial
package namespace into a same-project recoverable quarantine. The original
failed run evidence remains in place and protected. A receipt records all three
inventories. The operation uses no recursive delete and refuses every existing
archive, quarantine, destination or v003 result.

## Frozen lane hashes

| File | SHA-256 |
|---|---|
| baseline v003 | `A124CE80D77717C062CFFE5AFDD5058905957D29B8A8BB01979A4567149653A6` |
| freezer v003 | `249FAFC90068E56D28A6D472730AF885495D7435F4BFEAE82BA55FC88C705A0E` |
| importer v003 | `5F3C31C39A91C2A27C7EAB2A2D8E3EB264014076AB221EDA9EB28003B21E554A` |
| independent validator v003 | `10E8D3B11358540671E52AF56BA3F30FF24BDBB95453A5BE5CEF268A1E4DF606` |
| runner v003 | `BD85E71B15A00DDE80AF48F882F059163679DCF79AB85C34278180C6D8AB5FC8` |
| offline tests v003 | `39740328EEF71B3CBF124B599124E84305B645C66E98B519A3C1E1BB8C751059` |

## Exact guarded one-shot command

All final hashes and offline gates pass. Root may execute the command below
exactly once while the destination, recovery root and v003 audit root remain
absent and all protected hashes remain unchanged:

```powershell
& 'C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Scripts\run_body_shop_support_kit_native_unreal_import_lane_v003.ps1' -Acknowledgement 'IMPORT_FROZEN_BODYSHOP_SUPPORT_KIT_NATIVE_V002_BASELINE_V003_ONCE'
```

This command has now been consumed and must not be run again. Do not run v001 or
v002, and do not manually delete, move, replace or reimport either support-kit
namespace.

## Executed authority and runtime binding

The successful run root is
`Saved/Audits/BodyShop/SupportKitNative_v002/UnrealImportLane_v003/20260814T223952Z-fa3434b0`.

| Evidence | SHA-256 |
|---|---|
| failed-v002 recovery receipt | `BBE9F02910027B111B07CBABE163CDE3A139DE065FF8E24FE99BB497470090F6` |
| import receipt | `F5E1735BE76AD9F2086AE1B533CA92DD240D740129A9BBC147A872D818B2F286` |
| fresh-load receipt | `CDFA05DF4425695F8B6ABC8A06B17F377F6840739E207978E2595FA5A7B3DE82` |
| lane summary | `6797C6C7E295C00D1921DFB378100C26C9905848E8EF63DB0501BBA0FC583C22` |

The Body Shop runtime now uses the full native v002 stillage. One transient,
non-WIP `LB_BodyShop_ServiceDressing_v002` actor presents three HISM batches:
six empty-return carts, three component-service pallets and three open empty
small-parts crates. All 12 presentation instances are visual-only and preserve
the existing layout identities and transforms.

`Config/DefaultGame.ini` retains every legacy cook root and adds the native
robot and support-kit roots; its release-chain authority hash is
`4458BB41EE3A56B67B8ECDD6954A46B23FD038A9CB8294E9A79C48580A86852B`.

The shared read-only downstream authority is
`Scripts/body_shop_support_kit_native_v002_contract.py`. Material, HISM,
actual-player PIE, Development package, exact IoStore manifest and packaged
performance gates all call it and fail closed on any receipt, package, LOD,
material-binding or hash drift.
