# Cairnwell 2040 Runtime v001 — guarded Unreal import lane

Status: `APPROVED_V005__OFFLINE_FREEZE_AUTHORIZED__UNREAL_NOT_AUTHORIZED`

This is an offline authority-freeze record. Cairnwell `ProductionCandidate_v005` is the approved runtime winner, and its exact final manifest, manually authored and visually validated manual paint-mask, chronology-preserving approval supersession, and additive-freeze v002 amendment are frozen source authority. Only the offline input-contract and project-baseline freeze is authorized at this status. No Unreal import, destination materialization, runtime binding, or map work is authorized or underway.

## Truthful source identity

The planned runtime vehicle is the approved **Meshy-derived** Cairnwell `ProductionCandidate_v005` modular authority. Its emerald exterior and rolling-gear visual authorities retain Meshy-derived provenance, and its BIW authorities remain the supporting v005 modular sources. This lane must never describe the vehicle, its panels, or its textures as `Native`, clean-room, or provenance-free.

`ProductionCandidate_v006` was rejected as the runtime authority because its roof/window edges showed speckling, its glazing read as foil, and its fragmented PackedMR.A paint-mask candidates produced unsafe false positives. It is retained only as comparison evidence/alternate BIW work. No v006 FBX, texture, mask, or manifest may enter this v005 runtime closure.

The only reserved Unreal destination is:

`/Game/LineBoss/Factory/OneFactory/v001/Vehicles/Cairnwell2040Runtime_v001`

That namespace is fresh and absent. It does not authorize reuse, overwrite, reimport, deletion, migration, or cleanup in any existing vehicle namespace.

The contract accepts exactly this manifest and no fallback:

`SourceAssets/Candidate/Vehicles/Cairnwell2040/FinishedVehicleRuntimeDerivative_v001/ProductionCandidate_v005/MANIFEST_v005.json`

The manifest must declare `selected_candidate=ProductionCandidate_v005` and `selected_version=v005`. Every one of the 12 imported FBXs and three textures must reside beneath that exact v005 root. The path, winner identity, and source hashes must not be inferred from previews, intermediate Meshy exports, older manifests, screenshots, or filenames.

## Exact planned runtime closure

The approved manifest must close exactly four modular mesh roles under their frozen asset names:

| Exact role | Exact mesh asset name |
| --- | --- |
| `BIW_AutomotiveSkeleton` | `SM_LB_C2040_BIW_AutomotiveSkeleton_v001` |
| `BIW_UnderbodySubset` | `SM_LB_C2040_BIW_UnderbodySubset_v001` |
| `EmeraldBodyVisualAuthority` | `SM_LB_C2040_EmeraldBodyVisualAuthority_v001` |
| `EmeraldRollingGearVisualAuthority` | `SM_LB_C2040_EmeraldRollingGearVisualAuthority_v001` |

Each role must provide authored `LOD0`, `LOD1`, and `LOD2` FBX sources in that order. The lane therefore expects 12 pinned FBX source files, but produces four Unreal Static Mesh packages.

The exact texture semantics are:

1. `base_color`
2. `metallic_roughness`
3. `normal`

The manifest must declare exactly these four material authorities:

| Authority | Exact asset name | Exact recipe | Required purpose |
| --- | --- | --- | --- |
| Emerald body | `M_LB_C2040_BodyPaintTintPBR_v001` | `textured_tint_pbr` | Player-selectable painted body |
| Emerald rolling gear | `M_LB_C2040_RollingGearPBR_v001` | `textured_pbr` | Untinted wheels and rolling gear |
| Galvanised BIW | `M_LB_C2040_BIWGalvanized_v001` | `solid_pbr` | Galvanised structural metal |
| ED-coat | `M_LB_C2040_EDCoat_v001` | `solid_pbr` | Electrodeposition-coated underbody/BIW finish |

The body recipe must expose an Unreal Vector Parameter named exactly `VehiclePaintColour`. Its Base Color graph has one exact absolute-hue topology. The original linear base-colour sample feeds Lerp A and a Rec.709 luminance Dot Product with weights `[0.2126, 0.7152, 0.0722]`; luminance is multiplied by `1.35`, clamped to `[0.35, 1.15]`, and multiplied uniformly with `VehiclePaintColour.RGB` so the configured hue is preserved while source tonal detail remains. That detailed colour feeds Lerp B. The exact v005 manifest must declare the manually authored `metallic_roughness` texture's A channel as `BodyPaintMask`, and that sampled A channel may feed **only** Lerp Alpha. It must not drive metallic, roughness, normal, emissive, opacity, or any rolling-gear input. The same base-colour sample must feed the untinted path and luminance derivation. Simple multiplication by the emerald source RGB and flat colour replacement are both forbidden. The rolling-gear `textured_pbr` recipe remains untinted and must not contain or consume the player paint parameter or paint-mask graph.

The mesh and material asset names listed here are frozen lane identities. The winning manifest must match every name exactly or contract generation fails. The `EmeraldBodyVisualAuthority` slots must resolve to the body authority and never the rolling authority, while `EmeraldRollingGearVisualAuthority` slots must resolve to the rolling authority and never the body authority. The two BIW roles must resolve only to their declared galvanised or ED-coat solid authorities. Every material slot must resolve exactly once and remain in the same order across all three LODs.

The final Unreal package closure is fixed:

| Asset class | Exact count |
| --- | ---: |
| Static Mesh | 4 |
| Texture2D | 3 |
| Material | 4 |
| **Total packages** | **11** |

In short: **4 meshes + 3 textures + 4 materials = 11 packages**. No redirector, material instance, generated collision asset, auxiliary texture, or extra package is part of this lane.

This four-mesh runtime vehicle closure is deliberately disjoint from the separate panel-module lane and its namespace. No stamped/body panel module package is an input, destination, dependency, or authorized side effect here; the exact 11-package closure makes cross-lane inclusion fail closed.

## Source gates before any freeze

The exact v005 manifest must explicitly declare `approval_status` as `APPROVED_FOR_GUARDED_UNREAL_IMPORT`. Before the offline contract can be frozen, the preparer must verify all of the following from the manifest and pinned files:

- the exact four roles, three texture semantics, four material recipes, and 11-package dependency closure;
- an exact `+X` forward, `+Z` up, shared zero vehicle datum;
- three authored FBX LODs per role with pinned paths, byte counts, and SHA-256 hashes;
- a manifest- and audit-backed closed-body-shell declaration for `EmeraldBodyVisualAuthority`, plus an eight-part pre-combine rolling-gear declaration covering four tyres and four rims;
- positive bounds, shared pivot within 0.01 cm, exact triangle counts, positive source/imported vertex counts, zero source degenerate triangles, and a strictly descending LOD triangle chain (FBX seam splits mean Blender and Unreal vertex totals are not falsely equated);
- zero or one UV channel per mesh LOD, with exactly one UV channel wherever the textured material is bound;
- stable semantic material slots and exact one-to-one material bindings across every LOD;
- three pinned standalone lossless 2048×2048 texture sources: sRGB base colour, non-colour RGBA packed metallic/roughness/body mask, and non-colour tangent normal data, with exact source channel counts, Unreal compression, channel mapping, and explicit OpenGL/DirectX convention (OpenGL must flip green for Unreal; DirectX must not);
- an exact `paint_mask_authority` block with status `APPROVED__MANUALLY_AUTHORED_V005_BODY_PAINT_MASK__VISUALLY_VALIDATED`, `selected_version=v005`, `manual_authored=true`, `v006_mask_reused=false`, `texture_semantic=metallic_roughness`, `channel=A`, `false_positive_fragment_count=0`, and a pinned audit path/hash/byte count beneath the v005 root;
- an exact `Audit/Cairnwell2040_v005_FinalApprovalSupersession.json` record with schema `lineboss.cairnwell2040.v005.final-approval-supersession.v1` and status `APPROVED__V005_MANUAL_MASK_SUPERSEDES_HISTORICAL_DO_NOT_PROMOTE_WITHOUT_DELETION`; it must name and hash the preserved historical hold marker, final manifest, final manual-mask audit, final mask texture, and exact front/hero/rear/side manual-mask renders;
- the corrected supersession must use the exact `$schema` key and remain 3319 bytes at SHA-256 `738E19C3D1D07028C0F2C107AD023F14DBC94FD44DAE2107411D6C8A317A348C`; the stale v1 additive receipt remains byte-exact at SHA-256 `F7C761D794F44E7EEEBB2958A7947F63D59D0EE828510E1803D7B69EA62642F0` and is evidence, not current contract authority;
- an exact `Audit/Cairnwell2040_v005_AdditiveFreezeReceipt_v002.json` record with schema `lineboss.cairnwell2040.v005.additive-freeze-amendment.v2`, status `PASS__V005_ADDITIVE_FREEZE_RECEIPT_V002__CURRENT_CONTRACT_AUTHORITY__SOLE_SCHEMA_KEY_CORRECTION`, 24420 bytes, and SHA-256 `7BCE6A5A1DF2C0080011D8EB78D24C5839B44A4755F65FD2939F0E562D75A4A0`; it must pin the stale v1 receipt, corrected supersession, sole `schema`→`$schema` correction, identical 36-file pre-existing before/after inventories, empty missing/unexpected/other-change gates, and the full 44-file final additive inventory;
- the exact body `textured_tint_pbr` contract: three Texture Samples, one `VehiclePaintColour` Vector Parameter, fixed linear-luminance weights, a Dot Product, normalization, Clamp, absolute-hue detail Multiply, and one Linear Interpolate; original base→luminance and Lerp A, parameter×clamped detail→Lerp B, and `metallic_roughness.A` `BodyPaintMask`→Lerp Alpha only;
- an untinted rolling `textured_pbr` binding, plus distinct galvanised BIW and ED-coat `solid_pbr` bindings, with body-versus-rolling role separation;
- the complete Meshy-derived v005 provenance statement and final visual approval, without relabelling the source as `Native` or accepting any v006 import source.

Any missing field, hash drift, extra role, extra package, unapproved status, or visual freeze ambiguity keeps this lane in the waiting state.
The pre-existing `PENDING_ROOT_VISUAL_APPROVAL_DO_NOT_PROMOTE.md` is preserved byte-for-byte as chronology evidence. It is never deleted or rewritten. Contract creation is allowed only when the separate final supersession record both hashes that exact marker and explicitly sets `historical_marker_preserved_byte_exact=true` and `supersedes_historical_marker_without_deletion=true`, and the v002 amendment independently pins the preserved stale v1 receipt plus the corrected current supersession. An absent amendment, stale linkage, any hash drift, or any no-other-drift inventory failure fails closed.

## Prepared import policy

If and only if the exact v005 authority and its manual paint mask are approved and frozen, the later importer is constrained to the fresh namespace above:

- import LOD0 as one combined mesh for each role, then attach its authored LOD1 and LOD2;
- import textures separately and build the four controlled Unreal materials rather than accepting FBX-created materials or textures; preserve the exact `VehiclePaintColour`/paint-mask Lerp graph for later player paint selection;
- disable automatic lightmap-UV generation, automatic collision generation, degeneracy removal, and animation import;
- set manual LOD screen sizes to `1.0`, `0.35`, and `0.12`;
- disable Nanite and navigation data;
- require zero simple and zero convex collision primitives and use `CTF_USE_SIMPLE_AS_COMPLEX`;
- create and save only the exact 11 expected packages;
- preserve partial artifacts for explicit review if a guarded import fails; automatic cleanup is not authorized.
- run the full editor with positional `/Engine/Maps/Entry`, the exact transient `LoadLevelAtStartup=None` command-line override, `-NoAutoSave`, and `-NoSaveOnExit`; Python must prove the active bootstrap world is exactly `/Engine/Maps/Entry.Entry` before touching assets.

Overwrite, reimport, deletion, project-map load/save, runtime binding, map promotion, and writes to `Source`, `Config`, maps, or campaign saves are outside this lane. The immutable Engine Entry bootstrap is not a project map and may never be saved.

## Offline authority artifacts

The offline authority state must be coherent: these four artifacts are either all absent before the one-shot offline freeze or all present afterward. A partial state fails closed:

- `Scripts/cairnwell_2040_runtime_v001_import_contract.json`
- `Scripts/cairnwell_2040_runtime_v001_import_contract.sha256`
- `Scripts/cairnwell_2040_runtime_v001_import_baseline.json`
- `Scripts/cairnwell_2040_runtime_v001_import_baseline.sha256`

The destination Content directory and lane result receipts remain absent in either offline state. The contract preparer and baseline preparer use standard Python only and do not authorize or launch Unreal.

## Later guarded sequence

The offline contract and baseline portions of the sequence are authorized. Steps that start Unreal remain descriptive only until a separate explicit coordination decision.

1. Reverify the exact approved v005 manifest with all pinned source hashes, explicit v005 winner identity, and the pinned manual-mask visual audit proving zero fragmented false positives and no v006 mask reuse. Preserve the historical hold marker and stale v1 receipt byte-exact; require the corrected supersession and v002 amendment chain described above.
2. In standard offline Python, pass that exact `MANIFEST_v005.json` path and freeze the import contract once using its v005-specific acknowledgement. Review the generated JSON and SHA-256 sidecar.
3. Still offline and before Unreal, freeze the complete project baseline once. It must cover the source authority, prepared lane files, project descriptor, all `Source`, all `Config`, all existing Content outside the fresh destination including maps, and campaign saves.
4. Reverify the contract, baseline, source, protected project inventory, empty destination, absent prior receipts, and exact runner acknowledgement.
5. Start **Unreal process A** for import only with the exact Engine Entry/bootstrap override guards. It may materialize the four meshes, three textures, and four materials inside the fresh namespace and write the import receipt under the dedicated audit run directory. It must not load or save a project map.
6. Exit process A and prove that no Unreal Editor, commandlet, Crash Reporter, or build process remains.
7. Start a distinct **Unreal process B** with the same Engine Entry/bootstrap override guards for read-only fresh-process validation. It must reload the contract and baseline, prove a different process identity, validate LODs, UVs, slots, bounds, pivots, triangles, textures, the exact `VehiclePaintColour`/paint-mask Lerp graph and body-versus-rolling bindings, Nanite/collision/navigation policy, exact dependency closure, and package hashes, then write only the validation receipt.
8. Exit process B, prove all relevant processes are gone, re-run the exact v005 contract/source verification, reverify the baseline-pinned source/protected/lane inventories in post-import mode, and independently re-hash all 11 packages from disk. Those hashes must equal both the import receipt and validator hashes.
9. Only after both receipts pass may a separately reviewed task consider runtime binding or map promotion. Neither is part of this import lane.

This two-process boundary is mandatory: importing and validating in one Unreal process is not an acceptable substitute for fresh-process validation.

## Current decision

Freeze and reverify only the offline contract and project baseline from the exact approved v005 authority chain. Do not run Unreal, create the destination, generate import receipts, bind the vehicle, or touch maps until the guarded one-shot Unreal lane is explicitly coordinated. Continue to reject every v006 import or paint-mask source.
