# Line Boss: Visual Changelog and Regression Ledger

**Baseline date:** 2026-08-13  
**Scope:** player-visible factory from inbound coil delivery to finished-vehicle handoff.  
**Purpose:** prevent a newer file, import, map, or render from being mistaken for a visual improvement without evidence.

This is append-only and supplements, rather than replaces:

- `Docs/ReleaseGate/VISUAL_ART_ASSET_LEDGER_v001.md`
- `Docs/VISUAL_ASSET_LEDGER_v001.md`
- the owner/engineering authority packs for each station.

## Non-regression rules

1. Functional engineering authority is never overwritten by visual work.
2. A candidate is not an improvement merely because it is newer, more detailed in isolation, or imported into Unreal.
3. Every claimed improvement needs a same-camera **before/current/after** evidence pair at the real player overview, plus a close technical view where relevant.
4. Runtime collision donors, blockouts, validation assets and Developer-only imports are not visual authority.
5. No candidate may hide moving mechanical process geometry, change the approved envelope, alter pivots, obstruct player/HMI/service clearances, or replace working light-state logic.
6. Any asset with flat-grey/missing materials, incorrect scale, wrong process role, melted Meshy topology, poor orientation, or darker/blockier presentation is a **regression** until corrected.
7. `v913` remains the protected clean map. Runtime proof is made only in a new direct child of `v913`.

## Status vocabulary

| Status | Meaning |
| --- | --- |
| **Engineering authority** | Functional source that must remain unchanged. |
| **Runtime baseline** | Current live player-build binding; may still be visually weak. |
| **Retained visual evidence** | Useful reference or approved source evidence, not automatically runtime-promotable. |
| **Candidate-only** | May be evaluated in isolation; no release/runtime claim. |
| **Do not reuse** | Explicitly rejected, wrong role, or known regression. |
| **Unproven** | No real player-runtime screenshot or gate evidence yet exists. |

## Current change record

At the time of this baseline there is **no new PR005 runtime art binding**. The detailed Meshy HMI has been identified and assessed only. No map, source authority, gameplay, save format, collision, pivot, or `v913` change is represented by this document.

## Factory-wide baseline

| Family | Functional / immutable baseline | Current runtime or project state | Best retained visual evidence | Known regression / do-not-reuse | Delta verdict | Required proof before promotion |
| --- | --- | --- | --- | --- | --- | --- |
| Opening hall, build UI, player overview | `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913` | Bright clean shell; current source overview is sparse/dim | `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v915/clean_builder_runtime.png`; packaged v016 `Saved/StagedBuilds/Windows_UMGOnly_AuthoredPress_v016/LineBossCarFactory/Saved/Screenshots/Windows/LineBoss_AutoCapture.png` | Do not treat the clean empty hall as finished factory art | **Unproven visual hold** | Same real overview camera before/current/after; lighting, route readability, density and cook proof |
| Inbound lorry / coil handling / AGVs | `SourceAssets/Candidate/PressShop/PRESS_SHOP_APPROVED_ASSET_MANIFEST_v20260810.json` | Player-placeable inbound dock | Owner review `.../InboundCoilDelivery/.../v808_ApprovalPack/Review/01_Lorry_Loaded_Hero_v808.png`; real Coil AGV sources | Softer rebaked Coil AGV v919 was rejected; do not replace a readable working asset with it | **Runtime-ready, visual evidence incomplete** | Overview screenshot, materials, collision/nav, save/reload, cook |
| PR004 depack | `SourceAssets/PR004/RoboticDepackRobot` | Engine-native presentation | Existing role-specific coil/depack sources | Do not solve its visual debt with unrelated press or Walker assets | **Proxy / unproven** | Owner visual authority, isolated import and runtime pair |
| PR005 decoiler / threader | Immutable `SourceAssets/Candidate/PressShop/PR005/OwnerApprovalPack_v20260809_v812/PR005_ExteriorEnclosure_OwnerReview_v812.blend` | `LBFactoryBuildMachine.cpp` uses 10 existing PR005 candidate modules, within the player-built PR005 package | Pre-skin original: `.../ArtDerivative_v002_MachineFirstRefined/Renders/00_PR005_v812_ExposedMachinePreview.png`; candidate machine-first views `01_PR005_v014_Front.png` to `06_PR005_v014_EngineeringShellDiagnostic.png`; engineering orthos `Saved/ValidationScreenshots/PR005/MeshySkinDesignPack_v001/01...08_*` | Do not direct-export v026 embedded HMI/cabinet: broken/null material assignments create flat-grey regression. Do not replace v812 with a skin-only, blockier or featureless enclosure. Skin v012/v013 and v026 are candidates only, not runtime proof. | **Runtime baseline retained; art candidate unproven** | Current overview baseline + candidate overview from same camera; verify visible mandrel/rolls/threader, HMI clearance, no collision/nav/overlap, material slots, Nanite/LOD, save/reload, cook |
| PR006 cassette leveller | `SourceAssets/PR006/PrecisionCassetteLeveller/Candidate_v001/PR006_PrecisionCassetteLeveller_Candidate_v001.blend`; moving authority `LBPR006Station.cpp` | `LBFactoryBuildMachine.cpp` compact 12-part candidate package | `.../Candidate_v001/Validation/pr006_v001_{operator,elevated,drive}.png`; dedicated `ReleaseDetail_v001` is a matched removable-detail source | Do not replace leveller with a coil winder, generic press, or arbitrary rack; do not hide roll/cassette/cylinder movement | **Candidate-only** | ReleaseDetail visual-only intake, operator clearance, moving-sweep test, overview pair, lights, save/cook |
| PR007 washer / lube | `SourceAssets/PR007/WasherLubeUnit/Candidate_v001` | Compact candidate package | `.../Candidate_v001/Validation/pr007_v001_{operator,elevated,drive}.png`; matched `ReleaseDetail_v001` | Do not use unrelated Meshy machine as a washer/lube replacement | **Candidate-only** | Detail overlay, fluid/mist/service clearance, overview pair, save/cook |
| PR008 servo blanking line | `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/Module01...Module10` | Existing detailed-module binding in `LBFactoryBuildMachine.cpp` | `.../Detailed_v001/Validation/pr008_module01...10_*_v001.png`; station-specific cabinets/HMI are part of this source | `EngineeringBlockout_v001` is blockout, not a quality reference. Do not stretch generic console/cabinet models onto it. | **Candidate-only** | Whole-assembly material/collision/LOD validation, real overview pair, motion/clearance, cook |
| PR009 blank stacker | `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/PR009_Source/CA_MW_PR009_AutomatedBlankStacker_ProductionSource_v002.blend` | `/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/*` | `.../Candidate_v002/PR009_Renders/v002/PR009_v002_{front,rear,left,right,top,isometric_restored,cctv_overview_restored,drone_inspection_restored}.png` | v087 is a collision donor, not final visual authority. Do not call it a visual improvement just because it is current runtime. | **Visual-debt / candidate-only** | Art-source import/overlay, collision remains separate, current player pair, save/cook |
| PR010 four-lane supermarket / press feed | Engineering `SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v103/CA_MW_PR010_ReleaseArt_v103.blend`; visual design `SourceAssets/Candidate/PressShop/PR010/ProDesignPack_v20260809_v820/PR010_PRO_DESIGN_JOB_v820.md` | Explicit `Blockout_v001` deck/lane beds plus v101 pallets/blank stacks | Existing four-lane engineering and ProDesign authority; role-correct roller conveyor/stillage/HMI only | No standalone Meshy “supermarket” exists. v103 is engineering/service-art candidate, **not** directly promotable final art. Direct Meshy v874/v882+ trials were melted/glossy and not promoted. | **P0 proxy** | New derivative retains four lanes/interfaces; before/after overview; material/scale/clearance; save/cook |
| Conveyors, panel handling, stillages | Factory-builder logistics authority | Mixed legacy/runtime bindings | `SourceAssets/Candidate/FactoryLogistics/PoweredConveyor_v001`; `SourceAssets/Candidate/PressShop/FinishedPanelStillage/Authorities/FP_STILLAGE_Meshy_Textured_AppearanceAuthority_UNTOUCHED.blend` | Do not use cargo rack as PR009 replacement or make a raw high-poly one-mesh source a runtime claim | **Candidate-only** | Modular visual-only derivative, payload/root/stack test, overview pair, cook |
| Body Weld fixture / BIW / robots / vision / tools | `SourceAssets/Candidate/WeldShop/BodyWeldRuntimeArt_v001/Freeze/FROZEN_v001.json` | `/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001` is imported/technical candidate; player binding pending | `Saved/ValidationScreenshots/WeldShop/WeldRobotRuntime_v001_r2/weld_robot_runtime_v001_family_front_oblique_r2.png`; role-specific fixture/MIG/spot/vision/pick sources | Raw high-poly Meshy robots/tools are reference sources, not direct runtime. Do not replace animation/pivots/tool sockets with a fused raw mesh. | **No player overview proof** | Full-cell binding, sockets/pivots, real weld/light state, visual pair, collision/LOD/Nanite, cook |
| ED coat | Existing technical source / `EDLineRuntime_Candidate_v001` | Deferred by work order | Existing ED tank/gantry/oven sources | Do not let ED polish hide unfinished press/Body Weld work | **Deferred** | Press and Weld completion first |
| Support / cleaning / maintenance robots | CR01 v065 / MR01 v022 approved authorities | Clean support-fleet bindings | Existing fleet assets | Do not spend visible-machine budget here while press proxies remain | **Runtime-ready / overview hold** | Lighting/material/overview/cook |
| Factory envelope | `SourceAssets/UnrealDerived/Architecture/FactoryEnvelopeKitRuntime_v001` | Candidate runtime envelope | Existing wall/door/loading Meshy source pool | Do not make factory dark or over-dress hidden bays before visible machines | **Candidate-only** | Player overview, glazing/two-sided, route clarity, lighting/cook |
| Cairnwell vehicle / finished drive-off | Existing Cairnwell 2040 visual/reference sources | Not imported for final runtime | `SourceAssets/Candidate/Vehicles/Cairnwell2040/*` | Reference-only vehicle panels/finished car are not a license to bind arbitrary high-poly source | **Blocked / deferred** | Press + Body Weld first; then vehicle semantic/runtime validation |

## Explicit historical regression holds

The following are retained as negative evidence and must not be revived merely because their files are newer or detailed:

- Old `ProDetailVisual_v354` / v923 captures: rejected visual lineage (`Docs/PROJECT_HANDOFF.md`, approx. lines 5207–5210).
- Initial v924 presses: sideways orientation, rejected (`Docs/PROJECT_HANDOFF.md`, approx. lines 5209–5212).
- v640: below-floor placement failure.
- v650/v651: approximately 82,000 cm scale failure.
- v654/v655: 1/100 scale failure.
- Washed-out newer Meshy texture trial: rejected (`Docs/PROJECT_HANDOFF.md`, approx. line 5234).
- Re-baked Coil AGV v919: softer/lower-readability result, rejected (`Docs/PROJECT_HANDOFF.md`, approx. line 5173).
- Press Train S02–S06 Walker / S03 fused reworks: separate family; prohibited as a shortcut for PR005–PR010.

## PR005 controlled first change

**Candidate:** intact textured Meshy HMI v632, as a separate visual-only asset—not the broken copied HMI within PR005 v026.

| Field | Recorded value |
| --- | --- |
| Immutable source | `SourceAssets/Shared/FactoryAssetLibrary/MeshyCabinetHMI_v632/SM_CA_Factory_OperatorHMI_MeshyMaster_v632.glb` |
| Dimensions | 0.522 × 0.733 × 1.212 m; 107,020 triangles |
| Texture proof | PBR base-colour, ORM, normal and emissive atlas survive prior Unreal developer-validation intake |
| Intended runtime destination | `/Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/HMI_v001` |
| Runtime lifecycle | Separate `PR005DetailedHMIVisual` component only; not added to the 75-part composite asset contract |
| Candidate transform | PR005 station-local `(-241, 300, 0) cm`, yaw `180°`, inherited `0.48` package scale |
| Functional protection | Existing HMI interaction target remains `(-241, 300, 105) cm`; no collision, no overlaps, no navigation; no process/pivot/save change |
| Light authority | Existing `ULBStatusBeaconComponent` remains authoritative. Meshy emission alone is not treated as working status lights. |
| Before evidence | `Saved/ValidationScreenshots/PR005/pr005_unreal_overview_v001.png`; `.../pr005_unreal_process_v001.png`; original v812 preview above |
| After evidence | **Pending fresh direct child of v913 and real player build** |
| Verdict before screenshot | **Unproven candidate — not an improvement claim** |

## Required entry for every future change

Append an entry containing:

1. exact source, derivative and Unreal runtime paths;
2. immutable engineering authority and protected functionality;
3. original/current/candidate status;
4. player-overview **before** and **after** screenshot paths using identical camera/framing;
5. close technical screenshot path where material, screen, light, socket, pivot or collision needs inspection;
6. visual delta verdict: `improved`, `equal`, `regressed`, or `unproven`;
7. materials, bounds/scale, pivot/sockets, collision, nav/overlap, LOD/Nanite, save/reload and cook results;
8. any rejection, rollback location, or reason the asset must not be reused.

No entry may be marked **improved** until all applicable gates above are evidenced.

## 2026-08-13 � PR005 detailed HMI v001 candidate binding

- **Change:** Added PR005DetailedHMIVisual as an isolated visual-only component of ALBFactoryBuildMachine; it loads the freshly imported SM_CA_MW_PR005_dHMI_Meshy_v001 from /Game/LineBoss/Stations/Press/PR005/Candidate_v001/ArtDerivatives/HMI_v001/....
- **Functional boundary:** deliberately excluded from GCoilPreparationVisualSpecs, CoilPreparationVisualAssets, and PlaceholderParts; the 75-part functional press contract, original HMI interaction datum, pivots, ports, process/save state, status beacon and v913 map are unchanged.
- **Placement:** PR005 local (-115.68, -856.00, -350.00) cm, yaw 180 deg, uniform scale  .48; source texture atlas retained unchanged.
- **Physics:** forced NoCollision, overlaps off, navigation off before and after generic presentation sync.
- **Texture policy:** preserve imported full PBR atlas; do not globally retint mixed screen/control/label/cable material.
- **Build:** LineBossCarFactoryEditor Win64 Development � succeeded 2026-08-13.
- **Automation:** CoilPreparationImportedCompositeAssetContract, CoilPreparationCookManifestContract, OrderedCatalogueAndPersistence � 3/3 succeeded; report Saved/Automation/PR005_DetailedHMI_v001/index.json.
- **Visual status:** runtime-ready candidate; not release-ready. The existing QA screenshot was invalid because positional Python rotation inverted the mesh below the floor; bounds audit confirms the imported mesh is valid and upright when given yaw-only rotation. A real player-overview before/current/after pair and final cook remain open.
- **Explicit exclusions:** no external PR005 roof-height cable tray (CW_PR005_V014_UtilityTray) or dependent exterior hose drops/glands. Retain engineering floor hydraulic routing only.

### PR005 detailed HMI runtime-cell overview evidence (2026-08-13)

- **Capture:** Saved/ValidationScreenshots/PressShop/PR005_DetailedHMI_v001/pr005_runtime_cell_overview_v005.png � 1920x1080, 48-degree FOV, temporary in-play PR005 cell on v913; the actor was spawned only for capture and the editor exited without saving.
- **Runtime assertion:** passed. PR005DetailedHMIVisual was visible with SM_CA_MW_PR005_dHMI_Meshy_v001, its original Material_0, and NoCollision; logged in Saved/Logs/LineBossCarFactory.log at LINE_BOSS_PR005_DETAILED_HMI_RUNTIME_CELL.
- **Evidence scope:** proves the actual runtime component, material binding, transform and collision treatment. It is not a full-factory player-HUD before/current/after pair because clean v913 contains no pre-placed PR005 actor. Do not call it release-ready until an actual built/placed overview camera pair and cook pass exist.

### PR005 real player-HUD before/after evidence (2026-08-13)

- **Before (archived packaged v016):** `Saved/StagedBuilds/Windows_UMGOnly_AuthoredPress_v016/LineBossCarFactory/Saved/AutomationBridge/sessions/20260813T140238Z-33696-8902E595/screenshots/pr005_overview_before_v016.png` — 1280x720, SHA-256 `D70BF4CF99123A2CDBF666946AC5DDD076B9F21EF59CDDD821C9CE2D8FB64A70`.
- **After (Development candidate):** `Saved/AutomationBridge/sessions/20260813T135822Z-36812-774DA59E/screenshots/pr005_overview_after_detailed_hmi_v001.png` — 1280x720, SHA-256 `4AE3900708E351C6C262A81B4CE17B7A986FA92FD461C25117854C6ADD91E13C`.
- **Capture authority:** both images use the real `ALBManagementPawn::FocusBuiltFactory()` view (48-degree FOV, yaw -50 degrees, 4,200 cm focus distance) with the Overview HUD open. PR005 was dynamically placed using the normal `LineBossAutoBuildPressShop` builder fixture; no map or player save was written.
- **Functional verification:** the candidate session confirms real PR005 (`COIL-PREP-001`) at `(-4400,-1000,0)` alongside the player-built inbound/press flow; the candidate HMI component remains visual-only, no collision/nav/overlap.
- **Visual delta verdict:** **equal / not visibly meaningful at the player overview**. The HMI binding is runtime-valid, but its small scale does not change the visible PR005 silhouette at 4,200 cm. It must not be counted as release-quality PR005 art or used to claim visual improvement.
- **Next permitted visual scope:** original v812 engineering core plus separately removable, medium-detail exterior skin pieces only: broad warm-white enclosure panels, graphite bases/mechanisms, selected Cairnwell-green service panels, genuine yellow guards, exposed steel mandrel/roll zones, and one clear HMI/door/vent/beacon cluster. Exclude the historic exterior roof cable tray (`CW_PR005_V014_UtilityTray`), dependent exterior hose drops, roof clutter, and micro-detail that does not read at overview distance.
- **Open gates:** PR005 exterior skin fit/clearance, player-visible silhouette before/after, materials, collision/LOD/Nanite policy, functional light state, save/reload, and cook.
- **Pair integrity check:** both frames are 1280x720 opaque rendered images; a 4-pixel sampled comparison yields mean RGB delta 0.5193 and only 0.0312% of samples above 15. This corroborates the overview verdict: the HMI is runtime-correct but not player-visible enough to constitute meaningful visual progress at the intended camera scale.
