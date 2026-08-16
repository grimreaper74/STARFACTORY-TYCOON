# Line Boss visual-art asset ledger

Baseline established 2026-08-13. Status reflects the current playable
player-buildable path and is not a release claim. Source assets remain
immutable; candidate assets require isolated validation before promotion.

## Opening-view baseline

The packaged `Windows_UMGOnly_AuthoredPress_v016` build opens on the empty,
bright management/build hall. Its first build-panel selection is **Inbound
Coil Delivery Cell**; it does *not* open at an unloading sequence or on the
placed PR005--PR010 line. The only opening-world presentation visible in the
captured view is the clean hall, route paint, four support units and the
selected inbound-build UI. This is the player-camera ordering authority for
the pass; the manufacturing-flow ordering begins after placement.

Opening screenshots:

- Packaged v016 UI baseline: `Saved/StagedBuilds/Windows_UMGOnly_AuthoredPress_v016/LineBossCarFactory/Saved/Screenshots/Windows/LineBoss_AutoCapture.png`.
- Current-source PIE overview: `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v915/clean_builder_runtime.png`.

The current-source fixed overview is a visual hold: it reads as overly empty and
dim, with the starter support fleet too small to establish useful scale. It is
evidence only; it is not a release-ready camera or lighting pass.

| Player-visible family | Source authority | Current runtime binding | Status | Blocker / next gate | Screenshot |
| --- | --- | --- | --- | --- | --- |
| Opening hall, build UI and starter support fleet | Default map + `ALBGameMode` clean-shell/support-fleet bootstrap | `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913`; `ALBManagementPawn`; `ALBGameMode` | runtime-ready / visual hold | Current-source overview is overly empty and dim; fleet legibility, actual player-camera framing, envelope and release lighting gates remain required | `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v915/clean_builder_runtime.png` |
| Inbound lorry, coils, crane, stands and Coil AGV | `SourceAssets/Candidate/PressShop/PRESS_SHOP_APPROVED_ASSET_MANIFEST_v20260810.json` | `LBFactoryBuildMachine.cpp` player-placeable inbound dock | runtime-ready | It is the first selected build option, not an opening placed scene. Whole-player placement-preview, material/collision/save/cook confirmation still required | opening UI baseline only |
| PR002 coil inspection | `/Game/LineBoss/Candidates/PressShop/PR002/RuntimeGLB_v922/SM_CA_MW_PR002_ScannerWeighCell_v922` | Player-buildable process stage 1 | runtime-ready | Overview and cook inclusion confirmation | pending baseline |
| PR004 depackaging | `SourceAssets/PR004/RoboticDepackRobot` | Engine-native presentation in `LBFactoryBuildMachine.cpp` | proxy | Owner-approved visual master and isolated Unreal validation are missing | pending baseline |
| PR005 decoiler / feed | `SourceAssets/PR005/*/module_manifest.json` | `/Game/LineBoss/Stations/Press/PR005/Candidate_v001/*` | candidate-only | Current player build uses a 14-module native placeholder; validate source-derived assembly, material slots, pivots and collision before binding | pending baseline |
| PR006 precision leveller | `SourceAssets/PR006/PrecisionCassetteLeveller/ReleaseDetail_v001` | `/Game/LineBoss/Stations/Press/PR006/Candidate_v001/*` | candidate-only | Release-detail intake and overview comparison required | pending baseline |
| PR007 washer / lube | `SourceAssets/PR007/WasherLubeUnit/ReleaseDetail_v001` | `/Game/LineBoss/Stations/Press/PR007/Candidate_v001/*` | candidate-only | Release-detail intake and overview comparison required | pending baseline |
| PR008 servo blanking | `SourceAssets/PR008/ServoBlankingLine/ReleaseAnchorBase_v001` plus detailed modules | `/Game/LineBoss/Stations/Press/PR008/Detailed_v001/*` | candidate-only | Validate authored modules as one runtime assembly; collision, LOD/Nanite and material review required | pending baseline |
| PR009 blank stacker | `SourceAssets/PR009/AutomatedBlankStacker/*` | `/Game/LineBoss/Candidates/PressShop/PR009/v087/ReleaseCollision/*` | candidate-only | Release collision donor is not a release visual; approved segmented visual and runtime gate required | pending baseline |
| PR010 multi-lane transfer / blank buffer | `SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v103/PR010_RELEASE_ART_MANIFEST_v103.json` | `/Game/LineBoss/Candidates/PressShop/PR010/Blockout_v001/*` plus `ReleaseArt_v101` payloads | **proxy (P0)** | Four visible lane beds are explicit blockout assets. v103 service-bank, hatch and identity art is accepted on its original map but remains unpromoted for runtime; validate it as an additive isolated binding before replacing the blockout | pending baseline |
| Conveyors / panel stillages | `SourceAssets/Candidate/FactoryLogistics/PoweredConveyor_v001` and `SourceAssets/Candidate/PressShop/FinishedPanelStillage/Working` | Existing mixed/legacy bindings | candidate-only | Source import, root clearance, stack/payload and overview validation | pending baseline |
| Body Weld fixture, BIW, robots, vision / tools | `SourceAssets/Candidate/WeldShop/*_Intake_v001` and `WeldRobotRuntime_v001` | No approved runtime art binding | blocked | Every supplied source is reference-only or Unreal-unvalidated | pending baseline |
| ED coat | `SourceAssets/Candidate/PaintShop/EDLineRuntime_Candidate_v001` | `/Game/LineBoss/Candidates/PaintShop/EDLine/Runtime_v001` and `v002` | candidate-only | Select one authority and validate process-flow/runtime/cook | pending baseline |
| Cleaning / maintenance robots | CR01 v065 and MR01 v022 authorities in approved manifest | Clean support fleet bindings | runtime-ready | Brightness/material and overview/cook confirmation | pending baseline |
| Factory envelope | `SourceAssets/UnrealDerived/Architecture/FactoryEnvelopeKitRuntime_v001` | Candidate runtime envelope assets | candidate-only | Need real-player overview, shutter/glazing two-sided check and lighting consistency | pending baseline |
| Cairnwell vehicle / panels | `SourceAssets/Candidate/Vehicles/Cairnwell2040/*` | Not imported | blocked | Reference-only sources require semantic rebuild and validation | pending baseline |
| Full-factory lighting / camera | Current authoritative map `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913` | Default map / player-buildable runtime | blocked | Current default map is a clean reconstruction; no full-factory release overview yet exists | pending baseline |

## P0 decision

Do not use the Press Train S02--S06 Walker visual to solve the PR005--PR010
chain. It is a separate, approved family. The immediate P0 target is the
PR010 `Blockout_v001` deck and lane-bed binding, followed by PR005's native
placeholder assembly, in the player-visible process order.
