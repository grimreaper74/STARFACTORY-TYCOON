# Body Shop native robot final release refresh v001

**Frozen intake:** 2026-08-14 final native-robot clean-import lane
`20260814T204134Z-19e41ca7` plus native-support guarded import lane
`20260814T223952Z-fa3434b0`  
**Scope:** downstream Body Shop material, HISM, actual-player, release,
Development package, manifest and packaged-performance validators.  
**State:** scripts are pinned to both final intakes; all downstream receipts
created before this refresh are historical and must be regenerated.

## Final native robot authority

| Evidence | SHA-256 |
| --- | --- |
| `lane_summary_v001.json` | `B1AFEDB019C28B04082497F46B954C29262D0A30B19854D00CF1168537AA2F73` |
| `import_receipt_v001.json` | `B7738C068F344BBA391442F404E38A87BAF0C70B72A19CD2CA5DDDC68A5210BF` |
| `fresh_load_validation_receipt_v001.json` | `9A4097CBB68F46297031A092FF861B20FC4B2F60576150005B483D984E26EBEA` |
| clean-import baseline | `D967E8CD1596FC620066668138FEE14A47C702D55989FB1DB1C3AAF0ABF0FF31` |
| clean-disposition contract | `E9862B44C656586879EF3607C33BD8A536E9CE0D816C144AFF870C31A7B52BC3` |

The accepted family is Base, J1-J6 and open C-gun: eight assets, three LODs each, one UV channel on all 24 LODs, strict per-asset triangle reduction and aggregate triangle totals `2628 / 1964 / 1356`. The downstream gates also bind each of the eight final `.uasset` hashes instead of accepting any later receipt with a similar PASS string.

Post-import compilation passed at
`Saved/Audits/BodyShop/NativeRobotPostImportBuild/20260814T204529Z/build.stdout.log`
(`5709E2DF522FDF1737896E2005447B2357566A5ED1EBED3A4FE7E0FE0E87A7AB`).

After the native-support runtime binding, compilation passed again and the exact
current 43-test Body Shop inventory completed at
`Saved/Automation/BodyShop/NativeSupportFullBaseline_v002_20260814T230022Z/index.json`
(`C7868BDF7471829140C2298CF1131860D4E535CFB9E2A41C1DA9269C076FD2A9`):
42 clean successes, one warning-bearing success, zero failures and zero not-run
tests. Its inventory includes
`LineBoss.BodyShop.Experimental.ServiceDressing.UnconditionalNativeV002SpawnContract`.

## Native support-kit v002 authority

The successful guarded import root is
`Saved/Audits/BodyShop/SupportKitNative_v002/UnrealImportLane_v003/20260814T223952Z-fa3434b0`.

| Evidence | SHA-256 |
| --- | --- |
| failed-v002 recovery receipt | `BBE9F02910027B111B07CBABE163CDE3A139DE065FF8E24FE99BB497470090F6` |
| import receipt | `F5E1735BE76AD9F2086AE1B533CA92DD240D740129A9BBC147A872D818B2F286` |
| fresh-load receipt | `CDFA05DF4425695F8B6ABC8A06B17F377F6840739E207978E2595FA5A7B3DE82` |
| lane summary | `6797C6C7E295C00D1921DFB378100C26C9905848E8EF63DB0501BBA0FC583C22` |
| import baseline | `A124CE80D77717C062CFFE5AFDD5058905957D29B8A8BB01979A4567149653A6` |

The accepted support family is exactly 12 packages with three LODs per asset
and aggregate triangles `20408 / 7580 / 1780`. The runtime binds the v002 full
panel stillage and exactly one active non-WIP
`LB_BodyShop_ServiceDressing_v002` actor. Its three HISM batches contain six
empty-return carts, three component-service pallets and three open empty
small-parts crates. The shared downstream authority
`Scripts/body_shop_support_kit_native_v002_contract.py` checks the four receipts,
all 12 package hashes, all LODs and the material bindings before a gate can pass.

## Runtime and package contract

The current packaged core renderer target remains exactly 25 components across
10 unique meshes. Native service-dressing props contribute to whole-scene
totals, but do not redefine that core renderer manifest. The previous
22-component/nine-mesh package and performance receipts predate J6/open-C-gun
finalization, and every existing 25/10 receipt predates the native support-kit
binding; neither is current release authority.

The package manifest now requires both exact final validation receipts as
explicit arguments. It binds their lane/import siblings, verifies all eight
robot and all 12 support-package hashes, and requires every package in both
stage and archive IoStore listings. The active Body stillage must be the v002
support package.

## Press preservation

Every current Body Shop material/HISM/release/package/performance protected snapshot covers both:

- Press v913: `26A901442CFA8415E3875BD998A2E3220045E296C17829335552D64837A190A6`
- full restored Press factory map: `D3F8652AA45E7C2FCEE5AF1971F6AA78A3F027E60E361B039D14DAD5806C74A5`

Neither map is loaded, saved, cooked as a Body Shop dependency or otherwise modified by these validators. A hash change fails the current gate.

## Receipts that must be regenerated in order

1. `presentation_materials_v002_native_robot_support_kit_validation_v004.json`
2. `presentation_materials_v002_functional_hism_usage_validation_v004.json`
3. `presentation_materials_v002_functional_hism_usage_validation_summary_v004.json`
4. `ReleaseValidation/<UTC>/live_pie_release_validation_v003.json` and its
   `release_validation_summary_v001.json`
5. `PackageValidation/<UTC>-<id>/development_package_summary_v002.json` and its
   exact manifest receipt
6. `PackagedPerformanceLODValidation/<UTC>-<id>/packaged_performance_lod_gate_v002.json`
   and validation summary

Historical receipts remain evidence of their own earlier builds, but they cannot
authorize the final native robot packages, any native support package, the
service-dressing actor or the current package/performance chain.
