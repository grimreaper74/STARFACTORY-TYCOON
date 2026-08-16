# Line Boss: Car Factory — Unreal 5.8 handoff

## 2026-08-09 — user-approved Coil AGV, isolated PR002 intake, PR009/PR010 intake v851-v860

- The user's newer Cairnwell Coil AGV supersedes the square API AGV for release use. v851 creates seven textured parts, scales them to 1.70 x 2.20 x 0.75 m, floor-aligns the assembly and reduces 1,984,003 to 323,723 polygons (83.68%) with zero further credits. Runtime blend SHA-256: `7A2B1CD3BF75A71F9270A11B01F672669A19C3B610A6AF4444C013C6BA6CD088`.
- v853 isolated Unreal map `/Game/LineBoss/Maps/LB_PressShop_PR002_AGV_IsolatedValidation_v853` imports the seven-part AGV at exactly 170 x 220 x 75 cm and the 16-part PR002 scanner with removable coil. High-detail visuals use NoCollision with separate coarse proxies. Do not promote to v791 until route/dock clearance validation passes.
- v855 explicitly restores the AGV atlas and PR002 palette after FBX embedded materials failed to bind. v858 removes the AGV normal map after Unreal evidence showed it amplified decimated triangle facets; retain its colour atlas with roughness 0.62 and metallic 0.08. Post-v858 recapture remains required.
- The user confirmed the long narrow pair as PR009. v859 preserves the 1,858,711-polygon textured master (`E70F10D663E3849D9986657A7D56735EE26E15D070ED08370DE99FD67045F071`) and 63-part segmentation source (`F93C695889C05AD3AA1C38691633AFDD65D8D0C4536DD8BBF46D8F11D0D2ADCE`) under workspace `SourceAssets/Candidate/PressShop/PR009/UserMeshy_v20260809_v859`. Blender intake passes; optimisation, scale and semantic grouping remain pending.
- The user confirmed the wider multi-lane gantry pair as PR010. v860 preserves the 1,918,632-polygon textured master (`39566DBE2464A737C8923EF632F51EBFA745776CF7979941139CE9520E51D094`) and 81-part segmentation source (`FB8094ED244649594ABBDC7B166BA8C1F8DCE0F804D431C53B854A15F2874DC3`) under workspace `SourceAssets/Candidate/PressShop/PR010/UserMeshy_v20260809_v860`. Blender intake passes; optimisation, scale and semantic grouping remain pending.
- No further Meshy API task was submitted; balance remains 7,085. Protected v438 remains unchanged at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-09 — PR002 scanner runtime candidate and Coil AGV API candidate v844-v848

- PR002 scanner v844 reduces the accepted 16-part painted modular source from 1,938,490 to 463,267 polygons (76.1%) while retaining the separate wrapped-coil payload, label, cradle, cabinets, console, safety posts, scanner structure and materials. Fresh loaded/empty Blender renders pass: the wrapped coil removes cleanly, the cradle remains intact and no fragments float.
- PR002 v848 uses the reference wrapped-coil OD of 1.65 m as scale authority, creates `PR002_SCANNER_ASSEMBLY_ROOT`, floor-aligns the station at Z=0 and yields a 3.580 x 3.691 x 3.624 m station with a 1.633 x 1.076 x 1.667 m removable coil. Runtime candidate: `SourceAssets/Candidate/PressShop/PR002/UserScanner_v20260809_v839/PR002_CoilScanner_RuntimeCandidate_v848.blend`; SHA-256 `46E000B3E8FAC1A65B218383A9D0FED0E92A6C9429EFEDBA59BCB2BE4C1E85D6`. It is ready for isolated Unreal intake, not direct clean-map promotion.
- One controlled Meshy 6 four-view Coil AGV API task `019fe789-9b82-7aff-a0bf-a9086f59f8a8` succeeded with 2K PBR textures for 30 credits. Balance changed exactly 7,115 to 7,085; no duplicate task was submitted. Raw GLB/FBX, four hashed views and API records are preserved under workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/CoilAGV_Meshy6_API_v20260809_v845`.
- Blender v846 preserves an untouched one-mesh textured master (1,207,086 polygons). Meshy made it too square at 1.90 x 1.90 x 0.80 m; v847 corrects the gameplay envelope to 2.80 x 1.70 x 0.90 m and creates seven textured adjustable parts (main body, lower chassis, coil cradle and four corner sensor modules), reduced to 392,682 polygons. Assembled Blender views pass as a readable AGV; exposed internal split boundaries remain rough, so v847 is an adjustable gameplay candidate rather than close-up release art. Unreal import/collision/navigation remains pending.
- Protected builder-authority map v438 was not modified and remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Meshy 6 Train A production-route sources v638

### v640-v646 continuation

- v660 assembles complete source-only Train A at the retained 57.65 m footprint: five linked tall modular presses, 55 isolated press-component instances, four inter-press transfers, S01/S04/S05/S07 P0 systems, five die carts, two HPUs, trim/slug bins, stillage, powered conveyor and zero-credit procedural service platforms/ladders. Four Blender views pass the tall/floor-seated/coherent-line visual gate. No new Meshy credits; confirmed balance remains 7,345.
- v661 stages eleven unique P0/P1 support meshes for nineteen instances. v662 imports them and reuses the twelve validated v658 press assets across five stations in a fresh complete-Train-A Unreal map. v663 adds the runtime navigation bootstrap/player start. Combined P0 moving-part sources remain explicitly tagged separation-pending and are not falsely bound as whole moving frames.
- v664 preserves a valid navigation failure caused by missing world navigation configuration. v665/v667/v668 preserve UE 5.8 configuration API/type failures. v670 successfully authors a non-null module config and one dynamic Recast nav actor. Static v672 then finds the review floor/proxies were half-size because Unreal cube scale was treated as a half-extent.
- v673 corrects floor, full press blockers and service-access dimensions while retaining the already correct hinged gate proxies. v674 PIE passes operator aisle (4311.20 cm), service aisle (4313.98 cm) and outfeed cross-aisle (1800 cm), with zero points entering any protected press envelope.
- v675 preserves a Python GUID-method failure and v676 preserves an early-phase sampling failure. v677 saved-map PIE passes: one native authority, exact role counts (five slides, five upper dies, five rotors, ten gate visual/collision pivots), all gates open/close at 72 degrees, untrusted power is rejected, trusted power/start and identified blank are accepted, five rotors turn, S03 ram and upper die share a measured 19.649 cm stroke while other slides remain at rest, and save identity is valid. Current best isolated whole-train map is `/Game/LineBoss/Developer/Validation/PressTrains/LB_PressTrainA_RuntimeNav_v673`; Unreal visual capture/performance gate and P0 sub-part separation remain pending, so it is not promoted.

- v654/v655 preserve a rejected local-pivot intake: Unreal retained actor pivots and therefore did not bake the FBX scene-unit transform, so the first module arrived at 1/100 scale and the bounds gate stopped immediately. v656 applies the established centimetre geometry route only to the twelve modular files; v657 then preserves a UE 5.8 Python signature failure before save.
- v658 passes the fresh twelve-asset modular Unreal intake with centimetre bounds matching the Blender manifest. The S03 ram/slide, upper die, hinge-edge gate and central-pivot flywheel remain separate and carry native presentation tags. Visual meshes are `NoCollision`; coarse shell and hinge-following gate proxies are `BlockAll` and navigation-relevant. Map: `/Game/LineBoss/Developer/Validation/PressTrains/LB_PTA_S03_ModularRuntime_v658`.
- Native authority now binds `access_gate` and `flywheel_rotor` roles in addition to the existing stage-slide/upper-die roles. v659 automation passes both `ModularPresentationBinding` (gate open/close, rotor rotation, shared S03 stroke) and the existing full `RuntimeSafetySave` regression. Navigation path proof and whole-train visual/performance gates remain pending; no candidate is promoted.

- v649 assembles one complete source-only S03 around the retained 8.2 m v643 shell: ram, upper/lower dies, two doors, fence, gate, cabinet, HMI, flywheel housing and separate spoked rotor. Four Blender review views confirm a tall floor-seated press and readable die opening/flywheel/control/guarding scale. This is a visual/TBC gate, not engineering approval.
- v650/v651 are preserved failed scale evidence: the first FBX route multiplied metre geometry by 100 and Unreal converted units again, producing an 82,000 cm press; the isolated intake rejected it before map creation/promotion. v652 removes the redundant scale transform.
- v653 passes fresh isolated Unreal intake at 1008.19 x 581.92 x 820.00 cm. Nanite is enabled, the 1.48 M-polygon combined review aggregate is `NoCollision`, and two hidden coarse `BlockAll` proxies carry collision/navigation intent. Map: `/Game/LineBoss/Developer/Validation/PressTrains/LB_PTA_S03_CompleteVisual_v653`. Modular moving-part import, nav path test and runtime binding remain pending; v653 is not promoted.

- v646 completed all eleven isolated Meshy 6 jobs for 330 credits; confirmed post-batch balance is 7,345. Visual audit accepts ram/slide, both dies, left access door, electrical cabinet, HMI, flywheel housing and spoked rotor/shaft as repairable sources. Asset-specific optimized masters are under their `Cleaned_v647` folders. Raw sources remain untouched.
- Reject v646 Asset 05 as a right access door because it changed semantic class into a cabinet. Treat v646 Assets 06/07 as reference-only because the input-sheet lettering made their visible review ambiguous. v648 spends zero credits: it mirrors the accepted left door for the right side and procedurally rebuilds clean fixed-fence and interlocked-gate structural sources. Manifest: `Generated/Meshy6_v646/Repaired_v648/REPAIR_MANIFEST_v648.json`; script: `Scripts/repair_press_safety_modules_v648.py`.
- v648 remains source-only/TBC. It has not entered Unreal and has no authored collision, navigation, gameplay authority or release approval. Continue by assembling and visually gating one complete S03 at the retained datum before deriving the other stations.

- Reject v640 as a visual/scale parent: it inherited low/wide v636 Walker cores and their transformed geometry penetrated below the review floor. Owner screenshot confirmed the below-floor failure. Never use v640 as an assembly parent.
- v642 optimizes the earlier full-Meshy v624 static press shell to a 350k-polygon reusable source. v643 replaces all five S02-S06 cores with that taller Pro-aligned shell, recomputes true bounds, floor-seats the master at Z=0 and instances it at the retained 7.5 m station centres. The new source review has no below-floor press geometry; dimensions remain visual/TBC and Unreal promotion is not authorised.
- P1 v641 generated six unique reusable Meshy 6 modules for 180 credits: die cart, HPU, large trim-scrap bin, small slug bin, flat panel stillage and powered roller conveyor. All passed first visual/source review; the motor is visibly separable. Asset-specific optimized masters are under each `Cleaned_v644` folder. Confirmed balance after v641 is 7,675.
- Owner direction fixes the completion sequence after the press trains: validate backward through S01, blank preparation/decoiling, coil storage, Coil AGV/receiving saddle, crane/C-hook and the restrained inbound lorry/dock. The existing inbound work remains retained but release-incomplete; the final chain must prove physical unloading, identity handoff, capacity/queue behavior, navigation, collision, save/restore and control-room authority.
- v645 prepares four-view inputs for eleven deliberately isolated press components from the preserved Pro panels, using the corrected spoked rotor reference for Asset 11. v646 is the bounded full-Meshy generation/collection batch; do not treat submission or successful download as acceptance.

- Submitted exactly five textured Meshy 6 multi-view jobs for S01 destack/blank feed, inter-press transfer, S04 trim-scrap, S05 slug collection and S07 inspection/unload. All succeeded at 30 credits each. Task IDs, four source views, settings, raw GLB/FBX downloads and responses are preserved under `SourceAssets/Candidate/PressTrains/TrainA/Meshy6SupportingSystemsProduction_v638`.
- The owner upgraded Meshy to Ultra during the batch. Confirmed post-batch API balance is 7,855 credits. Treat this as the current monthly ceiling: reuse approved geometry across S02-S06 and Trains A-D, generate only unique visible modules, and inspect each bounded batch before more spending.
- The sources look promising but are not shippable: each has roughly 1.17M-1.95M polygons and thousands of connected islands. Blender optimization, meaningful moving-part separation, scale/orientation, pivots, collision, LODs, materials and isolated Unreal gates remain mandatory.
- Protected v438 was not modified. S01 task `019fe175-5280-7070-942f-18656d4f5426` was recovered after a local lineage-write bug and reused without duplicate charge. Corrected script: `Scripts/submit_collect_meshy6_supporting_p0_v638.ps1`.
- Additive v639 Blender masters reduce each P0 source to about 180k polygons while preserving the originals. Transfer, S04, S05 and S07 remain strong repairable candidates. S01 is conditional because its silhouette reads too much like a press frame; compare it in the complete train before acceptance. The blanket 180k reduction softens small detail, so final LOD0 budgets must be asset-specific. Script: `Scripts/prepare_meshy6_supporting_master_v639.py`.

## 2026-08-08 — Standing control-room / overhead builder handoff v608-v612

- The standing control-room pawn can now possess the overhead management pawn, use the functional build page, and return through the existing Stand/Seat action. Entry fails closed unless exactly one build authority exists; the exact original standing pawn is retained for return and the temporary overhead pawn is destroyed afterwards.
- Build and focused runtime evidence pass, and the full native Line Boss regression passes 34/34 with zero failures/errors (`ControlRoomManagementHandoff_v608.log`, `LineBossControlManagementHandoff_v609.log`). Protected v438 hash is unchanged.
- Exact-v597 read-only audit v610 confirms it already has the intended game mode, one PlayerStart, one operations console, one build authority and four train authorities, so no speculative child-map placement is justified. v611/v612 are validator-only failures caused by Unreal Simulate mode not creating a possessed default pawn; retain them as failed evidence, not gameplay conclusions.
- The latest four user inbound sheets exactly match the already preserved Pro pack by SHA-256. Continue using that single authoritative copy; exact flow is four-coil lorry → protected C-hook → fixed receiving saddle → separate low-profile Coil AGV → PR-003. All unverified engineering data stays TBC.

## 2026-08-08 — Inbound bright wrapped-steel retention v547-v548

- Added a lorry-only bright wrapped-steel material and coherent-lorry Candidate_v003 without modifying shared materials or earlier candidates.
- Fresh v548 fixes the dark-coil regression: all four restrained trailer coils read as bright curved metallic wrapped steel while preserving the complete lorry → crane/C-hook → saddle → Coil AGV sequence and v540 hall context.
- Retain v548 as the next installed visual-evidence parent, not as release art or promotion authority. Remaining visual and direct-v438 technical gates stay open. Audit: `Saved/Audits/PressShopIntegration/inbound_lorry_bright_wrap_retention_v548.json`.

## 2026-08-08 — Inbound visual experiments v541-v545

- Reject v541: its roof/camera/exposure pass flattens the machinery and over-brightens the crane.
- Retain additive lorry PBR Candidate_v002/v543 as technical source only. Its nine material slots correctly use the controlled inbound family, but v544 makes the four trailer coils too dark and v545 ambient/reflection recovery is insufficient. Reject v544/v545 as visual evidence.
- v540 remains the strongest layout/environment evidence and next parent. The next visual action is a dedicated bright wrapped-steel lorry material variant; do not alter shared Press Shop materials. Decision: `Saved/Audits/PressShopIntegration/inbound_visual_experiments_decision_v541_v545.json`.

## 2026-08-08 — Inbound dock architecture and continuous hall context v536-v540

- Purpose-built `DockArchitecture_v001` passes isolated Unreal intake: 1240 x 655 x 648 cm, eight controlled material slots and collision body setup. It adds the owner-sheet dock portal, seals, wheel guides/restraint, control pedestal, traffic lights, scanner, bollards and guarded waiting zone with all engineering values TBC.
- Fresh isolated v540 is the strongest installed inbound composition so far. It preserves the exact four-coil lorry, installed crane/powered C-hook, fixed receiving saddle and separate loaded Coil AGV while replacing the central black void with continuous hall context.
- Retain v540 as layout/environment evidence only, not release art or a promotion parent. Release-quality machinery surfaces, balanced lighting, readable controls/signage, Pro comparison and all direct-v438 runtime/collision/navigation/save/authority gates remain open.
- Audit: `Saved/Audits/PressShopIntegration/inbound_dock_context_decision_v537_v540.json`. v438 SHA-256 remains `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Purpose-built inbound enclosure v001 / Unreal v526

- Built additive Blender source `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Enclosure_v001` with framed guard panels, vertical infill, kick plates, interlocked gate openings, control/status towers, HMI/E-stops, scanners, mounted identity boards, impact guards and protected service trays. All engineering values remain TBC.
- Isolated Unreal v526 intake passed bounded scale (812 × 661 × 345 cm), five material slots and collision body setup. Retain the enclosure as a candidate module; no accepted asset was replaced.
- Reject v526 as release presentation. The enclosure reads clearly, but the inherited lorry is visually detached and the full lorry → crane/C-hook → saddle → AGV process is too spread out.
- Decision: `Saved/Audits/PressShopIntegration/inbound_enclosure_decision_v526.json`. Next gate is a recomposed installed linear cell using the retained enclosure. v438 remains byte-identical.

## 2026-08-08 — Inbound protected-cell presentation v525

- Fresh isolated v525 adds guarded crane-cell boundaries, dock/handoff bollards, gate/status points and three process identity zones on top of retained v524 geometry. The build and two fixed captures passed technically.
- Retain the safety layout as evidence only. Reject visual promotion: the overview makes the process too small, the hall remains an isolated stage, the complete lorry and powered C-hook transfer are not immediately readable, and the identity boards are not release signage.
- Do not continue camera churn on this geometry. The next inbound gate is a purpose-built installed enclosure and recomposed linear lorry/dock cell, then new fixed-camera comparison to the four Pro sheets.
- Decision: `Saved/Audits/PressShopIntegration/inbound_release_presentation_decision_v525.json`. Builder authority v438 remains unchanged.

## 2026-08-08 — Inbound Modular_v005 Unreal review v524

- Modular_v005 adds a more detailed cab-over lorry front, open-trailer bows and restraints, powered dock restraint/lock indication, fuller dock HMI and entrance interlocks. Its isolated v524 Unreal intake passed all nine bounds/material/body checks.
- v524 preserves exactly four trailer coils, installed bridge crane with retained powered C-hook, fixed receiving saddle and Coil AGV handoff. All engineering values remain TBC.
- Retain v524 as geometry/process evidence only. Do not promote it: the process camera crops the cab, protected enclosure and floor safety zoning are sparse, and C-hook/signage/control presentation remains below the four owner Pro sheets.
- Decision: `Saved/Audits/PressShopIntegration/inbound_modular_v005_decision_v524.json`; evidence: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v524/`. Builder authority v438 remains byte-identical.

# Automatic linked production and inbound Pro pack v483-v486 (2026-08-07, latest gameplay)

- The existing transactional player-built flow now advances automatically over real generated links in deterministic downstream-first passes. Parallel compatible machines share a source buffer and increase throughput; constrained outputs hold upstream work and expose visible starved/processing/blocked reasons.
- `ALBFactoryBuildMachine` save state v2 persists gameplay input/output capacity, process-step progress and operating state while retaining v1 migration. Process steps are gameplay tuning/TBC, not engineering specifications. Reload-stable material-derived press reservation and panel-handoff IDs replace runtime-only counters.
- UE5.8 build passes. `Saved/Automation/AutomaticTimedFlow_v484` passes all three material-flow tests. Full `Saved/Automation/LineBossFullRegression_v486` passes all 34 native tests: 33 clean plus the already-known identity teardown warning. v485 failed only because the builder preflight had not yet accepted machine state v2; that migration defect is corrected.
- Four owner-supplied Pro inbound sheets are preserved, hashed and indexed at `SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807`. They establish the visual chain as lorry/restraint -> crane/C-hook -> receiving saddle -> separate AGV handoff -> PR-003. All dimensions and safety values remain TBC. Build a new isolated child from v438; never overwrite the retained map or bypass its runtime authorities.

# Continuous inbound coil-AGV delivery v478-v480 (2026-08-07, latest gameplay)

- `ALBCoilAGVController` now completes a safe repeatable handoff, empty return and reload cycle with exact coil identity and empty-state save/restore.
- `ALBInboundDeliveryController` binds the player-built inbound dock, its real automatic AGV link, the retained coil AGV and an identified coil store. Ownership is singular and transactional; full storage holds the next delivery before dispatch.
- UE5.8 build passes. Focused v478/v479 evidence passes, and `Saved/Automation/FactoryBuilderRegression_v480` passes all four factory-builder tests.
- Still open: visible lorry reverse/arrival, overhead-crane unload presentation, campaign-slot integration and exact retained-map visual binding. This checkpoint changes no map and is not a visual promotion.

# Campaign save format 14 inbound-logistics authority v481 (2026-08-07, latest gameplay)

- Save format 14 jointly persists the retained coil AGV and inbound-delivery coordinator with exact dock/store endpoint identities; format-13 loads remain supported.
- Dynamic machines, storage and transport links restore before endpoint rebind, then the AGV restores before its coordinator, preventing duplicate ownership of a mid-delivery coil.
- UE5.8 build and `Saved/Automation/LineBossFullRegression_v481` pass all 33 native `LineBoss` tests. No visual map changed or was promoted.

# Retained-map inbound binding audit v482 (2026-08-07)

- Read-only exact-v438 audit `Saved/Audits/PressShopIntegration/press_shop_inbound_binding_v482.json` confirms the retained AGV chassis/deck/load, AGV authority and bridge crane, but no lorry/trailer presentation. Crane `EndTruck` labels are excluded from the vehicle check. No map was saved.
- Reuse those retained logistics assets. Add the new dock/store endpoints and coordinator only in a fresh v438 child after the Pro inbound-cell relationship is available and validated against existing PR-003/PR-004 authority.

# Build authority and variable management zoom v438 (2026-08-07, latest gameplay)

- Retain the unpromoted v438 decision at `Saved/Audits/PressShopIntegration/press_shop_builder_authority_variable_zoom_retention_v438.json`. Player train placement now requires exactly one map-owned build authority and validates the complete protected envelope against authorised bays, protected routes and reachable utility spines before overlap/spawn. Every failure is player-readable and the transaction remains fail-closed.
- Fresh direct-v429 child `/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438` (SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`) records exact A-D reconstruction lanes only; it changes no visual geometry and is not promoted. Retained v429 remains byte-identical at `6A715DDF9EE0AA6C1529103F2DE905E1DDD94C612D1462F899961D049B4414F0`.
- The overhead camera now has smoothed continuous mouse-wheel zoom from close-machine to whole-shop range, plus controller-trigger zoom. Placement alone holds a 6500 cm minimum framing distance. UE5.8 build and all 28 native `LineBoss` tests pass.
- Exact-v438 navigation is now evidenced: v439 passes six non-partial whole-shop routes and v440 passes the three player aisles plus conservative 6 x 3 x 2 m service lanes; B-C retains the known single centred service lane.
- Exact build-bay placement passes direct validator v446: true yaw-90 A-D transforms are accepted only in their matching bays with matching utility spines, and the outside control is explicitly rejected. v441 misread the Python return shape; v442/v443/v445 used Unreal Python's positional Rotator arguments as pitch rather than yaw and are failed validator evidence only. None saved the map. Fresh native regression passes 28/28 with zero failures (one teardown-warning test). Retain v438 unpromoted under `press_shop_builder_authority_exact_retention_decision_v447.json`; final aggregate binding, support sockets, Pro-reference visual comparison and separately authored expansion capacity remain open.

# Anywhere management and builder grid v437 (2026-08-07, previous gameplay)

- Retain the unpromoted v437 gameplay decision at `Saved/Audits/PressShopIntegration/press_shop_anywhere_management_builder_grid_retention_v437.json`. The normal overhead factory view now owns the same controller-friendly management HUD as the optional physical control room, with authoritative production, train and autonomous fleet actions.
- The progression-aware Build page offers only the next valid complete press train. Preview snaps to a local 1 m grid, rotates by 90 degrees, displays the 15 m x 57.65 m protected envelope in valid/invalid colours and explains rejection. Automatic identity and safe removal remain in the native train subsystem.
- Fresh build and all 28 `LineBoss` tests pass. Do not promote visually: lot/utility checks, final aggregate preview, support attachment sockets and exact-v429 PIE comparison remain required.

# Whole Press Shop campaign coordinator v436 (2026-08-07, latest runtime)

- Retain the unpromoted v436 runtime decision at `Saved/Audits/PressShopIntegration/press_shop_whole_campaign_coordinator_retention_v436.json`. A single coordinator now captures, validates and restores PR-004–PR-010, the exact GUID-matched press-train set, the operations console and optional support-fleet/crane authorities.
- Restore is fail-closed and preflighted before world mutation; production/train authorities restore before the control-room binding. Memory and native disk-slot round trips pass, and the complete UE5.8 `LineBoss` suite is 27/27 green.
- This changes no visual map. Continue from retained visual v429. The physical control room should remain optional while an anywhere-accessible, controller-friendly management UI is developed and compared against the observed Car Manufacture workflow.

# Runtime Press Train identity/save authority v434 (2026-08-07, latest)

## Factory-builder placement/removal transaction v435

- Retain the unpromoted v435 runtime decision at `Saved/Audits/PressShopIntegration/press_shop_factory_builder_train_transaction_retention_v435.json`. Player-authorized placement now creates one native authority through the A-Z/GUID registry and rejects overlap against the retained Train A protected envelope. Removal is interlocked to isolated-and-empty state; designation reuse does not renumber survivors.
- UE5.8 build and the complete 26-test native suite pass. Do not promote visually: exact-map PIE, lot/utilities, placement UI, campaign-slot coordination and completed visual-assembly binding are still required.

- Retain `Saved/Audits/PressShopIntegration/press_shop_runtime_train_identity_retention_decision_v434.json` as the current unpromoted identity/save foundation. The existing train authority now has immutable GUID identity, lowest-free A-Z designation allocation, survivor non-renumbering, freed-letter reuse, derived S01-S07 station IDs and persisted custom display names.
- Save root v13 adds the multi-train `PressTrains` array while retaining the v12 `PressTrainA` migration field. Control-room state v2 stores `AssignedTrainGuid` so save authority survives designation reuse. UE5.8 build succeeds and the complete native `LineBoss` automation set passes 26/26.
- No visual map was modified or promoted. World-level train capture/restore is exact-set and GUID matched, including validated placement transforms. Continue from retained visual v429 and runtime v434; next runtime work is the player placement/removal transaction and central campaign-slot integration, followed by fresh PIE and fixed-camera gates.

# Dynamic physical Press Train identity checkpoint v429/v433 (2026-08-07)

- Current retained unpromoted identity parent: `/Game/LineBoss/Maps/LB_PressShop_DynamicTrainIdentityCandidate_v429`, SHA-256 `6A715DDF9EE0AA6C1529103F2DE905E1DDD94C612D1462F899961D049B4414F0`; fresh direct child of immutable v386 (`057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038`).
- Fresh v430 fixed-camera evidence passes A-D physical/dynamic label readability plus the four-line overview. Exact v431 whole navigation and v432 aisle/collision gates pass; A-D remain 338 actors each.
- Decision and rejection lineage: `Saved/Audits/PressShopIntegration/press_shop_dynamic_train_identity_retention_decision_v433.json`. Never use v398/v400/v404/v408/v412/v416/v418/v420/v426/v427 as parents.
- Runtime allocation/save identity remains open: next available A..Z, immutable GUID, no renumbering of survivors and station IDs `<designation>-S01..S07`. Do not conflate visual tags with implemented runtime/save authority.

# 2026-08-07 — Four-train PBR and balanced lighting v386/v390

- Current retained unpromoted visual/runtime successor is `/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386`, SHA-256 `057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038`.
- Fresh direct-v374 v383 resolves all 1,224 repeated FBX slots on the four train aggregates to 13 consistent PBR finish families. v382 failed only the unmapped copper-service gate and is never a parent. v386 adds twelve visual-only broad train fills while preserving every geometry, collision, navigation, runtime, production and save-authority contract.
- Owner accepted the fresh v387 matched views. Exact PIE v388 passes six non-partial whole-shop navigation routes in 0.969 s; v389 passes every player corridor plus conservative gameplay service-equipment lanes. Current evidence still does not justify enlarging the exterior shell.
- Retention authority: `Saved/Audits/PressShopIntegration/press_shop_train_pbr_lighting_retention_decision_v390.json`. Keep unpromoted pending A-D identity, final Pro comparison and full whole-shop management/save/automation release gates.
- Reject v391 and v393 identity experiments; neither is a parent. Their free text/boards fail physical integration and oblique readability. Preserve clean v386 and require modeled or UV-authored identity next. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_identity_visual_rejection_v395.json`.

# 2026-08-07 — Pro-detail Train A v046/v354 and expanded four-line layout v356

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374`, SHA-256 `DDB934BEB76EE377E5E19B36D24C92888AEDC08946774EDC2998FEC58CA06F81`, as the next structural-presentation experiment parent. It preserves v367's 22 m centres, removes six audited X=2000 cm columns, replaces six crude v301 slab girders and adds twelve 40 m fabricated visual trusses. All structural values remain TBC.
- Reusable Blender truss source is under `SourceAssets/Candidate/PressShop/Structure/WideSpanTruss_v372`; v373 is failed partial intake evidence and never a parent. Fresh v375 views materially improve the four-line and B-C sightlines but still fail final lighting/material/identity quality.
- Exact v376 passes six whole-shop nav routes and v377 passes all player plus conservative gameplay service-equipment aisle probes. The exterior shell remains unchanged and enlargement is not required. Decision: `Saved/Audits/PressShopIntegration/press_shop_wide_span_truss_retention_decision_v378.json`.

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367`, SHA-256 `5CF44DDD90C49BAD1447C50406680045862A957ED01FD4BBF44C58C685594355`, as the next layout parent. Four lines use 22 m centres and retain approximately 843.5 cm between completed visual envelopes; current evidence does not require exterior-shell enlargement.
- v361 isolated the old nav timeout to missing train coverage plus excessive dynamic-nav dirtying, dominated by 756 MR01 `NoCollision` visual components. v362 adds dedicated train-block coverage; v367 makes 767 `NoCollision` visual primitives nav-neutral with zero collision, visibility or runtime-authority changes.
- v364 passes all three standing-player corridors and a conservative gameplay-only 6 x 3 x 2 m service-equipment sweep. B-C has one clear centred 3 m lane; all actual equipment dimensions remain TBC.
- v368 completes the exact whole-shop rebuild in 2.734 s and passes six valid, non-partial routes spanning the three train aisles, support fleet, PR-009 and PR-010. Authority: `Saved/Audits/PressShopIntegration/press_shop_expanded_layout_retention_decision_v369.json`.
- v367 is retained but unpromoted pending fresh fixed-camera release comparison, B-D identity, whole management/save/automation regression and release-art gates.

- Expanded-pitch v356 keeps centres at `-4300, -2100, +100, +2300 cm` (22 m pitch) and approximately `843.5 cm` between completed visual envelopes; it fits the current exterior floor.
- Read-only PIE audits `press_shop_expanded_train_pitch_pie_v359.json` and `press_shop_expanded_train_pitch_pie_v360.json` ended without saving after the whole-shop nav build remained locked through their 75 s and 180 s safety windows. This is inconclusive and grants no promotion or engineering clearance.
- Diagnose the navigation rebuild cost and repeat player plus conservative service-equipment route probes. Exterior/column enlargement is conditional on that evidence.

- `ProDetailModular_v046` is the retained modular master (474 renderables) for the Pro-led Train A direction. It includes connected S04/S05 collection equipment, refined S01 feed hardware and refined S07 robot/HMI detail; all engineering data remains TBC.
- v351 and v353 are explicit failed/nonparent Unreal intakes. Transform-baked visual aggregate v049 corrects their import/axis issues without replacing the modular source. Fresh v354 passes isolated intake at `5765.0 x 1356.5 x 939.0 cm`, floor Z `0`, preserves one native authority plus 126 native collision components, and remains unpromoted visual-only evidence.
- Fresh v356 uses 22 m A-D centres (`A -4300`, `B -2100`, `C +100`, `D +2300 cm`) and preserves native authority/collision while previewing the v049 family on all four lines. The resulting adjacent visual gap is `843.5 cm`; the existing shell contains these centres, so no exterior shell enlargement has been made.
- v357 player-height A-B aisle evidence provisionally passes spacing/readability. Its overview camera is rejected above-roof evidence; v355 views are also rejected for release composition. Structural-column treatment, rebuilt navigation/collision, die-cart/bin service envelopes, B-D identity, separate movers, runtime and final fixed-camera gates remain open. Authority: `Saved/Audits/PressShopIntegration/press_shop_expanded_train_pitch_visual_decision_v358.json`.

# 2026-08-07 — Train A v343 integration and measured layout rule

- Current unpromoted whole-shop substrate is `/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343`, SHA-256 `7CE2F5B7D627776B4B71C8197255B035A0561B9E49DEED20A354ABFFB7560317`. It preserves one native authority and 126 collision-bearing native components; 337 old presentation actors are hidden, not deleted. Upright v040 is visual-only.
- v342 produced no artifact. v344 fixed-camera evidence is rejected for oblique/close composition and column obstruction; v343 remains retained but not promoted. Decision: `Saved/Audits/PressTrains/press_train_a_release_integration_visual_rejection_v344.json`.
- Pro supporting-system and S04 Trim/Scrap sheets are preserved under `SourceAssets/Reference/PressTrains/TrainA/`, SHA-256 `D6B7675C2AF1C8086E14EF23D6CE7B7A502464F59546641BC5DE98E44BCDF00E` and `53BCCF46045C2CF2ABD82EBB6E4FF458E8B49E015610000F8DBF9E99A55D8562`; visual authority only, engineering TBC.
- Read-only v346 proves 17 m A-D centre pitch. Old 15 m protected envelopes leave 2 m; equal 10.4575 m v040 visible envelopes leave about 6.5425 m. Preserve centres and fit final service/scrap presentation within the existing protected envelope unless fresh clearance, collision or navigation evidence proves a layout change necessary.
- Keep old B-D presentation until A passes full release gates. Audit: `Saved/Audits/PressTrains/press_train_abcd_layout_envelopes_v346.json`.

# 2026-08-07 — Train A axis-corrected modular source v033 retained

- v033 is the current source-only full Train A direction: dedicated S01, correctly oriented shared S02-S06 presses with five unique tooling identities, and dedicated S07. The valid corrected views are in `ModularAssembly_v033/MatchedReview_v034`; the first v033 review is failed camera evidence.
- Do not import or promote yet. Strengthen S01/S07 presentation, then run isolated Unreal, inherited-hall, collision, navigation, runtime and matched comparison gates. Decision: `Saved/Audits/PressTrains/press_train_a_modular_assembly_visual_decision_v033.json`.

# 2026-08-07 — Station tooling variants v030 retained

- Retain the five source-only S02-S06 tooling variants for assembly. They are TBC, unimported and unpromoted. Decision: `Saved/Audits/PressTrains/press_train_a_station_tooling_variants_decision_v030.json`.

# 2026-08-07 — Train A modular assembly v031 axis rejection

- v031 contains the correct seven-station architecture and inherited v012 datums, but fresh bright views prove S02-S06 were installed 90 degrees off: their narrow service faces point toward the operator.
- Reject v031; do not import, promote or parent from it. Correct only the S02-S06 local-to-v012 axis transform in non-overwriting v032, retain S01/S07 orientation and repeat matched views. Decision: `Saved/Audits/PressTrains/press_train_a_modular_assembly_visual_decision_v031.json`.

# 2026-08-07 — Dedicated Train A end-cell guarded source v029 retained

- v028 is preserved as a failed/nonparent open-cell attempt: mechanisms were intact, but a 100 KB S01 size heuristic failed and its tall perimeter outline dominated the cells.
- v029 replaces that outline with local low mesh guarding and preserves distinct S01 destack/feed and S07 robot/inspect/unload mechanisms. Source counts are 93 and 103 parts. Independent clean-scene FBX re-import passes exact geometry counts and <3 mm bounds drift.
- Retain v029 only as source input to an isolated complete Train A assembly. Do not import as a station replacement, promote it or roll it to B-D before inherited-hall and matched whole-train visual gates pass. Decision: `Saved/Audits/PressTrains/press_train_a_dedicated_end_cells_guarded_decision_v029.json`.

# 2026-08-07 — Dedicated Train A end-cell v027 visual rejection

- v027 passes source structure (S01 63 parts, S07 71 parts, 27 additions) but fails all-cell presentation: inherited black facades, identity walls and roof slabs dominate the new views and hide the destack/feed and robot/inspection mechanisms.
- **Reject v027 visually; do not import, promote or use it as a parent.** Retain only its component extraction method and useful mechanical parts. Decision: `Saved/Audits/PressTrains/press_train_a_dedicated_end_cells_visual_decision_v027.json`.
- The next non-overwriting source is v028: remove audited presentation-shell objects, retain machinery, add light open TBC safety framing, then repeat fresh visual review.

# 2026-08-07 — Shared A-D press-body module library v025 retained

- `PressBodyModuleLibrary_v025` exports all 16 v022 groups separately with exact 537-part conservation: 14 common modules and two tooling/transfer variant/interface modules. It is reusable across S02-S06 and Trains A-D while signs, tooling, EOAT, workpieces and runtime identity remain variant-specific.
- v024 failed by counting the hidden combined review mesh and is nonparent evidence. v025 is source-only, not imported or promoted. Decision: `Saved/Audits/PressTrains/press_train_shared_module_library_decision_v025.json`.

# 2026-08-07 — Complete Train A visual authority intake v023

- Accepted owner sheet SHA-256 `4638AAD84029DFAD74941CCD0586B182E4F39D4EE6230E3D87B388BF87E95DFD` as visual authority only. It defines S01 dedicated destack/feed, S02-S06 shared modular press bodies with unique tooling, and S07 dedicated inspection/unload. All unverified values remain TBC.
- v022 becomes the reusable S02-S06 source library, not a seven-station copy template. S01 and S07 require dedicated sources; installed datums remain TBC. Audit: `Saved/Audits/PressTrains/press_train_a_complete_visual_reference_intake_v023.json`; contract: `SourceAssets/Candidate/PressTrains/TrainA/TrainAComplete_v023/TRAIN_A_COMPLETE_VISUAL_CONTRACT_v023.json`.

# 2026-08-07 — Pro-aligned S03 compact-service source v022

- `PressModulePrototype_v022` retains the 16 reusable source groups and 537 authored parts, replaces the exposed rear pipe cage with compact backplate routing, adds readable Cairnwell/S03 source identity and provides uncropped full-machine review views.
- Retain as source visual direction and authorize only a non-overwriting isolated Unreal lighting comparison. Collision/navigation/runtime binding, station replacement and promotion remain forbidden. Decision: `Saved/Audits/PressTrains/press_train_a_s03_compact_service_source_decision_v022.json`.

# 2026-08-07 — Pro-aligned S03 detail source v021 visual decision

- Source-only `PressModulePrototype_v021` retains all 16 Pro groups and contains 525 authored parts. Its crown fabrication, tooling, rear-service density and mesh guarding are materially stronger than v020.
- Fresh visual review still fails release due to cage-like rear routing, overly smooth large surfaces, missing final identity graphics and cropped primary comparison views. Retain only as a source-detail parent; do not import or promote. Decision: `Saved/Audits/PressTrains/press_train_a_s03_release_detail_decision_v021.json`.

# 2026-08-07 — Pro-aligned S03 source v020 visual decision

- `CA-AMW-PT-A-S03-REF-01` is the current S03 visual modelling authority; all dimensions and engineering values remain TBC.
- `PressModulePrototype_v020` passes source structure with all 16 reference groups but fails release presentation because rear services, guarding, fabrication detail and surface construction remain insufficient.
- Retain its architecture/proportion method only. Do not import or promote v020. Continue through non-overwriting v021 and fresh matched visual review. Decision: `Saved/Audits/PressTrains/press_train_a_s03_pro_aligned_source_decision_v020.json`.

# Part-built Blender press-module source direction v018 retained (2026-08-07)

- Owner requested the direct component-by-component modelling approach demonstrated by a solo developer using SketchUp. Blender 5.2 provides the same modelling method without a paid SketchUp dependency and preserves the established FBX/Unreal automation.
- Fresh source-only `PressModulePrototype_v018` builds one mid-train station from 93 separately inspectable parts, joined only for FBX export. It has 14,300 vertices / 13,388 polygons and TBC visual dimensions `4.86 x 2.525 x 9.21 m`; no retained source, map, collision, navigation, mover or runtime authority changed.
- Full-height review shows clearly constructed uprights, plates, guides, ram, foundation, service hardware and fasteners. It also shows a still-toy-like crown/drive, empty opening, missing guarded tooling context and clean studio materials. **Retain the modelling method and v018 source direction; do not promote or install this exact shape.** v017 failed its conservative width check and is preserved as failed evidence.
- Refine the crown, guarded drive and die/feed context in a new source successor, then perform isolated Unreal intake under v301 lighting. Decision: `Saved/Audits/PressTrains/press_train_a_part_built_station_source_decision_v018.json`.

# Train A wide-span structural-clearance direction v301 retained (2026-08-07, latest)

- Fresh direct-v300 `/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301`, SHA-256 `8ECBEF72EE262899A15E70B2924EF8F2F1EB8A8480E49525DDFA4FF9245D8BF6`, removes only the six audited X=6000 cm operator-side columns and adds six visual-only 40 m TBC girders. All four trains remain exactly 338 actors and v300 is unchanged.
- Exact management, four native dock collision, corrected PR009 routes and all three PR010 routes pass. The four-train overview is substantially clearer. **Retain v301 as structural-clearance direction and next experiment parent only; do not promote it.** Its rectangular girders remain crude visual placeholders and must become credible trusses without inventing engineering authority. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_wide_span_clearance_decision_v301.json`.

# Train A measured lighting direction v300 retained (2026-08-07, latest)

- Exact-v295 read-only inventory proves the contrast problem is systemic: 133 lights, a single unbound Basic exposure pinned `1.0..1.0` with bias `+0.75`, steep film response, two 2,350 Train A spots and three 520 close fills.
- Fresh direct-v295 `/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300`, SHA-256 `93BF6B46BAD2292019E31C08EF31AF9C9C21CE98BAB9A045CF7670AF5A7AA52C`, uses a measured open exposure range, softer film response, reduced harsh task lighting, increased broad ambient fill and the isolated v016 segmented shell. It preserves all 338 Train A actors and every runtime/collision/navigation authority.
- Exact playable management, four native docks, corrected PR009 integrated routes and three PR010 routes are green. Visual midtones are materially better than v295-v299. **Retain v300 only as the measured lighting/segmented-shell direction and next experiment parent; do not promote it.**
- Dense posts still obstruct every useful view, station separation is insufficient and inherited slab forms remain. The owner reports firsthand that real Toyota production stations are much farther apart; use that as qualitative design authority without inventing Toyota dimensions. Next audit exact column roles and build an isolated wide-span structural-clearance child, then repeat all gates. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_balanced_lighting_decision_v300.json`.

# Train A material-readability v299 visual rejection (2026-08-07, latest)

- Fresh direct-v295 child `/Game/LineBoss/Maps/LB_PressShop_TrainAMaterialReadabilityCandidate_v299` passes structural construction with all 338 Train A actors, 352 Train A-only inherited material overrides, the five-slot v016 shell and three new cameras. Map SHA-256: `AF1BF46D5C9191C10220CBBA50AB1BEDDD9CBF79E1F913A317FF1EE811993E20`.
- Its exact-map views still crush faces to black, clip upper surfaces toward white and remain column-obstructed. **Reject v299 visually; never promote or parent from it.**
- Return to v295. Do not create another exposure-only, material-only or camera-only successor; first record the exact inherited lighting/post-process state and correct the measured cause in a fresh direct child. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_material_readability_decision_v299.json`.

# Train A segmented-shell v298 visual rejection (2026-08-07, latest)

- `PresentationShell_v016` remains retained source/isolated technical evidence. Its isolated Unreal v041 intake passes exact bounds, five material slots, `NoCollision`, non-navigation and protected-map parity.
- Fresh direct-v295 child `/Game/LineBoss/Maps/LB_PressShop_TrainASegmentedShellCandidate_v298` passes its structural build gate with 338 installed Train A actors and exact operator-face placement. Map SHA-256: `A3CB483BE3D56E344324CA0C78175F6EC10EDDF810324384E07D71185674AF3F`.
- Exact-map visual review fails: clipped white upper surfaces, crushed black working faces, residual slab/block mass and column-obstructed overview do not meet the Pro-reference or owner gameplay-readability bar.
- **Reject v298 visually; never promote or parent from it.** Return to v295 for the next whole-shop child. Improve the source geometry/PBR midtone response and camera sightlines before running the expensive runtime gates; never roll this failed treatment across B-D. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_segmented_shell_decision_v298.json`.

# Train A fabricated operator-face direction v295 (2026-08-07, latest)

- New source-only `PresentationShell_v015` rebuilds the visual shell from immutable `AssemblyStudy_v013` as 235 layered fabricated parts (73,640 vertices / 70,030 polygons), with open H-frame posts, separate crown/gearbox pods, bearing stacks, lifting eyes, recessed panels, service doors and hydraulic detail. Its FBX SHA-256 is `FEE1630F594E128EA702761ED148BA4268DDD065BB6F66E95432F24F81FA51A5`. Isolated Unreal intake v040 passes scale, five-slot material, `NoCollision`, non-navigation and retained 336-actor/native-station parity.
- v293 and v294 prove scale/material binding but place the shell at the train centreline, where the retained assembly hides most of it. Preserve them as evidence/technical lineage only; neither is a release parent.
- `/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295`, current SHA-256 `5CF8715BEE1F55EF98E1B9B713C74BF4F9C87281FE209FA190D73DA61DE94ABF`, moves only the shell datum to `[1600,-5180,0]` cm. Its world Y envelope `-4789.00..-4695.00` cm now matches the retained operator facade. Protected station/runtime parent v288 remains byte-identical at `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`.
- Fresh exact-v295 gates pass: whole-shop playable management; four native service-dock collision ownership with zero unexpected overlaps; corrected integrated PR009 service routes with zero protected-space traversal; and all three non-partial PR010 support routes. The first direct PR009 wrapper is retained as failed harness evidence because it bypassed the corrected whole-shop endpoint contract; the true v288-successor adapter passes.
- Fresh v295 captures materially improve machinery credibility and expose separate crown pods, bearings, lifting eyes, access panels, open posts and manifolds. They still fail release presentation because hall exposure clips white faces and crushes upper detail, structural columns dominate the overview, and inherited slab/block geometry remains visible. **Retain v295 as the technical and visual direction only; do not promote it and do not copy it to B-D yet.** Next create a fresh v295 child for local exposure, release-composed cameras and remaining slab cleanup, then repeat fixed-camera Pro comparison. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_fabricated_shell_operator_face_decision_v295.json`.
- Visual-only v296 and camera-only v297 are both rejected as release parents. v296 crushes midtones and places its overview outside the usable hall envelope; v297 restores a usable overview but fixed exposure still darkens close detail and the immutable column grid continues to fragment the train. Preserve both as evidence and return to v295. Do not continue exposure-only iteration: the next successor must improve remaining source slab geometry/material response and compose around the measured column grid. Decisions: `press_shop_train_a_release_readability_decision_v296.json` and `press_shop_train_a_release_camera_decision_v297.json`.

# Train A inherited-hall axis and visual decision v292 (2026-08-07)

- v290 is visually rejected: its long cameras crossed the measured structural-column grid and its management camera was fully obstructed. Preserve it only as initial static-placement evidence; never promote or parent it.
- v291 is technically and visually rejected. A positional `unreal.Rotator(0,-90,0)` call pitched the imported 36.355 m shell onto its side, leaving it about 1.14 m high and projecting it across the aisle. It must never be promoted or used as a parent.
- Fresh direct-v288 `/Game/LineBoss/Maps/LB_PressShop_TrainAShellAxisCorrectedCandidate_v292`, SHA-256 `0DF1DFD004629FD718F67BC939F0D869DE3DDC24B16E571CE48F0C112E8FEE09`, uses explicit named yaw and proves the correct upright envelope: X `1980.50..5616.00`, Y `-4357.00..-4243.25`, Z `32.50..1072.00` cm. All 338 retained Train A actors are unchanged; the shell remains `NoCollision`, non-navigation, and protected v288 remains byte-identical.
- Fresh inherited-hall renders prove alignment but fail the release visual bar: large planar cheeks/crown slabs remain blockout-like, the material contrast is harsh, and the hero composition still suffers column intrusion. **Retain v292 only as technical axis/envelope evidence; do not install A-D and do not run broad release regression from a failed visual direction.** Next source successor must preserve the v292 envelope while replacing uninterrupted slabs with credible fabricated/chamfered structure and recessed service detail. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_shell_axis_corrected_decision_v292.json`.

# Train A detailed fixed-shell checkpoint v039 (2026-08-07)

- Source-only `PresentationShell_v014` adds 265 fabricated-detail parts across S02-S06, joined as one 54,320-vertex / 49,470-polygon fixed visual asset. It adds rounded crown drives, layered frame cheeks, service doors, ribs, manifolds, pressure vessels, pipes, valves and fasteners without editing retained moving parts, pivots, collision or runtime authority.
- v035 and v036 are failed intake evidence (wrong metre scale / collision profile); v037 proves scale and collision but has the FBX forward axis reversed; v038 corrects alignment. Fresh material child `/Game/LineBoss/Maps/LB_PressTrainAPresentationShellMaterialCandidate_v039`, SHA-256 `FA4FFF48C0F684E28FA9C3BA3EAC2FC97FC34151CB9827F637B67FD062A6394E`, rebinds all five shell slots to retained Cairnwell PBR materials.
- Exact v039 standing-player floor/aisle/navigation/guarding/mover/robot-sweep and spatial hydraulic/transfer/press/robot/safety audio gates pass with zero failures. The new silhouette is materially more machine-like, but the isolated diagnostic stage clips bright surfaces and is not release visual authority.
- **Retain v039 as a technical and visual-direction checkpoint only; do not promote or install A-D yet.** Next place one Train A shell into a fresh direct-v288 comparison child under inherited hall lighting, then repeat collision/navigation/runtime and fixed-camera Pro-reference review. Protected v288 remains unchanged. Decision: `Saved/Audits/PressTrains/press_train_a_presentation_shell_decision_v039.json`.

# Whole-shop train presentation visual hold and source v013 checkpoint (2026-08-07)

- Exact v288 whole-shop release captures are visually rejected: the protected technical/runtime parent remains byte-identical at SHA-256 `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`, but inherited cameras, structural columns, black upper-shell contrast and rectilinear press bodies do not meet the Pro-reference release bar.
- Fresh child `/Game/LineBoss/Maps/LB_PressShop_TrainPresentationCandidate_v289` recalibrates exactly 1,342 installed train material slots, adds 12 local train-bay task-fill lights and four close fixed cameras without changing gameplay contracts. Fresh renders materially improve equipment legibility but still fail source-geometry fidelity. **Reject v289 as a parent; retain it only as material/readability evidence.** Decision: `Saved/Audits/PressShopIntegration/press_shop_train_presentation_decision_v289.json`.
- New source-only `AssemblyStudy_v013` is a direct immutable-v012 successor. It preserves all 336 object names/transforms/origins/roles/hierarchy edges and the exact `15,000 x 56,000 x 10,750 mm` bounds while adding fabrication chamfers to 285 objects, smooth treatment to 122 curved objects and calibrated PBR worked-steel/green materials. Blender source SHA-256 is `5CD601624C240A7629649304428A994E19796B4254B571C6FCD6EDC80A1CC8C5`; FBX SHA-256 is `C78F63859AEF38D2F5C82632BA85BD14456826B47AF38AFD72E43D45AB403F96`.
- Next import v013 into a new isolated Unreal candidate, prove exact actor/pivot/bounds/material/collision/runtime-binding parity, then install A-D only into a fresh direct-v288 whole-shop successor and repeat every technical and fixed-camera Pro gate. v013 is source evidence only and is not yet authorized for whole-shop integration.

# Whole-line control-room orchestration source checkpoint (2026-08-07)

- `ALBControlRoomOperationsConsole` now requires and binds the complete PR005-PR010 chain, the transactional `ALBPressShopMaterialFlowController`, and the selected native press train. Automatic Start powers/starts PR005-PR008 and PR010 in order, leaves PR009 waiting for an actually accepted PR008 blank, and leaves the train isolated until PR010 releases reserved material.
- Automatic runtime progression uses the existing rollback-safe PR008->PR009 and PR009->PR010 transactions, reserves occupied PR010 lanes, feeds the selected train within its real four-blank queue capacity, hands off only native inspected panels, and never fabricates remaining coil length. PR005-PR010 or train faults identify the failed authority, hold the order and command the whole-line controlled stop.
- New native `WholeLineStartAndFaultRollback` proof covers staged start, exact traceable blank/stack/train/panel progression, honest material hold, PR007 guard-fault rollback, corrected-fault resume, one-panel order completion and campaign-root save/reload with stack genealogy and monotonic transaction identity. `Saved/Automation/ControlRoomOrchestration_v008/index.json` passes 2/2; the complete control-room family at `Saved/Automation/ControlRoomCurrent_orchestration_v001/index.json` passes 5/5, including standing-pawn movement, chair, gamepad and physical centre-view interaction. The full `LineBoss.PressShop` regression at `Saved/Automation/PressShopCurrent_v288_orchestration_v001/index.json` passes 16/16 with zero warnings/failures.
- Fresh exact-map PIE evidence is `Saved/Audits/PressShopIntegration/press_shop_playable_management_pie_v288_orchestration_v001.json`; physical named-button routing is separately green at `Saved/Audits/ControlRoom/control_room_physical_buttons_pie_v288_orchestration_v001.json`. Together they pass authority counts, honest hold, Create/Start/Pause/Stop, train selection and non-selected-train isolation. Retained v288 remains byte-identical at SHA-256 `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5` and is still not promoted. Remaining release work includes the whole-shop presentation gate and packaged playable closure.

# PR006-PR008 station-complete whole-shop checkpoint v288 (2026-08-07)

- Retained fresh direct-v273 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288`, SHA-256 `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`. Protected v273 remains byte-identical at `96E6B172BF284BF6BEA02504C9D07CBBF6E56A4A51F2ED23ABDCE022F93B4394`.
- v288 restores the complete visible retained PR006, PR007 and PR008 cells with exact Unreal rotation ordering and retained task lighting. Static donor fidelity is exact across 371 checked actors with zero mesh, material, transform or bounds mismatches.
- Exact PR006, PR007 and PR008 runtime gates pass, including motion, live HMI, faults, isolation and save state. Whole-shop management, PR009/PR010 navigation and four native service-dock collision ownership gates pass. Current native Press Shop automation is 16 succeeded, 0 warnings, 0 failures.
- Fresh fixed-camera PR006/PR007/PR008 evidence under `Saved/ValidationScreenshots/PressShopIntegration/v288_complete_cell/` passes the connected-cell readability gate. v285 and v286 are rejected/nonparents; v287 is a technical-pass/nonparent because its task lighting remained too dark.
- **Retain v288 as the station-complete whole-shop parent, not as the final Press Shop release.** Whole-shop final presentation, end-to-end production-order/material orchestration, standing-player control-room release proof and complete playable-package closure remain open. Decision: `Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_complete_cell_decision_v288.json`.

## 2026-08-07 — PR-006–PR-008 complete-cell repair v285 retained technically, visual gate open

- Protected whole-shop v273 remains byte-identical (SHA-256 `96E6B172BF284BF6BEA02504C9D07CBBF6E56A4A51F2ED23ABDCE022F93B4394`). v284 is rejected as a release parent: donor comparison proved its operational movers lacked their stationary housings, beds, guards, supports and service cabinets.
- Fresh direct-v273 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v285` restores only exact donor station actors absent by label: 69 PR-006, 108 PR-007 and 274 PR-008 static meshes, plus three retained live-HMI rows per station and exact retained commissioning values. Candidate SHA-256 is `924D347FC70462B87DFC45DFE728C32950152EFEBE97E99F2646FB6CBD3DCCF3`.
- Exact PR-006, PR-007 and PR-008 runtime/save gates pass; PR-008 also proves motion, live HMI, safety fault/isolation and recovery. The full native automation family remains 24/24 clean.
- **v285 is not promoted.** Its heavy-map unattended fixed-camera captures did not retain files, so visual completeness is unproven. Next obtain reliable exact-map visual evidence, then run whole-shop collision/navigation/management/save regressions and authoritative Pro-reference comparison. Decision: `Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_complete_cell_decision_v285.json`.

## 2026-08-06 — modular service-dock runtime v030 retained technically, isolated visuals rejected

- New non-overwriting `Runtime_v026` assets componentize MR01's source-authorised probe, tool-rack door and waste drawer; CR01 service hardware stays static until real pivots/travel exist.
- Native `ALBSupportRobotServiceDock` compiles and its guarded mechanism/safe-restore automation passes. Service requires exact dock/variant identity, a stopped docked robot and all three safety permissives; any loss closes the dock and saved powered motion is never restored.
- Alignment and exact resolved-material rebinding are technically verified. Isolated v026-v029 fixed-camera evidence is visually rejected because its stage washes both the new meshes and retained aggregate controls. Do not install these actors into the cumulative map from that evidence.
- Protected `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269` remains the current unpromoted parent. Next use representative inherited hall lighting and exact four-berth collision/navigation/docking gates before a child-map replacement decision. Evidence: `Saved/Audits/SupportRobots/service_dock_modular_runtime_decision_v030.json`.

## Press Shop support-fleet certified dispatch checkpoint v269 (2026-08-06, latest)

- Retained `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269` (SHA-256 `DDB2708F68F751C5FA69B08C8EFD525BDB3A42ACBE740530AF7512869BB1EFD9`) as a fresh direct child of green navigation parent v262. Protected v260/v262 are unchanged.
- Native `ALBPressShopSupportFleetController` discovers and commissions exactly two MR01 and two CR01 units, owns R05 outbound/return/automatic-charge routes, and completes exact-PIE collision-swept dispatch and return for all four robots. Correct dock identity, certification, mission counts and no-fault state are proven; maximum standby/dock errors are 9.401/8.204 cm.
- Changed only 42 decorative floor saw-cut actors and 8 painted support-bay marks from `BlockAll` to `NoCollision`/non-navigation. All genuine support equipment, divider, column and dock-proxy blockers remain active. Exact collision, management, PR-009/PR-010 navigation and automation regressions pass.
- Static close visual evidence passes at retained blockout quality. Moving full-render evidence timed out and is not claimed. Keep v269 **unpromoted** until moving visual, dock door/drawer/probe/tool-rack sweeps and final hall presentation gates are completed. v261 and v263-v268 are failed/nonparent candidates.
- The native source successor closes the fleet campaign-persistence subgate while leaving the v269 map hash unchanged. `ALBPressShopSupportFleetController` captures/restores an exact identity-checked two-CR01/two-MR01 format-12 snapshot, preserves the rest of an existing campaign root, and performs safe route/safety revalidation with no motion authority resumed. Fresh writer and reader processes agree on 15,045 bytes and SHA-256 `9c3ac306fef9535e9115f3e5b568ce9a113515635d64418438ee14760bd20114`; the complete four-unit dispatch regression remains green.
- `ALBControlRoomOperationsConsole` now binds fleet authority, renders the selected robot state/dock/battery and exposes Robot/Dispatch/Recall commands. Exact console-API PIE dispatches and recalls CR01-01, proves two missions and its correct dock, and cycles selection to CR01-02. Evidence/decision: `Saved/Audits/ControlRoom/control_room_support_fleet_pie_v269.json` and `Saved/Audits/SupportRobots/press_shop_support_fleet_dispatch_runtime_decision_v269_r2.json`.
- Physical and visual fleet-console gates now pass in the source successor. `BTN_SUPPORT_DISPATCH`, `BTN_SUPPORT_RECALL` and `BTN_SUPPORT_UNIT` are individually resolved through `HandleComponentInteraction`; the full route/dock cycle remains green. The initial cyan slab/floating controls are retained as rejected visual evidence. New v271 exposure-compensated materials are non-overwriting assets; the same walk-up camera now shows one dark contained HMI, bezel, raised keys and readable fleet row (SHA-256 `BE507496F47FC2B73E589DE220550F69469061BC458DCC24A2498F83095593B2`). This is a console subgate pass, not whole-shop promotion.

## Manufacturer CAD/dimensional reference intake (2026-08-06, latest)

- `SourceAssets/ReferencePacks/Manufacturer_CAD_References_v001/` is a reference-only, unpromoted intake containing verified/hash-recorded official ABB IRB 7710 and Schuler ServoLine/automation PDFs, with official ABB IRT 710 and AIDA public tandem specification links retained where local intake was unavailable or web-only. Do not redistribute or promote raw manufacturer content without a rights review.
- Use these sources to calibrate original Cairnwell press, transfer, front-of-line and robot proportions. Keep Cairnwell branding and gameplay interfaces; do not represent fictional equipment as an ABB, Schuler or AIDA product.
- `cairnwell_comparison_audit_v001.json` records that current press slide/bolster dimensions are in the correct large-panel class. Current shared train pitch is 7,500 mm versus public 5,200-5,900 mm examples; this is a review item, not permission to alter retained maps.
- PR-005 through PR-010 source families cover the expected coil-to-blank machinery chain, but end-to-end installation/promotion and production proof remain open.
- `DatasmithImporter` and `DatasmithCADImporter` are now enabled and verified in the actual Unreal 5.8 project (`Saved/Audits/CAD/datasmith_cad_importer_verification_v001.json`). This is editor import capability only; no manufacturer CAD has been imported and PDFs remain dimensional references rather than convertible 3D models.

## Four-berth dock-family source and MR01 fit checkpoint (2026-08-06, latest)

- Fleet authority is two CR01 plus two MR01 robots and four independent berths. v253 has proven provisional capacity, but no dock/robot is installed; do not claim the support fleet is operational.
- Preferred shared source is RP01 DockCore v003, SHA-256 `30BDF2776592811DB1B7243E4CB0D318AE7406C721274E54A23FE508D90D0350`. It preserves the exact common base/sockets and clears the MR service aperture by post-mounting the controls within the 2.6 m width. It is validated source only, not an Unreal asset.
- Preferred MR sources are dock v004 (`67234DEF9F5DC8A405113CEA24568793A317215C97EC6FFE75BE334CDF446839`) and robot v022 (`432233FA43ACB2D67A2E58DE8110272032D10EB53A82AF5971F8ACD3E895EBE8`). Exactly eight rack positions are now physically visible/accessibly packaged. Exact datum/static portal fit passes with 165 mm per side; moving collision/sweeps and Unreal runtime remain open.
- Preferred CR source is dock v007, SHA-256 `44C4201880265AB9DB10DBA24448F11B43BC5BFD29BA32A269498CD4099430F4`. All six interfaces pass, but current renders prove retained v014 source fit only. Actual Unreal CR01 v065 fit is still open and the conflicting outside envelope remains TBC.
- Isolated Unreal v008 is diagnostic-only and rejected for integration. Although its charging numbers were self-consistent, fresh portal views prove MR01 v021 is physically side-on: the visible vehicle length runs on local Y while its nominal charge components are on local -X. The intended operation is straight reverse docking with the arm folded upright, never sideways. Audits: `service_dock_actual_robot_fit_visual_decision_v008.json` and `service_dock_mr01_orientation_rejection_v008.json`.
- Decision: `Saved/Audits/SupportRobots/service_dock_family_source_visual_decision_v003.json`. Never parent v006/v007/v008. First create a clean non-overwriting MR01 successor from retained v022 with rear-face socket authority and v021 runtime/save regression, then repeat actual-robot collision/service-sweep gates before making any fresh direct v253 child for the four berths.

## Press Shop balanced support-layout checkpoint v253 (2026-08-06, latest)

- v251 is rejected/never-parent due one exact support-to-column overlap at the PR040 south header. v252 resolves the collision but is rejected/never-parent because its support task lighting is severely overexposed and the departments remain generic.
- Fresh direct-v249 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253`, SHA-256 `51CAF557666AB9F4FE6833165BEA30223200059E9AB548D38DF64074C7094842`, adds 143 balanced support-bay actors. Its 121 support blockers have zero overlaps with 1,920 inherited blockers. Exact management PIE, PR009/PR010 navigation and full Press Shop automation pass; automation is 16/16 with zero warnings/failures.
- Fresh evidence retains the separate maintenance/support-bay layout direction but does not pass release art: one camera is column-obstructed, eastern departments remain sparse/generic, and CR01/MR01 docks are absent.
- **Retain v253 only as an unpromoted support-layout checkpoint and authorized source for a fresh support-detail child.** v249 remains the protected shell parent; never parent v251/v252. Decisions: `Saved/Audits/PressShopIntegration/press_shop_structured_support_collision_rejection_v251.json`, `press_shop_structured_support_visual_rejection_v252.json`, and `press_shop_balanced_support_visual_decision_v253.json`.

## Four support-robot berths and MR01 dock source v001 (2026-08-06, latest)

- The Press Shop requires two CR01 and two MR01 robots, hence four independent berths. Reuse one dock asset per robot type and instance each twice.
- Read-only v253 screening found 74 collision-free MR01 pairs in the maintenance bay and 465 CR01 pairs in the utilities bay while reserving side service and 3 m straight approaches. Provisional best roots: MR01 X `-6495/-5095`, CR01 X `-1495/-295`, all Y `5160` cm. Capacity is proved; installation, navigation and service-route acceptance are not. Audit: `Saved/Audits/SupportRobots/press_shop_support_dock_placement_capacity_v253.json`.
- User Pro sheets pass visual-direction review with corrections for the incorrect cleaner-like MR01 depiction, exactly eight tools, CFR-X calibration travel and contradictory CR01 TBC envelopes.
- `SourceAssets/SharedSystems/MaintenanceAMR/Dock_Candidate_v001/LB_MR01_ServiceDock_v001.blend` links 38 objects from the new RP01 dock-core source and passes exact source/interface/pivot/eight-tool gates. Fresh renders fail release quality because the result remains a solid-cabinet blockout with hidden tools, sparse fabrication, floating identity and no real MR01/Unreal proof. Retain as technical evidence only; do not import/integrate. Decision: `Saved/Audits/SupportRobots/mr01_service_dock_source_visual_decision_v001.json`.

## Press Shop support-area v250 rejection (2026-08-06)

- Direct-v249 support staging child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v250`, SHA-256 `71BF04812BA6A29C95293E4E9E45BDAE8B5CCF982C80047B09990DF9D128D37F`, adds 45 existing assets at authoritative EST-P support anchors without changing v249, machinery or authority.
- Exact management PIE passes and the collision screen passes 45 support blockers against 1,920 inherited blockers with zero overlap pairs.
- Dedicated support views are a visual failure: isolated props, insufficient operational density, no coherent bay structure or supported services, and inadequate task illumination.
- **v250 is rejected visually and never a parent.** Preserve as evidence; build any successor directly from retained v249. Decision: `Saved/Audits/PressShopIntegration/press_shop_support_area_visual_rejection_v250.json`.

## Press Shop retained shell/lighting checkpoint v249 (2026-08-06, latest)

- Latest retained unpromoted whole-shop parent: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249`, SHA-256 `CCA3DA3BA67DAD74E4C58D7B0AB0F811639521F666B108987D2C775FA9C12B47`. It preserves machine-complete v241, the retained v242 graphite-grey shell and all accepted collision/navigation/runtime contracts. Rejected lighting studies v243-v248 are not in its ancestry.
- v249 changes only three broad movable preview-only roof-bounce lights. Geometry, machines, materials, collision, navigation and runtime authority are unchanged. Fixed-view upper-frame luminance improves across management, front and south views without material highlight clipping.
- Exact management PIE passes, full `LineBoss.PressShop` automation passes 16/16 with zero warnings/failures, and exact Play-state evidence proves 11 pale-silver stored coils plus one identified transfer coil.
- **Retain v249 as the latest unpromoted visual parent.** Do not promote or call the Press Shop complete: inherited structural-column sightline obstruction, support-area/operator presentation and end-to-end production gameplay remain open. Decision: `Saved/Audits/PressShopIntegration/press_shop_shell_lighting_visual_decision_v249.json`.

## Press Shop machine-complete/navigation checkpoint v241 (2026-08-06, latest)

- Latest retained unpromoted physical parent: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241`, SHA-256 `1CFF3E917A1FD02697CFA41BFF6E6ED08508F0648B14389B486D44820E44B636`. It carries the exact accepted PR009/PR010 v103 presentation, explicit PR010 collision ownership at the Train B/C S01 interface, and the exact accepted PR009/PR010 navigation contracts. No visible geometry, runtime authority or engineering datum was invented.
- Collision integration passes with zero restored-machine/train blocker overlaps. Integrated PR009 navigation passes 2/2 nonpartial service routes and PR010 passes 3/3, all with zero protected traversal. Exact v241 management PIE passes PR004-PR010 plus Train A-D authority and control routing. Full `LineBoss.PressShop` automation passes 16/16 with zero warnings/failures.
- Exact Play-state evidence proves 11 pale-silver stored coils plus one transfer coil; editor-before-Play coil captures remain invalid acceptance evidence. The restored machine chain and PR010/train interface are visibly present in the fresh v241 captures.
- **Retain v241 as the next physical parent, but do not promote it as release.** Upper-hall/perimeter darkness, structural-column camera obstruction, machine-facade contrast and incomplete support-area presentation remain visual holds. Continue with a fresh isolated v241 child. Decision: `Saved/Audits/PressShopIntegration/press_shop_machine_navigation_visual_decision_v241.json`.

## Press Shop missing-machine restoration / coil evidence checkpoint v239 (2026-08-06, latest)

- The user's audit finding is confirmed: v236 had native PR009/PR010 authorities but no identifiable PR009/PR010 presentation. Fresh child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239` restores all 510 exact accepted v103 presentation actors without adding authority or inventing datums. SHA-256: `FE38A3920A1B5A0076F4C19DE693789B79A9EC097EBBCD4F2B61D413DDFE3B6F`. Exact management PIE and full Press Shop automation pass 16/16.
- v239 is **integration HOLD / not promoted**. Its restored PR010 presentation has 132 conservative blocker contacts with the provisional Train B/C S01 infeed presentation; these are confined to the master-plan interface zone and must be classified/resolved before v239 can become a parent. Continue physical children from protected v236 until that decision is complete.
- Fresh exact PIE on v236 proves the coils remain pale silver: 11 stored plus CS-06 on the AGV. The dark version is a non-Play/editor capture-path artifact, not a retained material change. Static coil screenshots are invalid for acceptance; require exact PIE or standalone evidence. Proof: `Saved/ValidationScreenshots/PressShopIntegration/v236_pr003_pr004_coil_readability/press_shop_v236_runtime_inventory_north.png`.

## Press Shop roof/train-readability checkpoint v236 (2026-08-06, latest)

- Press Shop finishing remains ahead of gameplay expansion. v235 completes the physical hall roof with a continuous 91-panel grid and preserves at least 211.9999 cm measured clearance above the highest crane-labelled upper bound. Map SHA-256: `94D344ADCA249A00974907EAC8DEF80D6C24168FE62B214C8E722EBF639C1200`.
- Latest retained unpromoted whole-shop parent: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236`, SHA-256 `DBDE7CDB66CD2B284D8927F28597F4A72D821A6559E23AA67AD509DC934354A7`. It changes exactly 489 Train A-D presentation slots from charcoal to calibrated graphite and makes no geometry, transform, tooling, accent, machine, control or authority changes; v235 remains byte-identical.
- Exact v236 management PIE passes all PR004-PR010 and Train A-D authority/control checks. Full `LineBoss.PressShop` automation passes 16/16 with zero warnings/failures. Fresh views retain v236 for improved press-frame separation, but promotion remains forbidden because inherited wide cameras are column-obstructed and release lighting/material/support-area finishing is incomplete.
- Continue only from v236 for new whole-shop visual children. v231/v232/v234 are visual rejects and never parents. Evidence: `Saved/Audits/PressShopIntegration/press_shop_train_surface_readability_visual_decision_v236.json` and its referenced build, PIE, automation and screenshot records.

## Press Shop machine-flow and whole-hall visual checkpoint v230 (2026-08-06)

- User priority is now explicit: finish the Press Shop environment and machinery before further control-room/gameplay work. No new gameplay scope was added after this decision.
- Native PR009 now retains the exact blank IDs in each completed carrier and exposes a transactional released-stack handoff. PR010 accepts and saves the same stack manifest. Press Shop save root advances compatibly to format 12; legacy PR009/PR010 v1 snapshots remain accepted. The focused PR009-to-PR010 genealogy test and the full `LineBoss.PressShop` suite pass 16/16.
- The Coil AGV mesh dependency fault is closed additively: 11 exact missing material packages were created at the paths already referenced by the retained chassis and lift-deck meshes. Both meshes load and fresh logs contain no CoilAGV load errors. No mesh, engineering rating or runtime authority was changed.
- Fresh non-overwriting visual lineage: v229 extends the inherited ambient luminaire grid over all four installed train rows; v230 adds a map-only readable dark-charcoal override to exactly 489 installed-train material slots. Latest map: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230`, SHA-256 `C5BC0FFA15FD54AA2F5803ECC6B03DD2320A8C1BC6DB294EC0448177698145A4`. Protected v228 and v229 hashes remain unchanged.
- Exact v230 PIE passes one PR004-PR010 authority each, four Train A-D authorities, honest Start hold, selected-Train-A-only Start, controlled Pause/Stop and Train-B selection. Fresh fixed images show better train-body separation and continuous upper-hall luminaires, but the inherited high cameras remain obstructed by structural columns and the roof/perimeter still reads too black. **Retain v230 as the latest unpromoted whole-shop visual child; continue Press Shop visual/support-area completion before gameplay.**
- Evidence: `Saved/Audits/PressShopIntegration/coil_agv_missing_materials_repair_v001.json`, `press_shop_upper_hall_lighting_build_v229.json`, `press_shop_train_charcoal_readability_build_v230.json`, `press_shop_playable_management_pie_v230.json`, `Saved/Automation/PressShopFull_v229_r2/index.json`, and `Saved/ValidationScreenshots/PressShopIntegration/v230_playable_management/`.

## Whole-shop control-room ergonomics v228 and physical-button checkpoint (2026-08-06, latest)

- Fresh non-overwriting v227 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v228`, SHA-256 `1EE7EDC1CEB1A34E893C2EC9FE2971BF26C69A0CB80801819DA6A621936A462F`, moves only the PlayerStart and fixed walk-up camera 115 cm closer to the operations console. Protected v227 remains unchanged at `82B2D4A89F8C52CC5AD2872DB582EDEF0EC5FFBF3E516ABE7EADA026F193EBC7`; machine and authority changes are zero.
- The console now binds and displays live PR006-PR010 states in addition to PR005 and the selected train. Pause/Stop issue guarded controlled-stop requests across every bound station and the selected train; Start remains honestly limited to PR005 plus selected-train authority until PR009 stack identity, PR010 reservation and train blank-destack handoff are explicitly resolved.
- Fresh v228 walk-up evidence is materially more readable. Exact authored Start distance falls from 381.55 cm to 272.33 cm. Exact physical-button PIE passes Create, interlocked Start, authorized Train-A Start, Pause, Stop and Train-B selection through actual `BTN_*` hit components; B-D stay isolated. Exact standalone launch loads `LBControlRoomGameMode` and logs standing seat `X=2200 Y=4240 Z=95`, camera `Z=175`, yaw 90.
- Native build, Control Room 3/3, Press Shop 15/15 and exact v228 management gates are green. v228 remains unpromoted: the upper hall and western train bays remain underlit/sparse, CoilAGV material dependencies still warn as missing, physical DualSense hardware is untested, and full PR006-PR010 order/material orchestration remains open. Evidence: `Saved/Audits/ControlRoom/control_room_walk_up_ergonomic_build_v228.json`, `control_room_physical_buttons_pie_v228.json`, `control_room_standalone_spawn_v228.json`, and `Saved/ValidationScreenshots/PressShopIntegration/v228_playable_management/v228_control_room_walk_up.png`.

## Whole-shop playable management v227 and controller usability checkpoint (2026-08-06, latest)

- Retained whole-shop v226 remains immutable at SHA-256 `44E892DEA8F6D6D93F3CB5AF4988F2B79799005F9467D62C46414554EAF63451`. Fresh non-overwriting child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v227`, SHA-256 `82B2D4A89F8C52CC5AD2872DB582EDEF0EC5FFBF3E516ABE7EADA026F193EBC7`, changes only preview lighting: four column-blasting point lights are replaced by eight downward train-bay spotlights; authority and machine changes are zero.
- Exact v227 PIE again passes one PR004-PR010 authority each, one material-flow controller, four isolated Train A-D authorities, honest Start hold, selected-Train-A-only Start, controlled Pause, Stop and Train-B selection. Full post-change automation passes Press Shop 15/15 and Control Room 3/3. v227 remains unpromoted because fresh images still show underlit western train bays, a black/sparse upper hall and a control console that needs stronger walk-up legibility.
- Native control-room input now supports generic Unreal gamepads without removing keyboard/mouse: left stick movement, right stick view, Cross/A centre-view interaction, Circle/B reset, Triangle/Y stand/sit and left shoulder CCTV. The native regression proves the centre ray hits physical `BTN_START`; exact v226 authored distance is 381.55 cm inside the 900 cm limit. A physical DualSense device has not yet been hands-on validated.
- Current easiest-play conclusion: retain the standing walk-up control room as the primary interface, with optional seated overview and separate no-collision free-roam only for inspection. The main remaining gameplay gap is full PR006-PR010 orchestration/material handoff and clearer operator-screen status, not locomotion or controller mapping. Evidence: `Saved/Audits/ControlRoom/control_room_gamepad_authored_reach_v226.json`, `Saved/Audits/PressShopIntegration/press_shop_playable_management_pie_v227.json`, and `Saved/ValidationScreenshots/PressShopIntegration/v227_playable_management/`.

## Press Train A tooling-sightline/HMI v013 checkpoint (2026-08-06, latest train work)

- Powered C-hook v143 and bright hook/coil treatment v190 remain closed/frozen. v013 is an isolated direct child of v012; production placement remains `TBC_NOT_INVENTED`, and protected v010, v012, v107 and v213 are unchanged.
- Immutable `AssemblyStudy_v007` preserves exact `15,000 x 56,000 x 10,750 mm` bounds and 336 actors while providing five physically open facade apertures, true bolted window frames and real die-space throats. Source validation passes 15/15 with clean FBX round-trip.
- `/Game/LineBoss/Maps/LB_PressTrainASightlineCandidate_v013` replaces only the 336 presentation actors, retains one native authority and exact motion bindings, uses genuinely translucent glazing, and places one live native TextRender HMI on the authored console. Map SHA-256 `24DB4253EB910A1282891F38CA52D6A8B5A93E2D01E1ECE9006A57CF12A56683`.
- Static, live PIE, exact Train A automation and all 15 `LineBoss.PressShop` regressions pass. PIE proves slide/die, transfer, robot and panel motion; one-at-a-time workpiece state; all beacons; readable HMI; controlled stop; fault recovery; isolation; and save restoration.
- Fresh Unreal views materially pass S02/S04 tooling visibility through real translucent glazing and the native access-fault HMI. S07 remains on visual hold because retained support/gate geometry crowds the robot articulation silhouette. Train A also still lacks state-driven sound, collision/sweep/navigation and maintenance/die-change clearance gates; installed datums remain TBC.
- Decision: **RETAIN V013 AS AN UNPROMOTED TRUE-TOOLING-SIGHTLINE AND AUTHORED-HMI CHECKPOINT; S07 ROBOT, SOUND, PHYSICAL CLEARANCE AND INSTALLED DATUMS REMAIN OPEN.** Review: `Saved/Audits/PressTrains/press_train_a_sightline_visual_review_v013.json`.

## Press Train A motion/state v012 checkpoint (2026-08-06, latest train work)

- Powered C-hook v143 and bright combined hook/coil treatment v190 remain closed/frozen. Train A stays isolated at local origin; production placement is `TBC_NOT_INVENTED`, and protected v010, v107 and v213 are unchanged.
- New immutable source `AssemblyStudy_v003` adds five separate press slides, five upper dies, five lower dies/bolsters, five carried workpiece states, an eight-edge hierarchical S07 robot, explicit red/amber/green stage beacons and authored HMI hardware while preserving exact measured bounds `15,000 x 56,000 x 10,750 mm`. Source validation passes 13/13 with clean FBX round-trip.
- Native `ALBPressTrainAStation` now binds stage-matched slides/upper dies, one-at-a-time carried panel presentation, the hierarchical robot shoulder root and mutually exclusive state beacons. Compile passes, exact `RuntimeSafetySave` passes, and all 15 `LineBoss.PressShop` regressions pass.
- v011 stopped on a reflected native-class `isinstance` API mismatch and is never a parent. Fresh direct v010 child `/Game/LineBoss/Maps/LB_PressTrainAMotionCandidate_v012` passes exact build/static gates with 336 presentation actors, one native authority, one live text HMI and exact robot hierarchy. Map SHA-256 `E51F2EDE5D8D2C71FC7E096E79535A6389E4FEC5EADBF373842268E32C22F688`.
- Live PIE passes controlled stop, access-fault recovery, zero-energy isolation and save while measuring 79.16 cm slide/upper-die motion, 34.94-degree robot motion, 284.90 cm formed-panel motion, exactly one carried state and all five green/amber/red beacons.
- Fresh Unreal views prove the visual hold: normal player views still hide tooling behind operator skins, S07 robot articulation is obscured, the authored HMI panel is not yet bound to live native text, lighting is overbright against the black isolation surround, and Train A has no state-driven sound. Decision: **RETAIN V012 AS AN UNPROMOTED TECHNICAL MOTION/STATE CHECKPOINT; VISUAL RELEASE REJECTED.** Closure: `Saved/Audits/PressTrains/press_train_a_motion_closure_v012.json`.

## Press Train A native runtime v010 checkpoint (2026-08-06, latest train work)

- Powered C-hook work remains closed/frozen at retained v143 and combined hook/coil readability remains retained at v190. Train A remains isolated at local origin; v107, v213 and all accepted production maps are unchanged, and world placement remains `TBC_NOT_INVENTED`.
- New native `ALBPressTrainAStation` supplies an identified reserved-blank input buffer, deterministic seven-stage cycle, identified good-panel output, reject counting, trusted control-room commands, controlled stop/restart, access and E-stop faults, acknowledgement/reset, zero-energy isolation evidence and moving-state save restoration. `ULBPressShopSaveGame` advances compatibly to format 11 with `FLBPressTrainASaveState` version 1.
- `/Game/LineBoss/Maps/LB_PressTrainARuntimeCandidate_v010` is a fresh isolated child of retained v009 with exactly one native authority, 309 presentation actors, one live HMI and explicit bindings for three destack, 25 transfer, eight unload-robot and two formed-panel actors. Map SHA-256 `8CA5F44D54F3D47E160AF54D92C6D8307BC74CAF0778711FA3A71E1C76E81DD2`; v009 remains unchanged at `ECEBA05566328E4DAE480BD58EAD543F6442E6B7558440E3004C57A43F97696A`.
- Compile, exact Train A automation and all 15 `LineBoss.PressShop` regression tests pass. Live PIE measures 119.96 cm destack, 749.20 cm transfer, 34.81-degree robot and 288.54 cm panel motion, and passes HMI, controlled-stop, fault-recovery, isolation and save gates. Three failed validator/runtime attempts are preserved: over-broad world scope, Python reflected-name mismatch and Static component mobility.
- Four fresh runtime captures prove the current visual limit: there are no separate press-slide meshes, carried workpiece state is unclear, the simplified S07 arm is not yet a credible articulated unload, and the fault image lacks readable HMI/beacon cause-and-effect. Decision: **RETAIN V010 AS AN UNPROMOTED TECHNICAL RUNTIME CHECKPOINT; VISUAL RELEASE REJECTED.** Next author separate moving press/tooling geometry, state feedback/sound and isolated collision/navigation/clearance gates. Closure: `Saved/Audits/PressTrains/press_train_a_runtime_closure_v010.json`.

## Press Train A source-detail integration v009 checkpoint (2026-08-06, latest train work)

- Powered C-hook work is closed/frozen at retained v143 and combined hook/coil readability remains retained at v190. Train A production placement remains `TBC_NOT_INVENTED`; v107, v213 and all accepted production maps are unchanged.
- New immutable `SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v002/` expands the train from 163 to 309 presentation objects while preserving exact local bounds `15,000 x 56,000 x 10,750 mm`. It differentiates central-stage tooling/mechanics/utilities, adds S01 blank-entry/centring hardware and adds S07 robot/panel/stillage handling. Source validation passes 10/10 with clean FBX round-trip; blend SHA-256 `4C8A2A2D0885B62DC340C56256E25D4DC09B0A80B88CE59AC7DD6DB6551F7ACA`, manifest SHA-256 `4DBD4A70D9B3A014247A5C16E018BA9DB970E84C387B13CE79F69047D345E585`.
- `/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyDetailCandidate_v009` is an isolated child of the v008 validation environment only. It removes the 163 inherited presentation actors and places all 309 exact v002 manifest actors while retaining 32 validation/collision/camera actors. Map SHA-256 `ECEBA05566328E4DAE480BD58EAD543F6442E6B7558440E3004C57A43F97696A`; exact static/import/collision/nav-authoring/performance/branding gate passes with seven fixed cameras and exact bounds.
- Seven fresh Unreal images under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_assembly_detail_v009/` prove the added detail reads in-engine. S01, S07, utilities and tool variation are materially clearer, but the pale simplified press bodies, block-like tooling, static endpoint process and black isolation surround remain below release quality; the mechanics view also has `5.96%` clipped highlights.
- Decision: **RETAIN V009 AS AN UNPROMOTED ISOLATED SOURCE-DETAIL INTEGRATION CHECKPOINT; WHOLE TRAIN RELEASE HOLD.** Next implement isolated native Train A runtime/save/fault/isolation authority and component bindings. Do not install it in v107/v213 until authoritative Train A-D datums are supplied. Closure: `Saved/Audits/PressTrains/press_train_a_assembly_detail_closure_v009.json`.


## Press Train A exact-assembly visual-readability v008 checkpoint (2026-08-06, latest train work)

- Powered C-hook work is closed/frozen at retained v143, combined hook/coil readability remains retained at v190, and cumulative PR005-PR008 v213 remains the unpromoted station-detail checkpoint. Train A production placement remains `TBC_NOT_INVENTED`; no production map, v107, v213, v053, v069 or accepted station authority changed.
- `/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyVisualCandidate_v008` is a fresh direct child of exact-import baseline v005, not v069. It preserves all 163 manifest objects, transforms, materials, seven collision proxies, walkable isolation floor and local bounds `15,000 x 56,000 x 10,750 mm`; only non-production evidence lighting/exposure and seven fixed cameras change. Map SHA-256: `DCB2CF4A6511D9D540AA4C83764AEC23675BE215CDA745CA8A492853FEB6BAE7`; v005 remains unchanged at `675994525DB72BADC561F1067C8788649638D68A76AF98AAAAD7B448934C9EF6`.
- Exact static gate passes with 189 inherited scoped actors, 163 presentation actors, seven cameras, zero transform/material/collision/branding failures and exact bounds. The first scope audit is preserved because it incorrectly treated six v008-only validation fill lights as v005 provenance; the corrected rule excludes only those lights and weakens no machine check. v006 and v007 are preserved overexposed calibration evidence and are never parents.
- Seven fresh 1920 x 1080 Unreal images under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_assembly_visual_v008/` resolve v005's black underexposure and buried cameras. Hero mean luminance improves from `11.11` to `65.70/255` with `1.95%` clipped highlights. The train is readable, but S02-S06 remain repetitive/mechanically shallow, S01/S07 process handoffs remain weak, carts/couplings are simplified, surfaces are pale/clean and the black isolation surround proves no installed scale.
- Decision: **RETAIN V008 AS AN UNPROMOTED ISOLATED VISUAL-READABILITY CHECKPOINT; KEEP V005 AS THE EXACT IMPORT BASELINE; WHOLE TRAIN RELEASE HOLD.** Next create a source/detail successor that differentiates stage mechanics/tooling/utilities and makes S01 packaged-blank entry plus S07 formed-panel inspection/stillage truthful. Do not place Train A in v107/v213 without authoritative datums. Closure: `Saved/Audits/PressTrains/press_train_a_assembly_visual_closure_v008.json`.

## Cumulative PR005-PR008 release-detail v213 checkpoint (2026-08-06, latest full-line work)

- The powered C-hook task is closed/frozen at retained v143, with combined hook/coil readability retained at v190; no hook geometry or PR003 coil material changed. v211 and v212 are preserved failed cumulative attempts and are never valid parents: v211 exposed the missing PR005 v197 cage-infill donor, and v212 exposed a collision-getter API mismatch. Failure record: `Saved/Audits/PressShopIntegration/press_shop_cumulative_release_failures_v211_v212.json`.
- `/Game/LineBoss/Maps/LB_PressShop_CumulativeReleaseCandidate_v213` is a fresh direct child of retained full-line parent v107, not a chain through station candidates. It replays the exact read-only donor specifications from PR005 v205, PR006 v208, PR007 v209 and PR008 v210: 43 actors added, six superseded PR005 v053 logistics actors removed, 48 generic PR008 v082 anchor primitives removed, the retained PR005 v197 cage infill included and four inherited PR006/PR007 spot calibrations matched. Map SHA-256: `1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554`.
- All protected hashes remain unchanged, including v107 SHA-256 `E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77`. Exact v213 gates pass: PR005 commissioning/interlocks/fault/save and real 48 kHz state-driven spatial audio; PR006 native sequence; PR007 wash/lube sequence and both strip joints; PR008 motion/HMI/safety/isolation/save; nonpartial `1396.953125 cm` navigation; collision/navigation; traceable PR004-to-PR005 handoff; measured PR008-to-PR009 interface; and inherited accepted PR009/PR010 authority.
- Five fresh live images under `Saved/ValidationScreenshots/PressShopIntegration/v213_pr005_runtime/` prove all four local station directions coexist and provide the exact inherited v107 connected-line framing. Station detail is coherent, but the upper hall/perimeter remains black and sparse, several floor pools are too hard/bright, PR005 service identity is dark and release wear/utilities/service density remain open. The first whole-line attempt requested obsolete `LB_PR005_V046_CAM_PR005WholeLine` and failed without changing the map; the correct `LB_ENV_V107_CAM_ConnectedLine` image SHA-256 is `6FE04DA780B2261A641098E090EEF359ACAFC2B0A8EFC7FEDAF4D55EF5935617`.
- Decision: **RETAIN V213 AS THE UNPROMOTED CUMULATIVE PR005-PR008 DEVELOPMENT CHECKPOINT; KEEP V107 AS THE FULL-LINE VISUAL PARENT; DO NOT PROMOTE THE HALL.** No camera-only successor is needed. The correct whole-line view confirms the large empty slab/column field is reserved space left by the four absent press trains; continue with an isolated Press Train A visual successor and obtain authoritative Train A-D installation datums before production placement. Closure: `Saved/Audits/PressShopIntegration/press_shop_cumulative_release_closure_v213.json`.

## PR-008 authored anchor-base v210 checkpoint (2026-08-06, latest full-line work)

- Powered C-hook work remains closed/frozen at retained v143, with combined hook/coil readability retained at v190. PR005 v205, PR006 v208 and PR007 v209 remain separate local checkpoints. Retained `/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107` is still the full-line visual parent and its SHA-256 remains `E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77`.
- Exact v107 baseline audit found one native PR008 authority, all 14 mover bindings and 48 inherited generic v082 anchor plate/stud actors. New immutable source `SourceAssets/PR008/ServoBlankingLine/ReleaseAnchorBase_v001/` supplies six measured NoCollision modules covering the entry loop, servo feed, pre-punch, shear, HPU bundle and cabinet bases, with authored plates, washers, hex nuts, cleats and weld beads. Capacity, grade, torque, embedment and certification remain TBC.
- `/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210` is a fresh direct child of v107. It removes exactly those 48 generic anchor actors in the child and places six authored modules within 2 mm while changing no machine, datum, authority, mover pivot, collision or navigation. Map SHA-256: `056084A36740F9E7EA50DE079D5DC22DD62AA9CC16F010EC735B2FF78E1F0CD6`.
- Exact gates pass: native PR008 sequence/motion/HMI/safety/isolation/save, one authority and all 14 bindings, PR008-to-PR009 measured interface, nonpartial navigation, collision/navigation, traceable PR004-to-PR005 handoff, inherited accepted PR009 enclosure/door/identity authority with 55 cm blank clearance per side, and inherited accepted PR010 scope. The first runtime attempt is preserved as a stale validator-version failure; the corrected validator matches compiled station version 3 and root save format 10 without weakening checks.
- Three fresh live views under `Saved/ValidationScreenshots/PressShopIntegration/v210_pr005_runtime/` show improved local machine grounding and the inherited running HMI. Anchor hardware remains small/dark at floor level, materials and local light pool remain development-clean, and the upper hall remains black/sparse. The process and HMI capture processes produced valid PNG evidence before exiting `-1073741819`; do not claim clean exits.
- Decision: **RETAIN V210 AS AN UNPROMOTED LOCAL PR-008 AUTHORED-ANCHOR CHECKPOINT; KEEP V107 AS THE FULL-LINE VISUAL PARENT; DO NOT PROMOTE WHOLE PR-008 OR THE HALL.** A later explicit cumulative merge must combine retained PR005/PR006/PR007/PR008 work rather than assuming separate checkpoints are cumulative. Closure: `Saved/Audits/PressShopIntegration/press_shop_pr008_authored_anchor_closure_v210.json`.

## PR-007 installed release-detail v209 checkpoint (2026-08-06, latest full-line work)

- Powered C-hook work remains closed/frozen at retained v143. PR005 v205 and PR006 v208 remain separate local checkpoints; neither is the PR-007 parent. Retained `/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107` is still the full-line visual parent and its SHA-256 remains `E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77`.
- New immutable source `SourceAssets/PR007/WasherLubeUnit/ReleaseDetail_v001/` supplies six dimensioned NoCollision modules: fabricated four-door operator surrounds, distinct blue wash and green lubricant service manifolds/routes with gauges and drains, mist-extraction fabrication, infeed/outfeed sensor-guide portals, and an 8,000 x 5,800 x 12 mm sealed-grey-concrete inset. It changes no datum, strip bridge, safety authority, native door/window/HMI or mover pivot and adds no static fake spray state.
- `/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209` is a fresh direct child of v107. Map SHA-256: `FF4FB682B9EDD49EEAF447AC6835B26AFD8501CAB1D16357C99352405C64EC3A`. Exact import is within 2 mm, one native PR007 authority and all seven mover bindings remain unchanged, and lighting is recalibrated to 460/370 cd side accents plus one broad 19 cd fixture.
- Exact v209 gates pass: running wash/lube consumption and strip travel, controlled stop/restart, guard-open fault, corrected reset and stable save; nonpartial `1396.953125 cm` navigation; collision/navigation; traceable PR004-to-PR005 handoff; both inherited PR007 strip/bridge joints; and inherited accepted PR010 scope. The first two runtime samples are preserved timing-window failures; the unchanged checks passed after lubricant consumption exceeded reflected-float precision.
- Four fresh live views under `Saved/ValidationScreenshots/PressShopIntegration/v209_pr005_runtime/` pass the local installed-service direction and show readable live HMI `RUNNING | WASH 82% | LUBE 76%`. The connected view still proves excessive empty slab and a dark/sparse upper hall; state-driven visible spray/film/mist, release wear/decals, subjective audio and final Pro equivalence remain open.
- Decision: **RETAIN V209 AS AN UNPROMOTED LOCAL PR-007 INSTALLED-SERVICE DEVELOPMENT CHECKPOINT; KEEP V107 AS THE FULL-LINE VISUAL PARENT; DO NOT PROMOTE WHOLE PR-007 OR THE HALL.** A later explicit cumulative merge must combine retained PR005/PR006/PR007 work. Closure: `Saved/Audits/PressShopIntegration/press_shop_pr007_release_art_closure_v209.json`.

## PR-006 installed release-detail v208 checkpoint (2026-08-06, latest full-line work)

- The powered C-hook remains closed/frozen at v143. PR005 v205 remains a separate local service-bay checkpoint and is not the PR-006 parent: exact audit proved v205 contains zero PR-006 native authority. Retained `/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107` is the correct full-line visual parent; its SHA-256 remains `E6851D041D3D566B2FE32560F331725CBB1FE84B034E7B86DA9B0D33191ECF77`.
- New immutable source `SourceAssets/PR006/PrecisionCassetteLeveller/ReleaseDetail_v001/` supplies six dimensioned NoCollision presentation modules: fabricated operator access, drive utility rack with filters/gauges/routes, crown ribs/seams/fasteners/lift sockets, infeed and outfeed process portals, and an 8,200 x 5,350 x 12 mm sealed-grey-concrete inset. It changes no datum, 1500 mm strip, mover pivot or safety authority.
- v206 stopped on the UE 5.8 material-slot API mismatch and is failed partial evidence; v207 was a fresh v107 child but its 180/145 cd calibration made the machine too dark. Preserve both and never parent from either. `/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208` is another fresh direct child of v107, not v206/v207. Map SHA-256: `EBE2210C87FC1AA23B0364C4BF24859C31721B6A2B7D1470B68DA58AF4B1E98B`.
- v208 uses restrained 420/340 cd side accents plus one broad 18 cd linear fixture. Four fresh live views under `Saved/ValidationScreenshots/PressShopIntegration/v208_pr005_runtime/` pass the local installed-detail direction and show readable live HMI `RUNNING | GAP 1.15 mm | LOAD 58%`. The connected view still proves a dark/sparse upper hall and neighbouring release-detail mismatch, so whole-hall and final PR-006 promotion remain held.
- Exact v208 gates pass: one native PR-006 authority, all 28 mover bindings, calibration/running/controlled stop/restart/cassette-unlocked fault/reset/save, valid nonpartial `1396.953125 cm` navigation, static collision/navigation, traceable PR004-to-PR005 handoff, unchanged PR006-to-Pro-PR008 joints (`-0.074981689 cm` overlap; `0.000007629 cm` lateral error), and inherited accepted PR-010 authority.
- Decision: **RETAIN V208 AS AN UNPROMOTED LOCAL PR-006 DEVELOPMENT CHECKPOINT; KEEP V107 AS THE FULL-LINE VISUAL PARENT; NEVER PARENT V206 OR V207; DO NOT PROMOTE WHOLE PR-006 OR THE HALL.** Continue matching release-detail work at PR-007, then plan an explicit cumulative branch merge rather than assuming separate PR005/PR006 checkpoints are already combined. Closure: `Saved/Audits/PressShopIntegration/press_shop_pr006_release_art_closure_v208.json`.

## PR005 installed service-return bay v205 checkpoint (2026-08-06, latest PR005 release-art work)

- The powered C-hook task remains closed and frozen at retained v143; no hook or PR003 coil material was changed. Retained runtime/audio parent remains `/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198`, SHA-256 `B18AD5D7D6321DBE2FA176FC3A1C15094E54950F6B9B63AEAA1068CE3C7E01A2`.
- v199-v201 proved that material/light escalation did not fix the isolated dark logistics blockout; v202 overexposed the slab; v203 put the new service screen camera-side; v204 corrected screen placement but left mirrored/cropped identity and excessive local fill. Preserve v199-v204 as visual rejects and never use them as parents. Record: `Saved/Audits/PressShopIntegration/press_shop_pr005_release_art_visual_rejections_v199_v204.json`.
- New immutable source `SourceAssets/Candidate/PressShop/PR005/ServiceBayInstalled_v012` and UE derivative `ServiceBayInstalled_UnrealDerived_v013` replace the six inherited v053 logistics blockouts with one 4,500 x 2,000 x 2,450 mm installed service-return bay: detailed stillage, pallet/crates, trolley, sealed-concrete inset, open entrance, rear mesh screen, player-facing PR-005 identity, source-authored task fixtures and dock bollards. Exact intake passes dimensions, handedness, pivot and all material slots with zero reported drift.
- `/Game/LineBoss/Maps/LB_PressShop_PR005ReleaseArtCandidate_v205` is a direct child of v198, not v199-v204. It preserves production flow and native PR005 authority, uses six selective collision boxes and two restrained 20 cd local fixture lights. Map SHA-256: `4DB252D89BFBBD4E4515D6D3BDED0CB6A3375D44E7E26D3E48A3C20B216FADD7`.
- Exact v205 gates pass: 1,396.953125 cm runtime navigation path, static collision/navigation, traceable PR004-to-PR005 handoff, commissioning/interlocks/fault/in-memory restore and state-driven spatial audio on the real 48 kHz Windows device. The audio audit wrote PASS before Unreal crashed during post-gate shutdown with `-1073741819`; preserve the crash log and do not claim a clean process exit.
- Seven fresh views are under `Saved/ValidationScreenshots/PressShopIntegration/v205_pr005_runtime/` and `pr005_release_art_v205/`. Player/elevated views pass the local installed-service direction. The whole-line view proves the inherited logistics datum is still isolated in a sparse foreground, and PR005/hall materials remain bright/flat versus the Pro references.
- Decision: **RETAIN V205 AS AN UNPROMOTED LOCAL SERVICE-BAY DEVELOPMENT CHECKPOINT; KEEP V198 AS THE RUNTIME/AUDIO PARENT AND V197 AS THE EXTERIOR VISUAL CHECKPOINT; DO NOT PROMOTE WHOLE PR005.** Physical gate travel/state binding, subjective whole-hall mix, whole-hall release art and the 10.4 m versus 11.5 m notation remain open. Closure: `Saved/Audits/PressShopIntegration/press_shop_pr005_release_art_closure_v205.json`.


## PR-003/PR-004 combined powered C-hook + coil-readability v190 branch (2026-08-05, latest combined work)

- Hook work from the separate task is now merged, not assumed: `/Game/LineBoss/Maps/LB_PressShop_PR003PR004HookLightingMergeCandidate_v190` is a direct isolated child of retained v180. It replaces only the inherited Candidate_v034 hook presentation with retained manufacturer-neutral Candidate_v035 geometry and adds three v143-equivalent proof cameras. Sheet 2 layout, v180 lighting/materials, AGV/crane/navigation/collision/gameplay authority and all protected predecessors remain unchanged.
- Fresh live PIE inventory evidence `Saved/ValidationScreenshots/PressShopIntegration/v190_pr003_pr004_hook_lighting_merge/press_shop_v190_runtime_inventory_north.png` proves exact physical inventory (11 stored + 1 in transfer) and pale-silver cylindrical coils with naturally dark bores. The earlier dark static-editor images are a capture-path artefact: unchanged v180 is also dark through that path, so live PIE is authoritative for lighting/material review.
- Three fresh live carry views under `Saved/ValidationScreenshots/PressShopIntegration/v190_pr004_crane_runtime/` prove the detailed yellow C-hook's lower arm passes through the coil bore and supports the load from below, with no visible hover, clipping or registration drift.
- All six exact v190 gates pass: primary 40 t transfer, AGV fault/recovery/save/restore/handoff, independent 30 t support-crane dispatch/return, traceable PR004-to-PR005 handoff, runtime navigation and collision/navigation. Map SHA-256: `B8C71FB66552FB5EEEDD48BCB81E29DD1AD42A5EE89C0D644430E5D959FD804F`.
- Decision: **RETAIN V190 AS THE UNPROMOTED COMBINED HOOK/COIL-READABILITY DEVELOPMENT BRANCH; KEEP V124 AS THE PRIMARY LAYOUT CHECKPOINT; DO NOT PROMOTE OR CERTIFY.** The upper hall/distant bays still need a release-art lighting and density pass plus fresh fixed-camera Pro comparison. Hook SWL/structure/fatigue/contact/drive/braking/certification remain TBC. Review: `Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_hook_lighting_merge_visual_review_v190.json`; closure: `Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_hook_lighting_merge_closure_v190.json`.

### Whole-hall readability experiments v191-v192 (2026-08-05, visual rejects)

- v191 and v192 were each built directly from retained v190; neither uses the other as a parent. Both preserve the hook, coils, exact 11+1 inventory and runtime authority. They test muted architectural liners, an additional support-side row of linear LED high-bays and broad wall wash using live PIE rather than the invalid dark static capture path.
- v191 improves the ceiling grid but fails because the north wall remains too black, the management camera is column-occluded and the support/logistics bay remains a dark sparse void. v192 corrects framing and lifts the front-end wall/ceiling hierarchy without darkening the coils, but proves the support/logistics problem is missing installed content and developed envelope—not something more light can solve.
- Decision: **REJECT V191 AND V192 AS WHOLE-HALL PARENTS; DO NOT REGATE OR PROMOTE; RETURN TO RETAINED V190 AND INTEGRATE MISSING STATIONS/SUPPORT AREAS BEFORE FURTHER HALL LIGHTING.** Records: `Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_whole_hall_visual_rejection_v191.json` and `press_shop_pr003_pr004_whole_hall_visual_rejection_v192.json`.

## PR-005 Candidate_v002 isolated Unreal mesh intake v003 (2026-08-05, latest PR-005 work)

- Read-only comparison confirms retained v053 contains proven PR005 runtime/handoff/collision/navigation authority but only the earlier open machine presentation, while source Candidate_v002 supplies the stronger enclosure, controlled glazing, maintenance access, HMI/utility exterior and presentation-only process witnesses. World placement remains `TBC_NOT_INVENTED`; v053 was not changed.
- The first isolated Unreal import under `ExteriorEnclosure_v002` is preserved failed evidence: UE 5.8 Interchange imported every valid source FBX at exactly 1/100 dimensions and ignored the requested uniform scale. No failed asset was integrated or promoted.
- Immutable source Candidate_v002 remains unchanged. New derivative `SourceAssets/Candidate/PressShop/PR005/UnrealDerived_v003` applies only a documented local-vertex x100 FBX compensation. Nine new assets under `/Game/LineBoss/Candidates/PressShop/PR005/ExteriorEnclosure_v003/Meshes` now match source dimensions exactly.
- Corrected handedness-aware audit proves every mesh dimension and pivot-local bound within 2 mm, including Blender +Y to Unreal -Y conversion, with maximum reported drift zero. Decision: **TECHNICAL MESH INTAKE PASS / WORLD PLACEMENT, MATERIALS, COLLISION, NAVIGATION, INTERLOCKS, SAVE, RUNTIME MOVER SUBSTITUTION AND VISUAL INTEGRATION HOLD / NOT INTEGRATED / NOT PROMOTED.** Audit: `Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_enclosure_unreal_handedness_reaudit_v003.json`.

## PR-003/PR-004 powered C-hook v143 branch (2026-08-05, latest powered-hook work)

- New manufacturer-neutral source `SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v035` was built from official Bushman, Winkle and Caldwell design evidence. It includes the credible fabricated frame/load-arm/contact/rotator/hoist/electrical/sensor/guard details required by the brief; no WIMO branding, proprietary markings or capacity claim was copied.
- The independent Blender/FBX audit passes (`Saved/Audits/press_shop_crane_powered_chook_candidate_v035_source.json`) and the Unreal import preserves exact source bounds and ten material roles. Nominal `1900 x 1500 mm`, interface `1800-2100 mm OD x <=1550 mm`, 590 mm bore/load datum and +150 cm body-to-load-centre relationship are preserved. All unavailable engineering values are TBC.
- v141 passed the exact primary-crane pickup/carry/deposit, AGV dock/fault/recovery/save/restore, independent 30 t support crane, PR004-to-PR005 handoff, navigation and collision gates but failed visual acceptance. v142 is also a preserved camera-framing reject.
- `/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v143` is a camera-only successor. Live full-side, true bore-axis and load-arm-oblique evidence proves that the lower arm enters the bore and carries from below without visible clipping, separation or registration drift.
- Decision: **RETAIN V143 AS AN UNPROMOTED DEVELOPMENT BRANCH ONLY.** No engineering certification or release promotion is implied. v124, v135 and v136 remain immutable. See `Saved/Audits/press_shop_pr004_powered_chook_visual_review_v143.json` and `Saved/Audits/PressShopIntegration/press_shop_pr004_powered_chook_closure_v143.json`.

## PR-003 coil-readability v180 branch (2026-08-05, latest environment/readability work)

- The coils went dark because the imported v107 environment-lighting policy disabled/reduced local PR-003 illumination; all 12 inherited pale-silver material assignments were unchanged. v138 is preserved as the dark visual reject, and v139 is preserved as the overbright/clipped reject.
- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR003PR004CoilReadabilityCandidate_v180` retains restrained physical task-light pairs on both north and south sides of the store. It changes no coil material, Sheet 2 `6 x 2` layout, AGV inventory model, machinery, navigation or runtime authority. It was rebased to v180 so the independent powered-hook v141 branch keeps an unambiguous identity.
- Live PIE evidence `Saved/ValidationScreenshots/PressShopIntegration/v180_pr003_pr004_coil_readability/press_shop_v180_runtime_inventory_north.png` shows readable pale-grey/silver cylinders with naturally dark bores and the exact runtime inventory of 11 stored plus one physical coil in transfer.
- All six exact v180 gates pass with zero failures: primary 40 t crane transfer, exact AGV fault/recovery/save/restore/handoff sequence, independent 30 t support-crane dispatch/return, PR004-to-PR005 traceable handoff, runtime navigation and collision/navigation. Closure: `Saved/Audits/PressShopIntegration/press_shop_pr003_pr004_coil_readability_closure_v180.json`.
- Decision: **RETAIN V180 AS THE UNPROMOTED COIL-READABILITY/ENVIRONMENT DEVELOPMENT BRANCH; KEEP V124 AS THE PRIMARY PR003/PR004 LAYOUT CHECKPOINT**. Whole-hall visual approval remains open because the upper hall and distant bays are still too dark/sparse for release art.

## PR-003/PR-004 coil AGV and powered C-hook v136 checkpoint (2026-08-05, latest primary-task work)

- The user-supplied real powered C-hook photo is typology/proportion reference only. No WIMO branding or `16t` claim was copied. New source `SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v034/` provides a fabricated C spine, lower bore arm, replaceable red/black pads, powered rotator, motor/gearbox, encoder, junction box, hoses and sensors. Source FBX audit passes dimensions/material identities; every engineering performance value remains TBC.
- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookCandidate_v136` is a direct successor of the exact-runtime AGV candidate v135. It replaces only the active purpose-built hook presentation, preserves the inherited transform, the project `590 mm` coil-bore datum and `+150 cm` body-to-load centre, and leaves immutable v124 unchanged.
- Fresh live runtime side and bore captures under `Saved/ValidationScreenshots/PressShopIntegration/v136_pr004_crane_runtime/` prove the lower yellow arm enters the coil eye and supports the packaged coil from below. Visual decision: retain the real-reference powered C-hook direction, with SWL, structure/fatigue, contact pressure, rotator torque/brake, clearances, interlocks and certification all TBC. Review: `Saved/Audits/press_shop_pr004_powered_chook_visual_review_v136.json`.
- Exact v136 gates pass: primary 40 t coil transfer; independent 30 t maintenance dispatch/return with zero production-load drift; traceable PR004-to-PR005 handoff; runtime navigation; static collision/navigation; and exact AGV fault, no-drift, named recovery, in-flight save/restore and handoff-ready dock pose. The physical inventory is exactly 11 stored coils plus one in transfer.
- Decision: **RETAIN V136 AS THE UNPROMOTED POWERED-C-HOOK/AGV DEVELOPMENT BRANCH; KEEP V124 AS THE LATEST PRIMARY PR003/PR004 CHECKPOINT**. Closure: `Saved/Audits/press_shop_pr003_pr004_powered_chook_checkpoint_v136.json`. Do not promote v136 as engineering authority until its TBC design and whole-area visual holds are closed.

## PR-003 Sheet 2 coil-store layout v124 checkpoint (2026-08-05, latest primary-task checkpoint)

- User review correctly identified excessive unassigned space around the PR-003 coils. Read-only v118 inspection proved the installed store was an inherited `3 x 4` arrangement. The authoritative `Sheet_2_PR001_to_PR005_Operational_Plan.png` instead defines 12 positions as two rows of six, with `2.2 m` centre pitch along each row and `6 m` between row centrelines for crane/maintenance clearance.
- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR003Sheet2LayoutCandidate_v124` was duplicated directly from retained v118. It moves all 122 actors belonging to the 12 complete slot clusters as units into the authoritative `6 x 2` arrangement. PR-004/PR-005 geometry, collision settings, navigation roles, machinery/gameplay authority and v118 remain unchanged. Build: `Saved/Audits/press_shop_pr003_sheet2_layout_build_v124.json`.
- All five exact-map gates pass: primary 40 t crane pickup/transfer/deposit from moved CS-10, maintenance 30 t dispatch/return, runtime navigation, collision/navigation and traceable PR-004-to-PR-005 handoff. Runtime carry and package-close images are under `Saved/ValidationScreenshots/PressShopIntegration/v124_pr004_crane_runtime/`; the valid layout overview is `v124_pr003_sheet2_layout/press_shop_pr003_v124_sheet2_oblique.png`.
- The attempted top capture is black because its camera was above the roof and is explicitly invalid evidence. The oblique and live runtime frames show two organized rows, cylindrical coils and the retained sealed-concrete floor; the wide centre lane is documented operational clearance rather than space to fill.
- Decision: **RETAIN V124 AS LATEST ISOLATED PR-003/PR-004 CHECKPOINT / SHEET 2 LAYOUT DIRECTION PASS / WHOLE PR-004 HOLD / NOT PROMOTED**. Closure: `Saved/Audits/press_shop_pr003_v124_checkpoint_closure.json`.
- Hall-finish experiments v119-v123 are preserved visual rejects and are never valid parents: v119 was too black/flat, v120 introduced circular hotspots, v121 retained hotspots, v122 still left two dominant pools and v123 was severely underexposed. Rejection record: `Saved/Audits/press_shop_pr004_hall_finish_rejections_v119_v123.json`. The valid lineage is v113 -> v116 -> v117 -> v118 -> v124; accepted PR-004 v006 remains immutable.

## PR-004 pale-silver packaged-wrap v118 checkpoint (2026-08-05, latest primary-task checkpoint)

- New isolated successor `/Game/LineBoss/Maps/LB_PressShop_PR004WrapResponseCandidate_v118` was duplicated directly from retained v117. Fifteen packaged-coil presentations receive map-local overrides on wrap, overlap, repair-patch, compressed-fibre and label slots. Geometry, authored 12-hull collision, navigation, machinery/gameplay authority and v117 remain unchanged.
- Fresh runtime close and live-carry evidence under `Saved/ValidationScreenshots/PressShopIntegration/v118_pr004_crane_runtime/` shows pale silver protective polymer, visible overlaps/patches, dark steel bands, brown compressed edge protection and readable labels. It matches the retained v005 source-render direction materially better than v117's charcoal/flat response; the v117 sealed-concrete floor survives.
- All five exact-map gates pass on v118: primary 40 t crane transfer, maintenance 30 t dispatch/return, runtime navigation, collision/navigation, and PR-004-to-PR-005 traceability handoff. Build: `Saved/Audits/press_shop_pr004_wrap_response_build_v118.json`; closure: `Saved/Audits/press_shop_pr004_v118_checkpoint_closure.json`.
- Decision: **RETAIN V118 AS LATEST ISOLATED PR-004 CHECKPOINT / PACKAGE-WRAP DIRECTION PASS / WHOLE PR-004 HOLD / NOT PROMOTED**. Remaining visual holds are repetitive/dark hall wall treatment and whole-cell lighting/material hierarchy versus the Pro references. Accepted v006 is immutable; v117 and v116 remain retained predecessors; rejected v114/v115 remain invalid parents.

## PR-004 sealed-concrete floor v117 checkpoint (2026-08-05, latest primary-task checkpoint)

- User review correctly identified that v116's floor still read as teal timber planks. Read-only inventory proved that the real base slab was covered by large thin coloured zone actors using stretched inherited floor/pillar-texture materials, including the `1900 x 6000 cm` PR-003 overlay beside PR-004.
- New isolated successor `/Game/LineBoss/Maps/LB_PressShop_PR004ConcreteFloorCandidate_v117` was duplicated directly from retained v116. It rebinds exactly 14 base/zone/pad actors to muted sealed-concrete materials. Safety-marking geometry, collisions, navigation, machinery, gameplay authority and v116 are unchanged. Build receipt: `Saved/Audits/press_shop_pr004_concrete_floor_build_v117.json`.
- Fresh runtime images `Saved/ValidationScreenshots/PressShopIntegration/v117_pr004_crane_runtime/press_shop_v117_traceability_carry_installed_context_runtime.png` and `press_shop_v117_package_condition_close_runtime.png` show a continuous subtly mottled grey factory floor with protected routes and yellow/red boundaries intact. The teal/plank read is removed.
- All five exact-map gates pass on v117: primary 40 t crane transfer, maintenance 30 t crane dispatch/return, runtime navigation, collision/navigation, and exact PR-004-to-PR-005 traceability handoff. Receipts use the corresponding `*_v117.json` filenames under `Saved/Audits/`.
- Decision: **RETAIN V117 AS LATEST ISOLATED PR-004 CHECKPOINT / FLOOR DIRECTION PASS / WHOLE PR-004 HOLD / NOT PROMOTED**. Remaining visual holds are the flat/synthetic packaged wrap, repetitive/dark hall wall treatment, and whole-cell lighting/material hierarchy versus the Pro references. Closure: `Saved/Audits/press_shop_pr004_v117_checkpoint_closure.json`.
- v116 is therefore retained as the fully gated camera-composition predecessor; v113 remains its historical gated predecessor. Rejected v114/v115 remain preserved and are never valid parents. Accepted v006 remains immutable.

## PR-004 installed carry-context v116 checkpoint (2026-08-05, latest primary-task checkpoint)

- New isolated camera-only successor: `/Game/LineBoss/Maps/LB_PressShop_PR004CarryContextCandidate_v116`, duplicated directly from retained `/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113`. Rejected visual experiments v114 and v115 are preserved but are explicitly not parents. Accepted PR-004 v006, rejected v007-v010, all machinery/material/lighting/gameplay authority and production maps remain unchanged.
- Fresh live PIE evidence: `Saved/ValidationScreenshots/PressShopIntegration/v116_pr004_crane_runtime/press_shop_v116_traceability_carry_installed_context_runtime.png`. The camera targets the authoritative carried-coil centre derived from the existing 59 cm hook-to-load offset and shows the live carried coil, trace label, C-hook, guarded route, storage buffer and destination area in installed hall context. This resolves the old black calibration void and the v114/v115 framing failures.
- Honest visual decision: **TARGETED CAMERA DIRECTION RETAIN / EXACT-MAP TECHNICAL REGATES REQUIRED / WHOLE PR-004 HOLD / NOT PROMOTED**. Packaged wrap remains pale/flat and the shared teal/plank-like floor plus whole-hall lighting remain below release quality. Review: `Saved/Audits/press_shop_pr004_carry_context_visual_review_v116.json`.
- Preparation/build receipts: `Saved/Audits/press_shop_pr004_carry_context_prepare_v116.json` and `Saved/Audits/press_shop_pr004_carry_context_candidate_v116.json`. Five exact-map validation scripts now recognize v116: primary crane, support crane, navigation PIE, collision/navigation audit and PR-004-to-PR-005 handoff. Their v116 runs are still outstanding. Resume by verifying those patches, running the five gates, capturing fresh inherited package/support views as needed, and only then deciding whether v116 supersedes v113 as the retained isolated PR-004 checkpoint.
- PR-005 `SourceAssets/Candidate/PressShop/PR005/Candidate_v002/` remains retained source-only and must not be described as integrated or promoted. Press Train A AssemblyStudyIntegration v005 is a separate technical-retain/visual-fail study. A separate control-room gameplay task was requested; inspect current repository and handoffs before assuming it produced durable changes.

## Press Train A AssemblyStudyIntegration v005 isolated Unreal study (2026-08-05, authoritative latest assembly integration review)

- First isolated UE 5.8 study of immutable `SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001` is retained at `/Game/LineBoss/Candidates/PressTrains/TrainA/AssemblyStudyIntegration_v005` with map `/Game/LineBoss/Maps/LB_PressTrainAAssemblyStudyIntegrationCandidate_v005`. Both shared packs were immutable inputs. Placement remains local and `TBC_NOT_INVENTED`; no production map/content, accepted baseline, v053, v063, v069, v107, PR-004 support identity v113, or PR-005 Candidate_v001/v002 was changed. Nothing was promoted.
- V005 reconstructs all 163 retained manifest objects from 26 shared-module FBXs plus 26 deduplicated assembly-authored local-pivot FBXs at unit actor scale. Exact bounds are `15,000 x 56,000 x 10,750 mm`, min/max `[-7,500, -5,500, 0] / [7,500, 50,500, 10,750] mm`, with positive-Y flow preserved. Fourteen candidate materials and 140 assignments validate with zero transform, mesh, material, or branding failures. Build/static receipts: `Saved/Audits/PressTrains/press_train_a_assembly_integration_build_v005.json` and `press_train_a_assembly_integration_static_v005.json`.
- Collision is intentionally presentation-safe: visual meshes are `NoCollision`; seven hidden simple stage blockers plus the walkable isolation floor carry collision. One nav-bounds volume proves authoring only; runtime navigation is not applicable because no authoritative gameplay route/world placement exists. The static performance inventory is 52 unique meshes, 179,463 unique LOD0 vertices, 74,139 unique LOD0 triangles, and approximately 400 instanced material sections. Fourteen large fixed families use Nanite; carts/dies/couplings and other prospective movers remain non-Nanite. LOD0-only and no runtime profile mean performance remains an assessment, not release proof.
- Import attempts v001-v003 are preserved rejected 1/100-scale evidence (`150 x 560 x 134.25 mm`); v004 is preserved rejected aggregate-Z evidence (`15,000 x 56,000 x 13,425 mm`). V005 resolves scale by importing dimensioned modules and derived local-pivot meshes, then rebuilding immutable manifest transforms. History: `Saved/Audits/PressTrains/press_train_a_assembly_integration_failed_scale_history_v001_v004.json`.
- Seven fresh 1920x1080 fixed-camera Unreal images and direct Pro Sheet 04/05 boards are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_assembly_integration_v005/`. The geometry direction survives, but the visual gate fails honestly: mean luminance is only `3.483–33.170/255`, `63.460%–96.592%` of pixels are below luminance 32, operator-side/mechanics cameras are occluded, S01 is clipped, and surface hierarchy/labels/utilities disappear in shadow versus the Pro references.
- Decision: **TECHNICAL RETAIN / VISUAL ITERATION REQUIRED / REJECT AS PROMOTION OR RUNTIME-PROOF CANDIDATE / NOT PROMOTED**. Retain v005 only as exact import, pivot/material, collision-authoring and performance-inventory evidence. A new versioned isolated successor must fix exposure/fill and cameras, then repeat comparison. Runtime machine authority, animation, production navigation, gameplay, clearance, timing and production-readiness claims remain false/open. Review: `Saved/Audits/PressTrains/press_train_a_assembly_integration_visual_review_v005.md` and `.json`.

## PR-005 exterior enclosure / animation-readiness source Candidate_v002 (2026-08-05, authoritative latest source-only review)

- New source-only successor: `SourceAssets/Candidate/PressShop/PR005/Candidate_v002/`. Immutable `Candidate_v001` was re-read as review authority and not modified; its manifest and Blender SHA-256 values are recorded in the v002 manifest. No Unreal map, `Content` asset, production asset, accepted baseline or runtime authority was opened or changed; nothing was imported, integrated, promoted or overwritten. `PressTrains/TrainA/AssemblyStudy_v001` and PR-004 `SupportIdentityCandidate_v113` were not touched.
- V002 directly resolves the retained v001 presentation gaps: a low guarded tunnel and large direction witness make the exact PR005-OUT-STRIP handoff readable; `Renders/05_maintenance_open_wide_v002.png` clearly shows the frame-45 access state and internal route; controlled low glazing plus render-only internal task lighting exposes separate upper/lower pinch-roll and threader-table witness modules in `Renders/04_glazing_pinch_threader_v002.png`. These witness mechanisms and motions are source-presentation geometry only; existing PR-005 runtime movers remain authoritative.
- The static shell remains `5,763 x 10,360 x 3,550 mm`. Nine modular FBXs are under `Exports/`. `PR005_EXTERIOR_ENCLOSURE_MANIFEST_v002.json`, `PR005_EXTERIOR_ENCLOSURE_DIMENSIONS_v002.csv` and `PR005_EXTERIOR_ENCLOSURE_PIVOTS_v002.csv` record exact bounds, SHA-256, provenance, pivot bases, frame 1/45/90 demonstrations and runtime-authority holds. All nine pass Blender 5.2 clean-scene round trip within the 2 mm source gate; worst aggregate dimension drift is `0.002 mm`. This is not Unreal validation.
- The dimensional records are now explicitly separated without inventing a reconciliation: `10.4 m` is the gameplay-footprint Y extent from the exact centre/half-extent record; `11.5 m` is the revised operational-plan station notation; the source shell is `10.36 m` long inside the gameplay footprint. Existing authority does not define the production relationship between 10.4 m and 11.5 m, so it remains `TBC_NOT_INVENTED` rather than selecting a new value.
- Seven fresh fixed-camera Blender renders plus `Renders/08_structured_pro_comparison_v002.png` compare the controlled glazing/process read and maintenance-open language directly with the revised PR-001-to-PR-005 operational plan and Cairnwell remaining-machinery concept. Branding is Cairnwell Automotive / Moorcross Works / PR-005 only; non-diegetic working-title text visible on Pro sheets was not copied in-world.
- Honest decision: **SOURCE TECHNICAL PASS / V001 REVIEW GAPS RESOLVED AT SOURCE-PRESENTATION LEVEL / RETAIN V002 / RELEASE-INTEGRATION HOLD / NOT IMPORTED / NOT INTEGRATED / NOT PROMOTED**. Authoritative placement, the 10.4 m/11.5 m production relationship, certified maintenance/MR-01/crane clearances, utilities, collision/navigation, interlocks, save state, live HMI, runtime mover substitution, motion/audio, Unreal materials/lighting and CCTV validation remain open. Full review: `PR005_EXTERIOR_ENCLOSURE_VISUAL_REVIEW_v002.md`.

## PR-004 30 t support-crane identity v113 (2026-08-05, authoritative latest isolated Unreal review)

- Retain `/Game/LineBoss/Maps/LB_PressShop_PR004SupportIdentityCandidate_v113` as the isolated successor to retained v109. It adds a two-sided bridge plate reading `CR-30-01 | SWL 30 t` with subordinate `CAIRNWELL AUTOMOTIVE | MAINTENANCE SUPPORT`, hangs fully below the open catwalk rail, and preserves the v109 detailed hoist. All 14 identity actors remain movable with `LB.Motion.CraneBridge` / `LB.Crane.30T`; authority, accepted v006 and production maps are unchanged.
- Fresh v113 gates pass on the exact candidate: 30 t dispatch/return (`19.0 s`, PARKED, no fault, zero 40 t/coil drift); independent 40 t coil transfer (`28.046 s`, COMPLETE, no fault, zero native follow error); valid non-partial `1396.953125 cm` navigation; collision/navigation with no failures; and traceable PR-004 to PR-005 handoff with payoff visible and 15 native mover bindings.
- Fresh runtime evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v113_pr004_support_crane_runtime/`. The management-distance fleet view proves readable equipment identity without obscuring the rail; parked and on-station close views preserve motor, gearbox, service door, rope guides and guarded C-hook readability.
- Honest decision: **retain v113 as the isolated support-crane identity successor / targeted identity and hoist visual pass / whole PR-004 hold / not promoted**. v110 is rejected for unreadable/mirrored identity, v111 for broken font-material blocks, and v112 for rail-crossed text. Final whole-cell lighting/wear and remaining PR-004 release gates stay open. Review: `Saved/Audits/press_shop_pr004_support_identity_visual_review_v113.json`.

## PR-005 exterior enclosure / animation-readiness source study v001 (2026-08-05, authoritative latest source-only review)

- New source-only candidate: `SourceAssets/Candidate/PressShop/PR005/Candidate_v001/`. The Blender master is `PR005_ExteriorEnclosureAnimationReadiness_Candidate_v001.blend`; it adds a modular externally visible enclosure, two separately pivoted service doors, external HMI/E-stop, utility interface and strip-path readability group around the existing project-owned PR-005 source context. No Unreal map, `Content` asset, production asset, accepted baseline or runtime authority was opened or changed; nothing was imported, integrated, promoted or overwritten. Accepted PR-004 v006 remains immutable, rejected v007-v010 remain rejected, and the separately owned `PressTrains/TrainA/AssemblyStudy_v001` and `PR-004/SupportIdentityCandidate_v110` scopes were not touched.
- The static shell measures `5,763 x 10,360 x 3,550 mm`. Six modular FBXs are under `Exports/`, with exact source/round-trip dimensions, SHA-256, pivots and provenance in `PR005_EXTERIOR_ENCLOSURE_MANIFEST_v001.json`, `PR005_EXTERIOR_ENCLOSURE_DIMENSIONS_v001.csv` and `PR005_EXTERIOR_ENCLOSURE_VALIDATION_v001.json`. All six pass Blender 5.2 clean-scene FBX round trip within the 2 mm source gate; worst aggregate dimension drift is 0.002 mm. This is not Unreal validation.
- The new exported geometry is project-original candidate source. The build loads 116 existing project-owned PR-005 FBXs as non-exported fit/render context, with source paths and hashes recorded. The audited Factory Environment vendor kit was rejected for hero/process-defining reuse. No vendor geometry was incorporated.
- Six fresh fixed-camera Blender renders plus `Renders/07_structured_pro_comparison_v001.png` compare the result with the revised PR-001-to-PR-005 operational plan and the remaining-machinery enclosed front-end/train concept. Exterior identity is Cairnwell Automotive / Moorcross Works / PR-005 only; working-title text visible on non-diegetic Pro sheets was not copied into the machine.
- Honest decision: **SOURCE TECHNICAL PASS / EXTERIOR DIRECTION RETAIN / RELEASE-INTEGRATION HOLD / NOT IMPORTED / NOT INTEGRATED / NOT PROMOTED**. The long low enclosure, guarded coil end, controlled glazing, service panels, readable HMI/E-stop and named moving groups are worth retaining, but source v002 must strengthen strip-outlet and maintenance-open readability, reveal more credible pinch/threader mechanism through glazing, and explicitly reconcile the `10.4 m` gameplay footprint with the `11.5 m` planning-line notation. Utility terminations plus certified maintenance, MR-01 and crane clearances remain `TBC_NOT_INVENTED`; Unreal materials, collision, navigation, interlocks, save state, HMI, motion/audio and CCTV checks remain unrun. Full decision: `PR005_EXTERIOR_ENCLOSURE_VISUAL_REVIEW_v001.md`.

## Press Train A source-only seven-stage assembly study v001 (2026-08-05, authoritative source latest)

- New independent source-only assembly: `SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v001/`. It treats `Shared/ExteriorPolishPack_v001` and `Shared/CrownToolingUtilityPack_v001` as immutable inputs and assembles a complete local-coordinate S01-S07 Train A in the proven `+Y` process direction. No Unreal map or Content was opened or changed; v053, v069, v107, accepted PR-004 v006, both shared packs and production content remain unchanged. Nothing was imported, integrated or promoted.
- The exact planning foundation and measured assembly bounds are `15,000 x 56,000 x 10,750 mm` inside the `15,000 x 56,000 x 11,350 mm` authority envelope, with min/max `[-7,500, -5,500, 0]` / `[7,500, 50,500, 10,750] mm`. Stage centres are S01-S07 at Y `0, 7,500, 15,000, 22,500, 30,000, 37,500, 45,000 mm`. Production/world placement remains `TBC_NOT_INVENTED`.
- The 163-object assembly includes enclosed S01 blank-feed/destack and S07 discharge/inspection endpoints; five heavy frames, stage-specific S02-S06 mechanics, long loaded die carts and engaged low-profile couplings; seven yellow access modules; supported hydraulic/pneumatic/electrical utility routing; and Cairnwell/Moorcross, Train A and S01-S07 identity with no Line Boss in-world wording. Source: `CA_MW_PressTrainA_AssemblyStudy_v001.blend`; FBX: `FBX/SM_CA_MW_PTA_SevenStageAssemblyStudy_v001.fbx`; transforms: `PRESS_TRAIN_A_ASSEMBLY_TRANSFORMS_v001.csv`.
- `PRESS_TRAIN_A_ASSEMBLY_STUDY_VALIDATION_v001.json` passes 11/11 checks: immutable source existence/SHA-256, inventory, transforms, finite/non-degenerate geometry, materials, exact envelope, seven-stage +Y layout, required systems, branding/TBC policy, fresh evidence and clean-scene FBX round trip. Round-trip bounds are `15,000.005 x 56,000 x 10,750 mm`, a maximum 0.005 mm aggregate drift within the 1 mm gate. Nine fresh images are under `Renders/`; boards `08_comparison_sheet04_seven_stage_v001.png` and `09_comparison_sheet05_endpoints_detail_v001.png` compare directly with Pro Sheets 04/05.
- Honest decision: **RETAIN WITH CONDITIONS as a source-only candidate for a future isolated Unreal integration study / NOT IMPORTED / NOT INTEGRATED / NOT PROMOTED**. The direction now reads as a coherent industrial seven-stage train, but remains more repetitive and less mechanically dense than the Pro authority; S01/S07 are simplified planning assemblies, loaded tooling is repeated, and collision/LOD/animation/clearance/performance/UE PBR/installed-lighting gates remain open. Review: `PRESS_TRAIN_A_ASSEMBLY_STUDY_VISUAL_REVIEW_v001.md`.

## PR-004 30 t support-hoist v109 (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressShop_PR004SupportHoistCandidate_v109` as an isolated successor to retained v108. It replaces only inherited actor `LB_INT_FRONT_30T_HoistBlock` with visual-only `SM_LB_Crane_SupportHoist_30T_Candidate_v001`; dimensions are `121.0 x 93.05 x 121.0 cm`, six controlled material families are assigned, and the original `LB.Motion.Hoist` / `LB.Crane.30T` authority tags remain on the same movable actor. Accepted v006 and production maps are unchanged.
- Fresh v109 gates pass: 30 t maintenance dispatch/return, separate 40 t master-coil transfer (`28.047 s`, COMPLETE, no fault), valid non-partial `1396.953125 cm` navigation path, collision/navigation with no failures, and traceable PR-004 to PR-005 handoff with payoff visible.
- Three fresh runtime views are in `Saved/ValidationScreenshots/PressShopIntegration/v109_pr004_support_crane_runtime/`. The targeted upper-hoist gate passes: motor, gearbox, service door, rope guides, controlled Cairnwell materials and local CR-30-01 identity replace the previous plain casing, while the support crane stays subordinate in the fleet view.
- Honest decision: **retain v109 as isolated support-hoist successor / whole PR-004 hold / not promoted**. Bridge-side identity is still too small at management distance, and final installed lighting/wear remains open. Review: `Saved/Audits/press_shop_pr004_support_hoist_visual_review_v109.json`.

## PR-004 packaged-coil condition v108 (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressShop_PR004PackageConditionCandidate_v108` as an isolated successor to proven PR-004/PR-005 handoff map v042. Accepted PR-004 integration baseline v006 and production maps remain unchanged. The candidate imports `SM_LB_MasterCoil_Candidate_v005` at 150.07 x 190.00 x 190.05 cm with 12 authored convex UCX hulls, ten semantic material slots, and replaces exactly 15 packaged-coil presentations including the native `PR004_WrappedCoilVisual`.
- Fresh v108 gates pass: real 40 t coil transfer (`28.047 s`, phase COMPLETE, no fault, 0 cm native follow error), 30 t maintenance dispatch/return (`18.875 s`, PARKED, no fault), valid non-partial `1396.953125 cm` navigation path, collision/navigation audit with no failures, and traceable PR-004 to PR-005 handoff with payoff visible. Evidence is in `Saved/Audits/press_shop_pr004_*_v108.json` plus `press_shop_pr004_package_condition_candidate_v108.json`.
- Fresh fixed-runtime views: `Saved/ValidationScreenshots/PressShopIntegration/v108_pr004_crane_runtime/press_shop_v108_package_condition_close_runtime.png` and `press_shop_v108_traceability_carry_runtime.png`. Review passes the targeted package-condition gate: restrained relief, compression/scuff variation, bands, buckles and labels now read at cradle and during the real crane carry.
- Honest decision: **retain v108 as the isolated package-condition successor / whole PR-004 release hold / not promoted**. Wrap response remains somewhat flat in current lighting, the carry view retains a black calibration void, and separate 30 t upper-hoist identity plus broader PR-005 polish gates remain open. Review: `Saved/Audits/press_shop_pr004_package_condition_visual_review_v108.json`.

## Shared Press Train crown/tooling/utility source pack v001 (2026-08-05, authoritative latest)

- New independent source-only candidate: `SourceAssets/Candidate/PressTrains/Shared/CrownToolingUtilityPack_v001/`. It contains one Blender catalog and 12 modular FBXs: mid/draw heavy crown-frame families, a cart-compatible Train A large outer-panel loaded die, five distinct S02-S06 exterior mechanical modules and four supported hydraulic/pneumatic/electrical utility-routing modules. ExteriorPolishPack_v001 was read only for the temporary loaded-cart Blender render; none of its files changed. No Unreal content or map was imported, integrated or promoted; v053, v069, v107, accepted PR-004 v006 and production content remain unchanged.
- Key measured XYZ dimensions are: mid frame `6477.999 x 5125 x 8200 mm`; draw frame `6977.998 x 5625 x 10500 mm`; loaded die `5701.701 x 2250 x 2130 mm` with documented cart-relative offset `0 x 0 x +1220 mm`; S02-S06 mechanics range from `2200 x 2140 x 1815 mm` to `2500 x 1780 x 1980 mm`; supported horizontal utilities range from `4810 x 575 x 1310 mm` to `5400 x 730 x 1730 mm`; multi-utility drop is `1090 x 1500 x 3600 mm`. Full schedule: `PRESS_TRAIN_CROWN_TOOLING_UTILITY_DIMENSIONS_v001.csv`.
- `PRESS_TRAIN_CROWN_TOOLING_UTILITY_VALIDATION_v001.json` passes all 12 source objects and all 12 independent FBX round trips with zero failures: hashes, finite/non-degenerate triangulated geometry, local-zero origins, manifest/envelope dimensions, <=2 mm round-trip tolerance, materials, TBC authority and in-world branding scan. Seven fresh Blender/comparison images are under `Renders/`; `06_comparison_sheet04_crown_mass_v001.png` and `07_comparison_sheet05_tooling_utilities_v001.png` compare directly with Pro Sheets 04/05.
- Honest decision: **SOURCE TECHNICAL PASS / COMPONENT-SCALE VISUAL DIRECTION PASS / INSTALLED-SEVEN-STAGE HOLD / NOT IMPORTED / NOT INTEGRATED / NOT PROMOTED**. Retain all 12 modules as independent source candidates; reject installed/release claims until a future isolated assembly proves frame/facade transitions, separately authored movers, fitted cart/die clearances, stage visibility, final utility terminations, installed lighting and Unreal PBR response. Review: `PRESS_TRAIN_CROWN_TOOLING_UTILITY_VISUAL_REVIEW_v001.md`. World placement remains `TBC_NOT_INVENTED`.

## Shared Press Train exterior-polish source pack v001 (2026-08-05, retained source candidate)

- New source-only candidate: `SourceAssets/Candidate/PressTrains/Shared/ExteriorPolishPack_v001/`. It contains one Blender catalog and 17 modular FBXs: a long eight-wheel die-change cart, low-profile engaged dock coupling, mid/tall enclosure exterior families, yellow access/guard module, Cairnwell Automotive / Moorcross Works identity, seven S01-S07 function plates and four separate A-D train badges. No Unreal content or map was imported, integrated or promoted; v053, v069, v107, accepted PR-004 v006 and production content remain unchanged.
- Key measured XYZ dimensions are: cart `7135 x 2802.5 x 1705 mm`; dock `2355 x 1600 x 716.011 mm`; mid enclosure `1107.5 x 5200 x 5600 mm`; tall enclosure `1207.5 x 5600 x 7600 mm`; access/guard `4770 x 3100 x 2652.5 mm`; site identity `218 x 4200 x 1050 mm`; each stage plate `188 x 1700 x 520 mm`; each A-D badge `188 x 1800 x 520 mm`. Full schedule: `PRESS_TRAIN_EXTERIOR_POLISH_DIMENSIONS_v001.csv` in the candidate root.
- `PRESS_TRAIN_EXTERIOR_POLISH_VALIDATION_v001.json` passes all 17 source objects and all 17 independent FBX round trips with zero failures: hashes, finite/non-degenerate triangulated geometry, local-zero origins, manifest/envelope dimensions, <=2 mm round-trip dimension tolerance, material slots, TBC authority and in-world branding scan. The six fresh Blender/comparison images are under `Renders/`; `05_comparison_sheet04_shared_v001.png` and `06_comparison_sheet05_train_a_v001.png` compare directly with Pro Sheets 04/05.
- Honest decision: **SOURCE TECHNICAL PASS / COMPONENT-SCALE VISUAL DIRECTION PASS / WHOLE-TRAIN RELEASE HOLD / NOT IMPORTED / NOT PROMOTED**. Retain all component families as source candidates; reject release/promotion claims until a future isolated seven-stage assembly proves loaded tooling, crown/frame integration, utility density, installed scale and final Unreal PBR response. Review: `PRESS_TRAIN_EXTERIOR_POLISH_VISUAL_REVIEW_v001.md` in the candidate root. World placement remains `TBC_NOT_INVENTED`.

## Train A v069 endpoint-direction pass / whole-train visual hold (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v069` is a direct-from-v053 isolated evidence candidate; v065-v068 remain rejected calibration/clearance history.
- v069 removes the obsolete coarse S01/S07 occluders, corrects both endpoint assemblies to positive-Y process flow, places S07 0.9 m inward to retain the 56 m envelope, and leaves the separate enclosed facades intact. Production maps are unchanged.
- Static gate passes at 187 scoped actors, 140 presentation actors, seven stages/cameras/endpoints, five warning-clean couplings, four correctly materialed access assemblies, no missing meshes/failures and exact 15,000.005 x 56,000.001 x 11,350 mm bounds. Evidence: `Saved/Audits/PressTrains/press_train_a_endpoint_clearance_static_v069.json`.
- Seven hashed fixed views in `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v069/` pass the endpoint direction/occlusion subgate against Sheet 05: blank feed/centring is visible at S01 and downstream rollers/panel staging/inspection framing are visible at S07.
- Whole-train review remains **visual hold / not promoted** because the facade massing is block-built, carts/couplings look simplified, sheet-metal process pieces lack realism, labels/HMI/wear lack depth, and installed factory lighting/scale are unproven. Review: `Saved/Audits/PressTrains/press_train_a_endpoint_clearance_visual_review_v069.json`.
- Continue the next isolated visual successor directly from v053, reusing only v069's proven endpoint direction and clearance. Production installation remains prohibited while Train A-D datums are `TBC_NOT_INVENTED`.

## Control-room standing-first operator revision (2026-08-05, authoritative latest)

- User review confirms the console screens are physically flat/correct, but the seated-first initial view is too low for the intended walk-to-screen play loop. `ALBControlRoomPawn` now starts standing at the retained approximately 1.68 m eye height with collision and bounded WASD movement enabled. `V` remains an optional chair sit/stand action and sitting is refused away from the chair.
- Camera transition now interpolates both height and the seated forward offset, avoiding the seated desk offset while standing. The editor target compiles successfully.
- The updated standing-first automation test covers default standing state, authored movement bounds, chair radius, seated translation lock and return to standing. Current unattended UE 5.8 launches crash inside NavigationSystem before the test queue begins, so this change remains runtime/visual pending and does not promote v041. The pre-existing active-CCTV VSM overflow hold remains open.

## Train A v064 endpoint-evidence static pass / visual hold (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v064` is a direct-from-v053 isolated evidence build and is not promoted.
- Exact static audit passes at 189 scoped actors, 142 presentation actors, seven cameras, four correctly yawed/yellow access modules with copied material overrides, five warning-clean v003 couplings, seven endpoints and exact retained bounds. Evidence: `Saved/Audits/PressTrains/press_train_a_endpoint_evidence_static_v064.json`.
- Seven hashed fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v064/`. Sheet 04/05 decision: **endpoint evidence failed / visual hold**. Dedicated cameras prove S01's packaged blank/feed story and S07's formed-panel/inspection/stillage story are hidden or visually weak. The repeated facade massing and die-cart/coupling treatment also remain below the Pro bar.
- Visual review: `Saved/Audits/PressTrains/press_train_a_endpoint_evidence_visual_review_v064.json`. Continue an isolated direct-from-v053 endpoint-visibility successor. Production placement into v107 remains prohibited by `Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md` until authoritative Train A-D world datums exist.

## Train A v063 industrial-readability static pass / visual hold (2026-08-05)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. v061 failed commandlet spawning and v062 failed the envelope through a wrong rotation axis; preserve both as rejected evidence.
- `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v063` is a clean direct-from-v053 rebuild. Its standalone static gate passes at 187 scoped actors, exact 15,000.005 x 56,000.001 x 11,350 mm bounds, four access modules, five v003 couplings, seven endpoints, correct authority/branding, no missing meshes and no failures.
- Fresh five-camera Sheet 04/05 review is **visual hold / not promoted**. Access silhouette is improved, but two spawned modules lack copied material overrides, S01/S07 are still weak, carts remain too toy-like and isolated context cannot establish installed scale.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v063/`; review: `Saved/Audits/PressTrains/press_train_a_industrial_readability_visual_review_v063.json`. Continue the next isolated candidate from v053. Do not place it in v107: `Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md` explicitly keeps all Train A-D production datums `TBC_NOT_INVENTED`.

## Train A v060 warning-clean coupling pass / visual hold (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v060` is an isolated direct successor; it is not promoted.
- The low-profile `DockCouplingEvidence_v003` imports with zero errors/warnings and resolves v059's tangent/binormal import failure. Exact static audit passes with 185 actors, five couplings, seven endpoint bindings, exact retained bounds and no missing assets/failures.
- Fresh Sheet 04/05 comparison evidence is under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v060/`. Decision: **technical pass / visual hold**. Coupling scale is improved, but industrial depth, restrained finish, yellow service/access structure, S01/S07 readability and installed context are below the release-quality visual bar.
- Review: `Saved/Audits/PressTrains/press_train_a_reference_finish_visual_review_v060.json`. Preserve v059 as failed import evidence and v060 as reusable coupling evidence; continue the next candidate directly from v053.

## Train A v058 reference-finish direction pass / coupling hold (2026-08-05, authoritative latest)

- `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v058` is an isolated, unpromoted direct successor of retained v053. It applies the Sheet 05 charcoal/worked-metal massing policy while preserving restrained Cairnwell and Train A identity.
- Exact static audit passes at 185 scoped actors with the verified 15,000.005 x 56,000.001 x 11,350 mm envelope, five couplings, no missing assets and no map warnings. Fresh evidence: `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v058/`.
- Visual decision against actual Press Train Sheets 04/05: **direction pass / not promoted**. The darker massing is better, but DockCouplingEvidence_v001 reads as a duplicate compact cart; yellow guarding, S01/S07 state readability and installed factory context remain open.
- Review: `Saved/Audits/PressTrains/press_train_a_reference_finish_visual_review_v058.json`. Keep v053 as baseline; redesign the coupling source and rebuild directly from v053 with the v058 material policy.

## Train A v057 coupling-fit technical pass / visual hold (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. v056 is a preserved technical failure and is not a valid parent.
- `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v057` derives directly from v053 and passes the exact static gate: 185 scoped actors, five stage-local couplings, 15,000.005 x 56,000.001 x 11,350 mm bounds, zero missing assets and zero map warnings. Audit: `Saved/Audits/PressTrains/press_train_a_dock_coupling_static_v057.json`.
- Fresh fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v057/`. Direct review against machinery-pack Press Train Sheets 04/05 is a **visual hold / not promoted**: finish is too bright/clean/green, yellow guarding is weak, carts are too compact, coupling evidence is cluttered, and S01/S07 states lack management-camera readability.
- Decision record: `Saved/Audits/PressTrains/press_train_a_dock_coupling_visual_review_v057.json`. Continue the next isolated successor from v053 and reuse only the verified v057 fit result.

## Integrated Press Shop environment v107 retained direction (2026-08-05, authoritative latest)

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107` as the latest shared-hall visual parent. Accepted station map v103 remains immutable and unchanged.
- v107 succeeds rejected v104 for operational camera composition: five cameras are below the roof/cranes and show front-end flow, crane/coil work, the connected PR-005–PR-010 line, PR-009/PR-010 cells and logistics spine. Twenty shared luminaires establish continuous ambient coverage; 42 measured 6 m slab joints remove the plank-floor read.
- Fresh evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v107_integrated_environment/`. Review: `Saved/Audits/PressShopIntegration/integrated_environment_visual_review_v107.json` = **DIRECTION PASS / WHOLE-HALL AND PRESS-TRAIN INSTALLATION HOLD / RETAINED / NOT PROMOTED**.
- v105 and v106 are preserved failed partial builds and must not become parents. v107 build audit passes with no failures: `integrated_environment_build_v107.json`.
- The remaining column forest/black upper shell cannot be honestly closed while four press trains are absent from the production map. Continue isolated Train A from retained v053, obtain authoritative Train A-D production datums, then install the trains into a new v107-derived environment successor. Do not invent world placement or run full integrated promotion gates yet.

## Control-room monitor correction, seated/standing loop and dormant PR-004 CCTV v041 (2026-08-05, authoritative latest)

- Latest retained control-room successor: `/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVDormantCandidate_v041` (**not promoted**).
- Corrected the monitor-angle basis at source. The specified 12-degree tilt is back from vertical, so Blender uses 78 degrees from horizontal. Source: `SourceAssets/ControlRoom/MainControlRoom_v034`; v041 seated evidence: `Saved/Screenshots/WindowsEditor/ControlRoomOperatorEvidence_20260805_124522.png`.
- `ALBControlRoomPawn` now starts seated but supports `V` stand/sit, a 1.68 m standing camera, collision-bounded WASD exploration, chair-proximity enforcement and exact return to the 1.30 m seated view. Runtime evidence: standing `...122347.png`, walked-back room view `...122423.png`, seated return `...122505.png`.
- CCTV workload is dormant at startup, starts through `C`/click, and stops through `Home`. The real close PR-004 feed is readable, but active capture still raises the VSM non-Nanite marking-job overflow warning. Settled Home view is clean. Do not promote until this performance gate is resolved without degrading image quality.
- Technical evidence: `Saved/Automation/ControlRoom_v041/index.json` (3/3 success, 0 warnings); visual decision: `Saved/Audits/ControlRoom/main_control_room_seated_standing_cctv_visual_review_v041.json`.
- v032/v033 monitor basis, v036 initial black capsule obstruction and v037-v039 CCTV exposure/shadow candidates remain rejected evidence.

## Control-room authored seated view / upright live-CCTV work v032 (2026-08-05, authoritative latest)

- Continue from unpromoted `/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveCCTVAuthoredSeatCandidate_v032` when returning to the control room. It inherits v018's corrected `+12` degree monitor meshes, restores the source-authored fixed seated camera, and owns a real selected PR-004 SceneCapture feed on an upright wall surface.
- Fresh actual-game evidence `Saved/Screenshots/WindowsEditor/HighresScreenshot00026.png` passes monitor orientation; visual review is `Saved/Audits/ControlRoom/main_control_room_authored_seat_visual_review_v032.json`. The screens aim down/front at the operator rather than toward the ceiling.
- v030 and v031 remain rejected composition history. v032 remains **not promoted** because selected-feed zoom/readability, foreground cleanup, performance and the full Pro-reference gate are still open. Technical build: `Saved/Audits/ControlRoom/main_control_room_pr004_live_cctv_authored_seat_build_v032.json`.

## Control-room monitor face-normal correction v018 / PR-004 v019 (2026-08-05, authoritative latest)

- User inspection proved v008 still leaned the monitor faces toward the ceiling. The visible source-mesh face is local `-Y`, so the previous negative-sign conclusion was wrong.
- Preserve v006/v008 as rejected evidence. Continue physical orientation work from `/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCorrectedCandidate_v018`, which replaces only `Interaction` and `State_Mothballed` with the preserved v005 `+12` degree meshes. Their visible faces aim down/front toward the seated 1.12 m operator eye after Unreal conversion.
- Technical audit: `Saved/Audits/ControlRoom/main_control_room_operator_aim_corrected_build_v018.json`. Fresh centered actual-game evidence: `Saved/Screenshots/WindowsEditor/HighresScreenshot00014.png`. Visual review: `Saved/Audits/ControlRoom/main_control_room_operator_aim_visual_review_v018.json`.
- v018 passes the physical monitor-orientation sub-gate only and is **not promoted**.
- The PR-004 WidgetComponent checkerboard cause was confirmed by the older station implementation: it hides the unreliable render target and presents live state through deterministic TextRender components. `ALBControlRoomPR004Console` now uses the same pattern while retaining the real widget as its authority/interaction host; the editor target compiles successfully.
- Fresh `/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v019` mounts that authority-backed console on v018. Technical build passes. Fresh actual-game close views `HighresScreenshot00015.png` and `HighresScreenshot00016.png` prove the checkerboard is gone and live PR-004 authority text is visible, correctly oriented and flush; review is `Saved/Audits/ControlRoom/main_control_room_pr004_console_visual_review_v019.json`. Pointer action, state mutation, save/authority and final foreground-occlusion gates remain open.
- Retained successor `/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v020` adds a dedicated invisible visibility-channel screen hit surface. `ALBControlRoomPawn` routes that hit to the console's guarded PR-004 action. `Saved/Automation/ControlRoom_v020/index.json` passes both control-room tests with zero warnings and proves the trace target, packaged-to-unpackaged authority mutation, Press Shop save-root memory serialization, and restore into a fresh station. Actual runtime before/after evidence is `HighresScreenshot00016.png` / `HighresScreenshot00017.png`; the latter visibly reads `COIL UNPACKAGED`. Review: `Saved/Audits/ControlRoom/main_control_room_pr004_pointer_save_runtime_review_v020.json`.
- v020 is **not promoted**. Final selected-screen composition remains obstructed by a foreground lever, and the required real selected Press Shop CCTV feed plus full fixed-camera Pro comparison remain open.

Updated: 2026-08-05

## Current decision

This is the clean, parallel Unreal 5.8 implementation requested by the user.
It is deliberately outside OneDrive at:

`C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8`

Unreal created this folder when the user selected **Open a copy** during the
5.8 conversion prompt. This is the authoritative Unreal working project.

The existing Godot project at
`C:\Users\greg_\Projects\car factoy mayhem` remains intact and is the source
of proven gameplay, measurements, Blender sources and comparison evidence.
Do not delete it or overwrite it during the Unreal evaluation.

## Authoritative product direction

- PC-first, detailed 3D factory-management game.
- Initial campaign: **The Restart — Press Shop**.
- Fixed Press Shop footprint: 220 m east-west by 120 m north-south.
- The player is the Line Boss: management decisions plus selective close-control
  interaction through real machine HMI cabinets.
- Near-future automation must remain recognisable and industrial, not science
  fiction.
- The shop is recommissioned from a mothballed state and progresses from dark,
  isolated equipment to certified production.
- The initial product family is the modular Rebuild U-Series light-commercial
  platform; Press works in batches while later shops support increasing mixed-
  model flexibility.
- The proposal source is
  `C:\Users\greg_\Downloads\LINE_BOSS_CAR_FACTORY_FULL_GAME_PROPOSAL_PRESS_SHOP_v1.0.docx`.

## Completed Unreal foundation

- Project: `LineBossCarFactory.uproject` (Unreal 5.8, Blueprint-first).
- Startup map: `/Game/LineBoss/Maps/LB_PressShop_Foundation`.
- Script: `Scripts/build_press_shop_foundation.py`.
- Layout data: `Content/LineBoss/Data/press_shop_layout_v001.json`.
- The saved foundation contains 112 actors: finished floor, seven functional
  zone slabs, four perimeter walls, an 11-by-8 structural column grid, eight
  roof beams, material-flow datum, directional fill and two validation cameras.
- Cameras:
  - `LB_CAM_PressShop_ManagementOverview`
  - `LB_CAM_PressShop_TopDown`
- The foundation successfully opened and built in the desktop Unreal 5.8 editor.

## Asset-production boundary

Do not copy the rejected exploded PR-005 Unreal parity scene into this project.
Its imported GLB hierarchy did not reconstruct the Blender assemblies correctly.

Re-export custom assets one at a time from their Blender sources, beginning with
the shared HMI cabinet. Each asset must preserve dimensions, pivots, meaningful
moving subassemblies and material slots. Validate it against fixed Blender
reference views before promotion.

Free/vendor packs may supply the building shell, lamps, fences, generic platforms,
electrical cabinets, fire equipment, pallets and background dressing. They must
not replace Line Boss hero equipment: the HMI cabinet, PR-004 crane/C-hook, coils
or primary process machinery.

The UE5.8 read-only pack audit is at:
`C:\Users\greg_\Projects\car factoy mayhem\prototypes\unreal\pr005_renderer_ab\Saved\Audits\factory-pack-ue58-load-audit.json`

## Next work

1. Reopen the project and confirm the foundation startup map and 112 actors.
2. Capture management and top-down fixed-camera evidence.
3. Establish `/Game/LineBoss` folders for Core, Stations, Shared, UI, Data,
   Materials, Maps and Developer validation assets.
4. Export and import the shared HMI cabinet cleanly from Blender; do not rebuild
   it as loose primitives in Unreal.
5. Validate cabinet silhouette, downward-facing screen angle, physical controls,
   rear service door and scale before beginning PR-005 machinery.
6. Build PR-005 as modular moving assemblies and only then compare Unreal with
   the accepted Blender reference.

## 2026-08-01 shared HMI A/B result

Two unpromoted HMI candidates now exist for evidence-based workflow selection:

- Blender/CAD-led v004, imported as 33 semantic single-material modules at
  `/Game/LineBoss/Shared/HMI/IND_HMI_001_V004_Modeling003`.
- Fully Unreal-native v005, built as 63 separate primitive components in
  `/Game/LineBoss/Developer/Validation/LB_HMI05_UnrealNativeValidation`.

The v005 native candidate is dimensionally correct (600 x 460 x 1280 mm cabinet,
1590 mm overall, 340 x 255 mm 4:3 screen at 20 degrees) and is easier to select,
move and animate. It is not visually better: its hero silhouette, folded shell,
bevels, hood, door and small fittings are more blocky than Blender v004. The
approved production boundary is therefore Blender/CAD for hero geometry plus
Unreal for modular assembly, material authoring, collision, interaction and
animation. Neither candidate has been promoted.

Scripts and evidence:

- `Scripts/build_hmi_v005_unreal_native.py`
- `Scripts/audit_hmi_v005_materials.py`
- `Scripts/prepare_hmi_v005_validation_materials.py`
- `Scripts/capture_hmi_v005_unreal_native.py`
- `Saved/Audits/shared_hmi_v005_unreal_native.json`
- `Saved/Audits/shared_hmi_v005_material_bindings.json`
- `Saved/ValidationScreenshots/HMI/`

The material-binding audit confirms that all 63 native components point at the
intended material assets and material graph inputs validate. However, unattended
SceneCapture currently renders those assets as fallback grid/invalid exposure,
including saved validation instances. Treat that as a capture-pipeline blocker,
not acceptable visual evidence. Do not promote either candidate from those
frames.

## Safety

- No OneDrive project paths.
- The earlier seed at `C:\Users\greg_\Projects\LineBossCarFactory_Unreal` was
  superseded by this 5.8 copy and deleted on 2026-08-01 after the HMI scripts
  and audit evidence were hash-verified in this project.
- Preserve the Godot project and unrelated user files.
- Do not bulk-migrate the 9.35 GB vendor project.
- Do not promote assets merely because they import or compile.
- Do not commit unless the user explicitly requests it.

## 2026-08-01 production-engine decision

The user has now selected Unreal Engine 5.8 as the production target for the
full game. The Godot project remains an untouched reference/fallback and must
not be deleted. Continue using the established hybrid asset workflow:

1. dimensioned CAD/CadQuery or FreeCAD core where measurements matter;
2. Blender finishing for hero silhouette, bevels, pipework, wear and UV work;
3. semantic FBX modules with mover-safe pivots;
4. Unreal assembly, materials, collision, animation and gameplay;
5. fixed-camera evidence before promotion.

## 2026-08-01 PR-005 modular Unreal vertical slice

PR-005 has been exported from the existing Blender candidate as 13 module
manifests and imported at:

`/Game/LineBoss/Stations/Press/PR005/Candidate_v001`

The candidate contains 59 static-mesh assets, including 47 independently
addressable moving groups, with 140 material slots. The post-import audit now
reports zero missing slots and zero `WorldGridMaterial` fallbacks. The first
eight-second operational proof animates 25 relevant actors (mandrel/coil,
pinch and table rollers, strip witness, keeper/snubber, peeler and crop shear):

`/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Sequences/LS_PR005_OperationalCycle_v001`

Validation level:

`/Game/LineBoss/Developer/Validation/LB_PR005_ModularValidation`

Evidence:

- `Saved/ValidationScreenshots/PR005/pr005_unreal_overview_v001.png`
- `Saved/ValidationScreenshots/PR005/pr005_unreal_process_v001.png`
- `Saved/ValidationScreenshots/PR005/pr005_unreal_top_v001.png`
- `Saved/Audits/pr005_modular_unreal_import_v001.json`
- `Saved/Audits/pr005_unreal_materials_v001.json`

Status remains **candidate / not promoted**. The modular import and animation
pipeline is proven, but visual polish, factory-context lighting, collision,
interactive HMI logic and a gameplay-driven station state machine remain.

## Current toolchain blocker

Unreal editor/Python work is operational. Native C++ gameplay compilation is
currently blocked because Unreal 5.8 reports the Windows SDK as unavailable
(`Required version 10.0.19041.0`; detected 10.0.22621.0 is marked invalid).
The staged `Source/LineBossCarFactory` code is therefore not registered in the
`.uproject` yet. Do not re-enable the module until a compatible Windows SDK and
the required Visual Studio C++ components are installed. Blueprint/editor-side
content work can continue in the meantime.

## 2026-08-01 PR-005 gameplay contract and anchors

The PR-005 candidate now has an authoritative gameplay contract at
`SourceAssets/PR005/pr005_gameplay_contract_v001.json`. The validation level has
21 engine-native port, interaction and volume actors. All 59 PR-005 candidate
meshes are tagged, including 35 state-driven moving groups. The contract audit
passes for three material ports, seven interactions and thirteen commissioning
conditions. This establishes stable gameplay identities without coupling code
to actor labels.

Evidence:

- `Saved/Audits/pr005_gameplay_markers_v001.json`
- `Saved/Audits/pr005_gameplay_contract_audit_v001.json`

The richer native PR-005 controller is staged in
`Source/LineBossCarFactory/LBPR005Station.h/.cpp`, but remains uncompiled until
the Windows/Visual Studio C++ toolchain blocker is resolved. Do not claim runtime
gameplay integration yet.

## 2026-08-01 curated vendor kit and audio decision

A selective Factory Environment shortlist is now contained at
`/Game/LineBoss/Vendor/FactoryEnvironment`. It contains 15 reusable support
meshes plus dependencies, not the complete 8.71 GB pack. Fixed-camera review
accepts the geometry for background/support use at normal gameplay distance;
it is not suitable for hero process machinery. All 15 meshes have at least one
simple collision primitive. The validated screenshot is:

`Saved/ValidationScreenshots/Vendor/factory_environment_shortlist_v001.png`

Six audio assets were also isolated under the vendor Audio folder as candidates.
They may provide distant factory, motor and ventilation beds after listening
tests. PR-005 machine actions will be custom and state-driven according to
`SourceAssets/PR005/pr005_audio_contract_v001.json`.

Full policy and evidence: `Docs/VENDOR_ASSET_AUDIT_2026-08-01.md`.

## 2026-08-01 opening campaign: power unlocks the first coil

The opening production sequence is now fixed. Essential power and safety-system
recovery is the prerequisite, but the first operational objective is then to
receive and load the test coil. That same identified coil provides the visible
material thread through PR-001 receipt, PR-002 inspection/weighing, PR-003
storage, PR-004 packaging removal/transfer and PR-005 loading. Automatic strip
preparation is unlocked only after the verified coil is on the mandrel, guarding
and interlocks are healthy, threading and dry cycle succeed, and first strip is
approved.

Authoritative campaign data:

`Content/LineBoss/Data/restart_campaign_v001.json`

Do not turn initial power recovery into a long electrical-repair minigame. It is
a short strategic commissioning gate that makes the arrival of the first coil
the player's first major production event.

## 2026-08-01 PR-005 audio candidates

Twelve original 48 kHz stereo sound candidates were generated for PR-005. They
cover HPU idle, coil-car start/travel/stop, mandrel expansion, keeper-arm
engagement, roller drive, continuous strip motion, gate interlock, warning alarm,
controlled stop and emergency stop. Source and Unreal import audits pass for
format, duration, clipping, DC offset and loop-boundary quality.

Sources:

`SourceAssets/Audio/PR005/Candidate_v001`

Imported candidate assets:

`/Game/LineBoss/Stations/Press/PR005/Candidate_v001/Audio`

Evidence:

- `Saved/Audits/pr005_audio_source_quality_v001.json`
- `Saved/Audits/pr005_audio_import_v001.json`

Status remains **candidate / not promoted** until listening review and in-engine
state/attenuation testing. Vendor audio is restricted to low-level hall/HVAC
ambience; recognisable PR-005 actions use the original synchronized layers.

## 2026-08-01 front-end guarding and master-coil decision

The opaque vendor fence was rejected for production use. A reusable Line Boss
open-mesh machine-guarding candidate now provides a 2 m welded-wire panel,
1.5 m bolted post, hinged 1.2 m interlocked gate and separate coded interlock
box. The user explicitly approved the yellow-framed open-mesh appearance on
2026-08-01, so this is the visual language to retain and extend around later
Press Shop machinery. Do not replace it with opaque wall-like fencing.

Source and importer:

- `SourceAssets/IndustrialKit/SafetyBarrier`
- `Scripts/import_safety_barrier_kit.py`

Imported candidate root:

`/Game/LineBoss/IndustrialKit/Safety/Barrier`

The current 25--30 t packaged master-coil candidate was also rebuilt with
consistent outward normals and an explicit opaque-material contract. Fresh
lit Unreal captures now show solid coil bodies rather than the earlier
see-through fault. Its very clean white wrap and simplified finish still need
release-quality surface work; opacity correction alone is not promotion.

Evidence:

- `Saved/Audits/safety_barrier_kit_candidate_v001.json`
- `Saved/Audits/master_coil_candidate_v002.json`
- `Saved/ValidationScreenshots/PressShopIntegration/press_shop_pr001_pr002_v001.png`
- `Saved/ValidationScreenshots/PressShopIntegration/press_shop_coil_store_crane_v001.png`

The populated PR-001--PR-004 integration level remains **candidate / not
promoted**. It currently contains 15 visual coils, the exact twelve-position
PR-003 store, two modular overhead cranes and the approved guarding language.
Fixed-camera review exposed over-dark shell lighting and weak crane/PR-004
detail framing, which must be corrected before any front-end promotion.

## 2026-08-01 authoritative front-end layout and first-coil automation contract

The Press Shop master-plan anchors are now recorded at
`Content/LineBoss/Data/press_shop_master_plan_anchors_v001.json`. The Unreal
transform preserves the 220 m x 120 m building, maps material flow to world +X
and keeps PR-004 at source coordinate (80,000, 59,500, 0) mm / Unreal world
(-5,050, -2,000, 0) cm. PR-003 is fixed as twelve positions arranged three
along material flow by four across; do not rotate it back to a 4 x 3 layout.

The latest integration candidate is
`/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002`. Its front-end
audit records 155 open-mesh panels and 174 real bolted posts, plus four gates,
fifteen coils, twelve PR-003 slots and two cranes. It remains **candidate / not
promoted**. The Unreal 5.8-safe build workflow uses three separate processes:
foundation build, `prepare_press_shop_integration_candidate.py`, then
`build_press_shop_integration_candidate.py`. Combining duplication and
population in one editor process previously caused a world-duplication crash.

The first identified coil's authoritative state and interlock contract is
`Content/LineBoss/Data/first_coil_automation_v001.json`. It requires a visible,
non-teleporting material chain from packaged storage through crane transfer,
PR-004 depackaging and PR-005 commissioning. Level Sequences may present
motion, but the planned `BP_LB_FirstCoilFlowController` must own cross-station
gameplay state. PR-004 now has a source-level controller and shared-cabinet HMI
contract, but neither has compiled or run in Unreal and the cross-station flow
controller, UMG screens and production SaveGame integration remain unimplemented.

## 2026-08-01 PR-004 robotic depackaging design lock

The user supplied four coordinated PR-004 design sheets and then a fifth,
consolidated **PR-004A Realistic Robotic Coil Destrapping + Dewrapping Cell**
sheet. The consolidated sheet is preserved at
`Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004A_Realistic_Robotic_Coil_Destrapping_Dewrapping_Cell_v002.jpg`
and is now the whole-cell integration authority. It fixes the existing 14.4 m
across-flow x 12.4 m along-flow envelope, 2.4 m open-mesh fence, estimated
4.5 m maximum equipment height, facility anchor X=80,000 mm / Y=59,500 mm /
Z=0, two-stage process, equipment placement, interlocks, fault set and Unreal
module split. The earlier compact primary and supporting sheets remain detail
authorities only where they do not conflict with PR-004A or the master-plan
anchors. The concept's local axes must be rotated into the canonical facility
axes: source Y is material flow and Unreal +X. The 24.4 m x 14.4 m alternate
remains explicitly rejected because it overlaps the established PR-003 and
PR-005 spacing; do not resize the master plan to make that alternate fit.
The two new reference files, their SHA-256 hashes, normalized values and NTS
limitations are recorded in
`Saved/Audits/pr004_design_sheet_intake_revA.json`. This is a reference-intake
gate only and is not evidence that any source or Unreal asset is promoted.

The normalized cell contract is
`Content/LineBoss/Data/pr004_robotic_depack_cell_v001.json`. It fixes the
existing PR-004 anchor and specifies a guarded six-axis industrial robot (never
an android or humanoid), powered restrained V-cradle, controlled band capture
before cutting, tool changing, wrap and edge-protector removal, separated waste,
camera/RFID inspection and player quality disposition. The 610 mm bore, 1.8--
2.1 m outside diameter and maximum 1.55 m width envelope matches the new master
coil v003 candidate. The robot, tools, powered cradle motions, inspection gantry,
and controller are still missing from runtime, so this is a **design lock, not
a promoted station**. Source-only candidates now exist for the modular powered
cradle and for a runtime-separable packaged coil, but neither has entered the
Unreal promotion path.

The non-mutating fit audit is
`Saved/Audits/pr004_pr005_clearance_v001.json`. A cell envelope centred on the
PR-004 anchor overlaps the conservative PR-005 gameplay envelope by 90 cm and
the imported PR-005 floor-zone mesh by 28.25 cm. The actual PR-005 machine mesh
has 73 cm clearance, still 47 cm short of the audit's 120 cm assumption. A
future local PR-004 child-envelope offset of 210--232 cm west appears feasible
without moving any station anchor; a balanced 221 cm offset estimates 131 cm
clearance on each side. This is an unapplied candidate solution only. Do not
apply it until the final robot, tools, inspection equipment, gates and crane
swept bounds are present and audited together.

The powered restrained cradle source candidate is under
`SourceAssets/PR004/PoweredRestrainedCradle/`, with five separate FBXs for the
fixed body, two side clamps, index drive and end-stop locator. Its independent
FBX re-import audit and fixed-camera source renders are recorded at
`Saved/Audits/pr004_powered_cradle_candidate_v001_fbx_validation.json` and
`Saved/ValidationRenders/PR004/PoweredCradle_v001/`. These source gates pass,
but there is no Unreal collision, animation, interlock or visual-comparison
gate yet, so promotion is forbidden. On 2026-08-01 the user explicitly approved
the cradle's visual direction as "brilliant". Preserve its proportions and
industrial detail density as the PR-004 benchmark; this is visual-direction
approval, not runtime promotion.

The persistent-coil packaging source rig is under
`SourceAssets/PR004/PackagingRig/`. It separates one bare coil from sixteen
opaque wrap sections, four identified bands plus eight captured cut-state tails,
eight edge protectors, label/RFID children and a short Unreal SplineMesh source
profile. All 40 exported FBXs passed the independent Blender 5.2 re-import gate
recorded in
`Saved/Audits/pr004_packaging_rig_candidate_v001_fbx_validation.json`, including
manifest bounds, pivots, rotation, unit scale, IDs, metadata and opaque-material
checks. This is a source gate only; the Unreal state transition, visible spline
withdrawal, waste-bin entry and save/load persistence remain unimplemented and
unvalidated, so the packaging candidate is not promoted. The user
clarified the correct steel-band behaviour: an uncut band is tensioned around
the coil; after both ends are controlled and it is snipped, it loses the closed
loop but retains sharp set-bends at the former coil-edge and bore transitions.
The cut band must therefore use a segmented flexible spline with kink control
points and restrained recoil and be visibly pulled clear by the robot
withdrawal tool. The user then chose a guarded powered waste-conditioning
route: the same kinked band feeds through straightening rollers, winds
progressively into a compact flat pancake coil, has its tail restrained and is
visibly ejected into the steel-band bin. The source band bit cannot clear before
that ejection acknowledgement, and each compact coil retains its source-band ID
in the waste log. A rigid cut hoop, smooth rope, instant disappearance or
already-perfect coil is incorrect.

Recovered plastic follows a separate two-process route. The robot uses the T5
film start-tab cutter/clamp only to locate the seam, make a controlled opening
and hand the tracked tab to the T6 powered dewrapper. It must then retreat to a
confirmed clear pose. A dedicated collapsible spindle winds the dull opaque-grey
film or paper while the restrained cradle indexes slowly in electronic
synchronisation; a dancer arm, load cell and tear camera supervise continuity
and tension. The wound material is stripped into a guarded transfer and
compactor, becomes one dense irregular bale rather than a neat roll, and is
visibly ejected into the plastic-only bin. Torn fragments remain individually
tracked and require trapped-key manual recovery rather than being silently
cleared. The governing module contract is
`Content/LineBoss/Data/pr004_film_dewrap_spindle_v001.json`. The dedicated Pro
sheet has now been received and preserved at
`Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004_Powered_Coil_Wrap_Dewinding_Compaction_Module_RevA.jpg`.
It is drawing `PR-004-DS-001`, revision A, dated 2025-05-17. It confirms the
fixed 14.4 m x 12.4 m cell and facility anchor, 4.5 m maximum operating height,
1.0 m robot-rear and spindle/compactor service clearances, 1.2 m electrical
cabinet front clearance, 1.4 m gates and 1.5 m crane pick/drop exclusion. Its
mechanical lock includes an 80 mm tab-clamp stroke, 400--1,000 mm hydraulic
spindle expansion, continuously variable spindle rotation up to 120 RPM,
-60 to +60 degree dancer travel, a 600 mm / approximately 60 kN compactor ram
and an estimated 3.5--5.0 minute cycle per coil. The sheet is NTS and does not
publish every isolated base footprint or pivot coordinate, so final source
geometry remains parametric and must pass complete robot/cradle/spindle swept
bounds; do not infer missing dimensions by measuring pixels.

The sheet's plan-view direction required a separate plant-level check. The
read-only comparison at `Saved/Audits/pr004_footprint_orientation_v001.json`
locks the existing 12.4 m dimension along Unreal +X material flow and 14.4 m
across world Y. A literal 14.4 m flow interpretation is 178 cm too long to
preserve two 120 cm audit margins between the fixed PR-003 and PR-005 contract
envelopes; centred, it overlaps the PR-005 contract by 190 cm, its floor zone
by 128.25 cm and physical equipment by 27 cm. Retain the sheet's process
topology, but normalize its internal arrangement to the authoritative master
plan rather than copying NTS pixels. No anchor or level actor was moved. The
selected 12.4 m flow envelope still needs the previously identified 210--232 cm
westward child-geometry rebase, fence review and complete swept bounds; this is
an orientation decision, not a clearance pass.

The first modular film-dewrapper source rig now exists under
`SourceAssets/PR004/FilmDewrapSpindle/`. It contains eleven separately exported
modules: fixed machine and guards plus the tab clamp, spindle expander, rotor,
dancer arm, dancer roller, stripper, transfer gate, compactor ram and bale
discharge. The builder now bakes inherited Euler/quaternion rotation and scale
into each mesh before setting its true origin pivot, so every FBX imports at
identity and the manifest supplies only the assembly rest transform. The
independent audit at
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v001_independent.json` passes
the clean-FBX technical gate for all eleven modules but fails the release visual
gate. The housings remain broad, clean and toy-like, the isolated wrap strip is
bright white and too perfect, no dancer/tension fault state is demonstrated,
and the compactor view does not show an irregular bale positively discharged
into the plastic-only bin. Keep v001 as a rig/pivot prototype only; it has not
been imported into Unreal and must not be promoted.

The band winder and plastic path have explicit health interlocks, jam/ejection
faults, HMI recovery actions and saveable waste counts in
`pr004_robotic_depack_cell_v001.json`, `first_coil_automation_v001.json` and the
PR-004 controller source. The first modular waste-conditioning source candidate
now exists under `SourceAssets/PR004/WasteConditioningSkid/`. It exports fourteen
source modules, including independently controllable band rollers, straightener,
winder, clip head, ejectors, gates, plastic nip, compactor ram and a separate
open-mesh guard module. Its steel-band bin is correctly south of the winding
mandrel and its plastic-only bin is east of the compactor, with physically
separate open chutes. The source self-audit is
`Saved/Audits/pr004_waste_conditioning_skid_candidate_v001_source.json`.
This remains functional-rough source only: the obsolete direct robot-to-nip
plastic lane must be revised around the dedicated spindle, its materials and
mechanical detail are below the cradle benchmark, and no independent FBX or
Unreal runtime/visual gate has passed. Do not promote or permanently import it.

The real-machine basis is recorded from the official Signode RCU robotic metal
coil destrapper and ACU-CH3M automatic strap cutter, both of which positively
capture/cut and condition removed banding while the cradle carries the coil, and
from the MSK Defotech unwrapper, which supports the separate powered film-winding
and recycling principle. References:
`https://www.signode.com/en-gb/productslist/rcu/`,
`https://www.signode.com/en-au/news/signode-unveils-automatic-strap-cutting-unit-for-s/`
and `https://www.mskcovertech.com/solutions/unwrapping-systems/unwrapper/`.
These links are design evidence only, not licensed game assets.

Independent visual review rejected packaging v001 for permanent integration
despite its passing source audit: the partial-removal pose behaves like rigid
petals, the wrap is too uniform and razor-edged, the closed bands stand away as
square frames, the bare coil reads as a solid spool, and the edge protectors and
label are too simple. Preserve v001 only as a technical pipeline test. A visual
replacement was built under `SourceAssets/PR004/PackagingRig_v002/`, but its
independent audit at
`Saved/Audits/pr004_packaging_rig_candidate_v002_independent_fbx_visual_audit.json`
also fails the visual gate despite all 43 FBXs re-importing cleanly. Its wrap
reads as near-white felt instead of dull grey industrial film; the dark
face/bore and bright speckled barrel do not read as one coherent oiled-steel
coil; the plastic bale remains too cuboid and cloth-like; protectors, clips and
labels are too clean; and neither a guarded winder/bin drop nor the revised
spindle/compactor/bin path is demonstrated. Retain only the flexible peel
direction, controlled kinked band path and compact clipped band-pancake
silhouette. Neither packaging version may be used by the permanent PR-004
level; v003 must follow PR-004A and the received `PR-004-DS-001` revision A
powered dewinding/compaction module sheet.

The modular depackaging robot v002 is under
`SourceAssets/PR004/RoboticDepackRobot/`. It exports 28 FBXs, including J1--J6,
four tool bodies and 11 independently animatable tool movers. The independent
audit at `Saved/Audits/pr004_robot_candidate_v002_fbx_validation.json` passes
25/25 source checks and preserves the declared reach, axes, limits and child
pivots. v002 retires v001 from further integration. It is suitable for an
isolated Unreal hierarchy/animation test, but its broad housings and source
materials remain cleaner and more CAD-like than the powered-cradle benchmark.
It is not level-integration or promotion ready until shared materials/LODs,
release PBR finish, deforming dress pack, swept collision, tool changes,
interlocks and fresh in-cell cameras pass.

A fresh read-only Unreal promotion-state audit at
`Saved/Audits/pr004_unreal_promotion_state_v001.json` confirms that none of the
PR-004 hero families has been imported or promoted. The permanent station and
developer-validation destinations do not exist; cradle v001, robot v002,
rejected packaging v002, the waste-conditioning skid and the new film spindle
remain source-only. The current integration map therefore still uses generic
coil-saddle, master-coil, prep-bench and recovery-bin placeholders. This clean
boundary must be preserved until the footprint/swept-bound decision, isolated
import/runtime gates and fixed-camera visual review all pass.

The local Factory Environment Collection has been audited as a selective donor,
not as an automatic replacement for the custom hero robot. Its large rigged
`SK_IndustrialRobot` and smaller IK/FABRIK robot are suitable only for an
isolated comparison or as technical references; neither has the PR-004 reach,
tool-change, process hierarchy or proven UE 5.8 shipping suitability. Useful
licensed-content candidates include fixed cable bundles, motors, panels,
cameras, junction boxes, decals and background dressing. There is no suitable
moving drag chain or robot dress pack, and vendor UV-specific robot textures
must not be applied to the custom mesh. Verify Fab entitlement terms and run
conversion/render gates before shipping any vendor content. Preserve the
approved Line Boss barrier kit where it is already stronger.

The data-driven PR-004 controller at
`Source/LineBossCarFactory/LBPR004Station.h/.cpp` was reconciled on 2026-08-01:
the former simplified `.cpp` no longer conflicted with the newer v3 header. It
preserves one coil identity, tracks four bands, eight protectors and sixteen
wrap sections with saveable bitmasks, and requests a visible action before any
source bit can clear. Each band requires positive capture, detachment,
conditioning, compact winding and visible bin ejection. Each wrap section
requires controlled tab handoff, robot-clear confirmation, synchronized
cradle/spindle indexing, tensioned wind and guarded transfer; the final section
also requires compaction and visible irregular-bale ejection. Both film drives
stop together on tension, synchronization or robot-clear loss. Waste records
are idempotent, power loss requires explicit in-flight material ownership,
torn/trapped film requires zero-motion trapped-key recovery with every fragment
ID accounted for, quality disposition is human-controlled, and handoff/reject
transactions retain the same coil identity.

The strict v2 source/data audit at
`Saved/Audits/pr004_controller_contract_v001_source.json` now passes declaration
/ definition parity, all 18 scenario-visible source invariants and exhaustive
write/restore coverage for all 61 fields in `FLBPR004SaveState`. This is still
not a compile or runtime pass. The first Unreal 5.8 build attempt did not reach
UHT or the compiler because this PC has Visual Studio Code but no MSVC Build
Tools or Windows SDK; exact evidence remains in
`Saved/Audits/pr004_controller_cpp_compile_v001.json`. Do not claim the
controller compiles until a supported SDK/toolchain is installed and the target
is rebuilt.

The corresponding shared-cabinet workflow is locked in
`Content/LineBoss/Data/pr004_hmi_controller_contract_v001.json`. It defines ten
PR-004 pages, the downward-facing 17-inch 4:3 screen, physical control mapping,
13-step process display, read-only safety page, all controller calls/events,
complete fault grouping, guided trapped-key recovery and the rule that the HMI
can never clear material or increment waste directly. Its binding audit at
`Saved/Audits/pr004_hmi_controller_contract_v001_source.json` passes against the
header. No UMG widget or runtime binding exists yet, so this is an interface
contract rather than a promoted console implementation.

The required PR-004 gameplay and persistence scenarios are locked in
`Content/LineBoss/Data/pr004_controller_test_matrix_v001.json`. It includes 18
tests covering cold start, identity mismatch, crane/robot exclusion, visible
band winding/ejection, robot-to-spindle handoff, synchronized cradle/spindle
indexing, dancer/tension/synchronisation faults, guarded compaction/ejection,
trapped-key torn-wrap recovery with complete fragment accounting,
non-duplicating recovery, separated waste permissives, quality hold/release,
partial-mask and waste-count save/restore, and same-actor handoff. The matrix is
authoritative but not yet executable while the
C++ toolchain and Unreal bindings are absent.

The PR-004 fit review exposed a pre-existing PR-005 orientation error. The
modular PR-005 geometry and gameplay contract travel along Unreal-local +Y, so
the station placement is now yaw -90 degrees, mapping that direction onto
facility world +X. The former +90-degree placement put the strip output toward
PR-004. `build_press_shop_integration_candidate.py` now calculates the gameplay
ports in world space and refuses to build unless the coil input is west of the
anchor and the strip output is east. This correction still requires fresh
integration screenshots and therefore does not promote PR-005.

## 2026-08-01 — PR-004 film-dewrapper v004 independent source decision

The fourth film-dewrapper source iteration is preserved under
`SourceAssets/PR004/FilmDewrapSpindle_v004/`. Its builder now corrects a nested
versioning defect inherited from v002/v003: all eleven exported FBXs, including
the plastic-compactor ram and bale-discharge movers, use coherent `_v004`
names. The two obsolete misnamed `_v003` FBXs generated inside the v004 folder
were deleted only after the corrected v004 files were verified. No Unreal
asset or permanent level was touched.

The independent clean-scene audit is
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v004_independent.json`.
Blender 5.2 independently re-imported all eleven manifest FBXs and passed the
technical source gate: exact module count and names, identity import
transforms, origin pivots, finite dimensions and vertices, manifest bounds and
mesh counts, assembly-pivot metadata, opaque materials and absence of source
folder `.uasset` files. This result establishes a sound modular interchange
candidate only.

The same audit explicitly fails the visual promotion gate. v004 improves the
process over v002/v003 by replacing the rigid ring bundle with one full-width
wound sheet shell and by giving the normal and high-tension film states
different paths. However, the film remains too pale and smooth in the Blender
audit views, the dancer arm and roller are buried behind the material path, and
the compacted bale still reads as a pale crumpled rock or foliage mass instead
of dense folded plastic. The guarded overview also obscures the process more
than the authoritative PR-004A/PR-004-DS-001 views. Therefore v004 is
`SOURCE_FBX_GATE_PASS__VISUAL_GATE_FAIL__CANDIDATE_NOT_PROMOTED`.

The governing data contracts now record the v002, v003 and v004 review history:
`Content/LineBoss/Data/pr004_film_dewrap_spindle_v001.json` and
`Content/LineBoss/Data/pr004_robotic_depack_cell_v001.json`. The next permitted
step is an isolated, disposable Unreal PBR/hierarchy/motion preflight to decide
which deficiencies are caused by source preview materials and which require a
v005 geometry/readability rebuild. Permanent PR-004 import, anchor movement or
promotion remains forbidden until the complete cradle/robot/tool/spindle/waste
cell passes collision, interlock, persistence, runtime animation and fresh
fixed-camera visual comparison gates.

## 2026-08-01 — PR-004 isolated Unreal preflight and fixed-camera rejection

The isolated preflight now exists only under
`/Game/LineBoss/Stations/Press/PR004/Candidate_v002` and
`/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v002`.
All 49 source FBXs were imported sequentially after the Interchange batch path
proved unstable; evidence is in
`Saved/Logs/PR004_Candidate_v002_SequentialImport.log` and
`Saved/Audits/pr004_unreal_import_candidate_v002.json`. Candidate collision is
still complex-as-simple and is not accepted as release collision. No permanent
Press Shop map, station anchor, source FBX, vendor asset or Godot file was
changed, and nothing in this candidate is promoted.

The first off-screen diagnostic used a direct `SceneCapture2D` path and produced
false monochrome evidence. A controlled PR-005 A/B test proved that current
direct scene captures are invalid for colour approval while Unreal's normal
`AutomationLibrary.take_high_res_screenshot` viewport route retains colour.
The diagnostic is preserved, but all PR-004 visual decisions now use the seven
fresh 1920 x 1080 fixed-camera viewport files in
`Saved/ValidationScreenshots/PR004/Candidate_v002/`. Do not use direct
`SceneCapture2D` output as a colour gate until its engine-level discrepancy is
resolved.

Candidate-only material and lighting repairs made the geometry judgeable. The
constant direct materials under
`/Game/LineBoss/Stations/Press/PR004/Candidate_v002/MaterialsDirect_v003` were a
diagnostic stabilization step, not a release material solution. Validation-map
lighting v004 supplies broad non-shadowing review illumination and fixed
exposure; its mutation record is
`Saved/Audits/pr004_candidate_lighting_repair_v004.json`. The repaired view
confirms the flat-ended coil, real fence posts and mesh, robot scale, cradle and
locked 12.4 x 14.4 m envelope, but it also exposes the real quality gap.

The independently inspected seven-camera result is recorded at
`Saved/Audits/pr004_fixed_camera_visual_gate_v004.json` and is a visual failure.
The packaged coil remains too smooth and uniform, its close-range protective
film/fibre/tape/label construction is below the Pro and Blender references, the
tool-change camera shows an unfinished box/cylinder rather than four legible
tools, and the film module reads as a black housing rather than an understandable
tab-clamp/spindle/dancer/nip/compactor process. Finished HMI, labelled separated
waste, inspection towers and safety/maintenance dressing are also absent. No
fresh runtime animation, release collision, interaction or controller binding
proof exists. Promotion remains forbidden.

The next permitted work order is therefore release-surface and process
readability work inside the isolated candidate: first restore a modular PBR
packaged-coil/cradle presentation using licensed local surface inputs only where
they suit the custom UV/material contract, then correct the tool rack/camera and
film-path readability. After each change, repeat the same seven high-resolution
fixed cameras and compare them to both authoritative PR-004 sheets. A technically
passing import or source render is not sufficient for promotion.

## 2026-08-02 - PR-004 reach, guarding and dewrapper identity decision

The PR-004 v004 assembly was not accepted at its inherited layout. The robot
base-to-coil-centre distance was 458.803 cm, beyond the 350 cm working-radius
contract, and the old robot-to-coil route crossed the tool rack. This was an
Unreal candidate-layout error, not an error in the authoritative Pro sheets.
The corrected candidate keeps the cradle at `(-280, 120)` cm, places the robot
base at `(-40, 70)` cm, moves the tool rack to the rear service side, and places
the film-dewrapper root at `(330, -250)` cm. The resulting pivot distances are
252.036 cm to the coil centre, 296.919 cm to the film handoff and less than
345 cm to every tool dock. Static XY footprints no longer overlap. Evidence is
in `Saved/Audits/pr004_cell_reach_layout_repair_v004.json`. These results are a
numeric and static-clearance pass only; articulated swept collision for every
process pose remains mandatory.

The fixed-camera review exposed an arm-through-coil presentation pose. The map
now uses a clear 90-degree home sector explicitly marked as a validation home,
not as a band-cutting or dewrapping pose. The fresh image
`Saved/ValidationScreenshots/PR004/Candidate_v004/pr004_candidate_v004_overview_sw_pbr.png`
confirms that the parked robot is clear of the packaged coil. The robot retains
its authored 128 x 128 cm anchored pedestal/plinth; it must remain visually and
structurally legible in the release rebuild.

PR-004 now also has a candidate 2.4 m modular perimeter-guarding kit under
`SourceAssets/IndustrialKit/SafetyBarrier_v002/` and Unreal content under
`/Game/LineBoss/IndustrialKit/Safety/Barrier_v002`. The cell assembly contains
24 mesh panels, 27 actual bolted posts, three gates and three interlock boxes
around the locked 12.4 x 14.4 m envelope. The local film-dewrapper guard is an
additional nip/compactor hazard guard, not a substitute for the outer cell
perimeter. Its assembly evidence is
`Saved/Audits/pr004_perimeter_guarding_candidate_v002.json`. Release simple
collision, gate motion, navigation and interlock binding are still absent.

The current Unreal film-dewrapper v004 is not a different approved machine.
It is a simplified candidate representation of the powered coil-wrap
dewinding and compaction module shown in
`Docs/References/PR004_Robotic_Depackaging_Cell/v002/PR004_Powered_Coil_Wrap_Dewinding_Compaction_Module_RevA.jpg`.
The fresh fixed-camera view confirms that it still reads as a black enclosure
and roller rather than the drawing's powered winding spindle, guide/tension
mechanism, transfer path and compactor/baler. It remains visually rejected and
must be rebuilt to the drawing before promotion. The Pro drawing is
authoritative; the present v004 silhouette must not redefine the design.

## 2026-08-02 - PR-004 film-dewrapper v005 source visual gate

The source-only v005 rebuild under
`SourceAssets/PR004/FilmDewrapSpindle_v005/` successfully generated fourteen
independent FBX modules and five fresh Blender fixed-camera renders. It now
separates the tab clamp, expanding spindle, spindle rotor, dancer arm and
roller, stripper, transfer gate, compactor ram, bale discharge, full-width
film web, wound-film state and compacted-plastic-bale state. The build and its
numeric source checks are recorded in
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v005_source.json`.

This version is visually rejected and was not imported into Unreal. Inspection
of all five renders found that the compactor enclosure still dominates the
machine silhouette, the wound-film state reads as a second metal coil rather
than flexible packaging, and the web/dancer/transfer path is not readable as a
single process from the management camera. The surfaces are also too clean and
diagrammatic for close-range release quality. The explicit rejection record is
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v005_visual_gate.json`.
Passing export checks does not override this failure. The next iteration must
use the approved powered-spindle/dancer/compactor drawing as its silhouette
authority, expose the material path, make film states visibly flexible, and
pass source visual review before any Unreal import is attempted.

## 2026-08-02 - PR-004 open-frame film-dewrapper v006

The v005 black-enclosure direction was replaced rather than polished. The new
source-only v006 candidate is under
`SourceAssets/PR004/FilmDewrapSpindle_v006/` and contains fourteen independently
exported modules. It retains the established mover pivots but uses an open
spindle frame, three visible full-width guide rollers, a compact side-mounted
baler, a separate flexible web, irregular wound-film layers and a compacted
plastic-bale state. Two generator errors discovered in the first render (a
solid header plate and wall-sized baler corner posts) were corrected before the
visual decision.

Five rebuilt fixed-camera renders are in
`Saved/ValidationRenders/PR004/FilmDewrapSpindle_v006/`. Their review records a
process-silhouette pass: spindle, guide train and handoff are now legible, the
baler is subordinate, and the local guard protects only the baler hazard. This
supports isolated Unreal import testing, not promotion. Diagnostic source
materials, flexible-film behaviour, wear, fasteners, decals, release simple
collision, animation, interlocks and the seven-camera Unreal gate remain open.
The decision is recorded in
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v006_visual_gate.json`.

## 2026-08-02 - PR-004 v006 isolated Unreal fixed-camera rejection

The v006 film-dewrapper passed independent source-FBX checks and imported only
under `/Game/LineBoss/Stations/Press/PR004/Candidate_v006`. The isolated map is
`/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Depackaging_Candidate_v006`.
Its import audit is `Saved/Audits/pr004_unreal_import_candidate_v006.json`.
This technical success did not promote or alter the permanent Press Shop.

All seven fresh 1920 x 1080 Unreal viewport captures completed and were visually
inspected. They are under
`Saved/ValidationScreenshots/PR004/Candidate_v006/`. The open spindle frame,
guide train, subordinate compactor, robot pedestal and local open-mesh compactor
guard are present, but the complete candidate fails the visual gate. The review
lighting clips dark machinery and bright surfaces, both overview cameras crop
the cell, the top camera is far too wide, and the film-path camera does not show
the complete source-to-compactor process. The packaged coil still reads as a
rigid segmented shell rather than tensioned film, paper, bands and separate edge
protectors. Close views expose diagnostic geometry and material quality below
the authoritative Pro references. The tool view also fails to prove four
distinct docked tools or reachable automatic tool-change access.

The fail-closed decision is recorded in
`Saved/Audits/pr004_fixed_camera_visual_gate_v006.json`. Promotion remains
forbidden. The next pass must first rebuild the packaged-coil presentation,
replace the validation lighting with a neutral industrial review rig, reframe
all seven cameras, and assemble the authoritative outer perimeter, gates, HMI
and labelled waste modules. Only then may the same seven-camera gate be repeated.
Runtime animation, release collision, interlocks, persistent packaging/waste
state and the PR-005 handoff remain separate mandatory gates after visual parity.

User visual direction: retain the dewrapper's dirty, oily industrial character.
Future material work must use deliberate localized PBR grease and oil around
bearings, roller ends, drive housings, service panels and corresponding floor
stains. Do not clean the machine into a showroom asset, but also do not treat
viewport or path-tracing speckle as valid dirt; release screenshots must
distinguish authored wear from render noise.

Released plastic must not retain the coil's cylindrical silhouette. Model and
animate three physically distinct states: tensioned wrapping while still on the
coil; a thin, sagging and wrinkled web whose taut sections occur only between
real contact points; and an irregular folded, crumpled or wound waste mass at the
spindle and compactor. Any free plastic that reads like a second rigid coil is a
visual-gate failure.

Campaign condition authority: this equipment has been mothballed for seven
years. PR-004 release surfacing must therefore distinguish old shutdown history
from fresh recommissioning work. Use settled dust on upward faces, dried oil and
hydraulic weeping below joints, light oxidation on exposed edges and fasteners,
faded paint and labels, stale packaging debris, and darker grime in inaccessible
recesses. Recently inspected handles, guards, sensor faces, lubrication points
and serviced mechanisms should have clean witness marks or selectively renewed
parts. Safety-critical restoration may make the powered cradle, interlocks and
local repairs look newer without erasing the aged surrounding structure.

## 2026-08-02 - PR-004 flexible released-film v007 source pass

The v006 mechanical silhouette was retained, but its released-plastic states
were replaced in the source-only v007 candidate under
`SourceAssets/PR004/FilmDewrapSpindle_v007/`. The free web now has gravity sag,
cross-width wrinkles, edge curl and local taut spans only between authored
contact points. The take-up state uses distorted asymmetric sheet ribbons
instead of regular torus rings, so it no longer retains the source coil's rigid
cylindrical identity. Five fresh renders are under
`Saved/ValidationRenders/PR004/FilmDewrapSpindle_v007/`.

The film-behaviour silhouette passes source review, and all fourteen exported
FBXs passed independent clean-scene re-import. Evidence is in
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v007_visual_gate.json` and
`Saved/Audits/pr004_film_dewrap_spindle_candidate_v007_independent.json`.
This does not prove seven-year surfacing, Unreal deformation, collision,
interlocks or persistent packaging/waste state. The candidate is not promoted.

## 2026-08-02 - mostly autonomous factory and cleaning-AMR authority

The intended operating factory is mostly autonomous, not human-free. Normal
production, crane transfers, logistics, inspection, cleaning, condition
monitoring and supported routine maintenance should execute automatically once
commissioned. The player acts as Line Boss: commissioning systems, setting
policy and schedules, approving safety-critical actions, resolving exceptions
and deciding investments. Humans remain necessary for unusual damage, heavy
repairs, LOTO work, statutory inspection and final safety/quality release.

The user-approved LB-CR01 cleaning-AMR design sheet is archived at
`Docs/References/SharedSystems/CleaningAMR/v001/LB_CR01_Autonomous_Industrial_Floor_Cleaning_AMR_v001.png`.
It is the design authority for the shared floor-cleaning vehicle and dock. The
AMR may autonomously sweep, scrub, service at its dock and report hazards, but
must stop and isolate a route when it detects oil or hazardous spills. A future
maintenance-support robot may perform inspection, lubrication, sensor cleaning,
simple consumable/module swaps and tool delivery; it must not imply magical
self-repair or replace human certification.

## 2026-08-02 - coil packaging scope reduction

The user approved a simpler and clearer coil-state rule. Normal inbound and
stored production coils are bare steel rather than fully wrapped. They may carry
transport bands, an identity label and limited edge protection, but PR-001,
PR-002 and the normal PR-003 store presentation must not depend on full plastic
or paper packaging. PR-005 and every downstream strip-preparation view also use
the bare coil.

PR-003 therefore shows bare coils in its storage positions and does not require
an unwrapper animation. PR-004 becomes a robotic coil-transfer, optional
restrained-destrapping, identity-verification and surface/bore inspection cell.
The powered film-unwrapper is removed from mandatory baseline production,
animation and promotion gates. It may return later as an optional supplier or
weather-protected-coil module, but it must not delay the front-end release.

This decision removes repeated wrapping geometry, materials and the difficult
film-deformation animation while retaining meaningful PR-004 automation:
bare/banded inbound coil -> identification and inspection -> optional safe band
removal -> accepted bare-steel coil -> PR-005.

## 2026-08-02 - LB-MR01 maintenance-support robot design authority

The user-supplied LB-MR01 autonomous industrial maintenance-support robot sheet
is archived at
`Docs/References/SharedSystems/MaintenanceRobot/v001/LB_MR01_Autonomous_Industrial_Maintenance_Support_Robot_v001.png`.
It is accepted as the visual and gameplay authority for a shared cross-shop
inspection, diagnosis, light-service and small-parts-delivery robot. It is not a
humanoid and does not replace technicians, LOTO, heavy repair or recertification.

The sheet's fixed 1,550 mm length and 930 mm width are suitable starting datums.
Blue estimated values, the deployed-arm clearance and the proposed Press Shop
dock coordinate remain provisional until tested against authoritative aisles,
pedestrian routes, AGV routes and machine exclusion zones. Modelling is deferred
until PR-004 has passed its first automation gate; PR-004 remains the current
release-critical work.

## 2026-08-02 - PR-004 v007 fixed-camera rejection and state decision

Candidate_v007 was recaptured from all seven fixed Unreal cameras after neutral
cross-lighting, wider framing, explicit process-state isolation and correction
of the VCI-film material routing. Evidence is under
`Saved/ValidationScreenshots/PR004/Candidate_v007/`; the fail-closed review is
`Saved/Audits/pr004_fixed_camera_visual_gate_v007.json`.

The bare production-ready coil and powered cradle now read clearly, validating
the decision to reserve packaging for inbound/PR-004 transition states. The
complete cell still fails: it lacks the authoritative outer perimeter, posts,
two gates, operator-side HMI, inspection and waste layout; the robot tool view
is obstructed; the film path is not readable; and the packaging close-up still
shows rigid face panels. Candidate_v007 remains isolated and unpromoted.

The next candidate must rebuild the authoritative outer-cell layout first,
mount the robot on its proper pedestal, move the tool rack outside the swept
envelope with reach evidence, and replace the packaged input with one restrained
low-complexity transport-wrap state. Only then should the seven-camera visual
gate be repeated; runtime animation and interlocks remain downstream gates.

## 2026-08-02 - PR-004 bare-coil layout correction evidence

The approved modular safety kit has now been assembled around the isolated
Candidate_v007 map as a 12.4 x 14.4 m perimeter: 24 panels, 27 physical posts,
one 1.4 m operator gate and two 2.4 m transfer gates. The assembly audit is
`Saved/Audits/pr004_perimeter_guarding_candidate_v007.json`. It passes asset and
placement checks only; release collision, gate motion, coded interlocks,
navigation rebuilding and swept-volume checks remain required.

The corrected tool-rack layout places the rack behind the robot with its tools
facing the robot. Static route evidence reports that the direct robot-to-coil
line no longer crosses the rack and all docked tools remain inside nominal
reach. Evidence is in
`Saved/Audits/pr004_cell_reach_layout_repair_v007.json`. This does not prove the
animated arm's swept volume or maintenance access.

The shared HMI v004 cabinet has been assembled from 33 modular meshes outside
the operator gate at local `(180, 735, 0)` cm. Evidence is in
`Saved/Audits/pr004_shared_hmi_candidate_v007.json`. Fresh screenshots dated
2026-08-02 are under `Saved/ValidationScreenshots/PR004/Candidate_v007/`.
They fail the visual gate: the cell remains too sparse; the overview materials
are washed out; the HMI is not framed clearly; and the identity/surface/bore
inspection, optional restrained band handling, band compactor and realistic
service details are not yet present. The obsolete full-film module and rigid
wrap shell are hidden from the bare-coil baseline. Candidate_v007 remains
unpromoted.

## 2026-08-02 - shared support-robot Press Shop fleet assumption

Reserve map capacity for two LB-CR01 cleaning AMRs and two LB-MR01 maintenance
support robots. Each class requires two dock positions, primary/secondary
routes, controlled crossings, recovery points and machine-side stopping points.
The robots begin the restart campaign mothballed and must be repaired,
route-validated and commissioned. Their routes must remain outside active crane,
robot and material-transfer envelopes. Current planning clearances are 1.4 m
for the cleaning AMR route and 1.8 m around a maintenance robot with its arm
deployed; both remain provisional until the revised authoritative Press Shop
map and runtime navigation tests confirm them.

## 2026-08-02 - revised bare-coil front-end authority received

Four new Pro sheets are archived under
`Docs/References/PressShop_Revised_BareCoil_FrontEnd/v001/`. They supersede the
old wrapped-coil front-end layout and the old 14.4 x 12.4 m PR-004 cell:

- `Sheet_1_Revised_Press_Shop_Master_Plan.png`
- `Sheet_2_PR001_to_PR005_Operational_Plan.png`
- `Sheet_3_Revised_PR004_Cell.png`
- `Sheet_4_Front_End_Automation_Sequence.png`

The building remains fixed at 220 x 120 m. The revised front end uses bare
coils, retains twelve single-level PR-003 positions, and defines PR-004 as a
22 x 12 m robotic identification, optional destrapping and inspection cell.
Sheet 3 is now the PR-004 layout authority: powered V-cradle west, robot at the
cell centre, tool rack on the robot's rear/north side with all dock faces toward
the robot, steel-band compactor/bin northeast, HMI and operator position south,
and transfer gates on the material-flow boundaries. It also specifies face,
bore/ID and top cameras, inspection lights, LOTO, E-stops, maintenance access
and ready/hold lights.

The sheets explicitly include two LB-CR01 cleaning AMRs and two LB-MR01
maintenance-support robots, initially mothballed, with docks, routes, inspection
stops and PR-004 as a mobile-robot no-go interior. Candidate_v007 therefore
remains rejected historical evidence. A new Candidate_v008 must be built around
the 22 x 12 m coordinate system before any PR-004 promotion claim.

The interim v007 rack has been moved to the side indicated by its current J6
wrist pose, with all four tool pivots inside nominal reach. Evidence is in
`Saved/Audits/pr004_tool_rack_pointing_pose_v007.json`. This confirms the user's
orientation correction but does not substitute for the new Sheet 3 coordinate
rebuild or an animated docking/swept-collision test.

## 2026-08-02 - PR-004 Candidate_v008 first authoritative-layout review

`LB_PR004_Inspection_Candidate_v008` now uses the Sheet 3 22 x 12 m envelope,
with 37 modular fence panels, 40 explicit posts, west/east transfer gates and a
south operator gate. The cradle is assigned to the west datum, the robot to the
cell centre, and the four-position rack to the north/rear with dock faces toward
the robot. The obsolete full-film equipment is absent. The shared 33-module HMI
cabinet is assembled outside the south perimeter. Technical assembly evidence:
`Saved/Audits/pr004_authoritative_layout_candidate_v008.json` and
`Saved/Audits/pr004_shared_hmi_candidate_v008.json`.

Fresh fixed-camera evidence under
`Saved/ValidationScreenshots/PR004/Candidate_v008/` rejects this first v008
assembly for promotion. The inherited packaging group does not share a clean
assembly pivot: the bare coil separates from its powered cradle and appears
outside the east boundary. Several inherited robot/tool child meshes are also
detached after group translation. Lighting/background and missing inspection
equipment remain below release quality. Do not place this candidate in the full
Press Shop map. Rebuild the cradle/coil and robot/tool assemblies around clean
parent pivots, add the specified cameras, lighting, band compactor and status
devices, then recapture before integration.
## 2026-08-02 — PR-004 master-bay dimensional resolution and Candidate v009

- The revised Pro authority contains a dimensional conflict: Sheets 1–2 reserve an 11.5 m east-west PR-004 bay in the fixed 220 m × 120 m Press Shop, while the isolated Sheet 3 detail labels a 22 m × 12 m cell. A 22 m cell overlaps PR-003 and PR-005 at the authoritative master-plan anchors.
- Decision: the fixed master plan and the PR-001–PR-005 operational bay dimensions govern integration. The Sheet 3 equipment relationship remains the visual/process reference, but it must be refitted into an 11.5 m × 12 m bay without scaling machinery.
- Candidate map created/refitted: `/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009`.
- Refit audit: `Saved/Audits/pr004_v009_master_bay_refit.json`.
- Robot-chain repair audit: `Saved/Audits/pr004_v009_robot_chain_repair.json`.
- Fixed-camera evidence: `Saved/ValidationScreenshots/PR004/Candidate_v009/`.
- Technical result: map check is 0 errors / 0 warnings; the 11.5 m × 12 m perimeter, explicit fence posts, transfer openings and operator opening save correctly.
- Visual result: **REJECT / ITERATE**. The first screenshot pass exposed detached robot children outside the cell. They were reassembled into one compact base-to-wrist chain and recaptured, but the current imported multipart geometry remains visually bunched around the wrist/tool-rack area and the neutral validation lighting is too flat for release approval.
- Candidate v009 must not be promoted or copied into the full Press Shop yet. Next work is robot silhouette/pivot cleanup, reach-envelope proof, and a fresh fixed-camera comparison against revised Sheet 3.
- Floor decision: the isolated PR-004 candidate keeps a neutral validation floor. Continuous station colours, walkways, crane routes, crossings, seven-year wear and oil/dirt dressing belong to the full Press Shop map after station placement is accepted; only local maintenance/robot-sweep markings remain part of the reusable PR-004 module.

## 2026-08-02 — user-accepted PR-004 v009 integration and honest dirty-state review

- The user accepted the corrected PR-004 v009 visual candidate for full-map placement. This authorises integration but does not waive runtime, collision, animation, interlock or final release-art gates.
- The preserved source remains `/Game/LineBoss/Developer/Validation/PR004/LB_PR004_Inspection_Candidate_v009` and the previous full-map candidate remains `/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v002`.
- New integration map: `/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v003`.
- PR-004 is anchored at authoritative world coordinates `(-5050, -2000, 0)` cm. The integration copied 142 selected mesh actors, removed 129 obsolete PR-004 blockout actors and excluded 12 validation-only floor/envelope/light objects. Audit: `Saved/Audits/press_shop_pr004_v009_integration_v003.json`.
- Fresh evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v003_dirty/`: whole shop, front end and PR-004 close views. The placement, scale, fence posts and relationship to PR-003/PR-005 are readable. However, the current full map is still too bright and clean to represent seven years dormant, and downstream Press Shop areas remain largely empty/blockout. These screenshots are truthful current-state evidence, not release-quality dirty-state approval.
- Continuous floor ageing, dirt/oil, dormant lighting and route paint must be authored at full-map level; do not bake a separate clean slab into PR-004.

## 2026-08-02 — LB-CR01 Candidate v001 started

- The first dimension-locked modular cleaning-AMR candidate has been generated from the archived design authority at `Docs/References/SharedSystems/CleaningAMR/v001/LB_CR01_Autonomous_Industrial_Floor_Cleaning_AMR_v001.png`.
- Source generator: `SourceAssets/SharedSystems/CleaningAMR/build_lb_cr01_candidate_v001.py`.
- Candidate source, GLB and fixed-oblique render: `SourceAssets/SharedSystems/CleaningAMR/Candidate_v001/`.
- Fixed envelope is 1.520 m long x 0.980 m wide x 1.120 m high. Wheels, hubs, side brushes, scrub deck/discs, service doors, hopper access, recovery points, squeegee, depth/LiDAR sensors and stack-light sections are separate objects for later animation and servicing.
- Visual status: **BLOCKOUT / ITERATE**, not approved for Unreal integration. The silhouette and modular split are viable, but the next pass requires rugged service detail, grilles, water/debris hardware, charging contacts, labels, seven-year grime and reference-quality material wear.

## 2026-08-02 — mothballed Press Shop v004 and LB-CR01 Unreal dimensional gate

- Preserved `/Game/LineBoss/Maps/LB_PressShop_IntegrationCandidate_v003` and created the reversible derivative `/Game/LineBoss/Maps/LB_PressShop_MothballedCandidate_v004`.
- The v004 pass reduces 19 inherited production lights, retains three local emergency/service pools, and adds 11 removable full-map floor-grime/oil dressing actors prefixed `LB_MOTH_V004_`. Audit: `Saved/Audits/press_shop_mothballed_v004.json`.
- Fresh evidence: `Saved/ValidationScreenshots/PressShopIntegration/v004_mothballed/press_shop_v004_mothballed_whole.png`, `press_shop_v004_mothballed_front_end.png`, and `press_shop_v004_mothballed_pr004.png`. Map check during capture: 0 errors / 0 warnings.
- Visual verdict: **CANDIDATE / ITERATE**, not release promotion. The dormant shell and localized working-light concept now read clearly, and PR-004 remains positioned correctly, but the temporary blue PR-004 service pool is too saturated, the grime patches are still broad procedural placeholders, and the empty downstream Press Shop remains the dominant visual blocker.
- LB-CR01 first Unreal import v001 failed the fixed envelope because brushes and service hardware exceeded 1.520 x 0.980 x 1.120 m. Corrected import lives under `/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v002`; audit `Saved/Audits/lb_cr01_candidate_v002_unreal_import.json` reports 70 meshes, 12 tagged movers and aggregate bounds 151.05 x 96.0 x 108.65 cm, so the dimensional gate passes.
- LB-CR01 v002 remains **CANDIDATE / NOT PROMOTED**. Neutral fixed-camera validation exposed an unstable presentation-lighting setup (first too dark, then overexposed) and Unreal crashed during a follow-up validation-light adjustment. Preserve the valid imported geometry and source; next pass should improve materials/service hardware and rebuild a stable isolated evidence map rather than repeatedly reimporting.
- Win64 SDK validation remains independently blocked (`Win64 INVALID 10.0.22621.0`). This does not invalidate content-map captures but still blocks a trustworthy packaged/runtime gate.

## 2026-08-02 — LB-CR01 v004 visual rejection after Press Shop placement test

- The improved Blender source in `SourceAssets/SharedSystems/CleaningAMR/Candidate_v002/` was imported as `/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v004` after a preserved v003 import exceeded the fixed envelope.
- Candidate v004 contains 89 meshes and 13 tagged movers. Unreal aggregate bounds are 151.25 x 96.70 x 108.85 cm against the fixed 152 x 98 x 112 cm envelope, so the dimensional gate passes. Audit: `Saved/Audits/lb_cr01_candidate_v004_unreal_import.json`.
- Isolated evidence is under `Saved/ValidationScreenshots/LB_CR01/Candidate_v004/`. It proves a readable scale-correct machine, but visual review rejects promotion: the silhouette is too boxy/toy-like, materials are flat and clean, service hardware and brush mechanisms are underdeveloped, and the dock is not yet a release-quality asset.
- Two non-promoted placement instances and provisional docks were added to the preserved derivative `/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005`; placement audit: `Saved/Audits/press_shop_lb_cr01_v004_placement_v005.json`.
- The west fixed-camera view confirms management-distance scale and floor fit. The east test exposed an incorrect pitch/mirroring transform that placed the robot below the floor while leaving its provisional dock visible. Do not promote or animate either placement. Repair or replace the east transform only as part of the next cleaner revision.
- User visual decision: **REBUILD / ITERATE**. Before route or cleaning automation, rebuild the rugged tapered body, recessed bumpers, access doors, debris/water service points, brush/squeegee articulation, charging dock, seven-year dormant dirt and Unreal PBR materials. Then import as a new preserved candidate and repeat isolated plus in-map evidence.

## 2026-08-02 — shared support-robot chassis decision

- The LB-CR01 cleaning AMR and LB-MR01 maintenance-support robot will use one dimension-controlled autonomous mobile base rather than two unrelated vehicles.
- Shared base target: approximately 1,520 mm long x 930 mm track width, with identical traction modules, battery trays, safety bumpers, charging interface, navigation sensors, recovery/tow points, controller bay and core state/save identifiers.
- Variant envelopes remain honest: LB-CR01 reaches about 980 mm overall width through its projecting cleaning brushes and 1,120 mm height with sensors/stack light; LB-MR01 may reach about 1,550 mm overall length with towing equipment and about 1,250 mm travel height with the inspection arm stowed.
- Cleaning-only modules: clean/recovery tanks, debris hopper, scrub deck, side brushes, rear squeegee and water/waste dock services. Maintenance-only modules: arm turntable and vertical lift, six-axis arm, tool magazine, stabilisers, parts drawers and inspection mast.
- The dock uses a shared electrical/data alignment datum, with variant service manifolds attached modularly. Unreal should use a shared base Blueprint/state component plus child variant Blueprints so navigation, faults, charging, save/load and restoration condition are authored once.
- Current LB-CR01 Blender Candidate v003 is a preserved silhouette experiment only. It remains visually rejected for release use and must not be imported merely because it fits the envelope.
- Shared-platform Blender experiment `SourceAssets/SharedSystems/SupportRobotPlatform/Candidate_v001/` establishes the common deck rails, four drive cassettes, service doors, navigation sensors, recovery points and charging datum. Its fixed-oblique render was visually reviewed and **REJECTED** before Unreal import: wheels and corner guards are too visually dominant, the body reads stylised/toy-like, and procedural wear resembles wood grain rather than painted industrial steel. Preserve its dimensions and component split only; rebuild the visible shell with fabricated-sheet-metal proportions and subtler PBR wear.
- Candidate v002 at `SourceAssets/SharedSystems/SupportRobotPlatform/Candidate_v002/` corrects the false wood-grain colour variation, partially shrouds the drive wheels and reduces the corner guards. **Architecture accepted / visual iterate**: its deck, drive, charging and service-module datums are suitable foundations for both variants, but the naked base is not a release asset and must not be imported yet. Variant bodywork must hide more of the rectangular chassis, add credible panel seams/fasteners and be reviewed first as complete LB-CR01 and LB-MR01 silhouettes.

## 2026-08-02 — Pro LB-CR01/RP01 build-pack intake and v009 gate

- The user supplied `LB_CR01_SHARED_ROBOT_PLATFORM_BUILD_PACK_v1.0.zip`. Its
  extracted canonical copy is under
  `SourceAssets/ReferencePacks/LB_CR01_SHARED_ROBOT_PLATFORM_BUILD_PACK_v1.0/`.
- The pack is now the cleaner/shared-platform authority. Numeric authority is
  `data/authoritative_dimensions.json`, followed by the pivot and socket data;
  its images are visual references and never override numeric values.
- Fixed CR01 travel envelope: 1520 x 980 x 1120 mm with 110 mm ground
  clearance. The exact shared RP01 source owns the chassis, payload plate,
  running gear, battery/control interfaces and common electrical/data dock;
  CR01 and future MR01 must instance it rather than duplicate it.
- CadQuery 2.8.0 and Blender 5.2 LTS successfully execute the supplied scripts.
  The supplied Blender starter itself fails its own fixed envelope at
  1500 x 950 x 1120 mm, so its generated proxy is not import authority.
- Corrected candidate source:
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v009/LB_CR01_ProPack_v009.blend`.
  Its independent validation passes exactly at 1520 x 980 x 1120 mm, with no
  negative/non-uniform scale and no required-object omissions.
- Fresh source evidence is under
  `Saved/ValidationRenders/LB_CR01/Candidate_v009/`. Visual verdict is
  **REJECT / ITERATE**: the body is coherent but remains too rectilinear,
  brushes and service mechanisms are proxy-level, and materials lack release
  PBR detail. Do not import or place v009 in Unreal. Retain its dimension-locked
  RP01/interface foundation and rebuild the visible CR01 surface language.

## 2026-08-02 — LB-CR01 v010/v011 pack-contract progress

- Candidate v009 remains preserved for comparison. Candidate v010 at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v010/` replaces its stacked
  boxes with a continuous tapered side-profile shell, detailed cylindrical and
  radial brushes, side/rear service faces, couplers, hoses and protected
  cleaning assemblies. After correcting a 13.3 mm squeegee overhang and
  restoring required names, it passes 1520 x 980 x 1120 mm exactly.
- Candidate v011 at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v011/` preserves v010 and
  adds all 30 authoritative pivot declarations, all 17 required sockets and
  seven simple UCX source collision meshes. The completeness JSON passes with
  367 mesh objects, 3 curve hoses, 11,944 base triangles and 13 materials.
- Despite those technical passes, the latest fixed source views remain
  **VISUAL ITERATE / NOT PROMOTED**. The tapered silhouette is a meaningful
  improvement, but wheels, brush-arm mechanics, service internals, dock and
  final PBR condition variants still do not match the Pro sheet closely enough.
  Do not export/import v011 merely because its contract audit passes.
- Required production folders now exist under `SourceAssets/Robots/`; existing
  numbered candidates remain in their historical paths to avoid duplication.
  Mapping and tool evidence are in `SourceAssets/Robots/SOURCE_PATH_MAPPING.md`
  and `SourceAssets/Robots/BUILD_ENVIRONMENT.md`. Full current gate status is
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/VALIDATION_REPORT.md`.

## 2026-08-02 — LB-CR01/RP01 formal Phase 1 evidence gate

- The build-pack author's requested Phase 1 evidence has been executed in the
  canonical non-OneDrive environment. CadQuery 2.8 regenerated the RP01 and
  CR01 STEP/GLB blockouts; Blender 5.2 LTS generated a separately preserved
  Phase 1 `.blend` and four fixed evidence views.
- The corrected CR01 blockout measures exactly `1520 × 980 × 1120 mm`. The
  bright orange calibration cube in every view measures exactly
  `1000 × 1000 × 1000 mm`. Machine-readable evidence is at
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Phase_1_Blockout/PHASE_1_VALIDATION.json`.
- Required views are under
  `Saved/ValidationRenders/LB_CR01/Phase_1_Blockout/`: front, side, top and
  fixed oblique. The report with exact commands and paths is
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Phase_1_Blockout/PHASE_1_REPORT.md`.
- The pack's original Blender starter output remains documented as failing at
  `1500 × 950 × 1120 mm`; it was not silently treated as authoritative. The
  corrected evidence is isolated from Candidates v009–v012, all of which are
  retained for comparison.
- Phase 1 technical status: **PASS / AWAITING EXTERNAL REVIEW**. This authorises
  continued source development once reviewed, but does not promote any cleaner
  candidate into Unreal or release content.

## 2026-08-02 — LB-CR01 Phase 1 approved; Phase 2 authorised

- The external build-pack author reviewed the formal front, side, top and
  fixed-oblique dimensional evidence and approved Phase 1. The gate is now
  **PASS / EXTERNALLY APPROVED**; detailed Phase 2 shared-platform production
  geometry is authorised.
- Candidate v012 at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v012/LB_CR01_Mechanics_v012.blend`
  retains the exact `1520 x 980 x 1120 mm` envelope, all 30 required pivots,
  all 17 sockets and seven simple collision sources. It improves wheels,
  running gear and brush mechanisms but remains visually too clean and
  blockout-like for promotion.
- Candidate v013 is preserved as failed visual evidence: its procedural finish
  read as timber/wood and is explicitly rejected. Candidate v014 replaces that
  material graph with a subtle parameter-driven industrial finish and remains
  dimensionally valid, but mothballed/restored states are not yet visually
  distinct enough. Neither candidate is promoted.
- The first separately authored service dock source is
  `SourceAssets/SharedSystems/CleaningAMR/Dock_Candidate_v001/LB_CR01_ServiceDock_v001.blend`.
  It separates RP01 electrical/data alignment hardware from CR01 water, waste,
  wash and drain systems. The fresh fixed-oblique render is
  `Saved/ValidationRenders/LB_CR01/Dock_Candidate_v001/LB_CR01_ServiceDock_v001_fixed_oblique.png`.
- Dock Candidate v001 is **DIMENSIONAL/MECHANICAL BASE ONLY / VISUAL REJECT**.
  The layout is readable but still resembles clean blockout cabinetry; Phase 2
  must add believable hoses, rigid pipework, couplers, guards, drains, labels,
  service fasteners and dormant/restored PBR condition before Unreal import.
- Dock Candidate v002 preserves v001 and adds separate wet-service pipe and
  hose runs, flanges, clamps, electrical/network conduits, drain grate, wash
  nozzles, hose guards, fasteners and service-label plates. Source:
  `SourceAssets/SharedSystems/CleaningAMR/Dock_Candidate_v002/LB_CR01_ServiceDock_v002.blend`;
  evidence:
  `Saved/ValidationRenders/LB_CR01/Dock_Candidate_v002/LB_CR01_ServiceDock_v002_fixed_oblique.png`.
- v002 is also **VISUAL ITERATE / NOT PROMOTED**. It proves the modular service
  split but the routed pipes are too angular/bright, the front docking strike
  zone is congested and the cabinets still lack final fabricated detail. The
  next pass must reroute services against the rear panel, use restrained hose
  loops at the robot interface and validate the cleaner physically docked.
- Dock v003 performed the first actual-geometry docked test using CR01 v014,
  proving that the cleaner orientation and gross rear-face placement are
  correct. Its automatic Bezier routes visibly swept across the approach and
  were rejected; v003 remains preserved as failure evidence.
- Dock Candidate v004 reroutes wet and dry services into cabinet drops and a
  concealed dock plinth, leaving only short protected couplers at the robot
  face. Fresh actual-cleaner evidence:
  `Saved/ValidationRenders/LB_CR01/Dock_Candidate_v004/LB_CR01_Dock_v004_actual_cleaner_docked.png`.
- Machine-readable interface validation is
  `SourceAssets/SharedSystems/CleaningAMR/Dock_Candidate_v004/DOCKED_INTERFACE_VALIDATION.json`.
  At the authoritative 1445 mm centre offset, dock datum, two charge contacts,
  network, clean-water and dirty-extraction sockets all match the actual CR01
  v014 sockets with `0.0 mm` error. This passes the interface-fit gate only;
  dock v004 and cleaner v014 remain **VISUAL ITERATE / NOT PROMOTED**.
- Cleaner Candidate v015 proves the non-duplicated condition-variant approach:
  shared material parameters plus `30_CONDITION_MOTHBALLED` and
  `31_CONDITION_RESTORED` switchable dressing/service-part collections. Its
  first comparison clearly separates states, but broad opaque dirt polygons
  and bright green restored bezels read as debug art; v015 is preserved and
  visually rejected.
- Candidate v016 at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v016/LB_CR01_Condition_v016.blend`
  replaces those overlays with translucent dirt/water/oil dressing, short
  gravity-led grime marks, muted certification hardware and dark service lens
  bezels. Fixed comparison views are under
  `Saved/ValidationRenders/LB_CR01/Candidate_v016/`.
- v016 makes the seven-year mothballed/restored distinction readable without
  duplicating the robot and is a meaningful condition-system improvement, but
  remains **VISUAL ITERATE / NOT PROMOTED**. Some planar overlays are still
  detectable at close evidence distance, the body remains too block-built
  compared with the Pro sheet and Unreal decals/PBR must replace source-preview
  dressing before release promotion.

## 2026-08-02 — LB-CR01 Phase 2 source-contract correction

- Pro/build-pack review has confirmed the Phase 1 evidence is good. The exact
  `1520 x 980 x 1120 mm` Phase 1 blockout and its four evidence views are now a
  frozen, externally approved baseline. Phase 2 may refine production geometry
  but must not overwrite or retrospectively alter that evidence package.
- The authoritative socket/interface count is **18**, not 17. Candidate v012's
  earlier handoff entry recorded the old count; the current validator now reads
  `data/sockets_interfaces.json` directly and requires all 18 interfaces.
- Candidate v018 is the current technically valid Phase 2 source at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v018/LB_CR01_Condition_v018.blend`.
  Machine-readable validation is
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v018/source_validation.json`.
  It measures exactly `1520 x 980 x 1120 mm`, contains 546 mesh objects, three
  curve objects and 57,574 evaluated triangles, and passes all 30 pivots, all
  18 sockets, seven collision meshes, applied-transform and scale checks.
- The reusable source validator is
  `SourceAssets/SharedSystems/CleaningAMR/validate_lb_cr01_production_source.py`.
  It evaluates curve geometry rather than trusting Blender curve bounding-box
  artefacts and limits envelope checks to production collections.
- Fixed v018 comparison evidence is under
  `Saved/ValidationRenders/LB_CR01/Candidate_v018/`. Technical source status is
  **PASS**, but visual status remains **ITERATE / NOT PROMOTED**: the broad
  condition overlays are still visibly planar, the restored recertification
  plate reads like debug geometry and the body silhouette remains more
  block-built than the Pro reference. Passing the source contract does not
  authorise Unreal/release promotion.

## 2026-08-02 — LB-CR01 Candidate v019 visual cleanup

- Candidate v019 is preserved at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v019/LB_CR01_Condition_v019.blend`.
  It removes the broad roof, side, lower-front and ledge condition cards that
  read as tape/cardboard in v018. Remaining mothballed witnesses are local
  fastener oxidation, lower-edge corrosion, dirty lenses and degraded service
  parts, with metadata requiring Unreal decal/material-instance replacement.
- The restored debug-green rectangle is replaced by a compact fabricated SS304
  recertification plate with border-scale data bars, inspection mark and four
  fasteners. This is physically more plausible and remains a separate,
  switchable restored-condition module.
- `validate_lb_cr01_production_source.py` now fails with a deterministic message
  when no production geometry is loaded instead of raising an unhelpful empty
  `min()` traceback. v019 passes its complete source contract: exactly
  `1520 x 980 x 1120 mm`, 540 mesh objects, three curves, 57,616 evaluated
  triangles, all 30 pivots, all 18 sockets, seven collision meshes and no
  negative/non-uniform scales. Evidence:
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v019/source_validation.json`.
- Fresh comparison renders are under
  `Saved/ValidationRenders/LB_CR01/Candidate_v019/`. Visual status remains
  **ITERATE / NOT PROMOTED**. v019 removes the most obvious dressing artefacts,
  but its management-distance mothballed/restored distinction is now too subtle
  and the main body still lacks the rounded, rugged manufactured silhouette of
  the Pro reference. The next pass should improve shared body-panel geometry
  and service identity rather than adding more flat preview overlays.

## 2026-08-02 — LB-CR01 Candidate v020 manufactured silhouette

- Candidate v020 is preserved at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v020/LB_CR01_Condition_v020.blend`.
  It increases the segment count and realistic manufactured radii on the shared
  body shell, roof, lower skirts, front brow/blackout, sensor bar, rear inset
  and service hatches. It reuses the existing RP01/CR01 production components;
  no duplicate body or platform was introduced.
- The pass materially improves the compact rounded silhouette visible in the
  Pro reference while retaining the exact approved travel envelope. Evaluated
  geometry is now 63,320 triangles, still appropriate for the source/high-detail
  candidate before formal LOD construction.
- The production validator now proves authoritative pivot/socket placement, not
  merely name existence. All 30 pivots are checked to 0.1 mm against the CFR
  coordinates and checked for ID, asset, sharing-class and axis metadata. All
  18 sockets are checked to 0.1 mm and checked for shared/CR01 scope. v020 has
  zero pivot position/metadata failures and zero socket position/scope failures.
- Machine-readable evidence is
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v020/source_validation.json`;
  fixed mothballed/restored evidence is under
  `Saved/ValidationRenders/LB_CR01/Candidate_v020/`.
- v020 remains **PHASE 2 CANDIDATE / NOT PROMOTED**. The silhouette is a clear
  improvement and the technical evidence is strong, but release promotion still
  requires operational/deployed views, LOD/UV/collision/export completion and
  fresh Unreal 5.8 fixed-camera runtime evidence against the Pro sheet.

## 2026-08-02 — LB-CR01 v020 deployed-cleaning evidence

- A non-destructive operational evidence harness now exists at
  `SourceAssets/SharedSystems/CleaningAMR/render_lb_cr01_v020_operational.py`.
  It opens v020, poses only the in-memory evidence scene and never saves the
  operational pose back into the production `.blend`.
- The harness measures the evaluated side-bristle geometry rather than relying
  on nominal arm travel. The stowed bristle span required 192.782 mm lateral
  deployment per side to produce the authoritative 1,350.0 mm cleaning swath.
  Machine-readable evidence is
  `Saved/ValidationRenders/LB_CR01/Candidate_v020/LB_CR01_v020_operational_pose_validation.json`;
  the measured swath passes exactly at `1350.0 mm`.
- Fresh deployed evidence is
  `Saved/ValidationRenders/LB_CR01/Candidate_v020/LB_CR01_v020_restored_operational_deployed.png`.
  The cleaning head is now readable and dimensionally correct, but this view
  also exposes that the current source linkage visually translates more than it
  articulates. This is **OPERATIONAL FOOTPRINT PASS / ANIMATION VISUAL ITERATE**,
  not promotion evidence. Unreal assembly must drive the side-brush arm about
  its authoritative pivots and combine that rotation with the lift/spin stages.

## 2026-08-02 — LB-CR01 Candidates v021/v022 export-source preparation

- Candidate v021 consolidated 15 production materials to the pack limit of ten
  without replacing the robot or flattening lamp identity. Red, amber, green,
  blue and warm lamp materials now share
  `M_LB_RP01_LensVertexTint_v021`; individual colours are stored in exported
  CORNER-domain `LB_Tint` vertex colour data. Label plates reuse the brushed
  SS304 master and retain metadata for Unreal decal content.
- The UV audit then found that 496 of 497 base production meshes had UV0, while
  `SM_LB_CR01_TaperedBodyShell` did not. v021 is preserved; v022 adds a named
  `UV0` layout to that shell and is preserved at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v022/LB_CR01_Export_v022.blend`.
- `validate_lb_cr01_production_source.py` now includes base-production material
  and UV gates. v022 reports 497 base meshes, exactly ten materials, no missing
  UV0, 63,320 evaluated triangles, exact `1520 x 980 x 1120 mm` dimensions,
  all 30 pivots with authoritative placement/metadata, all 18 sockets with
  authoritative placement/scope, seven collision meshes and clean transforms.
  Machine-readable evidence is
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v022/source_validation.json`.
- Fresh post-consolidation fixed views are under
  `Saved/ValidationRenders/LB_CR01/Candidate_v022/`; stack-light and service
  colours remain readable. Status is **EXPORT SOURCE GATES PASS / VISUAL AND
  UNREAL GATES STILL OPEN**. LOD assets/exports and Unreal runtime evidence are
  still required before promotion.

## 2026-08-02 — LB-CR01 Candidate v023 LOD and FBX export gate

- Pro confirmed the Phase 1 dimensional blockout as good. That evidence remains
  frozen and v022 remains the unmodified close-range production source.
- Candidate v023 is preserved at
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v023/LB_CR01_LODs_v023.blend`.
  Its reproducible builder is
  `SourceAssets/SharedSystems/CleaningAMR/build_lb_cr01_lods_v023.py`.
- Separate FBX evidence for LOD0–LOD4 is under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v023/`. LOD0–LOD2
  retain separate component objects for Unreal assembly; the whole cleaner was
  not collapsed into a skeletal or single static mesh. LOD3/4 are deliberately
  small management-distance silhouette assemblies.
- Machine-readable results are in
  `SourceAssets/SharedSystems/CleaningAMR/Candidate_v023/LOD_EXPORT_VALIDATION.json`:
  LOD0 55,424 triangles/10 materials; LOD1 55,424/9; LOD2 34,948/7;
  LOD3 740/3; LOD4 464/3. Every pack triangle/material limit and non-empty FBX
  gate passes. LOD0's mesh-only count excludes source curve evaluation reported
  by the broader v022 validator; both remain within the LOD0 budget.
- Fixed-camera comparison renders are under
  `Saved/ValidationRenders/LB_CR01/Candidate_v023/`. The visual pass caught and
  corrected an initial millimetre/metre scale error in the far proxies before
  acceptance. LOD0–LOD2 retain the cleaner identity; corrected LOD3/4 retain a
  coherent industrial silhouette at their intended distances.
- Status is **SOURCE LOD/FBX GATES PASS / CANDIDATE NOT PROMOTED**. Unreal 5.8
  import, materials, component hierarchy, collision/navigation and fresh
  in-engine fixed-camera evidence remain mandatory before promotion.

## 2026-08-02 — LB-CR01 Unreal orientation, runtime and visual gates

- The original v023 FBX imported at `98 x 152 x 112 cm`, putting the cleaner's
  longitudinal axis on Unreal Y. v024 and v025 metadata-only axis attempts also
  failed and are retained as negative evidence; none was promoted.
- Candidate v026 uses an explicit -90-degree Z export-datum conversion while
  leaving v022/v023 source geometry untouched. The FBX is
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v026/LB_CR01_FullRobot_LOD0_XForward_v026.fbx`.
  Unreal import evidence at `Saved/Audits/lb_cr01_candidate_v026_unreal_import.json`
  passes with 497 meshes, 84 tagged movers and aggregate bounds of
  `152.000015 x 98.000015 x 111.999992 cm`; the longitudinal axis is Unreal +X.
- `Scripts/build_lb_cr01_runtime_travel_v026.py` creates a six-second, 30 fps
  Level Sequence translating the complete 497-actor assembly 250 cm on +X.
  Live Play-In-Editor inspection proved the complete cleaner travels together.
  This is **RUNTIME TRAVEL PROOF ONLY**: FBX object placement is presently baked
  into mesh assets, so individual wheel/brush mechanisms do not yet have safe
  local component pivots. Mechanism animation remains a blocking promotion gate.
- Native candidate materials replace pale FBX placeholders and six attached
  runtime lights now represent two work lights, two red rear safety lights, an
  amber stack light and a blue route projector. Material/light evidence is in
  `Saved/Audits/lb_cr01_candidate_v026_materials.json`.
- Fresh fixed-camera screenshots are under
  `Saved/ValidationScreenshots/LB_CR01/Candidate_v026/`. Visual verdict is
  **ITERATE / NOT PROMOTED**: the oblique view is readable, but the side is too
  dark, the top camera is cropped, the blue projector is too intense and roof
  highlights still dominate. Technical/runtime passes do not override this
  visual rejection.

## 2026-08-02 — LB-RP01 authoritative shared-platform extraction

- The approved v022 cleaner remains unchanged. Its existing shared collections
  were extracted without remodelling into the authoritative source
  `SourceAssets/Robots/LB_RP01_Shared/Blender/LB_RP01_SharedParts_v001.blend`.
  The reusable source contains 98 visible meshes, three RP01 collision hulls
  and 21 shared pivots/sockets. It owns chassis, bumpers, drive/caster families,
  service hardware, stack light/sensors and dock/charge/tow/fork/audio/MR01
  interfaces once.
- Reproducible extraction and machine-readable evidence are
  `SourceAssets/Robots/LB_RP01_Shared/Blender/extract_lb_rp01_shared_v001.py`
  and
  `SourceAssets/Robots/LB_RP01_Shared/Validation/LB_RP01_SharedParts_v001.json`.
- CR01 Candidate v027 is preserved at
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v027/LB_CR01_LinkedRP01_v027.blend`.
  It library-links all 122 RP01 source objects rather than carrying local
  lookalike duplicates. Validation at
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v027/LB_CR01_LinkedRP01_v027.json`
  proves 598 source/candidate objects, no missing or extra names, no changed
  geometry/material signatures and zero envelope drift at exactly
  `980 x 1520 x 1120 mm` in Blender axes.
- This is **SHARED-SOURCE REUSE PASS / NOT A VISUAL PROMOTION**. MR01 must now
  link this exact RP01 library; it must not copy or recreate similar base parts.

## 2026-08-02 — LB-CR01 enclosure repair and Candidate v031 visual rejection

- Candidate v029 replaced the fragile single extruded body shell with 18
  explicit closed-volume CR01-only side-skin, door-surround, rocker and shoulder
  meshes around the unchanged linked RP01 platform. Candidate v030 added 62
  finish objects including the continuous safety belt, door seams, hinges,
  latches, vent cassettes, side markers, certification plates and roof infills.
  Sources and validation are under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v029/`,
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v030/` and their
  matching `Validation/Candidate_v029/` and `Validation/Candidate_v030/`
  directories. The authoritative RP01 library remains unchanged.
- The complete v030 FBX imported as 573 separate meshes with the correct Unreal
  +X envelope of approximately `152 x 98 x 112 cm`. Candidate v031 applies
  native Unreal materials and a fixed-exposure validation setup without changing
  geometry. Fresh evidence is under
  `Saved/ValidationScreenshots/LB_CR01/Candidate_v031/`.
- Fixed left and right views prove both sides are now enclosed and symmetrical;
  the original missing/back-face side failure is resolved. Visual status remains
  **ITERATE / NOT PROMOTED**: the enclosure is too box-like against the Pro
  authority, roof beacons still read as primitive cylinders, and panels lack the
  close-range manufacturing and condition detail required for release.
- Candidate v032 is a warning-clean re-export of the same v030 geometry using
  FBX face smoothing. It is preserved at
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v032/` and retains
  the exact `1520 x 980 x 1120 mm` Unreal-oriented envelope. Unreal re-import at
  `/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v032/LOD0` contains all
  573 separate meshes; `Saved/Audits/lb_cr01_candidate_v032_unreal_import.json`
  records `152.000015 x 98.000015 x 111.999992 cm`, and the import log contains
  zero smoothing-group or Python errors. This clears the import-warning gate,
  not the visual or mechanism-pivot gates.
- Fine-detail authority is now explicit: CadQuery owns dimensions/interfaces;
  Blender owns silhouette, seams, hardware and separated mechanisms; Unreal owns
  final PBR response, condition decals, dirt/oil and lighting. Surface-only
  treatment must not substitute for missing physical silhouette or service
  geometry.
- Release blockers remain: refined Pro-matching enclosure silhouette, modelled
  stack light and sensor housings, warning-clean Unreal v032 import, verified
  local pivots and individual wheel/brush/deck/squeegee animation, simple convex
  collision/navigation footprints, mothballed/restored material variants and
  fresh in-factory fixed-camera evidence.

## 2026-08-02 — LB-RP01 shared-detail Candidate v002 and CR01 relink v033

- The original authoritative RP01 v001 library remains preserved. Candidate
  v002 is at
  `SourceAssets/Robots/LB_RP01_Shared/Blender/Candidate_v002/LB_RP01_SharedParts_v002.blend`.
  It adds 20 genuinely shared meshes: a manufactured stack-light foot/stem,
  separator collars and cap; a protected forward perception housing with two
  camera lenses, bezels, central LiDAR window and service fasteners; and a rear
  sensor pod. The reproducible builder and report are
  `SourceAssets/Robots/LB_RP01_Shared/Blender/refine_lb_rp01_shared_v002.py`
  and
  `SourceAssets/Robots/LB_RP01_Shared/Validation/Candidate_v002/LB_RP01_SharedParts_v002.json`.
- CR01 Candidate v033 replaces its 122 v001 links with 142 true library links
  from RP01 v002; CR01-specific body and cleaning payload geometry remains local.
  Source and reuse evidence are
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v033/LB_CR01_LinkedRP01_v002_v033.blend`
  and
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v033/LB_CR01_LinkedRP01_v002_v033.json`.
  MR01 must link the same RP01 v002 candidate rather than copy these meshes.
- Blender review evidence is under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v033/Blender/`.
  The protected front perception bar is a visible improvement. Status remains
  **ITERATE / NOT PROMOTED**: the stack-light silhouette is still too plain, the
  cleaner body is too slab-sided/clean against the Pro reference, and Unreal
  import/runtime/fixed-camera gates for v033 have not yet run.

## 2026-08-02 — LB-MR01 Phase 1 linked-platform dimensional candidate

- Pro's complete `LB_MR01_SHARED_PLATFORM_BUILD_PACK_v1.0` is preserved under
  `SourceAssets/ReferencePacks/`; its numeric dimensions, pivots, sockets,
  shared-parts matrix, tools, LOD/collision budgets and design sheet are the
  MR01 authority.
- The reproducible builder is
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Blender/build_lb_mr01_linked_blockout_v001.py`.
  It creates
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Blender/Phase_1_Blockout/LB_MR01_LinkedRP01_Blockout_v001.blend`.
- The candidate uses 16 mesh datablocks library-linked directly from RP01 v002
  and creates zero local copies of shared meshes. MR01 repositions instances to
  its authoritative four-corner running-gear layout; it does not copy CR01's
  two-drive-wheel plus caster placement.
- Fresh front, side, top and oblique Blender evidence plus machine-readable
  validation are under
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Phase_1_Blockout/`.
  Visible bounds measure `1550 x 932 x 1250 mm` against the fixed
  `1550 x 930 x 1250 mm` authority and pass its +/-5 mm tolerance.
- Visual status is **DIMENSIONAL BLOCKOUT PASS / NOT PROMOTED**. Production body
  panels, a real six-axis arm, eight-tool magazine, telescoping stabilisers,
  service access, deployable mast, collision, LODs, materials, Unreal assembly
  and runtime evidence remain required.
- Future tow motor, autonomous stillage forklift and low-profile stillage AGV
  remain separate logistics platforms. They may share sensors, warning/HMI
  language, fleet state and dock protocols, but require their own load-rated
  chassis, braking, hitch/fork and safety envelopes after aisle and stillage
  dimensions are fixed.
- User-approved MR01 mobility decision: the maintenance robot is the fast
  breakdown-response unit. Project override
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Data/MR01_GAMEPLAY_MOBILITY_PROFILE_v001.json`
  permits 2.0 m/s only on certified clear emergency routes, derating to 1.2 m/s
  normal transit, 0.6 m/s in occupied/shared aisles, 0.2 m/s at machinery and
  0.1 m/s while docking. Fast mode requires the arm, mast, outriggers, drawers
  and doors fully stowed; safety and route permissives cannot be overridden.

## 2026-08-02 — CR01 silhouette and shared-sensor integration candidates

- CR01 v034 adds a tapered, maintainable service-body silhouette while retaining
  142 true library links to RP01 v002. Fresh Blender evidence is under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v034/Blender/`.
- The v034 audit found two actionable failures: obsolete CR-local depth sensors
  duplicated the RP01 v002 perception suite, and the left vent blades exceeded
  the fixed 980 mm width envelope by 10 mm. Audit evidence is
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v034/LB_CR01_Audit_v034.json`.
- Candidate v035 removes eight obsolete local perception meshes and moves seven
  cosmetic left vent blades 5 mm inward. It does not modify shared RP01 geometry
  or CR01 cleaning mechanisms. Source and evidence are under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v035/` and
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v035/`.
- Visual status remains **ITERATE / NOT PROMOTED**. The side silhouette is much
  closer to the Pro sheet and the front is cleaner, but the body still needs
  mothballed/restored material variants, integrated labels/fasteners, production
  pivots for cleaning equipment, and fresh Unreal fixed-camera/runtime evidence.

## 2026-08-02 — CR01 functional cleaning rig candidate v036

- Audit of v035 proved that its authoritative pivot empties existed but had no
  cleaning meshes parented to them. Candidate v036 corrects the hierarchy for
  the front sweeper lift/spin, twin scrub-deck lift/discs, left/right side-brush
  arms/lifts/spin groups, and rear squeegee lift/yaw while preserving world-space
  geometry and all 142 RP01 v002 library links.
- Reproducible rig builder:
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/rig_lb_cr01_cleaning_components_v036.py`.
  Machine-readable hierarchy evidence:
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v036/LB_CR01_FunctionalRig_v036.json`.
- Fresh deployed-pose renders are under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v036/Blender/`.
  They prove the cleaning assemblies now follow their pivot groups, but side
  brush deployment still needs a clearer visual/readability pass and Unreal
  runtime animation verification. Status is **FUNCTIONAL-RIG CANDIDATE / NOT PROMOTED**.

## 2026-08-02 — CR01 condition and Unreal modular-runtime candidate v038

- Candidate v037 introduced collection-based mothballed/restored condition
  components without duplicating the complete robot. Visual review rejected
  three roof-grime planes that floated above the curved roof. Candidate v038
  removes those invalid decals while preserving the earlier sources for
  comparison. Blender source is
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v038/LB_CR01_ConditionCorrected_v038.blend`.
- The pivot-correct modular export contains 16 separate X-forward/Z-up FBXs at
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v038_ModularRig/`.
  Export evidence is `MODULAR_RIG_EXPORT_VALIDATION.json` in that directory.
- Unreal import/runtime assembly passed for all 16 modules and 11 authoritative
  moving pivots. The validation map and six-second cleaning cycle are
  `/Game/LineBoss/Developer/Validation/LB_CR01_CleaningAMR_ModularRig_v038`
  and
  `/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v038_ModularRig/Sequences/LS_LB_CR01_CleaningCycle_v038`.
  Evidence is `Saved/Audits/lb_cr01_modular_rig_v038.json`.
- UE 5.8 Interchange imported Blender metres as centimetres and ignored its
  reimport uniform-scale setting. This was measured in
  `Saved/Audits/lb_cr01_unreal_bounds_v038.json`: the 1.52 m body arrived as
  1.52 cm. The validation assembly therefore uses absolute x100 root scale on
  each module so attached children do not compound scale. Evidence is
  `Saved/Audits/lb_cr01_actor_scale_v038.json`. A production importer should
  fix this conversion upstream rather than retain the workaround.
- The imported FBX materials were parameterless white material instances.
  Candidate-only Unreal materials now provide a readable charcoal, safety
  yellow, rubber, steel, sensor-glass, dust and oxide palette across 54 mesh
  slots. Evidence is `Saved/Audits/lb_cr01_material_lighting_v038.json`.
- Fresh Unreal evidence is under
  `Saved/ValidationScreenshots/LB_CR01/Candidate_v038/`. It proves correct scale,
  complete visible body geometry and a distinct deployed cleaning pose.
  Visual status remains **UNREAL RUNTIME CANDIDATE / NOT PROMOTED**: compared
  with the Pro reference the body is still too boxy/generic, the mothballed
  surface treatment is weak, and the side-brush operating silhouette is not
  sufficiently clear. Collision/navigation and gameplay-state integration also
  remain open.
- Corporation/factory branding remains undecided. Keep neutral Line Boss and
  functional asset IDs until the user approves a corporate identity; do not
  bake the provisional `Alder Forge Automotive / Greyford Works` names into
  assets.

## 2026-08-02 — obsolete CR01 v004 Press Shop placements removed

- At the user's direction, the two obsolete CR01 Candidate v004 map instances
  and their provisional cube-built service docks were removed from
  `/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005`.
- The guarded Unreal cleanup removed exactly 190 known actors and verified that
  zero matching actors remained before saving. Evidence is
  `Saved/Audits/press_shop_removed_obsolete_cr01_v004_v005.json`.
- Source assets under
  `/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v004` remain preserved
  for comparison and recovery. No cleaner candidate was promoted by this map
  cleanup; CR01 v038 remains a visually rejected runtime candidate pending a
  stronger release-quality rebuild.

## 2026-08-02 — PR-005 dry-cycle and width source correction; build gate blocked

- `LBPR005Station` previously entered `DryCycle` for eight seconds without
  advancing its strip/mandrel motion distance. Source now derives transient
  commissioning travel from dry-cycle elapsed time without adding that travel
  to saveable produced-strip totals or cycle counts.
- Existing asset evidence showed a 1500 mm authored continuous strip and a
  1512 mm authored payoff coil. Those authored widths are now explicit and the
  strip plus payoff-coil presentation scale from the loaded coil width. A new
  `PR005_PayoffCoilMover` component keeps that visual binding modular.
- These changes are **SOURCE CORRECTED / NOT RUNTIME VALIDATED / NOT
  PROMOTED**. UnrealBuildTool cannot currently build Win64 because neither a
  Windows SDK nor Visual Studio C++ Build Tools is installed. Exact evidence is
  `Saved/Audits/pr005_native_build_gate_2026-08-02.json`; UBT requires Windows
  SDK 10.0.19041.0 or newer.

## 2026-08-02 — Cairnwell Automotive identity adopted as internal authority

- The user supplied `CAIRNWELL_AUTOMOTIVE_BRAND_IDENTITY_PACK_v1.0.zip`.
  Its preserved source is
  `SourceAssets/ReferencePacks/CAIRNWELL_AUTOMOTIVE_BRAND_IDENTITY_PACK_v1.0/`.
- Approved internal names are **Cairnwell Automotive** (corporation),
  **Moorcross Works** (site), **U-Series** (vehicle platform) and **The
  Restart** (campaign). These supersede the provisional Alder Forge
  Automotive / Greyford Works names for all new work.
- Exact colours, typography, hierarchy and application rules are recorded in
  `Docs/BRAND_IDENTITY_AUTHORITY.md`. Safety yellow and signal red remain
  functional safety colours, not general corporate decoration.
- Status is **APPROVED INTERNAL DESIGN AUTHORITY / LEGAL CLEARANCE PENDING**.
  Do not claim trademark clearance before formal pre-release checks.
- Branding will first be validated on the shared HMI cabinet and PR-005 asset
  plate. Do not roll it across the factory or promote branded candidates until
  fresh fixed-camera Unreal screenshots prove legibility and placement.

## 2026-08-02 — Cairnwell first application review

- Deterministic SVG and PNG sources are under
  `SourceAssets/Brand/Candidate_v001/`; corresponding Unreal textures and
  materials are isolated under
  `/Game/LineBoss/Brand/Cairnwell/Candidate_v001`.
- The shared-cabinet validation map is
  `/Game/LineBoss/Developer/Validation/LB_HMI04_CairnwellBranding_v001`.
  Fresh evidence is
  `Saved/ValidationScreenshots/Brand/Candidate_v001/cairnwell_hmi_shared_plate_front.png`.
  The Cairnwell plate is upright and legible, but the underlying HMI v004
  cabinet remains materially rough/washed out. Status: **BRAND PLATE VISUALLY
  ACCEPTABLE / CABINET NOT PROMOTED**.
- The PR-005 validation map is
  `/Game/LineBoss/Developer/Validation/LB_PR005_CairnwellBranding_v001`.
  Fresh evidence is
  `Saved/ValidationScreenshots/Brand/Candidate_v001/cairnwell_pr005_asset_plate_hmi.png`.
  A read-only Blender audit established the authored plate face at
  `[-290.5, 280.0, 65.5] cm` in Unreal coordinates. A new 480 x 144 x 12 mm
  bevelled modular carrier was built from the canonical source workflow and
  mounted at `[-290.7, 280.0, 65.5] cm`, with its printed face at X=-292.0 cm.
  Source and export are under
  `SourceAssets/Brand/Candidate_v001/PR005_Plaque/`; measurement evidence is
  `Saved/Audits/pr005_hmi_plaque_source.json` and candidate evidence is
  `Saved/Audits/cairnwell_pr005_plate_candidate_v001.json`.
  The final fixed-camera capture proves correct orientation, readable
  `PR005-DC01` identity and credible fit below the controls. Status:
  **PLAQUE-SPECIFIC VISUAL PASS / MODULE NOT PROMOTED**. The surrounding HMI
  screen, cabinet materials and interaction state still require a separate
  release-quality pass.
- A follow-on source audit found substantial PR-005 station logic in
  `LBPR005Station.h/.cpp` (commissioning, recipe, interlock/fault, dry-cycle,
  motion and save state), but no PR-005 UMG widget, HMI data contract or input
  binding asset. The touchscreen in the fresh capture is therefore genuinely
  black, not merely awaiting a material refresh. Evidence and the required
  first screen scope are in
  `Saved/Audits/pr005_hmi_software_inventory_2026-08-02.json`. The next visual
  candidate is a PR-005 commissioning overview screen; live binding remains
  dependent on restoring the native Windows SDK/C++ build gate.
- UE 5.8 leaked the old world when an unattended process switched between the
  HMI and PR-005 validation maps. Stable automation now launches and captures
  each map in its own Unreal process; retain this one-map-per-process rule.

## 2026-08-02 — Cairnwell pack verification and PR-005 commissioning screen

- The supplied Cairnwell v1.0 zip contains exactly four identity-authority
  files. The preserved copy under `SourceAssets/ReferencePacks/` was hash
  verified against the download; evidence is
  `Saved/Audits/cairnwell_identity_pack_intake_v001.json`. No broad factory
  branding rollout has been authorised by this intake.
- The first deterministic PR-005 commissioning overview is now mounted on the
  exact 340 x 255 mm authored display surface, exported from the original
  Blender HMI with its world transform baked and an 8 mm face-normal standoff.
  This replaces the rejected engine-plane approximation that intersected the
  black display and reconstructed its rotation incorrectly.
- The display mesh is
  `/Game/LineBoss/Brand/Cairnwell/Candidate_v001/PR005_HMI/DisplaySurface_v001/SM_LB_PR005_HMIDisplaySurface_Candidate_v001`.
  The unlit material corrects the source UV orientation by 180 degrees without
  changing physical geometry. Fresh evidence is:
  `Saved/ValidationScreenshots/PR005/HMI/Candidate_v001/pr005_hmi_close.png`
  and
  `Saved/ValidationScreenshots/PR005/HMI/Candidate_v001/pr005_hmi_operator.png`.
- Visual verdict: **STATIC SCREEN VISUAL PASS / HMI MODULE NOT PROMOTED**. The
  close view is upright, fills the bezel, remains readable and follows the
  Cairnwell/Moorcross hierarchy. At operator distance it reads as a credible
  live industrial overview. It is still deterministic artwork, not a live UMG
  screen; station-state binding, input handling, SaveGame integration and
  native runtime validation remain blocked by the missing C++ toolchain.

## 2026-08-02 — PR-005 live-HMI and save-state source contract

- `Content/LineBoss/Data/pr005_hmi_controller_contract_v001.json` now fixes the
  production interface between the shared physical cabinet, the PR-005
  controller and its runtime touchscreen. It defines ten pages, a 24-field
  immutable `FLBPR005HMIStatus` projection, 10 Hz refresh, physical-control
  routing and explicit safety boundaries. The E-stop remains a hardwired input;
  the touchscreen has no software command that can assert it healthy.
- `LBPR005Station` now has OFF/MANUAL/JOG/AUTOMATIC control authority and a
  single guarded `PressCycleStart` entry point. MANUAL may authorise only the
  commissioning dry cycle; AUTOMATIC may start only a certified station. Power
  removal forces OFF/ISOLATED, and reset still requires power, closed guarding
  and a healthy safety circuit.
- `LBPR005HMIWidget.h/.cpp` stages a native Cairnwell 4:3 runtime widget that
  reads only `GetHMIStatus` and routes cabinet actions through controller
  commands. It does not reach into protected station fields or implement a
  software E-stop.
- `FLBPR005SaveState` and `ULBPressShopSaveGame` provide the first explicit,
  versioned campaign-save root. Restoring an interrupted dry cycle, start, run
  or stop returns the station to a stopped state, invalidates the safety reset
  and requires revalidation instead of resuming hidden motion.
- Source audits pass with no failures:
  `Saved/Audits/pr005_hmi_controller_contract_v001.json`,
  `Saved/Audits/pr005_hmi_widget_source_v001.json` and
  `Saved/Audits/pr005_save_source_v001.json`. These are **SOURCE-ONLY PASSES**,
  not compile, UMG, interaction or serialization evidence.
- A fresh UnrealBuildTool run still fails before compilation because Win64 has
  no detected Windows SDK (`10.0.19041.0` or newer required) and no Visual
  Studio C++ toolchain. The updated gate is
  `Saved/Audits/pr005_native_build_gate_2026-08-02.json`. Do not add the native
  module to `LineBossCarFactory.uproject` until that environment is restored,
  otherwise the Blueprint-first project would stop opening.
- Two subsequent unattended API-probe launches failed during Unreal 5.8 engine
  startup before Python execution (RigVM access violation, then a background
  XML/crash-diagnostics array assertion). They changed no assets and provide no
  HMI result. Retain the one-map-per-process rule and avoid repeated startup
  probes until the toolchain/editor environment is repaired.

## 2026-08-03 — integrated PR-004 dormant-lighting correction v006

- Preserved the accepted PR-004 v009 equipment coordinates and the cleaned
  support-robot derivative v005, then created
  `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`.
- The previous full-map evidence gave PR-004 an implausibly saturated blue
  service pool that obscured the coil, robot and safety colours. Six local
  lights within 18 m of the authoritative PR-004 centre were normalised to a
  warm service-light colour and intensity-capped; no machine, fence, gate,
  floor or camera transform changed. Technical evidence:
  `Saved/Audits/press_shop_pr004_lighting_v006.json`.
- Fresh fixed-camera evidence is under
  `Saved/ValidationScreenshots/PressShopIntegration/v006_pr004_lighting/`:
  `press_shop_v006_pr004.png`, `press_shop_v006_front_end.png` and
  `press_shop_v006_whole.png`.
- Visual verdict: **LOCAL LIGHTING PASS / PR-004 STILL ITERATE**. The integrated
  cell now reads as a controlled dormant-service/commissioning pool; safety
  yellow, open-mesh guarding, steel coil, cradle and robot silhouette are
  materially separable, while PR-003 remains dark. PR-004 is not promoted:
  machine surfaces remain too clean/flat against the Pro reference, the robot
  dressing and tool/inspection hardware need a final detail pass, and the
  whole-shop view truthfully exposes large empty downstream areas. Review:
  `Saved/Audits/press_shop_pr004_lighting_visual_review_v006.json`.
- The Unreal run completed with 0 commandlet errors/warnings for the map edit
  and all three screenshots were freshly written. This is not a packaged
  runtime gate; Win64 SDK/C++ toolchain validation remains unavailable.

## 2026-08-03 — Cairnwell identity intake and PR-004 material experiment v007

- Preserved the supplied Cairnwell identity authority at
  `SourceAssets/ReferencePacks/CAIRNWELL_AUTOMOTIVE_BRAND_IDENTITY_PACK_v1.0/`.
  Source integrity, hashes and the non-promotion decision are recorded in
  `Saved/Audits/cairnwell_identity_pack_intake_v001.json`. The game title
  remains **Line Boss: Car Factory**; Cairnwell Automotive is the in-world
  corporation, Moorcross Works is the site, U-Series is the vehicle family and
  The Restart is the campaign. Legal clearance remains pending.
- The first Cairnwell PR-005 HMI artwork remains a static visual candidate; it
  does not constitute live UMG/runtime integration.
- Created a non-destructive material experiment in
  `/Game/LineBoss/Maps/LB_PressShop_PR004MaterialCandidate_v007`. It duplicates
  the accepted v006 integration baseline and applies restrained PBR actor
  overrides to all 28 `robot_v002` modules. Source meshes, pivots, layout and
  transforms are unchanged. Technical audit:
  `Saved/Audits/press_shop_pr004_robot_material_candidate_v007.json`.
- Fresh fixed-camera evidence is under
  `Saved/ValidationScreenshots/PressShopIntegration/v007_pr004_material/`:
  `press_shop_v007_pr004.png`, `press_shop_v007_front_end.png` and
  `press_shop_v007_whole.png`.
- Visual verdict: **TECHNICAL PASS / VISUAL REJECT / NOT PROMOTED**. The close
  surface breakup is coherent but too subtle, and it is effectively invisible
  at the intended management camera. Preserve v007 only as comparison evidence
  and retain v006 as the current integration baseline. The next useful pass is
  authored robot dressing and seven-year wear masks/decals, followed by release
  collision and the same fixed-camera gate. Review:
  `Saved/Audits/press_shop_pr004_robot_material_visual_review_v007.json`.

## 2026-08-03 — PR-004 authored-condition experiment v008

- Inspected the complete `robot_v002` Blender source before changing it. Its 28
  modules already contain detailed joints, fasteners, motors, service hardware,
  dress packs, tool changer and four tool families; rebuilding these would
  duplicate good source work. The visible deficiency is authored condition.
- Built non-destructive derivative map
  `/Game/LineBoss/Maps/LB_PressShop_PR004MothballedCandidate_v008b` with 18
  functionally grouped condition materials across all 28 robot modules. Source
  geometry, layout and pivots remain unchanged. Technical evidence:
  `Saved/Audits/press_shop_pr004_mothballed_candidate_v008.json`.
- Fresh evidence is in
  `Saved/ValidationScreenshots/PressShopIntegration/v008_pr004_mothballed/`.
  Verdict: **VISUAL REJECT / NOT PROMOTED**. The new close camera is misframed,
  and the stronger material treatment makes the arm pale beige under the local
  lights instead of credibly aged safety yellow. Retain v006 as baseline.
- Next pass: author mesh/UV-specific wear masks or decals for paint loss,
  grease, dust and fastener oxidation; repair the close camera from a known
  valid PR-004 transform before review. Release collision and runtime motion /
  interlock validation remain open. Review:
  `Saved/Audits/press_shop_pr004_mothballed_visual_review_v008.json`.

## 2026-08-03 — PR-004 authored slots and deterministic safety-paint tests v009-v010

- Audited the integrated robot material bindings and found that Blender's
  authored `EdgeWear`, `WarningLabel`, hydraulic-ID and residue slots had been
  consolidated into generic Unreal materials. This hid useful source detail;
  the 28-module robot geometry itself does not require a blind rebuild.
- Created non-destructive authored-slot map
  `/Game/LineBoss/Maps/LB_PressShop_PR004AuthoredDetailsCandidate_v009`, then
  deterministic safety-paint derivative
  `/Game/LineBoss/Maps/LB_PressShop_PR004SafetyPaintCandidate_v010`. The latter
  changes only the 13 source slots explicitly named `SafetyOchre` or
  `SafetyYellow`; geometry, layout and pivots are preserved. Technical audit:
  `Saved/Audits/press_shop_pr004_safety_paint_candidate_v010.json`.
- Fresh fixed-camera evidence is under
  `Saved/ValidationScreenshots/PressShopIntegration/v010_pr004_safety_paint/`.
  Verdict: **TECHNICAL PASS / VISUAL REJECT / NOT PROMOTED**. The robot is no
  longer pale cream, but the deterministic paint reads as clean saturated
  orange rather than aged RAL 1023 safety yellow. Robot and station surfaces
  remain too flat, the PR-003 coil store still reads as placeholder art, and
  the bright sparse cell does not yet communicate seven years dormant.
- Keep `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006` as the
  accepted integration baseline. Review:
  `Saved/Audits/press_shop_pr004_safety_paint_visual_review_v010.json`.
- Cairnwell identity source remains preserved at
  `SourceAssets/ReferencePacks/CAIRNWELL_AUTOMOTIVE_BRAND_IDENTITY_PACK_v1.0/`.
  Its safety yellow (`#F2C300`, approximate RAL 1023) is the colour authority
  for the next layered paint pass. Cairnwell is internal art authority only;
  formal trademark/design clearance remains required before public release.

## 2026-08-03 — new-chat continuity handover

- Created `Docs/NEW_CHAT_HANDOVER_2026-08-03.md` with the canonical repository
  rule, current v006 baseline, rejected v007-v010 decisions, tool paths,
  evidence locations, Cairnwell authority, release blockers and exact next
  actions. This is a continuity document, not a promotion or completion claim.
- Generated candidate derivative
  `SourceAssets/Brand/Cairnwell/Textures/T_Cairnwell_PrimaryLogo_2400x640.png`
  from the preserved SVG and visually inspected it. It has not yet been
  imported, placed or promoted; the supplied SVG remains authoritative.

## 2026-08-03 — Cairnwell logo candidate v002 and PR-004 layered-material v011 rejection

- Read `Docs/NEW_CHAT_HANDOVER_2026-08-03.md` and this handoff completely before
  resuming. The accepted integration baseline remains
  `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`; rejected
  v007–v010 maps were neither promoted nor used as a replacement baseline.
- Verified the derived Cairnwell primary-logo PNG at exactly `2400 x 640`,
  32-bit ARGB with transparency, 46,256 bytes and SHA-256
  `21e05a1043d19a3c452168ceee7e891451a562fe99b545a4d5d62f8708afad94`.
  Provenance and legal status are recorded in
  `SourceAssets/Brand/Cairnwell/cairnwell_primary_logo_candidate_v001_manifest.json`.
- Imported the logo non-destructively under
  `/Game/LineBoss/Brand/Cairnwell/Candidate_v002` and created reusable opaque
  surface and alpha-masked material candidates. Audit:
  `Saved/Audits/cairnwell_primary_logo_unreal_candidate_v002.json`. No map
  placement or factory-wide rollout was performed. Status remains **UNREAL
  ASSET CANDIDATE / NOT PROMOTED / LEGAL CLEARANCE PENDING**.
- Built populated derivative
  `/Game/LineBoss/Maps/LB_PressShop_PR004LayeredMaterialCandidate_v011` directly
  from v006. It preserves all geometry, layout and pivots, resolves all 28
  robot modules and applies 172 exact audited slot overrides, including
  Cairnwell `#F2C300` safety-paint authority plus authored edge-wear, grease,
  hydraulic-ID, service-label and warning-label identities. Technical evidence:
  `Saved/Audits/press_shop_pr004_layered_material_candidate_v011.json`.
- Fresh detail, cell and front-end screenshots are under
  `Saved/ValidationScreenshots/PressShopIntegration/v011_pr004_layered_material/`.
  Visual verdict: **TECHNICAL PASS / VISUAL REJECT / NOT PROMOTED**. Under the
  accepted v006 lighting the robot still reads pale beige/white, the detail
  camera is too tightly cropped, the material change is effectively invisible
  at management distance, and the cell remains far sparser than revised Pro
  Sheet 3. Seven-year dust/weeping/oxidation/service witnesses are not a
  coherent readable condition story. Review:
  `Saved/Audits/press_shop_pr004_layered_material_visual_review_v011.json`.
- Retain v006 as baseline. The next material pass requires a paint-specific
  master rather than inherited tint-times-vendor-base response, mesh/UV-specific
  wear masks or decals, and a wider complete-robot detail camera. Release
  collision, motion/swept-volume, interlocks, HMI/save-state and native/package
  runtime gates remain open.
## 2026-08-03 — PR-004 paint-response v012 and aged-dust v013 review

- Preserved `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006` as the accepted PR-004 integration baseline. Rejected candidates v007-v010 remain rejected; v011-v013 are not promoted.
- Built `/Game/LineBoss/Maps/LB_PressShop_PR004PaintSpecificCandidate_v012` from the accepted v006 lineage to isolate safety-paint response from vendor base-color multiplication. Technical/content generation passed and fresh fixed-camera evidence confirmed a complete robot silhouette, but the result was over-bright, uniform and newly sprayed. Verdict: `PAINT_CHROMA_PASS__CONDITION_VISUAL_FAIL__NOT_PROMOTED`.
- Built `/Game/LineBoss/Maps/LB_PressShop_PR004AgedDustCandidate_v013` as a tightly scoped material-only follow-up. It tones the paint, raises roughness and adds upward-facing dust modulation while preserving all accepted geometry, pivots, module transforms and non-target bindings.
- Fresh v013 fixed-camera evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v013_pr004_aged_dust/`. Compared with v012, the safety paint is less neon and less highlight-clipped, but the wear remains too subtle at management distance and the cell still lacks the equipment density, operator/HMI presence and coherent seven-year condition story visible in the Pro Sheet 3 reference.
- v013 verdict: `PAINT_RESPONSE_IMPROVEMENT__OVERALL_VISUAL_ITERATE__NOT_PROMOTED`. Retain it only as the best current authored safety-paint comparison; it does not replace v006.
- Audit records:
  - `Saved/Audits/press_shop_pr004_paint_specific_candidate_v012.json`
  - `Saved/Audits/press_shop_pr004_paint_specific_visual_review_v012.json`
  - `Saved/Audits/press_shop_pr004_aged_dust_candidate_v013.json`
  - `Saved/Audits/press_shop_pr004_aged_dust_visual_review_v013.json`
- Next PR-004 material step: stop tuning whole-material constants. Add mesh/UV-specific condition masks or decals for hydraulic weeping, oxidized fasteners, faded labels, serviced witness marks and contact wear, alongside the missing Pro-reference cell equipment, then repeat the fixed-camera gate.
- Native Win64 build, collision/runtime interaction, HMI, save-state and gameplay gates remain unavailable until the local Windows SDK/MSVC toolchain is installed. Unreal Python/content generation and fresh rendered visual checks remain operational.

## 2026-08-03 — PR-004 band-tool attachment correction v014

- User visual review correctly identified that the band tool was not properly seated on the robot. Source inspection found the cause in `Scripts/pose_pr004_candidate_v009_band_tool.py`: the evidence pose deliberately kept a 35 cm separation between the quick-changer datum and tool-body datum.
- Built `/Game/LineBoss/Maps/LB_PressShop_PR004ToolAttachmentCandidate_v014` directly from accepted v006. The complete six-actor band-tool assembly was translated by `[35, 0, 0]` cm as one rigid group. The tool datum moved from `[-5289, -1965, 220]` to `[-5254, -1965, 220]`, exactly matching the quick-changer datum. No non-tool transforms or mesh geometry changed.
- Fresh close and cell evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v014_pr004_tool_attachment/`. Static visual verdict: `PASS_TOOL_SEATED_ON_QUICK_CHANGER`.
- v014 is retained as the corrected attachment candidate but is **not promoted**. The tool modules are still independent actors; release acceptance requires a verified runtime attachment hierarchy, tool-lock/presence interlocks and articulated swept-collision checks against the coil, cradle, guarding and robot body.
- Audit records:
  - `Saved/Audits/press_shop_pr004_tool_attachment_source_v014.json`
  - `Saved/Audits/press_shop_pr004_tool_attachment_candidate_v014.json`
  - `Saved/Audits/press_shop_pr004_tool_attachment_visual_review_v014.json`
- Accepted integration baseline remains `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`.

## 2026-08-03 — Reusable modular robot architecture v002 and PR-004 integration v016

- User chose to make the PR-004 robot reusable across compatible factory cells rather than creating bespoke copies. Engineering reuse envelope: 400 kg rated payload, 350 cm working radius and the documented six-axis quick-changer interface. A different robot family is warranted only when payload, reach, environment or process geometry materially differs.
- Added reusable source contract `SourceAssets/PR004/RoboticDepackRobot/LB_Modular6AxisRobot_ReusableContract_v002.json`.
- Built candidate robot core `/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v002/BP_LB_Modular6AxisRobot_400kg_v002` with the J1-J6 component hierarchy, quick-changer, dress-pack previews, `ToolMount` and replaceable `EquippedTool` child component.
- Built four interchangeable candidate tool Blueprints under `/Game/LineBoss/Equipment/Robots/Modular6Axis/Candidate_v002/Tools`: Band Cutter/Capture, Wrap Peeler/Vacuum, Edge Protector Gripper and Label/RFID Inspection. Band-tool child offsets use the visually verified working pose rather than the earlier rack-preview spacing.
- Built `/Game/LineBoss/Maps/LB_PressShop_PR004ReusableRobotCandidate_v016` from corrected v014. It replaces 18 loose robot/band-tool actors with one reusable Blueprint instance while preserving the guarded rack and three unselected tools.
- The v015 map hierarchy probe passed parent propagation for the band tool and all five moving children after converting them to Movable; the rest pose was restored before save. This is editor-component evidence, not a substitute for gameplay/runtime interlock testing.
- Fresh v016 close and cell screenshots in `Saved/ValidationScreenshots/PressShopIntegration/v016_pr004_reusable_robot/` reproduce v014 without visible pivot drift, missing modules or tool separation. Verdict: `REUSABLE_COMPOSITION_EQUIVALENCE_PASS__OVERALL_RELEASE_GATES_OPEN__NOT_PROMOTED`.
- Reusable architecture direction is accepted for continued development, but neither the Blueprint assets nor v016 are promoted. Open gates: instance variables/state, joint animation/limits, tool-change state machine and interlocks, release collision and swept volumes, save/load, condition materials and full Pro-reference visual density.
- Audits:
  - `Saved/Audits/press_shop_pr004_tool_hierarchy_candidate_v015.json`
  - `Saved/Audits/reusable_modular_robot_blueprints_v002.json`
  - `Saved/Audits/press_shop_pr004_reusable_robot_candidate_v016.json`
  - `Saved/Audits/press_shop_pr004_reusable_robot_visual_review_v016.json`
- Accepted integration baseline remains `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`; v016 is the active reusable-robot development candidate only.

## 2026-08-03 — Cairnwell internal project-use authorization clarified

- The user confirmed that Cairnwell is a fictional identity made with Pro for Line Boss (`"its made up by pro"`). Record: `Saved/Audits/cairnwell_user_authorization_2026-08-03.json`.
- Internal use of the Cairnwell name and supplied identity assets in Line Boss is user-authorized. This removes the previous internal project-use hold.
- No claim is made here about registered trademark status, exclusivity or territory-specific conflict clearance; those remain optional external release/business checks.
- Branding assets still require the normal technical and fresh fixed-camera visual gates. User authorization does not itself promote any logo, plaque, HMI treatment or map placement.

## 2026-08-03 — v020 Surface Forge/UE 5.8 checkpoint and BIOS maintenance pause

- Built an isolated v020 reusable-robot candidate from the accepted v016
  composition while retaining v006 as the accepted overall PR-004 integration
  baseline. No rejected map was promoted.
- v020 contains 27 duplicated robot/tool meshes processed with UE 5.8 Geometry
  Script repair/compact operations, candidate simple convex collision on each
  duplicate, four reusable tool Blueprints, a lightweight material using only
  the three selectively copied Surface Forge Metal Paint Chips PBR textures,
  35 semantic CastIron-only overrides, and deterministic Cairnwell plate
  assets. Build audit:
  `Saved/Audits/press_shop_pr004_surfaceforge_robot_candidate_v020.json`.
- A log gate found that UE 5.8 interpreted the builder's `float` Blueprint pin
  requests as integers. v020 is therefore not technically accepted and no
  visual promotion review has occurred. The builder now uses `real`; the exact
  generated core/map rebuild script is ready at
  `Scripts/rebuild_press_shop_pr004_surfaceforge_robot_real_state_v020.py` but
  was not run before reboot.
- Unreal work was paused at the user's request to update an ASUS Z790-F / Intel
  i9-14900K system from BIOS 2402 and microcode 0x125 to verified ASUS BIOS
  3201. Full restart state, firmware hashes and resume order are recorded in
  `Docs/REBOOT_CHECKPOINT_2026-08-03.md`.
- v020 status at pause: **GENERATED CANDIDATE / NUMERIC STATE REBUILD PENDING /
  RUNTIME AND FRESH FIXED-CAMERA GATES OPEN / NOT PROMOTED**.

## 2026-08-03 — ASUS BIOS 3201 maintenance verification

- The user completed the ASUS EZ Flash update and loaded BIOS defaults after
  the update. A fresh Windows read-back at 08:35 Europe/London verified BIOS
  `3201`, BIOS date `2026-01-15`, and a fresh boot at `08:33:35`.
- The Intel Core i9-14900K now reports live microcode bytes `2F 01 00 00`,
  revision `0x12F`, satisfying the planned firmware/microcode gate.
- DDR5 is configured at the safe default `4800 MHz`. No WHEA-Logger events or
  Windows bugchecks were recorded between the fresh boot and verification.
- The firmware gate is **PASS**. Unreal remains paused until the motherboard's
  built-in MemTest86 gate is completed and recorded. This maintenance result
  does not alter any Unreal candidate or promotion decision.

## 2026-08-03 - RP01/CR01/MR01 intake, architecture gate and v001 runtime rejection

- Development resumed after the firmware pass; MemTest86 remains a separate
  overnight hardware gate. The accepted overall PR-004 integration baseline is
  still `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`.
  Rejected v007-v010 candidates remain rejected and v020 remains an unpromoted
  robot-development candidate.
- Verified the complete known CR01, MR01, RP01/Cairnwell and Pro-reference
  extracted content in the canonical repository. Evidence:
  `Saved/Audits/pro_reference_pack_inventory_2026-08-03.json`. Raw ZIP files
  are not project dependencies; the preserved extracted files and hashes are
  the intake authority. Fab content remains in VaultCache unless a specific,
  licensed asset is selectively imported into the candidate namespace.
- Built the reusable, data-only RP01 Pawn candidate at
  `/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase`.
  It has one scene root, 23 anchors, 19 typed instance fields, 47 visual
  bindings and seven material bindings. A fresh NullRHI compile/currentness,
  hierarchy, type and reload audit passed with MapCheck 0 errors and 0
  warnings: `Saved/Audits/lb_rp01_mobile_base_candidate_v001_independent.json`.
  This is an architecture-only pass. Simple collision count is zero and
  runtime movement, navigation, docking, battery/fault behaviour, SaveGame and
  fixed-camera visual gates remain open. It is not promoted.
- CR01 Candidate v040 now has a more credible rounded enclosure and a readable,
  seated Cairnwell/Line Boss/CR01-001 plate. It is still too clean and blocky
  against the Pro reference and lacks a complete deployed-cleaning proof,
  release materials, collision, LOD, Unreal runtime and fresh Unreal cameras.
  MR01 Phase 2 v006 proves a four-outrigger, telescoping-mast and rigid six-axis
  hierarchy only; its body, arm and T1-T8 tools remain placeholder quality.
  The 5-degree J2/J3 visual offsets and derived 90-degree outrigger foot yaw are
  unapproved deviations and must not be silently promoted.
- Independent review rejected the first staged native runtime draft. The old
  token audit could match safety vocabulary without proving behaviour. Critical
  defects include fault-clear deadlocks, caller-forgeable route/dock authority,
  blind transform/task/permit restoration, incomplete dynamic arm interlocks,
  unproved outrigger loads, CR01 route completion with cleaning systems still
  active, non-finite input holes, and multiple pack numeric/timing mismatches.
  `Scripts/validate_support_robot_runtime_source_v001.py` and
  `Saved/Audits/support_robot_runtime_source_v001.json` now record
  `SOURCE_CONTRACT_REJECTED__SAFETY_ARCHITECTURE_SUPERSEDED`, with
  `promotion_authorized=false` and `all_checks_pass=false`.
- Keep `LBSupportRobot*`, `LBCleaningAMR*` and `LBMaintenanceAMR*` dormant for
  traceability. Do not register them, do not enable a project source module and
  do not reparent the accepted RP01 Pawn. The approved replacement direction is
  a disabled-by-default runtime plugin/component attached to the data-only Pawn.
  It must own no geometry or root, resolve pack anchors by stable names/tags,
  consume route/dock proof only from trusted world services, continuously
  monitor interlocks, reject non-finite values, and restore in a stopped state
  with tasks, permits and sensor proof cleared. Saved transforms may be used
  only after explicit world/nav/collision validation; blind teleport is banned.
- The `.uproject` remains Blueprint-only with no Modules array. Local UE 5.8
  requires a supported Windows SDK and VS2022 C++ toolchain, but neither is
  installed. Obtain explicit user approval before the system-wide Build Tools
  installation, then run isolated UHT/compile/runtime gates before enabling any
  plugin or native module.
- Shared-anchor authority conflict remains open: CR01/RP01 define
  `SCK_Audio_Warning` at Z=850 mm while the MR01 pack also calls Z=950 mm
  exact-shared. Keep RP01 at the CR/RP authority and do not let an MR01 child
  silently mutate the shared socket.

## 2026-08-03 - CR01 v042, MR01 v012 and shared robot-paint review

- CR01 Candidate v042 is preserved under
  `SourceAssets/Robots/LB_CR01_CleaningAMR`. Its payload-only export contains
  24 FBXs covering M07-M25 plus condition overlays, with zero shared RP01 mesh
  sources. Fresh source/reimport audits pass hierarchy, units, +X metadata and
  composition boundaries. This is useful technical evidence only.
- Independent visual review is **REWORK / QUARANTINED TECHNICAL IMPORT ONLY**.
  The model remains boxy and toy-like against the Pro reference, brush media
  and lift/guard/hose/vacuum details are under-resolved, M20 and M25 are still
  declared nulls, and no release condition materials or Unreal cameras exist.
  The exact published M09/M10 +/-65 degree range reaches a best stowed width of
  1,252.6377 mm and exceeds the allowed 985 mm maximum by 267.6377 mm. No
  unauthorized range change is accepted. Candidate v043 is developing a
  carrier-contained inboard stow mechanism while retaining the published arm
  range and +/-500 mm deployed brush centres.
- The v042 1,350 mm deployed claim must be treated as a nominal swept-disc
  result, not a snapshot-bounds pass. Earlier evidence measured 1,332.6132 mm
  at +/-22.5 degree spin and later measured 1,350 mm at +/-90 degree spin with
  unchanged arm/lift pose. Unreal validation must sample a full rotation or
  use analytic 350 mm swept discs so brush phase cannot affect the result.
- MR01 Candidate v012 is preserved under
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot`. Its fresh-reopen data verifies
  the 1,550 x 930 x 1,251.433 mm travel envelope, exact J2 -35/J3 130 stow,
  rigid arm weighting, four-stage mast, four outriggers and eight distinct tool
  classes. Independent visual verdict is **REWORK**: the pale procedural body,
  thin arm/dress pack, weak stabilizer and cradle load paths, primitive tools,
  concealed carousel and crossed Cairnwell plate remain far below the Pro
  sheet. No Candidate_v012 interchange export exists, so the unversioned pack
  import script must not be run. Any future technical import must use a hashed
  deterministic export and isolated candidate namespace.
- Shared robot-paint Candidate v001 is formally superseded/rejected. A fresh
  D3D12 screenshot exposed default-material fallback, and its log recorded
  virtual-texture sampler mismatches plus three missing OneMinus inputs. The
  preserved v001 files remain evidence and are not to be bound to robots.
- Corrected shared robot-paint Candidate v002 is under
  `/Game/LineBoss/Robots/Shared/Materials/Candidate_v002`. It uses the required
  virtual samplers and valid OneMinus inputs. The fresh fixed-camera v003 map
  and screenshot compile without those failure patterns and visibly separate
  charcoal, Cairnwell green, safety yellow and service grey in mothballed and
  restored states. Swatch gate passes, but the chip/normal response is too
  coarse for automatic acceptance and must be tuned on actual robot panels.
  Audit:
  `Saved/Audits/lb_support_robot_shared_materials_candidate_v002_visual_review.json`.
- No asset in this section is promoted. The overall accepted PR-004 integration
  baseline remains `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`.

## 2026-08-03 - Diegetic branding boundary clarified

- The user explicitly clarified that **Line Boss is only the working title of
  the game**. It is not the corporation, factory or equipment brand and must not
  appear diegetically on robots, machinery, buildings, HMI identity plates or
  factory signage.
- In-world identity uses Cairnwell Automotive / Moorcross Works, equipment IDs
  such as `CR-01` or `MR-01`, and appropriate safety/service/warning markings.
  Internal Unreal package and project filenames may retain `LineBoss` as
  non-diegetic project metadata.
- Any `LINE BOSS` wording shown on a Pro reference sheet is non-authoritative
  placeholder/layout text. Continue using those sheets for silhouette,
  dimensions, mechanisms, materials and camera comparison, but do not reproduce
  that wording on production assets.
- The older CR01 v040 plate containing Cairnwell / Line Boss / CR01-001 is now
  specifically rejected for branding scope in addition to its existing visual
  rework status. CR01 v043 and MR01 v013 were instructed to use Cairnwell and
  functional asset/safety markings only.

## 2026-08-03 - Robot v043/v013 and disabled runtime v2c4 current state

- Continue only from accepted map
  `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`; v007-v010
  remain rejected and nothing below changes that promotion baseline.
- CR01 v043 source SHA-256 is
  `AF633C0E228813E93F3DD3CE7D6DA4C140366DB38C1B5D9F4C5A3732416ABFC3`.
  Deterministic payload export, hierarchy, UV/material coverage, authoritative
  45 L hopper/filter geometry, 980 +/-5 mm stow and 1,350 mm analytic sweep pass
  source engineering. Visual gate is **REWORK / NOT PROMOTED** because the
  body, sensors, panels, materials, cleaning-hardware presentation and
  stow/deploy readability remain below the Pro reference. Do not import this
  candidate into Unreal.
- MR01 v013 source SHA-256 is
  `BD66622C80A16ECEAF8B2E8B82DB53E3A690FC9A7EB2DBB286573FADF57617E9`.
  Source/reimport/export engineering passes. All retained MR01 design sheets
  are byte-identical (SHA-256
  `A5860F7C4BD12387AE7D66EF45F3E9D2C1D1150020B83FB426CA4A6B292CCD02`),
  and the pack engineering authority requires exactly four independently
  driven corner modules. v013 already uses exactly four linked RP01 wheel/hub
  modules at X +/-500 mm, Y +/-405 mm, so the wheel layout is locked and is not
  being changed. Local guards/brackets do not replace or duplicate the shared
  drive modules.
- MR01 visual gate remains **REWORK / NOT PROMOTED**. Boxy upper works, a
  working arm buried too low and reading undersized inside bulky casing, primitive mast/sensors/lights, oversized
  bumpers/pods, weak rear/service detail, generic tools, coarse materials and
  an unconvincing seven-year mothballed layer all require source rework before
  Unreal import. Record:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v013/LB_MR01_RuggedExportCandidate_v013_VISUAL_REVIEW.json`.
- The installed VS2022 17.14.37 / MSVC 14.44.35228 / Windows SDK 10.0.22621
  toolchain supersedes the earlier toolchain-absent note. Disabled plugin
  `Plugins/LineBossSupportRobotsRuntimeV002` passes isolated UHT, editor
  Development, game Development and game Shipping builds in package `B/V2C4`.
  Evidence: `Saved/Audits/lb_support_robot_runtime_v002_build_v2c4.json` and
  `Saved/Audits/lb_support_robot_runtime_v002_source_audit.json`.
- The runtime plugin remains disabled by default, absent from the `.uproject`
  and unpromoted. Production authority providers, CR resource/coverage
  progression, provider-owned task modes, MR exceptional parking proof,
  canonical Blueprint binding, runtime movement/navigation, simple collision,
  fault injection, save round-trip and fresh fixed-camera Unreal/Pro visual
  gates remain open. Neither robot candidate may be promoted merely because
  source or compile tests pass.
- Cairnwell Automotive / Moorcross Works remains the diegetic identity.
  `Line Boss` remains project/game-title metadata only and must not appear on
  in-world robots, factory assets, HMIs or signage.

### MR01 v014 visual rework decision

- MR01 v014 source SHA-256 is
  `F519927D3B31AC1B746A2B77C5D43CA985782718B0BD501B21BC39342F3143D9`.
  Its independent continuity audit confirms four unchanged linked RP01 wheels
  and four unchanged linked RP01 hubs, Cairnwell identity and no diegetic
  working-title text. Audit:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v014/LB_MR01_VisualReworkCandidate_v014_INDEPENDENT_AUDIT.json`.
- Fresh Blender renders show useful improvement to bumper/pod scale, mast head,
  sensing fascia, side access and rear service detail. Visual result remains
  **REWORK / NOT PROMOTED / NO UNREAL IMPORT** because the arm is too low and
  visually undersized inside bulky casing, while the arm/cradle integration,
  upper-rear body mass, bumper integration, local wheel-module presentation,
  material finish and mothballed condition remain below the Pro reference.
  Review:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v014/LB_MR01_VisualReworkCandidate_v014_VISUAL_REVIEW.json`.

## 2026-08-03 - CR01 cleaner visual rework v044-v048

- Cleaner v043 remains the last full deterministic payload-export engineering
  candidate. Source-only v044-v048 branches improve its visible release design
  without changing linked RP01 content or published cleaning pivots.
- v044 established the retained direction: graphite powder-coated enclosure,
  restrained yellow replaceable wear guards, recessed sensor/work-light face,
  protected roof LiDAR, service louvres/latches, rear markers and Cairnwell /
  CR01-001 diegetic identity. `Line Boss` remains absent from the robot.
- v045 made deployed brushes legible but was rejected because the bristles read
  as coarse rectangular paddles and the front roller retained a cage silhouette.
  v046 shortened and densified the front fibres and thinned the side clusters.
  Its independent audit then correctly rejected excess Y/Z and wrong-axis fibre
  bounds. v047 restored the full travel envelope; v048 tapers side bundles and
  uses a dense fibrous roller material without detached geometry.
- Latest source:
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v048/LB_CR01_TaperedBrushCandidate_v048.blend`,
  SHA-256
  `22167D94D1A43C194797FDD4018DE7BF850131C0DF158BB91F9002058DE85B08`.
  Build audit verifies linked RP01 and pivot continuity, 984.64 mm stowed width,
  Y +/-760 mm, Z max 1120 mm and 1349.207 mm deployed sweep.
- Fresh fixed Blender evidence is under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Validation/Candidate_v048/Blender`.
  Manual Pro comparison rejects v048: side fibres remain too rigid/even, the
  front roller silhouette is perfectly smooth and some enclosure/bumper forms
  remain simplified. Status is **REWORK / NOT PROMOTED / NO UNREAL IMPORT**. A
  final authored brush/surface pass is required before
  any isolated Unreal import, collision, navigation, save or camera gate.

## 2026-08-03 - disabled support-robot runtime v2c5

- Isolated strict native package `B/V2C5` passes UHT plus UnrealEditor
  Development, UnrealGame Development and UnrealGame Shipping using VS
  17.14.37 / MSVC 14.44.35228 / Windows SDK 10.0.22621, with strict includes,
  no PCH/shared PCH and unity disabled. DLL SHA-256 is
  `58C91A603ECB266744186187BA58617ADB5E7F60C34794E75B0F625C2248F72C`.
- Evidence:
  `Saved/Audits/lb_support_robot_runtime_v002_build_v2c5.json` and
  `Saved/Audits/lb_support_robot_runtime_v002_source_audit.json`; the source
  audit reports 27 checks and zero failures.
- CR01 cleaning mode and process progression are now provider-owned through
  trusted task grants and monotonic measured samples. Replay, non-finite,
  capacity and speed/swath implausibility revoke/safe-stop with
  `ProcessAuthorityFault`. This closes the caller-forgeable process-input source
  gap only. No production provider, Blueprint binding, runtime movement,
  collision/navigation, fault-injection, disk save or fixed-camera Unreal proof
  exists. The plugin remains disabled, absent from the `.uproject` and
  unpromoted.

## 2026-08-03 - CR01 v052/v053 Unreal gate decision

- Candidate v052 completed deterministic modular export and clean factory-empty
  Blender reimport validation for all 24 payload FBXs. Isolated Unreal import,
  Blueprint compile/assembly, 96 shared material bindings and authored collision
  proxy construction passed their technical audits.
- Fresh fixed-camera Unreal evidence rejected v052. The reusable RP01 v001 base
  had doubled wheel/caster/dock transforms beneath its anchors, producing
  detached running gear and severe lower-platform clipping. v052 is therefore
  preserved but **REJECTED / NOT PROMOTED**.
- Reusable parent candidate RP01 v002 fixes the anchor compensation without
  modifying v001. CR01 v053 reparents the unchanged v052 cleaner payload and
  collision set to RP01 v002. A fresh reload/compile audit passes and new fixed
  cameras confirm that wheel/caster/dock alignment is materially improved.
- v053 remains **REWORK / NOT PROMOTED** after manual Pro-reference comparison.
  Open visual defects are weak Cairnwell/CR01 legibility, over-coarse surface
  response, excessive pale bumper/roof/wheel-centre contrast, a slab-sided and
  top-heavy enclosure, and insufficient mothballed/restored separation. Runtime
  deployed-swath, navigation, fault, save/reload and production-provider gates
  are also still open.
- Key evidence:
  `Saved/Audits/lb_cr01_candidate_v052_unreal_technical_independent.json`,
  `Saved/Audits/lb_cr01_candidate_v052_collision_build.json`,
  `Saved/Audits/lb_cr01_candidate_v052_unreal_visual_review.json`,
  `Saved/Audits/lb_rp01_mobile_base_candidate_v002_build.json`,
  `Saved/Audits/lb_cr01_candidate_v053_unreal_technical_independent.json`,
  `Saved/Audits/lb_cr01_candidate_v053_unreal_visual_review.json`, and
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v053_CorrectedParentVisual`.
  The accepted PR-004 integration map remains v006 and was not modified.

## 2026-08-03 - CR01 v054-v056 material/identity gate

- Reusable shared paint Candidate v003 and RP01 v003 replace the coarse v053
  surface response while retaining the accepted anchor correction. CR01 v054
  passes fresh technical reload/compile checks but its joined-FBX wordmark is
  depth-occluded in Unreal.
- CR01 v055 adds two source-coordinate-seated identity plaques with readable
  Cairnwell / CR-01 001 / Moorcross Works diegetic text. CR01 v056 then separates
  20 structural light-metal/warm-white slots from that lettering and binds them
  to restrained service grey. No Line Boss in-world branding is present.
- v056 fresh technical evidence passes: 24 preserved payload meshes, 19 moving
  child stages, 47 inherited RP01 visuals, 96 effective payload material slots,
  58 Candidate v003 paint bindings and no default-material failures.
- Six fresh fixed cameras were manually compared with the Pro sheet. The
  material/identity direction is accepted for continued development, but v056
  remains **REWORK / NOT PROMOTED** because the front impact bar is still too
  pale, the enclosure remains simplified/slab-sided and deployed-cleaning,
  navigation and save/reload proof remains open.
- CR01 gameplay fault scope is intentionally light: low battery, blocked
  brush/obstacle, tank or hopper full and needs service. Reserve detailed fault
  simulation and diagnostics for production machinery.
- Evidence: `Saved/Audits/lb_cr01_candidate_v056_unreal_technical_independent.json`,
  `Saved/Audits/lb_cr01_v056_trim_hierarchy_capture.json`,
  `Saved/Audits/lb_cr01_candidate_v056_unreal_visual_review.json`, and
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v056_TrimHierarchyVisual`.
  Accepted PR-004 v006 remains untouched; the runtime plugin remains disabled.

## 2026-08-03 - CR01 v057 rejection and v058 functional authority gate

- CR01 v057 attempted to add `FloatingPawnMovement` directly to the visual
  Blueprint. A fresh spawned-instance audit proved that Unreal did not remap
  the template `UpdatedComponent` reference: it was null at runtime. v057 was
  rejected and preserved under
  `Saved/FailedCandidates/Candidate_v057_updated_component_not_remapped_20260803_1406`;
  it must not be promoted.
- The existing project C++ support-robot code was compiled against UE 5.8.1.
  Narrow PR-005 HMI compatibility fixes renamed two local `Slot` variables,
  bridged the `TObjectPtr<UTextBlock>` output safely and declared the already
  used Slate/SlateCore dependencies. The `.uproject` now declares the existing
  `LineBossCarFactory` runtime module, so the project authority classes are
  actually loadable. The separate
  `Plugins/LineBossSupportRobotsRuntimeV002` plugin remains disabled and absent
  from the project plugin list.
- CR01 v058 is at
  `/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v058/Blueprints/BP_LB_CR01_CleaningAMR_v058`.
  It subclasses `ALBCleaningAMR` and mounts the preserved v056 robot as a
  visual-only child. The authority owns one swept `RP01_CollisionRoot`; at
  runtime it disables the three duplicate presentation blockers and binds the
  visible brush/deck/squeegee pivots.
- Final UE automation
  `LineBoss.SupportRobots.CR01.FunctionalRuntime` passes. It proves build/load,
  three presentation blockers disabled, certified travel, swept obstacle stop
  at X=143.394 cm before a box centred at X=260 cm, Blocked state and route
  revocation, visible side-brush/scrub-deck deployment, and save/reload returning
  to SafetyStop without restoring route authority or resuming cleaning.
  Evidence: `Saved/Automation/CR01_v058_final/index.json` and
  `Saved/Audits/lb_cr01_candidate_v058_functional_runtime_gate.json`.
- Six fresh 1920x1080 fixed cameras are under
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v058_FunctionalAuthority`.
  Ground alignment, deployed hardware, readable Cairnwell / CR-01 001 /
  Moorcross Works identity and absence of diegetic Line Boss wording pass.
  Manual Pro comparison still holds promotion: the front impact bar is too
  bright, the enclosure is too slab-sided/rectilinear and busy, the fascia reads
  too much like a compact truck, the seven-year mothballed layer is weak, and
  accepted PR-004 v006 factory-lighting proof remains open.
- v058 status is **FUNCTIONAL INTEGRATION PASS / VISUAL REWORK / NOT PROMOTED**.
  Keep cleaner fault gameplay limited to low battery, blocked obstacle/brush,
  tank or hopper full and needs service. Spend detailed fault work on production
  machinery. Next refine the visible front value hierarchy and enclosure
  silhouette, then rerun fresh cameras before any promotion.

## 2026-08-03 - CR01 v063 current integration candidate

- v059-v063 replace the v058 slab-sided/truck-like visual with a rounded modular
  scrubber enclosure, corrected dark front impact beam, Candidate v003 layered
  materials and two-sided Cairnwell / CR-01 001 / Moorcross Works identity.
  Current functional asset:
  `/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v063/Blueprints/BP_LB_CR01_CleaningAMR_v063`.
- `LineBoss.SupportRobots.CR01.FunctionalRuntime` passes from
  `Saved/Automation/CR01_v063_final/index.json`: zero enabled presentation
  blockers, one swept collision authority, movement, obstacle stop, Blocked
  state/route revocation, deployed cleaning tools and safe save/reload all pass.
- Fresh six-camera evidence is in
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v063_FunctionalAuthority`.
  Manual Pro comparison accepts the new silhouette, value hierarchy, grounded
  cleaning equipment, brand identity and absence of diegetic Line Boss text.
- Status remains **FUNCTIONAL INTEGRATION PASS / VISUAL POLISH HOLD / NOT
  PROMOTED**. The mothballed state needs stronger dormant wear, upper fascia and
  roof equipment need restrained polish, and a fresh accepted PR-004 v006
  factory-lighting camera set is still mandatory before promotion.
- Fault scope is intentionally shallow for this support robot: low battery,
  blocked obstacle/brush, tank or hopper full, and needs service. Detailed fault
  simulation belongs to production machinery.
- Evidence:
  `Saved/Audits/lb_cr01_candidate_v063_functional_runtime_gate.json` and
  `Saved/Audits/lb_cr01_candidate_v063_unreal_visual_review.json`. PR-004 v006
  remains unchanged; v059-v063 are candidates only; the separate runtime plugin
  remains disabled.

## 2026-08-03 - CR01 v065 accepted-lighting gate

- v064/v065 add a stronger dormant/restored Candidate v004 material family and
  preserve the rounded 24-part scrubber, corrected front value hierarchy,
  two-sided Cairnwell identity, RP01 relationship and project-module authority.
- UE 5.8.1 build and the final v065 functional automation pass. Evidence:
  `Saved/Automation/CR01_v065_final/index.json` and
  `Saved/Audits/lb_cr01_candidate_v065_functional_runtime_gate.json`.
- Ten fresh fixed-camera images were reviewed: six clean-stage images under
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v065_FunctionalAuthority`
  and four in an isolated duplicate of the accepted PR-004 v006 lighting under
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v065_PR004Lighting`.
  The accepted baseline was not modified.
- Scale, grounding, deployed cleaning tools, rounded scrubber reading, Cairnwell
  / CR-01 001 / Moorcross Works branding and absence of diegetic Line Boss text
  pass. Front sensor/fascia geometry, roof service hardware and the seven-year
  dormant layer remain below the Pro reference.
- Status: **FUNCTIONAL REUSABLE CANDIDATE PASS / VISUAL GEOMETRY HOLD / NOT
  PROMOTED**. Evidence:
  `Saved/Audits/lb_cr01_candidate_v065_fixed_camera_visual_review.json`.
- Cleaner faults remain deliberately light: low battery, blocked brush/path,
  tank or hopper full and needs service. Reserve deep diagnostic/repair gameplay
  for production machinery. Continue MR-01's exact four independently driven
  corner-wheel platform while retaining v065 for later focused art refinement.
- Accepted PR-004 v006 is unchanged; the separate support-robot runtime plugin
  remains disabled.

## 2026-08-03 - MR01 v015 source visual decision

- v014 preserves the exact four RP01-linked corner wheels/hubs but was rejected
  for Unreal import because its working arm remained visually buried in the
  upper body.
- v015 lowers the non-authoritative upper skin/coamings and rear crown, reseats
  the parking cradle and widens only the arm's cross-vehicle thickness from
  272.0 to 331.8 mm. Arm bones, reach axes, TCP, 1,800 mm reach contract and
  four-wheel coordinates are unchanged.
- Independent Blender audit passes exactly four wheels and hubs, unchanged
  shared RP01 library geometry/locations/dimensions, unchanged authoritative
  arm hierarchy and heads, 86 mm shoulder exposure above the corrected deck,
  Cairnwell identity and absence of Line Boss in-world branding.
- Four fresh source renders were inspected against the Pro sheet. v015 is
  **ACCEPTED FOR ISOLATED UNREAL TECHNICAL EXPORT AND IMPORT / NOT PROMOTED**.
  Evidence is under
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v015`.
- Remaining release gates: formed bumper integration, wheel-pod finish, Unreal
  material/ageing proof, arm/tool/outrigger/mast articulation, collision,
  navigation, authority-provider, save-state and fresh fixed-camera Unreal
  review. Do not embed or duplicate RP01 wheel/hub geometry in the payload and
  keep the separate runtime plugin disabled.

## 2026-08-03 - MR01 v017-v020 raised arm, strict Unreal skeleton and connected lift

- v017 raises the complete arm installation by 90 mm without changing link
  geometry, ten-bone authority or the four shared RP01 corner-wheel transforms.
  Source proof reaches 1,900 mm forward and 2,450 mm high with the T6 powered
  torque tool selected. The first 400 mm lift render was visually rejected
  after the user correctly identified that the skeletal arm had moved without
  its physical carriage, leaving a visible gap above the chassis.
- The first Unreal v017 import is rejected because FBX converted hose, socket
  and installation nodes into 25 bones. v018 joins the ten already weighted
  flexible hose/clamp meshes into the arm mesh but is also rejected because the
  Blender armature container remained as an eleventh Unreal bone. Preserve both
  failed namespaces; do not promote them.
- v019 uses one skinned arm mesh and Unreal's stripped `Armature` container.
  Its isolated import at
  `/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v019` passes with exactly
  ten authored bones, 344 payload meshes, one skeletal arm, carousel plus T1-T8
  and no embedded RP01 wheels/hubs. It is a technical stepping stone only.
- v020 adds a nested moving lift sleeve. At the full 400 mm stroke the sleeve
  travels 200 mm and the carriage/arm travel 400 mm, retaining 199.0 mm fixed
  guide-to-sleeve overlap and 36.5 mm sleeve-to-carriage overlap. The corrected
  source render shows the chassis, lift, arm and T6 as one continuous mechanism.
- v020 clean Blender reimport and strict Unreal import pass. Current isolated
  assets are at `/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020`; audit:
  `Saved/Audits/lb_mr01_candidate_v020_unreal_import.json`. Counts are 354
  static meshes including the added sleeve and nine tool/carousel assets, one
  skeletal mesh, one skeleton and exactly ten bones.
- v020 remains **SOURCE VISUAL CORRECTION PASS / ISOLATED UNREAL IMPORT PASS /
  RUNTIME AND FACTORY CAMERA GATES OPEN / NOT PROMOTED**. Next assemble the
  reusable MR01 actor from the shared RP01 base, drive sleeve/carriage/arm as a
  synchronized lift, implement mutually exclusive carousel/coupler T6 state,
  then run collision, save-state and fresh fixed-camera Unreal proof. Accepted
  PR-004 v006 and the disabled separate support-robot runtime plugin are unchanged.

## 2026-08-03 - MR01 v021 reusable native-authority assembly

- Built `/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021`
  on native `ALBMaintenanceAMR`, using v020 connected-lift art and direct
  references to the shared RP01 wheel assets. The Blueprint contains 345
  payload components, one ten-bone poseable arm, exactly four independent
  corner wheel modules, carousel and eight mutually exclusive stored/equipped
  tool pairs. No caster wheels or duplicated RP01 geometry were added.
- UE 5.8 Python cannot address C++-created inherited pivots as Blueprint
  SubobjectData parents. The release-oriented bridge tags visual groups with
  `LB.MR01.AttachTo.<contract>` and native `BeginPlay` reparents them to the
  matching wheel, outrigger, mast, door, drawer or rack component using
  `KeepWorldTransform`. This preserves the baked CFR assembly while allowing
  the native authority to animate it.
- The native presentation layer now drives ten-bone component-space FK, the
  half-stroke sleeve/full-stroke carriage lift and stored/equipped tool
  visibility. The C++ editor target compiles successfully after the bridge.
- Build audit: `Saved/Audits/lb_mr01_candidate_v021_reusable_authority_build.json`.
  Status is **REUSABLE ASSEMBLY BUILT / FRESH RELOAD, RUNTIME, COLLISION,
  SAVE-STATE AND FIXED-CAMERA GATES OPEN / NOT PROMOTED**.

## 2026-08-03 - MR01 v021 runtime pass, visual hold and Press Shop priority

- Fresh disposable-instance reload passes for v021: 378 static components,
  345 v020 payload parts, one ten-bone poseable arm, exactly four independent
  shared-RP01 corner modules, sixteen wheel/rim/hub/bearing visuals and eight
  stored plus eight equipped tool visuals. Audit:
  `Saved/Audits/lb_mr01_candidate_v021_reusable_authority_fresh_audit.json`.
- `LineBoss.SupportRobots.MR01.FunctionalRuntime` now passes from a clean editor
  process. It proves runtime contract attachment, T6 rack-to-coupler transfer,
  400 mm arm/lift travel, 200 mm nested-sleeve travel, save/restore, the
  1550 x 930 x 1250 mm collision authority, navigation relevance, swept
  obstacle stop and route-authority revocation. Evidence:
  `Saved/Automation/MR01_v021_r5/index.json`.
- The first fresh Unreal screenshot at
  `Saved/ValidationScreenshots/SupportRobots/MR01/Candidate_v021/lb_mr01_v021_stowed_oblique.png`
  is visually rejected: shared wheels render with bright default material, the
  supposed stowed arm remains horizontally extended, the second proof instance
  intrudes, and the stage framing is weak. v021 remains **RUNTIME/COLLISION/SAVE
  PASS / VISUAL HOLD / NOT PROMOTED**. A repair script exists at
  `Scripts/repair_lb_mr01_v021_visual_gate_v002.py` but did not execute and is
  not authoritative.
- User priority is now explicit: finish the entire Press Shop, including
  PR-001 through PR-010, all four press trains and support areas, before any
  further CR01/MR01 work. Preserve the robot checkpoint and stop robot changes.
# PR-004 v020 fresh visual gate (2026-08-03, latest)

- Fresh fixed-camera Unreal captures now exist under `Saved/ValidationScreenshots/PressShopIntegration/v020_pr004_surfaceforge_robot/`.
- Capture gate passed for robot detail, cell and front-end views.
- Visual gate failed: the close view is dominated by bright yellow/orange paint and coarse wear, the PR004-RBT-01 plate reads mirrored from the audited side, and the wider views do not materially improve the sparse accepted-v006 composition against the Pro references.
- v020 remains an unpromoted development candidate. Its reusable hierarchy may be harvested later, but its material/cell presentation must not replace the accepted `/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006` baseline.
- Decision audit: `Saved/Audits/press_shop_pr004_surfaceforge_robot_visual_gate_v020.json`.
# PR-004 native runtime/save gates (2026-08-03, latest)

- Added `Source/LineBossCarFactory/LBPR004StationTests.cpp` with dedicated PR-004 automation coverage.
- Added read-only active packaging-scan and inspection request-token getters to `LBPR004Station.h` for HMI/runtime observability and deterministic testing.
- UE 5.8 `LineBossCarFactoryEditor Win64 Development` build passes with Visual Studio 14.44 and Windows SDK 10.0.22621.0.
- Fresh report `Saved/Automation/PR004_r2/index.json`: **2 succeeded, 0 failed, 0 not run**.
- Covered: power/commissioning ordering; complete authorisation permissives; packaging-scan transition; gate-open fault during securing motion; proved fault reset; power-loss material-ownership reconciliation; stable save/restore; invalid save-version rejection.
- This closes the current native station logic/save regression gate, not the presentation binding, full-map runtime, HMI, collision/navigation, performance or visual promotion gates.
# Bare-coil front-end v021 gate (2026-08-03, latest)

- Built isolated `/Game/LineBoss/Maps/LB_PressShop_BareCoilFrontEndCandidate_v021` directly from accepted PR-004 v006; rejected v007-v010 maps were not used.
- Replaced the obsolete wrapped MasterCoil asset in PR-001, PR-002 and all twelve PR-003 store positions: 14 actors total.
- Reusable duplicated mesh: `/Game/LineBoss/IndustrialKit/MaterialHandling/BareCoil/Candidate_v021/SM_LB_BareMasterCoil_v021`, with 8 convex simple-collision hulls, default trace and exact preserved saddle contact height (maximum delta 0 cm).
- Fresh captures: `Saved/ValidationScreenshots/PressShopIntegration/v021_bare_coil_front_end/`.
- Authority direction passes, but the visual gate fails: the inherited coil-steel material is too dark/flat and reads like black rubber rather than wound steel. v021 is not promoted; retain geometry/collision and iterate the material.
- Audits: `Saved/Audits/press_shop_bare_coil_front_end_candidate_v021.json` and `Saved/Audits/press_shop_bare_coil_front_end_visual_gate_v021.json`.
# Wound-steel material v022 gate (2026-08-03, latest)

- Built isolated `/Game/LineBoss/Maps/LB_PressShop_WoundSteelFrontEndCandidate_v022` from preserved v021 and applied a contained procedural wound-steel material to 15 bare coils, including PR-004.
- Surface Forge was deliberately not used: the installed subset contains only Metal Paint Chips textures, unsuitable for exposed wound steel.
- Fresh captures under `Saved/ValidationScreenshots/PressShopIntegration/v022_wound_steel/` pass technically but fail visually: there is no meaningful management-distance improvement and the coils remain too dark.
- Do not promote v022. Next pass must co-develop the coil shader with local front-end lighting/reflection capture; do not repeat shader-only value changes.
- Audits: `Saved/Audits/press_shop_wound_steel_candidate_v022.json`, `Saved/Audits/press_shop_wound_steel_visual_gate_v022.json`.

# PR-004 depackaging scope correction (2026-08-03, latest)

- User authority confirms that a dedicated coil-unwrapping robot was rejected as more complexity than its gameplay value justifies.
- Do not continue, promote or require the v020 robotic depackaging candidate for Press Shop completion.
- PR-004 remains a packaging-preparation/depackaging station, but its release implementation should use credible fixed handling/cutting equipment and worker interaction within the existing safety/HMI/material-state authority.
- The accepted integration baseline remains v006 and the coil material/lighting work remains in scope. Pro robotic-cell sheets are visual/layout references only where compatible with this corrected gameplay scope.
- With the robot removed, do not retain the inherited full robotic safety cage in the release layout. Use only proportionate local guarding for real fixed cutting, clamping and pinch hazards, with suitable emergency stops.
- User authority further confirms that all received and stored coils remain visibly packaged. At PR-004 the selected wrapped coil sits on the preparation stand; clicking `Unpackage` changes only that coil to the bare state for PR-005. Do not display the PR-001/PR-002/PR-003 inventory as bare coils.

# PR-004 simplified wrapped-stand candidate v024 (2026-08-03, latest)

- Built isolated `/Game/LineBoss/Maps/LB_PressShop_PR004WrappedStandCandidate_v024` without touching accepted v006 or rejected v007-v010.
- Removed 98 obsolete PR-004 robot/cage actors, retained the powered stand and one operator emergency stop, and placed the packaged coil at exactly the prior support height with simple collision.
- Corrected all fourteen PR-001/PR-002/PR-003 receipt/store coils back to the packaged asset at their exact support heights.
- Removed malformed `LB_MOTH_V004_PR004_ServiceOil`, an oversized rotated engine cylinder whose bounds extended 95.17 cm below the floor and rendered as a large beige wedge.
- Added native `UnpackageCoil` interaction authority. It atomically changes the selected packaged coil to the bare/handoff-ready state without robot/cage/scanner/waste-module health dependencies and persists through stable save/restore.
- UE 5.8 editor build passes. Fresh `Saved/Automation/PR004_r3/index.json`: **3 succeeded, 0 failed, 0 not run**, including `SimpleUnpackageInteraction`.
- Fresh corrected views: `Saved/ValidationScreenshots/PressShopIntegration/v024_pr004_wrapped_stand/`.
- Visual direction is approved, but v024 is **not promoted**: packaging needs believable labels/seams/scuffs/ageing, and the live in-map wrapped-to-bare presentation/HMI binding remains open.
- Audits: `Saved/Audits/press_shop_pr004_wrapped_stand_candidate_v024.json`, `press_shop_pr004_wrapped_stand_repair_v024.json`, and `press_shop_pr004_wrapped_stand_visual_gate_v024.json`.

# PR-004 native presentation and local-floor candidate v025 (2026-08-03, latest)

- `ALBPR004Station` now owns wrapped and bare coil visuals and switches their visibility/click collision from saveable authority. `Saved/Automation/PR004_r4/index.json` passes all three PR-004 tests, including restored wrapped-to-bare presentation.
- Native map binding is recorded in `Saved/Audits/press_shop_pr004_interactive_coil_binding_v024.json`.
- Current isolated map: `/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025`. Its local non-colliding/navigation-irrelevant markings replace the obsolete robot footprint with a compact stand boundary, operator pad and transfer lane to PR-005; no whole-floor rebuild is required.
- Fresh front, packaged-close and unpackaged-close views are in `Saved/ValidationScreenshots/PressShopIntegration/v025_pr004_interactive_floor/`.
- Status is **DIRECTION PASS / POLISH AND RUNTIME GATES OPEN / NOT PROMOTED**. Hold promotion for believable wrapped-coil labels/seams/scuffs/ageing, clearer worn operator-zone paint, player-visible click/HMI proof, PIE, navigation and disk save/load gates.
- Visual audit: `Saved/Audits/press_shop_pr004_interactive_floor_visual_gate_v025.json`.

# PR-004 packaged-coil/HMI/navigation candidate v026 (2026-08-03, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026` is the active isolated candidate from accepted v006 lineage. It does not promote or supersede v006; rejected v007-v010 remain rejected.
- PR-001 through PR-003 inventory is visibly packaged. The selected Cairnwell-labelled PR-004 coil is supported on the powered preparation cradle and native `ALBManagementPawn::InteractWithActor` changes it to the bare PR-005 handoff state. No unwrapping robot or redundant full robot cage is present.
- `ALBPR004Station` hosts the native HMI authority. The invisible World WidgetComponent remains a query-only click surface/widget host; the command-line renderer's checkerboard-prone visual layer is hidden. A deterministic native TextRender layer provides the release-visible black-screen presentation: Cairnwell Automotive / Moorcross Works, station, live state, coil ID, recipe/interlocks and Unpackage action. There is no diegetic Line Boss wording.
- `ALBPressShopNavigationBootstrap` plus the v026 NavMeshBoundsVolume provides local runtime navigation. Native-code path validation avoids the Unreal Python class-default-object ensure. Fresh PIE route evidence is valid, non-partial and 1396.95 cm: `Saved/Audits/press_shop_pr004_navigation_runtime_v026.json`.
- `Saved/Audits/press_shop_pr004_collision_navigation_v026.json` reports **COLLISION_AND_RUNTIME_NAVIGATION_PASS / NOT PROMOTED**. Eleven floor markings are NoCollision/navigation-irrelevant; bins and HMI support remain physical; the HMI touch plane is query-collidable; HMI text is non-colliding; minimum bin-to-HMI clearance is 599.1 cm.
- Fresh UE 5.8 editor build succeeds. `Saved/Automation/PR004_r11/index.json` reports **3 succeeded, 0 failed, 0 not run** for commissioning/interlocks, management-pawn Unpackage interaction and stable save/presentation round-trip.
- Fresh front, packaged, unpackaged and runtime-HMI evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v026_pr004_packaging_polish/`. v026 remains **TECHNICAL/INTERACTION/NAVIGATION PASS / VISUAL AND BROADER RELEASE GATES OPEN / NOT PROMOTED**. Still required: final cradle/pad/material ageing and lighting review against Pro references, operational crane trolley/hoist/hook/load transfer, broader import/authority gates and disk-level game SaveGame proof.
- Downstream design authority: PR-005 has detailed dimensioned modular source assets and moving assemblies plus gameplay/HMI/audio contracts. PR-006 leveller, PR-007 washer/lube, PR-008 servo-feed/cut/pre-punch, PR-009 stacker, PR-010 four-lane blank store and the four press trains have approved master-plan footprints, positions, process/buffer/safety/service/control requirements. They are not yet final PR-005-detail CAD sets; create reusable modular production machines and visually gate each area before promotion.

# PR-004 native crane v027/v028 checkpoint (2026-08-03, latest)

- Added reusable native `ALBBridgeCraneController` and `LBBridgeCraneControllerTests.cpp`. Tagged bridge, trolley, hoist, reeving and C-hook modules now transfer the real CS-10 packaged coil into native PR-004 authority with interlocked fail-stop/recovery and in-flight save/restore. Cairnwell backing and both text layers remain rigidly owned by the moving package.
- Corrected the C-hook/load datum: the authored padded lower bore arm is 59 cm below the C-body actor origin, and the carried coil now follows that physical bore centre. Fresh test coverage explicitly asserts this relationship.
- v027 is the first complete runtime transfer proof. Current isolated visual rework map is `/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028`, derived from v027 and still unpromoted. Accepted PR-004 baseline remains v006; rejected v007-v010 remain rejected.
- User review found the inherited 4.5 m bridge did not reach both runway rails. v028 now uses a measured 6210 cm rail-to-rail span: the 40 t bridge has two fourteen-module girders plus eight cross-ties; the 30 t bridge has one fourteen-module girder. Each module is 443.57 cm, closing exactly between end-truck Y=-5520 and Y=690 cm.
- Latest evidence: `Saved/Automation/PR004_r13/index.json` = **4/4 pass**; `Saved/Audits/press_shop_pr004_crane_runtime_v028.json` = **PASS** with exact coil identity, complete phase trace and 0 cm native rigid-follow error; `Saved/Audits/press_shop_pr004_navigation_runtime_v028.json` = valid/non-partial 1396.95 cm path; `Saved/Audits/press_shop_pr004_collision_navigation_v028.json` = **PASS**.
- Fresh fixed runtime evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v028_pr004_crane_runtime/`, including frontal/oblique full-span, live bore-engagement and deposited-coil views. A movable diegetic plate identifies `CAIRNWELL AUTOMOTIVE / CR-40-01 / SWL 40 t`; there is no Line Boss in-world wording. Visual decision remains **FAIL / REWORK REQUIRED / NOT PROMOTED** in `Saved/Audits/press_shop_pr004_crane_visual_gate_v028.json`: width and bore engagement are corrected, but bridge fabrication/material wear, festoon and trolley detail, packaged-wrap layering/label contrast, lighting balance and a completely unobstructed span view remain below Pro-reference release quality. The 30 t bridge has corrected geometry but no native logistics authority yet.

# PR-004 packaged crane load v029/v030 checkpoint (2026-08-03, latest)

- Rebuilt the packaged master coil as reusable source v004 with exact 1499.8 x 1900 x 1900 mm dimensions, 78,656 render triangles, ten controlled material slots, twelve convex UCX ring segments and a 640 mm collision bore. Independent Blender re-import passes. UE 5.8 Interchange incorrectly merged the UCX meshes into render geometry; the final candidate import therefore uses the supported legacy FBX static-mesh factory and gates exact bounds plus twelve convex elements. The failed tiny/overscale imports are quarantined and not referenced by the map.
- `/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029` replaces all fifteen placeholder packages with the detailed asset. `/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030` adds darker layered wrap instances, moves Cairnwell labels clear of the bore, repairs the first blank west-camera frame and gives fixed cameras deterministic exposure. Neither candidate is promoted.
- Runtime evidence in `Saved/Audits/press_shop_pr004_crane_runtime_v029.json` and `press_shop_pr004_crane_runtime_v030.json` passes the complete CS-10 transfer with exact `MCX-U-CS10-0001` ownership and 0 cm native load/attachment drift. `press_shop_pr004_navigation_runtime_v029.json` remains valid/non-partial at 1396.95 cm; `press_shop_pr004_collision_navigation_v029.json` passes with no failures.
- Fresh v030 images are in `Saved/ValidationScreenshots/PressShopIntegration/v030_pr004_crane_runtime/`. They prove both bridges reach the full 6210 cm runway span and the lower C-hook arm remains through the packaged-coil bore. They do **not** pass release presentation. `Saved/Audits/press_shop_pr004_crane_visual_gate_v030.json` records the remaining blockers: central-column/dual-crane framing, uneven roof/hall luminance, repeated blank module plates, absent readable west-side identity, underlit label/front face with clipped lower crescent, incomplete festoon/trolley/grease/wear detail, and geometry-only 30 t authority. Promotion remains forbidden.

# PR-004 full-span crane fabrication v031 checkpoint (2026-08-03, latest)

- User clarified that the crane must be full width. `/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031` preserves the exact measured 6210 cm span across both overhead bridges. It remains isolated and unpromoted; accepted v006 and rejected v007-v010 statuses are unchanged.
- v031 adds layered aged crane materials, 52 splice plates, running rails/grease witnesses, 37 festoon actors, two trolley service cabinets and Cairnwell CR-40-01/SWL 40 t plus CR-30-01/SWL 30 t west identities. Runtime audit reports 69 bridge-fabrication actors and two trolley-service actors following with 0 cm error through the complete CS-10 pickup/deposit sequence.
- Technical gates pass: `Saved/Audits/press_shop_pr004_crane_runtime_v031.json`, `press_shop_pr004_navigation_runtime_v031.json` and `press_shop_pr004_collision_navigation_v031.json`. Fresh fixed-camera evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v031_pr004_crane_runtime/`.
- Visual gate still fails in `Saved/Audits/press_shop_pr004_crane_visual_gate_v031.json`: the lower hall and PR-004 scene are underlit, the wide framing makes the nearer 30 t bridge dominate the working 40 t bridge, and the close view reveals simplified hook-block/pad/reeving geometry. The packaged load also needs stronger final material response. Promotion remains forbidden pending a new isolated visual rework with all technical gates retained.

# PR-004 crane lifting-detail v032 checkpoint (2026-08-03, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004CraneLiftingCandidate_v032` is an isolated, unpromoted v031 derivative. Both bridges remain exactly 6210 cm full-span.
- Eleven hook/yoke/lance actors and four reeving falls were added. The first live test correctly exposed a discovery error: low-centred `LB.Motion.CHook` lance detail moved the controller's initial datum from 820 to 761 cm. The lance now follows as non-reeving hoist detail, and `validate_press_shop_pr004_crane_pie_v027.py` has a new mandatory 820 cm post-discovery/pre-transfer datum gate.
- Corrected runtime, navigation and collision audits all pass: `press_shop_pr004_crane_runtime_v032.json`, `press_shop_pr004_navigation_runtime_v032.json`, `press_shop_pr004_collision_navigation_v032.json`. The complete CS-10 deposit has 0 cm native load/attachment error; inherited bridge/trolley and new lifting detail remain rigidly bound.
- Fresh captures under `Saved/ValidationScreenshots/PressShopIntegration/v032_pr004_crane_runtime/` fail visual review. `press_shop_pr004_crane_visual_gate_v032.json` records a centre-column-obstructed wide view, an oversized box-like primitive yoke silhouette, obvious cube/cylinder fabrication, hot roof lighting and an overbright/sparse deposit view. Do not promote v032.
- Carry the strengthened gates forward, but replace the rejected v032 lifting dressing with a purpose-built dimensioned C-hook/suspension asset. Preserve the 820 cm datum, 59 cm bore-centre offset and full 6210 cm bridge span.

# PR-004 purpose-built C-hook v033 checkpoint (2026-08-04, latest)

- Reusable source is `SourceAssets/IndustrialKit/BridgeCrane/CHook/Candidate_v033/`; independent Blender FBX audit passes. The corrected asset is 2.421 x 0.558 x 2.017 m and imports to Unreal at 242.1 x 55.8 x 201.7 cm under a hard bounds gate.
- Isolated map `/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033` replaces the visible/discoverable 40 t placeholder with the purpose-built hook. It uses Z=820, yaw 90 onto world-Y bore axis, 59 cm vertical load offset and 150 cm body-to-load Y offset. Its 1.88 m padded arm crosses the 1.50 m package width while the forged body stays outside the face.
- The initially tiny import, wrong 0 degree orientation and too-short 0.94 m cantilever were each rejected by import/runtime/camera gates and corrected at source. Latest runtime, navigation and collision audits pass with exact CS-10 deposit and effectively zero visual/native follow error.
- Latest four-camera evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v033_pr004_crane_runtime/`. The hook subassembly earns a **direction pass for reuse**, but the full v033 map remains unpromoted: lighting hierarchy, parked 30 t composition, deposit presentation, package label/material polish and 30 t native support authority remain open. Decision audit: `Saved/Audits/press_shop_pr004_crane_visual_gate_v033.json`.
- Fleet authority: 40 t is the primary front-end master-coil crane; 30 t is a distinct parked support/maintenance crane; separate press-train cranes will be added later for die changes/major maintenance only where required.

# PR-004 crane hierarchy/material v034 checkpoint (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034` is an isolated, unpromoted v033 derivative. Accepted v006 and rejected v007-v010 remain untouched.
- The complete 30 t moving assembly is parked at the west/north service end (bridge X=-9100, trolley Y=-4700, hook stow Z=1010 cm) while fixed rails/columns stay measured and its Cairnwell plate now identifies SUPPORT duty. The 40 t crane alone retains live master-coil authority at Z=820 with the purpose-built C-hook and [0,150,-59] cm load relationship.
- v034 adds lighter layered woven-grey package materials, restrained 620 x 280 mm Cairnwell plates and three low-power floor task fills. Runtime, navigation and collision gates all pass with exact CS-10 deposit, zero native drift and the unchanged 1396.95 cm complete operator route.
- Four fresh fixed runtime captures are under `Saved/ValidationScreenshots/PressShopIntegration/v034_pr004_crane_runtime/`. `Saved/Audits/press_shop_pr004_crane_visual_gate_v034.json` remains a deliberate hold: southeast management framing is column-obstructed, ceiling pools are clipped, front package/HMI readability still needs polish, and the parked 30 t crane has no distinct native support authority. Do not promote v034.
- Next isolated v035 should move the management camera inside the south structural line and rebalance ceiling/floor light without altering the technically proven 40 t crane, C-hook or package ownership.

# PR-004 crane/package/HMI finish v035 checkpoint (2026-08-04, latest)

- Current isolated map is `/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035`; it remains unpromoted and does not replace accepted v006.
- The selected clear interior management camera removes structural-column obstruction, keeps the working 40 t crane dominant and leaves the stowed 30 t support crane recessed. Broad roof fills are reduced to 320/450 while v034 floor spots remain.
- Package identity is consolidated onto the dimensioned asset's existing physical 420 x 250 mm main panel. Both imported fixed label/ink slots use controlled blank paper; obsolete baked IDs are gone. Live Cairnwell/Moorcross backing and text actors are aligned with the panel and all three CS-10 attachments retain native rigid ownership.
- After the final label alignment and camera additions, runtime, navigation and collision were rerun and pass: exact `MCX-U-CS10-0001`, every transfer phase, initial/final hook Z=820, zero native load/attachment error, 1396.95 cm complete path and zero collision failures.
- Selected fresh evidence under `Saved/ValidationScreenshots/PressShopIntegration/v035_pr004_crane_runtime/` proves clear crane hierarchy, package label alignment, C-hook bore traversal, completed cradle deposit and readable live Cairnwell PR-004 HMI.
- Visual decision in `Saved/Audits/press_shop_pr004_crane_visual_gate_v035.json`: **DIRECTION PASS / RELEASE POLISH AND 30 T AUTHORITY OPEN / NOT PROMOTED**. Retain the subassemblies. Still required: live secondary heat/lot/barcode presentation, final wrap fibre/wrinkle/scuff finish, final factory luminaire/reflection treatment, distinct native 30 t support dispatch and combined PR-004 campaign/fault/save plus PR-005 handoff proof.

# PR-004 30 t support-crane authority and hook v036-v038 (2026-08-04, latest)

- `ALBSupportCraneController` is the reusable native authority for CR-30-01. It cannot handle master coils and is separate from the 40 t controller. Press Shop save format is v3 with `FLBSupportCraneSaveState`.
- Dispatch requires power, route/personnel clearance, maintenance permit, support-zone reservation and 40 t swept-zone clearance. Motion fail-stops on a lost proof. Moving restore is safely faulted pending named recovery; only Parked and OnStation are stable restore contracts.
- `Saved/Automation/SupportCrane_v001/index.json` passes. v038 dispatches to (-7600,-4700,760), returns to (-9100,-4700,1010), leaves all 117 observed 40 t actors at 0 cm drift and neither moves nor consumes the master coil.
- v036's C-hook was rejected as contradictory. Reusable v038 Blender/Unreal hook asset is `/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SupportHook/Candidate_v038/SM_LB_Crane_SupportHookBlock_30T_Candidate_v038`, with a conventional forged hook, safety latch, swivel, twin sheaves and guarded near face. Bounds are 117.07 x 69.50 x 161.09 cm; its service envelope is clear of coil inventory.
- v038 primary-crane, navigation and collision regressions pass alongside the support cycle. Evidence: `Saved/Audits/press_shop_pr004_support_crane_runtime_v038.json`, `press_shop_pr004_crane_runtime_v038.json`, `press_shop_pr004_navigation_runtime_v038.json`, `press_shop_pr004_collision_navigation_v038.json`.
- Fresh images are in `Saved/ValidationScreenshots/PressShopIntegration/v038_pr004_support_crane_runtime/`. Visual decision is **DIRECTION PASS / HOLD / NOT PROMOTED** in `Saved/Audits/press_shop_pr004_support_crane_visual_gate_v038.json`: bridge identity is not readable enough, the inherited upper hoist casing is below the new lower block's finish, final restrained hook wear is open, and the final fleet view must keep the 30 t crane subordinate to the active 40 t crane.
- Reuse the native authority, guarded hook and clear service datum. Do not promote v036-v038. Continue live heat/lot/barcode, wrap fibre/wrinkle/scuff, factory luminaire/reflection and combined PR-004 campaign/save plus PR-005 handoff work while preserving accepted v006 and rejected v007-v010 status.

# PR-004 live coil traceability v039 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039` is the current isolated derivative of retained v038. It is **not promoted**; accepted v006 and rejected v007-v010 status are unchanged.
- Native PR-004 stable save format is v4. `HeatId`, `SupplierLotId` and `TraceabilityBarcode` are validated, persisted, restored and cleared with coil ownership. The 40 t crane deposits exact CS-10 values `HT-CW26-08417`, `LOT-MCXU-260804-A`, `503184064100010`.
- `Saved/Automation/PR004_Traceability_v039/index.json` reports 4 succeeded, 0 failed. UE 5.8 editor compilation and controller/HMI source contracts pass.
- Fourteen external packages have live secondary trace actors and the native PR-004 wrapped presentation has matching components. Six CS-10 actors move under crane ownership. A first runtime failure caught Static text actors at 1269.14 cm drift; after correction to Movable the final audit reports 0 cm native load/attachment drift.
- Final overlay uses the CAD-authored heat-label datum: 240 x 150 mm at imported X=-27 cm / face Y=+75.3 cm / Z=-36 cm. Two estimated transforms were visually rejected because they added or partially exposed a third white panel. Fresh final images show data seated on the one authored lower paper panel.
- After final placement, primary/support crane runtime, valid non-partial 1396.953125 cm navigation, and collision/navigation all pass. Evidence is in the v039 audits and `Saved/ValidationScreenshots/PressShopIntegration/v039_pr004_crane_runtime/`.
- `Saved/Audits/press_shop_pr004_traceability_visual_gate_v039.json` records **DIMENSIONED LIVE TRACEABILITY DIRECTION PASS / PACKAGE AND FACTORY RELEASE VISUAL HOLD / NOT PROMOTED**. Remaining blockers are small-type/barcode polish, wrap fibre/wrinkle/scuff and edge-compression finish, luminaires/reflections, final 30 t hierarchy/upper-hoist detail, and combined PR-004 campaign/save plus PR-005 handoff proof.

# PR-004 package surface and local task light v040 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040` is the current isolated v039 derivative. It remains unpromoted; accepted v006 and rejected v007-v010 are unchanged.
- v040 changes only packaged-coil material slots 2/3/4/6 and adds one non-colliding/navigation-irrelevant package task source. Package dimensions, detailed geometry, labels, crane datums and six-actor CS-10 ownership are preserved.
- Final retained values produce woven silver-grey wrap, restrained blue-grey overlap/patch contrast and dry compressed-fibre edge pads. Dark, overbright and pale intermediate render balances were inspected and rejected before the current compromise.
- Final v040 primary/support crane, navigation and collision/navigation gates pass with zero native ownership/isolation drift and the unchanged valid non-partial 1396.953125 cm route.
- Fresh fixed close, carried and clear management evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v040_pr004_crane_runtime/`. Visual gate `Saved/Audits/press_shop_pr004_wrap_finish_visual_gate_v040.json` is **PACKAGE SURFACE AND LOCAL TASK LIGHT DIRECTION PASS / AUTHORED WRINKLE AND FACTORY LIGHTING HOLD / NOT PROMOTED**.
- Next work: restrained shallow wrinkle/scuff/edge-compression geometry or decals, inventory/store luminaires and roof-reflection balance, then remaining trace typography, 30 t upper-hoist/identity and combined campaign/save/PR-005 handoff gates.

# PR-004 directed factory luminaire candidate v041 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041` is the current isolated v040 derivative. It remains unpromoted; accepted v006 and rejected v007-v010 are unchanged.
- v041 replaces the dominant visual contribution of the fifteen omnidirectional ceiling fills with a downward factory task-light grid while retaining each old source at low ambient intensity. The new sources do not cast shadows or affect collision/navigation. Geometry, package labels, six-actor CS-10 ownership and both crane authorities are unchanged.
- Final v041 primary/support crane, navigation, and collision/navigation gates pass. The route remains valid/non-partial at 1396.953125 cm and neither crane reports authority drift.
- Fresh fixed management, package-close and carried-package evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v041_pr004_crane_runtime/`. Visual gate `Saved/Audits/press_shop_pr004_luminaire_visual_gate_v041.json` is **DIRECTED FACTORY LUMINAIRE DIRECTION PASS / PACKAGE CARRY AND RELEASE LIGHTING HOLD / NOT PROMOTED**.
- The directed grid is retained as the lighting foundation because it reduces the repeated v040 roof bloom and restores readable work-floor pools. Promotion remains blocked by the pale carried package against the dark upper hall, final wall/reflection exposure, authored wrap wrinkles/scuffs/edge compression, trace typography/barcode polish, 30 t upper-hoist/identity finish, and combined PR-004 campaign/save plus PR-005 handoff proof.

# Native PR-004 to PR-005 traceable material flow v001 (2026-08-04, latest)

- The previously documented Windows SDK/C++ blocker is resolved. The UE 5.8 editor target compiles successfully with Visual Studio 2022 toolchain 14.44.35228 and Windows SDK 10.0.22621.0.
- `ALBPressShopMaterialFlowController` now provides an atomic front-end ownership transaction. It validates PR-004 release and PR-005 acceptance, requests the PR-004 handoff, loads PR-005 with exact coil/heat/lot/barcode/width data, confirms PR-004 release only after acceptance, and restores both pre-transaction snapshots if any step fails.
- `FLBPR005SaveState` advances to version 2 with heat, supplier lot and barcode; `ULBPressShopSaveGame` advances to format 4. Restore accepts legacy PR-005 version 1 and safely initializes its absent trace fields.
- Focused automation `Saved/Automation/PR004_PR005_Handoff_v001/index.json` passes 1/1. Native Press Shop regression `Saved/Automation/PressShop_NativeRegression_v001/index.json` passes 6/6 with zero warnings/failures. Source HMI/widget contracts still pass; the updated PR-005 save-source audit passes.
- Evidence summary is `Saved/Audits/press_shop_pr004_pr005_material_flow_v001.json`. Status is **NATIVE TRACEABLE HANDOFF AND IN-MEMORY SAVE ROUNDTRIP PASS / MAP RUNTIME AND DISK-SLOT GATES OPEN / NOT PROMOTED**. Next create an isolated v041 derivative with bound PR-004/PR-005/controller actors, visible handoff presentation, PIE transaction proof, disk-slot restore and fixed-camera comparison.

# Full-map PR-004 to PR-005 handoff candidate v042 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042` is the current isolated derivative of unpromoted v041. Accepted v006 and rejected v007-v010 remain unchanged; v042 is not promoted.
- v042 binds the existing 59-actor modular PR-005 geometry set to one native `ALBPR005Station` and the transactional material-flow controller. Fifteen payoff, mandrel, coil-car, strip and crop moving actors are attached to native mover components. The payoff coil starts hidden and becomes visible only after PR-005 accepts the exact traceable PR-004 coil.
- PIE handoff audit `Saved/Audits/press_shop_pr004_pr005_handoff_runtime_v042.json` passes: PR-004 clears ownership to AwaitingCoil; PR-005 owns `MCX-U-CS10-0001`, heat `HT-CW26-08417`, lot `LOT-MCXU-260804-A`, barcode `503184064100010`; the payoff presentation is visible; all 15 mover bindings remain present.
- Fresh v042 40 t transfer, 30 t support dispatch/return, valid non-partial 1396.953125 cm navigation and collision/navigation gates pass. Native regression v002 passes 6/6 and includes real SaveGame memory serialization/deserialization of Press Shop format 4.
- The initial camera pair was rejected for structural-column obstruction. Revised fixed evidence in `Saved/ValidationScreenshots/PressShopIntegration/v042_pr004_pr005_handoff_runtime/` clearly shows the loaded coil and the PR-004 stand/handoff-lane/PR-005 relationship.
- Visual gate `Saved/Audits/press_shop_pr004_pr005_visual_gate_v042.json` is **TRACEABLE HANDOFF AND LOADED PAYOFF DIRECTION PASS / PR-005 HMI, MATERIAL AND RELEASE POLISH HOLD / NOT PROMOTED**. Next bind the accepted Cairnwell live-HMI direction in the full map, author the coil-car/loading motion rather than an instantaneous visual swap, finish PR-005 materials/reflections and operational aisle dressing, prove disk-slot restore in a fresh process, then repeat fixed-camera inspection.
- Fresh-process disk persistence now passes: `Saved/Automation/PR004_PR005_DiskWriter_v001/index.json` writes the exact format-4 handoff state and a separate Unreal process in `Saved/Automation/PR004_PR005_DiskReader_v001/index.json` verifies PR-004 ownership release plus PR-005 coil/heat/lot/barcode. The reader removes only the named automation slot; no test save remains. Native regression v003 passes 7/7 with no warnings/failures. Remaining v042 blockers are therefore visual/interaction release work, not traceability or persistence.

# PR-005 live Cairnwell HMI candidate v043 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043` is an isolated v042 derivative and remains unpromoted. Accepted v006 and rejected v007-v010 statuses are unchanged.
- Native PR-005 now owns an interactive `ULBPR005HMIWidget` plus a deterministic command-line-PIE presentation mounted to the exact 340 x 255 mm cabinet display. The full-map -90 degree station transform is resolved. Runtime text truthfully reports Cairnwell Automotive / Moorcross Works, UNSURVEYED restoration state, transferred `MCX-U-CS10-0001`, `U_SERIES_1500`, 1500 mm, current permissives and the blocked action.
- The initial guard-obstructed/wrong-coordinate close view was rejected. Corrected fresh operator-close and loaded-cell evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v043_pr005_live_hmi_runtime/`.
- Fresh v043 technical gates all pass: `press_shop_pr004_crane_runtime_v043.json`, `press_shop_pr004_support_crane_runtime_v043.json`, `press_shop_pr004_navigation_runtime_v043.json`, `press_shop_pr004_collision_navigation_v043.json`, `press_shop_pr004_pr005_handoff_runtime_v043.json`, and 7/7 in `Saved/Automation/PressShop_NativeRegression_v004/index.json`.
- `Saved/Audits/press_shop_pr005_live_hmi_visual_gate_v043.json` records **LIVE CAIRNWELL HMI DIRECTION PASS / PR-005 CELL MATERIAL, MOTION AND RELEASE POLISH HOLD / NOT PROMOTED**. Remaining work is visible coil-car/loading motion, layered factory materials/reflections, local lighting/floor/aisle/logistics/workers and a fresh Pro-reference visual gate after those changes.
- The first native loading-motion pass is now present in v043: accepted coil ownership starts a five-second coil-car approach/lift from [-220,0,-38] cm and proves `bCoilCarPositioned` only on settlement. An incomplete owned-coil load restarts deterministically after restore rather than silently claiming position.
- Fresh fixed motion/HMI/settled images are in `Saved/ValidationScreenshots/PressShopIntegration/v043_pr005_live_hmi_runtime/`. Native regression v006 passes 7/7 and all inherited v043 technical gates were rerun successfully after the motion change.
- `Saved/Audits/press_shop_pr005_coil_car_motion_visual_gate_v043.json` records **COIL-CAR RUNTIME MOTION DIRECTION PASS / LOADING APERTURE, MATERIAL AND RELEASE POLISH HOLD / NOT PROMOTED**. Next clarify the guarded loading aperture and coil-car rails/support, then address the mirror-like coil and harsh black/yellow material/reflection balance before operational dressing.

# PR-005 layered material candidate v044 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044` is an isolated v043 derivative and remains unpromoted. Accepted v006 and rejected v007-v010 are unchanged.
- The material pass applies 116 overrides across 59 PR-005 actors. A duplicated reusable industrial-paint master uses the installed Surface Forge Metal Paint Chips PBR subset only for restrained dark painted machine surfaces. The first Surface Forge safety-yellow result turned the safety barrier nearly black and was rejected; final v044 restores controlled coated safety yellow and separates galvanised open mesh.
- New constant worked-steel/stainless/galvanised materials and a rougher coil-steel material reduce the worst mirror response. Fresh settled, motion and live-HMI captures are under `Saved/ValidationScreenshots/PressShopIntegration/v044_pr005_runtime/`.
- Fresh v044 primary/support crane, navigation, collision/navigation and exact handoff gates pass. Visual audit `Saved/Audits/press_shop_pr005_material_visual_gate_v044.json` is **SAFETY COLOUR AND STEEL BALANCE DIRECTION PASS / WOUND DETAIL, DARK MACHINE AND RELEASE DRESSING HOLD / NOT PROMOTED**.
- Continue with authored concentric wound-layer/edge treatment plus local task/reflection lighting. Then clarify the loading aperture/rails and add floor/aisle/logistics/workers before another Pro-reference gate.

# PR-005 authored coil-finish candidate v045 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045` is an isolated v044 derivative and remains unpromoted. Accepted v006 and rejected v007-v010 are unchanged.
- The source payoff coil was not rebuilt: its exact 151.2 x 184.0 x 185.4 cm dimensions, 32,188 triangles, 28 face windings, two edge bands, lap and bore collars are preserved. v045 binds distinct restrained steel to the three imported semantic slots and deliberately excludes Surface Forge paint-chip textures from bare steel.
- A glittering first edge-finish iteration was rejected. The corrected winding finish is rougher/lower-specular and two modest cross-key task lights reveal the coil and threader without a global floor wash. Equipment coordinates and navigable geometry are untouched.
- Fresh fixed PIE images are in `Saved/ValidationScreenshots/PressShopIntegration/v045_pr005_runtime/`; they cover settled loading, motion, live Cairnwell/Moorcross HMI, external guarded player context and internal material inspection.
- Fresh v045 primary crane, support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact traceable handoff gates pass. Barcode `503184064100010` and all 15 native mover bindings are retained. Native regression v006 remains 7/7 because v045 changes no native source.
- `Saved/Audits/press_shop_pr005_coil_finish_visual_gate_v045.json` records **AUTHORED WOUND COIL AND LOCAL LIGHTING DIRECTION PASS / CELL SCALE, DRESSING AND RELEASE POLISH HOLD / NOT PROMOTED**. Continue by clarifying the full 11,500 mm PR-005 line and loading rails/aperture, then add dark-machine service detail, floor wear/routes, logistics and workers before reinspection.

# PR-005 semantic floor-route candidate v046 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046` is an isolated v045 derivative and remains unpromoted. Accepted v006 and rejected v007-v010 remain unchanged.
- Five exact authored PR-005 floor slots now use deliberate service blue, maintenance red, material-flow cyan, label white and protected-walkway green instead of inherited generic grey/dark machine materials. Safety yellow is retained; machinery transforms, collision and navigation geometry are untouched.
- Fresh whole-line and route-detail PIE images are under `Saved/ValidationScreenshots/PressShopIntegration/v046_pr005_runtime/`. The whole-line camera confirms the long outgoing threader/strip path, but normal-distance floor hierarchy is still too weak and the outgoing path needs supports/continuity so it does not read as loose floor services.
- v046 primary/support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and traceable handoff receipts pass. Several otherwise successful Unreal sessions returned Windows `0xC0000005` only after PASS output and clean shutdown logging, without a new CrashReporter bundle; promotion remains blocked pending clean repeat.
- Visual decision `Saved/Audits/press_shop_pr005_floor_routes_visual_gate_v046.json` is **WHOLE-LINE CAMERA DIRECTION PASS / FLOOR-ROUTE PLAYER READABILITY AND CLEAN PROCESS EXIT HOLD / NOT PROMOTED**. Next build dimensioned, non-colliding walkway/maintenance/flow surface geometry and strengthen the outgoing line supports before another clean gate/visual cycle.

# PR-005 dimensioned route candidate v047 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047` is an isolated v046 derivative and is **visually rejected / not promoted**. Accepted v006 and rejected v007-v010 remain unchanged; v045 remains the best preserved PR-005 visual checkpoint.
- v047 authors an exact 11,500 x 1,500 mm walkway plus two yellow edges, ten red dashes and a cyan flow arrow. Sixteen surfaces are verified `NoCollision`, excluded from navigation and leave all machinery transforms untouched.
- An initial below-floor placement was rejected and corrected. `Saved/Audits/press_shop_pr005_v047_route_bounds.json` proves final dimensions, transforms, materials and visibility. Nevertheless the whole-line, angled and top fixed cameras fail to show a coherent release-quality route hierarchy.
- Fresh primary/support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact handoff receipts pass. Most v047 sessions exited cleanly; the final handoff session returned Windows `0xC0000005` only after its PASS receipt and clean shutdown log, with no new CrashReporter bundle.
- `Saved/Audits/press_shop_pr005_dimensioned_routes_visual_gate_v047.json` is **DIMENSION, COLLISION AND RUNTIME TECHNICAL PASS / FIXED-CAMERA VISUAL REJECT / NOT PROMOTED**. Re-author the floor composition as one coherent Blender/CAD decal or mesh package framed for player use, and improve outgoing threader/strip support continuity before adding workers/logistics.

# PR-005 station-local CAD floor-route candidate v048 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048` is an isolated derivative of preserved v045, not of rejected v046/v047. It remains unpromoted; accepted v006 and rejected v007-v010 are unchanged.
- Reusable source is `SourceAssets/PR005/FloorRoutes/Candidate_v048/`. One Blender-authored station-local mesh provides an exact 11,500 x 1,500 mm protected walkway, yellow bounds, red maintenance separation, rightward cyan material-flow arrow and PR-005/pedestrian wording through five semantic material slots. It is placed at the PR-005 datum, uses `NoCollision`, cannot affect navigation and changes no equipment transform.
- The first render exposed a hidden green field, reversed arrow and rotated wording; those source/placement faults were corrected. The inherited PR-005 zoning study is hidden in v048, but a wider pale factory cross-aisle still intersects the module and needs a designed junction.
- Final fresh player, elevated and whole-line fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/v048_pr005_runtime/`. They earn a floor-route **direction pass**, while the cross-aisle transition, hydraulic-service carrier/cover containment, restrained paint wear, workers/logistics and final lighting remain release holds.
- After the final mesh and visibility changes, the 40 t crane, 30 t support crane, valid non-partial 1396.953125 cm navigation path, collision/navigation and exact traceable PR-004→PR-005 handoff all pass. Barcode `503184064100010` and all 15 native mover bindings remain exact.
- Decision audit is `Saved/Audits/press_shop_pr005_cad_floor_visual_gate_v048.json`: **DIMENSIONED STATION-LOCAL FLOOR ROUTE DIRECTION PASS / CROSS-AISLE JUNCTION, SERVICE ROUTING AND RELEASE FINISH HOLD / NOT PROMOTED**. Retain the v048 module as the next floor-integration base; do not promote the map.

# PR-005 cross-aisle junction candidate v049 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049` is an isolated, unpromoted v048 derivative. Source is `SourceAssets/PR005/FloorRoutes/Candidate_v049/`; the v048 actor is hidden only in v049 and accepted v006/rejected v007-v010 remain untouched.
- Eight 120 mm white crossing bars and two yellow threshold bars form an 1800 x 1260 mm junction inside the exact 1500 mm protected walkway. This acknowledges the inherited pale factory cross-aisle instead of allowing it to cut through the green route without a transition.
- Fresh player, elevated and whole-line runtime images are under `Saved/ValidationScreenshots/PressShopIntegration/v049_pr005_runtime/`. The junction is legible and proportionate, but paint is too pristine, the broader pale cross-aisle lacks final global material authority, and the adjacent authored hydraulic carrier/exposed hose ends still need containment polish.
- Final v049 40 t crane, 30 t support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact PR-004→PR-005 traceable handoff all pass. Barcode `503184064100010` and 15 native mover bindings remain exact.
- Decision audit `Saved/Audits/press_shop_pr005_floor_junction_visual_gate_v049.json` is **CROSS-AISLE JUNCTION DIRECTION PASS / PAINT, SERVICE ROUTING AND RELEASE CONTEXT HOLD / NOT PROMOTED**. Retain v049 as the current floor-integration direction and move next to hydraulic-service containment.

# PR-005 hydraulic service-routing material candidate v050 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050` is an isolated, unpromoted v049 derivative. It preserves all authored hydraulic geometry and every station/equipment transform.
- The seven exact imported service slots now have distinct controlled materials: pressure red, return blue, union steel, hose rubber, anti-slip grip, crossing tread and galvanised carrier. This corrects the v044 inheritance that collapsed most service parts into the dark-machine material.
- Fresh player, elevated and whole-line runtime views under `Saved/ValidationScreenshots/PressShopIntegration/v050_pr005_runtime/` prove the capped red/blue unions, carrier, crossing plates and flexible hoses are a purposeful hydraulic assembly rather than a loose product strip.
- Visual decision `Saved/Audits/press_shop_pr005_service_routing_visual_gate_v050.json` is **SEVEN SEMANTIC HYDRAULIC MATERIALS DIRECTION PASS / LONG-RUN PHYSICAL COVER AND RELEASE CONTEXT HOLD / NOT PROMOTED**. The long horizontal twin-hose section still needs modular removable tread covers while both flexible end loops remain accessible.
- Final v050 40 t crane, 30 t support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact traceable handoff all pass. Barcode `503184064100010` and 15 mover bindings remain exact. Retain the v050 materials; do not promote the map.

# PR-005 removable hydraulic service covers v051 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051` is an isolated, unpromoted v050 derivative. Reusable source is `SourceAssets/PR005/HydraulicRouting/Candidate_v051/`.
- Five 640 x 680 x 50 mm removable galvanised panels cover 3480 mm of only the straight twin-hose run. Both flexible end zones and capped pressure/return unions remain accessible. Low yellow retainers and one inset anti-slip pad per panel reuse the v048/v050 controlled materials.
- The first four-rib treatment was visually rejected because it combined with inherited clamps into a conveyor-like silhouette. The corrected solid-panel treatment is retained; original clamps now read at the removable seams.
- Unlike the painted route modules, v051 uses real `BlockAll` collision and contributes to navigation. Final primary/support crane, valid non-partial 1396.953125 cm operator path, collision/navigation and exact handoff gates all pass; barcode `503184064100010` and all 15 mover bindings remain exact.
- Fresh player, elevated and whole-line images are under `Saved/ValidationScreenshots/PressShopIntegration/v051_pr005_runtime/`. Decision `Saved/Audits/press_shop_pr005_service_covers_visual_gate_v051.json` is **DIMENSIONED REMOVABLE SERVICE COVER DIRECTION PASS / IDENTITY, WEAR AND RELEASE CONTEXT HOLD / NOT PROMOTED**.
- Retain v051. Next add small hydraulic-service/no-step identity and restrained wear, then workers/logistics and final lighting without altering the proven cover collision or equipment datums.

# PR-005 functional service identity and restrained wear v052 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052` is an isolated, unpromoted v051 derivative. Reusable source is `SourceAssets/PR005/HydraulicRouting/Candidate_v052/`; accepted v006 and rejected v007-v010 remain untouched.
- Three identity iterations were rejected during fixed-camera review: top-only wording was invisible at player distance, the first vertical export faced away, and the next was mirrored/inverted. The corrected compact gameplay-side plate reads `HYD SERVICE / NO STEP` at normal distance without advertisement-scale branding. No in-world Line Boss wording is present.
- Eight sparse fixed edge-contact marks add restrained service use without procedural grime or paint-chip texture on galvanised metal. Cover dimensions, accessible flexible ends, material semantics, real `BlockAll` collision, navigation contribution and every equipment datum remain unchanged.
- Final v052 gates pass: 40 t crane, 30 t support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact traceable PR-004-to-PR-005 handoff. Barcode `503184064100010` and all 15 native mover bindings remain exact.
- Fresh player, elevated and whole-line runtime images are under `Saved/ValidationScreenshots/PressShopIntegration/v052_pr005_runtime/`. Decision `Saved/Audits/press_shop_pr005_service_identity_visual_gate_v052.json` is **FUNCTIONAL SERVICE IDENTITY AND RESTRAINED WEAR DIRECTION PASS / WORKERS, LOGISTICS AND FINAL LIGHTING HOLD / NOT PROMOTED**.
- Retain v052 as the current PR-005 service-detail direction; do not promote. Next add workers and logistics context without changing proven collision or machine datums, then perform final lighting and fresh Pro-reference inspection.

# PR-005 stationary logistics candidate v053 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053` is an isolated, unpromoted v052 derivative. It adds one contained licensed return stillage, one controlled-blue service pallet and three controlled safety-yellow service crates outside the proven operator route.
- The first fixed-camera set was rejected because two views missed the cluster and a structural column obstructed the third. Corrected player, elevated and whole-line runtime views are under `Saved/ValidationScreenshots/PressShopIntegration/v053_pr005_runtime/` and pass the restrained stationary-logistics direction check.
- The Factory Environment forklift remains quarantined because neither its neutral vendor finish nor the experimental layered wrapper passed isolated visual review. The old UE4 mannequin from the pack is excluded because it is not a release-quality worker.
- All five v053 gates pass: primary crane, support-crane dispatch/return, runtime navigation, collision/navigation and exact traceable PR-004-to-PR-005 handoff. Navigation remains valid, non-partial and exactly `1396.953125 cm`.
- Decision: `Saved/Audits/press_shop_pr005_logistics_visual_gate_v053.json` is **STATIONARY LOGISTICS DRESSING DIRECTION PASS / RELEASE WORKERS AND FINAL LIGHTING HOLD / NOT PROMOTED**.
- Retain v053; preserve accepted PR-004 v006 and retained v052. Do not promote until release-quality workers and final integrated lighting pass fresh Pro-reference inspection.

# PR-006 modular precision leveller candidate v054 (2026-08-04, latest)

- CAD-first source is `SourceAssets/PR006/PrecisionCassetteLeveller/Candidate_v001/`: 67 semantic local-pivot modules, a placement manifest, Blender source, 65 imported machine meshes plus three native identity rows, and fixed Blender/Unreal evidence.
- The machine honours the 1500 mm strip and approved `(-1700, -2000, 0)` world datum. It contains 9 lower and 10 upper work rolls, removable upper/lower cassette structure, four gap-control points, three drive motors, entry/exit guides and threaded-strip presentation.
- The first Unreal capture was rejected as nearly black; restrained local task lights corrected the machine read. Imported mesh lettering was mirrored and rejected; native Unreal text now supplies Cairnwell Automotive, PR-006 and cassette identity.
- Close operator/drive views earn a modular machine direction pass. The wide view is a deliberate full-line integration reject because PR-007 physically belongs between PR-005 and PR-006 and that process gap is still empty.
- All inherited v054 gates pass, including unchanged valid/non-partial `1396.953125 cm` navigation. This is not a PR-006 runtime pass: guarding, live HMI, cassette/roll-gap controller, faults and save state remain open.
- Decision: `Saved/Audits/press_shop_pr006_leveller_visual_gate_v054.json` is **MODULAR PRECISION LEVELLER DIRECTION PASS / FULL-LINE INTEGRATION REJECT / NOT PROMOTED**. Build PR-007 next, then recompose and regate the connected strip line.

# PR-007 washer/lube candidate v055 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055` is an isolated, unpromoted v054 derivative. Reusable CAD-first source is `SourceAssets/PR007/WasherLubeUnit/Candidate_v001/` with 78 semantic FBX modules, a placement manifest, source audit and fixed Blender evidence.
- The 1500 mm-strip module uses the approved `(-2700, -2000, 0)` world datum and contains four spray headers, 20 nozzles, two fluid tanks, pumps, duplex filters, lift hoods, mist extraction and service doors. Native Unreal text supplies Cairnwell Automotive, PR-007 and washer/lube identity.
- Fresh operator, service and connected-line runtime images are under `Saved/ValidationScreenshots/PressShopIntegration/v055_pr005_runtime/`. Close views pass the modular machine direction check and the connected view now proves the correct physical sequence PR-005 to PR-007 to PR-006.
- All five inherited v055 gates pass: 40 t crane transfer, 30 t support-crane dispatch/return, valid non-partial `1396.953125 cm` navigation, collision/navigation and exact traceable PR-004-to-PR-005 handoff.
- Decision: `Saved/Audits/press_shop_pr007_washer_lube_visual_gate_v055.json` is **MODULAR WASHER/LUBE AND CONNECTED STRIP-LINE DIRECTION PASS / GUARDING, HMI, RUNTIME FLUID AND SAVE-STATE HOLD / NOT PROMOTED**. Next add explicit continuous strip bridges, approved open-mesh guarding and a live local HMI, then implement and gate pump/lift-hood state without disturbing the inherited station authorities.

# PR-007 strip continuity, guarding and compact HMI v056 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056` is an isolated, unpromoted v055 derivative. Dimensioned reusable source is `SourceAssets/PR007/StripBridges/Candidate_v001/`.
- Endpoint audit proved a 512.5 cm PR-005-to-PR-007 gap with a 10.475 cm rise and a 257.5 cm PR-007-to-PR-006 gap. Two exact 150 cm-wide strip bridges, four roller supports and their frames now close those visual breaks without adding strip collision or changing station datums.
- Six approved v002 open-mesh panels and ten anchored posts guard only the exposed transition-table hazards. The enclosed washer/lube body is not surrounded by redundant fencing.
- Fixed-camera review rejected the first full shared HMI cabinet because its service internals faced gameplay and the large cabinet competed with the machine. The corrected compact pedestal touchscreen retains the validated display surface and Cairnwell/Moorcross/PR-007 status presentation.
- Fresh corrected connected-strip, HMI and elevated images are under `Saved/ValidationScreenshots/PressShopIntegration/v056_pr005_runtime/`. All five inherited gates pass; navigation remains valid, non-partial and exactly `1396.953125 cm`.
- Decision: `Saved/Audits/press_shop_pr007_strip_guard_hmi_visual_gate_v056.json` is **DIMENSIONED CONTINUOUS STRIP, OPEN-MESH GUARD AND COMPACT HMI DIRECTION PASS / PR-007 NATIVE RUNTIME, FLUID AND SAVE-STATE HOLD / NOT PROMOTED**. Next implement actual PR-007 pump/hood permissives and persisted fluid state; the current screen is presentation-only.
# 2026-08-04 continuation checkpoint — PR-007 native runtime v057

- Current retained runtime direction, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057`, isolated from v056. Accepted PR-004 v006 remains untouched; rejected v007-v010 remain rejected.
- Native `ALBPR007Station` now owns Priming/Running/Stopping/Fault state, guard and strip-threaded permissives, wash/lube levels, filter differential, mist extraction, controlled stop, safe fault reset, production travel and running hours. Press Shop save format advances to v5 with versioned `FLBPR007SaveState`; moving restores safely to Ready.
- Seven authored modules are bound to native local pivots: wash hood, both pump motors and four lower process rollers. The compact Cairnwell/Moorcross touchscreen is runtime-bound and shows live Running or Fault state; it remains a simple touchscreen rather than a redundant full console.
- Focused native automation `LineBoss.PressShop.PR007.RuntimeAndSave` passes. Map PIE audit `Saved/Audits/press_shop_pr007_runtime_v057.json` passes Priming→Running, fluid consumption, strip travel, hood closure, live HMI, controlled stop, restart, `GUARD_OPEN` trip, fault HMI and safe reset with all seven mover bindings exact.
- All five inherited v057 gates pass: primary crane, support crane, exact traceable PR-004→PR-005 handoff, collision/navigation and a valid non-partial navigation path of exactly `1396.953125 cm`.
- Fresh fixed evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v057_pr005_runtime/`; the readable close screen shows `RUNNING | WASH 82% | LUBE 76%`. See `Saved/Audits/press_shop_pr007_runtime_visual_gate_v057.json`.
- Decision: **NATIVE RUNTIME AND LIVE HMI DIRECTION PASS / RELEASE MACHINE DETAIL, PROCESS EFFECTS AND CLEAN EDITOR EXIT HOLD / NOT PROMOTED**. The simplified washer/lube casing, process visualization, final material wear and occasional post-audit Unreal shutdown `0xC0000005` remain open. Continue full Press Shop work without claiming v057 release-quality.

# PR-008 modular servo-blanking candidate v058 (2026-08-04, latest)

- Current retained PR-008 direction, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058`, isolated from v057. Accepted PR-004 v006 remains untouched and rejected v007-v010 remain rejected.
- Reusable CAD-first source is `SourceAssets/PR008/ServoBlankingLine/Candidate_v001/`: 79 semantic local-pivot modules covering loop control, servo feed, telescopic support, four-column pre-punch/cut press, scrap handling, outfeed, blank inspection, service cabinets and HPU at the approved `(-500, -2000, 0)` datum.
- Fixed-camera review rejected the first material classifier because entire feed housings read blue. Corrected v058 reserves blue for actual servos, encoders, hydraulic motors and pre-punch cylinders; grey housings/cabinets, charcoal frames, worked steel and safety-yellow process parts now give a credible modular direction.
- Fresh operator, drive and connected-line images are in `Saved/ValidationScreenshots/PressShopIntegration/v058_pr005_runtime/`. They pass only the modular/material direction. The design is still blockout quality relative to the requested authoritative Pro machine pack; guarding, live HMI, runtime authority, faults, restoration/save state, release detail and readable identity remain open.
- Exact world-bounds audit `Saved/Audits/press_shop_pr006_pr008_strip_continuity_v058.json` proves a 305 cm unsupported longitudinal strip gap, with zero lateral offset and only a 2.5 cm height change. Add a supported 1500 mm modular transition; do not stretch either machine envelope.
- All five inherited v058 gates pass: primary crane transfer, support-crane dispatch/return, exact traceable PR-004-to-PR-005 handoff, collision/navigation and valid non-partial navigation of exactly `1396.953125 cm`.
- Decision: `Saved/Audits/press_shop_pr008_servo_blanking_visual_gate_v058.json` is **MODULAR SERVO-BLANKING DIRECTION PASS / PRO REFERENCE, GUARD, HMI, RUNTIME AND STRIP-CONTINUITY HOLD / NOT PROMOTED**. Retain v058 as layout/material evidence only while the PR-008-to-PR-010/four-train Pro design pack is prepared.

# PR-008 supported transition and local guarding v059 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059` is an isolated, unpromoted v058 derivative. Reusable dimensioned Blender source is `SourceAssets/PR008/StripTransition/Candidate_v001/`.
- The exact 305 cm longitudinal break is closed by a 1500 mm-wide steel transition with a 25 mm fall and three serviceable roller stands. Unreal bounds prove both joints overlap by only `0.007369995 cm` and lateral centre error is `0.000007629 cm`; see `Saved/Audits/press_shop_pr008_transition_continuity_v059.json`.
- Four approved v002 open-mesh panels and six anchored posts guard the exposed transition rollers without stretching or enclosing the PR-006/PR-008 machine bodies. Fresh operator, elevated and connected-line images are in `Saved/ValidationScreenshots/PressShopIntegration/v059_pr005_runtime/`.
- All five inherited v059 gates pass: both crane authorities, exact traceable PR-004-to-PR-005 handoff, collision/navigation and valid non-partial navigation of exactly `1396.953125 cm`.
- Two capture processes returned Windows `0xC0000005` only after valid PNG output; the third exited normally. Clean repeated screenshot-process exit remains an explicit hold.
- Decision: `Saved/Audits/press_shop_pr008_transition_guard_visual_gate_v059.json` is **CONTINUOUS SUPPORTED STRIP AND LOCAL OPEN-MESH GUARD DIRECTION PASS / PRO REFERENCE, HMI, RUNTIME, RELEASE DETAIL AND CLEAN CAPTURE EXIT HOLD / NOT PROMOTED**. Retain the bridge source; defer final machine-wide access/guard layout to the incoming Pro pack.

# PR-008 native servo-blanking runtime v060 (2026-08-04, latest)

- Current retained PR-008 runtime checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060`, isolated from v059. Accepted PR-004 v006 remains untouched; rejected v007-v010 remain rejected.
- New native `ALBPR008Station` owns Isolated/Ready/Threading/Running/Stopping/Fault state, guards, strip availability, feed-servo and hydraulic permissives, scrap/outfeed faults, blank recipe, strip travel, blank counting, controlled stop/reset and safe restore. `ULBPressShopSaveGame` advances from format v5 to v6 with versioned `FLBPR008SaveState PR008`.
- UE 5.8 native build passes. Focused automation `LineBoss.PressShop.PR008.RuntimeAndSave` is 1/1 successful in `Saved/Automation/PR008_Runtime_v001/index.json`.
- Twelve semantic modules are bound to seven native movers: feed rolls, six telescope beams/drives, press slide, pre-punch die, guillotine beam and outfeed roll. Map PIE receipt `Saved/Audits/press_shop_pr008_runtime_v060.json` passes Threading-to-Running, first blank production, scrap accumulation, live HMI, controlled stop/restart, `BLANK_OUTFEED_BLOCKED` fault presentation and safe reset/save.
- A compact Cairnwell/Moorcross touchscreen is native-bound. Fresh close evidence reads `RUNNING | BLANKS 1 | 1450 mm`; process and connected-line views are in `Saved/ValidationScreenshots/PressShopIntegration/v060_pr005_runtime/`. All final capture sessions exit normally.
- All five inherited v060 gates pass, including valid non-partial navigation of exactly `1396.953125 cm`.
- Decision: `Saved/Audits/press_shop_pr008_runtime_visual_gate_v060.json` is **NATIVE RUNTIME, LIVE HMI AND CONTINUOUS-STRIP DIRECTION PASS / AUTHORITATIVE PRO MACHINE, RELEASE DETAIL, PROCESS EFFECTS AND FULL GUARD LAYOUT HOLD / NOT PROMOTED**. Retain the runtime authority and rebind it to the incoming Pro geometry rather than treating the current blockout as final art.
# PR-006 native runtime candidate v061 (2026-08-04, latest checkpoint)

- `/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061` is an isolated, unpromoted native-runtime checkpoint. PR-004 v006 remains protected and rejected v007-v010 remain rejected.
- `ALBPR006Station` owns calibration, Ready/Running/Stopping/Fault sequencing, cassette/guard/strip permissives, a 1.15 mm gap recipe, strip travel, drive load, controlled stop/reset and safe persistence. Press Shop save format is v7 with `FLBPR006SaveState PR006`.
- Focused automation is 1/1 green. PIE receipt `Saved/Audits/press_shop_pr006_runtime_v061.json` proves 28 exact mover bindings, calibration, Running, 58% load, stop/restart, `CASSETTE_UNLOCKED` fault/HMI, reset and safe save.
- Fresh fixed images are under `Saved/ValidationScreenshots/PressShopIntegration/v061_pr005_runtime/`; the close screen visibly reads `RUNNING | GAP 1.15 mm | LOAD 58%`. Two capture processes returned the known post-PNG `0xC0000005`, while one exited normally.
- `Saved/Audits/press_shop_pr006_runtime_visual_gate_v061.json` records **NATIVE RUNTIME/LIVE-HMI DIRECTION PASS / GUARD ACCESS, PROCESS DETAIL, FULL-LINE FINISH AND CLEAN THREE-PROCESS EXIT HOLD / NOT PROMOTED**.

# Cairnwell remaining Press Shop machinery pack intake v001 (2026-08-04, current authority)

- The supplied archive is preserved at `C:/Users/greg_/Downloads/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0.zip` and staged non-destructively at `SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/`.
- SHA-256 is `7021A2E5DE71F89306E1AA6CB96D2F6018870404E01F4F83FF27D5F6B2BC399A`; archive traversal audit is clean and all 28 internally manifested files verify.
- The pack is now authoritative under its stated hierarchy: owner brief/fixed datums, `authority_and_assumptions.json`, numeric CSV/JSON schedules, engineering spec, then visuals. Numeric tables override illustrations; EST values require blockout validation.
- PR-008 fixed datum is `(-500,-2000,0)` cm and planning envelope is `10400 x 5560 x 4490 mm`. Project datum progression proves a `-90 degree` station yaw: Pro local `+Y` material flow maps to world `+X`, and local `+X` maps to world `-Y`.
- This reveals that the v058-v060 PR-008 visual layout used the wrong source flow axis. Preserve v060 as runtime/HMI/continuity evidence, but supersede its visual blockout for an exact Pro-envelope rebuild; do not delete or promote it.
- The eventual native rebind must move the telescope on local Y, add edge-guide travel, service-door/scrap-flap movers, and align faults with the broader Pro vocabulary. The current HMI must also move to the exact transformed Pro position.
- In-world identity remains Cairnwell Automotive / Moorcross Works. Any `Line Boss` wording on reference-sheet titles is document context only and must never be copied into the factory.
- Full intake/decision receipt: `Saved/Audits/cairnwell_press_shop_remaining_machinery_pack_intake_v001.json`. Next build the ten-module isolated PR-008 Pro envelope candidate and inspect fresh fixed Unreal views before detail work or promotion.

# PR-008 Pro engineering-envelope candidate v062 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062` is an isolated v061 derivative and the current PR-008 spatial contract. It is engineering blockout only and is not promoted.
- Reusable source is `SourceAssets/PR008/ServoBlankingLine/ProEnvelope_v001/`: a Blender file, build script, 12 semantic FBXs, manifest, source audit and three source renders. Ten cages represent the exact scheduled modules; separate assets represent the fixed planning envelope and 1500 mm strip datum.
- All modules use the fixed `(-500,-2000,0)` cm datum and validated `-90 degree` yaw. The fixed cage measures `1040.000000 x 556.000000 x 449.000153 cm` in Unreal; HMI centre is exactly `(-185,-2252,110)` cm.
- v062 preserves but hides 114 superseded v058/v059/v060 PR-008 visual actors only in this derivative. Native PR-008/PR-006 authority and PR-004–PR-007 assets are preserved. Envelope meshes are `NoCollision` and navigation-neutral.
- Fresh operator/elevated/connected images are under `Saved/ValidationScreenshots/PressShopIntegration/v062_pr005_runtime/`. They pass Pro datum, axis, sequence, HMI-side and envelope review, but explicitly do not pass as machine art.
- One existing hall column, `LB_PRESS_Column_0_-2250`, intersects the fixed outer planning envelope. The guard/service-aisle design must coordinate around it without moving the fixed Pro datum merely to clear a placeholder.
- PR-006 output to Pro PR-008 entry remains a 305 cm gap, now with a measured 25.5 cm downward centre-height change. The old v059 25 mm-fall bridge is superseded for the Pro layout; build a new supported entry-loop transition rather than redesigning PR-006 or stretching either machine.
- Rows 08/09 use `Z=0` for visibly floor-standing utilities despite the table heading saying centre. v062 records the EST interpretation as base-on-floor; retain this as an open reference assumption.
- All inherited v062 technical gates pass after dependency-ordered rerun: both cranes, exact traceable handoff, complete valid/non-partial `1396.953125 cm` navigation and collision/navigation.
- Decision is `Saved/Audits/press_shop_pr008_pro_envelope_visual_gate_v062.json`: **PRO SPATIAL CONTRACT PASS / ENTRY-LOOP AND COLUMN COORDINATION HOLD / ENGINEERING BLOCKOUT ONLY / NOT PROMOTED**.

# PR-008 Pro entry-loop transition candidate v063 (2026-08-04, latest)

- Current connected Pro interface is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063`, isolated from v062. The old v059 25 mm-fall transition remains preserved and superseded for the Pro layout.
- Reusable source is `SourceAssets/PR008/StripTransition/ProEntryLoop_v002/`. It uses the measured PR-006 endpoint `(-1325,-2000,120.5)` cm and Pro PR-008 entry `(-1020,-2000,95)` cm: 3050 mm gap, 255 mm fall and 4.779 degree slope.
- Seven Blender-authored modules provide the 1500 mm strip, three serviceable support frames and three rolls. Four approved open-mesh panels plus six posts protect both exposed sides.
- Exact Unreal bounds receipt `Saved/Audits/press_shop_pr008_pro_entry_loop_continuity_v063.json` passes both joints at `-0.074981689 cm` (minute overlap) with `0.000007629 cm` lateral error.
- Fresh operator/elevated/connected images are under `Saved/ValidationScreenshots/PressShopIntegration/v063_pr005_runtime/`. They pass support, continuity and open-mesh direction; final bearings/adjusters/anchors, gate/light-curtain/interlock layout and release materials remain open.
- Both cranes, exact PR-004-to-PR-005 handoff, complete valid/non-partial `1396.953125 cm` navigation and collision/navigation pass after v063.
- `Saved/Audits/press_shop_pr008_pro_entry_loop_visual_gate_v063.json` records **EXACT CONTINUITY/SUPPORT/GUARD DIRECTION PASS / FINAL SAFETY AND RELEASE DETAIL HOLD / NOT PROMOTED**. Continue detailed PR-008 module construction inside the v062 cages, then coordinate the full guard line around the measured hall column.

# PR-008 detailed Module 01 candidate v064 (2026-08-04, latest)

- Current detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module01Candidate_v064`, isolated from v063. It replaces only Pro cage 01; cages 02-10 remain visible engineering contracts.
- Reusable source is `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/`. Twenty semantic FBXs supply the Cairnwell green/charcoal entry-loop frame, three rolls and replaceable sleeves, adjustable guides and handwheels, loop sensors, pinch shielding, services, reachable E-stop and identity plate.
- The initial source build failed containment because the E-stop projected 65 mm beyond the fixed envelope. It was corrected inward and rebuilt. Unreal union bounds now pass the exact Module 01 envelope; see `Saved/Audits/press_shop_pr008_module01_candidate_v064.json`.
- Fresh fixed evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v064_pr005_runtime/`. The first operator composition is explicitly rejected because foreground mesh obscures the machine; the replacement inspection view clearly reads process, controls and Cairnwell/Moorcross identity.
- All inherited v064 gates pass, including both cranes, exact PR-004-to-PR-005 handoff, collision/navigation and valid non-partial `1396.953125 cm` navigation.
- Branding is a reusable diegetic identity/material layer. Earlier machinery designed before the Cairnwell/Moorcross decision is not rebuilt for branding alone; retain valid engineering/runtime work and rebuild only for an authoritative dimensional, functional or inspected visual conflict. Line Boss remains prohibited in-world.
- `Saved/Audits/press_shop_pr008_module01_visual_gate_v064.json` records **DETAILED MODULE 01 DIRECTION PASS / NATIVE ROLL BINDING, LAYERED WEAR, FINAL GUARD AND RELEASE DETAIL HOLD / NOT PROMOTED**. Continue with exact Pro Module 02 edge tracking.

# PR-008 detailed Module 02 candidate v065 (2026-08-04, latest)

- Current detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module02Candidate_v065`, isolated from v064. It replaces only Pro cage 02; detailed Module 01 remains intact and cages 03-10 remain engineering contracts.
- Source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` now includes 14 Module 02 semantic FBXs: rigid edge-tracking frame, support rolls/sleeves, precision rails and protected ball screw, two correctly pivoted guide carriages, redundant edge sensors, geared drive, limits and service routing.
- The first Blender gate caught a 20 mm service overhang; Unreal then caught applied-bevel/FBX bounds that Blender had understated. Hardware/origin placement was corrected until both source and Unreal pass the exact `2200 x 650 x 1450 mm` envelope. Never enlarge the fixed Pro cage to hide an asset error.
- The two guide carriages carry the authoritative local-X `+/-150 mm` at `40 mm/s`, centred-safe movement contract. They remain unbound to native PR-008 runtime.
- Fresh fixed images are under `Saved/ValidationScreenshots/PressShopIntegration/v065_pr005_runtime/`. The guard-obscured drive view and earlier wrong-subject close views are rejected diagnostics. The current elevated three-quarter inspection view passes the process/mechanism direction, while readable Module 02 identity remains a release hold.
- All inherited v065 gates pass; navigation remains valid, non-partial and exactly `1396.953125 cm`.
- `Saved/Audits/press_shop_pr008_module02_visual_gate_v065.json` records **EDGE-TRACKING GEOMETRY/MOVING-PIVOT/PROCESS DIRECTION PASS / NATIVE RUNTIME, READABLE IDENTITY, WEAR AND RELEASE DETAIL HOLD / NOT PROMOTED**. Continue with exact Pro Module 03 servo feed.

# PR-008 detailed Module 03 candidate v066 (2026-08-04, latest)

- Current detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module03Candidate_v066`, isolated from v065. Detailed Modules 01-02 remain intact; only Pro cage 03 is replaced.
- Source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` adds 19 Module 03 semantic FBXs: rigid servo-feed frame, entry/exit support rolls and sleeves, top/bottom driven rolls and sleeves, bearing/gap-control set, paired geared servo drives and guarded couplings, encoder feedback, pinch shielding, service hardware, E-stop and identity plate.
- The first Blender gate rejected a 30 mm side-drive infringement and roughly 10 mm upstream E-stop/plate infringement. They were moved inward; source and Unreal now pass the exact `2600 x 1450 x 1950 mm` cage.
- Four roll/sleeve assets use shaft-centre pivots and the authoritative local-X continuous `12 rpm`, stop/brake-safe contract. Blue is restricted to actual powered gap/servo equipment.
- Fresh fixed Unreal evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v066_pr005_runtime/`. Drive and inspection views pass the servo-feed mechanism/process direction; the integrated plate is not yet strongly readable and the dominant black drive cover remains a release-detail review item.
- All inherited v066 gates pass, including valid non-partial `1396.953125 cm` navigation.
- `Saved/Audits/press_shop_pr008_module03_visual_gate_v066.json` records **SERVO-FEED GEOMETRY/ROTARY-PIVOT/DRIVE/PROCESS DIRECTION PASS / NATIVE REBIND, READABLE IDENTITY, WEAR AND RELEASE DETAIL HOLD / NOT PROMOTED**. Continue with exact Pro Module 04 telescopic strip support.

# PR-008 detailed Module 04 candidate v067 (2026-08-04, latest)

- Current detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module04Candidate_v067`, isolated from v066. Detailed Modules 01-03 remain intact; only Pro cage 04 is replaced.
- Source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` adds 13 semantic FBXs: fixed support bed, linear guides/wear strips, three nested moving stages, rack/pinion servo drive, cable carrier, home/end/position sensors, edge protection, service hardware, E-stop and identity.
- The first source gate rejected a 20 mm fully nested tip-stage and 5 mm motor infringement. Unreal then exposed incorrect joined-asset origin reflection: the drive appeared 950 mm outside its allowed world bound and services exceeded the downstream face. Drive/service origins were recentered on their geometry; both Blender and Unreal now pass the exact `2400 x 2000 x 1300 mm` safe/retracted cage.
- Three stage actors share the authoritative local-Y `0-1200 mm`, `60 mm/s`, retracted-safe command using one-third, two-thirds and full-travel ratios. This is authored pivot/contract evidence only; native movement is not yet bound.
- Fresh fixed Unreal evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v067_pr005_runtime/`. It passes the safe/retracted mechanical/process direction. Live extension, readable integrated identity, underside detail and release materials remain mandatory holds.
- All inherited v067 gates pass, including valid non-partial `1396.953125 cm` navigation.
- `Saved/Audits/press_shop_pr008_module04_visual_gate_v067.json` records **TELESCOPIC GEOMETRY/THREE-STAGE-PIVOT/DRIVE/PROCESS DIRECTION PASS / LIVE EXTENSION, NATIVE REBIND, IDENTITY, WEAR AND RELEASE DETAIL HOLD / NOT PROMOTED**. Continue with exact Pro Module 05 pre-punch press.

# PR-008 detailed Module 05 candidate v068 (2026-08-04, latest)

- Current detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068`, isolated from v067. Detailed Modules 01-04 remain intact; only Pro cage 05 is replaced.
- Source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` adds 15 semantic FBXs: four-column frame and tooling, moving pre-punch slide, hydraulics, guide/sensor set, slug drawer, moving scrap flap, two moving service doors, pinch protection, services, Cairnwell/Moorcross identity and operator-side E-stop.
- Source validation caught lift-eye and E-stop envelope infringements; the E-stop was also corrected from upstream-facing to the outward operator face. Unreal then caught reflected off-centre FBX origins on doors/services. Recentered export origins preserve the approved geometry and bring the assembly inside the exact `2850 x 1850 x 3500 mm` cage in both source and Unreal.
- Four authored movers retain safe contracts: slide local-Z down `0-220 mm` at `120 mm/s`, service doors `0-110 degrees` closed-safe and scrap flap `0-70 degrees` at `15 degrees/s` closed-safe. Runtime authority, faults and persisted safe restore are not yet rebound.
- All inherited v068 gates pass, including both cranes, exact handoff, collision/navigation and valid non-partial `1396.953125 cm` navigation.
- Fresh fixed evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v068_pr005_runtime/`. It passes the pre-punch mechanism/process direction, but the Pro comparison holds promotion for industrial density/enclosure, readable identity, wear/services/fasteners, live motion/tooling/scrap proof and complete interlocked guarding/light curtains. Diagnostic white engineering cages must be hidden before any final capture.
- `Saved/Audits/press_shop_pr008_module05_visual_gate_v068.json` records **PRE-PUNCH GEOMETRY/SLIDE/DOOR/FLAP/E-STOP/PROCESS DIRECTION PASS / NATIVE REBIND, RELEASE GUARDING, IDENTITY, WEAR AND CAGE-VISIBILITY HOLD / NOT PROMOTED**. Continue exact Pro Module 06 cut-to-length shear.

# Fully automated Press Shop / robot-only maintenance owner decision (2026-08-04, current authority)

- The game does not require worker NPCs or pedestrian population simulation. The Press Shop is fully automated and the player operates as a remote factory manager through HMIs and management controls.
- Machine faults are resolved by dispatching LB-MR01, not by a manual repair minigame or visible technician. The retained gameplay pressure is robot/route availability, correct tool and part inventory, battery, automated isolation/exclusion authority, diagnosis/repair time and lost production.
- Existing `ALBMaintenanceAMR` tasks already cover inspection, diagnosis, lubrication, sensor cleaning, parts delivery, approved fastener service, leak classification and approved module exchange. Heavy repair is represented by modular exchange and off-line depot time/cost rather than technician animation.
- LB-CR01 remains the routine cleaning authority. Multiple docked robots are allowed; certified routes, crane separation and machine stopping points remain mandatory.
- Historical forward-looking worker/logistics holds are superseded only in their worker/pedestrian portion. Automated logistics, material flow, guarding, light curtains, exclusion zones, zero-energy isolation, controlled stop/reset and all technical/visual promotion gates remain required.
- `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Data/AUTOMATED_PRESS_SHOP_MAINTENANCE_AUTHORITY_v001.json` is the machine-readable owner authority. PR-004 now records `PR004_AUTOMATED_CHECK_*` evidence and asks for player authorisation; MR01 isolation text now requires proved automated isolation and zero-energy lock.

## Control-room-only player model (2026-08-04 owner authority)

- The player stays in the control room and performs the entire game remotely. Do not budget factory-floor walking, a floor player avatar, worker NPCs or manual repair interaction as release requirements.
- All production, recipes, crane/material handling, machine commands, fault diagnosis, MR01/CR01 dispatch, parts/consumables, restoration and restart approval are exposed through control-room HMIs and management screens.
- Fixed station CCTV plus selectable inspection drones are the observation layer. Drones may carry visual/thermal/diagnostic sensors but do not repair machines. Their navigation must respect active cranes, machine exclusion volumes and no-fly states.
- Runtime camera performance rule: selected feed at full rate/quality; inactive feeds use cached or throttled thumbnails. Never run the entire camera wall as simultaneous full-resolution SceneCapture feeds.
- Existing direct world-click paths are prototype/test adapters only. Release interactions route the same native authorities through remote control-room commands; PR-004 Unpackage remains one automated state transition with no floor operator animation.

## Autonomous support-robot charging checkpoint (2026-08-04)

- `ALBSupportRobot` now owns a reusable certified automatic-charging route. At or below its configured idle reserve threshold it enters `Returning`, follows the certified docking route, docks using the route destination dock ID, charges to 100 percent and returns to `Docked`/available without player micromanagement.
- Critical-reserve handling attempts the certified automatic return before declaring a battery fault. `bAutomaticChargeReturnActive` prevents the dock/return loop from immediately redispatching itself.
- UE 5.8 native editor compilation passed after the implementation and again after the focused test/getter additions.
- Focused automation `LineBoss.SupportRobots.Common.AutomaticCharging` is 1/1 green. Evidence is `Saved/Automation/SupportRobot_AutomaticCharging_v001/` and `Saved/Logs/SupportRobot_AutomaticCharging_v001.log`; it proves 25 percent reserve -> autonomous certified return -> destination dock ID -> increasing charge -> 100 percent -> `Docked`/available.
- This common authority is reusable by both LB-CR01 and LB-MR01. It does not close either robot's visual promotion gate and does not weaken certified-route, dock, charger, collision or screenshot requirements.

# PR-008 detailed Module 06 candidate v069 (2026-08-04, latest)

- Current retained detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module06Candidate_v069`, isolated from v068 and replacing only Pro cage 06. Accepted PR-004 v006 and rejected PR-004 v007-v010 remain untouched.
- Source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` adds 16 semantic FBXs: enclosed guillotine frame, replaceable lower knife cassette, moving blade beam, twin servo-hydraulic drive, hold-down array, infeed/outfeed support, guides/sensing, trim drawer, service/access panels, light curtain, services/lifting hardware, identity and outward operator-side E-stop.
- Blender and Unreal pass the unchanged `2850 x 1200 x 3000 mm` Module 06 envelope. Unreal measured min `(-314.750002,-2139.999985,3.0)` cm and max `(-197.000008,-1857.5,237.499985)` cm; see `Saved/Audits/press_shop_pr008_module06_candidate_v069.json`.
- One separated blade-beam actor carries the Pro local-Z down `0-180 mm` at `300 mm/s`, top-safe movement contract. Native motion, cut sequencing, faults and persisted safe restore are not yet rebound.
- A fresh UE 5.8 editor build succeeds. Both crane runtime gates, exact PR-004-to-PR-005 handoff, collision/navigation and valid non-partial navigation of exactly `1396.953125 cm` pass after dependency-ordered execution.
- Four fixed 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v069_pr005_runtime/`. Against Pro Sheet 01 they pass shear/process/E-stop/connected-line direction, while promotion remains held for mechanical density, services/fasteners/anchors, layered wear, readable identity, live cut/blank/scrap proof, native fault/save restore, complete interlocked guarding/light curtains and removal of visible white planning cages.
- `Saved/Audits/press_shop_pr008_module06_visual_gate_v069.json` records **MODULE 06 DIRECTION PASS / RELEASE DETAIL, LIVE PROCESS, NATIVE REBIND, GUARDING AND CLEAN-CAPTURE HOLD / NOT PROMOTED**. Continue exact Pro Module 07 discharge rollers.

# PR-008 detailed Module 07 candidate v070 (2026-08-04, latest)

- Current retained detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module07Candidate_v070`, isolated from v069 and replacing only Pro cage 07. Accepted PR-004 v006 and rejected PR-004 v007-v010 remain untouched.
- Reusable dimensioned source is `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module07_discharge_v001.py`. Nineteen semantic FBXs provide the frame, seven individually pivoted rollers, bearings, guarded drive, guides, blank/skew sensing, representative cut blank, approved open-mesh sides, outfeed light curtain, services, attached identity and operator-side E-stop.
- Source validation initially rejected E-stop, drive, frame and light-curtain infringements. Components were moved inward instead of enlarging the fixed envelope. Blender now measures min `(-1.315,3.1,0.3)` m and max `(1.3,4.8,1.485)` m inside `2650 x 1750 x 1200 mm`.
- Unreal imports 19 semantic actors and seven moving rollers. World bounds min `(-189.999969,-2130.000009,29.999989)` cm and max `(-19.999985,-1868.5,148.500011)` cm pass the unchanged Pro cage; see `Saved/Audits/press_shop_pr008_module07_candidate_v070.json`.
- The rollers carry the Pro local-X continuous `0-60 m/min`, stop/brake-safe contract. Native speed, blank travel, blocked-outfeed fault and persisted safe restore are not yet rebound.
- Fresh UE 5.8 build, both cranes, exact handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation all pass in dependency order.
- Four fixed 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v070_pr005_runtime/`. Against Pro Sheet 01 they pass discharge mechanism/open-mesh/E-stop/identity/process direction, while live motion, the real PR-009 handoff, native fault/save authority, material/service density, full guarding and clean framing remain promotion holds.
- `Saved/Audits/press_shop_pr008_module07_visual_gate_v070.json` records **MODULE 07 DIRECTION PASS / LIVE HANDOFF, NATIVE REBIND, PR-009 INTERFACE, RELEASE DETAIL, FINAL GUARDING AND CLEAN-CAPTURE HOLD / NOT PROMOTED**. Continue exact Pro Modules 08-10, then rebind native PR-008 and measure the PR-009 interface.

# PR-008 detailed Module 08 candidate v071 (2026-08-04, latest)

- Current retained detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module08Candidate_v071`, isolated from v070 and replacing only Pro cage 08. Accepted PR-004 v006 and rejected PR-004 v007-v010 remain untouched.
- Reusable source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module08_hpu_v001.py` uses the v062 base-on-floor interpretation inside the exact `1100 x 900 x 1850 mm` cage. Eleven semantic FBXs provide bund/skid, reservoir, duty/standby pumps, filters, cooler, accumulator, manifold, pressure/temperature/level/leak instrumentation, hard lines, isolator and identity.
- Source validation moved 5 mm bund-lip and 2.5 mm identity infringements inward. Unreal then caught off-centre reservoir/pipe FBX reflection; geometry-centred export origins corrected it. Blender bounds min `(-2.6,3.6025,0.01)` m/max `(-1.5,4.495,1.79)` m and Unreal bounds min `(-139.750002,-1850,0.999994)` cm/max `(-50.499989,-1739.999989,179.000006)` cm pass.
- Fresh UE 5.8 build, both cranes, exact handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass in dependency order.
- Four fixed 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v071_pr005_runtime/`. The original drive image is rejected as shear-obscured; the replacement drive camera clearly reads the HPU beside Modules 06-07.
- Native pump/pressure/temperature/level/filter/leak states, fault/save evidence, MR01 maintenance dispatch, completed pressure/return connections, layered hydraulic wear, service-label density and clean planning-line-free captures remain mandatory holds. The `200 bar / 120 L/min` figure remains EST concept authority only.
- `Saved/Audits/press_shop_pr008_module08_visual_gate_v071.json` records **MODULE 08 DIRECTION PASS / NATIVE STATE, FAULT, SAVE, ROBOT MAINTENANCE, CONNECTION, MATERIAL AND CLEAN-CAPTURE HOLD / NOT PROMOTED**. Continue exact Module 09 electrical/drive cabinets.

# PR-008 detailed Module 09 candidate v072 (2026-08-04, latest)

- Current retained detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072`, isolated from v071 and replacing only Pro cage 09. Accepted PR-004 v006 and rejected PR-004 v007-v010 remain untouched.
- Reusable source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module09_cabinets_v001.py` generates 11 semantic FBXs for the plinth, separate incoming-power/servo-drive/controls-and-UPS shells, doors/hardware, controls, cooling, rear cable entry, beacon, sensors and label plates.
- Source corrections retained the exact `1250 x 650 x 2200 mm` base-on-floor envelope. Unreal caught off-centre FBX reflections; bounds-centred origins corrected all static cabinet exports without altering geometry. Unreal bounds min `(-127.500005,-2266.0,-0.000001)` cm and max `(-62.749985,-2145.0,219.000010)` cm pass.
- Dedicated `M_CA_MW_PR008_LightGrey_v001` preserves the authored electrical-enclosure finish. UE 5.8 build, both cranes, exact handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v072_pr005_runtime/`. Cabinet section/coating/placement direction passes only. Visible engineering/planning frames, obstructed views, weak identity/service labels, clean/flat materials, missing native electrical states/faults/MR01/save and missing real connections hold promotion.
- `Saved/Audits/press_shop_pr008_module09_visual_gate_v072.json` records **MODULE 09 DIRECTION PASS / IDENTITY, SERVICE DETAIL, NATIVE STATE, MATERIAL AND CLEAN-CAPTURE HOLD / NOT PROMOTED**. Continue exact Module 10 compact HMI, then native PR-008 rebind and measured PR-009 interface.

# Moorcross Works main control-room Pro reference intake (2026-08-04)

- Eight owner-supplied Pro sheets are preserved and hashed under `SourceAssets/ReferencePacks/CAIRNWELL_MOORCROSS_MAIN_CONTROL_ROOM_PRO_REFERENCE_v1.0/`; see `MANIFEST.json` and `Saved/Audits/cairnwell_control_room_pro_reference_intake_v001.json`.
- Sheet 03 fixed `14400 x 7800 mm` dimensions outrank Sheet 01 `14000 x 7500 mm` and Sheet 02 `18600 x 11400 mm` recommended alternatives.
- The set confirms the seated control-room-only player, selected-live/cached-inactive CCTV, inspection-only drone, autonomous MR01/CR01, alarm hierarchy and save-state authority. No Line Boss wording is permitted in-world.
- A parallel chat may create source assets only in `C:\Users\greg_\Projects\LineBoss_ControlRoom_Staging`; it must not open or modify this canonical Unreal repository. Integration follows PR-008 physical completion.

# PR-008 detailed Module 10 candidate v073 (2026-08-04, latest)

- Current retained detailed checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008Module10Candidate_v073`, isolated from v072 and replacing only exact Pro cage 10. This completes the scheduled physical source/import pass for PR-008 Modules 01-10 without changing accepted PR-004 v006 or rejected v007-v010.
- `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module10_hmi_v001.py` generates 10 semantic FBXs for the anchored base, sealed pedestal, neck, 15-17-inch display housing, separate touch surface, local control deck, controls, outward operator-side E-stop, rear services and Cairnwell/Moorcross label plates.
- The first Blender gate rejected base, deck, E-stop and rear-handle infringements; geometry was corrected inward. Blender bounds min `(2.22,2.93,0.461)` m/max `(2.82,3.37,1.7395)` m and Unreal bounds min `(-207.000004,-2282.0,46.099999)` cm/max `(-163.000004,-2222.000006,173.950006)` cm pass the exact `600 x 460 x 1280 mm` envelope.
- Separate interaction contracts are retained for `PR008_HMI_PRIMARY_TOUCH`, `PR008_HMI_LOCAL_CONTROLS` and `PR008_ESTOP`. These are source/import authority only, not proof of live UI or safe runtime control.
- Fresh UE 5.8 build, both cranes, exact handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass. Four fresh Unreal images are under `Saved/ValidationScreenshots/PressShopIntegration/v073_pr005_runtime/`.
- Pro Sheet 01 comparison passes compact-HMI form, operator orientation, touch/control/E-stop readability and equipment-family direction. Live UI/native state, measured operator/service clearance, readable identity, layered condition, remote-control-room routing, safe reset/isolation, fault/save proof and clean cage-free captures hold promotion.
- `Saved/Audits/press_shop_pr008_module10_visual_gate_v073.json` records **MODULE 10 PHYSICAL DIRECTION PASS / LIVE UI, NATIVE AUTHORITY, CLEARANCE, MATERIAL, SAVE AND CLEAN-CAPTURE HOLD / NOT PROMOTED**. Begin native PR-008 process/HMI/fault/save rebind and measure the actual PR-008-to-PR-009 interface.

# PR-008 native runtime candidate v074 (2026-08-04, latest)

- Current native checkpoint is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074`, isolated from v073. Accepted PR-004 v006 remains protected; rejected PR-004 v007-v010 remain rejected.
- Native `ALBPR008Station` now runs strip-wait, loop-control, feeding, pre-punch, cutting and discharge phases with the expanded Pro fault set, alarm acknowledgement, latched E-stop, trusted control-room authority `CW.MW.CONTROL_ROOM`, automated isolation/zero-energy proof/release and save version 2. Moving saves restore safely to Ready and require restart. Feed/discharge roll motion uses the corrected Unreal local-X Roll axis.
- The detailed station uses one authority, 27 semantic bindings, 14 attached movers, three HMI/control/E-stop interaction surfaces and live HMI text. UE 5.8 compilation passes. Focused automation `LineBoss.PressShop.PR008.RuntimeAndSave` is 1/1 green at `Saved/Automation/PR008_Runtime_v002/`.
- `Saved/Audits/press_shop_pr008_native_runtime_v074.json` proves all authored motion, strip/blank production, live phase/HMI state, E-stop acknowledgement, zero-energy evidence and safe return to Ready. v074 also passes primary/support crane runtime, exact PR-004-to-PR-005 handoff, collision/navigation and valid non-partial `1396.953125 cm` navigation.
- `Saved/Audits/press_shop_pr008_pr009_interface_v074.json` measures discharge end X `-19.999985 cm`, `2.499985 cm` from the Pro target, with `0 cm` primary process centreline error. PR-009 is not yet authored in this map, so the receiving gap remains unproved.
- Four fresh 1920x1080 fixed-camera captures are under `Saved/ValidationScreenshots/PressShopIntegration/v074_pr005_runtime/`. `Saved/Audits/press_shop_pr008_visual_review_v074.json` records **TECHNICAL/RUNTIME PASS / VISUAL RELEASE GATE FAIL / NOT PROMOTED** after manual Pro-reference inspection.
- Release blockers are the visible white planning cage, obstructing inherited grey slabs/columns, flat/clean materials, unfinished floor zoning/foundations/wear, harsh lighting, HMI/pedestal overlap, undersized visual hierarchy and obstructed PR-009 interface view. Next build isolated v075 from v074, remove only confirmed PR-008 placeholders, fix HMI clearance/cameras, layer materials/floor/lighting and repeat every inherited gate plus fresh screenshot inspection.

# PR-008 visual cleanup candidate v075 (2026-08-04, latest)

- Current retained visual direction is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075`, isolated from v074. v074/v073, accepted PR-004 v006 and rejected PR-004 v007-v010 are untouched.
- `Saved/Audits/press_shop_pr008_visual_obstructions_v074.json` proves which inherited actors were engineering artefacts. v075 suppresses only the white planning cage, engineering strip datum/labels and duplicate v073 HMI captions. The genuine hall column `LB_PRESS_Column_0_-2250` is preserved and cameras route around it.
- v075 adds a replacement process strip, dimensioned 1120 x 610 cm machine pad, 1120 x 220 cm remote service aisle, 8 cm boundary lines and four fixed cameras. The floor layer is `NoCollision` and navigation-neutral; see `Saved/Audits/press_shop_pr008_visual_cleanup_candidate_v075.json`.
- Native PR-008 motion/HMI/safety/isolation, both cranes, traceable PR-004-to-PR-005 handoff, collision and valid non-partial `1396.953125 cm` runtime navigation all pass on v075.
- `Saved/Audits/press_shop_pr008_pr009_interface_v075.json` retains the measured discharge X `-19.999985 cm`, `2.499985 cm` target error and `0 cm` primary centreline error. PR-009 has no receiver actors, so no final physical handoff is approved.
- Four fresh 1920x1080 captures are under `Saved/ValidationScreenshots/PressShopIntegration/v075_pr005_runtime/`; hashes and manual Pro inspection are in `Saved/Audits/press_shop_pr008_visual_review_v075.json`.
- Decision is **ENGINEERING CLEANUP / FLOOR ZONING / CAMERA DIRECTION PASS; MATERIAL / IDENTITY / ENVIRONMENT / PR-009 HANDOFF HOLD; NOT PROMOTED**. Next duplicate v075 to isolated v076 and add dedicated bright strip steel, layered machine/cabinet material response, legible identity and authored floor/foundation detail. Retain v075 camera sightlines and do not remove the real column; then repeat all gates before connecting PR-009.

# PR-008 layered v076 rejection and smooth-layer v077 checkpoint (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR008LayeredMaterialCandidate_v076` is rejected despite passing technical/runtime gates. Its procedural colour/roughness frequency and contrast visibly produced coarse sand-textured machinery. `Saved/Audits/press_shop_pr008_visual_review_v076.json` is authoritative; never promote or parent a new candidate from v076.
- Retained unpromoted direction is `/Game/LineBoss/Maps/LB_PressShop_PR008SmoothLayerCandidate_v077`, isolated directly from v075. It uses 229 controlled smooth overrides, preserves functional material distinctions and the real hall column/open-mesh guards, and provides mounted Cairnwell Automotive / Moorcross Works / PR-008 identity without Line Boss in-world branding.
- UE 5.8 editor build succeeds. Native PR-008 sequence/HMI/safety/isolation, both cranes, exact PR-004-to-PR-005 traceability, collision/navigation and valid non-partial `1396.953125 cm` navigation pass. PR-008 discharge remains within `2.499985 cm` of target and on the exact centreline; PR-009 has zero receiver actors and therefore no proved physical handoff.
- Fresh 1920x1080 evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v077_pr005_runtime/`; hashes and original-resolution Pro Sheet 01 inspection are in `Saved/Audits/press_shop_pr008_visual_review_v077.json`.
- Visual result is **SMOOTH MATERIAL / IDENTITY / CAMERA DIRECTION PASS; REFLECTION / ENVIRONMENT / MECHANICAL DENSITY / PR-009 HANDOFF HOLD; RETAINED; NOT PROMOTED**. The discharge blank can read nearly black, the hall remains sparse/flat and enclosure/cabinet/mechanism density is below the Pro hero reference.
- Control-room-only machine policy: fixed CCTV management readability is primary; selectable drone inspection is secondary; local HMIs are service/status panels. Do not build pedestrian/player walk-up paths as a release requirement, but retain machine/material collision, certified robot access, crane clearance, safety exclusions, maintenance access and close inspection detail.
- Continue from v077 with local reflection/industrial-lighting/hall-context improvement and Pro-guided mechanical depth. Repeat all gates and fixed cameras before promotion, and stage the real PR-009 receiver before approving the downstream handoff.

# PR-008 reflection-environment candidate v078 rejection (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR008ReflectionEnvironmentCandidate_v078` is an isolated v077-derived lighting test with three physical overhead luminaires, two camera fills and one local reflection capture. UE 5.8 build and every inherited runtime/crane/handoff/collision/navigation/interface gate pass.
- Fresh 1920x1080 captures in `Saved/ValidationScreenshots/PressShopIntegration/v078_pr005_runtime/` fail decisively: exposure clips most surfaces toward white, destroys material/safety-colour hierarchy, reduces HMI/identity legibility and lets fixture/column glare overwhelm the process.
- `Saved/Audits/press_shop_pr008_visual_review_v078.json` records **TECHNICAL PASS / SEVERE OVEREXPOSURE AND READABILITY FAIL / REJECTED / NOT PROMOTED**. Do not use v078 as a parent. Retain v077 and calibrate an order-of-magnitude lower lighting pass with an early single-camera exposure gate.
- Read-only check of `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging` confirms all declared hashes, parseable JSON and 25 inventory rows. It is a planning package only: no `.blend`, `.fbx`, `.uasset` or `.umap` exists, so source blockout remains required before canonical integration.

# PR-008 calibrated-lighting candidate v079 (2026-08-04, latest)

- Retained unpromoted direction is `/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079`, isolated directly from v077. Rejected overexposed v078 remains rejected and was not used as a parent.
- v079 preserves v077 smooth materials and adds calibrated installed-lighting candidates: three overhead fixtures at 550 intensity, 90/75 fills and one restrained local reflection capture. The early process-camera exposure check passed before full validation.
- UE 5.8 build, native PR-008 runtime/HMI/safety/isolation, both cranes, exact PR-004-to-PR-005 traceability, valid non-partial `1396.953125 cm` navigation, combined collision/navigation and interface datum inspection all pass.
- Four fresh 1920x1080 views are in `Saved/ValidationScreenshots/PressShopIntegration/v079_pr005_runtime/`; hashes and original-resolution Pro Sheet 01 review are in `Saved/Audits/press_shop_pr008_visual_review_v079.json`.
- Visual result is **CALIBRATED LIGHTING / WORKED-STEEL READABILITY PASS; HALL CONTEXT / MECHANICAL DENSITY / IDENTITY DISTANCE / PR-009 HOLD; RETAINED; NOT PROMOTED**. The strip/blank now read as metal and colour/HMI hierarchy survives, but the hall remains sparse, some floor/column highlights are hot, machine detail remains below the Pro hero reference and PR-009 is absent.
- Continue from v079 with believable hall architecture/installed lighting and Pro-guided enclosure/service density. Do not promote until the actual PR-009 receiver is staged, measured and live-transfer tested.

# PR-008 installed-hall candidate v080 early rejection (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR008InstalledHallCandidate_v080` added a rear wall, service spine, cable tray, large cell header and foundation anchors from v079. Its mandatory early process-camera check failed, so the full technical suite was intentionally not run.
- The rear wall reads as a cropped floating upper-right slab; service lines are unsupported, identity is clipped and hall/mechanical credibility regresses. Anchor plates are the only useful element to reconsider after checking machine-base correspondence.
- `Saved/Audits/press_shop_pr008_visual_review_v080.json` records **EARLY CAMERA FAIL / COMPOSITION REGRESSION / REJECTED / FULL GATES NOT RUN / NOT PROMOTED**. Keep v079 as the retained parent and place future architecture from measured camera frusta and actual clearances.

# PR-008 measured-anchor v081 rejection and external-tab v082 checkpoint (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR008AnchoredInstallationCandidate_v081` used exact measured v079 base bounds for 24 four-corner anchor assemblies. The mandatory early motion camera showed that the inset plates were almost entirely hidden beneath the machine footprints. `Saved/Audits/press_shop_pr008_visual_review_v081.json` records **MEASURED DIRECTION PLAUSIBLE / VISUAL EVIDENCE INSUFFICIENT / NOT RETAINED / FULL GATES NOT RUN / NOT PROMOTED**. Do not use v081 as a retained parent.
- Retained incremental direction is `/Game/LineBoss/Maps/LB_PressShop_PR008ExternalAnchorTabsCandidate_v082`, branched directly from retained v079. It places measured 120 x 120 mm external plates with 35 mm studs immediately outside six verified major base footprints, producing visible base-connected tabs without moving machinery or changing the established process composition.
- Fresh UE 5.8 compilation, native PR-008 process/HMI/safety/isolation, primary and support cranes, exact PR-004-to-PR-005 handoff, collision, valid non-partial runtime navigation and PR-008-to-PR-009 datum inspection all pass. The tab layer is deliberately `NoCollision` and navigation-neutral while its eventual authored physical-collision treatment remains open.
- Four fresh 1920x1080 Unreal captures are under `Saved/ValidationScreenshots/PressShopIntegration/v082_pr005_runtime/`. Original-resolution inspection confirms a modest installation-grounding improvement while preserving v079 lighting, worked-steel readability, material hierarchy and HMI/process presentation.
- `Saved/Audits/press_shop_pr008_visual_review_v082.json` records **MEASURED EXTERNAL ANCHOR-TAB GROUNDING PASS / HALL CONTEXT, MECHANICAL DENSITY, DISTANT IDENTITY AND PR-009 HOLD / RETAINED / NOT PROMOTED**. Generic plates/studs should become authored base geometry before release; the Pro hall/service-density gap remains substantial.
- Read-only staging inspection now confirms real PR-009 source deliverables in `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging`: one Blender source, 15 candidate FBXs, validation/interface/export manifests and 12 source renders. Source validation passes without promotion, but the proposed receiver begins at world X `220 cm`, leaving a measured `2399.99985 mm` unsupported gap from PR-008 discharge. No canonical Unreal import/runtime/collision/navigation/live-transfer proof exists yet.
- Next: intake and hash the completed PR-009 source package into the canonical repository, resolve the unsupported PR-008-to-PR-009 transfer span by authority-backed geometry/layout rather than silently moving fixed datums, then import into an isolated v083 candidate and repeat every compile/import/runtime/collision/navigation/interface and fixed-camera gate.

# PR-009 intake in progress and supported transfer source v001 (2026-08-04, latest)

- The external PR-009 task is still writing `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging`. An initial canonical copy correctly failed the independent hash gate when the Blender file/renders changed during intake; a refreshed snapshot subsequently matched, but it remains explicitly unpromoted and must be refreshed once more after the external task declares final completion.
- Current snapshot and independent receipt: `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v001/` and `Saved/Audits/press_shop_pr009_source_intake_v001.json`. The root `09_HANDOFF_MANIFEST.json` is stale because it predates the binary build; newer `PR009_Audits` receipts and the independent canonical manifest supersede only its old binary-count statement.
- A separate dimensioned interface source now exists at `SourceAssets/PR009/AutomatedBlankStacker/Interface_v001/`. It spans the measured `2400 mm` gap without moving either fixed station datum, uses a `900 mm` roller axis/`990 mm` roller top, and contains 17 individually pivoted rollers, six supported legs, bearings, guarded drive, guides, sensors, service routing, isolation hardware and approved open-mesh sides.
- Blender 5.2 source validation and 25 deterministic FBX exports pass. Three fresh 1600x900 source renders were inspected. `Saved/Audits/press_shop_pr008_pr009_supported_transfer_source_v001.json` records **SOURCE DIMENSION / PIVOT / OPEN-MESH / INSTALLATION DIRECTION PASS; UNREAL INTERFACE / RUNTIME / COLLISION / VISUAL HOLD; NOT PROMOTED**.
- `Scripts/import_build_press_shop_pr009_physical_integration_v083.py` is prepared and syntax-checked, but it has intentionally not been run while the external package remains mutable. It will duplicate retained v082 into isolated `/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083`, import the final source snapshot and supported bridge, then enforce measured bounds before any downstream gates.
- Native PR-009 authority now compiles in `LBPR009Station.h/.cpp`. It owns remote receiving, vision/centring, gantry stacking, separator placement, carrier release, traceability, machine interlocks/faults, controlled stop, isolation/zero-energy proof and safe save restore. Press Shop save format is now version 8 with `FLBPR009SaveState`.

# PR-009 v002 canonical intake and v083 visual hold (2026-08-04, latest)

- The parallel task owns PR-009 source only and must stop before PR-010. The canonical task reads/copies stable deliverables but never modifies `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging`.
- Point-in-time v002 snapshot `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/` matched 83 selected staging hashes when v083 was built, including one v002 production Blender source, 19 candidate FBXs and 16 source renders. `Saved/Audits/press_shop_pr009_source_intake_v002.json` records that snapshot receipt only. The external task subsequently resumed writes and added FBX reimport validation, so this is not the final canonical intake; refresh and rerun `Scripts/intake_pr009_candidate_v002.py` only after the parallel task declares PR-009 complete.
- `/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083` is an isolated v082-derived integration baseline. It places 16 full-detail PR-009 groups at fixed datum `(600,-2000,0)` cm/yaw `-90`, imports LOD1/LOD2 without overlapping placement, imports UCX candidates as unbound evidence, installs the 25-part supported PR-008/PR-009 transfer and contains one native `ALBPR009Station` with control-room authority `CW.MW.CONTROL_ROOM`.
- `Saved/Audits/press_shop_pr009_physical_integration_v083.json` proves the EST station envelope and measured interface span. It does not prove the six SK group motion decompositions, collision binding, navigation, live material flow or release readiness.
- Fresh fixed-camera images are under `Saved/ValidationScreenshots/PressShopIntegration/v083_pr005_runtime/`. Against Pro Sheet 02, the footprint, guarded process and material direction read correctly, but the cell is visibly below target for enclosure/mechanical depth, service density, layered material realism, CCTV composition and identity legibility. The interface capture also suffered a post-image Unreal process fault.
- `Saved/Audits/press_shop_pr009_visual_review_v083.json` is authoritative: **VISUAL GATE FAIL / TECHNICAL INTEGRATION BASELINE RETAINED / NOT PROMOTED**. Full promotion gates were intentionally not run. Next create an isolated PR-009 visual-depth/material candidate from v083, pass an early fixed-camera comparison, then bind/decompose native motion, attach collision evidence and run runtime/save/interface/collision/navigation/import gates plus stable fresh screenshots. PR-010 remains on hold.
- Motion-import pilot evidence: pivot-preserving/uncombined import with absolute transforms disabled returns 42 gantry parts at 1/100 expected scale and fails assembly reconstruction (`Saved/Audits/press_shop_pr009_gantry_decomposition_pilot_v001.json`). Uncombined import with absolute node transforms enabled returns all 42 parts and exactly matches the source assembly bounds (`Saved/Audits/press_shop_pr009_gantry_absolute_import_pilot_v002.json`), but the assets are named generic `Cube_###`. The parallel task has received a PR-009-only correction request for semantic mesh-data names, explicit cm/axis settings and deterministic per-object transform/pivot/parent manifests for all six SK groups. Do not bind motion by import order or generic names.
- Native PR-009 now has 26 explicit modular motion components plus the root: 18 individual infeed/output roller pivots and eight mechanism movers for gantry bridge/cross-slide/Z, lift table, side/end joggers and separator picker. The presentation state is driven by the authoritative receiving/centring/stacking/separator/releasing phases and retains safe restore/isolation behavior. UE 5.8 build succeeds; `Saved/Automation/PR009_Runtime_v002/` passes 1/1 with no warnings/errors. `Saved/Audits/press_shop_pr009_native_runtime_presentation_v002.json` records **NATIVE PROCESS / SAFETY / SAVE / PRESENTATION-CONTRACT PASS; FINAL SEMANTIC FBX BINDING AND VISUAL GATES REQUIRED; NOT PROMOTED**.
- Focused automation `LineBoss.PressShop.PR009.RuntimeAndSave` passes 1/1 with zero warnings/errors under `Saved/Automation/PR009_Runtime_v001/`. Receipt: `Saved/Audits/press_shop_pr009_native_runtime_source_v001.json` — **NATIVE PROCESS / REMOTE AUTHORITY / FAULT / ISOLATION / TRACEABILITY / SAFE SAVE PASS; MAP BINDING AND VISUAL GATES REQUIRED; NOT PROMOTED**.

# PR-009 corrected final-source intake, transactional handoff, v084 rejection and v085 retained material direction (2026-08-04, latest)

- The completed external PR-009 v002 source task stopped before PR-010. Canonical final intake is now immutable under `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/`: 84 selected files, 19 FBXs, 16 PNGs and all 61 declared final-handoff hashes pass. Obsolete point-in-time files were preserved under `_Superseded_PointInTime_2026-08-04`, not deleted. Receipt: `Saved/Audits/press_shop_pr009_source_intake_v002.json` — **CANONICAL V002 SOURCE HASH/MANIFEST PASS / UNREAL GATES REQUIRED / NOT PROMOTED**.
- Corrected pivot-preserving six-group Unreal import now reconstructs all 158 semantic modular actors at centimetre scale with identity component scale, no generic names, correct group counts and dimensions within 1.5%. Receipt: `Saved/Audits/press_shop_pr009_modular_import_pilot_v003.json`. The verified Unreal basis is fixed station yaw `-90` plus child relative yaw `180` (effective world yaw `+90`).
- Native PR-008-to-PR-009 material flow is transactional and traceable. PR-008 save version 3 owns semantic `PR008-BLANK-%06d` identities, a three-blank buffer and request/confirm/cancel state; PR-009 accepts the exact upstream identity and no longer invents phantom blanks. UE 5.8 compile passes. Focused automations `Saved/Automation/PR008_Runtime_v003/`, `PR009_Runtime_v003/` and `PR008_PR009_BlankHandoff_v002/` each pass 1/1 with zero warnings/errors, including blocked rollback and save/load ownership proof.
- `/Game/LineBoss/Maps/LB_PressShop_PR009CorrectedIntegrationCandidate_v084` contains one native PR-009 authority, one native transactional flow controller, ten corrected static groups, all 158 modular presentation actors bound by semantic role to the native movement hierarchy, and the 25-part supported transfer. Build receipt: `Saved/Audits/press_shop_pr009_corrected_integration_v084.json`.
- Four fresh v084 fixed-camera images under `Saved/ValidationScreenshots/PressShopIntegration/v084_pr009_corrected/` were inspected against authoritative Pro Sheet 02 and the corrected v002 Blender source render. `Saved/Audits/press_shop_pr009_visual_review_v084.json` records **CORRECTED MODULAR GEOMETRY DIRECTION PASS / MATERIAL, LIGHTING, IDENTITY AND PRESENTATION FAIL / NOT PROMOTED**. v084 remains a technical baseline only.
- Read-only Unreal slot inspection `Saved/Audits/press_shop_pr009_material_slots_v084.json` proved 23 authored slot names across 193 actors. v084 had incorrectly collapsed 97 assignments into generic charcoal, including the blank role, which explains the black merged stack.
- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v085` applies 237 explicit authored-role overrides: 12 blank slots use oiled sheet steel, 36 machined slots use worked steel, screen/amber roles are emissive, and frame/green/yellow/service-grey/galvanised/rubber/glass/red/white/blue remain distinct. Build receipt: `Saved/Audits/press_shop_pr009_layered_presentation_candidate_v085.json`.
- Four fresh 1920x1080 v085 fixed-camera captures under `Saved/ValidationScreenshots/PressShopIntegration/v085_pr009_layered/` prove a material improvement: the stack reads as metal, machined/structural parts separate and amber light curtains are visible. `Saved/Audits/press_shop_pr009_visual_review_v085.json` nevertheless records **MATERIAL-ROLE / BLANK-STEEL / LIGHT-CURTAIN DIRECTION PASS; EXPOSURE, IDENTITY, MECHANICAL MASS AND RELEASE PRESENTATION HOLD; RETAINED; NOT PROMOTED**.
- Measured v085 bounds prove the visible near guard face is at world Y approximately `-1741.75 cm`; the first identity plate was incorrectly placed on the far face around `-2264 cm`. Receipt: `Saved/Audits/press_shop_pr009_presentation_bounds_v085.json`. Next isolated v086 moves identity to the measured near face, darkens calibrated material values, reduces local light/reflection contribution and improves cameras. It must repeat technical and fresh visual gates before any promotion.
- A separate Codex task has been assigned validator-focused in-map PR-009 runtime, presentation-motion, save, authority, collision and navigation evidence. It is prohibited from touching PR-010, altering visual design, promoting assets or editing these handoff documents. PR-010 remains on hold.

# PR-009 calibrated v086 technical pass, visual and release-collision hold (2026-08-04, latest)

- Retained unpromoted baseline: `/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v086`. It preserves v085's corrected modular assembly and explicit material roles while using darker calibrated colours, lower local light/reflection contribution, improved cameras and a Cairnwell Automotive / Moorcross Works plate on the measured near guard face. No Line Boss branding is present in-world.
- Fresh Unreal evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v086_pr009_layered/`. `Saved/Audits/press_shop_pr009_visual_review_v086.json` records **CALIBRATED MATERIAL / NEAR-GUARD IDENTITY / BLANK-STEEL / LIGHT-CURTAIN DIRECTION PASS; TYPOGRAPHY / MECHANICAL DENSITY / ENVIRONMENT / RELEASE COLLISION HOLD; RETAINED; NOT PROMOTED** after comparison with Pro Sheet 02 and the corrected v002 source render.
- Full technical evidence is consolidated at `Saved/Audits/PR009_InMap_v086/PR009_IN_MAP_TECHNICAL_VERIFICATION.json`. All eight technical gates pass: exact authority/controller cardinality, traceable transactional blank ownership/rollback, all native motion in PIE, safe stopped save/load, trusted remote authority/isolation/zero-energy proof, collision coverage evidence, protected navigation and protected-file/PR-010 integrity. Both focused automations pass 1/1; two valid non-partial perimeter paths are `1040 cm` and do not enter protected process space.
- This is not a release pass. Ten combined PR-009 static groups use temporary complex-as-simple collision and zero simple collision elements; G6 therefore records `release_collision_ready=false`. The 158 modular actors are intentionally presentation-only `NoCollision`, while interface pieces keep authored simple collision where required.
- Next create isolated v087 from v086 for authored simple/convex/UCX collision on substantial structures, guard/service/interaction envelopes and required movers only. Prove every gantry axis, lift, jogger, separator, roller, carrier and blank path without self-blocking, then rerun compile, automations, PIE, static collision, navigation, save/authority/integrity and fresh fixed-camera Pro comparison. Do not modify or promote v086; do not start PR-010 or resume robot polish yet.
- Visual-successor plan: `Saved/Audits/press_shop_pr009_visual_successor_plan_v086.json`. Measured evidence shows the authored HMI and electrical cabinet already exist on the south service face around Y `-2240.5` and `-2208 cm`, but all four v086 cameras are north/near-side. After collision acceptance, first test a south-west service/hero camera against the v002 source hero, then enlarge CCTV-legible Cairnwell/Moorcross identity and improve installed grounding. Do not invent extra machinery until the existing 158 semantic actors and ten source groups are shown inadequate from the correct service-side view.

# PR-009 v087 authored-collision checkpoint and measured successor decision (2026-08-04, latest)

- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087` replaces complex-as-simple on all ten combined PR-009 station groups with authored simple box collision. Its inventory is 98 simple boxes: 58 on the ten combined groups, 14 on substantial fixed chassis actors and 26 query-only sensing envelopes on selected movers. There are zero convex primitives and zero complex-as-simple assets in release scope; 118 minor modular visuals remain deliberately `NoCollision`.
- Fixed chassis/substantial envelopes use blocking query-and-physics collision and navigation relevance where appropriate. Selected movers use query-only overlap sensing and do not become physical or navigation blockers. All 20 authored guard primitives, BaseFrame/fixed chassis traces and the physical/query-only distinction are directly proved.
- UE 5.8 compile, both focused PR-009 automations, transactional rollback/no-phantom ownership, native PIE motion, safe stopped restore, trusted authority, isolation/zero-energy proof, two non-partial `1040 cm` perimeter routes, protected-space exclusion and validation-window integrity pass. All 207 normalized v086/v087 visual actor payloads match exactly, and four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v087_pr009_release_collision/`.
- v087 is **not release-ready and not promoted**. A physical full-size `1800 x 2600 mm` blank sweep hits the current trace portal around world `(426,-1870,105.5)` cm because its `2600 mm` opening has zero side clearance. The complete source-authoritative `2800 mm` gantry contract also overlaps the trace beam and both posts; these three contacts are not approved. Authoritative report: `Saved/Audits/PR009_InMap_v087/PR009_RELEASE_COLLISION_VERIFICATION_REPORT.md`; consolidated status is `FAIL_RELEASE_COLLISION_BLOCKED_BY_MAX_BLANK_TRACE_PORTAL_AND_FULL_GANTRY_PORTAL_OVERLAPS__NOT_PROMOTED`.
- The next isolated successor must preserve the full `2800 mm` gantry travel. Move the complete portal visual and collision toward the output from source-Y centre `1.865 m` to `3.15 m` (verified Unreal world-X delta `-128.5 cm`), and widen its clear opening from `2.6 m` to `2.8 m`. This provides `0.165 m` clearance to the governing mover, `0.445 m` to the guarded-cell end and `0.1 m` per side around the maximum blank.
- Author the change as a separate dimensioned derived Blender/FBX/manifest package; preserve immutable Candidate_v002 and do not leave non-identity actor scale in the release asset. Plan: `Saved/Audits/PR009_InMap_v087/trace_portal_clearance_successor_plan.json`. Rerun import/bounds, full-contract sweeps, collision, compile, automations, PIE, save, authority, navigation, integrity and fresh fixed-camera Pro review. PR-010 and both robots remain on hold.

# PR-009 Pro-axis correction, v088 rejection and v089 technical acceptance (2026-08-04, latest)

- **This section supersedes the v087 portal-clearance conclusion immediately above.** Re-reading authoritative Pro Sheet 02 and `PRESS_SHOP_REMAINING_MACHINERY_ENGINEERING_SPEC_v1.0.md` proved local `+X` is across strip/lane and local `+Y` is material flow. The `2600 x 1800 mm` maximum blank is therefore tested as `2600 mm` along flow by `1800 mm` across, which maps through station yaw `-90` to world half extents `(130,90,0.8) cm`.
- M02's `0..2800 mm` entry is total travel within the `3100 mm` module envelope, not an additional `+2800 mm` from the authored midpoint at local Y `-0.3 m`. Correct endpoint offsets are `-1.4..+1.4 m`. With these authoritative interpretations, unchanged v087 clears the original trace portal and its analytical 26-mover full-contract audit has zero unapproved overlaps.
- The dimensionally valid derived portal package at `SourceAssets/PR009/AutomatedBlankStacker/TracePortalClearance_v001/` and map `/Game/LineBoss/Maps/LB_PressShop_PR009TracePortalClearanceCandidate_v088` were built only while testing the earlier interpretation. v088 is now **rejected / not promoted / never a parent** because the design change is unnecessary. Candidate_v002 and v087 remained unchanged. Authority receipt: `Saved/Audits/PR009_InMap_v089/axis_authority_correction.json`.
- Corrected physical tracing exposed the real issue: `SM_CA_MW_PR008_PR009_TransferGuides_01` had one generated collision envelope spanning both physical guide rails and filling the intended open channel. Isolated `/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089`, parented directly from v087, preserves identical guide vertices, triangles, bounds and materials while replacing that envelope with two authored side boxes. Clear channel is `2181.4 mm`, providing `190.7 mm` clearance per side for the Pro `1800 mm` across-strip blank.
- v089 passes: UE 5.8 native build; both focused automations 1/1 with zero warnings/failures; static collision with 98 station primitives plus the two guide boxes and zero complex-as-simple; runtime motion/save/authority/isolation; physical guard/chassis/interface traces; full blank sweep; all 26 full-contract mover sweeps with zero unapproved overlaps; and two non-partial `1040 cm` navigation routes with no protected-space points.
- Four fresh v089 images are under `Saved/ValidationScreenshots/PressShopIntegration/v089_pr009_transfer_guide_collision/`. `Saved/Audits/press_shop_pr009_visual_review_v089.json` records **RELEASE COLLISION / RUNTIME / SAVE / AUTHORITY / NAVIGATION PASS; TYPOGRAPHY / SERVICE-SIDE CAMERA / ENVIRONMENT / PRESENTATION HOLD; RETAINED; NOT PROMOTED**. The next isolated successor must keep v089 geometry/collision, first add the measured south-west service/hero camera to show the existing HMI and electrical cabinet, then improve CCTV-legible Cairnwell/Moorcross identity and installed presentation before any PR-009 promotion. PR-010 and robot polish remain on hold.

# PR-009 south service camera and measured fascia identity v090-v092 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraCandidate_v090` is an isolated v089 derivative with a fixed south-west service camera at `(0,-2820,400)` cm targeting `(550,-2020,130)` cm. Fresh evidence proves the existing local HMI, electrical/service cabinet, guarded transfer, gantry and blank stack from the remote-operations service side. v089 geometry, collision and authority remain unchanged.
- v091 attempted to reuse the north guard identity plate's reverse face. Measured probing and the fresh capture proved that plate remains about `5.2 m` behind the south service controls and is partly obscured. `/Game/LineBoss/Maps/LB_PressShop_PR009ServiceIdentityCandidate_v091` is **rejected / not promoted / not a parent**.
- `/Game/LineBoss/Maps/LB_PressShop_PR009ServiceFasciaIdentityCandidate_v092`, parented directly from v090, places Cairnwell Automotive / Moorcross Works / PR-009 Automated Blank Stacker text `0.85 cm` outside the measured south face of the existing authored PR-009 interaction fascia at world Y `-2258.75 cm`. It adds no plate and changes no process geometry, collision or navigation. Line Boss remains absent in-world.
- Fresh v091/v092 comparison evidence and hashes are recorded in `Saved/Audits/press_shop_pr009_service_identity_visual_gate_v092.json`. v092 is **SERVICE-FASCIA IDENTITY DIRECTION PASS / INSTALLED PRESENTATION AND FULL RELEASE GATES HOLD / RETAINED / NOT PROMOTED**. Guard mesh/rail interference, installed cable/ground/anchor detail, hall/floor condition, a complete four-camera suite and all repeated technical gates remain open. PR-010 and robot polish remain on hold.

# Enclosed automated-machine direction (2026-08-04, latest)

- The user selected connected enclosed automated machine cells as the normal production presentation: material enters a controlled opening, the named operation occurs inside and the correct intermediate or finished part exits toward the next station. Detailed authority is `Docs/MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md`.
- This is a reusable casing/state system, not permission to replace simulation with opaque boxes. Existing validated rollers, gantries, lifts, dies, transfers, sensors, buffers and traceability remain animated inside; inspection glazing, internal CCTV/drone views and isolated maintenance-open states expose them deliberately.
- PR-009 is the first enclosure pilot because v089 already proves its machinery, collision, transactional flow, authority, save and navigation. Preserve v089 and retained v092 service identity. Keep PR-009 infeed/outfeed and the south HMI/electrical cabinet accessible, use approved open mesh only at real transfer/access hazards, and do not start PR-010 until the reusable PR-009 shell passes fresh Unreal visual and runtime gates.
- User authority for the four press trains is management-game simulation depth: make each train look and sound operational without reproducing every internal working part or physically deforming sheet. One truthful saved gameplay cycle drives blank arrival, guarded feed, visible ram/die stroke, synchronized layered spatial audio, formed-panel mesh/state replacement, downstream transfer, HMI, throughput, energy, wear and faults. Detailed rule: `Docs/MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md`.

# PR-009 enclosed-cell v095 accepted baseline (2026-08-04, latest)

- The PR-009 enclosure pilot has passed its required candidate and accepted-map gates. The stable accepted map is `/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095`; its gated source candidate remains `/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095`. Preserve protected technical parent v089. v094 remains an unpromoted first pilot; rejected v091 and v093 must not become parents.
- Seven reusable identity-scale enclosure modules provide the structural shell, layered panels/roof, inspection glazing, interlocked service door and hardware, utilities and roof equipment. Normal production remains closed and interlocked; validated conveyors, gantry, lift, stack and carrier mechanisms remain visible through deliberate glazing/process views. Infeed/outfeed portals, south-side HMI/electrical access and approved open-mesh transfer guarding remain available.
- Native `ALBPR009Station` owns the service-door hinge. The door restores from saved `bGuardsClosed`, interpolates between 0 and 105 degrees at 90 degrees/s and is bound by semantic role rather than actor order. The shell has ten authored simple structure boxes and one authored simple door box; the old guard collision is disabled. The full Pro `2600 x 1800 mm` blank and all 26 configured mover contracts clear with zero unapproved overlaps.
- Final candidate verification is `Saved/Audits/PR009_InMap_v095/PR009_ENCLOSURE_RELEASE_VERIFICATION.json`: native build passed; both focused automations passed 1/1 with zero warnings/errors; static identity/collision/authority, runtime motion/transaction/save/isolation, physical shell/door/portal, two non-partial `1040 cm` navigation routes and full-contract sweep gates passed. Matching integrity snapshots prove 7 protected maps, 126 PR-009/enclosure source files, 1772 robot files and the held PR-010 scope did not change during the final gate run.
- Seven fresh images are under `Saved/ValidationScreenshots/PressShopIntegration/v095_pr009_enclosure/`. They were manually inspected against Pro Sheet 02, the PR-009 v002 source render and enclosure v002 hero. The enclosed silhouette, controlled portals, external service equipment, Cairnwell Automotive / Moorcross Works / PR-009 identity and deliberate internal visibility pass at management-camera distance. Line Boss does not appear in-world.
- Promotion used two clean Unreal sessions to avoid an editor world-lifetime conflict. Receipt: `Saved/Audits/PR009_Accepted_v095/promotion_receipt.json`, status `PASS__PR009_V095_ACCEPTED_BASELINE_CREATED`, with 2231 actors, seven enclosure modules, one PR-009 authority, one flow controller and zero candidate-not-promoted tags. Direct static, runtime/save/authority, physical and navigation validators also passed on the accepted map under `Saved/Audits/PR009_Accepted_v095/`.
- This is acceptance of the PR-009 enclosed-cell baseline, not a claim that the full Press Shop is release-complete. Shared hall exposure, roof/service-grey response, floor ageing and installed environmental dressing remain later factory-wide polish. The reusable enclosure direction may now proceed to PR-010, preserving PR-009 v095 and applying station-specific dimensions/interfaces rather than cloning its exact shell. Both support robots remain deferred; preserve MR-01 v021 as an unpromoted structural/runtime/collision/save checkpoint with its visual gate open.

# PR-009 v095 acceptance revoked by cross-station axis audit (2026-08-04, latest; supersedes the acceptance above)

- **Do not treat `/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095` as accepted or promoted.** The file is retained for forensic/correction use, but its accepted tags were removed and `LB.Asset.CandidateNotPromoted` plus `LB.Asset.AcceptanceRevoked.AxisIntegration` were applied. Receipt: `Saved/Audits/PR009_Accepted_v095/acceptance_revocation_receipt.json`, status `PASS__PR009_V095_ACCEPTANCE_REVOKED__MAP_RETAINED_NOT_PROMOTED`.
- PR-010 authority intake exposed a cross-station physical-flow contradiction not covered by the earlier station-local gates. Fixed datums progress PR-008 `X=-500` -> PR-009 `X=600` -> PR-010 `X=1350` cm. Station local `+Y` is material flow and PR-009 yaw is `-90 degrees`, so flow maps to increasing world X. Numeric authority therefore places PR-009 infeed near world X `275 cm`, output near `895 cm`, and PR-010 infeed shuttle near `1020 cm`.
- The v095 modular presentation is reversed: 43 infeed actors average world X `920.674 cm`, while 26 output actors average `274.327 cm`; the PR-008/PR-009 transfer occupies X `-12..212 cm`. Audit: `Saved/Audits/PR010_Intake/pr009_pr010_flow_axis_integration_v001.json`, status `FAIL__PR009_MODULAR_PRESENTATION_FLOW_AXIS_REVERSED__V095_ACCEPTANCE_REVOKED`.
- Earlier build/runtime/collision/navigation/save/authority and enclosure visual gates remain useful station-local evidence, but they cannot authorize promotion while physical input/output integration contradicts the fixed datums. Create an isolated successor from v095 that corrects modular source-origin placement to the station's `-90 degree` basis without negative release scale, preserves south service access and the accepted enclosure appearance, and reconnects PR-008 infeed plus future PR-010 output. Repeat every technical and fresh fixed-camera gate before promotion.
- No new Pro design is required. Existing Pro Sheets 02/03 plus numeric datum/axis schedules already resolve the intended relationship. PR-010 source authority intake passed at `Saved/Audits/PR010_Intake/pr010_authority_intake_v001.json`; do not place its Unreal blockout until the corrected PR-009 physical output is proved. Press-train datums remain TBC and must not be invented.

# PR-009 v096 corrected-axis accepted baseline (2026-08-04, latest; supersedes v095)

- The corrected stable PR-009 baseline is now `/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v096`. It supersedes the revoked v095 map. v095 remains retained and explicitly unpromoted for forensic comparison; rejected v091/v093 and the revoked map must not become production parents.
- Isolated candidate `/Game/LineBoss/Maps/LB_PressShop_PR009FlowAxisCorrectionCandidate_v096` reflects only the 158 modular mechanism source origins across fixed PR-009 world X `600 cm`, preserving south service Y, Z, actor rotations, positive identity scale, enclosure, and the fixed PR-008/PR-009 transfer. Corrected infeed averages world X `279.326 cm`; output averages `925.673 cm`; the fixed PR-010 infeed target is `1020 cm`.
- The separator picker retained its visible 500 mm extension and 350 mm vertical placement motion, but its decorative 12-degree yaw swing was removed because temporal PIE bounds proved that swing clipped `PR009_Base_GantryColumn_-1.95_1.15`. The corrected linear motion was sampled across 1,205 runtime frames and has zero unapproved mover/blocker overlaps. This is an implementation-path correction, not a Pro redesign.
- Consolidated verification is `Saved/Audits/PR009_InMap_v096/PR009_FLOW_AXIS_RELEASE_VERIFICATION.json`, status `PASS__PR009_V096_CORRECTED_ENCLOSED_CELL_BASELINE_PROMOTION_AUTHORIZED__PRESS_SHOP_NOT_COMPLETE`. UE 5.8 native build passed; both focused automations passed 1/1 with zero warnings/errors; static identity/collision/authority, runtime/save/isolation, physical shell/door/portals, navigation, and temporal full-contract collision gates passed.
- Six fresh fixed-camera captures are under `Saved/ValidationScreenshots/PressShopIntegration/v096_pr009_enclosure/`. Manual comparison with Pro Sheet 02, the PR-009 v002 source render, and enclosure v002 hero passed the corrected input/output direction, enclosed-cell silhouette, Cairnwell Automotive / Moorcross Works identity, external HMI/E-stops, controlled portals, approved open-mesh transfer guarding and deliberate internal visibility at the seated control-room/CCTV target distance.
- Promotion receipt: `Saved/Audits/PR009_Accepted_v096/promotion_receipt.json`, status `PASS__PR009_V096_ACCEPTED_BASELINE_CREATED`: 2231 actors, 219 accepted PR-009 actors, seven enclosure modules, one PR-009 authority, one material-flow controller and zero candidate tags. Direct static, runtime/save/authority, physical and navigation gates also pass on the accepted map under `Saved/Audits/PR009_Accepted_v096/`.
- Scope remains limited: PR-009 is accepted, but the Press Shop and game are not complete. The shared hall/floor are still too bright and clean in close views; factory-wide materials, ageing, installed services and environmental dressing remain a later common pass. PR-010 Unreal blockout may now begin from `Docs/PR010_IMPLEMENTATION_AUTHORITY.md`; press-train datums remain TBC and must not be invented. No additional Pro machinery design is required unless a genuinely missing or conflicting numeric dimension is found.

# PR-010 v097 dimensioned four-lane blockout (2026-08-04, latest)

- PR-010 authority is resolved in `Docs/PR010_IMPLEMENTATION_AUTHORITY.md`: fixed datum `(1350,-2000,0) cm`, yaw `-90 degrees`, local `+Y` flow to increasing world X, and fixed lane centres local X `-4500,-1500,+1500,+4500 mm`. The infeed shuttle at local Y `-3300 mm` lands exactly at world X `1020 cm`, downstream of accepted PR-009 v096. Press Train A-D world datums remain TBC and were not invented.
- Dimensioned source is `SourceAssets/PR010/FourLaneBuffer/Blockout_v001/`: one Blender 5.2 source, 23 deterministic semantic FBXs, 142 placed source objects, four lanes, eight carrier/stack positions, lane pylons, stops, gates, coordination HMI, service corridor, controlled crossing, quality-hold spur, handoff apron and a four-bay enclosed shuttle/utility spine. Source audit: `Saved/Audits/PR010_Blockout/pr010_dimensioned_source_v001.json`, **PASS / UNREAL GATES REQUIRED / NOT PROMOTED**.
- Isolated Unreal map `/Game/LineBoss/Maps/LB_PressShop_PR010BlockoutCandidate_v097` is parented only from `/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v096`. It contains 142 PR-010 blockout mesh actors plus three Cairnwell/Moorcross/PR-010 identity actors and four fixed cameras. All 149 are candidate-tagged, identity scale, non-negative scale, collision-free and navigation-neutral for this first visual gate. Existing accepted PR-009 authority cardinality remains one.
- Static evidence `Saved/Audits/PR010_Blockout/pr010_static_gate_v097.json` proves the rotated `840 x 1400 x 8 cm` deck, world lane centres Y `-1550,-1850,-2150,-2450 cm`, eight carrier positions and the shuttle at world X `1020 cm`. Authority v002 and accepted-parent context are under `Saved/Audits/PR010_Intake/pr010_authority_intake_v002.json` and `pr010_master_plan_context_v002.json`.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v097_pr010_blockout/`. The first opaque-wall enclosure attempt failed visual inspection and was corrected before retention into four upper fascia/glazing bays using accepted layered PR-009 material language. Manual Pro Sheet 03 review is `Saved/Audits/PR010_Blockout/pr010_visual_review_v097.json`, status `PASS__PR010_V097_DIMENSION_LAYOUT_AND_ENCLOSURE_DIRECTION__RETAINED_BLOCKOUT__NOT_PROMOTED`.
- v097 is not a release asset. Next create an isolated detailed successor from v097: strengthen CCTV-readable PR-010 identity, even the shared hall exposure, author approved open-mesh lane/end protection, scanners, tow points, service routing and detailed HMI, then add native reservation/buffer/vehicle-handoff authority, save state, selective collision, protected navigation and fresh fixed-camera gates. Do not promote v097 and do not place press trains until authoritative datums exist. No additional Pro design is required for this work.

# PR-010 v098 native runtime and retained detailed direction (2026-08-04, latest)

- Native `ALBPR010Station` is implemented and compiled. It owns Isolated/Ready/reservation/lane-select/transfer/stored/train-reserved/vehicle-handoff/stopping/fault states; four two-stack lanes; deterministic lowest-free-lane allocation; FIFO dispatch; exact stack identity; train reservations; quality hold; controlled-crossing, guard, shuttle, vehicle-handoff, safety and E-stop interlocks; control-room-only commands under `CW.MW.CONTROL_ROOM`; isolation/zero-energy proof; and safe stopped save restoration. Press Shop save format is now 9 and includes `FLBPR010SaveState`.
- UE 5.8 native build passed. `LineBoss.PressShop.PR010.RuntimeAndSave`, PR-008 runtime/save, PR-009 runtime/save and the PR-008-to-PR-009 traceable handoff each pass 1/1 with zero failures or warnings under `Saved/Automation/PR010_Runtime_v001/` and `Saved/Automation/PR010_Regression_v001/`.
- Isolated map `/Game/LineBoss/Maps/LB_PressShop_PR010DetailedRuntimeCandidate_v098` is parented only from retained v097 and does not modify it. One native authority is installed at `(1350,-2000,0) cm`, yaw `-90 degrees`, and all 74 authored moving parts are bound semantically: 52 rollers, 16 stops, four reservation gates, the infeed shuttle and quality-hold spur.
- v098 adds directionally correct open post-and-rail protection, four safety scanners, four tow points, side service trays, a remote HMI pedestal/screen, mounted Cairnwell Automotive / Moorcross Works / PR-010 identity and controlled local task lighting. The four inspection bays use the licensed Factory Environment translucent glass instance rather than the opaque sensor-glass placeholder. No Line Boss wording appears in-world.
- Final static evidence is `Saved/Audits/PR010_DetailedRuntime/pr010_static_gate_v098.json`: 192 PR-010 scope actors, one native authority, four lane beds, eight carrier positions, 16 open-guard posts, eight rails, four scanners, four tow points and four fixed cameras; no press-train datum was invented.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v098_pr010_detailed_runtime/`. Early evidence passes were rejected for opaque glazing, darkness, then overexposure and an edge-on HMI backplate; the retained images are from the corrected exact build. Review: `Saved/Audits/PR010_DetailedRuntime/pr010_visual_review_v098.json`, status `PASS__PR010_V098_RETAINED_DETAILED_RUNTIME_DIRECTION__NOT_RELEASE_ART__NOT_PROMOTED`.
- Consolidated technical evidence is `Saved/Audits/PR010_DetailedRuntime/PR010_V098_RELEASE_VERIFICATION.json`, status `PASS__PR010_V098_NATIVE_RUNTIME_STATIC_AUTOMATION_AND_FRESH_EVIDENCE__COLLISION_NAV_RELEASE_GATES_REMAIN__NOT_PROMOTED`. v098 is retained but not promoted: the inherited 142-object engineering blockout remains NoCollision/navigation-neutral, final collision contracts and temporal mover sweeps are open, robot-route navigation is unproved, modular art/HMI housing require final polish and Press Train A-D datums remain TBC.
- Next create an isolated v099 collision/navigation successor from v098. Author selective fixed-shell/service/safety collision without making rollers or stacks physical blockers, prove the full eight-stack and vehicle-handoff motion envelope, establish autonomous robot routes around—not through—the protected buffer, repeat runtime/save/authority regressions, and inspect fresh fixed cameras before any promotion. No new Pro design is required unless a genuinely missing or conflicting numeric dimension appears.

## Active v099 collision/navigation work

- `/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099` now exists as an isolated v098 child. Component-level collision was configured without modifying shared mesh assets: 57 fixed/detail blockers, 91 query-only moving/material actors and 31 navigation-neutral actors. Receipt: `Saved/Audits/PR010_CollisionNavigation/pr010_collision_configuration_v099.json`, status `PASS__PR010_V099_SELECTIVE_FIXED_AND_QUERY_COLLISION_CONFIGURED__RUNTIME_SWEEPS_AND_NAV_REQUIRED__NOT_PROMOTED`. Runtime temporal sweeps, protected navigation, regression and fresh visual gates remain open; do not promote v099 yet.

## PR-010 v099 corrected runtime/collision/navigation baseline (2026-08-04, latest; supersedes the active checkpoint above)

- v099 remains `/Game/LineBoss/Maps/LB_PressShop_PR010CollisionNavigationCandidate_v099`, isolated from v098 and **not promoted**. Native presentation binding was corrected so all 52 rollers and four reservation gates rotate about their own authored pivots instead of orbiting the station datum. The UE 5.8 build and focused `PR010`, `PR009`, `PR008` and traceable PR008-to-PR009 automations all pass 1/1 with zero failures/warnings under `Saved/Automation/PR010_V099_Final/`.
- Runtime collision evidence exposed that the 13,000 mm Item-05 shuttle envelope had been incorrectly treated as the M01 moving body. Existing Sheet 03 authority was sufficient to resolve it: the 13 m rail/enclosure bed is fixed, while a `2400 x 800 x 180 mm` transfer cradle moves inside the authoritative 1000 mm-deep envelope across the four lane targets. The provisional open guard posts/rails were moved outside that swept cradle with 150 mm lateral clearance; no new Pro design was required. Receipt: `Saved/Audits/PR010_CollisionNavigation/infeed_shuttle_correction_v099.json`.
- Final component contract is 58 fixed/detail blockers, 91 query-only moving/material actors and 31 navigation-neutral actors. `Saved/Audits/PR010_CollisionNavigation/runtime_collision_pie_audit_v099.json` sampled 2,217 PIE frames across eight normal stacks, quality hold, lane-A dispatch, all five motion contracts, trusted/untrusted authority and moving-state safe restoration. Roller/gate translation is effectively zero, shuttle travel is 449.97 cm, roller rotation reaches 180 degrees, gate rotation reaches 89.98 degrees and there are zero new mover/fixed overlap pairs.
- v099 adds a local `1400 x 2300 x 700 cm` navigation volume and exact `840 x 1400 x 500 cm` `NavArea_Null` protected buffer. Three non-partial runtime paths pass outside it: 900 cm south service, 900 cm north service and 1840 cm east vehicle-handoff route. Evidence: `Saved/Audits/PR010_CollisionNavigation/navigation_pie_audit_v099.json`.
- Four fresh exact-map images are under `Saved/ValidationScreenshots/PressShopIntegration/v099_pr010_collision_navigation/` and were inspected against authoritative Pro Sheet 03. The corrected moving cradle/fixed envelope, four lanes, open end guarding, material-flow story and Cairnwell/Moorcross/PR-010 identity pass directionally. Release art does not pass: stack/carrier/guard forms remain coarse, rails are visually heavy/repetitive, the remote HMI requires final housing/UI and the shared hall/floor/service presentation needs polish.
- Consolidated status: `Saved/Audits/PR010_CollisionNavigation/PR010_V099_RELEASE_VERIFICATION.json` = `PASS__PR010_V099_EXACT_MAP_COMPILE_STATIC_RUNTIME_SAVE_AUTHORITY_COLLISION_NAVIGATION__VISUAL_RELEASE_HOLD__NOT_PROMOTED`. Visual decision: `pr010_visual_review_v099.json` = `PASS__PR010_V099_CORRECTED_SHUTTLE_AND_GUARD_DIRECTION_RETAINED__PRO_SHEET_03_RELEASE_ART_HOLD__NOT_PROMOTED`.
- Next create an isolated v100 release-art successor from v099. Preserve all technical geometry, component roles, collision, navigation, native authority and motion pivots; replace only coarse presentation with dimensioned modular carriage/guard/HMI/service assets and improved layered materials/lighting, then repeat every gate and fixed-camera Pro inspection. Press Train A-D datums remain TBC and must not be invented.


# PR-010 v100 isolated release-art checkpoint (2026-08-05, latest)

- Isolated map `/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v100` is parented only from retained v099; v099 was not overwritten. Five dimensioned Blender 5.2/FBX modules are under `SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v100/`: 2700 x 80 x 1200 mm open-grid guard panel, 2400 x 800 x 180 mm transfer cradle, 760 x 500 x 1650 mm remote HMI, 220 x 220 x 240 mm scanner and 240 x 180 x 340 mm tow point. Source dimensions/material slots/branding pass at `Saved/Audits/PR010_ReleaseArt_v100/pr010_release_art_source_audit_v100.json`.
- v100 preserves one native station and every v099 runtime, mover-pivot, collision, navigation and save contract. The moving cradle mesh was replaced on the already-bound actor; 24 v099 guard blockers remain as invisible collision proxies with eight separate NoCollision open-grid visuals. Four scanners and four tow points were upgraded in place. The HMI moved to Pro Sheet 03 local `(6450,-3250,0) mm`, world `(1025,-2645,0) cm`, and uses only Cairnwell Automotive / Moorcross Works / PR-010 diegetic identity.
- Exact-map source/import/static/runtime/save/authority/collision/navigation gates pass. Runtime sampled 2,216 frames, proved all five motions, nine stored stacks including quality hold, one dispatch, trusted/untrusted authority, safe moving-state restoration and zero new temporal overlaps. All three non-partial protected-space routes still pass. Consolidated evidence: `Saved/Audits/PR010_ReleaseArt_v100/PR010_V100_RELEASE_VERIFICATION.json`.
- Four fresh 1920x1080 views are under `Saved/ValidationScreenshots/PressShopIntegration/v100_pr010_release_art/`. Honest Sheet 03 review retains the new open guards, cradle, scanner/tow hardware and HMI authority point, but **v100 is not promoted**: stack/carrier blocks remain too coarse, highlights clip, retained fascia/columns obscure the flow, and the ServiceHMI camera is obstructed so screen/identity are not legible. Visual decision: `Saved/Audits/PR010_ReleaseArt_v100/pr010_visual_review_v100.json`.
- Existing Pro Sheets already resolve the exterior and numeric authority; no Pro redesign is required. Next create isolated v101 from v100, preserving technical contracts while replacing coarse carrier/stack presentation, simplifying obstructive fascia, correcting exposure and providing an unobstructed, legible Unreal-driven HMI evidence view. Press Train A-D datums remain TBC and must not be invented.


# PR-010 v101 carrier/stack/HMI checkpoint (2026-08-05, latest)

- Isolated map `/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v101` is parented only from retained v100; v099/v100 were not overwritten. New dimensioned source under `SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v101/` contains an exact `2400 x 1900 x 180 mm` roller carrier pallet, `2200 x 1700 x 500 mm` layered/strapped blank stack with ID plate, and exact-envelope `2900 x 80 x 750 mm` open louver fascia. Source gate passes.
- v101 installs eight detailed carriers, nine layered stacks including quality hold, four open fascia visuals over retained invisible collision envelopes, lower PR-010 task-light intensities, and a corrected HMI camera/text hierarchy. The authoritative HMI now reads Cairnwell Automotive, Moorcross Works, PR-010 Four-Lane Buffer, Remote Ready and 8/8 Stack Positions in the fresh exact-map image.
- Exact-map static, 2,216-frame runtime/save/authority/temporal-collision, protected navigation, UE 5.8 native build and four focused automation regressions all pass. Automations are 1/1 with zero warnings/errors under `Saved/Automation/PR010_V101_Final/`. Consolidated evidence: `Saved/Audits/PR010_ReleaseArt_v101/PR010_V101_RELEASE_VERIFICATION.json`.
- Four fresh images are under `Saved/ValidationScreenshots/PressShopIntegration/v101_pr010_release_art/`. v101 materially improves the CCTV read: engineered carriers, visible steel-sheet layers, stack plates, open fascia, open guards and legible HMI. It is nevertheless **retained and not promoted** after direct comparison with `SHEET_03_PR010_ENGINEERING_REFERENCE_4K.png`: the hero's dense upper service deck/roof drives/routing/access rails are still absent, lane pylons and stack IDs need final detail, hall/floor/material response needs settling, and HMI presentation text is not yet bound to changing native status.
- No new Pro design is required. Sheet 03 plus the existing numeric schedules already define the remaining exterior direction. Next create isolated v102 from v101 for service-deck/rails/routing, detailed ID pylons and unique stack identity, live HMI binding, and final material/exposure polish; then repeat every gate and fresh fixed-camera review. Press Train A-D datums remain TBC and must not be invented.

# PR-010 v102 service-deck/live-HMI checkpoint (2026-08-05, latest)

- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR010ReleaseArtCandidate_v102` is parented only from retained v101; no earlier PR-010 map was overwritten. Dimensioned Blender/FBX source under `SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v102/` adds four repeated upper service housings, access walkway/rail sections, roof drive pods and utility routes plus four exact `350 x 350 x 2200 mm` detailed lane pylons. Source dimensions pass within `0.5 mm`.
- v102 installs 16 service-deck visuals over 20 separate hidden blockers, preserves all retained collision contracts, replaces the four legacy pylon visuals while retaining their hidden blockers, adds eight pylon identity texts and nine unique stack-position IDs, and binds the existing State and Capacity HMI text actors to the native `ALBPR010Station`. No Line Boss wording appears in-world and no Press Train datum was invented.
- Exact-map static authority/branding passes with one native station, eight carriers, nine stacks, eight open guards and 52 accounted hidden collision proxies. UE 5.8 native build passes. PR-010, PR-009, PR-008 and traceable PR-008-to-PR-009 automations each pass 1/1. Runtime stores nine stacks including quality hold, dispatches one, proves trusted/untrusted authority and safe-save restoration, exercises all five presentation motions across more than 2,200 frames, and reports zero new temporal overlaps. All three non-partial protected navigation routes pass.
- Map-bound HMI PIE proof is explicit: the exact v102 map changes the visible fields to `REMOTE RESERVATION WAIT` and `3 / 8 STACK POSITIONS`. Evidence is under `Saved/Audits/PR010_ReleaseArt_v102/`, with consolidated status in `PR010_V102_RELEASE_VERIFICATION.json`.
- Four fresh 1920x1080 fixed-camera images are under `Saved/ValidationScreenshots/PressShopIntegration/v102_pr010_release_art/`. Direct Sheet 03 review passes the enclosed automated silhouette, upper service deck, repeated drives/routes, detailed lane identity, material-flow presentation and unobstructed HMI direction.
- v102 is **retained and not promoted**. The close infeed view remains simpler/cleaner than the Pro hero, bright roof and stack highlights flatten the material hierarchy, installed conduit/hose/hatch/fastener density is still low, stack IDs are not reliably CCTV-legible, and the shared hall/floor remains unfinished. Visual authority: `Saved/Audits/PR010_ReleaseArt_v102/pr010_visual_review_v102.json`.
- No Pro redesign is required. Create isolated v103 from v102, preserve all technical contracts, add source-authored service conduits/hoses/access hatches/fasteners, calibrate roughness and highlights, enlarge stack-ID presentation within the existing plates, then repeat exact-map compile/import/runtime/collision/navigation/save/authority/live-HMI and fresh fixed-camera gates. Press Train A-D datums remain TBC and must not be invented.

# PR-010 v103 accepted baseline (2026-08-05, latest)

- Accepted immutable baseline: `/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103`, promoted only after direct original-resolution comparison with Pro `SHEET_03_PR010_ENGINEERING_REFERENCE_4K.png`. Earlier v097-v102 maps remain retained/rejected checkpoints and were not overwritten.
- v103 adds three dimensioned source modules under `SourceAssets/PR010/FourLaneBuffer/ReleaseArt_v103/`: exact installed-service bank, service-access hatch section and stack-identity plate. Four service banks, four hatch sections, nine readable electronic stack identities and calibrated local lighting close the isolated v102 station holds. Dedicated CCTV evidence reads `A1 MW-010-A01` normally, not mirrored.
- Candidate consolidated gate: `Saved/Audits/PR010_ReleaseArt_v103/PR010_V103_RELEASE_VERIFICATION.json`. Exact source/import/static authority, UE 5.8 build, four automation regressions, runtime/save/authority/temporal collision, three nonpartial navigation routes, live HMI and five fresh fixed-camera images all pass. Manual release review is `pr010_visual_review_v103.json` and authorizes station promotion.
- Promotion evidence: `Saved/Audits/PR010_Accepted_v103/promotion_receipt.json`. All 307 PR-010 actors carry `LB.Asset.Accepted.PR010.v103`; 667 inherited candidate tags were removed and zero remain. One accepted PR-009 native authority remains present.
- Post-promotion exact-map gates independently pass on the accepted map: `accepted_static_audit.json`, `runtime_collision_pie_audit.json`, `navigation_pie_audit.json` and `live_hmi_pie_audit.json`. A fresh accepted overview is in `Saved/ValidationScreenshots/PressShopIntegration/v103_pr010_accepted/`; consolidated accepted evidence is `PR010_ACCEPTED_V103_VERIFICATION.json`.
- Accepted technical contract remains fixed at datum `(1350,-2000,0) cm`, yaw `-90 degrees`, four lanes, eight normal stack positions plus quality hold, 52 collision proxies, safe stopped save restoration, zero new temporal overlaps and three protected robot routes. No Line Boss working-title branding appears in-world.
- PR-010 station promotion does not claim the Press Shop is complete. The common hall/floor, white structural columns, distant services and overall environmental ageing remain a shared-area release pass. MR-01 v021 remains unpromoted with its visual gate open; robot polish stays deferred until the Press Shop is complete.
- Existing Pro machinery references remain sufficient for enclosed CCTV-first press-train exteriors. Inspect and resolve the four press-train authority from the existing remaining-machinery pack next; do not invent Press Train A-D world datums. Request a targeted Pro dimension sheet only if the existing pack contains a genuine numeric conflict or omission.

# Press Train A-D authority intake (2026-08-05, active)

- The existing Pro remaining-machinery pack is hash-complete: all 28 listed files match their recorded size and SHA-256; the 29th on-disk file is the manifest itself. Evidence: `Saved/Audits/PressTrains/press_train_authority_intake_v001.json`.
- `Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md` now fixes the CCTV-first enclosed-machine gameplay model, seven reusable stages, local centres/envelopes, motion/safe-pose contracts, Cairnwell/Moorcross branding, Train A-D variant differences and isolated construction/promotion order.
- No new Pro exterior design is required. The pack is sufficient to build the shared kit and an isolated Train A. Production placement remains prohibited because the pack explicitly marks global Train A-D Unreal datums and rotations `TBC_NOT_INVENTED`; build locally first and request only targeted placement authority if no authoritative master-plan transform is found.

# Press Train shared kit and Train A v002 retained blockout (2026-08-05, latest)

- The dimensioned shared source kit is under `SourceAssets/PressTrains/Shared/Blockout_v001/`. It contains one Blender source and 16 semantic FBX modules: common platform, utility spine, transfer rail, seven stage shells, press slide, moving bolster, stage die set, die cart, transfer crossbar and destack lift. `Saved/Audits/PressTrains/press_train_shared_source_audit_v001.json` passes source dimensions, pivots, material identities and hashes. It is a local reusable source kit, not promoted release art.
- Train A v001 exposed an FBX-axis integration error and remains failed/unpromoted. Its common source assets mapped to Unreal `-Y` while stages were positioned along Unreal `+Y`, producing a `99,000 mm` aggregate length.
- Corrected isolated map `/Game/LineBoss/Maps/LB_PressTrainAFlowAxisCandidate_v002` rotates the 37 presentation actors by 180 degrees and pulls five die carts inside the width envelope without negative scale. Static evidence `Saved/Audits/PressTrains/press_train_a_flow_axis_static_v002.json` passes seven stages, 22 movers, five tooling actors, three fixed cameras and `15,000.005 x 56,000.001 x 11,350 mm` aggregate bounds within numerical tolerance. Global production placement remains `TBC_NOT_INVENTED`.
- Three fresh exact-map images are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v002/`. Direct original-resolution comparison with Pro Sheets 04/05 **fails the visual gate**: lighting clips service-grey/green surfaces, repeated shells read as cabinets rather than heavy presses, lower dies/slides/bolsters and transfer equipment are inadequately visible, yellow platforms/rails and service density are insufficient, and the close camera/text orientation is poor. Review: `Saved/Audits/PressTrains/press_train_a_visual_review_v002.json`.
- Retain v002 only as the verified dimensional and flow-axis parent; do not promote it and do not spend runtime/collision/navigation/save gates on the failed presentation. Create isolated v003 preserving all verified transforms/bounds, then correct exposure, guarded process openings, visible press mechanics, platforms/rails/services, distinct load/unload cells, identity facing and camera composition. Inspect an early fixed-camera image before completing downstream gates. No additional Pro exterior design is required.

# Press Train A v012 retained visual direction (2026-08-05, latest)

- v003 proved the original lighting was clipped but an overcorrection became too dark. v004 then proved that the 180-degree FBX flow-axis correction also swaps source left/right, placing the first open facade on the hidden service side. Both maps are preserved failed visual checkpoints and must not be promoted.
- Corrected shared presentation source `SourceAssets/PressTrains/Shared/Presentation_v003/` places the open guarded process facade on source `+X`, which becomes the negative-X fixed-camera side after the verified assembly rotation. All 16 Blender/FBX modules pass dimensions, pivots, hashes and materials in `Saved/Audits/PressTrains/press_train_shared_source_audit_v003.json`.
- Reusable visible press mechanics are independently authored under `SourceAssets/PressTrains/Shared/MechanicalBay_v001/`: lower platen, bolster guides, crosshead, ram block/face, four tie rods/collars, twin ram cylinders, camera-facing drive/gearbox and supported hydraulic/lube routes. Source measures `5860.001 x 4200 x 5255 mm` inside its `6500 x 5000 x 6500 mm` envelope and passes `Saved/Audits/PressTrains/press_train_mechanical_bay_source_audit_v001.json`.
- Current retained isolated map is `/Game/LineBoss/Maps/LB_PressTrainAManagementCameraCandidate_v012`. It contains the verified seven-stage source presentation plus five separate NoCollision mechanical-bay actors, fixed exposure, validation-only installed floor/wall/ceiling and a management camera below the ceiling. Static gate `Saved/Audits/PressTrains/press_train_a_management_static_v012.json` passes 42 presentation actors, seven stages, 22 movers, five tooling sets, five mechanical bays, three fixed cameras, Cairnwell/Moorcross identity and unchanged `15,000.005 x 56,000.001 x 11,350 mm` bounds. World placement remains `TBC_NOT_INVENTED`.
- Three fresh exact-map captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v012/`. Direct Pro Sheets 04/05 review `Saved/Audits/PressTrains/press_train_a_visual_review_v012.json` retains the open-bay, yellow-platform, visible-drive and complete management-view direction but keeps a **release-art hold**: internal mechanical hierarchy remains dark/flat, stages need trim/pierce/scrap/lubrication differentiation, S01/S07 endpoint equipment is too simple, die-change/service interfaces are weak, HMI/E-stop/ID/state-light/service density is incomplete and layered wear/restored-mothballed variation is absent.
- v012 is not promoted. Do not run costly runtime/collision/navigation/save gates until the next source-detail successor passes another fixed-camera review. Next add distinct S01 and S07 equipment, stage-specific service packs, readable die-change interfaces, ID/HMI/E-stop modules and calibrated internal material/task-light response while preserving v012 exposure, transforms and bounds. No Pro redesign is required.

# Press Train reusable stage-detail source v001 (2026-08-05, active successor)

- Existing Pro Sheets 04/05 remain sufficient; no redesign request is required. The implementation model is now explicitly CCTV-first enclosed machinery: exterior presentation, limited visible motion, sheet flow, lighting and sound sell operation while hidden mechanisms are not exhaustively modelled.
- Reusable dimensioned Blender/FBX source is under `SourceAssets/PressTrains/Shared/StageDetail_v001/`. It contains four NoCollision presentation modules: camera-side HMI/E-stop/isolation/ID/beacon/utility service pack, S01 blank-stack/destack head, S07 roller outfeed/inspection arch/stillage and a mid-train scrap/lubrication service pack.
- Source audit `Saved/Audits/PressTrains/press_train_stage_detail_source_audit_v001.json` passes four assets, measured dimensions within the 6500 x 5000 x 6500 mm local stage envelope, material slots, hashes, source Blend and `TBC_NOT_INVENTED` world authority. Nothing is promoted.
- Next import the kit into an isolated v013 child of v012, preserve all verified transforms/exposure/bounds, place seven service packs plus distinct endpoint/process cues, capture all fixed cameras and compare directly with Pro Sheets 04/05 before completing downstream gates.

# Press Train A v015 retained detail/material direction; v016 rejected (2026-08-05, latest)

- v013 imported 11 source-detail actors but failed its first static audit because seven inherited scoped validation actors lacked the explicit `TBC_NOT_INVENTED` authority tag. Its controls were also authored on the wrong local face. It remains rejected/unpromoted.
- Corrected reusable source `SourceAssets/PressTrains/Shared/StageDetail_v002/` turns the HMI, stage-ID, E-stop and S07 vision screen onto source `+X`, the verified CCTV side after 180-degree Unreal assembly rotation. Four assets pass dimensions, hashes, material slots and authority in `Saved/Audits/PressTrains/press_train_stage_detail_source_audit_v002.json`.
- Current retained direction is isolated `/Game/LineBoss/Maps/LB_PressTrainAInstalledReadabilityCandidate_v015`. It has 53 presentation meshes: seven shells, 22 movers, five tooling actors, five mechanical bays and 11 stage-detail actors. All 72 scoped actors have candidate and TBC authority tags; bounds remain `15000.005 x 56000.001 x 11350 mm`. Exact static evidence is `press_train_a_installed_readability_static_v015.json`.
- Three fresh exact-map images are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v015/`. Review `press_train_a_visual_review_v015.json` retains the CCTV-facing HMI/E-stop/status direction, distinct S01/S07 mass and restrained material palette but holds release art: bays remain dark, enclosure repetition/cleanliness is high, installed fasteners/seams/routes/hatches/wear are sparse, S04/S05 and die-change stories are weak, endpoints remain partly occluded and the hall is validation-only.
- Lighting-only v016 was stopped after its fresh close draw-stage image showed only marginal improvement. `press_train_a_visual_review_v016.json` is an explicit early reject; do not promote v016 and do not spend the other two captures or runtime gates on it.
- Preserve v015 as the current unpromoted direction. Next author reusable installed-service/die-change/stage-variant exterior detail and local light fixtures at source level, then create a new isolated successor and repeat fixed cameras. Do not request a new Pro redesign; Sheets 04/05 remain sufficient. Global Train A-D production datums remain `TBC_NOT_INVENTED`.

# Press Train installed-service source v001 (2026-08-05, active)

- Reusable dimensioned source now exists under `SourceAssets/PressTrains/Shared/InstalledService_v001/`: camera-side access-hatch/fastener/utility/manifold bank, opposite-side die-change dock/clamps, S04 trim-scrap extraction, S05 pierce-slug collection and an installed local task-light fixture.
- All five Blender/FBX assets pass source dimensions, hashes, materials, floor-centre pivots, NoCollision presentation roles, explicit `+X` operator/CCTV versus `-X` die-change side authority and `TBC_NOT_INVENTED` world placement in `Saved/Audits/PressTrains/press_train_installed_service_source_audit_v001.json`.
- Nothing is imported or promoted yet. Next create an isolated successor from retained v015, not rejected v016; add seven service banks/fixtures, five die docks and the two stage-specific service assemblies, pair fixtures with restrained local Unreal lights, then inspect an early close camera before full capture/static gates.

# Press Train A v022 retained installed-service/die-change direction (2026-08-05, latest)

- Current retained isolated map is `/Game/LineBoss/Maps/LB_PressTrainADieChangeEvidenceCandidate_v022`, descended from retained v015 through unpromoted checkpoints. It contains 74 presentation meshes: the v015 53 plus seven installed service banks, seven local task fixtures, five opposite-side die-change docks and distinct S04 trim-scrap/S05 pierce-slug assemblies. Four fixed cameras now cover operator hero, management overview, draw-stage detail and die-change/service side.
- Exact static/authority gate `Saved/Audits/PressTrains/press_train_a_die_change_evidence_static_v022.json` passes 111 scoped actors, four cameras, seven local fixture lights, five service rect lights, five dock-level point fills, all source assets, Cairnwell/Moorcross identity, no Line Boss wording, complete TBC authority tags and unchanged `15000.005 x 56000.001 x 11350 mm` presentation bounds.
- Four fresh exact-map 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v022/`. Direct Pro Sheets 04/05 review is `press_train_a_visual_review_v022.json`. It retains the installed access/utility/fixture language, visible S04/S05 variation and service-side camera proof of five dock zones, but keeps a release-art hold.
- v017 clipped fixture output; v018 still had a hotspot; v019 retained the operator-side service direction; v020 placed the first service camera inside the train envelope; v021 cleared it but remained too close/dark. Those maps remain unpromoted visual history. v022 is also **not promoted**.
- Remaining visual holds: final heavy-machinery seams/fasteners/wear/hoses/decals, less-identical service-bank state/label variation, higher-quality die carts/docks/changeover staging and final shared hall/floor context. Native HMI/state binding, motion/audio, material flow, faults/save, collision, navigation and crane-clearance gates are intentionally deferred until visual release quality passes.
- No new Pro design is required. Continue source-authored release detail from v022 without inventing global Train A-D datums or rotations.

# Press Train A v025 retained release-detail/material direction (2026-08-05, latest)

- Existing Pro Sheets 04/05 remain sufficient; no new Pro exterior design is required. Global Train A-D production datums and rotations remain `TBC_NOT_INVENTED`.
- Reusable Blender/FBX source `SourceAssets/PressTrains/Shared/ReleaseDetail_v001/` contains eight assets: a transform-compatible six-wheel die cart, separate large-panel tooling load, enhanced die-change dock, frame seam/fastener pack, supported hose/cable dress and distinct running/standby/maintenance service-state modules. `Saved/Audits/PressTrains/press_train_release_detail_source_audit_v001.json` passes eight dimensions, hashes, material slots, pivot/transform compatibility and TBC authority. Nothing is promoted.
- Isolated v023 `/Game/LineBoss/Maps/LB_PressTrainAReleaseDetailCandidate_v023` imported the release kit, swapped five carts and five docks in place and added 22 reusable presentation meshes. Import and exact static gates pass 96 presentation meshes, 145 scoped actors before temporary label cleanup, unchanged `15000.005 x 56000.001 x 11350 mm` bounds, Cairnwell/Moorcross identity, no Line Boss wording and no production-map or PR-010 change. Its four fresh images proved the geometry but failed release presentation for darkness, over-dominant state marks and temporary floating labels.
- v024 introduced procedural layered materials and removed all 12 temporary release-detail text actors, but its first large/high-contrast noise calibration visibly read as marble/smoke. v024 is rejected and must not be promoted.
- Current retained unpromoted direction is `/Game/LineBoss/Maps/LB_PressTrainAMaterialCalibrationCandidate_v025`. Exact static evidence `Saved/Audits/PressTrains/press_train_a_material_calibration_static_v025.json` passes 96 presentation meshes, 133 scoped actors, four fixed cameras, all eight release assets, branding/envelope/TBC authority and zero failures.
- Four fresh exact-map 1920x1080 captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v025/`. Original-resolution comparison against Pro Sheets 04/05 is `Saved/Audits/PressTrains/press_train_a_visual_review_v025.json`, status **release-detail and subtle layered-material direction retained / release-art hold / not promoted**.
- v025 corrects the v024 material artifact and retains improved carts, tooling loads, docks, supported utilities, fabricated detail and distinct service-state geometry. Release still holds because the hero/overview remain too dark, broad crown/enclosure panels are too plain, service evidence does not clearly prove wheel/dock mechanisms, seams/utilities are weak at management distance, endpoint machinery/hall context/decals/condition variants remain incomplete and runtime gates have not started.
- Next author a second reusable exterior-detail source pass for crown drives/ribs, access platforms and ladders, service doors/vents/fabricated depth, improve S01/S07 endpoint machinery, and move the die-change camera to a three-quarter view that proves bogies, tow points, clamps, connectors and cable chain. Repeat exact static and four-camera Pro gates before native HMI/motion/audio/flow/fault/save/collision/navigation/crane-clearance work.


# Press Train A v032 retained cart-mechanical parent; release-art hold (2026-08-05, latest)

- Existing Pro Sheets 04/05 remain sufficient; no new Pro exterior redesign is required. Global Train A-D production datums and rotations remain `TBC_NOT_INVENTED`.
- Reusable `ExteriorDetail_v002` source adds crown-drive dress, service-door/vent packs, access platform/ladder, S01 feeder detail and S07 inspection/stillage detail. Its source audit passes five dimensioned assets, hashes, materials and local bounds. Isolated v027 corrected the S07 aggregate length back to the verified 56 m envelope; v028 added five fixed evidence cameras and restrained overhead validation lights.
- v029 physically lifted each S02-S06 six-wheel die cart and its paired tooling load from `Z=90 cm` to `Z=120 cm`. This places the estimated wheel envelope at `47-107 cm` and deck bottom at `94 cm`, making mobility readable above the service deck while preserving pair transforms. v030-v032 correct Cairnwell identity-plate alignment, contrast, size and face clearance. These maps remain unpromoted checkpoints.
- Current retained parent is `/Game/LineBoss/Maps/LB_PressTrainACartPlateClearanceCandidate_v032`. Exact static evidence `Saved/Audits/PressTrains/press_train_a_cart_plate_clearance_static_v032.json` passes 110 presentation meshes, 157 scoped actors, five fixed cameras, five release carts/tool loads/docks, 14 exterior-detail actors, five cart identity plates, all required assets, Cairnwell/Moorcross-only branding, complete TBC authority and unchanged `15000.005 x 56000.001 x 11350 mm` bounds.
- Five fresh 1920x1080 exact-map images are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v032/`. Direct original-resolution review against Pro Sheets 04/05 is `Saved/Audits/PressTrains/press_train_a_visual_review_v032.json`. It retains the cart mechanical correction but keeps a **release-art hold**: the train remains too dark, skeletal and repetitive; blank crowns, floating stage labels, weak S01/S07 endpoints, sparse enclosed guarding/services and validation-only hall context still read as blockout rather than release machinery.
- Do not promote v028-v032 and do not begin costly runtime gates yet. Preserve v032 as the next isolated parent, author a reusable dimensioned enclosed exterior-shell source pass from the existing Pro references, replace floating stage names with integrated plates/HMI, improve CCTV lighting and repeat exact static plus all five fresh fixed-camera visual gates before HMI/motion/sheet-flow/audio/fault/save/collision/navigation/crane-clearance work.


# Press Train A v035 retained enclosed CCTV-first direction (2026-08-05, latest)

- No new Pro design is required. Existing Pro Sheets 04/05 remain the exterior authority; global Train A-D datums and rotations remain `TBC_NOT_INVENTED`.
- Reusable dimensioned source `SourceAssets/PressTrains/Shared/EnclosedFacade_v001/` contains four facade families: shared S03-S06 mid press, tall S02 draw press, S01 destack/load and wide S07 unload/inspect. Source audit `Saved/Audits/PressTrains/press_train_enclosed_facade_source_audit_v001.json` passes all four FBX/Blend assets, dimensions, hashes, materials, local floor-centred pivots and TBC authority.
- v033 imported seven physical facade actors, removed all seven validation-era floating stage labels and replaced them with flush text on authored physical plates. v034 added five broad operator-side validation fills and highlight-safe fixed-camera exposure. v035 adds facade-only layered dark foundry grey/deep Cairnwell green materials while preserving inherited mechanics, carts and service interfaces.
- Current retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainAFacadeMaterialCandidate_v035`. Exact static gate `Saved/Audits/PressTrains/press_train_a_facade_material_static_v035.json` passes 117 presentation meshes, 169 scoped actors, seven enclosed facades, seven integrated stage identities, five fixed cameras, complete carts/tooling/docks, all required assets, Cairnwell/Moorcross-only branding, unchanged `15000.005 x 56000.001 x 11350 mm` bounds and TBC authority.
- Five fresh 1920x1080 exact-map images are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v035/`. Direct original-resolution comparison against Pro Sheets 04/05 is `Saved/Audits/PressTrains/press_train_a_visual_review_v035.json`; it retains the enclosed CCTV-first architecture and cart direction but keeps a **release-art hold**.
- Remaining visual holds are inherited pale frame/crown response, over-repeated S03-S06 exterior cues, weak fixed-camera identity/HMI legibility, blockout-level S01/S07 process interiors, dark/unfinished die-change service side, final cart dock/tow/cable evidence and validation-only shared hall context. Runtime/HMI/motion/sheet-flow/audio/fault/save/collision/navigation/crane-clearance gates remain intentionally deferred.
- Preserve v035 as the next isolated parent. Calibrate inherited stage frame/crown materials, add process-specific trim/pierce/lubrication/scrap/restrike exterior cues, finish physical IDs/HMI and service-side evidence, then repeat all five fresh fixed-camera gates before runtime work or promotion.

# Press Train A v038 retained stage-specific exterior direction (2026-08-05, latest)

- No new Pro redesign is required. Existing Pro Sheets 04/05 remain sufficient; global Train A-D production datums and rotations remain `TBC_NOT_INVENTED`.
- v036 reassigned the exact inherited seven stage-shell and five crown material slots and passed its 169-actor static gate, but the fresh hero showed no decisive management-camera improvement. It remains unpromoted. v037 first integrated four exterior cue modules but exposed their blank backplates and is rejected/unpromoted.
- Reusable dimensioned source `SourceAssets/PressTrains/Shared/StageExteriorCues_v001/` contains four distinct modules: S03 paired form-pressure accumulators/servo manifold, S04 guarded trim-scrap chute, S05 four-drawer slug collection and S06 load-cell/quality confirmation. Source audit `Saved/Audits/PressTrains/press_train_stage_exterior_cues_source_audit_v001.json` passes dimensions, hashes, material separation and TBC authority.
- Current retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038`. Exact static gate `Saved/Audits/PressTrains/press_train_a_stage_cue_facing_static_v038.json` passes 121 presentation meshes, 173 scoped actors, four unique stage cues, seven enclosed facades, five cameras, unchanged `15000.005 x 56000.001 x 11350 mm` bounds, required assets and zero failures.
- Five fresh exact-map 1920x1080 captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v038/`. Review `Saved/Audits/PressTrains/press_train_a_visual_review_v038.json` retains the stage-specific enclosed process direction but keeps a release-art hold. Do not promote v036-v038.
- Remaining holds: pale/clean shared crowns and frame mass, fixed-camera physical identity/HMI legibility, S01/S07 material-flow interiors and limited motion, die-change-side mechanical/dock evidence, final common hall context and all runtime/HMI/motion/audio/flow/fault/save/collision/navigation/crane-clearance gates.

# Train A identity experiments v039-v045 rejected; v038 remains retained (2026-08-05, latest)

- v039 stopped on an exact semantic-tag resolver error and remains a preserved failed partial map. v040 correctly darkened the seven inherited facade label slots and shortened the text, but the fixed overview/draw cameras proved the inherited embedded plate coordinate face does not align reliably with its TextRender actor.
- v041-v043 used seven explicit physical plate plus TextRender assemblies. Their static gates passed after exact count corrections, but fixed-camera evidence showed faint/mirrored or incomplete glyph presentation even after correcting face rotation and reducing content to large S01-S07 codes. They are rejected/unpromoted.
- Reusable source `SourceAssets/PressTrains/Shared/RaisedIdentityPlates_v001/` contains seven dimensioned fabricated plates with raised Bahnschrift mesh lettering; source audit `Saved/Audits/PressTrains/press_train_raised_identity_plates_source_audit_v001.json` passes seven 73 x 1200 x 400 mm assets, hashes, separated plate/fastener/letter materials and TBC authority.
- v044 imported those seven assets and passed its corrected 128-presentation/173-scope static gate. v045 reversed all plate actors to test FBX handedness. Both fresh draw cameras show the plates and fasteners correctly but do not show readable raised letter faces, so v044-v045 are rejected and must not be promoted.
- `/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038` remains the retained unpromoted parent. Next identity source must use explicit box-built segmented glyph geometry rather than TextRender or converted font faces, then pass early draw/overview inspection before completing five captures.

# Press Train A v047 retained segmented-identity parent; release-art hold (2026-08-05, latest)

- No new Pro exterior redesign is required. Sheets 04/05 remain sufficient and global Train A-D datums/rotations remain `TBC_NOT_INVENTED`.
- Reusable `SegmentedIdentityPlates_v002` source supplies seven 98 x 1180 x 390 mm physical S01-S07 plate assemblies built from explicit raised cuboid segments, with no TextRender/font/decal/texture dependency. `Saved/Audits/PressTrains/press_train_segmented_identity_plates_source_audit_v002.json` passes all seven assets, dimensions, hashes, material separation and authority.
- v046 established camera-readable identities but left S07 occluded by its wider facade. v047 changes only the S07 identity X position to `-485 cm`, clearing the operator/CCTV face while preserving 173 scoped actors, five fixed cameras and the verified aggregate bounds.
- Current retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainAS07IdentityClearanceCandidate_v047`. Build evidence is `Saved/Audits/PressTrains/press_train_a_s07_identity_clearance_v047.json`; exact static evidence `Saved/Audits/PressTrains/press_train_a_s07_identity_clearance_static_v047.json` passes 128 presentation meshes, seven stages/facades, four unique process cues, all five cameras, unchanged `15000.005 x 56000.001 x 11350 mm` bounds and zero failures.
- Five fresh 1920x1080 exact-map captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v047/`. Direct original-resolution comparison against Pro Sheets 04/05 is `Saved/Audits/PressTrains/press_train_a_visual_review_v047.json`, status physical segmented identities retained / release-art hold / not promoted.
- Remaining visual holds are heavy crown/frame mass, believable S01 blank feed and S07 panel discharge/inspection/stillage flow, clearer service-side die-cart/dock mechanics, final shared hall context and condition variation. Do not promote v039-v047 or begin costly runtime gates until these visual holds materially improve.

# Press Train A v051 retained crown/endpoint refinement; release-art hold (2026-08-05, latest)

- Reusable `SourceAssets/PressTrains/Shared/CrownEndpointPresentation_v002/` contains three assets: a shared deep fabricated S02-S06 crown with recessed drive evidence, an S01 visible blank-feed module and an S07 visible formed-panel discharge/inspection/stillage module. Source audit `Saved/Audits/PressTrains/press_train_crown_endpoint_presentation_source_audit_v002.json` passes dimensions, hashes, material slots, local bounds and TBC authority.
- v048 passed static gates but was visually hidden behind the operator facades. v049 corrected depth but projected bright crown boxes too far; v050 brought them flush/darker but kept an oversized repeated circular guard. These maps are rejected as final art and remain unpromoted history.
- Current retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainACrownEndpointRefinementCandidate_v051`. Seven existing presentation actors are replaced in place with v002 meshes. Exact static evidence `Saved/Audits/PressTrains/press_train_a_crown_endpoint_refinement_static_v051.json` passes 135 presentation meshes, 180 scoped actors, five v002 crown bindings, S01/S07 endpoint bindings, all five cameras and unchanged `15000.005 x 56000.001 x 11350 mm` bounds.
- Five fresh 1920x1080 exact-map captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v051/`. Original-resolution Pro comparison `Saved/Audits/PressTrains/press_train_a_visual_review_v051.json` retains the recessed crown and visible endpoint direction but keeps the release-art gate open. Do not promote v048-v051.
- Remaining immediate holds: stronger camera-readable blank/panel material state, dark/unfinished die-change service side, weak clamp/tow/connector/cable-chain proof and three non-fatal missing-smoothing-group warnings on v002 import that require a clean later re-export/import gate. Continue die-change evidence next; runtime gates remain deferred.

# Press Train A v053 retained die-change evidence parent; release-art hold (2026-08-05, latest)

- Current retained isolated map is `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053`, descended from retained v051 through rejected v052. v052's closer cameras revealed the cart geometry but clipped worked-steel surfaces and identity; do not promote v052.
- v053 preserves the closer three-quarter service/cart compositions and reduces service/cart exposure to `0.56/0.52`, five rect lights to `205` and five dock fills to `105`. Exact static evidence `Saved/Audits/PressTrains/press_train_a_die_change_lighting_static_v053.json` passes 180 scoped actors, five cameras, all seven v002 crown/endpoint bindings and unchanged `15000.005 x 56000.001 x 11350 mm` bounds.
- Five fresh 1920x1080 exact-map images are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v053/`. Review `Saved/Audits/PressTrains/press_train_a_visual_review_v053.json` retains the improved service evidence: the six-wheel bogies, tooling stack, side drive housings and clamp hardware now read without v052 clipping. **v053 is not promoted.**
- A Python commandlet rendering attempt crashed inside Unreal 5.8 `FunctionalTesting`; it produced no evidence. The proven one-camera-per-normal-`UnrealEditor` route then produced all five valid images. Do not report the failed commandlet as a gate pass.
- Release holds remain: dock connector/tow-eye/cable-chain engagement is still partly occluded; operator-side finish is too clean/bright/modular versus Pro Sheets 04/05; S01 blank and S07 formed-panel states remain weak; v002 has three smoothing-group warnings; shared hall context and every native runtime/HMI/motion/flow/audio/fault/save/collision/navigation/crane-clearance gate remain open.
- No new Pro redesign is required. Sheets 04/05 already define the exterior direction. Continue from v053 with material-state/industrial-finish correction, clean v002 re-export/import and explicit dock-coupling evidence before costly runtime work. Global Train A-D datums remain `TBC_NOT_INVENTED`.

# Accepted v103 whole-shop walkthrough visual failure (2026-08-05, latest)

- The user opened `/Game/LineBoss/Maps/LB_PressShop_PR010Accepted_v103` in PIE and supplied seven free-camera 3840x2160 screenshots covering the overhead cranes, coil zones, connected PR-005–PR-010 machinery, floor routing and large hall areas.
- This evidence does **not** reverse the accepted PR-009/PR-010 station-level technical/runtime/save/collision/navigation/HMI result, but it proves that v103 is not a release-quality complete Press Shop. The accepted map remains preserved and must not be edited in place.
- Authoritative defect record: `Saved/Audits/PressShopIntegration/user_walkthrough_visual_review_v103_2026-08-05.json`, status **WHOLE-SHOP VISUAL GATE FAIL / ISOLATED ENVIRONMENT SUCCESSOR REQUIRED**.
- Confirmed blockers include a real-time skylight with no valid sky component, competing directional lights, timber/plank-like or heavily repeated coloured floor finishes, clipped white pools beside unresolved black voids, sparse/unfinished hall regions, inconsistent machinery/service density, repetitive coil presentation and incomplete crane/route/structure integration.
- The Unreal source-content-change prompt visible in the screenshots is not an import approval. Controlled source files must use scripted isolated intake; choose **Don't Import** in the open accepted map.
- A read-only exact-actor audit is prepared at `Scripts/inspect_press_shop_integrated_environment_v103.py`. Run it after the interactive editor session ends, then create a v103-derived isolated environment correction candidate. Repeat the station gates plus new whole-shop fixed cameras and Pro-reference inspection before any integrated-map promotion.
- Train A `DockCouplingEvidence_v001` source and its v056 import script were prepared concurrently but remain unpromoted and must not distract from closing the integrated lighting/floor/hall defects.

# Integrated environment v104 visual rejection and control-room intake (2026-08-05, latest)

## Control-room operator-aim monitor correction v006 source / v008 Unreal (2026-08-05, latest)

- User correctly rejected the v005/v006 positive-pitch appearance: although reduced to 12 degrees, the monitor bank still read as aiming toward the ceiling from the seated chair.
- Preserved all earlier source/maps and generated unpromoted `SourceAssets/ControlRoom/MainControlRoom_v006`. Main screens, frames, UI layers, terminal screens and mothballed masks use `-12` degree Blender X pitch, which aims their faces down toward the seated 1.12 m eye position while remaining inside Sheet 05's 10-15 degree magnitude.
- Source inspection uses twelve fresh 1920x1080 renders. The seated, console-detail and elevated views visibly present the faces to the operator.
- Imported only corrected `Interaction` and `State_Mothballed` meshes into `/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v008`, derived the playable map `/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008` from v007 and preserved `LBControlRoomGameMode`/`LBControlRoomPawn`.
- Technical import audit `Saved/Audits/ControlRoom/main_control_room_operator_aim_import_build_v008.json` passes. Fresh actual `-game` evidence is `Saved/ValidationScreenshots/ControlRoom/v008_operator_aim/main_control_room_v008_runtime_seated.png`; visual review `Saved/Audits/ControlRoom/main_control_room_operator_aim_visual_review_v008.json` passes this physical-orientation sub-gate.
- **v008 is not promoted.** Next: install the real PR-004 authority-backed console on the corrected bank, verify seated interaction, then wire one selected live Press Shop CCTV feed and repeat fixed-camera Pro inspection.

## Control-room screen-orientation correction v003 (2026-08-05)

## Control-room physical monitor-pitch correction v005 source / v006 Unreal (2026-08-05)

- User correctly identified that v003/v004 monitor geometry still appeared aimed toward the ceiling. The underlying v004 source used 72-degree main-screen and 78-degree terminal-screen X rotations despite Pro Sheet 05 specifying a 10-15 degree panel tilt.
- Preserved v004 unchanged and generated the canonical unpromoted successor `SourceAssets/ControlRoom/MainControlRoom_v005` with all main screens, UI layers, frames, terminal screens and mothballed masks corrected to 12 degrees.
- Fresh source renders confirm the screen faces are upright and operator-facing.
- Imported only the corrected `Interaction` and `State_Mothballed` categories into `/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v006` and assembled `/Game/LineBoss/Maps/LB_MainControlRoom_MonitorPitchCandidate_v006` from the v004 presentation map.
- Import/build audit: `Saved/Audits/ControlRoom/main_control_room_monitor_pitch_import_build_v006.json` — PASS technical import, not promoted.
- Fixed-camera visual review: `Saved/Audits/ControlRoom/main_control_room_visual_review_v006.json` — monitor pitch/orientation PASS; overall candidate remains unpromoted because gameplay, live-feed, collision, save/authority and final polish gates remain open.
- Fresh screenshots: `Saved/ValidationScreenshots/ControlRoom/v006_monitor_pitch/` (seated, front, elevated).

- Built `/Game/LineBoss/Maps/LB_MainControlRoom_SeatedVisualCandidate_v003` from the unpromoted v002 presentation candidate.
- Corrected the Blender-to-Unreal Y-axis camera conversion. Fresh seated/front captures confirm that the console screen faces and their authored upward tilt point toward the operator; the earlier apparent reversed orientation was caused by viewing the screen backs from the incorrectly converted camera side.
- Fresh fixed-camera captures are in `Saved/ValidationScreenshots/ControlRoom/v003_seated_visual`.
- Visual review: `Saved/Audits/ControlRoom/main_control_room_visual_review_v003.json`.
- v003 is **not promoted**. The orientation correction passes, but the displays remain too tall and obscure too much of the overview wall compared with Pro Sheet 05; lighting is still too bright; the elevated validation camera intersects/looks above the ceiling; gameplay/live feeds are not yet wired.

- Exact v103 inspection is recorded in `Saved/Audits/PressShopIntegration/integrated_environment_inspection_v103.json`: 67 lights, two active directional lights and one real-time skylight without atmosphere/cloud support explain the on-screen warnings. The front-end floor material master used concrete-pillar textures, which explains the plank-like floor repetition.
- Isolated `/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v104` corrected those exact technical causes without changing accepted v103. Its build and static gates pass, but its four fresh 1920x1080 fixed images failed the mandatory human visual gate. Verdict: `Saved/Audits/PressShopIntegration/integrated_environment_visual_review_v104.json`, **HALL COMPOSITION AND CAMERA REWORK REQUIRED / NOT PROMOTED**. The room-sized black void, sparse hall, roof/column occlusion, isolated light pools and non-actionable cameras remain blockers.
- The other control-room task's latest promoted source release is v004, not v003. It was preserved under `SourceAssets/ControlRoom/MainControlRoom_v004`; staging remains untouched. Authority is fixed Sheet 03: 14,400 x 7,800 x 3,600 mm with a 600 mm raised floor, Cairnwell Automotive / Moorcross Works identity and no diegetic working-title branding.
- Unreal v001 imported the v004 package as nine combined category meshes into `/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v001` and assembled `/Game/LineBoss/Maps/LB_MainControlRoom_IntegrationCandidate_v001`. Envelope audit passes exactly at 1440 x 780 cm. Import exposed missing smoothing-group data on multiple FBX nodes, so the final source-import gate remains open. v001 visual evidence is retained as an exposure/camera-axis failure and is not promoted.
- Isolated `/Game/LineBoss/Maps/LB_MainControlRoom_PresentationCandidate_v002` duplicates the meshes, applies 21 UE-native Cairnwell materials, locks exposure and mirrors camera Y because Blender +Y maps to Unreal -Y. Fresh seated/front images at `Saved/ValidationScreenshots/ControlRoom/v002_presentation/` confirm the screen faces and authored tilt are correct; the earlier apparent wrong orientation came from viewing their backs. v002 remains unpromoted: seated eye position/composition, smoothing groups, full fixed-camera suite and gameplay/runtime gates remain open.
- Next control-room work: refine the seated player eye position, complete the v002 visual suite against Pro Sheets 01/03/05, implement a no-walking seated pawn, then wire one real console to existing Press Shop station state and one selected live CCTV feed. Inactive feeds must be cached/throttled. Do not fake interactivity with static screens.
# PR005 exterior-enclosure integration v193-v195 (2026-08-06, latest)

- Retained runtime parent remains `/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053`; its package hash stayed unchanged throughout this work.
- Candidate v193 used incorrect unsuffixed source asset names and added no enclosure modules. It is a failed build and must never be used as a parent.
- Candidate v194 imported the correct v003 assets but a positional `Rotator` call applied 90 degrees of pitch instead of yaw. The shell lay through the station; v194 is rejected and must never be used as a parent.
- Candidate v195 `/Game/LineBoss/Maps/LB_PressShop_PR005ExteriorIntegrationCandidate_v195` corrects the transform with named pitch/yaw/roll fields. Its build audit `Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_integration_build_v195.json` passes source orientation, exact expected shell bounds and unchanged v053 hash.
- Four fresh fixed-camera captures under `Saved/ValidationScreenshots/PressShopIntegration/pr005_exterior_integration_v195/` prove that v195 is upright but visually and operationally unsuitable: the grey source shell overlaps the inherited yellow collision/navigation/runtime cage, a retained structural column penetrates the shell edge, and the combined assembly reads as a doubled unfinished enclosure.
- Authoritative verdict: `Saved/Audits/PressShopIntegration/press_shop_pr005_exterior_integration_visual_review_v195.json`, status **REJECT / NOT PROMOTED / NEVER PARENT**. Continue from v053, not v193-v195. The next source successor must resolve enclosure authority and provide verified column clearance while preserving v053 equipment, HMI, movers, collision, navigation and logistics.
# PR005 runtime-cage infill v197 retained direction (2026-08-06, latest)

- The rejected v195 full shell proved its datum/orientation but duplicated the native cage and intersected a hall column. A new reusable source asset was therefore authored at `SourceAssets/Candidate/PressShop/PR005/RuntimeCageInfill_v004`, with an immutable-safe UE scale derivative at `RuntimeCageInfill_UnrealDerived_v005`.
- The new asset deliberately uses retained v053 `GuardingHMI` as the only safety/collision/navigation structure. It adds only NoCollision dark kick panels, inspection glazing, process-bay roof cassettes, service covers and Cairnwell/Moorcross identity; it adds no door, HMI or runtime mover. Exact UE intake passes dimensions, handedness, pivot and all six material slots with zero reported drift.
- v196 stopped safely on a Python `Vector` indexing error in the overlap validator and is failed evidence, never a parent. Corrected `/Game/LineBoss/Maps/LB_PressShop_PR005RuntimeCageInfillCandidate_v197` is a fresh direct child of retained v053.
- v197 build evidence proves unchanged v053 hash, exact expected world bounds, no structural-column overlap, all four native guard/gate actors still collision- and navigation-authoritative, and no duplicate doors/HMI. Exact runtime navigation, static collision/navigation and traceable PR004-to-PR005 handoff all pass; all 15 native mover bindings remain present.
- Four fresh fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/pr005_runtime_cage_infill_v197/`; live HMI/logistics PIE views are under `v197_pr005_runtime/`. The cell now reads as one coherent yellow guarded enclosure with attached lower panels, controlled glazing and roof rather than two overlapping cages.
- Exact operational audit `Saved/Audits/PressShopIntegration/press_shop_pr005_runtime_sequence_v197.json` now passes commissioning, dry cycle, first-off approval, automatic start, interrupted-motion safe restore, guard-open fault, two unsafe-reset rejections, corrected reset, persisted fault restore and final safe recovery. Native guard collision/navigation remains present throughout.
- Decision: **RETAIN V197 AS THE UNPROMOTED PR005 EXTERIOR VISUAL-INTEGRATION PARENT; DO NOT PROMOTE.** Review: `Saved/Audits/PressShopIntegration/press_shop_pr005_runtime_cage_infill_visual_review_v197.json`. Remaining holds include roof/structure finish, glazing calibration, hall/logistics presentation, physical gate animation/state binding, campaign disk-slot serialization, exact runtime audio binding/listening evidence and the unresolved 10.4 m versus 11.5 m notation. Never parent from v193-v196.

# PR005 state-driven spatial audio v198 retained runtime parent (2026-08-06, latest)

- The powered C-hook task is closed separately; v143/v190 were not changed. `/Game/LineBoss/Maps/LB_PressShop_PR005AudioRuntimeCandidate_v198` is an isolated direct child of retained v197. Protected v197 SHA-256 remains `30CE02418F66E77122CCBB07F9745E14D1640EB05D1A7629865869C90C8B85C1`.
- Native `ALBPR005Station` now binds the already imported twelve-source Candidate_v001 library according to `SourceAssets/PR005/pr005_audio_contract_v001.json`. HPU, coil-car travel, roller-drive, strip-motion and warning-alarm loops are state/cause requested; coil-car start/stop, mandrel expansion, keeper engagement, gate interlock, controlled stop and emergency stop are cause-bound one-shots. Eight emitters are spatialized, explicitly attenuated and silent by default.
- A sequencing correction makes external `SetCoilCarPositioned(true)` end the loading presentation, play the stop cue and remove coil-car travel audio before dry cycle. No machine performance, gate travel or engineering value was invented.
- Exact v198 PIE audio evidence passes active playback and transitions through dry cycle, certified idle, starting, running, controlled stop and guard-open fault. The real Windows audio device initialized at 48 kHz stereo. Final subjective whole-hall mix audition remains open.
- Exact v198 runtime navigation, collision/navigation, traceable PR004-to-PR005 handoff, commissioning, first-off approval, automatic run, interrupted-motion safe restore, unsafe-reset rejection, persisted fault restore and final recovery all pass.
- Fresh live HMI and logistics captures under `Saved/ValidationScreenshots/PressShopIntegration/v198_pr005_runtime/` confirm inherited v197 cell presentation, but also reconfirm that the cart/pallets, floor transition and surrounding hall remain blockout. **RETAIN V198 AS THE UNPROMOTED PR005 RUNTIME/AUDIO PARENT; PRESERVE V197 AS THE EXTERIOR VISUAL CHECKPOINT; DO NOT PROMOTE.** Closure: `Saved/Audits/PressShopIntegration/press_shop_pr005_audio_runtime_closure_v198.json`.
- Campaign persistence is now exact-map proven. v198 wrote a running station snapshot to a named format-10 disk slot; a separate fresh editor process loaded it, restored safe Idle with the safety reset cleared, preserved coil/heat/lot/barcode/recipe/certification, required explicit revalidation and restart, then raised the correct guard-open fault. Both isolated slots were removed after readback. Evidence: `press_shop_pr005_disk_slot_writer_v198.json`, `press_shop_pr005_disk_slot_readback_v198.json`, plus green PR004→PR005 writer/readback automation reports under `Saved/Automation/`.
- Remaining immediate holds: physical gate animation (range still TBC), subjective whole-hall mix, PR005 roof/glazing/logistics/hall release art and the unresolved 10.4 m versus 11.5 m notation.
# 2026-08-06 — Train A S07 robot reference correction (active)

- Real tandem stamping references supplied by the user are now the visual direction for S07: compact press-adjacent proportions, slim cast/rectangular links, enclosed round joints, short pedestal, wrist/tooling and restrained cable routing.
- v014 is technically green but visually rejected; never promote it. Static evidence confirms its nine robot actors exactly retain the v009 world transforms and hierarchy, so the player-view separation is a geometry/proportion failure.
- Evidence: `Saved/Audits/PressTrains/press_train_a_robot_visual_rejection_v014.json` and `Saved/Audits/PressTrains/press_train_a_robot_hierarchy_static_v014.json`.
- `SourceAssets/Candidate/PressTrains/TrainA/AssemblyStudy_v010` is a source-only continuous-arm successor. It keeps 336 actors, exact 15,000 x 56,000 x 10,750 mm bounds and the native robot contract. Unreal intake and fresh fixed-camera review are open; it is not promoted.
# 2026-08-06 — Robot family pack intake and connected Train A v016

- The supplied Cairnwell family sheets define visual language for six separate task variants; they do not certify generated payload, reach, speed, battery, safety, standards or dimensions. Those remain TBC.
- v015 is rejected/non-parent because directional mesh-local Y was mirrored by the legacy FBX conversion, causing a disconnected robot despite correct actors and hierarchy.
- v016 corrects only robot mesh-local Y during staging, remains a direct v013 child, and shows connected rest and moving poses. Map SHA-256 `AC4AE375AC4A014586A4DA4AF62EF009504B790BD675D65B9D6B066773BC2183`.
- v016 static and PIE gates pass; exact Train A automation is 1/1 and full Press Shop is 15/15. Retain it as the technical axis-integration parent only. Cosmetic family implementation and fresh final player-view comparison remain open. Evidence: `Saved/Audits/PressTrains/press_train_a_robot_family_design_pack_intake_v016.json`.

# 2026-08-06 — Train A S07 Cairnwell robot-family successor v017 retained

- Three owner-supplied robot-family sheets define one Cairnwell visual language with separate press-handling, body-weld, paint, PR-004 depackaging, coil-AGV and pallet/forklift-AGV variants. They are visual references only; unverified engineering figures remain TBC.
- `AssemblyStudy_v012` preserves the 336-actor Train A contract and all 9 S07 robot pivots/roles/hierarchy edges while adding charcoal cast housings, orange joint accents, restrained cables, service details and a steel multi-cup vacuum tool.
- `/Game/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017` is a fresh v013 map child, SHA-256 `E647EB62C3552CF39EFFE83687C2A3AA058C0323F2DD53DACFD5FD0738B02E42`. Fresh static and PIE gates pass; peak robot motion is 34.56 degrees; exact Train A automation passes 1/1 and the full Press Shop passes 15/15.
- Fresh fixed-camera Unreal evidence shows a connected robot and attached tool at peak unload. Retain v017 as the current S07 visual successor, not as a whole-area promotion. Collision/swept volume, navigation/service clearance, sound and wider Train A release gates remain open. Decision: `Saved/Audits/PressTrains/press_train_a_robot_family_visual_decision_v017.json`.

# 2026-08-06 — Train A physical gameplay successor v024 retained

- Fresh direct v017 child `/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024`, SHA-256 `2AEE55ABF7AFB975CD0D9558AB84846F45B626F0455F24D9AE857EA803651584`, replaces seven inherited station-wide proxy boxes with 61 fixed blockers, 65 QueryOnly movers and 489 source-derived simple boxes. Failed v018-v023 are not parents.
- Exact static and PIE gates pass standing-pawn floor/aisle clearance, complete 3,800 cm runtime navigation, maintenance approach, guarded-entry blocking, query-only moving machinery, a full robot cycle and zero unexpected robot/blocker overlaps.
- Original Train A motion/safety/save validation passes with 34.34-degree robot motion and one visible workpiece. Exact Train A automation passes 1/1; full `LineBoss.PressShop` passes 15/15. Retain v024 as the unpromoted physical-gameplay successor. Sound, installed Train A-D datums and whole-hall cumulative/release-art work remain open. Decision: `Saved/Audits/PressTrains/press_train_a_physical_gameplay_decision_v024.json`.

# 2026-08-06 — Train A state-driven spatial audio successor v027 retained

- Fresh direct v024 child `/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027`, SHA-256 `00225848C15668BE523F181FD81A8C1FB472675A724B72847B9E206A7C99848F`, retains the finished Cairnwell S07 press robot and exact physical policy. Failed v025 is not a parent; v026 is superseded.
- Eight original `Audio_v002` sources pass 48 kHz mono PCM and zero-clipping QA. Six native spatial emitters follow real Train A state/phase and distinguish press, robot, controlled-stop, access-fault/alarm and emergency-stop events.
- Live audio cause/effect, motion/safety/save and exact physical inheritance all pass. The candidate has the same 366 actors as v024 with zero physical changes. Exact Train A automation is 1/1 and full Press Shop is 15/15.
- Retain v027 as the unpromoted Train A physical/audio successor. No separate robot task is required. Remaining gates are subjective whole-hall mix, authoritative Train A-D installed datums and cumulative release-art integration. Decision: `Saved/Audits/PressTrains/press_train_a_audio_runtime_decision_v027.json`.

# 2026-08-06 — isolated Press Trains B-D shared-runtime variants v001 retained on visual hold

- `ALBPressTrainAStation` now serves as the shared Train A-D runtime class. Its guarded variant configuration accepts only `TRAIN_A`-`TRAIN_D`, provides distinct native HMI/part-family/accent identity and output namespaces, and rejects cross-train save restoration. Existing Train A behavior is preserved.
- Three direct v027 isolated successors retain the exact 366-actor physical/audio contract with no invented world datum: Train B `/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001` SHA-256 `EA511F15D2E70C0FD84560CF8DD8B6909512ED2F051EC1B8230BEAD29BBAA30E`; Train C `/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001` SHA-256 `1F7282069883B84ECB537A666CE860902BA6B41F316752B4EE17775BA92423F6`; Train D `/Game/LineBoss/Maps/LB_PressTrainDIsolatedVariantCandidate_v001` SHA-256 `300ABFE9E5C9B259A68F366AAD2E2B235FA777244921003F9F5CDD1FCFD62982`.
- Per-variant PIE passes the full native motion/HMI/safety/fault/isolation/save sequence. The post-change complete regression report passes 15/15 at `Saved/Automation/PressTrainSharedVariantAuthority_v001_FullPressShop/index.json`. Protected v027 remains `00225848C15668BE523F181FD81A8C1FB472675A724B72847B9E206A7C99848F`; protected cumulative v213 remains `1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554`.
- Fresh live hero, S02 draw and S07 unload frames exist for B, C and D. Sheet 06-08 review retains them as technical/directional parents only: B green deep-draw and D purple smaller-die cues read; C's orange closure/flexible-gripper differentiation is not yet sufficiently visible, and no black-void isolated view can prove installed release quality.
- **RETAIN B-D V001 UNPROMOTED; VISUAL RELEASE HOLD; DO NOT INSTALL WITHOUT AUTHORITATIVE DATUMS.** Decision: `Saved/Audits/PressTrains/press_train_bcd_isolated_variant_runtime_visual_decision_v001.json`. Next create a non-overwriting visual successor that improves Train C identity/gripper legibility and captures B/C operator-side tooling.

# 2026-08-06 — B/C visual-successor v002-v004 disposition

- B/C v002 passed build and PIE but failed fixed-camera differentiation; preserve it as visually rejected. B v003 failed its collision gate and C v003 was never created; preserve B v003 only as failed lineage.
- Direct-v001 B/C v004 successors each contain 387 actors with 21 new visual-only actors, explicit `NoCollision` and no inherited transform changes. Both pass live motion, controlled stop, fault recovery, isolation and save gates.
- Hero/operator-side captures remain over-bright and the stage identity treatment is washed out or too small, leaving B and C insufficiently distinct. **REJECT B/C V004 VISUALLY; NEVER PROMOTE OR USE V002-V004 AS PARENTS.** B/C v001 remain the isolated technical/directional parents and installed placement remains TBC.
- Evidence and immutable lineage: `Saved/Audits/PressTrains/press_train_bc_visual_successor_lineage_decision_v004.json`.

# 2026-08-06 — standing-player floor-spawn runtime correction

- The v213 standalone owner session revealed that a default `ALBControlRoomPawn` without a `PlayerStart` was centred at `Z=0`; its 88 cm standing capsule therefore overlapped the floor and blocked the otherwise correct `WASD` movement.
- Native `BeginPlay` now traces to static floor below the initial transform and resolves the capsule centre to floor height plus its scaled half-height plus 2 cm before locking the walk area, with a safe half-height fallback and no seated-path change.
- Editor Development build passed. Fresh standalone v213 evidence logged seat `Z=95`, camera `Z=175` and a responsive process. Protected v213 remains byte-identical. Audit: `Saved/Audits/ControlRoom/standing_player_floor_spawn_runtime_fix_v001.json`.
- Focused control-room automation and post-session collision/navigation walking validation remain open; do not call this release-complete from the live log alone.

# 2026-08-06 — unrestricted owner inspection mode v001

- Added native `ALBFreeRoamGameMode`/`ALBFreeRoamPawn` as an inspection-only alternative to the bounded standing-player and colliding built-in default pawn. The spectator is explicitly `NoCollision`, unbounded and forced to start at or above `Z=500 cm`.
- Editor Development build passed and fresh v213 standalone runtime proved the 500 cm no-collision start with a responsive owner session. Production interactions/save authority remain intentionally absent from this mode; `LBControlRoomGameMode` remains authoritative gameplay.
- Protected v213 is unchanged. Audit: `Saved/Audits/ControlRoom/unrestricted_free_roam_runtime_v001.json`. Focused native defaults/input automation remains open until the owner session can be closed safely.
# Press Shop playable coil/shell checkpoint v233 (2026-08-06, latest)

- Press Shop environment/machinery remains the active priority; gameplay expansion is deferred.
- Exact PIE proves v230's runtime inventory is already correct and pale silver (11 stored + CS-06 on the Coil AGV). Dark editor-only captures did not represent playable presentation. v231 and v232 are rejected/non-parent experiments.
- Latest retained unpromoted child: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233`, SHA-256 `BA327B0CC7A56F14E468B4C1F3734D3AD7D6E2B00BCB3CD9A262C45120C7DD2A`. It changes only four perimeter-wall and twenty roof-liner material slots; v230 remains byte-identical at `C5BC0FFA15FD54AA2F5803ECC6B03DD2320A8C1BC6DB294EC0448177698145A4`.
- Exact v233 management PIE passes PR004-PR010, all four trains and Start/Pause/Stop/isolation. Visual release remains open: black upper roof field, high train contrast and structural-column occlusion. Camera-only v234 is rejected and never a parent.

# 2026-08-06 — MR01 straight-reverse dock and compact parked arm retained in isolation

- The maintenance robot does **not** dock sideways. It reverses straight in, rear charging face first, while its front identity/control face remains toward the aisle.
- Fresh non-overwriting MR01 `/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v022/Blueprints/BP_LB_MR01_MaintenanceAMR_v022` uses corrected v022 static payload and a presentation-only `-90°` axis root. Native RP01 collision, wheels, contacts, sockets, route projectors and pivots remain unchanged.
- Fresh direct retained-dock-family validation map `/Game/LineBoss/Developer/Validation/LB_ServiceDockActualRobotFit_v013` proves zero native contact-frame error, a 155 x 93 x 125 cm collision envelope in a 126 cm portal and 33 cm lateral body clearance. Protected cumulative Press Shop v253 stayed byte-identical at `51CAF557666AB9F4FE6833165BEA30223200059E9AB548D38DF64074C7094842`.
- Live PIE proved the old arm stayed flat. Root cause was native axis mapping, not bad skin weights: authored links run along local `-Y`, so J2/J3/J5 pitch must use Unreal Roll/X and J4/J6 axial roll must use Pitch/Y. The corrected native mapping compiled successfully.
- A 15,444-candidate live-FK search plus direct visual review selected exact parked state `[180, -75, 150, 0, 120, 0]` degrees at 0 mm lift. Its conservative 16 cm-radius link envelope is 32.0 x 85.1259 x 95.7325 cm, stays inside the native XY footprint, peaks at Z=168.1259 cm and places the TCP 18.3677 cm from the native cradle.
- Fresh live default-state image: `Saved/ValidationScreenshots/SupportRobots/ServiceDocks/ActualRobotFit_v013/service_dock_actual_robot_fit_v013_mr01_runtime_parked_v023.png`, SHA-256 `F64A9972050B54C31E66E82818417C9A27CA7177CBCCEF0EDA71C25306802D27`.
- `LineBoss.SupportRobots.MR01.FunctionalRuntime` passes with v022 fresh-load/spawn, upward shoulder fold, exact parked authority, shared wheels, T6 change, 400 mm connected lift, save/restore, collision and route blocking. Decision: `Saved/Audits/SupportRobots/mr01_straight_dock_compact_parked_pose_decision_v023.json`.
- Retain v022/v013 as isolated technical/visual successors only. Do not overwrite retained/protected maps. Next create a fresh Press Shop child and place two independent MR01 docks and two independent CR01 docks after an exact support-area/clearance audit.

# 2026-08-06 — Press Shop support fleet v260 retained unpromoted

- `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v260` is a fresh direct child of protected v255, SHA-256 `4A7DC500CE8B23CFEA06EC81B4CC88BE8DF4574B2C6F99856703C55B71383B8F`. It contains two MR01, two CR01 and four independent service/charging docks; v255 remains byte-identical at `38884454F39F649B9767517ECE6A68B7029B1D27219FD5FBA81483FF2DC71A23`.
- Every robot docks straight rear-first with exact `0.0 cm` native contact alignment. The dock visual alone is yaw-corrected `180°` so the open portal faces the aisle; robot, collision and runtime transforms are unchanged.
- Exact-map collision, playable-management, PR009 navigation and PR010 navigation pass. Post-change automation is green: Press Shop 16/16 and Support Robots 3/3, zero warnings.
- Five live fixed views in `Saved/ValidationScreenshots/SupportRobots/PressShopFleet_v260/` pass visual review. **RETAIN V260 UNPROMOTED AS THE CUMULATIVE SUPPORT-FLEET PARENT.** Never parent v254 or v256-v259. Remaining holds are robot dispatch routes/gameplay, dock door/drawer/probe/tool-rack sweeps, final hall release-art comparison and subjective audio. Decision: `Saved/Audits/SupportRobots/press_shop_support_fleet_visual_runtime_decision_v260.json`.
# 2026-08-07 v270 MR01 modular dock comparison decision

- Protected playable Press Shop remains `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269`; it was not changed.
- Fresh direct-child v270 replaced only `LB-DOCK-MR01-01` and retained the existing aggregate dock as an in-hall control.
- The first close camera was rejected and corrected without changing dock geometry. Fresh evidence: `Saved/ValidationScreenshots/SupportRobots/PressShopDockComparison_v270/press_shop_mr01_dock_pair_v270.png`.
- Visual result failed: the modular replacement renders mainly as the service cabinet/rear module and does not reproduce the complete retained aggregate dock bay.
- Decision: `REJECT_VISUAL__RETAIN_TECHNICAL_RUNTIME__DO_NOT_INTEGRATE_FOUR_DOCKS`. Guarded native mover/runtime work remains retained; repair the MR01 static-shell export grouping before another single-dock comparison.
- Decision audit: `Saved/Audits/SupportRobots/press_shop_mr01_modular_dock_comparison_decision_v270.json`.
# 2026-08-07 v271 correction — MR01 modular dock visual identity

- This entry supersedes the earlier v270 visual interpretation below; the earlier record is retained as lineage.
- Direct actor identity proves the complete left bay at X=-6495 cm is the modular `LB-DOCK-MR01-01`; the complete right bay at X=-5095 cm is the retained aggregate control. The isolated cabinet between them is a pre-existing workshop actor.
- Replacement static bounds are 260.0 x 149.1 x 170.7 cm versus retained 260.0 x 155.0 x 170.7 cm. All authorised movers remain inside the retained visual envelope. The larger actor bounds came from an invisible safety box.
- Single-dock visual/geometry gate passes, but promotion remains forbidden pending removal of its three superseded proxy blockers and collision/management regression on a fresh direct-v269 child.
- Evidence: `Saved/Audits/SupportRobots/press_shop_mr01_modular_dock_comparison_identity_v271.json` and `Saved/Audits/SupportRobots/press_shop_mr01_modular_dock_comparison_decision_v271.json`.
# 2026-08-07 v277 retained four-native-dock candidate

- Fresh direct-v269 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v273` now contains two guarded MR01 docks and two guarded CR01 docks. The 12 superseded proxy blockers were removed only in the child; v269 remains byte-identical at `DDB2708F...EFD9`.
- Route authority was corrected so each robot ignores only its own assigned native dock inside the 3.5 m approach/egress envelope. Other docks, machinery, guards, floors and robots remain authoritative. Build and `LineBoss.SupportRobots.ServiceDock.GuardedMechanismsAndSafeRestore` pass.
- Collision: 12 native structural boxes, zero unexpected overlaps, all 12 old proxy blockers absent.
- Runtime: all four robots dispatch, reach standby, return to the correct dock and resume charging. Standing control-room selection/dispatch/recall passes, including the physical console hit targets.
- The first v273 images are rejected because capture preceded material compilation. Accepted compiled-material evidence: `press_shop_native_docks_v273_mr01_pair_compiled_v276.png` and `press_shop_native_docks_v273_cr01_pair_compiled_v276.png` under `Saved/ValidationScreenshots/SupportRobots/PressShopNativeDocks_v273/`.
- Decision: retain v273 as the current four-native-dock candidate, not promoted. Audit: `Saved/Audits/SupportRobots/press_shop_native_service_docks_retention_decision_v277.json`.
# 2026-08-07 v278 whole-shop regression after native docks

- Exact retained v273 passes whole playable management after the four native docks: PR004–PR010 runtime authorities, all four press trains, honest unsafe-start hold, valid start/pause/stop and train selection.
- PR009 passes two non-partial integrated service routes with zero traversal points inside PR010 protected process space.
- PR010 passes three non-partial routes with zero protected-buffer traversal points.
- v273 remains retained but not promoted; whole-shop fixed-camera release comparison and remaining save/fault/audio completion gates remain open.
- Audit: `Saved/Audits/PressShopIntegration/press_shop_v273_post_dock_whole_shop_regression_v278.json`.

# 2026-08-07 - Train A readable-axis source v040 and isolated Unreal review v328

- The corrected Blender source is `SourceAssets/Candidate/PressTrains/TrainA/UnrealAxisReadableLabels_v040/CA_MW_PressTrainA_UnrealAxisReadableLabels_v040.blend`, SHA-256 `F0FA4875BBA8241BBDBD3906783AD5A6DDAB91207EC096500ACE93E1EB8ED0E5`.
- The corresponding FBX is `SourceAssets/Candidate/PressTrains/TrainA/UnrealAxisReadableLabels_v040/FBX/SM_CA_MW_PressTrainA_UnrealAxisReadableLabels_v040.fbx`, SHA-256 `9E2E5F205567F3083F1BDAB9ACF779957CE02A63CFB383F55F88F9B510D1FF4F`.
- `/Game/LineBoss/Maps/LB_PressTrainA_ReadableLabelsReviewCandidate_v328` proves upright machinery and readable station/process labels from both broadside faces. Accepted images are under `Saved/ValidationScreenshots/PressShopIntegration/v328_train_a_readable_labels/`.
- v319, v320 and v323 are upside-down/rejected; v321 is upright with mirrored/inverted signage; v324 is off-camera; v325 and v326 are retained axis/camera diagnostics only. Do not promote any of those variants.
- v328 is an accepted isolated visual source, not a playable whole-shop promotion. Its combined presentation mesh has `NoCollision` and does not replace native runtime authority.

# 2026-08-07 - Train A whole-shop visual review v329-v333

- `/Game/LineBoss/Maps/LB_PressShop_TrainAOldInGameReview_v329` and `/Game/LineBoss/Maps/LB_PressShop_TrainANewInGameReview_v330` are review children only. Native Train A actors were not deleted; the new v040 presentation actor is floor-seated, positive-scale and visual-only.
- The first matched camera saw only the hall wall and is rejected. The v332 old image is usable, but the v332 new comparison is rejected because transient editor hiding did not survive reload and mixed native Train A visuals with the rebuilt line.
- `Scripts/capture_press_train_a_old_new_ingame_wide_v333.py` is prepared to hide only native Train A visuals at capture time and make a clean retained-wide-camera comparison after the owner's live free-camera session ends.
- The owner is currently inspecting v330 in a visible Unreal Editor session. Do not run commandlets, off-screen captures, or close that editor while it is in use.
- Neither v329 nor v330 is promotable. Final integration still requires authoritative collision/navigation/runtime mapping plus a clean old/new/Pro comparison and full regression gates.
- `Scripts/assemble_press_train_a_old_new_pro_comparison_v334.py` is prepared and verified with the bundled Codex Python/Pillow runtime. After both v333 images exist, it creates a non-overwriting current/rebuilt/Pro evidence sheet plus a SHA-256 audit; it cannot promote a candidate.

# 2026-08-07 - True retained-old versus rebuilt Train A Blender reference v338-v340

- A read-only selected-actor export of the actual retained v301 Train A produced `SourceAssets/Reference/PressTrains/TrainA/InstalledRetained_v301/FBX/SM_CA_MW_PressTrainA_InstalledRetained_v301.fbx`, SHA-256 `1BAEAE39A216D0EFF4B77731A560AE9C01BF0317B86D6ECA9870A6CCA2C0951A`. It selected 338 tagged/prefixed Train A actors and did not save or modify v301.
- The new reference-only Blender file is `SourceAssets/Reference/PressTrains/TrainA/InstalledRetained_v301/Blender/CA_MW_PressTrainA_InstalledRetained_v301_Reference_v339.blend`, SHA-256 `6DC758347393FA4AEBD4D55B330BF91F33E68F99A775C2CBF52368338547C2CD`; it contains 336 renderable imported objects.
- True geometry comparison images are under `Saved/ValidationScreenshots/PressTrains/v340_true_old_new_blender_comparison/`. Old v301 image SHA-256 is `49BA83E62814FE35EE5AA838A802B72AD6A9340DD9191A7E78053DB2D0A87184`; rebuilt v040 image SHA-256 is `C0A9B553166280D083CE127C676EDAAFD451B059FB0C2A3A6B91F41D59BCA83F`.
- The retained-old FBX export is geometry/reference evidence only: Unreal material instances did not round-trip into Blender, so it renders neutral grey. Do not interpret the grey material as an in-game material regression or use this reference asset for promotion.
- The v333 whole-shop rebuilt capture is rejected: the aggregate visual was mixed/occluded and is not a fair current-vs-rebuilt comparison. Preserve it only as failed evidence.

# 2026-08-07 - Player-built storage-zone requirement

- The factory builder must support player-defined storage areas as first-class operational objects, not decorative floor paint.
- Press Shop storage types are: bare coils, prepared blanks/panels, finished-panel stillages, scrap, maintenance spares/consumables and quarantined material.
- A placed zone must carry capacity, accepted material type, occupancy, ingress/egress sockets and AGV/forklift access authority. It must fail placement when it blocks a pedestrian route, emergency access, crane envelope, machine service clearance or another protected zone.
- Build-menu choices are context-sensitive: only storage compatible with the selected shop, connected process stage and next valid production dependency is offered. Automatic identity/signage follows the same deterministic naming authority as player-built press trains.
- Management view uses a variable mouse-wheel zoom, placement grid and optional roof/upper-wall cutaway. The physical roof remains present in standing/free-roam play.
- This requirement extends the builder architecture; it does not authorise copying Car Manufacture assets or files.
- Current gameplay scope explicitly excludes research/technology trees and vehicle sales/dealership systems. Finished output terminates at a validated outbound buffer while the near-term loop concentrates on layout, material supply, automated production, quality, faults, maintenance and throughput.

# 2026-08-07 - Functional storage authority v454

- `ALBPressShopBuildAuthority` now owns authored storage bays and logistics spines in addition to train bays, protected areas and utility spines. Storage placement fails closed for invalid transforms, unsupported material types, incomplete bay containment, protected-area intersections and absent AGV/forklift reach.
- `ALBPressShopStorageZone` is the first functional player-built buffer actor. It provides deterministic IDs (`SZ-COIL-001` pattern), explicit type, capacity, occupancy, query-only zone volume, ingress/egress components and bounded store/withdraw operations.
- Editor build succeeded. Focused Unreal automation `LineBoss.PressShop.Builder.StorageAuthority` passed 1/1 with zero warnings and zero errors. Evidence: `Saved/Automation/StorageAuthority_v454/index.json`.
- This is authority/runtime groundwork, not visual promotion. Management placement UI, authored v438 storage/logistics geometry, save DTO integration, visible floor treatment/signage and AGV dispatch binding remain open.
## 2026-08-07 — Factory Builder automatic transport checkpoint v457

The first reusable automatic roller/belt connection authority is compiled and automation-tested. Machines expose authored process ports; placement may connect only output-to-input across the exact next process stage with matching material/transport types and verified range. The nearest valid predecessor is selected, and invalid or incomplete multi-input chains fail closed and roll back. The current generated actor owns a functional spline route and production-unit counter. Final conveyor geometry, supports, collision/nav, persistence and end-to-end inbound-lorry through finished-panel simulation are not yet complete.
## 2026-08-07 — automatic transport visual/parallel checkpoint v458

The v457 functional link now generates visible instanced rail, roller/belt and support geometry with blocking collision. Authored process-port capacity permits deliberate branching from buffers/distributors to parallel duplicate machinery, while all process-order and compatibility gates remain strict. Build succeeded and the focused automation test passed 1/1 without warnings. These are still implementation-grade procedural visuals; final Cairnwell modules/materials, individual-machine placement integration, persistence and in-game visual/navigation gates remain open.
## 2026-08-07 — automatic replenishment buffer checkpoint v460

Player-built storage zones now expose reorder level, replenishment batch, requested units, outstanding loads, starved and blocked state. Low occupancy raises bounded pull demand and deliveries close it. Player-facing/UI wording must be `Automatic Replenishment`; do not use the manufacturing-method term the user rejected. Build succeeded and the two focused storage/transport tests passed without warnings.
## 2026-08-07 — builder persistence and dragged coil-area checkpoint v468

Generated transport topology is now part of the Press Shop campaign save and restores from stable authored port IDs. Player storage zones also persist their footprint, identity, occupancy and Automatic Replenishment state through the single build authority. Coil storage is now sized by click-drag / hold-X; the preview derives rows, columns and total stands from the accepted 2.2 m × 6.0 m centre pitches and rejects a mismatched manual capacity. Compile succeeded; focused storage/campaign tests passed 2/2 and controller/HUD passed 1/1 without warnings. Runtime input/visual evidence is still open, so this checkpoint is technical only and not promoted.

## 2026-08-07 — generated multi-material storage modules v471

- Player-dragged storage saves its exact generated grid (rows, columns, pitch and boundary clearance). Empty positions remain physically visible and stored-load visuals track occupancy.
- Bare coils use cylindrical loads on saddles. The shared system also covers blank stacks, finished-panel stillages, removable scrap positions, maintenance-parts pallet/rack positions and quarantine positions; each still requires an authored compatible bay and unit pitch.
- Build and focused `StorageAuthority` plus `WholeShopCampaignRoundTrip` automation pass 2/2 at `Saved/Automation/DraggedMultiMaterialStorage_v471`. No production map or visual lineage was promoted; authored map integration and live visual/navigation evidence remain open.

## 2026-08-07 — storage process-graph integration v472

- Functional storage zones now own stable identity-derived process ingress/egress ports with explicit material, transport kind and ordered stage. They are no longer isolated capacity actors.
- A stage-zero inbound coil dock automatically connects by AGV handoff to a placed bare-coil zone's stage-one ingress; its egress can branch to parallel valid next-stage equipment.
- Build and `StorageProcessGraph_v472` pass 3/3 across storage authority, automatic transport and whole-shop campaign persistence. No map was promoted; the individual-machine catalog/placement layer remains the next runtime task.

## 2026-08-07 - Car Manufacture read-only structural study

- A read-only inspection of exposed installed-package metadata found a data-driven Unity structure with separate addressable blueprint, item and factory-entity bundles; a blueprint-preview scene; runtime preview generation; A*/navigation packages; reactive UI/dependency-injection libraries; and structured serialization support.
- Treat these as high-level architectural inspiration only. No proprietary assemblies were decompiled and no source code or game assets were extracted or copied.
- The original Line Boss implementation should use Unreal-native data assets and authority: grid/clearance previews, context-filtered next-valid machine choices, generated catalogue thumbnails, process-compatible auto-links, AGV route checks and modular saves. The management camera remains variable-zoom while standing/free-roam play remains fully 3D.
- Preliminary `ALBFactoryBuildMachine` scaffolding with ordered process ports compiles successfully. It is not promoted and must integrate with, rather than duplicate, existing press-train identity and station authority.

## 2026-08-07 - ordered machine catalogue and native press integration v475

- The context-filtered builder now withholds machines until their required preceding machine/buffer exists and returns actionable reasons. It supports parallel capacity after predecessor authority exists while keeping inbound delivery singular.
- Native press trains own stage-five process ports and keep the established identity, visual, production, safety and save authority. Generic machine actors cover inbound, depackaging, decoiler, inspection and outbound only.
- Generic machine identities/types/transforms are saved. Restore order is now trains, generic machines, storage zones, then automatic transport topology; this fixes dynamic endpoint availability during connection restoration.
- Newly placed storage opportunistically auto-connects to a valid predecessor without invalidating retained maps that author buffers first.
- Evidence: `OrderedMachineCatalogue_v473` 1/1, `OrderedBuilderRegression_v474` 3/3 and `OrderedBuilderCampaign_v475` 1/1 all passed after a successful UE5.8 build. This remains technical-only until HUD, authored envelopes, physical flow and map visual/navigation gates pass.

## 2026-08-07 - traceable player-built production chain v477

- Generic machine queues and player storage now preserve exact material identities. Storage state v3 remains backward compatible with v1/v2 while rejecting incoherent traceability records.
- Transactional transfers require a real compatible generated link and roll both endpoints back when acceptance or route accounting fails.
- End-to-end automation proves one identified coil reaches coil storage, depackaging and decoiling, becomes a deterministic blank, runs through the native seven-stage press authority, becomes an identified panel, passes inspection and finished storage, and completes outbound shipment with identity intact.
- Evidence: `PlayerBuiltEndToEndFlow_v476` 1/1 and `TraceableBuilderPersistence_v477` 3/3 passed after compilation. Lorry/crane motion, continuous dispatch timing, retained-map visuals, collision/navigation and player-facing HUD remain open and must not be inferred from this technical gate.
# Inbound modular source and isolated Unreal review v487-v492 (2026-08-07)

- The four-sheet Pro pack now has seven missing modular Blender/FBX source candidates at `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v001`. Isolated Unreal import passes scale/bounds/body setup, and controlled PBR material binding fixes the rejected pale v489 import.
- Fresh review-only `/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v492` combines the new modules with the retained Coil AGV and powered C-hook/bridge direction. Evidence is `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v492/inbound_overview.png`; decision is `Saved/Audits/PressShopIntegration/inbound_modular_visual_decision_v492.json`.
- v492 is not release art or production placement. Finish the cab/trailer and installed crane/dock envelope, then use a fresh direct child of v438 for authority binding and repeat runtime, save, collision, navigation and fixed-camera gates. v438 remains unchanged.
## 2026-08-07 — Inbound coil delivery v002 / review v494

- Preserved the four-sheet Pro reference pack under `SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807`; it is the visual authority for lorry arrival, four-coil curtain-sided trailer, protected dock, crane/C-hook unload, receiving saddle and AGV handoff. All engineering values remain TBC.
- Imported nine modular v002 source assets at scale 1.0 into `/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v002`. Bounds, body setup, collision and controlled material-slot checks passed in `Saved/Audits/PressShopIntegration/inbound_modular_import_v493.json`.
- Built and captured the isolated map `/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v494`.
- Visual decision: **rejected for promotion, retained as source evidence**. The sequence/count is coherent, but the cab is obscured, trailer/door relationship is unclear, AGV silhouette is ambiguous, crane/C-hook readability is weak and detail is below release standard. See `Saved/Audits/PressShopIntegration/inbound_modular_visual_decision_v494.json`.
- The retained builder-authority map v438 was not modified.
## 2026-08-07 — Inbound coil delivery v003 / Unreal review v497

- Built additive Blender source `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v003` from v002. It raises the previously closed entrance shutter, improves tractor and open curtain-sided trailer cues, keeps exactly four coils, adds a protected crane perimeter and separates the AGV handoff laterally.
- Imported nine v003 modules into `/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v003`. Scale, collision/body setup and controlled material binding passed in `Saved/Audits/PressShopIntegration/inbound_modular_import_v496.json`.
- Built and captured isolated `/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v497`.
- v003 is retained as a genuine source improvement, but v497 is **not promoted**: the lorry cab and crane/C-hook presentation remain below the Pro-sheet visual bar and the cell still lacks installed factory context. See `Saved/Audits/PressShopIntegration/inbound_modular_visual_decision_v497.json`.
- Retained builder-authority v438 remains untouched.
## 2026-08-07 — Inbound installed-context reviews v498-v501

- v498 added walls, roof beams, factory lighting and forced yellow crane/C-hook materials, but its camera was outside the side wall; rejected.
- v499 attempted a camera-only map duplication. UE5.8 aborted with its world-memory-leak safeguard while loading the duplicated map; retain as failed construction evidence and do not use as a parent.
- v500 rebuilt cleanly with the camera inside the bay, but roof beams and narrow walls dominated the frame; rejected.
- v501 rebuilt from v497 with only a rear factory backdrop/columns, opposite-side camera and visible yellow crane components. It is the clearest current installed-context placeholder, but remains unpromoted because the tractor/trailer and crane detail are below Pro fidelity. Decision: `Saved/Audits/PressShopIntegration/inbound_context_review_decision_v501.json`.
- Evaluated CC0 `OpenGameArt_RayB2_Vehicles_2019/vehicles.blend` with provenance retained under `SourceAssets/ThirdParty/CC0`. Rejected for integration because its American conventional low-poly semi is less suitable than the current European cab-over placeholder.
- Retained v438 was not modified; runtime/navigation/save gates were not claimed for this visually failed candidate.

## 2026-08-07 — Inbound lorry orientation reviews v502-v503

- v502 tested the lorry cab with positional Rotator `(0, 180, 0)`. In Unreal this rotated around the tipping axis and left the cab on its side; v502 is rejected and must not be used as a parent.
- v503 repeated the isolated review using positional Rotator `(0, 0, 180)`. This is the correct yaw convention for the current construction scripts: the European cab-over remains upright and its windscreen, grille and front face are now visible.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v503/inbound_orientation_test.png`.
- v503 is retained only as orientation evidence. It is not promoted because crane exposure, factory context, receiving-saddle readability and AGV-handoff presentation remain below the four-sheet Pro reference pack.
- The Pro pack confirms exactly four trailer coils and the normal sequence: protected C-hook unload to fixed receiving saddle, then Coil AGV transfer to PR-003. All engineering values remain TBC.
- Retained builder authority v438 remains unchanged.

## 2026-08-07 — Inbound presentation reviews v504-v505

- v504 retained the correct v503 cab yaw and reduced the extreme review lighting. Its fresh fixed-camera image remains visually rejected: the yellow crane still dominates and the receiving saddle/Coil AGV handoff is not sufficiently legible.
- v505 tested a side-on process view. It proves the open curtain-sided trailer contains exactly four coils, but crops the cab and exposes a deeper layout problem: compressed candidate geometry lets the crane guarding obscure the receiving and AGV handoff sequence.
- Decision: stop camera-only iteration. The next additive source successor must rebuild the crane/saddle/AGV presentation spacing and silhouettes while retaining the verified cab yaw, exact four-coil count and visual/TBC status.
- Evidence and decision are recorded in `Saved/Audits/PressShopIntegration/inbound_presentation_decision_v505.json`. Neither map is promoted and retained builder authority v438 remains unchanged.

## 2026-08-08 — Inbound Modular_v004 additive source

- Built `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v004` directly from retained source v003 without changing v001-v003.
- v004 removes the visually blocking near-face crane fence, retains protected side/far boundaries and introduces an open entry header with bollards. It replaces the weak saddle silhouette with a deeper rubber-lined V cradle, hydraulic-style base, end stops and locating pins. The AGV handoff now has a separate low-profile datum, guide rails, four locators and scanner housings.
- The preview spacing separates the crane/saddle operation from the AGV handoff and preserves the exact four-coil open trailer and European cab-over source.
- Blender 5.2 generated the `.blend`, nine FBXs, manifest and 1920x1080 source render successfully. This is retained source-only evidence with all engineering values TBC; it is not imported, integrated or promoted.
- Next gate: isolated Unreal v004 import with scale/bounds/body setup/material checks, followed by a fresh review combining the retained bridge/trolley/powered C-hook and Coil AGV. Retained builder authority v438 remains untouched.

## 2026-08-08 — Inbound v004 Unreal intake v506 / visual review v507

- Imported all nine Modular_v004 FBXs at scale 1.0 into `/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v004`. Bounds, controlled material-slot resolution and body setup passed for every asset in `Saved/Audits/PressShopIntegration/inbound_modular_import_v506.json`. Import emitted the known FBX smoothing-group warnings; no asset was promoted.
- Built fresh isolated `/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v507` with the retained bridge/trolley/powered C-hook and Coil AGV assets. The new receiving saddle is visibly better and the exact four-coil trailer/correct cab orientation remain intact.
- Visual decision: **rejected for promotion**. The Coil AGV/handoff is not readable in the fixed view, crane presentation remains crude/dominant and installed factory finish is below the Pro reference. See `Saved/Audits/PressShopIntegration/inbound_modular_visual_decision_v507.json`.
- Retain Modular_v004 and Candidate_v004 as source/technical evidence only. Retained builder authority v438 remains unchanged.

## 2026-08-08 — Inbound operational-readability review v508

- Built fresh isolated `/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryOperationalReadability_v508` using Candidate_v004, the retained Coil AGV, retained master coil and powered C-hook.
- v508 preserves the correct upright cab yaw and exact four-coil trailer, but is **rejected for promotion**: the loaded AGV is hidden behind the trailer, the crane remains schematic and the trailer coils are too dark to read as wrapped steel.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v508/inbound_operational_readability.png`; audit: `Saved/Audits/PressShopIntegration/inbound_operational_readability_decision_v508.json`.
- Do not integrate this view into v438. Create a fresh successor with an unobstructed AGV handoff lane, corrected coil materials and stronger installed crane/C-hook presentation.

## 2026-08-08 — Inbound readability reviews v509-v511

- Fresh isolated v509-v511 retain correct cab yaw, exact four trailer coils and the Modular_v004 saddle/handoff work. v509 improves coil wrap; v510 relocates the loaded Coil AGV; v511 proves it from the AGV side.
- Decision: retain v511 as **layout evidence only**, not release art. Its loaded Coil AGV is visible, but the wide presentation remains too dark and the crane/C-hook is too schematic. v509 and v510 are rejected.
- Audit: `Saved/Audits/PressShopIntegration/inbound_operational_readability_decision_v509_v511.json`. Retained builder authority v438 remains unchanged.
- Next successor must use production factory lighting and higher-fidelity installed crane/C-hook modules on the proven AGV-side layout before any v438 integration child is allowed.

## 2026-08-08 — Inbound installed-cell reviews v512-v513

- v512 establishes a usable production-lighting direction and clearly shows the four-coil trailer and loaded Coil AGV. It is retained as lighting/layout evidence only, not promoted.
- v513 adds generic runway/end-truck modules and fails visually: the parts float and the rear wall blocks the process. Reject v513 and do not use it as an integration parent.
- Asset audit confirms the powered C-hook v035 and Coil AGV v001 are already strong in their dedicated source renders. The missing asset is a coherent installed inbound crane bridge/runway/support module.
- Decision: `Saved/Audits/PressShopIntegration/inbound_installed_cell_decision_v512_v513.json`. Retained builder authority v438 remains unchanged.

## 2026-08-08 — Purpose-built inbound installed crane source v001

- Added `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/Candidate_v001` as additive Blender 5.2 source, based on the four-sheet inbound Pro reference pack. All engineering values remain TBC and the candidate is not promoted.
- Exported separate static runway/support and moving double-girder bridge FBXs so Unreal can retain independent bridge, trolley, hoist and powered C-hook motion contracts.
- Corrected a joined-object origin offset found in the first render; the regenerated proof now places the bridge on both runway rails and keeps the powered C-hook/coil inside the crane bay.
- The retained Powered C-hook Candidate_v035, Coil AGV Candidate_v001 and MasterCoil Candidate_v005 remain authoritative reusable modules. Next gate is an isolated Unreal import/bounds/material review and fixed process-camera validation. v438 remains untouched.

## 2026-08-08 — Inbound installed crane Unreal reviews v514-v518

- v514 imported the purpose-built static runway/support and moving bridge at scale 1.0. Bounds, material slots and collision body setup passed; see `Saved/Audits/PressShopIntegration/inbound_installed_crane_import_v514.json`.
- v517 is the strongest installed structure/material proof: coherent runway, bridge, service rails and clear loaded Coil AGV. It remains evidence only because the columns mask the C-hook transfer in the fixed view.
- Reject v518 as a presentation view: it proves crane-bay clearance but hides the four-coil lorry and therefore fails the complete lorry → C-hook → saddle → AGV narrative.
- v515/v516 were tooling-path failures only and produced no promotable successor. Decision: `Saved/Audits/PressShopIntegration/inbound_installed_crane_decision_v514_v518.json`. v438 remains untouched.

## 2026-08-08 — Inbound linear-layout reviews v519-v521

- v519 confirmed that the inherited end-on layout, rather than the camera alone, prevented the complete inbound process from reading clearly.
- v520 rotated/repositioned the isolated process to the Pro reference's linear layout: lorry/four-coil trailer → installed crane/C-hook → fixed receiving saddle → loaded Coil AGV. Retain these transforms as layout evidence.
- v521 provides the opposite fixed view and exposes every major asset, but the isolated black-background stage and apparent on-screen flow remain below installed-factory release quality. Do not promote v519-v521.
- Decision: `Saved/Audits/PressShopIntegration/inbound_linear_layout_decision_v519_v521.json`. Next gate is a fresh hall-context validation child with floor routes, safety boundaries, signage, process-overview camera and crane-hero camera. v438 remains unchanged.

## 2026-08-08 — Inbound installed-hall validation v522-v523

- Built fresh isolated v522/v523 from retained v520/v521 process geometry; no accepted or immutable map was overwritten. Builder authority v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Reject v522 for low roof, clipped exposure and unclear composition. Retain v523 as layout/hall-context evidence only: it visually contains four trailer coils, installed crane runway/bridge, powered C-hook with separate carried coil, fixed saddle and loaded Coil AGV.
- v523 still fails release visual quality because the cab is cropped and the hall, dock, safety, signage and control detail are below the owner Pro pack. It is not promoted and proves no runtime gate.
- Decision and evidence: `Saved/Audits/PressShopIntegration/inbound_hall_context_decision_v522_v523.json` and `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v523/`.

## 2026-08-08 — Coherent four-coil lorry intake / v527-v528 decision

- Added `SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryAssembly_v001` from retained Modular_v005. It preserves the European cab-over and exactly four restrained trailer coils in one coherent parked-state FBX while retaining the underlying modular sources.
- Unreal technical intake passes at `/Game/LineBoss/IndustrialKit/InboundCoilDelivery/LorryAssemblyCandidate_v001/SM_CA_MW_Inbound_LorryFourCoil_v001`: 270 x 1468.75 x 381 cm, nine slots and body setup. The smoothing-group warning remains a release cleanup item.
- v527 and v528 are visually rejected and never promotion parents. v527 proves independent cab/trailer origins caused the detachment; v528 fixes the vehicle but overlaps it with the protected crane cell and obscures the hook envelope. Retain only the asset and layout evidence. Audit: `Saved/Audits/PressShopIntegration/inbound_coherent_lorry_decision_v527_v528.json`.
- Next: recompose the owner-sheet sequence with the complete docked lorry upstream, an empty protected crane operating envelope, fixed receiving saddle and separate Coil AGV handoff downstream. All engineering values remain TBC; v438 remains byte-identical.

## 2026-08-08 — Inbound owner-sequence layout retention v529-v532

- v529-v530 separated the coherent lorry from the protected crane cell; v531 proved the opposite aisle was hidden by the temporary far wall. The read-only actor audit is `Saved/Audits/PressShopIntegration/inbound_hall_actor_audit_v531.json`.
- Retain v532 only as authoritative layout/camera evidence. A cutaway child removes the temporary roof/far wall but keeps beams and columns, proving the owner sequence left-to-right: four-coil lorry, protected powered C-hook crane cell, fixed saddle and separate loaded Coil AGV.
- v532 is not release art and is not a promotion parent. Installed hall/dock fidelity, PBR lighting/materials, signage/safety detail, FBX smoothing cleanup, direct-v438 integration and full technical gates remain open. Decision: `Saved/Audits/PressShopIntegration/inbound_owner_sequence_retention_v529_v532.json`.

## 2026-08-08 — Inbound lorry smoothing cleanup v533

- Rebuilt `LorryAssembly_v001` with explicit FBX face smoothing and reimported the existing isolated candidate. Unreal completed with zero warnings/errors; bounds remain 270 x 1468.75 x 381 cm, with nine material slots and body setup.
- Fresh v532 process-overview and crane-hero captures after reimport preserve the four-coil lorry → protected crane/C-hook → fixed saddle → loaded Coil AGV read. The smoothing release-cleanup item is closed.
- This does not promote v532 or authorize v438 integration. Hall architecture, PBR, lighting, dock controls/signage and all runtime/collision/navigation/save/authority gates remain open. Audit: `Saved/Audits/PressShopIntegration/inbound_lorry_assembly_import_v533.json`.

## 2026-08-08 — Inbound installed-context reviews v534-v535

- Built isolated v534/v535 from retained v532 without touching accepted authority. The successor replaces the black review void with a light factory wall/window band, sealed-grey floor language, structural columns, high-bay lighting and aisle-facing process signs.
- v534 is rejected as final visual evidence. v535 fixes sign direction and improves equipment/coil readability; retain only its environment and lighting direction.
- v535 remains below release fidelity because its hall backdrop is still validation geometry. It is not promoted and proves no runtime gate. Decision: `Saved/Audits/PressShopIntegration/inbound_release_context_decision_v534_v535.json`.

## 2026-08-08 — Inbound signage/control refinement v549-v551

- ProPack v20260807 is now the visual authority for the inbound sequence: four-coil lorry → protected powered C-hook crane cell → fixed receiving saddle → separate Coil AGV handoff toward PR-003; all engineering values are TBC.
- v550's signs/control were useful, but its oversized boundary stripes were rejected. Isolated v551 removes them, improves fixed-camera scale and sign legibility, and retains the corrected bright wrapped-steel treatment on exactly four trailer coils.
- Retain v551 only as the strongest isolated visual candidate. It is not promoted or merged into v438 and does not prove runtime/collision/navigation/save/authority. Audit: `Saved/Audits/PressShopIntegration/inbound_signage_controls_decision_v549_v551.json`.

## 2026-08-08 — Inbound close-detail diagnostic v552

- Camera-only v552 adds dock and handoff close-ups without altering v551 process geometry. All four captures passed and confirm the imported dock/restraint, controls, scanner, fixed saddle and separate Coil AGV modules exist in the intended order.
- Retain v552 as diagnostic evidence only. The close-ups expose insufficient dock mechanical/PBR fidelity; do not promote it or use it as a geometry parent. v551 remains the strongest isolated visual parent.
- Audit: `Saved/Audits/PressShopIntegration/inbound_detail_camera_decision_v552.json`. Immutable v438 remains unchanged.

## 2026-08-08 — Blender dock architecture v002 / installed review v553-v554

- Added source-only `DockArchitecture_v002` from the retained Blender generator. It preserves v001 and adds 133-module close-detail treatment for the leveller, tubular guides/anchors, bumpers, powered restraint, scanner/traffic/control hardware and guarded waiting zone. Engineering values remain TBC.
- v553 isolated Unreal intake passes at 1240 x 657 x 655 cm, eight material slots and body setup. v554 installs the asset in a direct v551 visual child and passes overview, crane, dock-detail and handoff-detail captures.
- Retain the source/isolated Unreal candidate, but do not promote or merge v554: the mechanical silhouette is improved, while close-range material and model density still miss release fidelity. v551 remains the strongest visual parent. Decision: `Saved/Audits/PressShopIntegration/inbound_dock_architecture_decision_v553_v554.json`.

## 2026-08-08 — Inbound dock PBR audit/binding v555-v557

- v555 audits eight named dock slots; v556 creates isolated DockArchitectureCandidate_v003 and maps them to the existing controlled Cairnwell inbound PBR set without changing v002 geometry, bounds or body setup.
- v557 passes four fresh fixed-camera captures and improves material separation without regressing coil brightness or process order. Retain v557 as the strongest isolated inbound visual candidate for further work.
- Do not promote or merge v557. The hall context, lorry and close-range surface/model density remain below release quality; all gameplay/technical gates remain open. Decision: `Saved/Audits/PressShopIntegration/inbound_dock_pbr_decision_v555_v557.json`. v438 is unchanged.

## 2026-08-08 — Inbound lorry identity refinement v558

- Direct-v557 child v558 adds a restrained Cairnwell-green identity rail and readable `CAIRNWELL AUTOMOTIVE | INBOUND COILS` text to the coherent cab-over lorry.
- Four fresh fixed-camera captures pass. Exactly four bright cylindrical coils remain visible, and the label does not obscure the open trailer, restraints or lorry → protected C-hook cell → fixed saddle → separate Coil AGV sequence.
- Retain v558 as the strongest isolated inbound visual candidate. Do not promote or integrate it yet: release-grade close geometry/surfaces and all technical gates remain open. Decision: `Saved/Audits/PressShopIntegration/inbound_lorry_identity_decision_v558.json`.

## 2026-08-08 — Detailed inbound lorry successor v559-v561

- Added source-only `LorryAssembly_v002` as an additive reconstruction of the retained coherent four-coil vehicle. It preserves the exact load and adds cab-over glazing/fascia, mirrors, access steps, chassis/service tanks, axle/wheel detail, open trailer rails/uprights, landing legs and rear underrun hardware.
- v559 isolated import passes at 295 x 1743.75 x 381 cm with 17 named material slots and body setup. v560 maps all slots to the controlled inbound PBR library and keeps only the original coil-steel slot on the approved bright-wrap material.
- v561 passes four fresh fixed-camera captures and is retained as the strongest isolated inbound visual candidate. Do not promote or merge it until the protected crane/dock enclosure reaches matching quality and all technical gates pass. Decision: `Saved/Audits/PressShopIntegration/inbound_detailed_lorry_decision_v559_v561.json`.

## 2026-08-08 — Protected enclosure/crane PBR decisions v562-v567

- v562 found five raw imported enclosure slots. v563 maps them to controlled inbound PBR assets; v564 passes all four fixed-camera captures and materially improves yellow guarding, charcoal structure, green identity/control surfaces, red stops and sensor glass. Retain v564 as the strongest isolated inbound visual parent.
- v565 audited the static runway, moving bridge, trolley, hoist and retained powered C-hook. v566 creates controlled-PBR duplicates for the runway and moving bridge; v567 passes captures but is visually neutral relative to v564.
- Retain the v566 crane assets for future integration, but do not use v567 as a visual parent merely because it is newer. Neither comparison is promoted or merged. Decision: `Saved/Audits/PressShopIntegration/inbound_enclosure_crane_pbr_decision_v562_v567.json`.
## 2026-08-08 - direct-v438 inbound integration v568-v571

- Rejected v568 because the new inbound sequence crossed the inherited x=-11000 cm west wall. No accepted map was overwritten; the protected v438 hash remained unchanged.
- Retained, unpromoted v570 is a fresh direct child of v438 with a deliberate 5000 cm west receiving-bay expansion and the retained four-coil lorry -> protected dock/crane/C-hook -> fixed saddle -> AGV handoff presentation installed upstream of PR-003.
- Exact-map authority audit v571 passes: one existing Coil AGV, one lift deck, one in-transfer coil, one Coil AGV controller, one Press Shop build authority and thirteen additive inbound visual modules. No duplicate material/vehicle authority was introduced.
- Fresh fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/inbound_direct_v438_v570`. They pass footprint/readability intent but remain too dark for release art. Run lighting refinement and exact navigation/collision/PIE/runtime/save gates before any promotion.

## 2026-08-08 - inbound functional integration and strongest retained candidate v577-v601

- Rejected v575/v576 safely; neither is a valid parent. v575 hit an Unreal-Python helper mismatch, while v576 correctly failed storage-footprint validation.
- `LBFactoryTransportLink` and `LBInboundDeliveryController` now persist installed scenario references. Native build and whole-shop campaign round-trip pass. v577 adds one hidden inbound dock authority (`INBOUND-001`), one 12-position PR-003 bare-coil storage zone (`SZ-COIL-PR003`), one transport link and one inbound controller, reusing the existing single Coil AGV controller and retained presentation assets.
- v578 reload audit and v579 exact-map PIE pass. The verified cycle dispatches one identified coil, stores it at PR-003, records one delivery and returns the AGV to ready/reload state.
- v586 is the retained technical navigation parent. v591 proves intentional protected-handoff segregation, and exact-map v592/v593/v594/v595 pass whole navigation, aisle collision, functional cycle and authority/hash gates.
- Reject v596 visually because of overexposure and an above-roof overview. Retain unpromoted `/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597` as the strongest current candidate. It adds restrained industrial lighting and fixed interior cameras without changing process, authority or navigation transforms.
- v597 evidence: `inbound_exact_authority_v601.json` PASS; `press_shop_inbound_whole_nav_pie_v598.json` PASS; `press_shop_inbound_aisle_collision_pie_v599.json` PASS; `inbound_functional_cycle_pie_v600.json` PASS. Fixed renders: `Saved/ValidationScreenshots/PressShopIntegration/inbound_release_v597/`.
- Protected v438 is still byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. Continue from v597 only; all engineering values remain TBC and no promotion is yet authorized.

## 2026-08-08 - ordered player-build machine workflow v602-v603

- The management-camera Factory Build menu now uses the live ordered catalogue instead of a hard-coded press-train-only choice. Only currently valid next machine packages are selectable; unavailable downstream machinery is not shown.
- The same grid placement path now covers inbound delivery, PR-004 depackaging, decoiler/feeder, complete press trains, inspection cells and outbound docks. Confirmation uses the existing machine-builder authority, so persistent automatic names and matching AGV/roller/panel-transfer links are created together or the placement rolls back.
- Generic machine footprints receive a protected-envelope obstruction test. Press trains continue to use native press-train identity/envelope authority. Player-drawn storage zones and automatic stand/capacity layout are retained unchanged.
- Verification: native Editor build PASS; five `LineBoss.FactoryBuilder` tests PASS in `Saved/Logs/FactoryBuilder_v602.log`; `LineBoss.Management.AnywhereHUD.ControllerWorkflow` PASS in `Saved/Logs/ManagementBuilder_v603.log`.
- This was code/UI work only. v597 remains the strongest unpromoted integrated visual/runtime candidate and v438 remains protected.

## 2026-08-08 - strict context-filtered build progression v604-v606

- Machine eligibility now validates the complete upstream process chain instead of trusting a single immediately preceding buffer. Finished storage alone cannot bypass inspection; equivalent upstream checks apply to depackaging and press-train placement.
- `GetAvailableStorageTypes()` supplies the management HUD with context-valid storage choices. No storage is shown before inbound. Production buffers unlock only after their feeding process exists, while extra unlocked buffers remain placeable for player-led bottleneck relief. Maintenance, quarantine and scrap unlock at appropriate factory milestones.
- Factory Build controller navigation now uses the dynamic machine-plus-storage list; unavailable downstream choices are absent rather than merely rejected after selection.
- Verification: Editor build PASS; builder 5/5 (`FactoryBuilderProgression_v604.log`), management 1/1 (`ManagementProgression_v605.log`), full native suite 34/34 with zero failures/errors (`LineBossFullProgression_v606.log`). No visual map changed.

## 2026-08-08 - player-built machine floor seating v607

- Generic management-grid placement now converts the traced floor point to the machine's centre datum by adding its authored half-height. This aligns committed collision, preview envelope and visible geometry and prevents half-buried inbound/depack/decoiler/inspection/outbound packages. Press-train placement retains its existing native datum.
- Editor build and all 34 native `LineBoss` tests pass with zero failures/errors (`Saved/Logs/LineBossPlacementDatum_v607.log`). Immutable v438 hash remains exact; no map changed.
## External reference acquisition rule (user-directed, 2026-08-08)

- When retained material is insufficient for release-quality modelling, search online for official manufacturer drawings, CAD/data sheets, manuals, and photographic references before continuing.
- Prefer primary sources; preserve provenance and licensing notes with downloaded references.
- Do not ship restricted or ambiguously licensed manufacturer geometry. Use permitted references to create brand-neutral Cairnwell assets.
- Leave unverified engineering values marked TBC.
## 2026-08-08 — inbound trailer coil identity and Production Line reference

- User correction: every coil carried by the inbound lorry must use the exact retained wrapped packaged-coil presentation already used in PR-003 storage, not a dark/simple substitute. Isolated map `/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616` now carries exactly four independent instances of `/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005`; the simplified imported trailer coils are excluded. The lorry is authored at an approach point and reverses to the dock. Candidate is not promoted pending fresh visual/PIE gates.
- Native `ALBInboundDeliveryController` now supports stable tag discovery at BeginPlay so the modular lorry, four coils, crane, C-hook and saddle can rebind after map reopen/save restore. Compile passed. Existing two inbound delivery automation tests passed before the tag-discovery addition; rerun plus exact-map visual sequence validation remains required.
- A UE 5.8 Save Map workflow briefly touched v597; hash preservation stopped the candidate. The touched package was preserved at `Saved/Audits/PressShopIntegration/forensic_touched_v597_before_restore_20260808.umap`, and v597 was semantically restored from the clean pre-edit v616 snapshot before the successful isolated edit. Do not treat byte hash alone as authority; rerun exact v597 semantic audit before further parenting.
- The installed game `Production Line` may be inspected read-only for exposed data/UI/mod/save structure and gameplay principles only. Never decompile its executable or copy proprietary code/assets. Useful independent ideas: zoomable isometric management view, ordered placement, visible buffers/alerts, auto-routing and compact scheduling. Cairnwell remains original, Unreal-native, realistic, robot/AGV-led, with separate buildings. Research and sales gameplay remain out of scope for now.
## 2026-08-08 — Isolated Meshy press-component intake contract v625

- `SourceAssets/Candidate/PressTrains/Shared/MeshyIsolatedIntake_v625/MESHY_ISOLATED_INTAKE_MANIFEST_v625.json` is the authoritative intake contract for the eleven separately generated press components required for clean Unreal pivots and animation.
- The contract prevents a fixed structure from being fused to a moving or independently placed component and requires original-source preservation, geometry audit, cleaned Blender source, isolated Unreal intake and fresh fixed-camera comparison before integration.
- No existing source, candidate or retained map was replaced. The v624 combined meshes remain unpromoted evidence; Asset02 ram is visually rejected as a moving ram because it resembles another outer press frame. Await the two Pro batches, then validate one S03 before expanding the shared S02-S06 family and trains A-D.

## 2026-08-08 — Lightweight component trial and maintenance spares v627-v628

- Both Pro component reference sheets are preserved under `SourceAssets/Candidate/PressTrains/Shared/MeshyIsolatedIntake_v625/Original/ProReferencePack_v627/`. The 1536x1024 sheet has been losslessly divided into eleven review panels under `Prepared/S03_ComponentPanels_v628/`; `manifest_v628.json` records every crop and SHA-256. This preparation submits no external jobs and spends no credits.
- One deliberately bounded, untextured Meshy Smart Topology trial used 5 credits. Its retained GLB is structurally valid at 245,632 bytes, 12,410 polygons and 7,991 vertices. It preserves the broad press-shell silhouette at more than 99% lower polygon count than the high-density source, but remains a candidate until shape, component separation, pivots, collision and fixed-camera comparison pass. It is not promoted to Unreal.
- Press components are now dual-purpose functional assets: fitted machine modules and placeable maintenance spares. Inventory states are `Available`, `Reserved`, `Fitted`, `Damaged`, `AwaitingRepair` and `Scrapped`. Stored heavy modules require an appropriate rack, die cart, pallet or protected floor stand and may never occupy pedestrian access. The same approved geometry, scale, sockets and materials must be used fitted and stored; no decorative duplicate authority is allowed.
- `SourceAssets/Candidate/PressTrains/Shared/MeshyIsolatedIntake_v625/REUSE_AND_SPARES_SCHEDULE_v629.json` now prevents redundant generation: common press structure, utilities, safety, transfer, scrap, inspection and finishing modules remain reusable across S02-S06 and Trains A-D. The eleven isolated assets are also functional maintenance spares with prescribed storage fixtures. New Asset 11 reference `S03_A11_FlywheelSpokedRotor_Orthographic_v629.png` supersedes the earlier solid-disc interpretation and preserves a separate spoked rotor/shaft inside the reusable fixed housing.
# Factory-wide reusable asset contract v630 (2026-08-08)

- Added `SourceAssets/Shared/FactoryAssetLibrary/FACTORY_WIDE_REUSE_CONTRACT_v630.json` so reuse applies across the whole game, not only the press trains.
- The catalogue covers robot cores/tooling, conveyors and automatic transport links, AGVs/docks/chargers, storage and physical buffers, safety modules, controls/utilities, building/dock modules and press-machine modules.
- Existing functional authorities such as `ULBFactoryConnectionSubsystem`, `ALBFactoryTransportLink` and the reusable coil-AGV cycle remain the basis for automatic connection. Pro sheets, Blender kits and Meshy outputs retain explicit candidate/source status until their own release gates pass.
- Station numbers, train letters, shop identity, colour and wear are instance data/material variants and must not create duplicate geometry. Search the catalogue before any paid generation.

## 2026-08-09 - New inbound asset rebuild and revised AGV planning reference

- The owner directed a clean Press Shop rebuild using only newly approved visual assets, with the inherited map retained only for positional reference. The accepted wider Press Trains A-D remain the downstream target; old press visuals and old S07 unload robots must not return.
- The existing powered C-hook is retained for scale/alignment validation. Do not spend Meshy credits rebuilding it unless the installed unloading-bay review proves a specific defect.
- The user-supplied textured adjustable coil stand was spatially split into 12 independently adjustable objects while preserving its original Meshy UVs and packed textures: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/MeshyAdjustableCoilStand_v20260809_v004/Cairnwell_AdjustableCoilStand_SpatialTexturedSplit_v004.blend`. Direct-open Blender evidence is `Saved/ValidationScreenshots/PressShopIntegration/coil_stand_spatial_split_v004_direct.png`; 12 mesh objects, 2 materials and 5 images loaded correctly. The earlier nearest-surface retexture result is rejected.
- A credit-free lorry successor replaces the temporary orange support bars with eight instances of the approved adjustable stand (two units per wrapped coil). Latest owner-directed fit uses 92.5% of the source stand X/Y footprint, paired centres at Y = +/-0.46 m, an approximately 0.70 m trailer cradle profile and coil base offset 0.35 m above the deck datum. The four coil stations are X = -2.25, 0.75, 3.75 and 6.75 m: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryLoadedWrappedCoils_v20260809_v004/Cairnwell_Lorry_Loaded_WrappedCoils_ApprovedStands_v004.blend`. Review: `.../Review/Lorry_Loaded_ApprovedStandPairs_hero_v004.png`. This remains Blender candidate art pending final owner visual acceptance and Unreal intake.
- A matching 12-position wrapped-coil store has been built as three rows of four, using 24 linked instances of the same approved stand and 12 linked repaired solid wrapped coils. Latest fit uses the same 92.5% X/Y footprint and +/-0.46 m stand-pair centres, retains the approximately 0.61 m floor-stand profile and seats the coil at a 0.10 m base offset so it no longer floats: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/WrappedCoilStorage12_v20260809_v001/Cairnwell_WrappedCoilStorage_12Position_v001.blend`. Review: `.../Review/WrappedCoilStorage_12Position_hero_v001.png`. This remains Blender candidate art pending final owner visual acceptance and Unreal intake.
- Pro produced revised AGV plan `C:/Users/greg_/Downloads/ChatGPT Image Aug 9, 2026, 08_45_47 AM.png`. Retain as **Rev A correction-pending planning evidence**, not coordinate authority. Required corrections: exactly 12 storage positions rather than 20, four physically located AGV charging bays rather than legend-only chargers, one explicit S01 AGV handoff bay for each Train A-D and drawing date 09/08/2026. Final coordinates and route clearances must be validated in the clean Unreal map.
- Later Pro revision `C:/Users/greg_/Downloads/ChatGPT Image Aug 9, 2026, 09_01_40 AM.png` correctly adds the player-built-layout notice and date, but is **rejected as planning authority** because it regresses required counts/placement: only nine visible coil positions plus a duplicate empty storage label, five chargers labelled CS1/CS2/CS2/CS3/CS4, chargers overlapping support rooms and no explicit AGV-S01 handoff A-D bays. Await a corrected sheet proving exactly 12 coil icons (3x4), exactly four accessible pull-off chargers CS1-CS4 with blue-route connections and exactly four S01 handoffs A-D. Preserve all Pro sheets as evidence only; none controls Unreal coordinates.
- No Meshy credits were spent on this Blender validation/recomposition work. The next paid Meshy asset should not be requested until the retained asset catalogue and corrected Pro plan prove a genuine missing release model.
- Retained powered C-hook Candidate_v035 was revalidated against the repaired wrapped coil v003. The repaired coil measures approximately 1.8105 m OD x 1.50 m width with a 0.61 m eye; after applying the powered 90-degree lifting orientation, the long padded carrying arm passes through the centre eye and supports the inner bore as intended. Evidence: `Saved/ValidationScreenshots/PressShopIntegration/retained_chook_wrapped_coil_v035_v003/retained_chook_wrapped_coil_side.png` and `.../retained_chook_wrapped_coil_bore_axis.png`. This confirms no paid C-hook regeneration is currently justified; installed crane motion/clearance validation remains required.
- **Player-build authority (owner reminder, 2026-08-09):** the revised Pro/AGV master plan is an example/reference arrangement, not a permanently pre-populated release map. As in the two factory-management games reviewed with the owner, players must construct and place the production system themselves. New inbound equipment, storage bays/stand pairs, AGV wait points/chargers/routes, preparation cells and wider Press Trains A-D must be catalogue-driven modular packages using the existing management-grid preview, obstruction/clearance checks, ordered progression, persistent automatic naming and automatic transport-link creation. Only genuinely fixed building-shell, road, fire/emergency and structural constraints may be pre-authored. Do not satisfy the rebuild by baking one fixed final layout into the map.
- **Owner replacement decision (2026-08-09):** Coil AGV Candidate_v001 is retained only as functional/envelope reference and must not be used as final visual art. Commission one proper unloaded Cairnwell coil-carrying AGV through a controlled Pro four-view pack and Meshy multi-view generation. The coil must remain a separate asset. Required separable modules are chassis, vertical lift/cradle deck, four wheel/bogie assemblies, safety bumpers and sensor/light modules. Preserve the current approximate 3.61 x 2.22 x 1.18 m vehicle envelope, 80 mm lift contract and 1.80 m OD x 1.50 m wide wrapped-coil interface; payload/certification remain TBC. Validate the textured combined master in Blender, then use the segmented `.blend` only for pivots/hierarchy while retaining the textured geometry/material authority.
- Prepared the no-credit AGV intake package at `SourceAssets/Candidate/PressShop/InboundCoilDelivery/MeshyCoilAGV_v20260809_v001/`. `INTAKE_CONTRACT.md` defines source preservation, Blender views/counts/material gates, repaired-coil and stand fit checks, modular pivots/exports and isolated Unreal/player-build gates. `intake_manifest.json` is awaiting the textured combined and part-segmented `.blend` paths. Do not commission a second generation before auditing the first textured download.
- Player-facing storage wording now matches the wrapped-coil inbound process without changing the legacy serialized enum value used by existing saves. The Control Room catalogue displays `WRAPPED COIL STORAGE`, and depackaging progression requests `PLACE AND CONNECT WRAPPED COIL STORAGE FIRST`. Native Editor build passed; all six `LineBoss.FactoryBuilder` automation tests passed in `Saved/Logs/FactoryBuilder_WrappedCoilWording_20260809.log`.
- **Credit-free AGV player-build infrastructure (2026-08-09):** the factory catalogue now has a separate saved placement authority for AGV charging stations, waiting points, route waypoints and one named S01 handoff for each Press Train A-D. Charging stations auto-name `CS-01` to `CS-04` and a fifth is refused; handoffs auto-name `S01-HANDOFF-A` through `-D` and duplicates are refused. These are modular player placements, not actors baked into the protected map. Placeholder presentation is intentionally replaceable by the approved Meshy AGV/charger art after Blender validation.
- Persistence is wired through `ULBPressShopSaveGame` and the whole-shop campaign controller. Native Editor build PASS; focused infrastructure test PASS in `Saved/Logs/FactoryBuilder_AGVInfrastructure_20260809.log`; all seven `LineBoss.FactoryBuilder` tests PASS in `Saved/Logs/FactoryBuilder_AGVInfrastructureRegression_20260809.log`; whole-shop campaign round-trip PASS in `Saved/Logs/FactoryBuilder_AGVInfrastructureCampaign_20260809.log`.
- Protected `LB_PressShop_BuilderAuthorityCandidate_v438.umap` was not edited and re-hashes exactly to `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. Remaining visual input is still the first proper Meshy coil-AGV textured/segmented `.blend` pair and a corrected Pro reference sheet proving 12 coil positions, exactly four accessible chargers and four A-D handoffs.
- **Meshy coil-AGV first pair rejected (2026-08-09):** both owner downloads are preserved unchanged under `SourceAssets/Candidate/PressShop/InboundCoilDelivery/MeshyCoilAGV_v20260809_v001/Original/`. Blender 5.2 proves the textured master is one mesh/one material/four images, 778,442 vertices, 1,568,665 polygons and approximately 1.900 x 1.900 x 0.788 m. The segmented file is 40 meshes/no materials/no images, 804,530 vertices, 1,611,597 polygons and approximately 2.000 x 2.000 x 0.829 m.
- Reject rather than clean/promote: all four Pro inputs depict nearly the same square face, so the generated AGV is square instead of the required 3.61 x 2.22 x 1.18 m envelope. Its cradle closes into a four-way central pocket rather than two long parallel V rails, and corner sensor/wheel geometry is visibly melted/fused. Retopology or texture repair would spend credits on the wrong structure. Direct renders: `Saved/ValidationScreenshots/PressShopIntegration/meshy_coil_agv_v001_textured_direct.png` and `.../meshy_coil_agv_v001_segmented_direct.png`; numeric audits are beside the intake manifest.
- Corrected no-credit source prompt is `SourceAssets/Candidate/PressShop/InboundCoilDelivery/MeshyCoilAGV_v20260809_v001/CORRECTED_PRO_ORTHOGRAPHIC_PROMPT.md`. It explicitly enforces true side-view 3.61:1.18 and end-view 2.22:1.18 silhouettes and prevents the four-way cradle. Do not spend again until the four corrected images visibly pass those ratios.
- **Clean rebuild asset gate (2026-08-09):** `SourceAssets/Candidate/PressShop/PRESS_SHOP_CLEAN_REBUILD_INTAKE_v20260809.json` is now the authoritative asset-sequence checklist, not a coordinate/layout authority. It covers 17 stages from loaded lorry through PR001-PR010, retained wider Press Trains A-D and S07 unload. It explicitly forbids old block/procedural presses, old S07 robots, old fixed PR001-PR010 visuals, the rejected square AGV and any finished prebuilt release layout.
- Current reusable/new evidence is deliberately narrow: repaired wrapped coil v003 is Blender validated; the spatially split textured stand v004, loaded-lorry v004 and 12-position store v001 remain owner-fit candidates; powered C-hook v035 is retained and bore-fit validated; the corrected AGV remains outstanding. PR001, PR002 and new hero visuals for PR005-PR010 are still missing. PR004 may reuse the retained six-axis arm core but still needs role-specific depack tooling, cradle, waste equipment and guarding.
- The owner-supplied textured/segmented six-axis suction robot pair is preserved under `SourceAssets/Candidate/PressTrains/Shared/MeshyUnloadRobot_v20260809_v001/` and correctly classified as shared S07 unload art, with possible PR004 arm-core reuse after reach validation. Blender audit: textured master 1 mesh/1 material/3 images, 994,983 vertices and 1,990,878 polygons; segmented source 24 meshes/no materials, 1,020,708 vertices and 2,042,191 polygons. Colour separation proves distinct base, major arm sections, wrist/tool groups, cable groups and eight individual suction cups. Retain for credit-free pivot/retopo/material-transfer cleanup; do not regenerate the robot.
- Robot direct evidence: `Saved/ValidationScreenshots/PressShopIntegration/meshy_s07_unload_robot_v001_textured_direct.png` and `.../meshy_s07_unload_robot_v001_segmented_parts_colour.png`. Exact six rotation axes, cup re-seating, role-specific tools, collision, reach and swept envelopes remain open; the source is not promoted.

## 2026-08-09 - whole-floor and walkway paint requirement

- Owner requirement: the clean Press Shop must repaint the complete visible floor and every walkway. Do not retain the inherited unpainted, mismatched or patchwork slab presentation.
- Credit-free presentation authority is `SourceAssets/Candidate/PressShop/FloorPaint_v20260809_v001/PRESS_SHOP_FLOOR_PAINT_SPEC_v001.json`; Blender source is `.../Cairnwell_PressShop_FloorPaint_Preview_v001.blend`, with review render `Saved/ValidationScreenshots/PressShopIntegration/press_shop_floor_paint_preview_v001.png`.
- The approved presentation uses sealed industrial-grey epoxy for the slab; green protected pedestrian/service walkways with yellow edges; white crossings with yellow thresholds; blue AGV lanes and pull-off/charging bays; cyan material-flow arrows; red dashed maintenance boundaries; yellow/charcoal exclusion hatch; and red/white fire keep-clear zones.
- Fixed shell/emergency markings may be authored with the building. AGV routes, handoffs and equipment/service zones must be generated from saved player placements because the Press Shop is player-built, not a fixed pre-populated layout. Paint meshes/decals must have no collision and must not change navigation.
- The Blender semantic preview is accepted as a paint-system sample only. Applying it across a clean Unreal candidate remains pending final equipment positions and the accepted replacement AGV envelope. Protected builder-authority map v438 was not edited.

## 2026-08-09 - S07 unload robot credit-free cleanup v001

- Built `SourceAssets/Candidate/PressTrains/Shared/MeshyUnloadRobot_v20260809_v001/Cleaned_v001/Cairnwell_S07_UnloadRobot_Cleaned_v001.blend` from the preserved 24-part Meshy segmented source. No Meshy call or credits were used and both originals remain unchanged.
- Per-part cleanup reduces the segmented source from 2,042,191 to 466,514 polygons including the small generated gripper structure and review floor (77.16% reduction). The candidate has named assemblies and readable Cairnwell green/charcoal/steel/yellow/rubber review materials.
- Corrected the major segmentation defect: all eight retained suction-cup meshes are now seated beneath a purpose-built two-rail panel gripper connected to the wrist. Review render: `Saved/ValidationScreenshots/PressShopIntegration/meshy_s07_unload_robot_cleaned_v001.png`; audit: `.../Cleaned_v001/cleaned_inspection.json`.
- Six joint-axis markers are deliberately tagged provisional. Do not promote or import as an animated production robot until posed motion proves the exact pivots, a runtime-only collection excludes review objects, collision/reach/swept envelopes pass and installed S07 orientation is validated beside each retained wider press train.
- Runtime separation is now complete at `.../Runtime_v001/Cairnwell_S07_UnloadRobot_RuntimeCandidate_v001.blend`: 29 visual meshes, 466,513 visual polygons and true visual bounds approximately 2.000 x 0.848 x 1.610 m. Review floor/camera/lights are excluded; seven conservative `UCX_` collision-review proxies and the six provisional axis markers are isolated in their own collections. Manifest: `.../Runtime_v001/runtime_manifest.json`. Motion/sweep/reach/LOD/installed-orientation gates remain open.

## 2026-08-09 - saved player-built AGV floor paint presentation

- `ALBFactoryAGVInfrastructure` now creates a separate 1 cm-thick, no-collision, non-navigation floor-marking surface for every saved charger, wait point, route waypoint and S01 handoff A-D. The marking uses approved AGV blue `#2167A5`, follows the validated placement envelope and is recreated through the existing save/restore path rather than baked into a fixed map.
- Native Editor build PASS. All seven `LineBoss.FactoryBuilder` tests PASS in `Saved/Logs/FactoryBuilder_DynamicFloorPaint_20260809.log`, including new assertions for charger-bay paint dimensions, blue semantics and route paint with no collision/navigation effect.
- This is the dynamic player-built portion of the floor system. The complete sealed-grey slab, fixed fire markings and protected shell walkways still belong to the future clean presentation candidate after equipment positions are accepted. Protected v438 was not edited.

## 2026-08-09 - clean-rebuild CR01/MR01 support-fleet review

- Current decision is `SourceAssets/Candidate/PressShop/SUPPORT_FLEET_CLEAN_REBUILD_REVIEW_v20260809.json`: retain the standalone technical/visual authorities for exactly two CR01 cleaning robots and two MR01 maintenance robots with four independent docks; discard all old-map transforms and presentation inheritance.
- CR01 v022/v023 already passes the exact 1520 x 980 x 1120 mm source contract, 30 pivots, 18 sockets, seven collision meshes, UV/material limits and five LOD budgets. Retain it for a fresh clean-map owner comparison; do not regenerate it in Meshy.
- MR01 v022 is visually and technically newer than the old v021 in-map screenshot with white wheels. Its direct Blender evidence has correct dark wheels/materials and a compact raised parked arm. The retained runtime proves straight-reverse docking, corrected six-axis mapping, eight-tool authority, connected 400 mm lift, save/restore, collision and route blocking. Reuse v022, not the superseded old-map presentation.
- Existing four-unit evidence already proves two CR01 plus two MR01 outbound/return missions, campaign persistence and control-room dispatch. Clean-map work must re-prove painted-floor contact, independent dock placement, unobstructed materials, cleaning-head/arm/tool/dock sweeps and four-unit routing. No Meshy credits are justified before that comparison.

## 2026-08-09 - v723/v770 clean-map visual rejection

- Fresh review of the existing v724/v771 screenshots supersedes their capture-pass status with `Saved/Audits/PressShopIntegration/clean_rebuild_visual_rejection_v20260809.json`. Capture success proved only that images were produced; it did not prove visual acceptance.
- `/Game/LineBoss/Developer/Validation/PressShop/LB_PressShop_CleanMeshyTrainsReview_v723` is **VISUAL REJECT / NEVER PARENT**: presses remain squashed, glossy/melted and crowded by inconsistent temporary/legacy-looking modules; the floor is unpainted and S07 is not the cleaned eight-cup candidate.
- `/Game/LineBoss/Maps/LB_PressShop_Trains_InboundVisual_v770` is **VISUAL REJECT / NEVER PARENT**: it shows an isolated gantry on a mostly empty unpainted slab rather than the complete loaded-lorry, storage, preparation and train flow, and its distant trains inherit v723 presentation.
- Preserve both packages and captures as diagnostic evidence only. The successor must start from fixed shell/structure/fire authority plus the new-assets-only gate; neither rejected package may be used as a parent. Protected v438 remains byte-identical.

## 2026-08-09 - fresh clean shell and fixed floor paint v003

- Built a genuinely new, non-legacy 220 x 120 m clean shell at `/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003`; it is a presentation/building base only and is not promoted over builder authority v438.
- The complete slab has sealed industrial-grey paint. Every fixed perimeter pedestrian/service walkway is green with yellow safety edging, and six fixed fire exits have red/white keep-clear panels. No old floor materials, presses, robots or map actors were inherited.
- Balanced-light review captures passed at `Saved/ValidationScreenshots/PressShopIntegration/clean_shell_v20260809_v003/`. Audit: `Saved/Audits/PressShopIntegration/clean_shell_lighting_build_v20260809_v003.json`; capture log contains `LINE_BOSS_CLEAN_SHELL_CAPTURE_V003_PASS`.
- Player-created AGV routes/chargers/waits/handoffs retain their tested dynamic blue paint. Equipment footprints, crossings, maintenance/exclusion zones and internal player-created walkways must be generated from accepted placements rather than baked into this empty reference shell.
- Protected v438 remains byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-09 - S07 posed-joint validation v002 rejected

- Built a non-destructive six-axis hierarchy and conservative home/pick/discharge pose test in `SourceAssets/Candidate/PressTrains/Shared/MeshyUnloadRobot_v20260809_v001/Rigged_v002/Cairnwell_S07_UnloadRobot_RigValidation_v002.blend`.
- The test correctly **fails** production animation: at the modest frame-40 pose, the segmented wrist/tool and upper joint shells visibly separate. The inferred markers from cleanup are not acceptable production pivots.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/meshy_s07_rig_validation_v002.png` and `.../Rigged_v002/rig_validation_manifest_v002.json` (`FAIL_POSED_JOINT_CONTINUITY__STATIC_VISUAL_ONLY`).
- Do not import this robot as animated S07 art or place it beside the trains yet. Preserve the good static visual and eight-cup tool, rebuild joint interfaces/pivots credit-free from the segmented source, then repeat the same three-pose continuity test before cell reach/sweep validation. No Meshy credits were used.

## 2026-08-09 - clean inbound/store Unreal intake v004-v006

- Exported the approved Blender stand as `.../MeshyAdjustableCoilStand_v20260809_v005/SM_CA_MW_AdjustableCoilStand_Approved_v005.fbx` (1.900 x 0.462 x 0.218 m, floor-centre origin) and the approved lorry visual as `.../LorryLoadedWrappedCoils_v20260809_v006/SM_CA_MW_InboundLorry_Approved_v006.fbx` (16.50 x 2.55 x 4.00 m). Coils and stands remain separate gameplay actors. Both exports used zero Meshy credits.
- Built `/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorage_v20260809_v004` from the fresh v003 shell only: exactly one lorry, four independent trailer coils, eight independent trailer stands, 12 independent PR003 coils and 24 independent PR003 stands. Audit: `Saved/Audits/PressShopIntegration/clean_inbound_storage_build_v20260809_v004.json`.
- The initial v004 visual was rejected for grey fallback materials and low/floating fit. Extracted the packed Blender PBR maps, created explicit Unreal base-colour/metal-rough/normal materials, and rebound both imported meshes. Evidence: `.../clean_inbound_pbr_material_repair_v20260809_v005.json` and `.../clean_inbound_material_visibility_v20260809_v006.json`.
- Non-overwriting fit/light successor `/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorageFit_v20260809_v005` seats storage stands at floor Z=0, storage coils at centre Z=112 cm and trailer coils at centre Z=200 cm. Storage stands are now visibly under the coils in `Saved/ValidationScreenshots/PressShopIntegration/clean_inbound_storage_v20260809_v005/storage_12_positions.png`.
- Counts, dimensions and contact are accepted as integration progress, but lorry colour readability remains **VISUAL REVIEW OPEN**: its Meshy atlas is extremely dark under the hall roof and is not yet a final Unreal colour match to the green Blender authority. Do not promote v004/v005 or infer final acceptance from capture success. Protected v438 remains unchanged.
- **Retained-train reconstruction visual gate (2026-08-09):** fresh child `/Game/LineBoss/Maps/LB_PressShop_CleanInboundRetainedTrains_v20260809_v011` reconstructed exactly 181 tagged static actors plus one authority for each isolated A-D donor, with 728 total actors, no rejected whole-shop parent, and corrected S01-west/S07-east process flow. The structural audit passes, but fixed-camera evidence hard-rejects the donor art: all four trains still use oversized plain grey block press bodies and old procedural top geometry mixed with detailed green modules. Preserve v011 only as diagnostic proof; never parent or paint the release layout from it. Rebuild the main press-body/station art from approved newer sources before installing A-D. Decision: `Saved/Audits/PressShopIntegration/clean_retained_trains_visual_rejection_v20260809_v011.json`. No Meshy credits used; protected v438 remains unchanged.
- **User-approved Walker recovery (2026-08-09):** preserved Greg's accepted `Meshy_AI_Cairnwell_S03_Walker_0808080548_texture (1).glb` unchanged and built a credit-free runtime derivative at `SourceAssets/Candidate/PressTrains/Shared/UserApprovedS03Walker_v20260809_v001/Runtime_v001/`. Conservative Blender decimation reduced 1,986,042 to 359,999 triangles (81.87%) while the fresh hero render retains the clean tall proportions, crisp cabinet structure and original pale-green/steel texture. This is approved as the shared static outer press body for S02-S06 only; moving die/ram, transfer beds, console and guarding remain separate gameplay assets. Direct comparison hard-rejects `MeshyStaticPressShell_v642`/v639: it is visibly melted and its 1.9007 x 1.0332 x 1.5721 proportions are deeper and squashed versus the approved Walker's 1.9019 x 0.6106 x 1.8696. Decision audit: `Saved/Audits/PressTrains/approved_walker_vs_melted_shell_decision_v20260809.json`. No Meshy credits used.

## 2026-08-09 - approved modular trains and placement-linked floor paint v015

- Blender authority is `.../NewApprovedAssembly_v20260809_v005/Cairnwell_PressTrain_NewApproved_Prototype_v005.blend`: S01 west, five tall Walker-based S02-S06 stations, six interstage roller beds and S07 east. Separate black/white S02-S06 plaques cover the repeated station identity without changing the accepted texture. Review includes corrected broadside and endpoint renders.
- Exported four reusable textured GLB modules in `.../RuntimeTexturedModules_v015/`: station, roller, S01 and static-review S07. These remain modular player-build parts, not one baked train. No Meshy credits used.
- `/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v015` contains four wider A-D reference trains plus placement-linked green operator walkways, yellow safety edges/equipment footprints, blue AGV loop and handoffs, white zebra crossings, red crane exclusion and yellow coil-storage boundary. Audit: `Saved/Audits/PressShopIntegration/clean_approved_trains_textured_oriented_v20260809_v015.json`.
- v012 is rejected for 100x FBX scale. v013 is rejected diagnostic-only for grey FBX materials and sideways presses. v015 replaces them with textured GLB authorities and a 90-degree press correction; the latest Unreal close capture confirms sensible scale, painted floor and front-facing station envelopes, but final material/lighting readability remains open and v015 is not promoted.
- S07 remains static visual only pending the failed-joint repair. Protected v438 remains byte-identical; zero Meshy credits were spent.

## 2026-08-09 - clean support fleet and lighting review v017-v018

- Clean successor `/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetLit_v20260809_v017` places exactly two retained CR01 cleaning robots, two retained MR01 maintenance robots and four independent v026 docks in a compact south service bank. Each has an independent green/yellow docking berth and remains a player-build reference placement.
- The Blueprint-origin floor error discovered in v016 is repaired from measured actor bounds: all four robot bottoms are within 0.25 cm of slab Z=0. Every robot/dock stays between the Train A safety edge and south AGV trunk; audit `Saved/Audits/PressShopIntegration/clean_approved_trains_fleet_lit_v20260809_v017.json` passes counts, floor contact and route clearance.
- Visual evidence `Saved/ValidationScreenshots/PressShopIntegration/clean_approved_trains_fleet_lit_v20260809_v017/support_fleet_south_floor_contact.png` clearly shows the four retained robots and four docks on painted berths. Runtime arm/tool/brush/drawer/door/dock-contact sweeps remain open before promotion.
- v018 local press-face point lighting is **VISUAL REJECT / NEVER PARENT** because it blows out the press fronts and floor. Resume from v017; decision `Saved/Audits/PressShopIntegration/clean_press_face_lighting_visual_rejection_v20260809_v018.json`.
- No Meshy credits were used; protected v438 remains unchanged.
## 2026-08-09 — full Press Shop floor-paint child v032

- Current review map: `/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032`.
- Parent: clean fleet/navigation v019; protected v438 was not modified.
- v023/v026 were rejected because the duplicated child did not retain the newly spawned paint; v029 proved the correct template workflow but retained doubled inherited route lines. They are evidence only and must not be parents.
- v032 uses the proven `new_level_from_template` workflow, removes 139 inherited partial paint actors and installs one clean 139-actor scheme: 11 connected walkways, 22 edges, 6 AGV surfaces, 12 blue AGV edges, 28 safety boundaries, 56 crossing stripes and 4 crane-exclusion edges.
- Exact map inspection proves all 139 new actors are saved. Fresh review captures are under `Saved/ValidationScreenshots/PressShopIntegration/clean_full_floor_paint_v20260809_v033/`; they show grounded markings, continuous green pedestrian routes, blue AGV circulation and no doubled partial route system.
- Coverage includes unloading, coil storage, coil preparation, trains A-D, support-robot docks, perimeter escape routes and AGV circulation. Meshy credits used: 0.

## 2026-08-09 - corrected loaded-lorry and storage fit v035-v037

- Continue visual/inbound review from `/Game/LineBoss/Maps/LB_PressShop_CleanInboundFlowFit_v20260809_v035`, a non-overwriting child of the clean fully painted v032 map. Protected v438 remains unchanged.
- The four independent trailer coils are centred at Y `-3100, -2700, -2300, -1900 cm` (400 cm pitch) and Z `220 cm`. Their paired independent chocks sit at +/-60 cm from each coil centre; all four loads remain inside the trailer envelope.
- Exact support evidence passes: coil bottom `125 cm`, chock top `132.815 cm`, contact overlap `7.815 cm`, and chock outer width `166.176 cm`. Audit: `Saved/Audits/PressShopIntegration/clean_inbound_trailer_fit_v20260809_v035.json`.
- Valid fixed-camera evidence is `Saved/ValidationScreenshots/PressShopIntegration/clean_inbound_fit_v20260809_v037/lorry_loaded_side.png`, `lorry_loaded_rear_oblique.png` and `storage_overview.png`. The earlier v036 lorry views were outside the wall and are invalid; only its storage overview remains useful corroboration.
- v035 retains 12 grounded storage coils on 24 independent stands. Coils/stands remain modular player-build parts rather than a baked load. No Meshy credits were used.

## 2026-08-09 - clean-map paint collision and runtime navigation v043-v050

- Current runtime-navigation continuation is `/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049`. It inherits the corrected v035 inbound fit, complete v032 paint and clean A-D/support fleet only; protected v438 remains unchanged.
- The v038 native-bootstrap build exposed that all 155 `LB_PAINT_*` actors (139 full-shop markings plus 16 dock markings) had reverted to `BlockAll` after save. Fresh v043 explicitly sets every paint component to `NoCollision`; the structural slab remains `BlockAll`. Audit: `Saved/Audits/PressShopIntegration/clean_paint_collision_nav_repair_v20260809_v043.json`.
- The full 22000 x 12000 x 1000 cm nav volume uses one native `LBPressShopNavigationBootstrap`; do not return to failed v020's unavailable Python `NavigationSystemModuleConfig` approach.
- Live PIE v050 passes all ten tested corridors: CR01-01/02 and MR01-01/02 straight dock exits; south, north, west and east AGV perimeter lanes; and both storage-loop lanes. Evidence: `Saved/Audits/PressShopIntegration/clean_runtime_navigation_pie_v20260809_v050.json`.
- MR01-02's former x=750 cm berth was uniquely blocked by the Train A western obstruction. v049 moves the complete berth (robot, independent dock and four paint pieces) to x=-1250 cm; all other unit positions remain unchanged. Audit: `Saved/Audits/PressShopIntegration/clean_mr01_02_egress_repair_v20260809_v049.json`.
- Fresh v051 support-fleet capture proves four separated berths and no visible overlap, but the unlit/roof-hidden evidence is too dark for final material approval. Retain it only as placement evidence; final lit robot material and motion/tool/dock-contact gates remain open. No Meshy credits were used.
- PR005 Candidate_v002 remains source-only/legacy-style and is forbidden from clean-map placement by `PRESS_SHOP_CLEAN_REBUILD_INTAKE_v20260809.json`; it is not a substitute for the still-missing newly approved PR005 visual.

## 2026-08-09 - clean support-fleet runtime v056-v062

- Current clean runtime continuation is `/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059`, a fresh v056 child of retained clean-map v049. Protected v438 remains unchanged.
- The old fleet controller's fixed-map coordinates are now optional. `LBPressShopSupportFleetController` retains its legacy default but exposes `bUseInstalledActorTransforms`, clean service-aisle Y and standby point for the reference/player-built layout. The clean controller reads berth roots from the installed actors and builds clean reference routes; future saved player-authored route assets remain the final player-build authority.
- v056 explicitly configures four durable runtime identities rather than relying on labels/tags: `LB-CR01-01`, `LB-CR01-02`, `LB-MR01-01`, `LB-MR01-02`. This fixes the earlier anonymous-unit collapse. Build audit: `Saved/Audits/PressShopIntegration/clean_support_fleet_runtime_build_v20260809_v056.json`.
- The runtime sweep now ignores only the assigned unit's own tagged standalone visual dock inside the 3.5 m dock approach envelope; every other dock, robot and machine remains a blocker. v059 tags exactly the structural slab as `LB.Environment.Floor.SealedConcrete`, allowing horizontal motion sweeps to distinguish floor contact from obstacles. Audit: `Saved/Audits/PressShopIntegration/clean_floor_runtime_authority_v20260809_v059.json`.
- Live PIE v060 passes commissioning, certification, automatic return configuration, sequential dispatch to `(0,-3500)` and exact return to each correct dock for all four units. Standby errors are 5.03-9.99 cm and return errors 5.13-5.15 cm. Evidence: `Saved/Audits/PressShopIntegration/clean_support_fleet_runtime_pie_v20260809_v060.json`.
- C++ editor build passes. All four `LineBoss.SupportRobots` automation tests pass in `Saved/Logs/CleanSupportRobotRegression_v061.log`; whole-shop campaign round-trip passes in `Saved/Logs/CleanSupportFleetCampaignRegression_v062.log`.
- This closes clean-layout fleet identities, commissioning, dispatch/return, assigned-dock collision and campaign regression. Final lit material presentation remains a visual gate; no Meshy credits were used.

## 2026-08-09 - floor and walkway finish requirement confirmed

- The user confirmed that the whole press-shop floor and every walkway must be painted; isolated route markings on bare/default floor are not acceptable.
- The clean continuation v059 already inherits the complete v032 scheme: sealed-concrete main slab, continuous green pedestrian walkways, yellow walkway edges and safety boundaries, blue AGV lanes, protected crossings, crane-exclusion markings, inbound/storage/preparation coverage, all four press-train aisles and support-fleet dock access.
- Keep all 155 `LB_PAINT_*` actors `NoCollision` and retain the structural floor as the collision/nav authority. Any later layout widening or player-build movement must regenerate/extend the painted coverage rather than leaving unpainted patches.
- Final approval requires fresh lit captures from the current continuation map; the earlier dark v051 placement capture is not colour/material evidence. Meshy credits required: 0.

### Lit paint review v064

- Fresh actual-map lit captures now pass the whole-floor/walkway presentation gate for current continuation v059: `Saved/ValidationScreenshots/PressShopIntegration/clean_lit_floor_walkways_v20260809_v064/`.
- Evidence covers the full overhead, inbound/storage, trains A-D and south support-fleet walkway. Audit: `Saved/Audits/PressShopIntegration/clean_lit_floor_walkways_capture_v20260809_v064.json`.
- The rejected v063 pass was overexposed and is not approval evidence. v064 used transient review lights only and did not save any lighting or actor changes into the map.
- Paint coverage and colours pass. AGV lane width remains provisional until the accepted replacement coil-AGV envelope exists; preparation footprints remain provisional until new PR001/PR002/PR004/PR005 visuals are approved.

## 2026-08-09 - support-fleet visual dock-contact correction v069-v071

- Continue clean runtime/visual work from `/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069`, a fresh child of v059. Protected v438 remains unchanged.
- Lit closeups v067 plus the alternate MR01-01 angle v068 prove both CR01 cleaning units and both MR01 maintenance units are grounded, use their intended materials and retain distinct cleaning/maintenance tooling. v065 was rejected as overexposed; v066 was incomplete because the MR01-01 camera was occluded.
- Review exposed a real presentation defect: every standalone visual dock face was 122.5-124 cm behind its parked robot. v069 moves only the four static visual docks forward 100 cm, leaving robot roots, native service-dock runtime targets, paint bays, controller and routes unchanged. Resulting visual service gaps are 24 cm for CR01 and 22.5 cm for MR01. Build audit: `Saved/Audits/PressShopIntegration/clean_support_visual_dock_contact_fix_v20260809_v069.json`.
- Live PIE v070 again passes commissioning, sequential dispatch to standby and exact return to the correct dock for all four units; return errors remain 5.03-5.15 cm and failures are empty. Audit: `Saved/Audits/PressShopIntegration/clean_support_fleet_dock_contact_runtime_pie_v20260809_v070.json`.
- Fresh lit v071 overview passes final robot grounding, materials, berth separation and visual dock alignment. Evidence: `Saved/ValidationScreenshots/PressShopIntegration/clean_support_dock_contact_v20260809_v071/support_fleet_four_docks_contact_lit.png` and matching v071 audit. No Meshy credits used.

## 2026-08-09 - completion audit v072

- Requirement-by-requirement audit: `Saved/Audits/PressShopIntegration/PRESS_SHOP_CLEAN_REBUILD_COMPLETION_AUDIT_v20260809_v072.md`.
- The objective is not complete and promotion remains forbidden. Proved areas are the clean lineage/protected-map invariant, corrected loaded-lorry fit, 12-position storage, four wider train rows/reference placement, whole-floor paint/nav corridors and the complete four-unit support fleet.
- Missing newly approved packages remain: replacement elongated coil AGV; PR001; PR002; PR004 tooling/cradle/guarding; PR005; PR007; PR006; PR008; PR009; PR010; final moving press assemblies; and final cleaned S07 runtime replacement/integration.
- `PRESS_SHOP_CLEAN_REBUILD_INTAKE_v20260809.json` was refreshed with current v035/v064/v069-v071 evidence while retaining every missing/rejected gate. No legacy preparation visual was promoted.

## 2026-08-09 - S07 user robot Blender-first repair v073-v785

- v073 was a technical clean-map experiment only: it removed the four static S07 placeholders and installed four six-part user-v776 hierarchies. Lit v074 rejected it because the source vacuum frame and cups were visibly detached and laid out between the arm and rollers. Never continue from v073; current clean map remains v069.
- Blender v783 reseated the entire original vacuum-tool group upward into the wrist. v784 added a manufactured two-rail, three-crossbar spreader and wrist adapter while retaining the original cups. v785 added eight explicit cup stems so the pickup system no longer reads as unsupported loose pieces.
- Approved Blender intake candidate: `SourceAssets/Candidate/PressTrains/Shared/S07UnloadRobotUserRuntime_v785/Cairnwell_S07_UnloadRobot_ConnectedVacuumTool_v785.blend` with GLB alongside it and review render `Review/S07_UnloadRobot_ConnectedVacuumTool_v785.png`.
- Audit: workspace `Saved/Audits/PressTrains/s07_connected_vacuum_tool_v785.json`. Status passes Blender visual intake only; fresh Unreal import, hierarchy/motion/collision tests and clean v069-child placement remain required. Meshy credits used: 0.

## 2026-08-09 - connected S07 Unreal replacement v787-v795

- Current clean continuation is now `/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791`, a fresh child of painted/runtime-approved v069. It removes exactly the four static S07 placeholders and installs four six-part textured robot hierarchies. Protected v438 remains byte-identical.
- Blender v787 preserves the approved v785 geometry but uses short unique component names (`S07_Base`, `S07_Turn`, `S07_Lower`, `S07_Upper`, `S07_Wrist`, `S07_Tool`) so Unreal cannot collapse the two arm meshes. Source: `SourceAssets/Candidate/PressTrains/Shared/S07UnloadRobotUserRuntime_v787/Cairnwell_S07_UnloadRobot_ShortNames_v787.blend` and GLB. No Meshy credits used.
- Fresh Unreal intake v788 passes six unique StaticMeshes, imported textures and two S07 tool material slots. Audit: `Saved/Audits/PressShopIntegration/s07_connected_vacuum_tool_intake_v20260809_v788.json`.
- v791 build audit passes 24 installed actors, exact `Base -> Turn -> Lower -> Upper -> Wrist -> Tool` chains, movable descendants, grounded bounds and zero protected-map change: `Saved/Audits/PressShopIntegration/clean_connected_s07_placement_v20260809_v791.json`.
- Fresh lit v792 passes all four installed robots and the Train A close view; no vacuum frame or cup is detached. Evidence: `Saved/ValidationScreenshots/PressShopIntegration/clean_connected_s07_v20260809_v792/` and matching capture audit.
- Transient v795 motion test rotates Train A's turntable 20 degrees; Lower, Upper, Wrist and Tool each follow exactly 20 degrees, then restore with zero error without saving the posed map. Audit: `Saved/Audits/PressShopIntegration/clean_connected_s07_hierarchy_motion_v20260809_v795.json`.
- v789 and v790 are incomplete script-error children only and must never be used as parents. v073 remains visually rejected. Remaining S07 work is gameplay controller/joint-specific range/collision certification as part of final moving press-train integration, not static-placeholder replacement.

## 2026-08-09 - user coil-AGV Blender cleanup v796-v798

- Direct Blender inspection v796 proves the textured source is one 1,568,665-triangle mesh with four packed 2K maps, while the matching split source contains 40 separate meshes / 1,611,597 triangles but no materials or images. Both originals remain untouched. Audit: workspace `Saved/Audits/PressShopIntegration/coil_agv_user_pair_inspection_v796.json`.
- Credit-free v797 retains all 40 segments, grounds the assembly, reduces it to 501,048 triangles, adds whole-vehicle/lift/payload authoring roots and changes the nearly square 2.0 x 2.0 m source into a provisional 2.8 x 1.7 x 0.9 m elongated envelope. The atlas transfer was visually rejected because the split source has no usable UV/material binding.
- v798 replaces the failed atlas transfer with clean procedural Cairnwell factory paint: green bodywork, dark bumpers/lower chassis, worked-steel coil cradle and yellow corner protection. Blender/GLB/review render: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v798/`; audit `Saved/Audits/PressShopIntegration/coil_agv_segmented_factory_paint_v798.json`.
- v798 is a review candidate only. Do not import it into the clean map until the owner approves the elongated proportions/paint and the 40 segments are classified into chassis, drive/corner equipment and moving coil-lift roles. Meshy credits used: 0.
- Blender v799 now classifies 6 central cradle/deck meshes as the coil lift and 34 meshes as fixed chassis/corner equipment. A transient 180 mm raised pose cleanly moves the full steel cradle while the chassis remains fixed; the saved Blender master stays neutral. Candidate: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v799/`; neutral/raised renders are under `Review/`; audit `Saved/Audits/PressShopIntegration/coil_agv_lift_classification_v799.json`. Owner visual confirmation, coil-fit/load test, collision proxies and Unreal runtime import remain open.
- Loaded-fit v800 is rejected: inherited payload parenting placed the coil bottom at 69.7 mm, visibly intersecting the AGV body. Never use v800 as a fit authority.
- Corrected Blender v801 seats the approved repaired wrapped coil with its axis across the vehicle width and bottom at 560 mm. The 1.65 x 1.15 x 1.65 m coil remains contained with 574 mm minimum longitudinal and 269 mm minimum lateral clearance per side and is parented to `AGV_COIL_PAYLOAD_ROOT` under the classified lift. Candidate/render: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v801/`; audit `Saved/Audits/PressShopIntegration/coil_agv_loaded_contact_corrected_v801.json`. Owner appearance approval and collision/route-envelope gates remain open; no Unreal import yet and no Meshy credits used.
- Blender runtime-prep v802 adds three independent proxies: 2.70 x 1.58 x 0.60 m blocking chassis, 2.00 x 1.18 x 0.24 m moving lift and a 0.825 m-radius / 1.15 m-wide optional payload-query cylinder. The raised lift clears the chassis proxy by 160 mm. Route authority from the 2.8 x 1.7 m visual envelope plus 300 mm safety margin is: 2.3 m minimum straight lane, 3.4 x 2.3 m charger/handoff bay and 1.938 m minimum swept turn radius. Candidate: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v802/`; audit `Saved/Audits/PressShopIntegration/coil_agv_runtime_collision_envelope_v802.json`. Unreal import remains gated on owner appearance approval.

## 2026-08-09 v803 continuation — floor/AGV envelope and machinery authority

- Current clean continuation remains `/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791`; this audit made no map changes.
- Whole-floor and all-walkway paint remains inherited and visually passed. Read-only audit `Saved/Audits/PressShopIntegration/clean_agv_paint_envelope_v20260809_v803.json` measures main AGV surfaces at 5.2 m and storage-loop surfaces at 4.2 m, both above the provisional loaded-AGV 2.3 m straight-lane requirement.
- Charger and S01 handoff bay markings remain unfrozen until the owner approves v802. Provisional bay authority is 3.4 x 2.3 m and swept turn radius is 1.938 m.
- The remaining-machinery engineering pack is registered under `SourceAssets/Reference/PressShop/RemainingMachineryPack_v1.0/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0`. ZIP SHA256 is `7021A2E5DE71F89306E1AA6CB96D2F6018870404E01F4F83FF27D5F6B2BC399A`; all 28 supplied manifest entries pass.
- Treat that pack as numeric datum, envelope, pivot and module authority for PR008-PR010 and shared train architecture only. Its drawings are not automatically approved finished art.
- Meshy credits used: 0.

## 2026-08-09 PR008 Blender engineering gate v804

- Built a new credit-free Blender engineering blockout from the verified remaining-machinery numeric authority: `SourceAssets/Candidate/PressShop/PR008/EngineeringBlockout_v20260809_v804/Cairnwell_PR008_EngineeringBlockout_v804.blend`.
- It contains all 10 scheduled modules, uses local +Y material flow, records world datum `(-500,-2000,0) cm`, and preserves the fixed `10400 x 5560 x 4490 mm` PR008 planning envelope.
- Thirteen objects are separately authored across the eight required motion groups: feed rolls, edge guides, telescopic support, pre-punch slide, shear blade, discharge rollers, service doors and scrap flap.
- Three Blender review renders and `pr008_engineering_blockout_audit_v804.json` sit beside the source. Safety clearance panels remain in the source hierarchy but are hidden in beauty renders so they do not obscure the machinery.
- Status is engineering blockout only: not owner-approved final art and not authorized for Unreal import. Meshy credits used: 0.

## 2026-08-09 PR001/PR002 authority gate v805

- PR001 owner reference is `SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807/Sheet03_AGVHandoffReceivingSaddle.jpg`, SHA256 `9FF84A3F0260E4920274F3619010C36B68982880649506E7F3EEA06AD1B602BF`. It is presentation/sequence authority only and explicitly marks all dimensions TBC.
- Legacy inbound `Modular_v001-v005` can provide component names and positional scale only; it is not final-art authority.
- PR002 has no new approved visual or dimensional authority. Old-map components establish function only: isolated weigh deck, four load cells, packaged-coil saddle, four-post inspection portal, two vision heads, controls and safety hardware.
- New owner-facing Pro/Meshy prompts, mandatory part splits and Blender gates are in `SourceAssets/Candidate/PressShop/PR001/PR001_NEW_ASSET_GENERATION_BRIEF_v805.md` and `SourceAssets/Candidate/PressShop/PR002/PR002_NEW_ASSET_GENERATION_BRIEF_v805.md`.
- Audit: `Saved/Audits/PressShopIntegration/pr001_pr002_new_asset_authority_v805.json`. Neither station is authorized for Unreal import. Meshy credits used: 0.

## 2026-08-09 PR004 retained-core/new-tooling gate v806

- Reuse boundary is now explicit: retain only the cleaned six-axis arm body/joint appearance from `MeshyUnloadRobot_v20260809_v001/Runtime_v001`. The S07 vacuum panel crossbar, rails and eight cups are forbidden as the PR004 depack tool.
- Legacy `SourceAssets/PR004/FilmDewrapSpindle_v005` is functional reference only. Its named pivot/state contracts may guide the new cell, but its geometry, materials, branding and outer appearance cannot enter the clean rebuild.
- New brief `SourceAssets/Candidate/PressShop/PR004/PR004_NEW_CELL_GENERATION_BRIEF_v806.md` defines 31 separately authored components spanning coil cradle, robot wrist depack tool, spindle/dancer, film transfer, compactor/bale discharge, bare-coil output saddle, guards, scanners and controls.

## 2026-08-09 PR001 credit-free engineering candidate v809

- Built `SourceAssets/Candidate/PressShop/PR001/EngineeringCandidate_v20260809_v809/Cairnwell_PR001_EngineeringCandidate_v809.blend` around the approved repaired wrapped coil, scaled to the 1.65 x 1.15 x 1.65 m gameplay reference envelope.
- All 19 mandatory player-build parts are separately selectable. The cradle, four pins, four sensors, end stops, AGV guides, scanner heads, beacon and HMI remain modular.
- Blender visual QA rejected the first solid scanner wall and replaced it with an open three-piece arch joined as one static portal, preserving coil-bore and vertical C-hook access.
- Six renders and `pr001_engineering_candidate_audit_v809.json` pass. Dimensions remain provisional, owner appearance approval is open, and Unreal import is not authorized.
- Protected builder-authority v438 remains SHA256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. Meshy credits used: 0.

## 2026-08-09 PR002 credit-free engineering candidate v810

- Built `SourceAssets/Candidate/PressShop/PR002/EngineeringCandidate_v20260809_v810/Cairnwell_PR002_EngineeringCandidate_v810.blend` without borrowing forbidden legacy appearance.
- All 20 mandatory player-build parts exist separately: isolated weigh deck, four load cells, saddle, four posts, crossbars, two moving vision heads, cabinet, HMI, beacon and two emergency stops.
- First-render QA caught double-applied parent transforms that displaced the saddle/camera helpers. The hierarchy was corrected and all six views rerendered.
- Blender measurement places the approved packaged-coil bottom at 0.704455 m within the rubber-pad 0.544217-0.895783 m contact envelope; four logical deck load paths remain visible.
- Owner appearance and final dimensions remain open; no Unreal import is authorized. Meshy credits used: 0.

## 2026-08-09 PR004 credit-free engineering layout v811

- Built `SourceAssets/Candidate/PressShop/PR004/EngineeringCandidate_v20260809_v811/Cairnwell_PR004_EngineeringCandidate_v811.blend` with the complete 31-part contract and six consistent Blender views.
- The retained robot is a non-destructive collection instance containing 13 arm body/joint meshes. No `S07_TOOL_*` vacuum crossbar, rail, manifold or cup is present.
- Layout flow is wrapped cradle → new wrist depack tool → expanding spindle/dancer → stripper/transfer gate → film compactor and bale → prepared output saddle.
- The model is engineering/reference geometry for Pro/Meshy views, not approved final art. Exact mover pivots, robot reach poses, owner approval and Unreal intake remain open. Meshy credits used: 0.

## 2026-08-09 PR005 generation-reference pack v812

- Re-rendered unchanged `Candidate_v002` geometry/materials under brighter neutral Blender lighting into `SourceAssets/Candidate/PressShop/PR005/OwnerApprovalPack_v20260809_v812/Review` with hero, front, rear, left, right and top views.
- All nine modular exports exist and match their manifest SHA256; source validation remains PASS. Preserve the 5763 x 10360 x 3550 mm shell and exact coil-in/strip-out/crop-scrap ports as engineering fit authority.
- This does not override the clean-rebuild ban on the blocky legacy appearance. Use v812 only as consistent Pro/Meshy generation reference unless the owner explicitly approves it. New final art and Unreal intake remain open. Meshy credits used: 0.

## 2026-08-09 PR002 owner Pro pack v813

- Archived the owner's five separate PR002 views under `SourceAssets/Reference/PressShop/PR002/ProPack_v20260809_v813` as front, rear, left, right and hero; immutable hashes are in `PR002_PROPACK_MANIFEST_v813.json`.
- Appearance authority now exists. Engineering scale/contact remains governed by v810 and the approved 1.65 x 1.15 x 1.65 m wrapped-coil envelope.
- `PR002_MESHY_JOB_v813.md` excludes the coil, floor and loose bollards from the generated machine, forbids baked text/logos and preserves the 20-part Blender split contract.
- Meshy generation was not started because the signed-in Edge browser was not connected to Codex browser control. Connect Edge under Settings -> Computer use, then upload the five views as one multi-view job. Credits used: 0.

## 2026-08-09 PR004 missing-equipment generation pack v814

- Generated bright hero/front/rear/left/right/top views at `SourceAssets/Candidate/PressShop/PR004/MissingEquipmentProMeshyPack_v20260809_v814/Review` from the v811 engineering layout.
- Hid the retained arm, approved coil and temporary film/wound-film/bale state geometry so Pro/Meshy cannot fuse reusable assets into the new cell art.
- `PR004_MISSING_EQUIPMENT_MANIFEST_v814.json` fixes all six hashes; `PR004_PRO_MESHY_JOB_v814.md` limits generation to the missing cradle, wrist tooling, spindle/dancer, transfer, compactor, output, guards and controls.
- This is generation reference only. Exact pivots/reach, Blender art validation, owner approval and Unreal intake remain open. Meshy credits used: 0.

## 2026-08-09 PR006 dimensioned generation reference v815

- Combined the dimensioned 67-module PR006 source and six hash-verified release-detail modules into `SourceAssets/Candidate/PressShop/PR006/GenerationReference_v20260809_v815/PR006_GenerationReference_v815.blend`.
- Engineering authority retained: 7.50 x 4.52 x 2.97 m, 1.50 m strip, nine lower plus ten upper rolls, four gap-control cylinders and three drives.
- Six bright hashed views and `PR006_PRO_MESHY_JOB_v815.md` are ready. The prompt forbids generic/fused roll banks and preserves the existing mover split.
- Existing geometry is generation/fit reference only, not newly approved final art. Blender art validation, owner approval and Unreal intake remain open. Credits used: 0.

## 2026-08-09 PR007 dimensioned generation reference v816

- Combined the 78-module dimensioned washer/lube source with six hash-verified release-detail modules in `SourceAssets/Candidate/PressShop/PR007/GenerationReference_v20260809_v816/PR007_GenerationReference_v816.blend`.
- Retained authority: 7.35 x 5.44 x 4.03 m, 1.50 m strip, four headers, twenty nozzles, two distinct fluid tanks and separately reusable ten-module strip bridges.
- Six bright hashed views and `PR007_PRO_MESHY_JOB_v816.md` require readable wash/lube circuits, pumps, filters, spray equipment and extraction rather than a generic sealed box.
- Old appearance remains generation/fit reference only. Final art, Blender validation, owner approval and Unreal intake are open. Credits used: 0.
- Mandatory state boundary is packaged wrapped coil in, exact same coil ID as bare coil out to PR005.
- Audit: `Saved/Audits/PressShopIntegration/pr004_retained_core_and_new_tooling_authority_v806.json`. No Unreal import; Meshy credits used: 0.

## 2026-08-09 coil AGV owner approval pack v807

- Render-only approval pack: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v807_ApprovalPack/`; the v802 Blender master was not changed.
- Five Blender views cover unloaded hero, loaded hero, loaded side, loaded top and loaded front. UCX collision/query helpers are hidden from presentation.
- Visual review confirms the 1.65 x 1.15 x 1.65 m wrapped coil is centred across the 2.8 x 1.7 x 0.9 m vehicle, visibly supported by the steel cradle and not floating.
- Audit `coil_agv_owner_approval_pack_v807.json` preserves route authority: 2.3 m lane, 3.4 x 2.3 m charger/handoff bay and 1.938 m swept turn radius.
- Owner appearance approval remains required before Unreal import. Meshy credits used: 0.

## 2026-08-09 loaded lorry owner approval pack v808

- Render-only pack: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryLoadedWrappedCoils_v20260809_v808_ApprovalPack/`; the v004 Blender master and clean Unreal map were not changed.
- Five views cover loaded hero, orthographic left side, rear, top and a close trailer/stand view.
- Visual review shows four evenly spaced wrapped coils, two independent green stands per coil, positive visible support contact and the stand orientation from the trailer rear. The Cairnwell green cab is dark but readable.
- The audit beside the renders retains v035 authority: coil centres separated by 4.0 m in the installed reference, coil centre Z 2.2 m, bottom Z 1.25 m, stand top Z 1.328149 m and 0.078149 m support overlap.
- Explicit owner appearance approval remains open. Meshy credits used: 0.

## 2026-08-09 PR008 detailed Pro-design gate v818

- Re-audited the verified Remaining Machinery Pack and found the authoritative detailed reference at `visuals/SHEET_01_PR008_ENGINEERING_REFERENCE_4K.png`; SHA256 `75F8F0445CE578C2176A4BCF3165DCB16836AAA7F765091D095966443E99C0C2`.
- The v817 six-view Blender output is dimensionally useful but visually rejected for Meshy: it is an envelope of boxes, not a sufficiently readable blanking machine.
- New job `SourceAssets/Candidate/PressShop/PR008/ProDesignPack_v20260809_v818/PR008_PRO_DESIGN_JOB_v818.md` asks Pro for five separate matching views while fixing the 10.40 x 5.56 x 4.49 m envelope, 1.50 m strip, ten modules and eight mover groups.
- Do not spend Meshy credits on PR008 until those detailed views are supplied and visually checked. No Unreal changes; credits used: 0.

## 2026-08-09 PR009 detailed Pro-design gate v819

- Verified authoritative Sheet 02 SHA256 `3D37D19DCBE4BDB5D30D6FA58F7E4C60D2654BAEB36057E6DBF46BB4FFC43008` and inspected its detailed automated blank-stacker hero, module register and motion table.
- Candidate_v002 is retained only for dimensions, pivots, interfaces and player-build part splits; its legacy visible appearance is not approved for the clean map.
- New five-view job: `SourceAssets/Candidate/PressShop/PR009/ProDesignPack_v20260809_v819/PR009_PRO_DESIGN_JOB_v819.md`. It fixes the 7.60 x 5.20 x 4.25 m guarded target, 2.60 x 1.80 m maximum blank, 1.40 m stack height, ten modules and eight mover groups.
- No Meshy generation or Unreal changes; credits used: 0.

## 2026-08-09 wider Press Trains shared missing-kit gate v821

- Visually inspected and hash-verified Sheets 04-08. Shared Sheet 04 SHA256 is `7B335A8CECC8487AF670873381139E1A24903644331CE09B7091B6CF93DAE0E6`; Train A-D hashes are fixed in the v821 manifest.
- Correct credit-saving architecture is one approved S03 Walker outer body reused at S02-S06 across all four trains. Do not generate four complete trains or duplicate press-frame geometry.
- Each train is 56.00 x 15.00 x 11.50 m with seven centres at 7.50 m pitch. Preserve the 1.50 m operator walkway, 2.50 m die-change corridor, 8.00 m hook clearance and longitudinal S01-to-S07 flow; never turn presses sideways.
- New Pro job `SourceAssets/Candidate/PressTrains/Shared/ProDesignPack_v20260809_v821/PRESS_TRAINS_SHARED_MISSING_KIT_PRO_JOB_v821.md` requests only S01, shared transfers, shared die-change/tooling and S07 surroundings without the retained robot.
- Final moving assembly, Blender validation, owner approval and Unreal intake remain open. Credits used: 0.

## 2026-08-09 player-built route and logistics-class gate v822

- New audit: `Saved/Audits/PressShopIntegration/press_shop_player_built_route_and_handoff_contract_v20260809_v822.json`.
- The elongated 2.80 x 1.70 m coil AGV serves only PR003 storage, PR004 depackaging and optional PR005 bare-coil input. It must never carry PR010 flat blank stacks to a train.
- PR010-to-S01 needs a second stack-carrier AGV/forklift envelope and five interfaces: one PR010 apron plus Train A-D S01 receivers. That vehicle remains TBC.
- Existing blue surfaces are 4.20-5.20 m wide against the coil AGV's 2.30 m requirement. Centred turn capacity is 2.10/2.60 m versus 1.937834 m required; use rounded saved route splines, never hard 90-degree corners.
- The current clean map has zero charger/handoff bay actors. Add them only in a fresh v791 child after owner approval. CR01/MR01 docks remain outside AGV bays; crossings require reservation revalidation afterward.
- No map changes and no Meshy credits used.

## 2026-08-09 blank-stack carrier AGV design gate v823

- PR010 authority proves a removable 2400 x 1900 x 180 mm carrier and 2200 x 1700 x 500 mm reference blank stack.
- New Pro job: `SourceAssets/Candidate/PressShop/BlankStackAGV/ProDesignPack_v20260809_v823/BLANK_STACK_AGV_PRO_JOB_v823.md`. It defines a distinct low-profile stack vehicle, not a coil AGV or forklift, and excludes the carrier/stack from generation.
- Provisional vehicle target is 3200 x 2200 x 420 mm, 2500 x 2000 mm deck support, 350 mm transfer plane, 2800 mm straight lane, 2241.649 mm swept radius and 3800 x 2800 mm bay.
- That turn fits the 5200 mm outer surfaces with 358.351 mm radius margin but fails the 4200 mm storage loop by 141.649 mm. Restrict it to the outer route pending final Blender/runtime measurement.
- No Meshy generation, owner approval, route placement or Unreal import yet. Credits used: 0.

## 2026-08-09 blank-stack AGV Blender candidate v824

- Built `SourceAssets/Candidate/PressShop/BlankStackAGV/EngineeringCandidate_v20260809_v824/Cairnwell_BlankStackAGV_EngineeringCandidate_v824.blend` without Meshy; SHA256 `D3C9C0D398E11890DF53FBA9361E38D03AAF322EB9FACEABFC2F5E761742BD7A`.
- Exact retained plan bounds are 3.20 x 2.20 m. Required parts pass: four drives, separate lift root, eight rollers, four retractable locators, sensors, bumpers, scanners, battery, controls, charge contacts and emergency hardware.
- Separate 2.40 x 1.90 x 0.18 m carrier sits exactly on the Z 0.35 m transfer plane; its top and the 2.20 x 1.70 x 0.50 m stack bottom both equal Z 0.53 m. Containment is positive on every side.
- Seven unloaded/loaded Blender views pass engineering readability. First measurement caught a 27.5 mm E-stop overrun; controls were moved inward and rerendered before retention.
- Owner appearance, authored collision, final runtime swept envelope and Unreal intake remain open. Outer route only. Credits used: 0.

## 2026-08-09 blank-stack AGV runtime-prep v825

- Successor: `SourceAssets/Candidate/PressShop/BlankStackAGV/RuntimePrep_v20260809_v825/Cairnwell_BlankStackAGV_RuntimePrep_v825.blend`; SHA256 `22B597D90474DD52729553A898B38A2009CC05EC1395D6D7D1BC7027A7B084E6`.
- Added separate hidden UCX chassis, lift-deck and loaded-payload proxies. Carrier and stack remain separate references beneath `STACK_AGV_PAYLOAD_ROOT_MOVING`.
- Transient +100 mm lift moved 28 descendants with `3.58e-8 m` maximum follow error; restored neutral error is exactly zero and the saved master is lowered.
- First script attempt stopped before saving due a diagnostic list/vector conversion bug; corrected rerun passes and produced the raised-state proof.
- Owner appearance and Unreal runtime swept-path validation remain open. Outer route only; credits used: 0.

## 2026-08-09 support fleet versus dual-AGV route gate v826

- Decision audit: `Saved/Audits/PressShopIntegration/support_fleet_vs_dual_agv_route_decision_v20260809_v826.json`.
- Retain the two CR01 cleaning robots, two MR01 maintenance robots, four docks and existing runtime. Do not regenerate them in Meshy.
- Their dispatch path runs north away from the south AGV lane and does not cross the blue surface. Four-unit commission/dispatch/return remains passed with 5.034-5.148 cm return error.
- Do not certify the 2.20 m-wide blank-stack AGV on the south segment beside dock X -1250 to +250 cm yet: current evidence records the dock face but not exact rear collision depth.
- Use north/east/west outer segments provisionally. After owner-approved AGVs exist, import only in a fresh v791 child and trace loaded collision, crossing reservation, robot priority stop and all four return cycles before opening the south segment.
- No map changes and no Meshy credits used.

## 2026-08-09 PR002 Pro-pack consistency hold v827

- Latest owner uploads hash exactly to archived v813; no duplicate archive was made.
- The left-side image has a contradictory central suspended scanner/tool, while the other views define two blue scanner heads mounted on the gantry uprights. Do not send v813 to Meshy.
- Correction prompt: `SourceAssets/Candidate/PressShop/PR002/ProPackCorrection_v20260809_v827/PR002_PRO_CORRECTION_PROMPT_v827.md`.
- Require front/rear/left/right true orthographic sheets plus one hero of the identical machine. Keep the coil removable and preserve separate gantry, weigh deck, V-cradle, cabinet, console and safety modules.
- v810 remains engineering/contact authority. No Meshy credits or Unreal changes.

## 2026-08-09 inbound installed crane Blender review v828

- Five-view material review: `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/ReviewPack_v20260809_v828/Review`.
- Audit: `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/ReviewPack_v20260809_v828/inbound_installed_crane_blender_review_v828.json`.
- Retain the separate static runway, moving bridge, trolley and v035 powered C-hook; the close view confirms bore insertion and padded lower-arm coil support.
- No Meshy remake is justified. Owner bridge/runway appearance, final structural data, Blender Y/X/Z motion sweep and Unreal loaded runtime remain mandatory before promotion.
- Source master unchanged; no map changes and zero credits used.

## 2026-08-09 inbound crane motion runtime-prep v829

- Successor: `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/RuntimePrep_v20260809_v829/CA_MW_InboundInstalledCrane_RuntimePrep_v829.blend`; SHA256 `70BC0F905FDFFEC92A385217BEFE43E4DAF3280226108E98A854394455348BCD`.
- Separate neutral roots now own bridge Y, trolley X and loaded hook/coil Z motion.
- First hierarchy test failed safely; corrected roots exposed the hook's offset origin and required an asymmetric trolley limit. Retained measured provisional limits are Y -6.00/+6.00 m, X -2.80/+2.30 m and Z -1.45/+0.50 m.
- All 27 axis-extreme combinations pass. Minimum loaded floor clearance is 0.30 m, maximum hook top is 5.74 m below the 5.93 m bridge underside, and neutral restore error is exactly zero.
- Six renders are under `RuntimePrep_v20260809_v829/Review`. Final engineering and Unreal loaded-runtime validation remain open; original source and maps unchanged; zero Meshy credits.

## 2026-08-09 inbound crane clean placement contract v830

- Audit: `Saved/Audits/PressShopIntegration/inbound_crane_clean_placement_contract_v20260809_v830.json`.
- Provisional root is (-9120,-2500,0) cm, yaw 0; do not copy rejected v770 crane/lorry transforms.
- Trailer pickups use trolley +1.20 m and bridge -6/-2/+2/+6 m for coils Y -3100/-2700/-2300/-1900 cm.
- PR001 provisional centre is (-9400,-2500,0) cm at yaw 90, using trolley -2.80 m and bridge 0. The yaw is mandatory: its local-Y coil bore must become world-X to match the powered C-hook and trailer coils.
- The rotated PR001 footprint leaves 1.80 m plan separation from the lorry. PR003 is outside crane reach by design and must be served by the coil AGV.
- Exact column/dock collision, loaded pickup/drop and exclusion-zone runtime remain open in a fresh v791 child; no map or Meshy change.

## 2026-08-09 combined inbound handoff validation v831

- **v830 coordinates are superseded; do not place them.** The actual lorry, four wrapped coils, v829 crane/C-hook and PR001 were combined in `SourceAssets/Candidate/PressShop/InboundHandoffComposite_v20260809_v831/Cairnwell_Inbound_Lorry_Crane_PR001_Handoff_v831.blend`, SHA256 `CB1170BCB41665A123EEE9DA7AEEC03697BBF5973214FEBB2FA77279216D4A09`.
- Corrected source-aligned world contract: crane root (-9120,-2722,0) cm yaw 0; lorry (-9000,-2500,0) cm yaw -90; PR001 (-9400,-2500,0) cm yaw -90.
- Trailer coil stops use bridge +6/+2/-2/-6 m and trolley +1.20 m. Maximum four-pickup centre error is 5.875 mm. PR001 drop uses bridge +1.50 m, trolley -2.80 m and has 4.527 mm centre error.
- The corrected geometry leaves 1.625 m between the PR001 and lorry X bounds. The saved master is neutral with all four trailer coils visible and both temporary carried/drop reference coils hidden.
- Coordinate audit: `Saved/Audits/PressShopIntegration/inbound_handoff_blender_placement_contract_v20260809_v831.json`; Blender measurement audit is beside the blend. Exact shell/dock collision, loaded Unreal runtime and owner appearance approval remain open. Protected v438 remains byte-identical; zero Meshy credits.

## 2026-08-09 inbound static-overlap and route hold v832-v833

- Headless read-only inspection of v791 found zero fixed shell, dock or column actor bounds overlapping the corrected v831 crane, lorry or PR001 volumes.
- The 13 collision actors reported by the raw broad phase are the retained same-source lorry, four trailer coils and eight stands already occupying the target delivery position; they are not additional blockers. Floor contact and the nav bounds are expected.
- The current `LB_PAINT_FULL_AGVSurface_West`, `LB_PAINT_FULL_AGVBlue_West_E` and `LB_CLEAN_WalkwayYellow_WestInner` do cross the validated crane/PR001 volume. The west AGV segment and walkway edge are therefore held and must be rerouted around the guarded inbound cell, never through it.
- Decision: `Saved/Audits/PressShopIntegration/inbound_v831_static_overlap_decision_v20260809_v833.json`; raw actor evidence: `inbound_v831_static_overlap_v20260809_v832.json`. Exact primitive/runtime collision remains open; maps unchanged and zero credits.

## 2026-08-09 support-robot visual parity gate v834

- Fresh source/render comparison retains MR01 v022 unchanged: its modern body, modular arm/tools, corrected materials, straight-dock fit and runtime contract already meet the new machinery standard. Do not regenerate MR01.
- CR01 v022 remains technically strong and must not be deleted: LODs, collision, brushes, squeegee, dock, dispatch/return and save behavior are proven. Its visible bodywork is distinctly older and more block-built than MR01 and the new Press Shop assets, so appearance remains an owner gate.
- Controlled replacement brief: `SourceAssets/Candidate/PressShop/SupportRobots/CR01_VisualReplacement_v20260809_v834/CR01_PRO_AND_MESHY_JOB_v834.md`. It fixes the 1520 x 980 x 1120 mm envelope, every cleaning/docking function and mandatory separated movers. Generate five consistent Pro views first; spend at most one Meshy job only after approval.
- Decision audit: `Saved/Audits/PressShopIntegration/support_robot_visual_parity_decision_v20260809_v834.json`. Current CR01 runtime remains the fallback authority. Maps unchanged; zero credits.

## 2026-08-09 inbound AGV bypass reservation v835

- Do not restore the rejected X -9500 cm west AGV strip. Reserve a 5.20 m-wide player-built bypass centred at X -7450 cm from the existing south outer centreline Y -4450 cm to the north outer centreline Y +4450 cm.
- The corridor spans X -7710 to -7190 cm. It leaves 9.275 m to the corrected crane frame and 8.950 m to the nearest PR003 stand, while connecting through the existing north/south outer lanes.
- Final PR002 guarding must remain wholly west of X -7860 cm to keep a 1.50 m service/guard margin to the lane. If the accepted model exceeds that edge, recalculate rather than squeezing either machine or lane.
- Audit: `Saved/Audits/PressShopIntegration/inbound_agv_bypass_reservation_v20260809_v835.json`. This is reservation evidence, not an installed route; rounded player spline, charger/wait/handoff actors and exact loaded/runtime tests remain open. No map or credits.

## 2026-08-09 current generation queue v836

- `Saved/Audits/PressShopIntegration/press_shop_current_generation_queue_v20260809_v836.json` is the current Pro/Meshy order. It supersedes stale summary wording that called PR009/PR010 wholly missing or treated contradictory PR002 v813 views as approved.
- Sequence is PR002 correction, optional owner-approved CR01 visual body, PR004 missing equipment only, PR005, PR007/PR006, PR008-PR010, then the shared Press Train missing kit. Pro five-view consistency always precedes Meshy.
- Generate shared train modules once and instance them across A-D; reuse the approved S03 Walker body for every S02-S06 position. Never generate four complete trains or regenerate retained coils, stands, lorry, crane/C-hook, PR003, MR01 or approved S07 geometry.
- Keep untouched textured masters and separate segmented blends; textures, pivots, contacts and motion must pass Blender before Unreal. Zero credits/maps changed.

## 2026-08-09 PR005 controlled Pro/Meshy job v837

- PR005 was the remaining prompt gap: v812 had six bright engineering-reference renders and Candidate_v002 had nine hash-verified exports, but no strict five-view Pro job.
- `SourceAssets/Candidate/PressShop/PR005/ProDesignPack_v20260809_v837/PR005_PRO_DESIGN_AND_MESHY_JOB_v837.md` fixes the 5763 x 10360 x 3550 mm shell, coil inlet, strip outlet, crop-scrap outlet, HMI datum, 1500 mm strip path and all nine separated modules.
- It requests five separate consistent Pro images and forbids melted panels, fused doors/rolls/table, baked environment and dimension invention. Meshy remains locked until owner cross-view approval.
- Audit: `Saved/Audits/PressShopIntegration/pr005_pro_job_readiness_v20260809_v837.json`. No generation, map change or credit use.

## 2026-08-09 PR004/PR006/PR007 separate-view gate v838

- The existing engineering prompts were strengthened to match the owner's separate-sheet rule: five separate images—front, rear, left, right and three-quarter hero—of one unchanged machine, never a combined board.
- PR004 continues to exclude the retained robot and all coil/state geometry. PR006 fixes all 19 rolls, four cylinders and three motors across views. PR007 fixes four headers, twenty nozzles and two tanks while excluding retained strip bridges.
- Every job now requires an untouched textured master plus a separate segmented blend and rejects material fallback after splitting.
- Audit: `Saved/Audits/PressShopIntegration/pr004_pr006_pr007_separate_view_prompt_gate_v20260809_v838.json`. No generation, map or credit change.

## 2026-08-09 PR002 user scanner intake v839

- The new Meshy scanner pair was preserved under workspace `SourceAssets/Candidate/PressShop/PR002/UserScanner_v20260809_v839`; neither source file was edited.
- Blender inspection found a usable textured visual master (one mesh, 958,771 vertices, 1,919,047 polygons) and a 16-part segmented source with no materials or images. The split source is parts evidence only, not an approved visual asset.
- Four true orthographic Blender renders confirm the gantry, twin camera heads, weigh deck/cradle, cabinet, console and safety posts. The supplied wrapped coil is baked into the visual master and must become a removable gameplay payload.
- Decision: conditional accept and perform a no-credit Blender modularization/texture-preservation pass before Unreal. Do not regenerate PR002 in Meshy at this stage. Workspace audit: `SourceAssets/Candidate/PressShop/PR002/UserScanner_v20260809_v839/PR002_SCANNER_INTAKE_AUDIT_v839.json`.

## 2026-08-09 PR002 modular scanner fallback v842

- A full-master UV projection attempt timed out and the subsequent v841 nearest-surface coil cut was explicitly rejected after the empty-state render showed suspended white coil fragments. Never import v841.
- Accepted candidate for further optimisation: workspace `SourceAssets/Candidate/PressShop/PR002/UserScanner_v20260809_v839/PR002_CoilScanner_ModularPainted_v842.blend`, SHA256 `8118C7358D6F5DDE4CECE87074526B97A27E775D5CD18F441C7EE91A8E5FA0A7`.
- v842 keeps all 16 Meshy parts, recreates clean Cairnwell green/charcoal/grey/yellow/white PBR materials, and treats both wrapped coil and its label as removable payload objects. Blender loaded/empty renders prove the cradle remains intact with no floating coil fragments.
- Remaining gates: silhouette-safe reduction from approximately 1.94 million polygons, exact PR002 scale, runtime pivots/collisions, and Unreal placement. Scanner heads are fused to the gantry in the supplied segmentation and therefore share its green material. Credits used: 0. Audit beside candidate as `PR002_SCANNER_MODULAR_PAINT_AUDIT_v842.json`.

## 2026-08-09 PR010 detailed Pro-design gate v820

- Verified authoritative Sheet 03 SHA256 `E69BF1B26342393840B41FBF3BDBB24B4D35DD9E3B25EDB5AD7C1A89348062B3` and inspected its detailed four-lane blank-supermarket hero, module register and motion table.
- ReleaseArt_v103 is retained only for engineering/gameplay interfaces and part splits; its legacy appearance is not authorized for the clean map.
- New five-view job: `SourceAssets/Candidate/PressShop/PR010/ProDesignPack_v20260809_v820/PR010_PRO_DESIGN_JOB_v820.md`. It fixes the 14.00 x 8.40 x 3.60 m footprint, exactly four 3.00 m-pitch lanes, two carrier positions per lane, ten modules and six mover groups.
- No Meshy generation or Unreal changes; credits used: 0.

## 2026-08-10 player-buildable clean Press Shop v913-v914

- Active clean map: `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913`. It is a duplicate of the hash-locked clean shell, not a child of any cluttered integration map. Actor audit contains 91 shell/light actors only: 68 basic shell meshes, 21 rect lights, one skylight and one directional light; no legacy presses, robots, lorry, coils or AGVs.
- The primary game mode now boots directly into the overhead management/build pawn and creates one broad player-buildable floor authority at runtime. There is no required control-room visit. The HUD bottom bar identifies direct build, move, rotate and zoom controls.
- Players can place machinery, draggable storage areas, pedestrian walkways/crossings, safety fencing, AGV route segments/waypoints, chargers, waits and press-train handoffs. Infrastructure and storage save/restore with the factory state. AGV-dependent storage accepts nearby player-built routes; fixed map routes are retained only for old-save migration.
- Wrapped-coil storage now constructs two independently bolted approved adjustable stand rails per coil position. The rails retract to X scale 0.62, sit at local Y +/-46 cm and support the repaired wrapped coil at its true floor-bound pivot. Coils remain separate occupancy/inventory visuals, so an empty player-built store contains empty stands.
- Blender validation: `Saved/ValidationRenders/PressShop/PlayerBuiltCoilStorage_v914/approved_coil_two_stands_three_quarter.png`; audit beside it records zero floating/penetration and zero Meshy credits.
- Approved repaired wrapped-coil Unreal asset: `/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003`, bounds approximately 1.81 x 1.50 x 1.79 m with body and structural-core materials assigned.
- Editor and Win64 game targets compile. Builder, infrastructure persistence, management and storage-authority automation tests pass. A first package attempt exposed editor-only `GetActorLabel` calls in PR006-PR008; these were replaced with runtime-safe `GetActorNameOrLabel`, and the Win64 game target then passed.
- Packaging target: `Builds/PlayerBuildable_v914`. Do not claim the Press Shop complete: accepted machinery visual registration, press-train assembly/orientation, inbound lorry gameplay, four train handoff selection and final packaged visual QA remain open. Protected v438 must remain byte-identical at SHA256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Packaged-camera QA found and fixed two clean-shell runtime faults: cooked shell actors lose their editor labels, so roof hiding now uses the known Z >= 1600 cm roof datum; authored ceiling rectangles are hidden during play because there are no baked lightmaps, with uniform movable sun/sky lighting used for the overhead builder instead. The initial camera distance is 120 m (zoom range 10-180 m), not the previous cramped 65 m.
- Fresh runtime proof: `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v915/clean_builder_runtime.png`. Final Win64 package re-staged successfully, and all nine focused FactoryBuilder/Management/StorageAuthority tests pass afterward.
## 2026-08-10 - player-built approved inbound delivery v916

- Bound the approved 16.50 x 2.55 x 4.00 m Cairnwell lorry directly to the player-build `InboundDeliveryDock` catalogue actor; it replaces the temporary cube presentation and keeps the source vehicle length on the gameplay flow axis without squashing.
- The loaded state is modular: four independently hideable repaired wrapped-coil visuals and eight independently rendered approved adjustable support rails are attached to the reusable empty lorry. The repaired coil uses a bottom-face pivot, so its load height is seated at the measured rail top (132.8 cm) rather than reusing the obsolete 220 cm centred-pivot transform.
- Trailer load spacing is 300 cm pitch, shifted behind the cab. This leaves all four loads readable and allows unloading one coil without replacing the lorry. Runtime proof: `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v916/player_built_approved_lorry.png`.
- Asset/bounds audit: `Saved/Audits/PressShopIntegration/inbound_lorry_unreal_v916.json`. Catalogue/persistence automation, including four-coil separation, passes. The lorry, rails and coils are retained approved assets; Meshy credits used: 0.
- The next inbound task is to connect these four visual load identities to the existing `ALBInboundDeliveryController` crane/C-hook/saddle/AGV handoff sequence. Do not bake the load into the lorry or fall back to the old whole-lorry assembly.
- Fresh Windows Development package including this load is `Builds/PlayerBuildable_v916/Windows/LineBossCarFactory.exe`; BuildCookRun completed successfully. Protected v438 remains byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. No project output was written to OneDrive.
## 2026-08-10 - modular player-built crane unload and grounded storage v917

- Extended the player-built inbound package with retained Blender-reviewed modules: installed runway, independently movable bridge, trolley, hoist and powered C-hook. Runtime visual proof now shows the loaded approved lorry inside the installed crane at `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v916/player_built_approved_lorry.png`.
- Added two approved adjustable rails as a separate fixed receiving saddle rather than importing the still-unapproved PR001 engineering candidate. The component unload authority moves the retained C-hook and an individual wrapped-coil component from trailer to the receiving load point, then hands the same coil identity to the AGV/store authority.
- New automation `LineBoss.FactoryBuilder.MaterialFlow.PlayerBuiltModularInboundUnload` proves one complete modular unload, one trailer visual removed, one identified coil stored and one physical handoff counted. All five `LineBoss.FactoryBuilder.MaterialFlow` tests pass, including the four-coil visible unload and end-to-end panel flow.
- Corrected wrapped-coil storage seating for the repaired bottom-face pivot: player-placed stands measure world bottom Z=0.000 cm and stored coils measure bottom Z=21.800 cm on the approved rail top. `LineBoss.PressShop.Builder.StorageAuthority` passes. Runtime proof: `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v917/player_built_coil_storage.png` (24 independent rails, 12 positions, seven occupied).
- `ALBGameMode` now guarantees one `ALBPlayerBuiltPressFlowController`, so downstream player-built machines and buffers actually advance instead of existing only in isolated tests. Proper player-built AGV art/placement binding remains the next inbound task; do not treat the current tagged AGV test fixture as final art.
- Fresh package: `Builds/PlayerBuildable_v917/Windows/LineBossCarFactory.exe`; BuildCookRun succeeded. Meshy credits used: 0.
# 2026-08-10 — Player-buildable Press Shop v918 AGV intake

- Compared the user-supplied textured and part-segmented Coil AGV Blender masters from orthographic front, rear, left, right and oblique views before Unreal work.
- Selected `Meshy_AI_Cairnwell_Coil_AGV_0809174530_texture.blend` as the appearance authority. The split file matches the envelope but is retained only as a moving-part/pivot guide because it has no usable texture presentation.
- Preserved both untouched sources locally under `SourceAssets/Candidate/PressShop/CoilAGV/Cleaned_v918/`; no project output was written to OneDrive.
- Created `LB_Cairnwell_CoilAGV_CleanMaster_v918.blend` and `SM_CA_MW_CoilAGV_Chassis_v918.glb`. Conservative UV-preserving reduction: 1,984,003 -> 436,479 triangles; dimensions retained at 1.460 x 1.902 x 0.570 m.
- Five-view Blender validation is under `Saved/ValidationScreenshots/SourceAssets/CoilAGV/Cleaned_v918/` and retains the green/white Cairnwell finish, V-cradle, scanners, bumpers and labels.
- Unreal import succeeds at `/Game/LineBoss/Candidates/PressShop/CoilAGV/Cleaned_v918/SM_CA_MW_CoilAGV_Chassis_v918/StaticMeshes/SM_CA_MW_CoilAGV_Chassis_v918` with correct 72.984 x 95.098 x 28.519 cm half-extents and three imported texture maps.
- Next: bind this approved visual to the player-built AGV runtime controller, keep the lift deck separate, and validate the complete receiving-saddle -> storage/prep -> train handoff route in the clean v913 map.
- Meshy credits used: **0**.
- Protected accepted map remains unchanged; SHA256 verified as `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## v920 approved player-built Coil AGV runtime

- Rejected the softer rebaked v919 runtime candidate after visual review; it remains source evidence only and is not referenced by game code.
- Used the split deck solely as a spatial guide to extract the real moving V-cradle directly from the good textured master. This preserves the original UVs, labels and factory paint with no rebake artifacts.
- Approved pair: `SM_CA_MW_CoilAGV_Chassis_v920` (365,718 triangles) and `SM_CA_MW_CoilAGV_LiftDeck_v920` (166,759 triangles), combined envelope 1.460 x 1.902 x 0.570 m.
- Five-view Blender evidence: `Saved/ValidationScreenshots/SourceAssets/CoilAGV/OriginalTextureSplit_v920/`.
- Unreal imports have correct independent bounds and one textured section each under `/Game/LineBoss/Candidates/PressShop/CoilAGV/OriginalTextureSplit_v920/`.
- `ALBCoilAGVController` now self-presents this approved chassis, real moving deck and repaired wrapped coil when no legacy tagged fixtures exist. `ALBGameMode` guarantees one runtime AGV in the clean player-buildable map.
- Player infrastructure is authoritative: wait point + waypoint + at least two painted route segments + selected Train A-D handoff are read by `ConfigureFromPlayerBuiltInfrastructure`; new placements refresh the route.
- Automation `LineBoss.PressShop.PlayerBuilt.ApprovedCoilAGVPresentation` passes, including fixture-free self-binding, player-route derivation, identified-coil travel and physical 80 mm lift-deck handoff.
- Runtime proof: `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v920/player_built_approved_coil_agv.png`. The proof exposed and drove correction of the carried coil seating; final bottom-face datum is 12.5 cm within the measured 7.7–29.1 cm V-cradle range.
- Meshy credits used: **0**.
# 2026-08-10 continuation — PR002 approved player-buildable weigh/inspection cell v921/v922

- Recovered the stronger PR002 Blender handoff from `C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressShop\PR002\UserScanner_v20260809_v839`, copied it into this non-OneDrive project, and revalidated front/rear/left/right/perspective views.
- Retained source: `SourceAssets\Candidate\PressShop\PR002\UserScannerRuntime_v20260810_v921\PR002_CoilScanner_RuntimeCandidate_v848.blend` (16 meshes, 463,267 triangles, correct 1.65 m coil; station envelope 3.580 x 3.691 x 3.624 m).
- Rejected the FBX runtime import because Unreal received it at 1/100 scale. Exported and imported two full-size GLBs instead:
  - fixed station: `RuntimeGLB_v922\SM_CA_MW_PR002_ScannerWeighCell_v922.glb` (14 joined fixed modules, 289,733 triangles, 6 materials);
  - removable load: `RuntimeGLB_v922\SM_CA_MW_PR002_RemovableWrappedCoil_v922.glb` (coil plus label, 173,519 triangles, 1 material).
- Unreal assets live under `/Game/LineBoss/Candidates/PressShop/PR002/RuntimeGLB_v922/`; measured Unreal extents are correct (cell 358.010 x 369.118 x 362.426 cm; coil 163.318 x 107.608 x 166.682 cm).
- Added `CoilWeighInspectionCell` to the player machine catalogue without renumbering older save enums. Player order is now inbound delivery -> PR002 -> depackaging/decoiler -> presses. PR002 is singleton, requires inbound first, and depackaging now requires PR002 plus wrapped-coil storage.
- The scanner/weigh station and wrapped coil are separate runtime components. An empty machine has no phantom coil; accepting a coil shows it seated on the weigh cradle; processing clears it. Save/capture remains deterministic.
- UE5.8 editor build passes. `LineBoss.FactoryBuilder.Machines.OrderedCatalogueAndPersistence` passes with approved visual, payload lifecycle and four-machine persistence assertions.
- Runtime proof in clean rebuild map: `Saved\ValidationScreenshots\PressShop\PlayerBuildable_v922\player_built_pr002_loaded.png`.
- Meshy credits used for this PR002 recovery: **0**.
- Protected accepted reference map remains untouched; SHA-256 is still `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
# 2026-08-10 continuation — clean-map wider Press Trains A-D proof v923

- Audited the player-build train path rather than trusting earlier cluttered-map screenshots. `ULBPressTrainIdentitySubsystem::PlaceTrain` already binds the retained corrected Pro-detail aggregate `SM_CA_MW_PressTrainA_ProDetailUnrealAggregate_v049`, not the old block/procedural presses.
- The retained completed asset measures 57.65 m along the material-flow axis, 13.565 m across and 9.39 m high. The player train protected envelope remains 57.65 x 15.00 x 9.50 m. It is deliberately long-axis local Y; no 90-degree rotation is applied by the player builder.
- Added end-facing runtime identity to each player-built line. The identity is derived from its immutable allocated designation and variant display name; it does not bake a fixed Train A label into B-D. Broadside floating lettering was tried in the first v923 capture and rejected/corrected before retaining the evidence.
- Fresh clean-map runtime proof places four independent lines at 22 m pitch with zero old machinery: `Saved\ValidationScreenshots\PressShop\PlayerBuildable_v923\player_built_press_trains_abcd.png`, SHA-256 `63961E223E03045AD0649252045C610D10A643E4280251CF5DA90CC0CE80995A`. The presses are upright, full length, consistently painted and spaced with service aisles; they are not squashed or sideways.
- UE5.8 editor build passes. `LineBoss.PressShop.PressTrains.Identity.NextAvailablePersistence` passes after the presentation change, including protected-envelope placement, sequential A/B identity, approved completed visual, removal and freed-letter reuse.
- This proves the retained wider train package and its player orientation. It does **not** close the preparation section: PR004/PR005 clean visual replacements and downstream PR006-PR010 player catalogue binding remain open. Do not fill those gaps with forbidden old appearances.
- Meshy credits used: **0**. Protected v438 is still byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

# 2026-08-10 correction — rejected v923/v924 press proof, Blender authority restored

- The v923 capture is **rejected**: it used the forbidden old `ProDetailVisual_v354` aggregate despite its earlier handover wording. It is not approval evidence and must not be restored to the player-build path.
- The first v924 modular capture is also **rejected** because S02-S06 were lying on their sides. The bad `Pitch=90` component transform was removed.
- Authoritative complete-line source is `C:\Users\greg_\Projects\LineBoss_Workspace\SourceAssets\Candidate\PressTrains\TrainA\NewApprovedAssembly_v20260809_v005\Cairnwell_PressTrain_NewApproved_Prototype_v005.blend`. Its retained Blender reviews show five upright Walker presses and the interstage roller beds as one continuous line. Fresh read-only audit: `Saved\Audits\PressTrains\complete_blender_train_v925.json`.
- Corrected Unreal validation now holds the Walker presses upright using `Pitch=0, Yaw=90`: `Saved\ValidationScreenshots\PressShop\PlayerBuildable_v924\player_built_new_press_trains_abcd.png`. This remains a validation layout, not final acceptance: end cells, exact roller joins, lighting and final A-D placement still require close-view verification.
- Never accept a train from automation/test output alone. Blender textured review and close Unreal visual comparison are both required before the train is promoted.
- Meshy credits used for this correction: **0**.

# 2026-08-10 correction v927/v928 — straight-through cup-transfer train

- The v005 Blender file is retained only as a donor for approved textured station modules. Its 12 m stage pitch and interstage roller beds are **rejected as layout authority**.
- Fixed clean-rebuild authority is the 56.0 m single-train envelope with seven stages at 7.5 m pitch: S01 destack, S02 draw, S03 form/restrike, S04 trim, S05 pierce, S06 flange/hem, S07 inspect/unload.
- The panel path must pass straight through every press. Roller beds were removed and replaced by six copies of the previously approved four-part traverse with vacuum cups from `SourceAssets\Candidate\PressTrains\Shared\SegmentedTransferRuntime_v746\Cairnwell_InterPressTransfer_Runtime_v746.blend`.
- Corrected Blender player unit: `SourceAssets\Candidate\PressTrains\TrainA\StraightThroughAssembly_v20260810_v928\Cairnwell_PressTrain_StraightThrough_PlayerUnit_v928.blend`.
- Blender proof views: `Saved\ValidationScreenshots\PressShop\Blender_v928\straight_through_side.png` and `straight_through_elevated.png`. They prove upright Walker presses and corrected 7.5 m pitch; S01 and the complete S07 cell remain open replacements.
- Unreal cup-transfer assets were imported under `/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260810_v927/CupTransfer`. Runtime construction now preserves each source object's authored offset and gives the assembled traverse a 155 cm base datum rather than stacking all four imported origins together.
- The whole train remains one player-placeable/saveable/removable actor while the crossbeam, actuator and cup array remain independently addressable moving parts.
- UE5.8 editor build passes and `LineBoss.PressShop.PressTrains.Identity.NextAvailablePersistence` passes after the 36-module train change. Protected v438 remains byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Meshy credits used: **0**.

## 2026-08-10 — S01 destack comparison (v932)

- Compared both supplied S01 generations in Blender using matching front, side and elevated views.
- Selected the newer set (`Meshy_AI_Cairnwell_S01_Destack_0810074757_generate (1).blend` plus `Meshy_AI__0810080129_part-segmentation.blend`) as the primary S01 geometry.
- Reason: the newer geometry is a clearer straight-through destack/blank-feed station, includes two stack tables and an overhead suction-transfer gantry, and its 52-part split provides better separation for player-buildable and moving components.
- The earlier tall compact S01 set is retained only as a reference/detail donor; its 29-part split includes a detached stray fragment and its enclosed form gives a less convincing through-feed path to S02.
- Rejected the newer Meshy texture as production material: it is washed-out and inconsistent. Use the newer split geometry with controlled Cairnwell materials made in Blender.
- Meshy's raw dimensions are normalized generation dimensions, not authoritative factory scale. Rescale and validate the station against the 7.5 m press-train pitch and S01/S02 handoff before Unreal import.
- No Meshy credits were used for this comparison.

## 2026-08-10 — Selected S01 Blender master (v937)

- Audited the selected newer Meshy split: 52 mesh parts; audit at `Saved/Audits/PressTrains/s01_selected_split_v936.json`.
- Created grounded player-unit master at `SourceAssets/Candidate/PressTrains/S01_Destack/HandPaintedSplit_v937/Cairnwell_S01_Destack_HandPaintedSplit_v937.blend`.
- Set validated working envelope to 7.0 m long x 3.2 m wide x 3.5 m high, with nominal 7.5 m station pitch and material flow along local +X.
- Replaced the rejected Meshy texture with controlled Blender PBR materials: Cairnwell emerald/dark green structure, graphite bases, brushed-steel blank contact decks, grey cabinets/guards, yellow moving suction carriage and black cups/pads.
- Blender proof renders: `Saved/ValidationScreenshots/SourceAssets/S01Comparison_v932/s01_hand_painted_v937_front.png`, `_side.png`, and `_elevated.png`.
- This asset has not yet been imported into the protected Unreal map; Blender validation is intentionally first.
- No Meshy credits used.

## 2026-08-10 — Cleaning robot LB-CR01 Blender intake (v938-v939)

- Received and compared original, 41-part split and textured cleaning-robot Blender files in matching front, side, rear and elevated views.
- Accepted the textured model as the visual master: geometry, wheels, forward side brush, underslung cleaning head, rear squeegee, beacon and Cairnwell/LB-CR01 markings read correctly in Blender.
- Retained the 41-part split as the animation/rig source so wheels, side brush, cleaning head and rear squeegee can be assigned separate pivots rather than treating the vehicle as one static block.
- Preserved all three masters outside Downloads at `SourceAssets/Candidate/PressShop/CleaningRobot/Cairnwell_LB_CR01_v938/`.
- Working dimensions are approximately 1.84 m long x 1.08 m wide x 1.22 m high for the original/textured visual; the split source has a normalized 2.0 m envelope and must be aligned to the textured master before rigging.
- Texture dependency audit `Saved/Audits/PressShopRobots/cleaning_robot_texture_dependencies_v939.json` passes: three file images, all packed into the `.blend`, no missing dependencies.
- Proof renders are under `Saved/ValidationScreenshots/SourceAssets/CleaningRobotComparison_v938/`.
- Unreal import remains pending. Disable Nanite for the first isolated Unreal material test because this already fixed Meshy-style triangular surface breakup on the coil AGV.
- No additional Meshy credits used by Codex.

## 2026-08-10 — Isolated Unreal material proof for S01 and LB-CR01 (v940-v946)

- Exported the approved Blender masters as GLB without reducing geometry or rebaking supplied texture maps. S01 retains 52 independently addressable meshes; the cleaning-robot visual remains one intact textured mesh while its separate 41-part source is reserved for the later rig.
- Imported both assets only into `/Game/LineBoss/Developer/Validation/BlenderApproved_v940/`; Nanite is disabled on every imported mesh. Audit `Saved/Audits/PressShopIntegration/blender_approved_s01_cleaning_robot_import_v941.json` passes (S01: 52 static meshes and 7 material instances; cleaning robot: 1 static mesh, 1 material instance and 3 packed textures).
- Neutral proof map is `/Game/LineBoss/Developer/Validation/Maps/LB_S01_CleaningRobot_MaterialProof_v944`. This is a validation map only; the clean player-buildable rebuild map and protected accepted reference map were not modified.
- Unreal close proof for S01 is `Saved/ValidationScreenshots/PressShop/MaterialProof_v945/s01_unreal_close.png`: the controlled emerald/graphite/steel/yellow Blender materials transfer cleanly with no triangular breakup.
- Unreal close proof for LB-CR01 is `Saved/ValidationScreenshots/PressShop/MaterialProof_v945/cleaning_robot_unreal_close.png`: the original Meshy packed PBR appearance transfers correctly after disabling Nanite. This proves Meshy textures are usable when the original geometry and maps are preserved; repaint only genuinely poor texture generations.
- The cleaning-robot import pivot is vertically centred. The proof actor requires a +61.496 cm Z placement offset to put its measured lower bound at floor Z=0. Preserve this grounding rule when the visual is later bound to the animated 41-part rig.
- No Meshy credits used. Protected v438 remains byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-10 — Approved S01 promoted into player-buildable train (v947)

- Removed the runtime dependency on the forbidden older one-piece S01 model. `ALBPressTrainAStation` now loads all 52 meshes from the approved hand-painted split at `/Game/LineBoss/Developer/Validation/BlenderApproved_v940/S01/Cairnwell_S01_Destack_HandPaintedSplit_v937/StaticMeshes/`.
- Rotated the complete S01 assembly +90 degrees as one authored group: Blender local +X material flow now aligns with the player train's local +Y flow. It is centred on the S01 datum, upright, grounded and hands off toward S02 at the retained 7.5 m station pitch.
- The complete player-placeable train now contains 87 visible modules: 52 S01 parts, five upright S02-S06 Walker presses, six four-part cup-transfer traverses and the six-part S07 unload robot. It remains one actor for placement, save/load and removal.
- UE5.8 Win64 editor build passes. `LineBoss.PressShop.PressTrains.Identity.NextAvailablePersistence` passes with the new 87-module fail-closed assertion.
- Clean-map runtime proof: `Saved/ValidationScreenshots/PressShop/PlayerBuildable_v947/player_train_approved_s01.png`. It shows the new twin-table suction destack cell directly upstream of the upright S02 press; no old S01 fallback is present.
- The clean v913 map is only loaded for transient proof; no test actor was saved into it. Protected v438 remains byte-identical at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- No Meshy credits used.

## 2026-08-10 — packaged player-buildable vertical slice v972

- The actual Windows Development game is packaged at `Builds/PlayerBuildable_v972/Windows/LineBossCarFactory.exe`. BuildCookRun compiled, cooked, staged, packed and archived successfully with exit code 0.
- Default play map remains the clean shell `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913`, with `LBGameMode`. A hidden packaged smoke run loaded that exact map and exited 0; no saved production actors were added to the map.
- The game is console-free by design. A clean boot opens the overhead player builder; `M` or `V` toggles the BUILD catalogue. The player can place machines, coil stands/storage, walkways, crossings, AGV route segments, wait/way points, handoffs and chargers.
- Authoritative process stages are now contiguous: inbound delivery 0 -> PR002 weigh/inspection 1 -> wrapped-coil storage 2 -> depack/ID 3 -> decoiler/threader 4 -> prepared blank buffer 5 -> press train 6 -> inspection 7 -> finished buffer 8 -> outbound 9. Exact material identity is preserved through PR002; the former inbound-to-storage bypass is removed.
- Player press trains are limited to the intended A-D. The current train uses the approved S01 split, five floor-seated upright Walker presses with their real through-throat aligned to material flow, six independently moving cup-transfer assemblies at the internal 202.221 cm panel datum, a native S03 moving die shoe and grounded S07 portal/robot. It remains one placeable/saveable/removable actor with 89 approved visible modules.
- The runtime coil AGV uses the untouched full-detail 1,984,003-triangle user Meshy geometry, not the rejected square/decimated model. The carried wrapped coil uses a duplicated controlled runtime mesh and R2 material that preserves straps/labels but drops the lossy mirror-like ORM/normal maps. Candidate/source assets remain untouched.
- Console-free runtime bootstrap now creates exactly one inbound authority, late-binds only to an unambiguous player dock + PR002 + real link + AGV route, delivers deterministic coil IDs, continues into late-placed storage and locally starts only healthy queued trains. Guard-open and restart-required trains remain fail-closed.
- Validation is green: UE 5.8 editor and packaged game builds pass; ConsoleFreeRuntime 3/3, MaterialFlow 5/5, ApprovedCoilAGVPresentation, OrderedCatalogueAndPersistence, NextAvailablePersistence and ConsoleFreeBuilder boot/confirm all pass (12 focused tests total). Protected v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Keyboard/mouse playtest controls: `M`/`V` catalogue, Up/Down select, Enter choose, WASD pan, Q/E rotate view, wheel zoom, Home reset, left-click place, R rotate placement, Esc cancel. Storage placement is click-drag-release. Gamepad placement confirm is still a known defect; use keyboard/mouse for v972.
- Remaining unapproved final appearances deliberately stay as gameplay placeholders. Replace them through the VisualMaster/MotionProxy/CollisionProxy pipeline without changing the proven gameplay chain. Meshy credits used for this continuation: **0**.

## 2026-08-10 — ordered branches, storage capacity and retained support fleet v973

- Packaged successor build: `Builds/PlayerBuildable_v973/Windows/LineBossCarFactory.exe`. BuildCookRun completed successfully (exit code 0) and a hidden packaged smoke run loaded `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913` and exited 0.
- The build catalogue remains process-ordered: later production equipment is unavailable until its immediate prerequisites exist. Player placement calls the native connection authority, which generates a visible three-point conveyor route with side rails, rollers/belt deck and floor supports; an invalid or out-of-range required predecessor link rejects the placement rather than leaving a disconnected machine.
- Parallel capacity is intentional. One compatible upstream output can feed multiple independently linked next-stage machines up to its authored connection capacity. `LineBoss.FactoryBuilder.Transport.AutomaticNextStageConnection` proves two automatic routes from one distributor output; `LineBoss.FactoryBuilder.MaterialFlow.AutomaticParallelBuffersAndVisibleBottlenecks` proves two depackaging robots drain the same coil buffer and process simultaneously. Extra storage zones and extra already-unlocked process machines therefore relieve genuine gameplay bottlenecks rather than acting as decoration.
- Player-placeable storage types are wrapped/bare coil stands, prepared blanks, finished-panel stillages, scrap, quarantine and maintenance parts. Wrapped-coil storage keeps two independent approved adjustable stand rails per position and separate occupancy-controlled coil visuals, so an empty zone displays empty stands.
- Console-free clean-map startup now creates the retained support fleet only when no legacy operations console exists: CR01-01/02 use approved v065 cleaning robots, MR01-01/02 use approved v022 maintenance robots, each has a separate native v026-compatible service dock, and the support-fleet controller uses the accepted clean service-bank transforms and aisle route. Legacy maps receive no injected starter fleet.
- Validation: UE 5.8 editor build passes; `LineBoss.FactoryBuilder.ConsoleFreeRuntime` 3/3, `LineBoss.SupportRobots` 4/4, automatic transport branching and five material-flow tests pass. Protected v438 remains unchanged. No Meshy generation was performed and credits used remain **0**.
- Art gate remains strict: PR004 engineering v811 is `NOT_UNREAL_AUTHORIZED`; PR005 Pro job v837 requires five consistent owner-approved views before generation/import, while existing modular source manifests remain `UNREAL_IMPORT_CANDIDATE_NOT_PROMOTED`. Keep the current clearly generic gameplay shells until a new visual master passes Blender front/rear/left/right/hero review and owner approval. Do not restore forbidden old/blocky appearances merely because their gameplay code exists.

## 2026-08-10 — future vehicle concept and Meshy text-preview gate v974-v975

- Future product direction is fixed as the Cairnwell M1 Moorcross model-year-2042 practical five-door EV hatchback, not a contemporary car. Concept authority and the owner retry brief are in `SourceAssets/Candidate/Vehicles/M1_Moorcross/DesignAuthority_v975/`.
- One official Meshy Text-to-3D preview task was submitted through the API (`019febd3-8b4b-7595-8458-884aa779080e`) for 20 credits; balance after submission was 6765. No refine, texture, split or rig task was submitted.
- Blender 5.2 preserved and audited the untouched preview: one mesh, 209,687 vertices, 419,642 triangles and seven watertight islands. At the correct 4.38 m length it is about 2.0095 m wide and 1.5506 m high, so it is rejected as too wide, too tall and too contemporary. Decision is recorded beside the source as `MESHY_TEXT_PREVIEW_DECISION_v974.json`.
- The owner will use Meshy's 40 web retries per request to choose geometry before spending on texture. Accept only a low five-door 2042 hatchback with four circular grounded wheels, consistent closures and the intended light-blade/closed-nose design. Download untouched original first, then a separate split, then texture only after Blender approval.

## 2026-08-10 — PR004 credit-minimised modular web retry pack v976

- Blender re-opened the v814 missing-equipment authority and extracted exact module envelopes and moving groups. The former one-shot whole-cell prompt is now split into five small Text-to-3D jobs: powered cradle, film winding/transfer, compactor, output saddle and robot wrist depack tool.
- Owner-ready prompts and acceptance/download order are in `SourceAssets/Candidate/PressShop/PR004/MeshyWebRetryPack_v20260810_v976/PR004_MESHY_WEB_RETRY_PACK_v976.md`. Each prompt excludes the retained robot arm, coils and state props and requires visibly separate moving groups.
- Guards, gate, scanners, HMI and bin remain deterministic reusable game modules instead of wasting Meshy work on layout-dependent parts. Geometry must pass Blender envelope and five-view review before split/texture; Unreal promotion remains unauthorized.
- Audit: `Saved/Audits/PressShopIntegration/pr004_modular_meshy_web_retry_readiness_v20260810_v976.json`. No API task was submitted, no credits were used and no map was modified.

## 2026-08-10 — approved-asset authority reconciliation v977

- `SourceAssets/Candidate/PressShop/PRESS_SHOP_APPROVED_ASSET_MANIFEST_v20260810.json` now matches the packaged v973 state instead of stale pre-integration notes. Inbound lorry/crane/stands/coils, PR002, wrapped-coil storage, Coil AGV, S01/S02-S06/S07 and CR01/MR01 fleets/docks are explicitly `APPROVED_RUNTIME_INTEGRATED`.
- Current generation authority is `Saved/Audits/PressShopIntegration/press_shop_current_generation_queue_v20260810_v977.json`. It removes PR002 and both support robots from the generation queue and makes PR004 v976 the next owner geometry task, followed by PR005, PR007/PR006, PR008-PR010 and optional shared train finishing kit.
- This was an authority/log correction only: no source asset, runtime code, map or packaged build changed, and no Meshy credits were spent.

## 2026-08-10 — continuous player-built inbound AGV route authority v978

- Fixed a genuine fail-open route defect: inbound previously accepted any two AGV route tiles anywhere in the world. It now samples both exact travel legs—wait to turn and turn to the live PR002 input—at 100 cm intervals and requires every sample to be covered by a player route tile within the 75 cm placement tolerance.
- The focused console-free test now places two distant disconnected route tiles and proves delivery remains idle/unbound, then adds a continuous horizontal/vertical route and proves binding, exact PR002 termination, one visible lorry coil removal and identity-preserving delivery.
- UE 5.8 editor build passes. `LineBoss.FactoryBuilder.ConsoleFreeRuntime` passes 3/3 and `LineBoss.FactoryBuilder.MaterialFlow` passes 5/5. Audit: `Saved/Audits/PressShopIntegration/inbound_player_agv_continuous_route_authority_v20260810_v978.json`.
- No map or asset was modified and no Meshy credits were used. Protected v438 remains byte-identical.

### Packaged checkpoint

- Current playable executable: `Builds/PlayerBuildable_v978/Windows/LineBossCarFactory.exe`.
- BuildCookRun completed successfully. A hidden 20-second packaged smoke exited 0 and the runtime log proves `LBGameMode` brought `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913` up for play.

## 2026-08-10 — gameplay parity/exceedance contract

- Durable product plan: `Docs/GAMEPLAY_PARITY_AND_EXCEEDANCE_PLAN_2026-08-10.md`.
- Honest status: v978 already has deeper physical material, routing, branching, storage, press-train and support-robot simulation than the reference baseline, but a complete superiority claim remains gated by onboarding, economy/orders, future vehicle BOMs, progression, quality/rework, UI polish and subsequent shops.
- Finish and user-test the Press Shop milestone before multiplying the same systems into Body, Paint and Assembly. The target is a first accepted panel within 15 minutes without developer intervention, with measurable bottleneck relief and save-safe order-to-profit flow.

## 2026-08-10 — measured inbound package placement v979

- Corrected the player catalogue's inbound placement datum and exclusion envelope from imported runtime bounds. The approved lorry actor now uses the selected factory floor as its root datum instead of being raised 225 cm.
- The protected package now includes the entire loaded lorry, four removable coils, eight support rails, installed crane runway, bridge, trolley, hoist, powered C-hook and receiving saddle. Measured local visible bounds are X -602.5..362.5 cm, Y -944.5..825 cm and Z 0..797 cm; the offset placement envelope adds 25 cm lateral clearance.
- Machine placement collision, debug box and floor grid now follow the offset full-package envelope under rotation, preventing players from building a route or another machine through the crane structure.
- Audit: `Saved/Audits/PressShopIntegration/inbound_player_package_protected_placement_v20260810_v979.json`. UE 5.8 editor build, ordered catalogue 1/1, management 2/2 and ConsoleFreeRuntime 3/3 pass. Protected v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. Meshy credits used: **0**.
- Current executable: `Builds/PlayerBuildable_v979/Windows/LineBossCarFactory.exe`. BuildCookRun succeeded and packaged smoke loaded clean v913 with `LBGameMode` before exiting 0.

## 2026-08-10 — contextual controller placement confirm v980

- Cross/A (`LB_ManagementConfirm`) is now contextual: it confirms the selected catalogue entry while the menu is open, then confirms an active machine, storage-zone or floor-infrastructure preview after the catalogue closes. It no longer becomes a dead button during placement.
- Keyboard/mouse behaviour is unchanged. Cancel remains Escape/B; rotate remains R/right shoulder. Audit: `Saved/Audits/PressShopIntegration/contextual_gamepad_placement_confirm_v20260810_v980.json`.
- UE 5.8 editor build and `LineBoss.Management` 2/2 pass. Meshy credits used: **0**.
- Current executable: `Builds/PlayerBuildable_v980/Windows/LineBossCarFactory.exe`. BuildCookRun succeeded; packaged smoke loaded clean v913 with `LBGameMode` and exited 0. Protected v438 remains byte-identical.

## 2026-08-10 — physical inbound C-hook/bore and saddle datum v981

- Corrected the player-built crane sequence to use the retained Powered C-hook v035 interface instead of snapping the coil's bottom pivot to the hook pivot. The padded arm load centre is 150 cm from the hook body and 59 cm below its datum, rotated with the live hook.
- Pickup, lift, cross-travel and lowering now preserve the wrapped coil's mesh-origin bore centre. At release, the coil's bottom pivot seats on the measured receiving-rail top at inbound local Z 21.8 cm.
- Focused automation observes the live HookEngage and SaddleRelease phases and proves both alignments within 1 cm. UE 5.8 editor build and the full `LineBoss.FactoryBuilder.MaterialFlow` suite pass 5/5.
- Audit: `Saved/Audits/PressShopIntegration/player_inbound_chook_bore_and_saddle_datum_v20260810_v981.json`. This remains visual/gameplay authority only; certified lifting engineering stays TBC. Protected v438 is unchanged and Meshy credits used are **0**.

## 2026-08-10 — save-safe physical unload v982

- Current playable executable: `Builds/PlayerBuildable_v982/Windows/LineBossCarFactory.exe`. BuildCookRun succeeded; packaged smoke loaded clean v913 with `LBGameMode` and exited 0.
- Inbound save schema v4 preserves the lorry, active coil and identity, crane bridge, trolley, hoist and powered C-hook transforms. A mid-lift resume no longer restores the coil while snapping the crane home.
- Save schemas 1-3 remain accepted. Full crane-pose restoration applies to v4 state.
- UE 5.8 editor build and `LineBoss.FactoryBuilder.MaterialFlow` pass 5/5. The player-built test perturbs all four crane components mid-lift, restores them exactly, then completes delivery.
- Audit: `Saved/Audits/PressShopIntegration/player_inbound_mid_unload_save_v20260810_v982.json`. Protected v438 remains unchanged. Meshy credits used: **0**.

## 2026-08-10 — controller infrastructure, A-D handoffs and support-fleet review v983

- Current playable executable: `Builds/PlayerBuildable_v983/Windows/LineBossCarFactory.exe`. BuildCookRun and clean-v913 packaged smoke pass.
- AGV routes, walkways, crossings, fences, chargers and handoffs now fall back to a controller centre-screen floor trace when there is no pointer hit. Cross/A can therefore select and place the complete infrastructure catalogue without a parked mouse cursor.
- S01 handoffs allocate Train A, B, C and D in order. The UI no longer hardcodes every handoff to A. Infrastructure placement no longer reroutes the inbound coil AGV toward S01; its endpoint-aware route remains the player lorry-to-PR002 leg.
- The retained two CR01 and two MR01 units were rechecked against the clean service bank. Exact robot/dock positions and 90-degree dock yaw are now automated assertions; all four commission, certify and bind to their own independent dock.
- Validation passes: editor build; AGV infrastructure 1/1; Management 2/2; ConsoleFreeRuntime 3/3; PressTrains 4/4; ordered catalogue 1/1; MaterialFlow 5/5; SupportRobots 4/4. Protected v438 remains byte-identical. Meshy credits used: **0**.
- Audit: `Saved/Audits/PressShopIntegration/player_infrastructure_train_handoffs_and_support_fleet_v20260810_v983.json`.
## 2026-08-10 — Player-buildable Press Shop v984 (process-readable pending-art stations)

- Replaced the generic two-block fallback for PR004, PR005, panel inspection and outbound handling with engine-native modular placeholders. These are explicitly provisional and do not claim owner art approval.
- PR004 now reads as an open coil-handling gantry with a clear C-hook/AGV centre, paired V-cradle, separate robot silhouette, cabinet and HMI. PR005 now keeps the coil axis and mandrel aligned with local Y material flow and feeds a six-roller line. Panel inspection has a clear through-portal and continuous bed. Outbound has an empty AGV-accessible stillage dock.
- Approved lorry/crane/C-hook, PR002, wrapped coils and stands, untouched Coil AGV, wider Press Trains A-D, CR01 cleaning robots, MR01 maintenance robots and docks were not modified. The old v438 map remains reference-only at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Verification: Editor build PASS; ordered catalogue 1/1; material flow 5/5; press trains 4/4; support robots 4/4; console-free runtime 3/3; approved Coil AGV 1/1. BuildCookRun and packaged clean-v913/LBGameMode smoke PASS.
- Package: `Builds/PlayerBuildable_v984/Windows/LineBossCarFactory.exe`. Audit: `Saved/Audits/PressShopIntegration/player_process_readable_placeholders_v20260810_v984.json`. Zero Meshy credits.

## 2026-08-10 — complete player-buildable coil preparation package v985

- The save-compatible `DecoilerFeeder` catalogue identity now presents and simulates the complete PR005–PR010 package: decoiler/threader, leveller, cleaning/oiling, pre-punch/shear, blank stacker and two-lane blank supermarket/feed buffer.
- The package uses 35 clean engine-native provisional modules and six visible automatic progress steps. It replaces no approved art. A second package remains a valid parallel flow branch for bottleneck relief.
- The current PR009/PR010 Meshy geometry was reviewed but not promoted because its direct/safe-material renders still show melted and glossy forms. Legacy v096/v103 cells are old-map donors and remain reference-only.
- Build PASS; ordered catalogue 1/1; material flow 5/5; BuildCookRun and clean-v913 packaged smoke PASS. Package: `Builds/PlayerBuildable_v985/Windows/LineBossCarFactory.exe`. Audit: `Saved/Audits/PressShopIntegration/player_complete_coil_prep_placeholder_v20260810_v985.json`.
- New owner asset intake: C plastic-film compactor original is preserved and passes static visual review, but requires texture/interaction work. A powered wrapped-coil cradle generation is rejected because it is a spindle unwinder with a blocked coil bore; retry via four consistent orthographic views. Zero Meshy credits used by Codex.

## 2026-08-10 — automatic branch/merge, storage materials and support-fleet checkpoint v986

- Automatic transport now supports authored fan-out and fan-in capacities. A downstream cell placed after parallel machines collects every compatible source; a parallel machine added later connects backward to its predecessor and forward to the existing downstream cell.
- A focused real-actor proof places Press Trains A-D around one prepared-blank buffer and one common panel-inspection cell. Every train receives an independent blank route and contributes an independent formed-panel route; both shared ports reach their designed four-link capacity.
- Primitive storage-zone structure now uses the controlled Cairnwell charcoal, yellow, steel and green materials. Approved wrapped-coil and stand materials remain untouched.
- The retained CR01-01/02 and MR01-01/02 bank remains at the accepted clean positions (`Y=-4050 cm`, docks `Y=-4380 cm`, service aisle `Y=-3500 cm`). Four independent docks commission and certify. Extra PR004 robots and PR005-PR010 packages remain available after unlock and immediately form live bottleneck-relief branches.
- Valid proof: editor build; Transport 2/2; MaterialFlow 5/5; ordered catalogue 1/1; ConsoleFreeRuntime 3/3; AGV infrastructure 1/1; PressTrains 4/4; SupportRobots 4/4; BuildCookRun; packaged clean-v913/LBGameMode smoke. Protected v438 remains byte-identical.
- Package: `Builds/PlayerBuildable_v986/Windows/LineBossCarFactory.exe`. Audit: `Saved/Audits/PressShopIntegration/player_branch_merge_storage_support_checkpoint_v20260810_v986.json`. Meshy credits used by Codex: **0**.
- Pro concept sheet decision: A-D are accepted as concepts pending separate matching orthographic views; E must be simplified before Meshy because its multi-gripper wrist form is likely to fuse during generation.

## 2026-08-10 — PR004 and coil-handler promotion v997-v999

- PR004 now uses the approved complete Meshy/Blender A-E cell and the same adjustable V-block saddle asset is reused for storage. Full masters are preserved; gameplay loads remain separate.
- Normal inbound unloading is autonomous and crane-free. The accepted Green Titan handler retains the textured Meshy chassis/fixed mast and uses a clean, independent lift/backrest/bore-ram assembly because Meshy fused the mast and omitted a usable movable ram in its split.
- Runtime namespace: `/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999`. Blender/audit authority: `SourceAssets/Candidate/PressShop/Inbound/CoilHandlerAGV_v20260810/Hybrid_v999` and `Saved/Audits/PressShopIntegration/coil_handler_hybrid_build_v999.json`.
- UE editor build passes. `LineBoss.FactoryBuilder` passes 12/12, including ordered catalogue, continuous inbound route, visible four-coil unloading, player-built modular unload, branch/merge and console-free bootstrap. The old-map/protected v438 asset remains reference-only.
- Remaining inbound gameplay gap: expose additional coil-handler units as player-placeable capacity and scale unloading throughput without duplicating inventory identity. Current implementation has one functional handler per inbound dock.
- Playable proof: `Builds/PlayerBuildable_v1000/Windows/LineBossCarFactory.exe`; BuildCookRun and clean-v913/LBGameMode packaged smoke pass. Audit: `Saved/Audits/PressShopIntegration/autonomous_coil_handler_pr004_playable_v1000.json`.

## 2026-08-10 — completed player-buildable Press Shop gate v1001

- The complete current `LineBoss` automation set passes 45/45 against the same sources packaged in v1000. Coverage includes the full inbound-to-panel chain, player build order, branches/merges, routes, A-D trains, all preparation handoffs, persistence and the complete CR01/MR01 support fleet.
- The clean v913 map is the sole runtime substrate. Old v438 remains reference-only at the protected SHA-256. Authorised placeholders remain only for assets the owner has not yet approved; gameplay and save authority are complete.
- Requirement-by-requirement evidence is `Saved/Audits/PressShopIntegration/press_shop_completion_audit_v1001.json`.

## 2026-08-10 — v1005 usability correction

- Use `Builds/PlayerBuildable_v1005/Windows/LineBossCarFactory.exe` (SHA-256 `6B66F6CAA95B46C49281728304102FDD7B963F2F73EDBB126800EC328A6DFDA1`). Trailer coil bores now face across the lorry and the physical handler engagement test remains green.
- Initial AGV route and service walkway generation is automatic when PR002 is placed and saved normally. The builder HUD is mouse-first and grouped into bottom-bar categories/cards rather than one combined list. Full automation passes 46/46 and packaging succeeds.
- Do not claim obstacle-aware live rerouting yet. Recalculate automatic route/walkway markings after later placements and reject a placement only when no clearance-valid detour exists.
- Company logo/colour selection is approved as a future saved setup feature; use shared parameterised materials and per-asset paint masks rather than duplicated meshes.
