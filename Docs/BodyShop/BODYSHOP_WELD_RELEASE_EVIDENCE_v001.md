# Body Shop Weld Release Evidence v001

**Evidence date:** 2026-08-14  
**Scope:** the isolated Body Shop underbody-weld vertical slice in Development builds.  
**Decision:** the slice is evidence-backed for continued Early Access development and demonstration. This is not a claim that the full Body Shop, the whole game, or a Shipping build is release-ready.

## Historical pre-native-robot evidence set

The receipts below remain valid evidence for the earlier 22-component/nine-mesh
build. They are superseded for the current native Base/J1-J6/open-C-gun build and
must not be used to authorize a new release or package.

| Gate | Result | Authoritative artifact | SHA-256 |
|---|---|---|---|
| Full automation plus actual-player PIE | `PASS__BODY_SHOP_FULL_AUTOMATION_AND_ACTUAL_PLAYER_PIE` | `Saved/Audits/BodyShop/Experimental_v001/ReleaseValidation/20260814T122821Z/release_validation_summary_v001.json` | `C5293832AAD3948842B5051CFCF634262E761D5111450E0859A9243794C99A4A` |
| Development package, save/restart/load | `PASS__BODY_SHOP_DEVELOPMENT_PACKAGE_TWO_PROCESS_V002` | `Saved/Audits/BodyShop/Experimental_v001/PackageValidation/20260814T123208Z-4180e2f7/development_package_summary_v002.json` | `8E4C7043B2588650F962F6DC728DF438A7A8A0B08FB13AAF7CBD2A3CF8F81F51` |
| Packaged real-RHI performance and renderer LOD run | `PASS__BODY_SHOP_PACKAGED_PERFORMANCE_LOD_VALIDATION_RUN_V002` | `Saved/Audits/BodyShop/Experimental_v001/PackagedPerformanceLODValidation/20260814T124258Z-1f9a4c36/packaged_performance_lod_validation_summary_v002.json` | `1A55F282F74FE6DDD0115C1F1759FCC8187ECB03ADBCCB9A7CB5CB0B3C9258B3` |
| Numeric performance and renderer-selected LOD gate | `PASS__BODY_SHOP_PACKAGED_NUMERIC_PERFORMANCE_AND_RENDERER_LOD_GATE_V002` | `Saved/Audits/BodyShop/Experimental_v001/PackagedPerformanceLODValidation/20260814T124258Z-1f9a4c36/packaged_performance_lod_gate_v002.json` | `5CADCF43EEA4B5843FEDA59E0905C4EC491AC423BA2BF30C2960A25A782A09AA` |

That historical release run completed 35 tests: 34 clean successes, one warning-only teardown success, and zero failures or unrun tests.

The final native robot intake, native support-kit v002 intake, post-binding
build, current 43-test PASS and the required downstream receipt regeneration are recorded in
`Docs/BodyShop/BODYSHOP_NATIVE_ROBOT_FINAL_RELEASE_REFRESH_v001.md`.

## Current native-support refresh boundary

The current runtime binds exactly one non-WIP native service-dressing actor with
three HISM batches and 12 instances (six empty-return carts, three
component-service pallets and three open empty small-parts crates), plus the
native v002 full panel stillage. Compilation and the exact 43-test Body Shop
inventory passed; the automation index is
`Saved/Automation/BodyShop/NativeSupportFullBaseline_v002_20260814T230022Z/index.json`
with SHA-256
`C7868BDF7471829140C2298CF1131860D4E535CFB9E2A41C1DA9269C076FD2A9`.

This does not upgrade the historical dynamic release evidence below. Fresh
material v004, functional-HISM v004, actual-player PIE v003, Development package,
IoStore manifest and packaged-performance receipts are still required. The
core renderer contract remains 25 components across 10 meshes; the 12 native
service instances affect whole-scene totals only.

## What the slice now proves

- An actual player can enter the prototype, place and rotate equipment without mutating the selected catalogue item, start the automatic cycle, observe starvation, transfer/presentation, mirrored underbody welding, conveyor movement, inspection, blocked output, quality hold, quality pass, and completion.
- A single persistent `BIW_UNDERBODY` WIP is aligned to a continuous straight skid conveyor. The cell has readable floor paint and markings, open safety fences/guards, buffers, fixture dressing, and a vision gate.
- The material handler has its own eight-cup panel-pick tool and authored handling role. The two weld robots retain inward-facing C-guns, correct mirrored base mounts, and several repeated mirrored work poses instead of sharing one identical rear-bin-to-car motion.
- Robot articulation can be paused and resumed with the simulation, allowing deterministic welding validation and captures without stale robot motion. Save/restart/load restores one logical and one visible WIP at `WELDING_UNDERBODY`, with an identical isolated-save SHA before and after reload.
- The explicit Development map ran successfully without changing the project default map. The package manifest and protected-content checks passed.

## Management and focus performance

Both packaged views used D3D12/SM6 at 1920 x 1080 with automatic LOD selection, 300 captured frames, and 260 settled frames. All configured budgets passed.

| Metric | Management view (5,480 cm) | Focus view (3,400 cm) |
|---|---:|---:|
| Frame time p95 / p99 | 10.3342 / 12.5186 ms | 10.6336 / 13.3796 ms |
| GPU time p95 | 4.1078 ms | 4.3638 ms |
| RHI draw calls p95 | 259.05 | 274.05 |
| RHI primitives drawn p95 | 120,421.7 | 126,933.8 |
| Physical memory used p95 | 2,697.786 MB | 2,734.2625 MB |
| Physical memory free p05 | 15,990.6963 MB | 15,997.5437 MB |
| GPU local memory p95 / budget | 3,868.9961 / 11,229 MB (34.4554%) | 3,870.6836 / 11,229 MB (34.4704%) |
| Renderer-selected target LODs | LOD2: 22 | LOD1: 1; LOD2: 21 |

This historical LOD proof covers exactly 22 target components across nine unique
meshes. The current core runtime contract is 25 target components across 10
unique meshes, now accompanied by 12 native service-dressing instances, and
requires a fresh packaged-performance run.

## Lessons applied from Car Manufacture

The comparator review was read-only; no proprietary code, meshes, textures, or other assets were copied.

- Build machines and vehicles from modular rigid parts, with separate links, tools, and presentation components, so animation, replacement, validation, and LOD remain inspectable.
- Reuse a small library of repeated authored programs by station role and robot slot. Repetition gives an industrial rhythm, while the handler and mirrored welders remain functionally distinct.
- Prefer useful station density, clear silhouettes, material separation, and readability at management and focus distances over maximizing or minimizing raw triangle counts in isolation. The measured automatic-LOD result is the acceptance evidence.

## Known weld-contact limitation

The current C-guns face inward and the robots show visibly fuller, mirrored articulation, but they do **not** make credible physical contact with the underbody. Every authored candidate work point remains more than 200 cm from its intended fixture target; the validation contract for a believable contact is at most 12 cm with a tool-direction dot product of at least 0.95.

This is a source geometry constraint, not a value that should be hidden with fake sparks or moved targets. The inherited J2/J3 travel is only approximately +/-5 degrees, J4 remains locked, and the current tool-flange/socket geometry and cell layout cannot safely close the reach. Credible contact requires a verified articulation/geometry and tool-socket rebuild and/or a deliberate robot-base/fixture-layout revision, followed by renewed proximity and direction tests.

## Narrow Early Access readiness statement

**Green:** use the historically evidenced bounded Development underbody-weld
slice as an Early Access candidate for gameplay iteration, user feedback,
demonstrations, and continued content production. Its earlier actual-player PIE,
Development packaging, isolated save/reload, real-RHI performance and
renderer-selected LOD evidence remain green for that exact earlier build.

**Refresh pending:** do not describe the newly bound native-support build as
dynamically release-validated until the ordered v004/v003/package/performance
receipts above have been regenerated.

**Not green:** claim finished contact welding, a complete Body Shop, Shipping-build readiness, full campaign readiness, Paint or Assembly readiness, or global game release readiness. The contact-geometry limitation above remains explicit release debt for the weld presentation.

Press, campaign saves, legacy Body Weld, default-map behaviour, and other protected production content remain outside this slice and were preserved by the authoritative gates.
