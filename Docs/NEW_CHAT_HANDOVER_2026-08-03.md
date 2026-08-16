# Line Boss: Car Factory — New Chat Handover

## 2026-08-10 — playable ordered Press Shop and retained support fleet v973

- Current playable Windows build: `Builds/PlayerBuildable_v973/Windows/LineBossCarFactory.exe`. It packages and boots the clean console-free v913 map successfully.
- Catalogue progression is ordered from inbound through PR002, wrapped-coil storage, depackaging, decoiler, prepared blanks, Press Trains A-D, inspection, finished storage and outbound. Required compatible links are generated automatically as visible conveyor assemblies; failed required links reject placement.
- Parallel branches are implemented and tested. A shared buffer can automatically feed multiple extra depackaging robots and both process concurrently, so players can add unlocked machines/storage to relieve bottlenecks. Press trains remain capped at the intended four A-D.
- Placeable storage exists for wrapped/bare coils, prepared blanks, finished-panel stillages, scrap, quarantine and maintenance parts. Empty coil storage retains empty approved stand pairs.
- Clean startup now includes two retained approved CR01 v065 cleaning robots, two retained approved MR01 v022 maintenance robots, four separate service docks and one installed-transform fleet controller. The support and console-free runtime test groups pass; legacy console maps are not modified.
- Do not promote PR004 v811 or the existing PR005 art: their own manifests say owner approval/Unreal authorization is missing. Keep honest gameplay placeholders until new Blender-validated front/rear/left/right/hero evidence is approved. No Meshy credits were used for v973.

## 2026-08-09 — user-approved Coil AGV, isolated PR002 intake, PR009/PR010 intake v851-v860

- Use the user's new Cairnwell Coil AGV, not the earlier square API AGV. v851 preserves the untouched master, creates seven textured parts, scales to 1.70 x 2.20 x 0.75 m and reduces 1,984,003 to 323,723 polygons. Runtime SHA-256: `7A2B1CD3BF75A71F9270A11B01F672669A19C3B610A6AF4444C013C6BA6CD088`.
- v853 is the isolated Unreal intake map for the user AGV and 16-part PR002 scanner. Bounds pass; the removable coil remains; visual meshes use NoCollision with separate proxies. It is not promoted to clean continuation v791.
- v855 restores missing Unreal materials. v858 disconnects the AGV generated normal map because it caused faceted paint; post-v858 recapture and route/dock clearance validation are next.
- User-confirmed PR009 is preserved under workspace `SourceAssets/Candidate/PressShop/PR009/UserMeshy_v20260809_v859`; user-confirmed PR010 is under `SourceAssets/Candidate/PressShop/PR010/UserMeshy_v20260809_v860`. Both textured masters and matching segmentation sources passed Blender intake, but optimisation, scale authority and semantic grouping remain pending.
- No further Meshy credits were used; balance remains 7,085. Protected v438 remains `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-09 — PR002 scanner runtime candidate and Coil AGV API candidate v844-v848

- PR002 v844 reduces the accepted 16-part modular painted scanner from 1,938,490 to 463,267 polygons. Loaded and empty Blender renders pass with the removable wrapped coil and intact cradle. v848 scales from the reference 1.65 m coil OD, floor-aligns the complete station and produces `PR002_CoilScanner_RuntimeCandidate_v848.blend` at 3.580 x 3.691 x 3.624 m; SHA-256 `46E000B3E8FAC1A65B218383A9D0FED0E92A6C9429EFEDBA59BCB2BE4C1E85D6`. Isolated Unreal intake is next; no clean-map placement is authorised yet.
- One controlled Meshy 6 four-view Coil AGV API task `019fe789-9b82-7aff-a0bf-a9086f59f8a8` succeeded for 30 credits with 2K PBR textures. Balance is now 7,085. Raw masters, input views and task evidence are under workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/CoilAGV_Meshy6_API_v20260809_v845`.
- v846 preserves the untouched textured AGV master. v847 corrects Meshy's square 1.90 x 1.90 x 0.80 m output to the intended 2.80 x 1.70 x 0.90 m envelope and produces seven textured adjustable parts at 392,682 polygons. Assembled Blender views pass; internal cut boundaries are visibly rough when exploded, so treat v847 as an adjustable gameplay candidate, not close-up release art. Unreal collision/navigation/route validation is still pending.
- Protected v438 remains untouched at SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

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

## 2026-08-08 — Isolated Meshy press-component intake contract v625

- Added the source-only intake boundary at `SourceAssets/Candidate/PressTrains/Shared/MeshyIsolatedIntake_v625`. Its manifest defines eleven deliberately separate components: ram/slide, upper die, lower die, left door, right door, fixed fence, moving gate, electrical cabinet, HMI pedestal, fixed flywheel housing and rotating flywheel/shaft insert.
- Every part has an explicit reuse scope, pivot, movement and collision contract. Original Meshy downloads must be preserved under `Original/`; cleaning and export are additive. Combined/fused v624 outputs remain evidence and are not silently replaced.
- Rebuild order is fixed: validate the existing static shell and isolated parts, assemble and gate one S03 at the retained v025 datum, derive S02-S06 and Train A only after S03 passes, then derive B-D through identity/material instances only after Train A passes.
- This is preparation only: no Meshy result was imported, no Unreal map changed and no visual or gameplay promotion is authorised. Protected v438 remains byte-identical at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Owner direction confirms the shipped factory should not chase unnecessary close-up density seen in raw Meshy output. v625 now targets roughly 150k-250k LOD0 triangles for one complete S03, with strong lower LODs; small bolts/wear are baked or instanced. Four-train whole-shop performance is the release gate.

## 2026-08-08 — Standing control-room / overhead builder handoff v608-v612

- `ALBControlRoomPawn` now enters the existing overhead `ALBManagementPawn` only when exactly one map-owned build authority exists. The temporary management pawn retains the exact standing pawn, and the existing Stand/Seat action returns possession and destroys the temporary pawn. This makes the build page usable from the standing-first control-room game mode without introducing a second builder authority.
- UE5.8 build passes. Focused `ControlRoomManagementHandoff_v608` passes 1/1 and full `LineBossControlManagementHandoff_v609` passes 34/34 with zero failures or errors. Protected v438 remains byte-identical at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- Read-only exact-v597 audit v610 confirms the correct control-room game mode, one PlayerStart, one operations console, one build authority and four press-train authorities; no child map or guessed placement is required. Exact simulate-mode validators v611/v612 are failed validator evidence only because Simulate does not spawn/possess the default player pawn. They do not indicate a gameplay failure and do not authorise promotion.
- The newly supplied four inbound Pro sheets are byte-identical to the preserved pack at `SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807`; do not duplicate them. They remain the visual authority for the four-coil trailer, protected C-hook unload, fixed receiving saddle and separate Coil AGV handoff, with all unverified values TBC.

## 2026-08-08 — Inbound bright wrapped-steel retention v547-v548

- v547 creates a dedicated lorry-only bright wrapped-steel Material and additive coherent-lorry Candidate_v003. It changes only the existing steel slot (index 5); shared Press Shop materials and prior candidates remain untouched.
- Fresh isolated v548 retains the continuous v540 installed context and visibly restores exactly four bright, curved metallic trailer coils without the v544/v545 dark-coil regression. Retain v548 over v540 as the strongest installed visual-evidence parent.
- v548 remains unpromoted: release-detail machinery/services, readable diegetic controls/signage, final Pro comparison and direct-v438 runtime/collision/navigation/save/authority gates remain open. Decision: `Saved/Audits/PressShopIntegration/inbound_lorry_bright_wrap_retention_v548.json`.

## 2026-08-08 — Inbound visual experiments v541-v545

- v541 roof/camera/exposure is rejected: it reduces empty ceiling but flattens machinery and clips the crane. Never use it as a visual parent.
- v543 creates an additive coherent-lorry v002 with all nine FBX slots remapped to the controlled inbound PBR family. Retain it as technical/material-source evidence only.
- v544 proves the controlled brushed-steel response makes the four trailer coils too dark; v545 skylight/key/reflection probes do not recover adequate silver-coil readability. Reject both visual maps and do not promote them.
- Keep v540 as the strongest installed-layout presentation. Next visual successor must use a dedicated bright wrapped-steel material variant rather than altering shared materials. Decision: `Saved/Audits/PressShopIntegration/inbound_visual_experiments_decision_v541_v545.json`.

## 2026-08-08 — Inbound dock architecture and continuous hall context v536-v540

- Purpose-built `DockArchitecture_v001` imported cleanly at 1240 x 655 x 648 cm with eight material slots and collision body setup. It supplies the missing open dock portal, seals, wheel guides, restraint, controls, traffic lights, scanner, bollards and guarded waiting zone; all engineering values remain TBC.
- v537 installed the dock with the coherent four-coil lorry but retained the black validation void. v538/v539 diagnosed the segmented-wall coverage, and fresh isolated v540 closes the rear-wall gap without obstructing the lorry approach or dock opening.
- Retain v540 only as installed-layout evidence. It clearly reads lorry/four coils → protected crane/powered C-hook → fixed saddle → separate loaded Coil AGV, but crane/lorry detail, lighting and diegetic signage are still below release art. Do not promote or integrate it into v438.
- Decision: `Saved/Audits/PressShopIntegration/inbound_dock_context_decision_v537_v540.json`; evidence: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v540/`. Protected v438 remains byte-identical at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Purpose-built inbound enclosure v001 / v526

- New additive Blender/Unreal candidate enclosure passes scale, five-slot material and collision intake. Retain its guard panels, gates, control/status towers, HMI/E-stops, scanners, signs, impact protection and service trays.
- Do not promote v526 map: enclosure quality improved, but the lorry remains visually detached and the process composition is too spread out. Recompose the full installed linear cell before the next fixed-camera gate.
- Audit: `Saved/Audits/PressShopIntegration/inbound_enclosure_decision_v526.json`; source proof under `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Enclosure_v001/Renders/`; Unreal views under `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v526/`.

## 2026-08-08 — Inbound protected-cell presentation v525

- Isolated v525 technically passes and adds low protected-cell rails, bollards, gate/status points and process identity boards without modifying accepted maps.
- Keep only its safety-layout evidence. Do not promote the render: equipment is too small, hall context remains schematic, and lorry/C-hook/signage presentation still misses the owner Pro sheets.
- Next: rebuild a purpose-built installed enclosure and linear lorry/dock composition before capturing again. Audit: `Saved/Audits/PressShopIntegration/inbound_release_presentation_decision_v525.json`; evidence under `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v525/`.

## 2026-08-08 — Inbound Modular_v005 review v524

- Added and imported Modular_v005 with improved cab, trailer restraints/bows, powered dock restraint, control HMI and entrance interlocks. Candidate_v005 passed isolated import checks; no accepted asset was overwritten.
- v524 proves the complete four-coil lorry → installed crane/C-hook → fixed saddle → Coil AGV chain, but remains geometry evidence only. Reject promotion because the cab is cropped and enclosure, safety zoning, signage/control and C-hook presentation still miss the Pro visual bar.
- Audit: `Saved/Audits/PressShopIntegration/inbound_modular_v005_decision_v524.json`. Evidence: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v524/`. Immutable v438 SHA-256 remains `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

# Automatic linked production and inbound Pro pack v483-v486 (2026-08-07, latest gameplay)

- `ALBPlayerBuiltPressFlowController` now ticks a bounded deterministic scheduler over the actual generated transport links. It empties downstream endpoints first, advances each generic machine once, then clears completed outputs. Shared buffers distribute work across parallel linked machines, so adding a second compatible machine genuinely increases capacity.
- Generic player-built machines now expose saved input/output limits, gameplay process-step tuning and visible `Idle`, `Starved`, `Ready`, `Processing`, `Blocked` and `Fault` states with actionable reasons. The tuning is explicitly gameplay data, not claimed engineering cycle time. A full output buffer prevents consumption rather than deleting or overwriting material.
- Inbound-delivery links are deliberately excluded from generic routing because `ALBInboundDeliveryController`, the crane sequence and the retained coil AGV own that physical handoff. Material-derived reservation/handoff IDs replace the former runtime-only serials so reload cannot reuse an active transaction name.
- Machine save state is version 2 with version-1 migration. UE5.8 build passes; focused `Saved/Automation/AutomaticTimedFlow_v484` passes 3/3 with no warnings. `Saved/Automation/LineBossFullRegression_v486` passes 34/34 (33 clean and the known identity-test teardown warning only). Failed v485 only exposed the missing v2 builder preflight acceptance and is not completion evidence.
- The four owner-supplied inbound design sheets are preserved under `SourceAssets/Reference/PressShop/InboundCoilDelivery/ProPack_v20260807` with SHA-256 lineage. They are the visual authority for the lorry, restraint, crane/C-hook, receiving saddle and separate AGV handoff, but all engineering values remain TBC. Integrate only in a fresh child of v438; do not overwrite or visually promote v438.

# Continuous inbound coil-AGV delivery v478-v480 (2026-08-07, latest gameplay)

- The retained `ALBCoilAGVController` is now reusable rather than a one-way demonstration. After a proved handoff it relinquishes the exact coil identity, lowers its deck, returns through its configured route, restores its original heading, waits empty at staging, survives empty-state save/restore and accepts the next identified coil. Existing safety fail-stops remain authoritative.
- New `ALBInboundDeliveryController` transactionally coordinates the player-built inbound dock, a real AGV transport link, the retained coil AGV and an identified coil-storage zone. Exactly one authority owns the coil at each stage. Full storage rejects the next delivery before dispatch, allowing a visible external lorry queue instead of silent deletion or overflow.
- UE5.8 editor build succeeds. `Saved/Automation/CoilAGVContinuousCycle_v478` and `Saved/Automation/InboundDeliveryContinuous_v479` pass; `Saved/Automation/FactoryBuilderRegression_v480` passes all four `LineBoss.FactoryBuilder` tests, including two consecutive exact-ID deliveries and full-buffer hold.
- This proves automatic inbound-dock-to-coil-store logistics, not final lorry reversing or overhead-crane unloading presentation. Campaign-slot integration and retained-map visual binding remain open. No map or visual lineage changed.

# Campaign save format 14 inbound-logistics authority v481 (2026-08-07, latest gameplay)

- Campaign format 14 adds optional, jointly persisted `FLBCoilAGVSaveState` and `FLBInboundDeliverySaveState`, including the exact bound inbound-dock and coil-store identities. Capture fails closed if only one authority exists or either endpoint identity is missing.
- Restore retains format-13 migration, recreates player machines, storage and transport topology first, then rebinds the saved endpoints and restores AGV state before coordinator state. This prevents a mid-delivery coil from being recreated simultaneously in the vehicle and buffer.
- UE5.8 editor build succeeds. `Saved/Automation/LineBossFullRegression_v481` passes all 33 native `LineBoss` tests with zero failures. No map changed and this remains technical rather than visual promotion evidence.

# Retained-map inbound binding audit v482 (2026-08-07)

- Read-only exact-v438 audit `Saved/Audits/PressShopIntegration/press_shop_inbound_binding_v482.json` confirms one retained coil-AGV chassis, one lift deck, one physical in-transfer coil, one `LBCoilAGVController` and the existing bridge-crane authority. It saved no map.
- No actual lorry/trailer presentation exists in v438; crane components named `EndTruck` are correctly excluded from that conclusion. Therefore the Pro inbound-cell pack is needed for the visible arrival/reversing/unload leg, while existing AGV/crane assets can be reused.
- Do not bind the new coordinator directly into v438 until the inbound dock/store endpoint relationship is authored in a fresh child and checked against the existing PR-003/PR-004 authorities.

# Build authority and variable management zoom v438 (2026-08-07, latest gameplay)

- Retain `Saved/Audits/PressShopIntegration/press_shop_builder_authority_variable_zoom_retention_v438.json` as an unpromoted gameplay/map-authority successor to v437. Native placement now fails closed unless exactly one map-owned `ALBPressShopBuildAuthority` validates the complete train footprint, protected routes and utility reach. Rejections explicitly distinguish missing/duplicate authority, out-of-bay footprint, protected-area conflict and unavailable utilities.
- Fresh direct-v429 child `/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438`, SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`, contains four exact retained A-D reconstruction bays and one explicit utility spine per lane. It changes no visual geometry and is not promoted. Protected v429 remains byte-identical at `6A715DDF9EE0AA6C1529103F2DE905E1DDD94C612D1462F899961D049B4414F0`.
- Management zoom is continuous and smoothed from 1000-18000 cm using the mouse wheel or controller triggers. Placement enforces only a 6500 cm minimum so the full 57.65 m train footprint stays framed. UE5.8 build, focused controller workflow and all 28 native `LineBoss` tests pass.
- Exact-v438 navigation now passes: `press_shop_builder_authority_whole_nav_pie_v439.json` records six valid non-partial whole-shop routes, and `press_shop_builder_authority_aisle_collision_pie_v440.json` passes all three standing-player aisles plus conservative 6 x 3 x 2 m service lanes. B-C retains the previously known single centred service lane.
- Exact build-bay placement now passes in corrected direct validator v446: true yaw-90 A-D transforms are accepted only in their matching bays with their matching utility spines, while the outside control is explicitly rejected. v441 misread the Python return shape; v442/v443/v445 accidentally pitched the train vertically because Unreal Python's positional Rotator order is roll/pitch/yaw. They are failed validator evidence only and never saved the map. Fresh full native regression passes 28/28 with zero failures (one teardown-only warning-bearing test). Retention decision: `press_shop_builder_authority_exact_retention_decision_v447.json`. v438 remains unpromoted pending final aggregate binding, support attachment sockets, Pro-reference visual comparison and separately verified expansion bays.

# Anywhere management and builder grid v437 (2026-08-07, previous gameplay)

- Retain `Saved/Audits/PressShopIntegration/press_shop_anywhere_management_builder_grid_retention_v437.json` as an unpromoted gameplay successor to v436. The primary overhead factory mode and standing control-room mode now share an original Cairnwell management HUD with Overview, Build, Production, Press Trains and autonomous Support Fleet pages. The physical control room remains optional.
- The Build page is progression-aware: it exposes only the next allowed complete S01–S07 press-train package. Placement uses a local 1 m grid, 90-degree rotation, green/red protected-envelope feedback, explicit rejection reasons and the authoritative automatic A–Z allocator. Read-only preview and committed placement share the overlap check.
- Car Manufacture was inspected only for high-level UI interaction patterns; no proprietary code or assets were extracted or copied. UE5.8 build and all 28 native `LineBoss` tests pass. Lot boundaries, utilities, final visual-aggregate preview, parent sockets for support modules and exact-map PIE evidence remain open; no visual map changed.

# Whole Press Shop campaign coordinator v436 (2026-08-07, latest runtime)

- Retain `Saved/Audits/PressShopIntegration/press_shop_whole_campaign_coordinator_retention_v436.json` as an unpromoted runtime successor to v435. `ALBPressShopCampaignController` now owns one fail-closed campaign snapshot across PR-004–PR-010, the exact registered press-train set, operations-console state and optional support-fleet/crane authorities.
- Preflight validates campaign/save identity, stable PR-004 coherence, exact PR-005–PR-010 identities, exact GUID train authority and optional 2+2 support-fleet counts before mutating the world. Restore orders production and train authorities before the control-room assignment, preventing partial or misbound recovery.
- Memory and disk-slot round trips pass. Fresh `Automation RunTests LineBoss` passes 27/27 with zero failures. No visual map changed; v429 remains the retained visual parent. Anywhere-accessible management UI, placement preview/confirmation, exact-map PIE evidence and visual assembly binding remain open.

# Runtime Press Train identity/save authority v434 (2026-08-07, latest)

## Factory-builder placement/removal transaction v435

- Retain `Saved/Audits/PressShopIntegration/press_shop_factory_builder_train_transaction_retention_v435.json` as an unpromoted runtime successor to v434. The world subsystem can now place a native press-train authority, reject overlap using the retained 15 m x 57.65 m protected visual envelope, and remove only an isolated train with no blank/in-process/panel inventory.
- Placement uses the same lowest-free A-Z allocator and immutable GUID/save record. Automation proves overlap rejection, powered-removal rejection, isolated-empty removal, B reuse and survivor A stability. Placement transforms continue through exact-set campaign capture/restore. UE5.8 build and all 26 `LineBoss` native tests pass.
- This is not a visual-map promotion. Factory-lot/utility authority, preview UI, exact-v429 PIE placement/navigation, central campaign-slot coordination and spawning/binding the completed visual assembly remain open.

- Retain the unpromoted native runtime foundation recorded by `Saved/Audits/PressShopIntegration/press_shop_runtime_train_identity_retention_decision_v434.json`. It extends the existing `ALBPressTrainAStation` authority rather than creating a parallel naming system.
- `ULBPressTrainIdentitySubsystem` allocates the lowest unused `TRAIN_A` through `TRAIN_Z`, assigns an immutable `FGuid`, releases a deleted train's designation without renumbering survivors, and derives station identities such as `C-S07`. Custom display names persist independently from operational identity.
- Campaign save format is now 13. The legacy singular `PressTrainA` record remains for v12 migration and the new `PressTrains` array carries identity-aware records. Train snapshots are version 2 with v1 restore support. Control-room snapshots are version 2 and bind the selected train by GUID as well as designation, preventing a saved order from silently targeting a replacement that reused a letter.
- UE5.8 editor build succeeds. Fresh `Automation RunTests LineBoss` passes 26/26 with zero failures. World-level capture writes every live train in deterministic designation order; restore requires an exact GUID-matched set and restores validated placement transforms, failing closed on missing, duplicate, unexpected or corrupt authorities. Player placement/removal transactions and central campaign-slot integration remain open. No map or visual lineage changed; v429 remains the retained visual identity parent.

# Dynamic physical Press Train A-D identity v429/v433 (2026-08-07)

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_DynamicTrainIdentityCandidate_v429`, SHA-256 `6A715DDF9EE0AA6C1529103F2DE905E1DDD94C612D1462F899961D049B4414F0`, as the current identity successor and next experiment parent. It is a fresh direct child of protected v386, which remains byte-identical at `057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038`.
- Four physical Cairnwell boards carry dynamic west-facing labels `PRESS TRAIN A-D / S01-S07`. Fresh exact-v429 close views prove A-D readable and correctly oriented; the matte charcoal face removes the v420 Train B task-light washout. The exact four-line overview shows no new obstruction or shop-presentation regression.
- All 338 actors per train remain. Exact v431 passes six whole-shop non-partial navigation routes with a 0.906 s rebuild; exact v432 passes all standing-player aisles and conservative gameplay service-equipment lanes. Decision: `Saved/Audits/PressShopIntegration/press_shop_dynamic_train_identity_retention_decision_v433.json`.
- v398, v400, v404, v408, v412, v416, v418, v420, v426 and v427 are rejected/nonparent identity attempts. Never parent from them. v429 is retained, not promoted.
- The actual next-available A..Z allocator, immutable save GUID, survivor non-renumbering and custom display-name persistence remain open runtime work; visual tags do not prove runtime/save authority.

# Four-train semantic PBR and balanced lighting v386/v390 (2026-08-07, latest)

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386`, SHA-256 `057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038`, as the current visual/runtime parent. It preserves v374 geometry and structure, remaps all 1,224 aggregate material assignments across Trains A-D into 13 consistent Press Shop PBR families, and adds twelve preview-only broad industrial fills.
- v382 is a failed partial material candidate because its copper-service family was unmapped; it is never a parent. Fresh direct-v374 v383 maps every slot, including a dedicated isolated metallic copper service finish. No source mesh, transform, collision, navigation, runtime, production or save authority changed.
- Owner accepted the v387 matched views as looking good. Exact PIE v388 passes six whole-shop non-partial navigation routes with a 0.969 s rebuild; v389 passes all three standing-player aisles and conservative gameplay service-equipment lanes. The exterior shell remains unchanged because current evidence does not require enlargement.
- Decision: `Saved/Audits/PressShopIntegration/press_shop_train_pbr_lighting_retention_decision_v390.json`. Do not promote yet: distinct A-D identity, final Pro comparison, whole-shop release art and full management/save/automation gates remain open.
- v391 floating TextRender identity and v393 mounted-board retry are both visually rejected and never parents. Their v392/v394 views show orientation, detachment and overview-obstruction failures. Keep clean v386; future A-D identity must be modeled or UV-authored physical signage. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_identity_visual_rejection_v395.json`.

# Wide-span trussed structural presentation v374/v378 (2026-08-07)

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_WideSpanTrussCandidate_v374`, SHA-256 `DDB934BEB76EE377E5E19B36D24C92888AEDC08946774EDC2998FEC58CA06F81`, as the next structural-presentation experiment parent. It preserves the v367 22 m train spacing, removes only the six audited X=2000 cm internal columns, replaces six crude v301 slab girders and adds twelve reusable 40 m fabricated truss visuals. All structural engineering values remain TBC.
- Blender source `SourceAssets/Candidate/PressShop/Structure/WideSpanTruss_v372` contains a 68-member joined truss. Blend SHA-256 `8FB9BE40FC28B9AB43BE1750E7F1BA808B124A73EDFE743E683D7D3FEC909189`; FBX SHA-256 `D437D415B4313900D1FA05D6502921E7D699E9187068472906267CB73D92FF67`. v373 is a failed partial intake caused only by an overly tight 70 cm width gate and is never a parent.
- Fresh v375 views materially clear the four-line and B-C sightlines and read more credibly than the slab girders. Release lighting, material realism and B-D identity still fail; do not promote.
- Exact v376 whole-shop navigation passes all six routes; v377 passes every standing-player aisle and conservative 6 x 3 x 2 m gameplay service probe. The outer factory shell remains unchanged and enlargement is not required. Decision: `Saved/Audits/PressShopIntegration/press_shop_wide_span_truss_retention_decision_v378.json`.

# Expanded four-line layout and whole-shop navigation v367/v369 (2026-08-07)

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_ExpandedTrainNavOptimizedCandidate_v367`, SHA-256 `5CF44DDD90C49BAD1447C50406680045862A957ED01FD4BBF44C58C685594355`, as the next expanded-layout parent. A-D remain on 22 m centres with about 8.435 m between completed visual envelopes. The current exterior floor contains them; exterior-shell enlargement is not required by current evidence.
- v361 found the earlier timeout cause: no train-area nav bounds and 756 MR01 `NoCollision` visual components incorrectly dirtying dynamic navigation. Fresh v362 adds a 66 x 75 m local train block; fresh v367 makes 767 `NoCollision` visual primitives navigation-neutral without altering collision, visibility or runtime authority.
- Exact PIE v364 passes direct standing-player lanes and a conservative gameplay-only 6 x 3 x 2 m service-equipment probe through all three gaps. B-C is the narrowest, retaining one clear centred 3 m-wide lane; its side lanes are constrained by a retained column and PR-010 equipment. Equipment engineering dimensions remain TBC.
- Exact whole-shop PIE v368 rebuilds navigation in 2.734 s and passes six valid non-partial routes: A-B, B-C, C-D, support-fleet common aisle, PR-009 and PR-010. Decision: `Saved/Audits/PressShopIntegration/press_shop_expanded_layout_retention_decision_v369.json`.
- Do not promote v367 yet. Fresh release-composition views, B-D identity, full runtime/management/save regression and final release-art gates remain open.

# Expanded-pitch navigation timeout evidence v359/v360 (2026-08-07)

- The 22 m A-D centre layout remains geometrically retained in unpromoted v356, with about 8.435 m between completed visual envelopes; the existing exterior floor contains it, so no exterior-shell enlargement is yet justified.
- Read-only live-PIE attempts v359 and v360 did not modify or save v356. Both timed out while Unreal reported the full Press Shop navigation build locked (75 s and 180 s respectively). Treat this only as inconclusive navigation-build evidence, not a layout failure or pass.
- Do not promote v356. Diagnose the nav rebuild/dirty-volume cost in a fresh validator, then prove player routes and conservative gameplay envelopes for die carts and removable S04/S05 bins. Move structural columns or enlarge the shell only if that evidence requires it.

# Pro-detail Train A v046/v354 and expanded 22 m four-line layout v356 (2026-08-07)

- Six owner-supplied Pro detail sheets are preserved under `SourceAssets/Reference/PressTrains/TrainA/ProDetailedPack_v20260807` as visual authority only; all unverified engineering values remain TBC.
- Modular source `ProDetailModular_v046` adds 46 retained parts to v044 for connected S04/S05 service paths, stronger S01 destack/feed mechanics and a more credible articulated S07 inspection/unload robot. It contains 474 renderable objects and remains within the protected envelope at `13.565 x 57.650 x 9.390 m`. Source decision: `Saved/Audits/PressTrains/press_train_a_pro_detail_source_decision_v048.json`.
- v351 is rejected because Unreal's combined multi-node import collapsed the longitudinal bounds; v353 is rejected because the complete single-mesh aggregate used the wrong axis mapping. Neither is a parent. Clean transform-baked aggregate v049 imported correctly in fresh v354 at `57.650 x 13.565 x 9.390 m`, floor Z `0`, with one native authority and 126 native collision components preserved. v354 remains NoCollision/navigation-neutral visual evidence and is not promoted.
- Fresh v356 moves native Trains B-D with their retained authority/collision to 22 m centres and previews the same completed source family on A-D. Exact completed visual gap is about `843.5 cm`; 493 native collision components remain. Existing shell floor contains the proposed centres, so exterior enlargement is not yet required.
- Fresh player-height v357 aisle evidence validates the spacing direction, while the roof overview and v355 release compositions are rejected. Columns and exact route/turning gates remain open. Decision: `Saved/Audits/PressShopIntegration/press_shop_expanded_train_pitch_visual_decision_v358.json`. Do not promote v354 or v356 until navigation, collision, die-cart/bin clearance, credible TBC structure, B-D identity and fixed-camera gates pass.

# Train A v343 integration, Pro S04 intake and layout audit v346 (2026-08-07)

- Fresh direct-v301 child `/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343`, SHA-256 `7CE2F5B7D627776B4B71C8197255B035A0561B9E49DEED20A354ABFFB7560317`, preserves one native Train A authority and 126 native collision-bearing components. It hides 337 superseded native presentation actors and adds upright v040 as a `NoCollision`, navigation-neutral visual substrate. Exact visible bounds are `5576.75 x 1045.75 x 939.0 cm`, floor Z `0 cm`; it is not promoted.
- v342 produced no artifact and is rejected. v344 evidence proves upright placement but is visually rejected for oblique, close and column-obstructed composition. Decision: `Saved/Audits/PressTrains/press_train_a_release_integration_visual_rejection_v344.json`.
- Preserved Pro references: supporting systems SHA-256 `D6B7675C2AF1C8086E14EF23D6CE7B7A502464F59546641BC5DE98E44BCDF00E`; S04 Trim/Scrap SHA-256 `53BCCF46045C2CF2ABD82EBB6E4FF458E8B49E015610000F8DBF9E99A55D8562`, both under `SourceAssets/Reference/PressTrains/TrainA/`. They are visual modelling authority only; engineering values remain TBC.
- Read-only v346 measurement proves exact A-D centre pitch is `1700 cm`. Native protected envelopes are `1500 cm` wide, leaving `200 cm` between old envelopes. Equal v040 visible envelopes would leave about `654.25 cm` between machines. Keep 17 m centres and require the completed Pro-led conveyor/bin/service presentation to stay inside the existing 15 m protected envelope. Only change layout in a fresh child if verified collision/navigation/maintenance access fails.
- Trains B-D deliberately retain the old presentation until A passes all visual and technical gates. Audit: `Saved/Audits/PressTrains/press_train_abcd_layout_envelopes_v346.json`.

# Train A axis-corrected modular source v033 retained (2026-08-07)

- v033 preserves the corrected v032 S02-S06 orientation, adds dual-side station-specific identity and exports a full-train FBX without adding runtime authority. Corrected bright review v034 proves the complete S01-S07 sequence, five broad-face shared presses and an unclipped top plan.
- Retain v033 as the current full-Train-A source direction only. It is **not comparison-ready or promoted**: S01 destack/feed and S07 inspect/unload remain visually too light and need integrated dedicated-cell presentation. Unreal, inherited-hall, collision, navigation and runtime gates remain open. Decision: `Saved/Audits/PressTrains/press_train_a_modular_assembly_visual_decision_v033.json`.

# Station tooling variants v030 retained (2026-08-07)

- Five source-only tooling variants distinguish S02 Deep Draw, S03 Form/Restrike, S04 Trim/Scrap, S05 Pierce/Slug and S06 Flange/Hem. All engineering values remain TBC; not imported or promoted. Decision: `Saved/Audits/PressTrains/press_train_a_station_tooling_variants_decision_v030.json`.

# Train A modular assembly v031 axis rejection (2026-08-07)

- v031 structurally assembled seven stations on retained v012 datums with five shared presses and five unique tooling variants. Fresh bright matched views exposed a decisive axis error: the v022 S02-S06 modules were not rotated from their standalone local frame into v012's +Y flow frame, so the operator elevation shows narrow service faces.
- **Reject v031 as an assembly parent; never import or promote it.** Build v032 with a 90-degree local-Z conversion for S02-S06 only, preserve v012-derived S01/S07 orientation and repeat matched views. Decision: `Saved/Audits/PressTrains/press_train_a_modular_assembly_visual_decision_v031.json`.

# Dedicated Train A end-cell guarded source v029 retained (2026-08-07, latest)

- v028 removed 20 obstructing shell objects and materially exposed the mechanisms, but failed only a crude 100 KB S01 FBX heuristic and its tall perimeter outline remained visually dominant. Preserve v028 as failed/nonparent direction evidence.
- Non-overwriting v029 uses lower local mesh guarding and retains distinct S01 destack/feed and S07 robot/inspect/unload machinery. It contains 93 S01 and 103 S07 source parts; independent clean-scene FBX re-import preserves exact vertex/polygon counts and stays below 3 mm dimension drift.
- Six fresh views are materially clearer, so **retain v029 as source direction for isolated complete-Train-A assembly only**. It is not release art, imported or promoted; inherited-hall, tooling/robot-detail and matched whole-train gates remain open. Decision: `Saved/Audits/PressTrains/press_train_a_dedicated_end_cells_guarded_decision_v029.json`.

# Dedicated Train A end-cell v027 visual rejection (2026-08-07, latest)

- Source structure passed with 63 S01 parts, 71 S07 parts and 27 reference-led additions, but six fresh full-cell views prove inherited black operator facades, identity walls and roof slabs hide the useful machinery and contradict the open S01 destack/feed and S07 inspect/unload authority.
- **Reject v027 visually; never import, promote or parent from it.** Retain only its mechanical extraction method and useful destack, feed, robot, inspection, conveyor and stillage components. Decision: `Saved/Audits/PressTrains/press_train_a_dedicated_end_cells_visual_decision_v027.json`.
- Build non-overwriting v028 by removing only the audited presentation shell objects, retaining the mechanisms and adding light open TBC safety framing. Repeat full-cell review before any Unreal intake.

# Shared A-D press-body module library v025 retained (2026-08-07, latest)

- Corrected source export `PressBodyModuleLibrary_v025` splits v022 into 16 separately reusable FBX modules with exact 537-part conservation: 14 common press-body/service groups and two tooling/transfer variant or interface groups. Reuse scope is S02-S06 across Trains A-D; S01/S07 remain dedicated cells.
- Failed v024 counted the hidden combined review mesh as a 538th part and is preserved as failed/nonparent evidence. v025 explicitly excludes that review mesh and passes exact module/part validation without editing retained assets.
- Retain v025 as a source module library only; it is not imported or promoted. Decision: `Saved/Audits/PressTrains/press_train_shared_module_library_decision_v025.json`.

# Complete Train A visual authority intake v023 (2026-08-07)

- Owner supplied `a_high_resolution_infographic_engineering_referenc.png`, SHA-256 `4638AAD84029DFAD74941CCD0586B182E4F39D4EE6230E3D87B388BF87E95DFD`. Accept it as the complete Train A visual modelling authority only; all dimensions, spacing, capacity, cycles, utilities and engineering values remain TBC.
- The sheet resolves the train architecture: S01 is a dedicated destack/blank-feed cell; only S02-S06 share the modular press body; S07 is a dedicated inspection/unload cell. Seven identical press copies are forbidden.
- v022's 16 groups / 537 parts are a reusable shared-body and common-services library for S02-S06 only. S01 requires a dedicated destack source; S07 requires a dedicated unload/inspection source using the retained Cairnwell robot direction. Station datums remain TBC and must not be invented.
- Intake: `Saved/Audits/PressTrains/press_train_a_complete_visual_reference_intake_v023.json`. Machine-readable source contract: `SourceAssets/Candidate/PressTrains/TrainA/TrainAComplete_v023/TRAIN_A_COMPLETE_VISUAL_CONTRACT_v023.json`.

# Pro-aligned S03 compact-service source v022 (2026-08-07)

- Non-overwriting `PressModulePrototype_v022` preserves the 16 reusable component groups and 537 authored parts. It removes 49 cage-like rear service parts, adds 61 compact routing/fabrication/identity refinements and keeps the TBC visual envelope at about 7.008 x 4.475 x 9.390 m.
- Fresh uncropped operator/front/side/rear views materially improve completeness, compact rear-service reading and Cairnwell/S03 identity. **Retain as a source visual direction and authorize isolated Unreal lighting comparison only.** It is not a station replacement and is not promoted.
- Decision: `Saved/Audits/PressTrains/press_train_a_s03_compact_service_source_decision_v022.json`. Whole-train S01-S07 differentiation remains governed by the requested future whole-train reference.

# Pro-aligned S03 detail source v021 visual decision (2026-08-07)

- Non-overwriting `PressModulePrototype_v021` retains the Pro sheet's 16 groups and grows the S03 source from 248 to 525 authored parts (48,376 vertices / 44,820 polygons) without editing retained assets or adding runtime authority.
- Fresh review materially improves crown seams, fabricated upright fasteners, tooling clamps, rear panels/filters/accumulators/valves and mesh guarding. It still fails release: rear pipes are too cage-like, large surfaces remain too smooth, identity graphics are not final and operator/front images crop the machine.
- **Retain v021 as source-detail direction only; do not import or promote it.** Decision: `Saved/Audits/PressTrains/press_train_a_s03_release_detail_decision_v021.json`. Use it only for a compact-service/fabricated-surface successor and fold in a whole-train visual authority when supplied.

# Pro-aligned S03 source v020 visual decision (2026-08-07)

- Owner-supplied sheet `CA-AMW-PT-A-S03-REF-01`, SHA-256 `7F55780C3DF3535C64C126CF71FBB8E5015E8D5540325D38F44B849FDCDB0FE2`, is accepted as visual modelling authority only; every dimension and engineering value remains TBC.
- Source-only `PressModulePrototype_v020` implements all 16 named assembly groups with 248 parts and materially improves the heavy press silhouette, open tooling throat and operator-side equipment relationship.
- Fresh full-machine review still fails release detail: rear services are too blank, crown/drive housings are too box-like, guarding lacks real mesh and the machine lacks reference-level seams, fasteners, latches, gussets and production surface construction. **Retain the sixteen-group architecture and proportion direction only; do not import or promote v020.**
- Decision: `Saved/Audits/PressTrains/press_train_a_s03_pro_aligned_source_decision_v020.json`. Build a non-overwriting v021 detail child and repeat matched front/side/rear/operator visual review before any isolated Unreal intake.

# Part-built Blender press-module source direction v018 retained (2026-08-07)

- Owner requested a trial of the solo-developer component-by-component modelling method seen in SketchUp. Blender 5.2 is the project-equivalent and already fits the automated FBX/Unreal pipeline.
- Source-only `PressModulePrototype_v018` contains 93 separately authored parts (14,300 vertices / 13,388 polygons) for one mid-train station: layered foundation/bolster, four built-up uprights, face/wear plates, ram/guides, crown courses, bearings, motor/flywheel, HMI, cabinet, manifold, pipes, ladder, bolts and guarding. Blend SHA-256 `BCBC3EB0C24C73F511E7472F0344CD61526CC0BA549E12756EB611D632D74A3B`; FBX SHA-256 `DB69B67D78F1D0359E35C5C3BB0A7E5AD8557F353DD2D35E0C283E753C25A921`.
- Fresh full-height renders prove the method produces a more visibly assembled machine than the inherited slab shell. **Retain the method and v018 source direction only; do not promote it.** Crown/drive proportions remain toy-like, the opening lacks die/feed context, exposed drive parts need guarding and materials still require inherited-hall review. v017 failed its conservative envelope check and is evidence only.
- Next refine the same modular source with heavier fabricated crown/guards and tooling context, then import the refined successor into an isolated Unreal comparison under v301 lighting. Decision: `Saved/Audits/PressTrains/press_train_a_part_built_station_source_decision_v018.json`.

# Train A wide-span structural-clearance direction v301 retained (2026-08-07, latest)

- Exact hall inventory proved a 20 m east-west by 15 m north-south structural grid. The X=6000 cm column row sat only about 4 m beyond the Train A operator facade and fragmented every useful view.
- Fresh direct-v300 `/Game/LineBoss/Maps/LB_PressShop_TrainAWideSpanClearanceCandidate_v301`, SHA-256 `8ECBEF72EE262899A15E70B2924EF8F2F1EB8A8480E49525DDFA4FF9245D8BF6`, removes only six audited X=6000 cm columns and adds six `NoCollision`, non-navigation 40 m visual girders marked TBC. All four trains remain exactly 338 actors.
- Exact management, four-native-dock collision, corrected PR009 navigation and all three PR010 routes pass. The overview is materially clearer. **Retain v301 as structural-clearance direction and next experiment parent only; do not promote it.** Replace the crude rectangular visual girders with believable trusses and keep all unverified structural values TBC. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_wide_span_clearance_decision_v301.json`.

# Train A measured lighting direction v300 retained (2026-08-07, latest)

- Read-only exact-v295 audit found 133 lights and one unbound fixed-exposure volume: Basic exposure was pinned `1.0..1.0` at bias `+0.75`, with a steep film curve; Train A also received two 2,350-intensity spotlights plus three 520-intensity close fills. Evidence: `press_shop_train_a_lighting_exposure_audit_v295.json`.
- Fresh direct-v295 `/Game/LineBoss/Maps/LB_PressShop_TrainABalancedLightingCandidate_v300`, SHA-256 `93BF6B46BAD2292019E31C08EF31AF9C9C21CE98BAB9A045CF7670AF5A7AA52C`, applies measured exposure/film balancing, reduces the five harsh Train A task lights, raises three broad ambient fills and uses the v016 segmented shell. All 338 Train A actors remain; protected v295 is unchanged.
- Exact v300 management, four-native-dock collision, corrected PR009 integrated navigation and all three PR010 routes pass. Fresh views materially recover midtones, so **retain v300 as the measured lighting/segmented-shell direction and authorized next experiment parent, but do not promote it**.
- Release remains blocked by the dense column forest, insufficient station breathing room and residual slab/block geometry. Owner real-plant experience confirms automotive stations are separated much more generously. Next audit the exact structural/collision role of every hall column and build a non-overwriting wide-span structural-clearance child; keep unverified spacing TBC. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_balanced_lighting_decision_v300.json`.

# Train A material-readability v299 visual rejection (2026-08-07, latest)

- Fresh direct-v295 candidate `/Game/LineBoss/Maps/LB_PressShop_TrainAMaterialReadabilityCandidate_v299`, SHA-256 `AF1BF46D5C9191C10220CBBA50AB1BEDDD9CBF79E1F913A317FF1EE811993E20`, retains all 338 Train A actors, replaces the operator-face shell with isolated v016, recalibrates 352 Train A-only material assignments and adds three evidence cameras. Structural build checks pass and v295 remains unchanged.
- Exact-map review still shows crushed black faces, clipped white upper surfaces and major column interruption. **Reject v299 visually; never promote or parent from it.** The failure proves material/camera-only iteration is insufficient.
- Return to v295 and audit its exact lights, post-process volumes and exposure controls before another successor. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_material_readability_decision_v299.json`.

# Train A segmented-shell v298 visual rejection (2026-08-07, latest)

- Source-only `PresentationShell_v016` and isolated intake `/Game/LineBoss/Maps/LB_PressTrainAFabricatedShellCandidate_v041` remain useful technical fabrication evidence: the exact envelope is unchanged and the source adds ribs, vents, gussets and fasteners without changing runtime authority.
- Fresh direct-v295 whole-shop child `/Game/LineBoss/Maps/LB_PressShop_TrainASegmentedShellCandidate_v298`, SHA-256 `A3CB483BE3D56E344324CA0C78175F6EC10EDDF810324384E07D71185674AF3F`, passes build/placement/material binding, retains 338 Train A actors and keeps the shell `NoCollision`/non-navigation.
- Fresh exact-map operator, fabrication and overview captures fail release presentation: top faces clip nearly white, working faces remain near-black, residual slab/block mass dominates and the overview is still column-obstructed. **Reject v298 visually; never promote it or use it as a parent. Do not roll it across B-D.**
- Return to protected whole-shop direction v295. The next successor must improve source geometry and calibrated PBR midtones, then use deliberate clear-grid camera sightlines; do not continue exposure-only iteration. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_segmented_shell_decision_v298.json`.

# Train A fabricated operator-face direction v295 (2026-08-07, latest)

- `PresentationShell_v015` is the preferred source-only fabricated visual direction: 235 layered parts, 73,640 vertices, 70,030 polygons, FBX SHA-256 `FEE1630F594E128EA702761ED148BA4268DDD065BB6F66E95432F24F81FA51A5`. Isolated intake v040 passes scale, five-slot materials, `NoCollision`, non-navigation and retained 336-actor/native-station parity.
- v293/v294 are evidence/technical lineage only because their centreline datum hides the shell inside the retained train. Exact operator-face child `/Game/LineBoss/Maps/LB_PressShop_TrainAFabricatedShellOperatorFaceCandidate_v295`, SHA-256 `5CF8715BEE1F55EF98E1B9B713C74BF4F9C87281FE209FA190D73DA61DE94ABF`, places the shell at `[1600,-5180,0]` cm and exposes the intended fabrication detail. Protected v288 remains byte-identical at `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`.
- Exact v295 playable management, four-dock collision, corrected PR009 integrated navigation and PR010 three-route navigation gates all pass. Fresh captures materially improve the train but still fail release presentation due to clipped/crushed exposure, column occlusion, inherited slabs and diagnostic camera composition. **Retain v295 as technical/visual direction only; do not promote or copy to B-D.** Next make a fresh v295 child for local exposure, release cameras and slab cleanup, then repeat Pro-reference review. Decision: `Saved/Audits/PressShopIntegration/press_shop_train_a_fabricated_shell_operator_face_decision_v295.json`.
- v296 and v297 are preserved rejected visual experiments and must never be parents. v296's broad fills/fixed exposure crush close detail and its overview is blocked outside the hall envelope. Direct-v295 camera-only v297 restores a usable overview but remains too dark close-up and column-dominated. Return to v295; the next work must improve residual source slabs/material response and deliberately compose around the immutable 2 m column grid rather than continue exposure-only iteration.

# Whole-shop train visual hold / source fabrication v013 checkpoint (2026-08-07)

- Protected runtime/station-complete parent v288 remains byte-identical at SHA-256 `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`. Fresh exact-map whole-shop captures fail release presentation because structural columns dominate the views, upper-shell contrast remains black/clipped and the inherited press bodies read too rectilinearly against the Pro references.
- Fresh child `/Game/LineBoss/Maps/LB_PressShop_TrainPresentationCandidate_v289`, SHA-256 `6E93AD9261F5F850FF497346B6905BECC3B69B14FE497A796BDDAA348031DBAB`, changes only 1,342 train material slots, 12 local task-fill lights and four inspection cameras. Its fresh views prove the complete machinery exists and improve service-detail readability, but they do not solve source geometry. **Reject v289 as a parent and retain it as evidence only.**
- New source-only `AssemblyStudy_v013` preserves the exact 336-object contract and `15,000 x 56,000 x 10,750 mm` bounds, adds 285 fabrication chamfers and smooths 122 curved objects. Validation passes with no unverified engineering values adopted. Source hashes: Blender `5CD601624C240A7629649304428A994E19796B4254B571C6FCD6EDC80A1CC8C5`; FBX `C78F63859AEF38D2F5C82632BA85BD14456826B47AF38AFD72E43D45AB403F96`.
- Next build a new isolated Unreal import from v013, prove exact object/pivot/bounds/material/collision/runtime-binding parity, then integrate A-D into a fresh direct-v288 child and repeat automation, management, collision/navigation, save and fixed-camera Pro-reference gates. Do not promote v288, v289 or source-only v013.

# Whole-line control-room orchestration checkpoint (2026-08-07, latest)

- Native control-room source now binds the complete PR005-PR010/material-flow/selected-train authority chain. Automatic Start stages PR005-PR008 plus PR010, then advances only real identified blanks and stacks through PR009/PR010 into the selected train; it respects the train's four-blank input capacity and counts only handed-off native inspected panels.
- Any PR005-PR010 or selected-train fault places the order on a named hold and requests a whole-line controlled stop. Unknown remaining coil length is intentionally retained as `AUTHORITY HOLD`, not estimated.
- `Saved/Automation/ControlRoomOrchestration_v008/index.json` is 2/2 green and includes real PR008->PR009->PR010->Train A->panel progression, PR007 guard-fault rollback/recovery, one-panel completion and campaign save/reload. The full control-room family is 5/5 green at `Saved/Automation/ControlRoomCurrent_orchestration_v001/index.json`, including standing-pawn/gamepad centre-view interaction. Full `LineBoss.PressShop` regression is 16/16 green at `Saved/Automation/PressShopCurrent_v288_orchestration_v001/index.json`.
- Exact v288 management PIE passes at `Saved/Audits/PressShopIntegration/press_shop_playable_management_pie_v288_orchestration_v001.json`; physical named-button Create/Start/Pause/Stop/train-selection proof passes at `Saved/Audits/ControlRoom/control_room_physical_buttons_pie_v288_orchestration_v001.json`. The retained map hash remains `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`; no map/save mutation occurred. Continue with final whole-shop visual comparison and packaged playable closure. Do not promote v288 yet.

# PR006-PR008 station-complete whole-shop checkpoint v288 (2026-08-07)

- Latest retained whole-shop parent is fresh direct-v273 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v288`, SHA-256 `D022A98D905916D9A2464CC87D02B2D383F951729DFE1562A5671D58490A47F5`. Protected v273 remains byte-identical at `96E6B172BF284BF6BEA02504C9D07CBBF6E56A4A51F2ED23ABDCE022F93B4394`.
- Complete visible retained PR006/PR007/PR008 cells are installed with exact donor fidelity: 371 checked actors, zero mesh/material/transform/bounds mismatches. Retained task lighting is restored and fresh fixed-camera evidence for all three connected cells passes readability and structural coherence.
- Exact PR006/PR007/PR008 runtime, whole-shop management, PR009/PR010 navigation, four-dock collision and native Press Shop automation gates pass. Automation report: 16 succeeded, 0 warnings, 0 failures.
- v285 is rejected/nonparent for visible superseded donor geometry; v286 is rejected/nonparent for wrong PR008 rotation replay; v287 is technical-pass/nonparent because local task lighting remained too dark.
- **Retain v288 as the station-complete parent only. Overall Press Shop release remains unauthorized** pending final whole-shop presentation, end-to-end order/material orchestration, standing-player control-room release proof and complete playable-package closure. Decision: `Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_complete_cell_decision_v288.json`.

## PR-006–PR-008 complete-cell repair checkpoint v285 (2026-08-07, latest)

- Protected v273 is unchanged at SHA-256 `96E6B172BF284BF6BEA02504C9D07CBBF6E56A4A51F2ED23ABDCE022F93B4394`. v284 is rejected/nonparent because it restored operational movers without the stationary donor structures that visually connect them.
- Fresh direct-v273 child v285 restores the exact absent donor station meshes (PR-006 69, PR-007 108, PR-008 274), retained HMI rows and retained commissioning. Exact runtime/save/motion/HMI/safety gates pass for all three stations. v285 SHA-256: `924D347FC70462B87DFC45DFE728C32950152EFEBE97E99F2646FB6CBD3DCCF3`.
- Do not promote or parent from v285 yet. Fresh fixed-camera visual proof, whole-shop collision/navigation/management/save regression and Pro-reference comparison remain mandatory. See `Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_complete_cell_decision_v285.json`.

## Modular service-dock runtime checkpoint v030 (2026-08-06, latest)

- Preserved Blender sources now export non-overwriting modular Unreal packages under `/Game/LineBoss/SupportRobots/ServiceDocks/Runtime_v026`: MR01 static body plus the exact 180 mm calibration probe, 0-100 degree tool-rack door and 450 mm waste drawer; CR01 remains static because its source defines no authorised moving pivots/travel.
- Added native `ALBSupportRobotServiceDock`. It requires the correct stopped robot/dock/variant plus clear safety zone, operator permit and healthy isolation; permissive loss forces closure. Restore never resumes powered movement and returns closed/de-energised. Native build and `LineBoss.SupportRobots.ServiceDock.GuardedMechanismsAndSafeRestore` pass.
- Corrected Blender +Y to Unreal -Y mechanism placement and rebound all five modular meshes to exact retained `Resolved_v006` material-slot names. Fresh isolated v026-v029 renders are **rejected as release evidence**: the diagnostic stage washes both modular meshes and same-light retained aggregate controls, so it cannot authorize a production replacement.
- **Retain the runtime work technically; do not replace the four installed v269 docks yet.** Next prove the modular actors under representative inherited Press Shop lighting, then run four-berth collision/navigation/docking sweeps in a fresh direct-v269 child. Decision: `Saved/Audits/SupportRobots/service_dock_modular_runtime_decision_v030.json`.

## Press Shop support-fleet certified dispatch checkpoint v269 (2026-08-06, latest)

- Retained fresh direct-v262 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269`, SHA-256 `DDB2708F68F751C5FA69B08C8EFD525BDB3A42ACBE740530AF7512869BB1EFD9`. Protected v260 and v262 remain byte-identical.
- Added the native `ALBPressShopSupportFleetController`. Exact PIE commissions the installed fleet of two MR01 maintenance robots and two CR01 cleaning robots, configures automatic outbound/return routes, and completes all four collision-swept dispatch-and-dock cycles with correct dock identity. Maximum standby error is 9.401 cm and maximum dock error is 8.204 cm; every unit records two completed missions with no faults.
- Corrected collision only on 42 decorative slab saw-cut joints and 8 painted support-bay marks (`NoCollision`, non-navigation). Real cabinets, dividers, structural columns and dock proxies remain blocking; visible geometry and materials were not changed.
- Exact v269 collision, playable-management, PR-009 navigation, PR-010 navigation and automation regressions are green. Fresh close visual evidence confirms an MR01 visibly docked in its retained Cairnwell dock; the overview is context evidence only.
- **Retain v269 as an unpromoted technical/runtime checkpoint.** Full-render moving-route capture, dock moving-part sweeps, and final hall lighting/material/audio polish remain open. Never parent from failed/nonparent v261 or v263-v268.
- Source successor now closes the campaign persistence subgate without altering the v269 map package: the controller captures exactly two CR01/two MR01 records into the existing format-12 root, preserves all other campaign fields, rejects duplicate/wrong identities before restore, and revalidates safety/routes without resuming motion. Separate writer/reader Unreal processes passed the same 15,045-byte slot SHA-256 `9c3ac306fef9535e9115f3e5b568ce9a113515635d64418438ee14760bd20114`; the post-save four-unit route regression also passes.
- The existing operations console now binds fleet authority, reports selected unit/state/dock/battery, and exposes Robot/Dispatch/Recall actions. Exact PIE through console APIs dispatches and recalls CR01-01 to its correct dock with two missions, then selects CR01-02. Updated decision: `Saved/Audits/SupportRobots/press_shop_support_fleet_dispatch_runtime_decision_v269_r2.json`.
- The physical/visual console subgates are now closed in the source successor. Exact `BTN_SUPPORT_DISPATCH`, `BTN_SUPPORT_RECALL` and `BTN_SUPPORT_UNIT` hit-component PIE completes the same CR01-01 round trip and selection change. The first cyan/floating-control render is retained as rejected evidence; the fixed-camera successor uses new non-overwriting v271 exposure-calibrated PBR materials, a contained dark HMI face, bezel and raised keys. Fresh SHA-256 `BE507496F47FC2B73E589DE220550F69469061BC458DCC24A2498F83095593B2` passes the console fleet presentation subgate only. Whole-shop promotion remains unauthorized.

## Manufacturer CAD/dimensional reference intake (2026-08-06, latest)

- Created `SourceAssets/ReferencePacks/Manufacturer_CAD_References_v001/` as a reference-only, unpromoted pack. It contains locally hashed official ABB IRB 7710 specifications and Schuler ServoLine/press-automation brochures, plus official link-only ABB IRT 710 and AIDA tandem-line sources. Redistribution and raw-CAD reuse remain rights-review items.
- Real public baselines now cover the missing machinery sequence, large automotive press/bolster proportions, 5.2 m Schuler crossbar step, 5.5-5.9 m AIDA press spacing, and ABB robot/track dimensional prints. They may calibrate original Cairnwell assets; manufacturer branding must not be copied.
- Comparison audit `cairnwell_comparison_audit_v001.json` found Cairnwell press slide/bolster scale directionally plausible, while its 7.5 m stage pitch is materially larger than the published examples. Do not resize retained geometry automatically: treat the extra pitch as an explicit gameplay/service-clearance decision requiring isolated visual, collision, navigation and runtime revalidation if changed.
- Project source coverage exists for PR-005 decoiling/threading, PR-006 levelling, PR-007 washing/lubrication, PR-008 feeding/blanking, PR-009 stacking and PR-010 storage. This does not prove those assets are all installed/promoted or that panels can yet be produced end-to-end in the protected map.
- Unreal 5.8's `DatasmithImporter` and `DatasmithCADImporter` are now explicitly enabled in `LineBossCarFactory.uproject`. Editor verification passes in `Saved/Audits/CAD/datasmith_cad_importer_verification_v001.json`. This enables genuine CAD intake when STEP/IGES/native CAD is obtained; it does not convert the retained PDFs into 3D CAD and no manufacturer model has been imported.

## Four-berth dock-family source and MR01 fit checkpoint (2026-08-06, latest)

- The Press Shop requirement remains two CR01 cleaning robots plus two MR01 maintenance robots with four independent berths. Exact v253 capacity screening still supplies collision-free provisional roots, but **no dock or support robot is installed and v253 remains the only retained support-layout checkpoint**.
- Preferred unpromoted shared source is now RP01 DockCore v003, SHA-256 `30BDF2776592811DB1B7243E4CB0D318AE7406C721274E54A23FE508D90D0350`. It preserves the exact 2.6 x 1.4 m base and common sockets while post-mounting diagnostics/HMI/E-stop within the envelope so they no longer obstruct the MR01 service aperture. Exact source validation passes; no Unreal intake exists.
- Preferred unpromoted MR source is dock v004, SHA-256 `67234DEF9F5DC8A405113CEA24568793A317215C97EC6FFE75BE334CDF446839`, plus robot source v022, SHA-256 `432233FA43ACB2D67A2E58DE8110272032D10EB53A82AF5971F8ACD3E895EBE8`. The full two-by-four rack is visibly accessible and exact validation proves eight tools, cradles and sockets. Combined datum/static portal review v004 passes with 165 mm lateral clearance per side. Moving sweeps, Unreal collision and runtime remain open.
- Preferred unpromoted CR source is dock v007, SHA-256 `44C4201880265AB9DB10DBA24448F11B43BC5BFD29BA32A269498CD4099430F4`. All six common/wet-service interfaces and the shifted-60 invariant pass. Its current images still use retained CR01 v014 source geometry; actual Unreal CR01 v065 fit and contradictory external envelope remain open/TBC.
- Isolated Unreal fit map v008 (`1A89326FA130BD340DDAF4B1FB1AB4CF496F9B839C6ADEF97A686B5A5699EF75`) is rejected for integration. Five fresh views prove MR01 v021 is docked sideways: its visible front/rear axis is local Y, but the nominal charging components are centred on local -X and the test yaw made the numbers agree while presenting the vehicle side-on. MR01 must reverse straight in with its arm folded upright. Decisions: `service_dock_actual_robot_fit_visual_decision_v008.json` and `service_dock_mr01_orientation_rejection_v008.json`.
- Family decision: `Saved/Audits/SupportRobots/service_dock_family_source_visual_decision_v003.json`. Earlier sources and isolated v006/v007/v008 attempts remain preserved as lineage evidence but are not preferred and are never Press Shop parents. **Do not integrate into a Press Shop map yet.** Next create a clean non-overwriting MR01 successor from retained robot source v022 with rear-face socket authority, regress v021 runtime/save behavior, then repeat actual-robot collision/service-sweep gates before any fresh direct child of v253.

## Press Shop balanced support-layout checkpoint v253 (2026-08-06, latest)

- v251, SHA-256 `576866A18C804ABC208BC3D49724271C5A4753E3C1F4448C01A0E8B3A49BA5AD`, is rejected and never a parent: its PR040 south header intersects inherited column `LB_PRESS_Column_10000_-3750` by `45.0 x 6.5 x 28.0 cm`. v252, SHA-256 `A0AB0BD7E805F0A7CDBB6B8FE386A4F8DB578C235BC518C5A2AB13E7EDFF77AC`, resolves that collision but is visually rejected and never a parent because its task-light pools are severely overexposed and the bays remain generic.
- Fresh direct-v249 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v253`, SHA-256 `51CAF557666AB9F4FE6833165BEA30223200059E9AB548D38DF64074C7094842`, adds the same 143 collision-safe support actors with balanced task lighting. It has 121 support blockers against 1,920 inherited blockers and zero overlap pairs. Exact management PIE, PR009 integrated navigation, PR010 navigation and the full `LineBoss.PressShop` suite pass; automation is 16/16 with zero warnings or failures. Protected v249 remains byte-identical.
- Fresh views establish a materially clearer north-west maintenance department and separately framed east support bays. The north-centre evidence camera is column-obstructed, the eastern departments remain too generic/sparse for release, and production CR01/MR01 docks are not installed.
- **Retain v253 only as an unpromoted support-layout checkpoint and authorized physical starting point for a fresh support-detail child. Do not promote it or call the Press Shop complete.** v249 remains the protected shell/lighting parent; v251 and v252 are never parents. Next refine/build CR01 and MR01 docks, integrate both support robots with charging/routes/collision/navigation/runtime, and repeat unobstructed visual gates. Decisions: `press_shop_structured_support_collision_rejection_v251.json`, `press_shop_structured_support_visual_rejection_v252.json`, and `press_shop_balanced_support_visual_decision_v253.json`.

## Press Shop four-robot dock capacity and MR01 source v001 (2026-08-06, latest support-robot work)

- Fleet authority is now explicit: two CR01 cleaning robots and two MR01 maintenance robots require four independent berths. Build one reusable CR01 dock asset instanced twice and one reusable MR01 dock asset instanced twice; do not make one robot of either pair queue behind a single berth.
- Read-only exact v253 capacity screening checked 1,921 blockers and found 74 valid MR01 pairs in the maintenance bay plus 465 valid CR01 pairs in the utilities bay. Best provisional docked-robot roots are MR01 `(-6495,5160)` and `(-5095,5160)` cm, CR01 `(-1495,5160)` and `(-295,5160)` cm. Each screen includes the 2.6 x 1.4 x 1.71 m dock structure, 1 m side service allowance and 3 m straight approach. Status is capacity pass only; nothing is installed. Evidence: `Saved/Audits/SupportRobots/press_shop_support_dock_placement_capacity_v253.json`.
- The three user-supplied Pro dock sheets are retained as visual form/module references. Corrections are locked: use actual MR01 v021 rather than the depicted cleaner-like robot; exactly eight MR tools; calibration probe travel is 180 mm along CFR X; conflicting CR01 envelope values remain TBC. Review: `Saved/Audits/SupportRobots/service_dock_pro_reference_review_v001.json`.
- New linked-source MR01 dock v001 passes exact 2,600 x 1,400 mm shared base, four common sockets, three moving pivots, exactly eight tools/cradles/sockets, 38 linked common objects and unit-scale gates. It is visually rejected as a release asset: cabinets remain blockout-solid, tools are not exposed correctly, service fabrication/detail is sparse, identity floats and no actual v021 robot fit or Unreal gate exists. **Retain v001 as technical source evidence only; do not import or integrate it.** Decision: `Saved/Audits/SupportRobots/mr01_service_dock_source_visual_decision_v001.json`.

## Press Shop support-area v250 rejection (2026-08-06)

- Fresh direct-v249 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v250`, SHA-256 `71BF04812BA6A29C95293E4E9E45BDAE8B5CCF982C80047B09990DF9D128D37F`, placed 45 existing support assets at the authoritative EST-P anchors for PR-039–044, maintenance, utilities and quality. Protected v249 remains byte-identical.
- Exact v250 management PIE passes. A conservative read-only screen finds zero overlaps between the 45 support blockers and 1,920 inherited blockers.
- Fresh dedicated views fail release quality: the support equipment reads as sparse loose props on open slab, lacks proper bay structure, task lighting, identity and supported services, and remains too dark for CCTV/player inspection.
- **Reject v250 visually; preserve it as technical evidence only; never use it as a parent.** Continue from retained v249. Decision: `Saved/Audits/PressShopIntegration/press_shop_support_area_visual_rejection_v250.json`.

## Press Shop retained shell/lighting checkpoint v249 (2026-08-06, latest)

- Latest retained unpromoted whole-shop parent: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v249`, SHA-256 `CCA3DA3BA67DAD74E4C58D7B0AB0F811639521F666B108987D2C775FA9C12B47`. Its physical ancestry is machine-complete v241 -> retained graphite-grey shell v242 -> v249. Rejected lighting calibrations v243-v248 are preserved as evidence and are not in v249 ancestry.
- v249 adds only three broad movable preview-only roof-bounce lights, with no geometry, machine, material, collision, navigation, engineering-authority or runtime-authority changes. Fixed-view upper-frame luminance improves in management, front and south views without a material clipped-highlight increase, and the roof underside no longer reads as a single black void.
- Exact v249 management PIE passes. Full `LineBoss.PressShop` automation passes 16/16 with zero warnings/failures. Fresh exact Play-state evidence again proves 11 pale-silver stored coils plus one identified transfer coil.
- **Retain v249 as the latest shell/lighting parent, but do not promote it as release.** Legacy whole-shop views remain structurally column-obstructed, support-area/operator-sightline presentation remains incomplete, and end-to-end production gameplay is not yet closed. Decision: `Saved/Audits/PressShopIntegration/press_shop_shell_lighting_visual_decision_v249.json`.

## Press Shop machine-complete/navigation checkpoint v241 (2026-08-06, latest)

- Latest retained unpromoted physical parent: `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v241`, SHA-256 `1CFF3E917A1FD02697CFA41BFF6E6ED08508F0648B14389B486D44820E44B636`. It preserves the exact accepted PR009/PR010 v103 presentation restored in v239, the explicit PR010/Train B-C S01 collision ownership resolved in v240, and restores the accepted PR009/PR010 navigation volumes without changing visible geometry, authority or invented engineering data.
- Exact collision integration passes with 239 restored blockers, 493 train blockers and zero overlap pairs. Integrated PR009 navigation passes two nonpartial service routes with zero protected traversal; PR010 passes three nonpartial routes with zero protected traversal. Exact v241 management PIE passes all PR004-PR010 and Train A-D authority/start/pause/stop/isolation checks. Full `LineBoss.PressShop` automation passes 16/16 with zero warnings/failures.
- Fresh exact PIE proves the coils are still correct: 11 stored pale-silver wrapped coils plus one identified transfer coil. Do not judge coil materials from editor-before-Play captures. Evidence: `Saved/ValidationScreenshots/PressShopIntegration/v241_pr003_pr004_coil_readability/press_shop_v241_runtime_inventory_north.png`.
- **Retain v241 as the machine-complete, collision-safe and navigable parent; do not promote it as release.** Fresh chain/interface views confirm the formerly missing machines are installed, but the hall remains too black, inherited structural columns obstruct key sightlines, machine facades are over-contrasty and support-area presentation is incomplete. Next whole-shop physical work must be a fresh isolated child of v241. Decision: `Saved/Audits/PressShopIntegration/press_shop_machine_navigation_visual_decision_v241.json`.

## Press Shop missing-machine restoration / coil evidence checkpoint v239 (2026-08-06, latest)

- The user's missing-machine report was correct. A read-only exact audit of retained v236 found substantial PR005-PR007 presentation, only six PR008 floor anchors, and no identifiable PR009 or PR010 presentation despite singular native authorities.
- Fresh protected child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v239`, SHA-256 `FE38A3920A1B5A0076F4C19DE693789B79A9EC097EBBCD4F2B61D413DDFE3B6F`, restores the exact accepted PR009/PR010 v103 presentation: 510 presentation actors total, with no new authority or invented datum. Exact management PIE passes and `Saved/Automation/PressShopFull_v239/index.json` passes 16/16.
- **Do not promote or parent further from v239 yet.** Conservative blocking-bound review finds 132 contacts, confined to the PR010/Train B-C S01 infeed interface: 91 common-foundation contacts, 16 transfer-rail contacts and 25 S01 feed/guard/facade contacts. The master plan places PR010 at `[1350,-2000,0]` and first press stages at `X=1600`, so this is the intended interface zone, but the presentation/collision ownership still needs explicit resolution before promotion. v236 remains the protected stable whole-shop parent.
- The coils were not rematerialized dark. Fresh exact PIE on v236 again proves 11 stored coils plus CS-06 on the AGV with pale-silver curved wrap. The dark appearance is confined to editor/non-Play capture rendering; static coil images are no longer valid acceptance evidence. Use exact PIE/standalone evidence for all future coil and whole-shop review. Fresh proof: `Saved/ValidationScreenshots/PressShopIntegration/v236_pr003_pr004_coil_readability/press_shop_v236_runtime_inventory_north.png`.
- Evidence: `press_shop_pr005_pr010_installed_chain_v236.json`, `press_shop_restore_pr009_pr010_presentation_build_v239.json`, `press_shop_playable_management_pie_v239.json`, `press_shop_v239_restored_train_collision_overlap.json`, and `Saved/Automation/PressShopFull_v239/index.json`.

## Press Shop roof/train-readability checkpoint v236 (2026-08-06, latest)

- User priority remains Press Shop completion before expanded gameplay/control-room work. Retained v235 is a fresh direct-v233 child that adds 71 NoCollision, navigation-irrelevant roof modules to the inherited 20, forming a continuous 91-panel physical roof grid over the full hall. The lower roof face is 211.9999 cm above the highest crane-labelled upper bound; geometry, lights, machines and authority are unchanged. v235 SHA-256 is `94D344ADCA249A00974907EAC8DEF80D6C24168FE62B214C8E722EBF639C1200`.
- Fresh direct-v235 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v236`, SHA-256 `DBDE7CDB66CD2B284D8927F28597F4A72D821A6559E23AA67AD509DC934354A7`, replaces exactly 489 installed Train A-D charcoal slots with calibrated graphite. It changes no geometry, transforms, tooling, accents, machine authority or controls; protected v235 remains byte-identical.
- Fresh fixed views show materially clearer press-frame separation while preserving all four trains and the v235 roof. Exact-map PIE passes PR004-PR010 authority, four Train A-D authorities, honest Start hold, selected-train Start, Pause/Stop and isolation. Full `LineBoss.PressShop` automation passes 16/16 with no warnings or failures.
- **Retain v236 as the latest unpromoted whole-shop parent.** Do not promote or call the Press Shop complete: inherited wide cameras remain column-obstructed and final hall/train lighting, material calibration and support-area visual completion remain open. v231, v232 and v234 remain rejected and must never be parents.
- Evidence: `press_shop_upper_hall_roof_build_v235.json`, `press_shop_upper_hall_roof_visual_decision_v235.json`, `press_shop_train_surface_readability_build_v236.json`, `press_shop_playable_management_pie_v236.json`, `press_shop_train_surface_readability_visual_decision_v236.json`, `Saved/Automation/PressShopFull_v236/index.json`, and `Saved/ValidationScreenshots/PressShopIntegration/v236_playable_management/`.

## Press Shop playable coil/shell checkpoint v233 (2026-08-06)

- User priority remains Press Shop completion before any further gameplay/control-room expansion.
- The apparent dark-coil regression was isolated to editor-before-Play evidence. Fresh exact PIE on protected whole-shop v230 proves the playable inventory state is correct: 11 stored coils plus identified CS-06 on the AGV, with curved pale-silver protective wrap. v231 lighting-only and v232 brighter-wrap experiments are visually rejected and must never be parents; continue from v230/v233 lineage only.
- Fresh direct-v230 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v233`, SHA-256 `BA327B0CC7A56F14E468B4C1F3734D3AD7D6E2B00BCB3CD9A262C45120C7DD2A`, refinishes exactly four primary perimeter walls and twenty front-end roof-liner panels as restrained deep graphite. Geometry, lights, machinery, collision, navigation and runtime authority are unchanged; protected v230 remains `C5BC0FFA15FD54AA2F5803ECC6B03DD2320A8C1BC6DB294EC0448177698145A4`.
- Exact v233 PIE passes one PR004-PR010 authority each, all four Train A-D authorities, honest Start hold, selected-Train-A-only Start, controlled Pause/Stop and Train-B isolation. Fresh images show improved perimeter separation but retain a black upper roof field, excessive train contrast and severe structural-column occlusion. **Retain v233 as the latest unpromoted shell-readability checkpoint; do not call the Press Shop complete.**
- Camera-only v234 is visually rejected and never a parent: its elevated front-end overview is clearer, but train/aisle views remain column-obstructed and ceiling-heavy. Evidence: `press_shop_coil_readability_delta_v230.json`, v230/v232 runtime inventory captures, `press_shop_shell_readability_build_v233.json`, `press_shop_playable_management_pie_v233.json`, `press_shop_shell_readability_visual_review_v233.json`, and `press_shop_release_view_camera_visual_rejection_v234.json`.

## Press Shop machine-flow and whole-hall visual checkpoint v230 (2026-08-06, latest)

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

- New manufacturer-neutral source `SourceAssets/IndustrialKit/BridgeCrane/PoweredCHook/Candidate_v035` was built from official Bushman, Winkle and Caldwell design evidence. It has a fabricated double-cheek C-frame, curved transitions, stiffeners/welds/fasteners, long tapered lower arm, replaceable curved saddle and rubber contact, counterbalance beam, powered rotator motor/gearbox/brake/encoder, hoist interface, junction box, protected services, sensors, inspection/guard details, restrained Cairnwell identity and moderate wear. No WIMO branding or capacity marking was copied.
- Independent FBX round-trip audit passes at `Saved/Audits/press_shop_crane_powered_chook_candidate_v035_source.json`; dimensions are `3.8825 x 1.215 x 2.76 m`, pivot is zero, required material slots are present, and all unavailable engineering values remain TBC.
- v141 contains the new geometry and passed the exact primary crane, AGV, 30 t support crane, PR004-to-PR005, navigation and collision gates, but is visually rejected because its original views could still read as hovering beside the coil. v142 is preserved as a second visual reject because its first proof camera cropped the frame.
- Camera-only successor `/Game/LineBoss/Maps/LB_PressShop_PR003PR004PoweredCHookVisualProofCandidate_v143` changes no geometry, materials or runtime authority. Its live full-side, true bore-axis and load-arm-oblique carry captures prove the lower arm is centred in the bore and supports the load without clipping or registration drift.
- Decision: **RETAIN V143 AS THE UNPROMOTED POWERED C-HOOK DEVELOPMENT BRANCH; DO NOT PROMOTE OR CERTIFY.** SWL, thicknesses, stresses, contact pressure, torque, stopping performance and certification are TBC. v124, v135 and v136 remain unchanged. Review: `Saved/Audits/press_shop_pr004_powered_chook_visual_review_v143.json`; closure: `Saved/Audits/PressShopIntegration/press_shop_pr004_powered_chook_closure_v143.json`.

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

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v069` was built directly from v053; v065-v068 are preserved failed calibration/clearance evidence and are not valid parents.
- v069 removes only the two obsolete coarse endpoint occluders, turns S01/S07 into the authoritative positive-Y material-flow direction, moves S07 0.9 m inward to preserve the exact envelope, and retains the separate enclosed endpoint facades. No production map was changed.
- Exact static gate passes: 187 scoped actors, 140 presentation actors, seven stages, seven cameras, seven endpoint assets, five warning-clean v003 couplings, four correctly materialed access assemblies, no missing meshes/failures, and 15,000.005 x 56,000.001 x 11,350 mm bounds. Audit: `Saved/Audits/PressTrains/press_train_a_endpoint_clearance_static_v069.json`.
- Seven fresh fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v069/`. Sheet 05 review passes the **endpoint direction and occlusion subgate**: S01's blank-feed/centring assembly and S07's downstream rollers/panel staging/inspection framing are now visible and truthful.
- Whole-train decision remains **VISUAL HOLD / NOT PROMOTED**. Press bodies remain block-built, carts/couplings toy-like, endpoint sheet metal simplified, labels/HMI/wear shallow, and the black calibration void does not prove installed scale or final lighting. Review: `Saved/Audits/PressTrains/press_train_a_endpoint_clearance_visual_review_v069.json`.
- The next isolated visual successor must again derive from v053 and selectively reuse v069's endpoint direction/clearance only. Do not install Train A in v107 while `Docs/PRESS_TRAINS_IMPLEMENTATION_AUTHORITY.md` keeps Train A-D production datums `TBC_NOT_INVENTED`.

## Control-room standing-first operator revision (2026-08-05, authoritative latest)

- The user confirmed the console screens are physically flat/correct again but the initial camera still reads too low. Product decision: the control-room player now starts **standing**, at the retained approximately 1.68 m eye height, with collision and bounded WASD movement active immediately. Sitting is optional and still requires returning within the authored chair radius before pressing `V`.
- `ALBControlRoomPawn` now initializes its camera at the standing offset and interpolates both height and fore/aft offset when transitioning between standing and the locked seated overview. The HUD already presents the appropriate standing/walking prompt.
- Native Win64 editor compilation passes. The renamed standing-first automation test covers default state, room-bound clamping, chair-proximity enforcement, seated translation lock and standing again. UE 5.8 currently crashes in NavigationSystem during unattended project startup before the automation queue opens, so a fresh visible v041 walk/sit runtime check remains required.
- This is a source/runtime behavior revision to retained `/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVDormantCandidate_v041`; no new map was promoted. The existing active-CCTV VSM overflow hold also remains open.

## Train A v064 endpoint-evidence static pass / visual hold (2026-08-05, authoritative latest)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v064` was rebuilt directly from v053; v061-v063 remain non-parent evidence.
- v064 preserves warning-clean `DockCouplingEvidence_v003`, correctly yawed four access modules, and now copies their component material overrides so all four render with the intended yellow access silhouette. It adds dedicated fixed S01 feed and S07 discharge cameras.
- Exact static gate passes: 189 scoped actors, 142 presentation actors, seven cameras, four access modules, five v003 couplings, seven endpoint assets, exact retained 15,000.005 x 56,000.001 x 11,350 mm bounds, authority/branding checks and no missing meshes/failures. Audit: `Saved/Audits/PressTrains/press_train_a_endpoint_evidence_static_v064.json`.
- Seven fresh views are in `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v064/`. Direct Sheet 04/05 review is **STATIC PASS / ENDPOINT-EVIDENCE FAIL / VISUAL HOLD / NOT PROMOTED**. S01 mainly shows facade/HMI/rollers instead of a packaged blank entering; S07 mainly shows enclosure/guarding/rollers instead of a formed panel, inspection and stillage handoff. Facades remain blocky/repetitive and carts/couplings remain toy-like.
- Review: `Saved/Audits/PressTrains/press_train_a_endpoint_evidence_visual_review_v064.json`. Preserve v064 as material-transfer and occlusion evidence only. The next isolated successor must derive from v053 and make endpoint processes truthful and legible at source or from a real process-axis camera. Do not install in v107 while Train A-D world datums remain `TBC_NOT_INVENTED`.

## Train A v063 industrial-readability static pass / visual hold (2026-08-05)

- Retain `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the Train A baseline. v061 is preserved failed spawn evidence; v062 is preserved wrong-axis/envelope failure; neither is a parent.
- `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v063` was rebuilt directly from v053. It reuses warning-clean `DockCouplingEvidence_v003`, moves four measured access-platform modules ahead of the facade, reduces repeated service green, and gives S01/S07 camera-clearance offsets without changing scale or process axis.
- Standalone exact gate passes: 187 scoped actors, 142 presentation actors, 16 exterior details, four correctly yawed maintenance-access modules, five v003 couplings, seven endpoint assets, 15,000.005 x 56,000.001 x 11,350 mm bounds, no missing meshes and no failures. Audit: `Saved/Audits/PressTrains/press_train_a_industrial_readability_static_v063.json`.
- Fresh Sheet 04/05 review is **STATIC PASS / VISUAL HOLD / NOT PROMOTED**. Yellow access silhouette improves, but two new access instances render grey because component overrides were not copied; endpoints remain weak; carts remain toy-like; facade/service depth and installed factory context remain below the Pro reference.
- Review: `Saved/Audits/PressTrains/press_train_a_industrial_readability_visual_review_v063.json`. Next candidate must again derive directly from v053, copy component materials and add endpoint-specific isolated evidence. Production installation into v107 remains prohibited until the authoritative Train A-D world datums are supplied.

## Train A v060 warning-clean coupling pass / visual hold (2026-08-05, authoritative latest)

- Preserve `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the retained Train A baseline. v060 was built directly from v053; v059 remains failed import-warning evidence and is not a parent.
- `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v060` uses the low-profile `DockCouplingEvidence_v003` source and the v058 charcoal/worked-metal policy. Its FBX import completes with zero errors and zero warnings.
- Exact static gate passes: 185 scoped actors, five warning-clean engaged couplings, seven endpoint bindings, 15,000.005 x 56,000.001 x 11,350 mm bounds, zero missing assets and no failures. Audit: `Saved/Audits/PressTrains/press_train_a_dock_coupling_static_v060.json`.
- Five fresh fixed views are in `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v060/`. Direct Sheet 04/05 review is **TECHNICAL PASS / VISUAL HOLD / NOT PROMOTED**. The coupling is no longer a duplicate full cart, but the train remains too dark/blocky, cyan/green parts read toy-like, yellow service structure is weak, endpoints lack readable process state and installed scale is unproven.
- Review: `Saved/Audits/PressTrains/press_train_a_reference_finish_visual_review_v060.json`. Continue a new isolated successor from v053, selectively reusing v003 coupling geometry and the v058 finish direction; do not run runtime promotion gates until the visual hold closes.

## Train A v058 reference-finish direction pass / coupling hold (2026-08-05, authoritative latest)

- Preserve `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053` as the retained Train A baseline. v058 was built directly from v053 while reusing only the verified v057 fit result.
- Isolated `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v058` applies 21 primary-mass material overrides: stage/enclosure green is replaced by layered charcoal and enclosure grey by worked metal, while secondary Cairnwell/Train A identity remains. Camera exposure is restrained.
- Exact static gate passes: 185 scoped actors, five couplings, 15,000.005 x 56,000.001 x 11,350 mm bounds, zero missing assets, zero map warnings. Five fresh fixed views are in `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v058/`.
- Direct Sheet 04/05 review is **DIRECTION PASS / COUPLING AND INSTALLED-CONTEXT HOLD / NOT PROMOTED**. Charcoal massing is improved, but the v001 coupling reads like a second cart, bright repeated housings look toy-like, yellow service structure and endpoint states remain weak, and the black validation void does not prove installed scale.
- Review: `Saved/Audits/PressTrains/press_train_a_reference_finish_visual_review_v058.json`. Next: redesign a dimensioned low-profile coupling source, rebuild an isolated successor from v053 with the v058 material policy, then repeat static and fresh visual gates.

## Train A v057 coupling-fit technical pass / visual hold (2026-08-05, authoritative latest)

- Preserve retained baseline `/Game/LineBoss/Maps/LB_PressTrainADieChangeLightingCalibrationCandidate_v053`. v056 failed the 15 m envelope and authority-tag gate; it remains failed evidence and must not become a parent.
- Isolated `/Game/LineBoss/Maps/LB_PressTrainADockCouplingEvidenceCandidate_v057` was rebuilt directly from v053. It corrects the five coupling tags and brings their service-side edge 621 mm inward without scaling. Exact static audit passes: 185 scoped actors, five engaged couplings, 15,000.005 x 56,000.001 x 11,350 mm aggregate bounds, zero missing assets, zero map warnings.
- Five fresh fixed-camera images are in `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v057/`. They were inspected against actual machinery-pack `SHEET_04_PRESS_TRAINS_SHARED_ARCHITECTURE_4K.png` and `SHEET_05_PRESS_TRAIN_A_4K.png`.
- Visual decision: **HOLD / NOT PROMOTED**. v057 is too bright, clean and green; yellow safety silhouette is weak; die carts are too compact; coupling engagement reads busy; S01/S07 operational states and installed scale cues remain weak. Review: `Saved/Audits/PressTrains/press_train_a_dock_coupling_visual_review_v057.json`.
- Next Train A successor must start from v053, selectively reuse the validated coupling fit, and correct charcoal/worked-metal finish, long service-side carts, guarding, endpoint states and installed context before runtime gates.

## Integrated Press Shop environment v107 retained direction (2026-08-05, authoritative latest)

- Retain unpromoted `/Game/LineBoss/Maps/LB_PressShop_IntegratedEnvironmentCandidate_v107` as the latest shared-hall visual parent. Accepted station map v103 remains immutable and unchanged.
- v107 succeeds rejected v104 for operational camera composition: five cameras are below the roof/cranes and show front-end flow, crane/coil work, the connected PR-005–PR-010 line, PR-009/PR-010 cells and logistics spine. Twenty shared luminaires establish continuous ambient coverage; 42 measured 6 m slab joints remove the plank-floor read.
- Fresh evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v107_integrated_environment/`. Review: `Saved/Audits/PressShopIntegration/integrated_environment_visual_review_v107.json` = **DIRECTION PASS / WHOLE-HALL AND PRESS-TRAIN INSTALLATION HOLD / RETAINED / NOT PROMOTED**.
- v105 and v106 are preserved failed partial builds and must not become parents. v107 build audit passes with no failures: `integrated_environment_build_v107.json`.
- The remaining column forest/black upper shell cannot be honestly closed while four press trains are absent from the production map. Continue isolated Train A from retained v053, obtain authoritative Train A-D production datums, then install the trains into a new v107-derived environment successor. Do not invent world placement or run full integrated promotion gates yet.

## Control-room monitor correction, seated/standing loop and dormant PR-004 CCTV v041 (2026-08-05, authoritative latest)

- Retain unpromoted `/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVDormantCandidate_v041` as the latest control-room baseline. It preserves the real streamed PR-004 authority/feed, corrected Cairnwell/Moorcross identity and the raised seated view.
- The prior monitor calculation was dimensionally wrong: the Pro reference's 12-degree operator tilt is measured back from vertical. Blender source rotation must therefore be `78` degrees from horizontal, not `12`. Preserved source successor: `SourceAssets/ControlRoom/MainControlRoom_v034`; map correction begins at v034. Fresh v041 seated image `Saved/Screenshots/WindowsEditor/ControlRoomOperatorEvidence_20260805_124522.png` passes this orientation subgate.
- `ALBControlRoomPawn` is now seated-first with a deliberate `V` stand/sit transition, 1.30 m seated eye, 1.68 m standing eye, WASD movement only while standing, collision/room bounds, chair-return radius, and exact authored-view restoration when sitting. Fresh standing/walking/return evidence: `ControlRoomOperatorEvidence_20260805_122347.png`, `...122423.png`, `...122505.png`.
- The real PR-004 CCTV is dormant at map start. `C` or clicking starts capture; `Home` hides and stops it while retaining the last frame. Clean settled Home evidence: `ControlRoomOperatorEvidence_20260805_124737.png`.
- Compile passes. `Saved/Automation/ControlRoom_v041/index.json` passes 3/3 tests with zero warnings, covering CCTV lifecycle, PR-004 authority binding/save and seated/standing constraints.
- v041 is **not promoted**. Active capture evidence `ControlRoomOperatorEvidence_20260805_124610.png` has a readable close PR-004 view but still triggers Unreal's VSM non-Nanite marking-job overflow warning. Resolve the real capture workload before promotion; do not merely suppress the message. Review: `Saved/Audits/ControlRoom/main_control_room_seated_standing_cctv_visual_review_v041.json`.
- Preserve v032/v033 as obsolete/rejected monitor-basis history; preserve v036 black-obstruction images and v037-v039 exposure/shadow experiments as rejected evidence.

## Control-room authored seated view / upright live-CCTV work v032 (2026-08-05, authoritative latest)

- Retain unpromoted `/Game/LineBoss/Maps/LB_MainControlRoom_PR004LiveCCTVAuthoredSeatCandidate_v032` for the next control-room iteration. It inherits the corrected v018 `+12` degree console monitor group, restores the authored fixed seated-camera transform, and keeps a real continuously updating PR-004 SceneCapture feed on a vertical wall plane.
- Fresh actual-game `Saved/Screenshots/WindowsEditor/HighresScreenshot00026.png` passes the console-monitor physical orientation subgate: the visible faces lean down/front toward the seated player, not toward the ceiling. Review: `Saved/Audits/ControlRoom/main_control_room_authored_seat_visual_review_v032.json`.
- Preserve v030/v031 as rejected composition evidence. v030 looked too far upward at the side-wall display; v031 moved the view into the 17.7-degree envelope but exposed obstructing console backs. Neither is promoted.
- v032 is also **not promoted**: the selected live feed needs an explicit zoom/selection presentation and the full Pro-reference/foreground/performance gate remains open. Build audit: `Saved/Audits/ControlRoom/main_control_room_pr004_live_cctv_authored_seat_build_v032.json`.

## Control-room monitor face-normal correction v018 / PR-004 v019 (2026-08-05, authoritative latest)

- User inspection proved v008 still leaned the monitor faces toward the ceiling. The visible source-mesh face is local `-Y`; therefore the prior negative-sign reasoning was reversed.
- Preserve v006/v008 as rejected evidence. Continue from `/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCorrectedCandidate_v018`, which installs preserved v005 `+12` degree Interaction and mothballed screen meshes. Technical audit: `Saved/Audits/ControlRoom/main_control_room_operator_aim_corrected_build_v018.json`; fresh centered game screenshot: `Saved/Screenshots/WindowsEditor/HighresScreenshot00014.png`; visual review: `Saved/Audits/ControlRoom/main_control_room_operator_aim_visual_review_v018.json`.
- v018 passes the physical monitor-orientation sub-gate only and is **not promoted**.
- The control-room PR-004 console now mirrors the proven station-HMI safeguard: its unreliable WidgetComponent render surface is hidden and live authority state is displayed with deterministic TextRender components. The compiled fresh successor is `/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v019`; technical build and close actual-game text visibility pass (`HighresScreenshot00015.png`, `HighresScreenshot00016.png`, `Saved/Audits/ControlRoom/main_control_room_pr004_console_visual_review_v019.json`). Pointer action, state transition, save/authority and final foreground-occlusion gates remain open.
- Retained successor `/Game/LineBoss/Maps/LB_MainControlRoom_PR004ConsoleCandidate_v020` adds the real screen hit surface. The seated pawn's visibility trace routes through the console to the guarded PR-004 authority action. `Saved/Automation/ControlRoom_v020/index.json` passes 2/2 with zero warnings, including packaged-to-unpackaged mutation and Press Shop save-root serialize/load/restore. Runtime before/after images are `HighresScreenshot00016.png` and `HighresScreenshot00017.png`; review is `Saved/Audits/ControlRoom/main_control_room_pr004_pointer_save_runtime_review_v020.json`.
- v020 remains **not promoted** pending foreground-lever composition correction, one real selected Press Shop CCTV feed and the complete fixed-camera Pro-reference gate.

Date: 2026-08-05 (Europe/London)

## Mandatory scope and repository rules

Continue the active objective:

> Complete Line Boss: Car Factory as a detailed, PC-first, release-quality modular 3D car-factory management game in Unreal Engine 5.8. Build and validate the Press Shop one area at a time, beginning with the PR-001–PR-005 front end, and require technical/runtime gates plus fresh fixed-camera visual review before promotion.

- Work only in the canonical Unreal repository:
  `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8`
- Never use OneDrive for project content.
- Preserve the Godot project as read-only reference:
  `C:\Users\greg_\Projects\car factoy mayhem`
- Preserve user-owned and unrelated files.
- Do not promote candidates merely because scripts/imports pass.
- Compare fresh Unreal screenshots against the supplied Pro reference sheets.
- Keep `Docs/PROJECT_HANDOFF.md` current after major decisions or promotion.

## Engine and tools

- Unreal Engine 5.8.1 editor:
  `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor.exe`
- Unreal commandlet:
  `C:\Program Files\Epic Games\UE_5.8\Engine\Binaries\Win64\UnrealEditor-Cmd.exe`
- Blender 5.2:
  `C:\Program Files\Blender Foundation\Blender 5.2\blender.exe`
- Project:
  `C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\LineBossCarFactory.uproject`
- Unreal Python/content commandlets work.
- Native Win64 editor builds are available and pass with Visual Studio 2022 toolchain 14.44.35228 and Windows SDK 10.0.22621.0. The source module is active.
- Screenshot automation is reliable when one map/view is run per editor process. Unreal may return exit code 1 after a successful scripted `QUIT_EDITOR`; confirm the PNG and log rather than treating the process code alone as failure.

## Current accepted baseline

Accepted PR-004 integration baseline:

`/Game/LineBoss/Maps/LB_PressShop_PR004LightingCandidate_v006`

This is not a release-quality station or a full promotion. It is the current best integration baseline because its local lighting is more readable and honest than later experiments.

Fresh v006 evidence:

- `Saved/ValidationScreenshots/PressShopIntegration/v006_pr004_lighting/press_shop_v006_pr004.png`
- `Saved/ValidationScreenshots/PressShopIntegration/v006_pr004_lighting/press_shop_v006_front_end.png`
- `Saved/ValidationScreenshots/PressShopIntegration/v006_pr004_lighting/press_shop_v006_whole.png`
- Audit: `Saved/Audits/press_shop_pr004_lighting_visual_review_v006.json`

## Candidate history and decisions

- v007 material experiment: technical pass, visually too subtle, rejected.
- v008 mothballed-material experiment: washed the robot pale beige/white and had a bad close camera, rejected.
- v009 authored-slot experiment restored source material distinctions such as `EdgeWear`, `WarningLabel`, hydraulic IDs and residue. It exposed that useful source detail had previously been consolidated into generic materials. Not promoted.
- v010 deterministic safety-paint experiment:
  `/Game/LineBoss/Maps/LB_PressShop_PR004SafetyPaintCandidate_v010`
  - 28 robot modules preserved.
  - 13 exact `SafetyOchre`/`SafetyYellow` source slots changed.
  - Technical build passed with zero commandlet errors/warnings.
  - Visual reject: saturated clean orange, flat materials, placeholder-looking PR-003 coils/saddles, sparse/bright cell, not credible seven-year dormant condition.
  - Do not promote v010.

v010 evidence:

- `Saved/ValidationScreenshots/PressShopIntegration/v010_pr004_safety_paint/pr004_v010_detail.png`
- `Saved/ValidationScreenshots/PressShopIntegration/v010_pr004_safety_paint/pr004_v010_cell.png`
- `Saved/ValidationScreenshots/PressShopIntegration/v010_pr004_safety_paint/pr004_v010_front.png`
- `Saved/Audits/press_shop_pr004_safety_paint_candidate_v010.json`
- `Saved/Audits/press_shop_pr004_safety_paint_visual_review_v010.json`

## PR-004 robot source assessment

Blender source:

`SourceAssets/PR004/RoboticDepackRobot/build_pr004_robot_candidate_v002.py`

The robot already has substantial modular geometry: joints, reducer faces, bolt rings, motors, service labels, grease fittings, wear strips, hydraulic IDs, dress packs, tool changer and band/wrap/edge/inspection tools. Do not blindly rebuild it.

The main visible deficiency is authored surface condition and material integration. The earlier Unreal import consolidated Blender material slots too aggressively, hiding authored detail.

Remaining major PR-004 blockers:

- layered aged safety-yellow paint that reads correctly under integrated lighting;
- believable seven-year dust, restrained paint loss, grease and oxidation;
- improved coil/store/saddle materials;
- denser credible cell dressing without obstructing reach, gates or maintenance access;
- release collision (current complex-as-simple setup is not acceptable);
- runtime robot/cradle/coil motion and safety-interlock validation;
- live HMI and production-state integration;
- runtime/save-state verification;
- fresh Pro-reference visual gate.

## Cairnwell Automotive identity authority

Source pack is preserved intact at:

`SourceAssets/ReferencePacks/CAIRNWELL_AUTOMOTIVE_BRAND_IDENTITY_PACK_v1.0/`

Authority:

- Corporation: Cairnwell Automotive
- Site: Moorcross Works
- Vehicle platform: U-Series
- Campaign: The Restart
- Game title: Line Boss: Car Factory
- Diegetic-branding boundary: **Line Boss is the non-diegetic working game
  title, not a corporation or factory brand. It must not appear on robots,
  machinery, buildings, HMI identity plates or other in-world equipment.** Use
  Cairnwell Automotive / Moorcross Works, asset IDs and safety/service markings
  in-world. Any Line Boss wording visible in a Pro reference is layout/art
  guidance only and is not text authority.
- Safety yellow: `#F2C300`, approximate RAL 1023
- Cairnwell green: `#1F4B44`
- Foundry charcoal: `#202428`

Intake audit:

`Saved/Audits/cairnwell_identity_pack_intake_v001.json`

The user has authorized internal project use because Cairnwell was created as a
fictional Pro identity for this game. External trademark/release clearance is a
separate optional business gate and does not affect internal candidate work.

A derived transparent PNG was generated immediately before this handover:

`SourceAssets/Brand/Cairnwell/Textures/T_Cairnwell_PrimaryLogo_2400x640.png`

It was produced from the supplied SVG using Edge headless rendering and visually inspected successfully. It has not yet been imported into Unreal, assigned to a material, placed in a map or promoted. Preserve the SVG as the authority and treat this PNG as a candidate derivative.

## Immediate next work

1. Verify the derived Cairnwell PNG dimensions/alpha/hash and create a brand-asset manifest.
2. Import the logo as a non-destructive Unreal candidate texture under `/Game/LineBoss/Brand/Cairnwell/` with appropriate UI/decal texture settings.
3. Create reusable Cairnwell decal/HMI material candidates; do not scatter branding across the map yet.
4. Build a new PR-004 layered paint candidate from v006/v009 using authoritative RAL 1023 colour, controlled roughness, restrained edge wear/dust and authored detail-slot overrides. Avoid another flat constant-orange material.
5. Capture the exact fixed cameras for detail, cell and front-end views.
6. Inspect against Pro references. Promote only if the station materially improves at the intended management camera and remains believable close up.
7. Then address simple UCX/convex collision and runtime motion/interlock validation.

## Useful scripts and audits

- `Scripts/build_press_shop_pr004_authored_details_candidate_v009.py`
- `Scripts/capture_press_shop_pr004_authored_details_v009.py`
- `Scripts/build_press_shop_pr004_safety_paint_candidate_v010.py`
- `Scripts/capture_press_shop_pr004_safety_paint_v010.py`
- `Scripts/audit_press_shop_pr004_camera_transforms.py`
- `Scripts/audit_press_shop_pr004_robot_material_bindings_v006.py`
- `Saved/Audits/press_shop_pr004_camera_transforms_v006.json`
- `Saved/Audits/press_shop_pr004_robot_material_bindings_v006.json`

## New-chat operating instruction

Read this file completely, then read `Docs/PROJECT_HANDOFF.md`. Inspect current files and evidence before acting. Resume from the accepted v006 baseline and current unpromoted branding/material candidates. Do not restart the project, do not migrate back to Godot, and do not claim PR-004 is finished until collision, runtime behaviour and fresh fixed-camera visual gates all pass.

## 2026-08-03 autonomous-robot continuation addendum

- The BIOS 3201 and microcode 0x12F firmware gate passed after defaults were
  loaded. DDR5 remains at the safe 4800 MHz default. MemTest86 is still planned
  for tonight; Unreal content work has resumed without changing any asset
  promotion decision.
- All known Pro robot/reference packs are preserved and verified in the
  canonical repository. Inventory:
  `Saved/Audits/pro_reference_pack_inventory_2026-08-03.json`.
- The reusable RP01 data-only Pawn candidate is
  `/Game/LineBoss/Robots/Shared/RP01/Candidate_v001/Blueprints/BP_LB_RP01_MobileBase`.
  Its hierarchy/type/reload commandlet gate passed, but it has zero simple
  collision and no runtime, save, navigation, docking or fixed-camera visual
  acceptance. It is not promoted.
- CR01 Blender Candidate v040 has improved the rounded enclosure and seated
  Cairnwell plate, but materials, condition, several carrier/null stages,
  deployed-cleaning proof, Unreal collision/runtime and Pro-reference cameras
  remain open. MR01 Phase 2 v006 is mechanism evidence only and remains visibly
  far below the Pro sheet; its J2/J3 packaging offsets and derived outrigger
  foot yaw are not approved authority changes.
- The first staged native robot runtime draft under
  `Source/LineBossCarFactory/LBSupportRobot*`, `LBCleaningAMR*` and
  `LBMaintenanceAMR*` is rejected and dormant. Independent review found
  forgeable route/dock proof, unsafe SaveGame restoration, deadlocked fault
  clearing, incomplete dynamic interlocks and authority mismatches. Audit:
  `Saved/Audits/support_robot_runtime_source_v001.json`, status
  `SOURCE_CONTRACT_REJECTED__SAFETY_ARCHITECTURE_SUPERSEDED`.
- Do not register that source module or reparent the accepted RP01 Pawn. The
  replacement direction is a disabled-by-default, Pawn-attached runtime
  component which resolves canonical anchors by stable names/tags and obtains
  route/dock authority from trusted world services. It must restore stopped,
  clear tasks/permits/sensor proof, reject non-finite input and never blindly
  teleport from a save.
- The `.uproject` intentionally still has no native Modules array. MSVC and a
  supported Windows SDK remain absent; install them only with explicit user
  approval, then run isolated UHT/compile gates before enabling native code.
- CR01 and RP01 use the authoritative shared warning-audio socket at Z=850 mm.
  The MR01 pack also labels a Z=950 mm value exact-shared; do not silently move
  the shared anchor. Record and resolve that authority conflict explicitly.

### 2026-08-03 robot source and shared-material decisions

- CR01 Candidate v042 is preserved as a technically coherent payload-only
  source/export candidate, not a production visual pass. Its 24 FBXs contain
  M07-M25 only and zero RP01 shared duplication. The live arm/lift/spin
  hierarchy and nominal 1,350 mm deployed swept diameter are useful for an
  isolated Unreal import, but the published +/-65 degree arm range only stows
  to 1,252.6377 mm, failing the 980 +/-5 mm travel-width gate. The apparent
  1,350 mm snapshot also changes with the sparse brush's spin phase; Unreal
  must validate the full rotational swept disc. Independent verdict: REWORK,
  technical-import-only, no promotion. Candidate v043 is being developed with
  an inboard stow carrier, denser cleaning hardware and missing M20/M25 source
  geometry while preserving the arm authority.
- MR01 Candidate v012 has a sound dimensional/rig foundation but remains a
  visual REWORK. The arm, outriggers, mast, cradle, tools and hidden carousel
  are not yet production-believable against the Pro sheet, and Cairnwell is
  crossed by the plate trim. There is no deterministic Candidate_v012 FBX/GLB
  export; do not run the pack's unversioned production-path import starter.
  Export and hash an isolated candidate first, then import only to a candidate
  namespace.
- Shared Surface Forge robot-paint Candidate v001 is rejected despite its
  earlier scalar/dependency audit. Fresh D3D12 evidence proved that Unreal used
  its fallback material: the three Surface Forge textures needed virtual
  samplers and three OneMinus nodes had invalid named inputs. Corrected
  Candidate v002 compiles without those errors. Fresh neutral-light v003
  swatches distinguish charcoal, Cairnwell green, safety yellow, service grey,
  mothballed and restored states. The texture reads too coarse on small test
  forms, so robot-panel tuning and fixed-camera Pro comparison remain open.
  Evidence:
  `Saved/Audits/lb_support_robot_shared_materials_candidate_v002_visual_review.json`.
- Neither robot nor the shared material family is promoted. The accepted
  PR-004 integration baseline remains v006.

## 2026-08-03 - Robot v043/v013 source gates and runtime v2c4 continuation

- The active development goal was renewed. Work continues only in this
  canonical non-OneDrive Unreal repository from the accepted PR-004 v006
  integration baseline. Rejected PR-004 v007-v010 candidates remain rejected.
- CR01 Candidate v043 is preserved at
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v043/LB_CR01_ProductionSource_v043.blend`
  with SHA-256
  `AF633C0E228813E93F3DD3CE7D6DA4C140366DB38C1B5D9F4C5A3732416ABFC3`.
  Its deterministic payload-only export, hierarchy, UV/material assignment,
  45 L hopper, filter geometry, 980 +/-5 mm stowed-width gate and analytic
  1,350 mm cleaning sweep pass the source engineering gate. Independent visual
  review remains **REWORK / NOT PROMOTED**: enclosure and sensor forms are too
  blocky, materials are flat, panel/service detail is weak, cleaning hardware
  is poorly exposed in the evidence cameras and stow/deploy readability is not
  release quality. Do not import v043 into Unreal until a better source visual
  candidate passes Pro-reference review.
- MR01 Candidate v013 is preserved at
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Blender/Candidate_v013/LB_MR01_RuggedExportCandidate_v013.blend`
  with SHA-256
  `BD66622C80A16ECEAF8B2E8B82DB53E3A690FC9A7EB2DBB286573FADF57617E9`.
  Its source, clean-reimport and deterministic export checks pass. The supplied
  MR01 packs contain no alternate design sheet: every retained MR01 sheet is
  byte-identical, SHA-256
  `A5860F7C4BD12387AE7D66EF45F3E9D2C1D1150020B83FB426CA4A6B292CCD02`.
  The higher-authority engineering files require exactly four independently
  driven corner modules. v013 satisfies that authority with four shared RP01
  wheel/hub instances at X +/-500 mm and Y +/-405 mm; no wheel-layout redesign
  is authorized or required. MR-local guards and mounting brackets remain
  permissible payload geometry.
- MR01 v013 nevertheless remains **VISUAL REWORK / NOT PROMOTED**. Compared
  with the Pro reference, its chassis and upper works remain boxy, the working
  arm is buried too low and reads undersized inside bulky casing, mast/camera/light forms are primitive, bumpers and
  wheel pods are visually oversized, rear/service detail is weak, tools are
  generic, and the mothballed state is a broad tint rather than layered
  seven-year condition. The source engineering pass and four-wheel authority
  pass must never be treated as visual acceptance.
- Visual review record:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v013/LB_MR01_RuggedExportCandidate_v013_VISUAL_REVIEW.json`.
  Neither v043 nor v013 has Unreal import, collision, navigation, runtime,
  save-state or fixed-camera Unreal acceptance.
- Visual Studio Build Tools 2022 17.14.37, MSVC 14.44.35228, Windows SDK
  10.0.22621 and the required .NET Framework targeting components are now
  installed. The earlier statement that the native toolchain was absent is
  superseded.
- Disabled plugin `Plugins/LineBossSupportRobotsRuntimeV002` passed isolated
  UHT plus UnrealEditor Development, UnrealGame Development and UnrealGame
  Shipping builds in strict no-unity/no-shared-PCH package `B/V2C4`. Evidence:
  `Saved/Audits/lb_support_robot_runtime_v002_build_v2c4.json` and
  `Saved/Audits/lb_support_robot_runtime_v002_source_audit.json`. This is a
  compile/source-contract pass only. The plugin remains disabled by default,
  is absent from the `.uproject`, and is not promoted.
- Runtime v2c4 closes the prior caller-forgeable actor/world, unsafe speed,
  overlapping arm-command and tool-inventory loopholes. Open gates still
  include production route/dock/safety/cleaning-process providers, trusted
  cleaning resource/coverage progression, provider-owned task-mode authority,
  MR exceptional 180-degree parking proof, canonical Blueprint binding,
  runtime movement/navigation, simple collision, fault injection, disk save
  round-trip and fresh fixed-camera Unreal evidence.
- BIOS 3201/microcode 0x12F remains a passed firmware gate. MemTest86 is still
  planned as an overnight hardware check and does not block source-content
  development or alter any promotion decision.

### MR01 Candidate v014 source visual branch

- Candidate v014 is preserved at
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Blender/Candidate_v014/LB_MR01_VisualReworkCandidate_v014.blend`,
  SHA-256
  `F519927D3B31AC1B746A2B77C5D43CA985782718B0BD501B21BC39342F3143D9`.
  Independent continuity audit passes: exactly four shared RP01 wheels, exactly
  four shared RP01 hubs, unchanged linked geometry/transforms, Cairnwell present
  and no diegetic working-title text. Evidence:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v014/LB_MR01_VisualReworkCandidate_v014_INDEPENDENT_AUDIT.json`.
- v014 reduces the oversized local wheel guards and bumper section, adds a
  protected three-lens mast head, front sensor fascia, service doors/louvres and
  rear service hardware, and removes the strongest uniform procedural bump.
  Fresh Blender evidence is in `Validation/Candidate_v014`.
- Manual Pro comparison is still **REWORK / NOT PROMOTED / NO UNREAL IMPORT**.
  The working arm is too low and visually undersized while its surrounding
  casing makes the package look triangular; the upper rear enclosure is
  slab-sided, perimeter protection is still too rail-like, local wheel-module
  integration and rear detail need refinement, and no new seven-year condition
  proof exists. Continue by exposing/strengthening the arm within the fixed
  1,800 mm reach and 1,250 mm travel envelope and integrating the body around it.

## 2026-08-03 - CR01 v044-v048 visual branches and runtime v2c5

- CR01 v044-v048 are source-only visual branches descended from the technically
  coherent v043 cleaner. v044 replaces the toy-like green nose emphasis with a
  graphite/yellow industrial enclosure, protected sensor/light face, guarded
  roof LiDAR, clearer service hardware and Cairnwell / CR01-001 identity. v045
  through v048 refine front and side cleaning brushes while correcting the
  added exterior back inside the authoritative travel envelope.
- Latest source is
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Blender/Candidate_v048/LB_CR01_TaperedBrushCandidate_v048.blend`,
  SHA-256
  `22167D94D1A43C194797FDD4018DE7BF850131C0DF158BB91F9002058DE85B08`.
  Its build audit confirms unchanged linked RP01 inventory and published pivots,
  984.64 mm stowed width, exact +/-760 mm length authority, Z max 1120 mm,
  1349.207 mm deployed sweep, 36 tapered bundles per side and an unchanged
  front-roller geometry envelope. Evidence is under `Validation/Candidate_v048`.
- Manual comparison against the Pro sheet remains **REWORK / NOT PROMOTED / NO
  UNREAL IMPORT**. The enclosure, branding, sensing and service presentation are
  materially improved, and v046's detached fibres are removed. Remaining gaps
  are overly rigid/even side fibres, a perfectly smooth front-roller silhouette
  and enclosure/bumper surfacing still simplified against Pro. Continue from
  v048; do not promote v044-v047.
- Disabled runtime package `B/V2C5` passes UHT, UnrealEditor Development,
  UnrealGame Development and UnrealGame Shipping with strict includes, no PCH,
  no shared PCH and unity disabled. Evidence:
  `Saved/Audits/lb_support_robot_runtime_v002_build_v2c5.json` and
  `Saved/Audits/lb_support_robot_runtime_v002_source_audit.json`.
- v2c5 adds provider-owned CR cleaning task grants and monotonic measured
  process samples for mode, coverage, water, recovery, hopper and wear. Replay,
  non-finite, capacity and speed/swath-implausible samples safe-stop with a
  process-authority fault. This is still compile/source-contract proof only:
  no production provider is registered, the plugin remains disabled and none
  of the Unreal runtime, save, collision, navigation or visual gates are closed.

## 2026-08-03 - CR01 v052 isolated import and v053 corrected RP01 integration

- CR01 v052 is the current deterministic export payload: 24 modular FBXs under
  `SourceAssets/Robots/LB_CR01_CleaningAMR/Exports/Candidate_v052_PayloadRig`.
  Its factory-empty Blender reimport audit passes hashes, timestamps, UV0,
  materials, hierarchy stages and absence of empties/shared meshes. This
  authorized isolated Unreal evaluation only; it did not authorize promotion.
- The isolated v052 Unreal build passed import, Blueprint assembly and shared
  material-binding checks. It has three blocking body collision proxies plus
  five non-blocking cleaning-query volumes. The first fresh fixed-camera Unreal
  review rejected it because the inherited RP01 wheel, caster and dock visuals
  were double-offset, the pale lower platform clipped badly, Cairnwell identity
  was not reliably legible and the result did not meet the Pro reference.
- The reusable RP01 fault was corrected non-destructively in
  `/Game/LineBoss/Robots/Shared/RP01/Candidate_v002/Blueprints/BP_LB_RP01_MobileBase`;
  v001 remains preserved. CR01 v053 composes the unchanged v052 payload and
  collision set over that corrected parent at
  `/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v053/Blueprints/BP_LB_CR01_CleaningAMR_v053`.
- Fresh reload/compile technical checks pass for v053 and its fixed-camera
  images show the reusable running gear is now aligned and the lower platform
  is better integrated. The visual decision remains **REWORK / NOT PROMOTED**:
  Cairnwell/CR01 markings are not readable enough, the Surface Forge response
  is too coarse at robot scale, pale bumper/roof/wheel-centre values dominate,
  the body remains slab-sided/top-heavy against Pro, mothballed/restored states
  are insufficiently distinct, and deployed-swath/runtime/navigation/save proof
  remains open.
- Authoritative evidence is in
  `Saved/Audits/lb_cr01_candidate_v052_unreal_visual_review.json`,
  `Saved/Audits/lb_rp01_mobile_base_candidate_v002_build.json`,
  `Saved/Audits/lb_cr01_candidate_v053_unreal_technical_independent.json`,
  `Saved/Audits/lb_cr01_candidate_v053_unreal_visual_review.json` and
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v053_CorrectedParentVisual`.
  Continue from v053; do not promote v052. The accepted PR-004 v006 map and the
  disabled runtime-plugin posture remain unchanged.

## 2026-08-03 - CR01 v054-v056 Unreal material and identity correction

- CR01 v054 replaces the robot-scale coarse/dimpled shared paint with reusable
  Candidate v003 material instances: 18x texture scale, 0.055 normal strength,
  restrained roughness variation and separate restored/mothballed palettes.
  RP01 v003 preserves the v002 anchor correction and darkens running-gear steel.
- Fresh v054 cameras proved the material response improvement but also proved
  that the authored joined-FBX Cairnwell lettering was depth-occluded in Unreal.
  CR01 v055 fixes that non-destructively with two physical green identity plates
  and diegetic `CAIRNWELL`, `CR-01 001` and `MOORCROSS WORKS` text components at
  the authoritative Blender carrier coordinates. No `Line Boss` world branding
  was added.
- CR01 v056 separates structural warm-white/brushed/carrier/wear steel from the
  plaque lettering and binds those 20 slots to restrained service grey. Fresh
  reload/compile audit passes with 24 preserved payload meshes, 19 child stages,
  47 inherited RP01 visuals, 96 effective material slots and 58 Candidate v003
  bindings.
- Six fresh 1920x1080 fixed-camera screenshots are under
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v056_TrimHierarchyVisual`.
  Manual Pro review accepts the v056 material/identity direction for continued
  development but does **not** promote it: the full-width front impact bar is
  still too pale, the enclosure remains somewhat simplified/slab-sided and the
  deployed cleaning, navigation and save gates remain open.
- Per user direction, keep CR01 faults light and player-readable (low battery,
  blocked brush/obstacle, tank or hopper full, needs service). Detailed fault
  simulation is reserved for press-shop production machinery.
- Evidence:
  `Saved/Audits/lb_cr01_candidate_v054_release_materials_build.json`,
  `Saved/Audits/lb_cr01_candidate_v055_identity_plaques_build.json`,
  `Saved/Audits/lb_cr01_candidate_v056_trim_hierarchy_build.json`,
  `Saved/Audits/lb_cr01_candidate_v056_unreal_technical_independent.json`,
  `Saved/Audits/lb_cr01_v056_trim_hierarchy_capture.json` and
  `Saved/Audits/lb_cr01_candidate_v056_unreal_visual_review.json`.
  Continue from v056; v054/v055 are preserved stepping stones. PR-004 v006 was
  not modified and the native support-robot plugin remains disabled.

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

## 2026-08-03 - CR01 v063 branded scrubber functional gate

- CR01 v059 replaces the v058 truck-like enclosure non-destructively with a
  rounded, continuous scrubber silhouette while preserving the 24-part modular
  payload, RP01 anchors and moving cleaning pivots. Clean Blender reimport and
  isolated Unreal import gates pass. v060 restores the layered material system,
  v062 restores two-sided native Cairnwell identity plates, and v063 is the
  newest C++ functional-authority wrapper.
- Current asset:
  `/Game/LineBoss/Robots/Cleaning/CR01/Candidate_v063/Blueprints/BP_LB_CR01_CleaningAMR_v063`.
  Final UE automation passes with zero enabled presentation blockers, one swept
  RP01 collision authority, certified movement, obstacle stop at X=143.394 cm,
  Blocked state plus route revocation, deployed cleaning gear, and safe
  save/reload behaviour. Evidence:
  `Saved/Automation/CR01_v063_final/index.json` and
  `Saved/Audits/lb_cr01_candidate_v063_functional_runtime_gate.json`.
- Six fresh fixed-camera screenshots are under
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v063_FunctionalAuthority`.
  The rounded enclosure, dark impact beam, cleaning-tool grounding and readable
  `CAIRNWELL / CR-01 001 / MOORCROSS WORKS` identity pass. No diegetic Line Boss
  wording is present.
- v063 is **FUNCTIONAL INTEGRATION PASS / VISUAL POLISH HOLD / NOT PROMOTED**.
  The mothballed state is too clean, the upper sensor/roof treatment needs a
  focused material/detail pass, and accepted PR-004 v006 in-factory fixed-camera
  proof remains open. See
  `Saved/Audits/lb_cr01_candidate_v063_unreal_visual_review.json`.
- Cleaner gameplay remains intentionally light: normal operation, low battery,
  blocked obstacle/brush, tank or hopper full and needs service. Detailed fault
  diagnosis and repair depth is reserved for production machinery.
- v059-v063 remain isolated candidates. Do not promote them yet. PR-004 v006 was
  not modified and `Plugins/LineBossSupportRobotsRuntimeV002` remains disabled.

## 2026-08-03 - CR01 v065 accepted-lighting proof and scope decision

- v064 adds a reusable Candidate v004 material family with stronger dormant
  wear, restrained restored values and 83 semantic bindings without changing
  the 24-part geometry, pivots, RP01 relationship or Cairnwell identity plates.
  v065 wraps v064 in the existing project-module functional authority.
- Full UE 5.8.1 editor build and
  `LineBoss.SupportRobots.CR01.FunctionalRuntime` pass. The test again proves
  zero enabled presentation blockers, one `RP01_CollisionRoot`, obstacle stop at
  X=143.394 cm, Blocked state/route revocation, deployed cleaning equipment and
  safe save/reload. Evidence:
  `Saved/Automation/CR01_v065_final/index.json` and
  `Saved/Audits/lb_cr01_candidate_v065_functional_runtime_gate.json`.
- Six clean-stage cameras and four additional cameras in an isolated duplicate
  of accepted PR-004 v006 were freshly rendered and manually compared with the
  Pro sheet. Factory proof is under
  `Saved/ValidationScreenshots/SupportRobots/CR01/Candidate_v065_PR004Lighting`;
  the accepted map itself was not modified.
- Factory proof passes scale, grounding, cleaning-tool readability, rounded
  scrubber silhouette, Cairnwell / CR-01 001 / Moorcross Works identity and no
  Line Boss in-world branding. It also confirms a remaining release-quality
  gap: the front sensor/fascia and roof service hardware are still too blocky,
  and seven-year dormant wear needs authored masks or geometry.
- v065 status is **FUNCTIONAL REUSABLE CANDIDATE PASS / VISUAL GEOMETRY HOLD /
  NOT PROMOTED**. See
  `Saved/Audits/lb_cr01_candidate_v065_fixed_camera_visual_review.json`.
- Per user direction, do not deepen cleaner fault simulation. Keep only low
  battery, blocked obstacle/brush, tank or hopper full and needs service. Put
  detailed fault/repair design effort into production machinery. Resume the
  four-corner-wheel MR-01 while preserving v065 for later focused art refinement.
- The accepted PR-004 v006 map remains unchanged and the separate support-robot
  runtime plugin remains disabled.

## 2026-08-03 - MR01 v015 arm-exposure source authority

- Current filesystem evidence showed v014 already preserved exactly four
  independently driven RP01-linked corner wheels and four matching hubs, but
  its working arm remained buried below an over-tall upper deck. v014 therefore
  remains source-only **REWORK / NOT IMPORTED / NOT PROMOTED**.
- v015 is at
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Blender/Candidate_v015/LB_MR01_ArmExposureCandidate_v015.blend`.
  It lowers only the false upper skin/coamings and rear crown, reseats the arm
  cradle, and strengthens the arm laterally from 272.0 to 331.8 mm. It does not
  move any arm bone, change forward reach, alter the vertical envelope, move the
  TCP or change the shared four-wheel layout.
- Independent source audit passes exactly four wheels, four hubs, unchanged
  linked RP01 mesh libraries/coordinates/dimensions, unchanged authoritative
  arm bones and heads, 86 mm visible shoulder clearance above the corrected
  deck, Cairnwell identity and no Line Boss diegetic wording. Evidence:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v015/LB_MR01_ArmExposureCandidate_v015_INDEPENDENT_AUDIT.json`.
- Four fresh Blender renders were manually compared with the Pro sheet. The arm
  is now readable as a substantial 25 kg maintenance manipulator and the body is
  less slab-sided. v015 is **ACCEPTED FOR ISOLATED UNREAL TECHNICAL EXPORT AND
  IMPORT / NOT PROMOTED**. Straight bumper rails, wheel-pod integration, Unreal
  materials/ageing, articulation, collision, navigation, authority and save
  gates remain open. See the v015 visual-review JSON beside the audit.
- Next export v015 without embedding or duplicating the RP01 wheels/hubs, build
  an isolated Unreal candidate, and require fresh fixed cameras before any
  promotion. Keep the separate runtime plugin disabled.

## 2026-08-03 - Current MR01 authority is connected-lift v020

- Do not use the v017 horizontal full-lift render as acceptance evidence. The
  user identified a real visible disconnect: the arm lift bone moved 400 mm but
  its static carriage did not. v017's source geometry and reach calculations
  remain useful, but that render/state is rejected.
- v018 and its Unreal namespace are rejected for an eleven-bone import after
  joining the flexible services; v017 imported 25 false bones. v019 proves the
  correct Unreal FBX hierarchy with exactly ten bones and is retained only as a
  technical stepping stone.
- Current source/import candidate is v020:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Blender/Candidate_v020/LB_MR01_ConnectedLiftCandidate_v020.blend`
  and `/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v020`.
- v020 adds a nested moving sleeve. At full 400 mm extension the fixed guide,
  half-stroke sleeve and full-stroke carriage retain 199.0 mm and 36.5 mm
  positive overlaps. T6 is visibly attached to the authoritative coupler and
  its carousel instance is hidden in the equipped proof. Corrected image:
  `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Validation/Candidate_v020/lb_mr01_v020_t6_connected_full_lift_machine_reach.png`.
- Clean Blender reimport and strict UE 5.8 import pass: 354 static meshes, one
  skeletal arm, one skeleton, exactly ten bones, carousel plus T1-T8, and no
  duplicated RP01 wheels/hubs. Audit:
  `Saved/Audits/lb_mr01_candidate_v020_unreal_import.json`.
- Status is **SOURCE VISUAL CORRECTION PASS / ISOLATED UNREAL IMPORT PASS /
  NOT PROMOTED**. Next build the reusable MR01 actor using the shared RP01
  authority, synchronize sleeve/carriage/arm animation, implement T6's exclusive
  stored/equipped state, then run runtime, collision/save and fresh isolated plus
  PR-004-lighting fixed-camera gates. Accepted PR-004 v006 remains untouched.

## 2026-08-03 - Current reusable MR01 candidate is v021

- Reusable Blueprint:
  `/Game/LineBoss/Robots/Maintenance/MR01/Candidate_v021/Blueprints/BP_LB_MR01_MaintenanceAMR_v021`.
- Parent is native `ALBMaintenanceAMR`; it contains 345 v020 payload meshes,
  one ten-bone poseable arm, four independent corner drive modules referencing
  shared RP01 assets, carousel, T1-T8 stored visuals and T1-T8 equipped visuals.
- Runtime visual groups use `LB.MR01.AttachTo.<contract>` tags. Native BeginPlay
  attaches them to the otherwise Python-inaccessible C++ wheel/outrigger/mast/
  door/drawer/tool-rack pivots with world transforms preserved. Do not replace
  this with duplicate Blueprint pivots.
- Native C++ compiles and the assembly audit passes:
  `Saved/Audits/lb_mr01_candidate_v021_reusable_authority_build.json`.
- v021 is **BUILT / NOT PROMOTED**. Next perform a fresh-process structural
  audit, game-world arm/lift/T6 and save/restore automation, collision/navigation
  checks, then fresh fixed-camera Unreal screenshots and Pro comparison.

## 2026-08-03 - MR01 v021 paused on visual hold; finish full Press Shop first

- Fresh structural audit passes:
  `Saved/Audits/lb_mr01_candidate_v021_reusable_authority_fresh_audit.json`.
- Full native functional automation passes:
  `Saved/Automation/MR01_v021_r5/index.json`. This covers four shared-RP01
  corner modules, native-pivot rebinding, T6 coupler state, synchronized
  400/200/400 mm arm/sleeve/carriage lift, save/restore, collision envelope,
  navigation relevance and swept obstacle stop.
- First Unreal camera is rejected:
  `Saved/ValidationScreenshots/SupportRobots/MR01/Candidate_v021/lb_mr01_v021_stowed_oblique.png`.
  Wheels are bright default material, the arm is not visually stowed, another
  instance enters frame and staging is weak. Do not promote v021.
- `Scripts/repair_lb_mr01_v021_visual_gate_v002.py` was authored but failed to
  launch and made no authoritative change. Resume it only after the Press Shop.
- Latest user priority overrides earlier robot sequencing: complete PR-001 to
  PR-010, four press trains and every Press Shop support area before returning
  to CR01 or MR01 visual work.
# PR-004 v020 fresh visual gate (2026-08-03, latest)

- Captures: `Saved/ValidationScreenshots/PressShopIntegration/v020_pr004_surfaceforge_robot/` (detail, cell, front).
- Capture gate: PASS. Visual gate: FAIL.
- Reasons: uncontrolled bright yellow/orange/coarse close finish, mirrored PR004-RBT-01 plate from the audited side, no meaningful management-distance improvement over v006, and major Pro-reference cell systems still visually absent or provisional.
- Keep v020 unpromoted. Continue from accepted v006 for the next PR-004 cell-systems candidate; do not promote rejected v007-v010.
- Audit: `Saved/Audits/press_shop_pr004_surfaceforge_robot_visual_gate_v020.json`.
# PR-004 native runtime/save gates (2026-08-03, latest)

- Added `Source/LineBossCarFactory/LBPR004StationTests.cpp` and request-token state getters in `LBPR004Station.h`.
- UE 5.8 editor target builds successfully with VS 14.44 / Windows SDK 10.0.22621.0.
- Fresh automation: `Saved/Automation/PR004_r2/index.json` = **2 pass, 0 fail**.
- Gate covers commissioning/interlocks, securing-motion safety fault/recovery, power-loss ownership reconciliation, stable save round-trip and invalid save rejection.
- Do not overclaim: full-map binding, HMI presentation, collision/navigation, performance and fresh promoted visual evidence remain open.
# Bare-coil front-end v021 gate (2026-08-03, latest)

- v021 map derives directly from accepted v006 and replaces 14 obsolete wrapped coils across PR-001/002/003 with the accepted bare-coil geometry.
- Technical: 8 convex hulls, default collision trace, exact saddle contact retention, fresh three-camera capture pass.
- Visual: HOLD / not promoted. The inherited coil material is too dark and flat to read as wound steel.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/v021_bare_coil_front_end/`.
- Audits: `Saved/Audits/press_shop_bare_coil_front_end_candidate_v021.json`, `Saved/Audits/press_shop_bare_coil_front_end_visual_gate_v021.json`.
# Wound-steel material v022 gate (2026-08-03, latest)

- v022 applies a procedural metallic wound-steel treatment to all 15 visible bare coils.
- Build/capture pass; visual gate fails because the front-end lighting/reflection environment keeps the coils too dark and v022 is not materially better than v021.
- Keep v022 unpromoted. Next candidate must change coil material and local lighting/reflection together.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/v022_wound_steel/`; audits in `Saved/Audits/press_shop_wound_steel_candidate_v022.json` and `press_shop_wound_steel_visual_gate_v022.json`.

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

- Native `ALBPR004Station` now owns reusable wrapped and bare coil presentation components. `UpdateCoilPresentation()` changes visibility and click collision from saveable station authority after load, Unpackage, restore and handoff reset.
- Fresh `Saved/Automation/PR004_r4/index.json` passes all three PR-004 tests, including wrapped-to-bare visibility and restored-state presentation assertions.
- v024's cosmetic stand coil was replaced with native actor `LB_INT_PR004_V024_InteractiveUnpackageStation`; binding audit: `Saved/Audits/press_shop_pr004_interactive_coil_binding_v024.json`.
- Current isolated map is `/Game/LineBoss/Maps/LB_PressShop_PR004InteractiveFloorCandidate_v025`. It adds only a compact 5.2 x 6.2 m stand boundary, 4.2 x 1.7 m operator pad and 2.0 m transfer lane toward PR-005. All markings are non-colliding and navigation-irrelevant. The rest of the Press Shop floor was preserved.
- Fresh fixed cameras under `Saved/ValidationScreenshots/PressShopIntegration/v025_pr004_interactive_floor/` prove packaged inventory, the packaged PR-004 stand state and the native unpackaged replacement state.
- Visual decision: **DIRECTION PASS / POLISH AND RUNTIME GATES OPEN / NOT PROMOTED**. Packaging is too uniform, the operator pad reads too dark/brown, paint is too pristine, and player-visible click/HMI plus full PIE/navigation/disk-save proof remain open.
- Audit: `Saved/Audits/press_shop_pr004_interactive_floor_visual_gate_v025.json`.

# PR-004 packaged-coil/HMI/navigation candidate v026 (2026-08-03, latest)

- Active isolated candidate is `/Game/LineBoss/Maps/LB_PressShop_PR004PackagingPolishCandidate_v026`, still derived from the accepted v006 lineage. Accepted baseline remains v006; rejected v007-v010 remain rejected. **v026 is not promoted.**
- All PR-001/PR-002/PR-003 inventory remains packaged. PR-004 presents one labelled Cairnwell packaged coil on the powered preparation cradle; the native player interaction changes only that coil to the bare PR-005 handoff state.
- A compact diegetic touchscreen now shows Cairnwell Automotive / Moorcross Works, PR-004 Coil Preparation, live authority state, coil ID, recipe/interlock checklist and `UNPACKAGE COIL`. The failed command-line WidgetComponent render surface is hidden but retained as the query-only click target/widget host; native TextRender is the deterministic visible screen layer over the physical black face. No Line Boss working-title branding is visible.
- The operator pad, stand boundary and PR-005 transfer lane have no collision and do not affect navigation. Physical waste bins and HMI supports retain collision. The HMI click target remains query-collidable and its text cannot block cursor traces.
- A 22 x 20 x 7 m local navigation volume and reusable native `ALBPressShopNavigationBootstrap` are present. Fresh PIE evidence generates a valid, complete 1396.95 cm route with five path points: `Saved/Audits/press_shop_pr004_navigation_runtime_v026.json`. Combined gate: `Saved/Audits/press_shop_pr004_collision_navigation_v026.json` = **COLLISION_AND_RUNTIME_NAVIGATION_PASS / NOT PROMOTED**.
- Fresh native editor build succeeds. `Saved/Automation/PR004_r11/index.json` = **3 succeeded, 0 failed**, covering commissioning/interlocks, the actual `ALBManagementPawn` player interaction route and stable authority/save presentation round-trip.
- Fresh fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/v026_pr004_packaging_polish/`. The latest runtime HMI proof is `press_shop_v026_pr004_hmi_pie.png`; the checkerboard fallback is gone and the live Cairnwell display is visible. Visual review still holds promotion for final material ageing/lighting judgment, crane runtime motion/load transfer, broader authority/import gates and disk-level game SaveGame proof.
- Machine-design coverage after PR-004: PR-005 has dimensioned modular production assets, moving assemblies, HMI/gameplay/audio contracts and is build-ready. PR-006 leveller, PR-007 washer/lube, PR-008 servo-feed/cut/pre-punch, PR-009 stacker, PR-010 four-lane blank store and all four press trains have authoritative process roles, footprints/layout coordinates, buffers, safety/service zones and control requirements, but do not yet have PR-005-level final detailed CAD for every machine. Build those as modular production designs and require fresh fixed-camera Pro-reference comparison before promotion.

# PR-004 native crane v027/v028 checkpoint (2026-08-03, latest)

- `ALBBridgeCraneController` now provides reusable tagged bridge/trolley/hoist/C-hook authority with route/personnel/gate and control-power fail-stop, named recovery, in-flight save/restore, rigid packaged-coil/label ownership and PR-004 deposit. The padded C-hook lower arm now remains 59 cm below the hook datum so it enters the bore instead of carrying the coil at a visibly disconnected datum.
- v027 proved the real CS-10 packaged coil transfer end to end. The latest isolated visual candidate is `/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v028`; it remains **NOT PROMOTED** and does not replace accepted v006.
- User visual review correctly identified that the inherited crane bridge was only one 4.5 m module and did not span the runway. v028 replaces it with two 40 t girders assembled from 28 exact 443.57 cm modules plus eight cross-ties across the full 6210 cm end-truck span. The secondary 30 t single-girder crane is also corrected with fourteen full-span modules.
- Fresh UE build passes. `Saved/Automation/PR004_r13/index.json` = **4 pass, 0 fail**, including the bore-engagement assertion. `Saved/Audits/press_shop_pr004_crane_runtime_v028.json` = **RUNTIME_CRANE_TRANSFER_PASS / NOT PROMOTED**, with all phases visited, exact `MCX-U-CS10-0001` deposit and 0 cm native load/attachment follow error.
- Fresh navigation remains valid/non-partial at 1396.95 cm. `Saved/Audits/press_shop_pr004_collision_navigation_v028.json` = **COLLISION_AND_RUNTIME_NAVIGATION_PASS / NOT PROMOTED**; all 44 added roof/wall/cross-tie visual-context primitives serialize as NoCollision and navigation-irrelevant.
- Fresh fixed PIE captures are in `Saved/ValidationScreenshots/PressShopIntegration/v028_pr004_crane_runtime/`, including frontal and oblique full-span views, live C-hook engagement and completed deposit. A bridge-owned `CAIRNWELL AUTOMOTIVE / CR-40-01 / SWL 40 t` identity plate now travels with the crane. `Saved/Audits/press_shop_pr004_crane_visual_gate_v028.json` deliberately records **FAIL / REWORK REQUIRED / PROMOTION FORBIDDEN**. Full width and C-hook geometry pass, but final bridge fabrication hierarchy/material wear, festoon/trolley detail, wrapped-coil fibre/wrinkles/label contrast, lighting balance and a completely unobstructed span camera remain open. Only the 40 t crane has native transfer authority; the corrected 30 t crane is geometry-only for now.

# PR-004 packaged crane load v029/v030 checkpoint (2026-08-03, latest)

- Built reusable packaged-coil source v004 from the detailed v003 render mesh: exact 1499.8 x 1900 x 1900 mm bounds, 78,656 render triangles, ten controlled material slots, twelve authored convex UCX ring segments and a 640 mm collision bore. UE 5.8 Interchange merged authored UCX into render geometry, so the accepted candidate import deliberately uses the still-supported legacy FBX static-mesh factory with exact post-import scale and convex-count gates. Failed 1.5 cm and 150 m import variants remain quarantined and unused.
- Current isolated maps are `/Game/LineBoss/Maps/LB_PressShop_PR004CraneLoadCandidate_v029` and visual rework `/Game/LineBoss/Maps/LB_PressShop_PR004CraneVisualCandidate_v030`. Both remain **NOT PROMOTED**; accepted baseline remains v006 and rejected v007-v010 remain rejected.
- All fifteen packaged-coil presentations now use the correct 1.50 m wide / 1.90 m OD asset with layered wrap faces, overlap collars, radial bands, buckles, compressed-fibre edge protectors, repair patches and labels. The Cairnwell plate was moved off the bore. The real CS-10 load and its three Cairnwell attachment actors still transfer rigidly.
- `Saved/Audits/press_shop_pr004_crane_runtime_v029.json` and `...v030.json` pass with exact `MCX-U-CS10-0001`, complete phase sequence and 0 cm native load/attachment follow error. v029 navigation remains valid/non-partial at 1396.95 cm and `press_shop_pr004_collision_navigation_v029.json` passes with zero failures.
- Fresh v030 fixed evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v030_pr004_crane_runtime/`. Full 6210 cm width and physical C-hook/bore engagement are proven. `Saved/Audits/press_shop_pr004_crane_visual_gate_v030.json` remains **FAIL / REWORK REQUIRED / PROMOTION FORBIDDEN**: central-column framing, roof/hall exposure, repeated blank girder plates, west-facing crane identity, close-load light balance, festoon/service detail and restrained crane wear remain open. Do not promote v029 or v030 merely because their runtime gates pass.

# PR-004 full-span crane fabrication v031 checkpoint (2026-08-03, latest)

- User correction was explicit: the **crane**, not a train, must be full width. `/Game/LineBoss/Maps/LB_PressShop_PR004CraneFabricationCandidate_v031` retains the measured 6210 cm wall-to-wall/runway span for both bridges; accepted PR-004 baseline remains v006 and v031 is **NOT PROMOTED**.
- v031 replaces repeated blank-module presentation with layered aged RAL1023/dark/exposed materials, 52 splice plates, three running rails and grease witnesses, 37 festoon actors, two trolley-owned service cabinets and west-readable Cairnwell CR-40-01/SWL 40 t and CR-30-01/SWL 30 t identities.
- Fresh `Saved/Audits/press_shop_pr004_crane_runtime_v031.json` passes the complete live transfer and exact PR-004 deposit. All 69 audited bridge-fabrication actors and both trolley cabinets follow their owners with 0 cm error. Fresh navigation and collision audits also pass: `press_shop_pr004_navigation_runtime_v031.json` and `press_shop_pr004_collision_navigation_v031.json`.
- Fresh fixed-camera evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v031_pr004_crane_runtime/`. The images prove the full span, C-hook bore engagement and completed deposit, but visual inspection still fails release quality. The hall/PR-004 area is too dark, the full-span framing over-dominates the nearer 30 t crane, and the close transfer view exposes simplified hook-block/pad/reeving geometry. Audit: `Saved/Audits/press_shop_pr004_crane_visual_gate_v031.json` = **FAIL / REWORK REQUIRED / PROMOTION FORBIDDEN**.
- Next crane pass must retain the proven 6210 cm geometry and runtime authority while improving hall/task lighting, camera hierarchy, fabricated C-hook/block/reeving detail and packaged-load material response. Do not weaken the runtime/collision/navigation gates or promote v031 merely because they pass.

# PR-004 crane lifting-detail v032 checkpoint (2026-08-03, latest)

- Built isolated `/Game/LineBoss/Maps/LB_PressShop_PR004CraneLiftingCandidate_v032` from unpromoted v031. The measured 6210 cm bridge span and all prior authority remain unchanged. v032 is **NOT PROMOTED**.
- Added eleven hook/yoke/lance fabrication actors, four native reeving falls, balanced factory/task fills and east-side/full-detail/deposit cameras. The first runtime attempt exposed that low-centred CHook-tagged lance parts changed native discovery's initial hook datum from 820 to 761 cm. That state was rejected immediately; the lance was rebound as non-reeving hoist-follow detail, and the runtime validator now explicitly requires 820 cm immediately after discovery before allowing transfer.
- Corrected fresh runtime evidence passes: `Saved/Audits/press_shop_pr004_crane_runtime_v032.json` starts at hook Z=820, completes exact `MCX-U-CS10-0001` deposit, reports 0 cm native load/attachment error, audits 69 inherited bridge actors, two trolley cabinets, eleven lifting-detail actors and four reeving falls with maximum fabrication error 0.0000305 cm. Navigation and collision also pass in the v032 audits.
- Fresh images are under `Saved/ValidationScreenshots/PressShopIntegration/v032_pr004_crane_runtime/`. Visual gate **FAILS** in `Saved/Audits/press_shop_pr004_crane_visual_gate_v032.json`: a structural column bisects the east full-span view, the cube/cylinder twin-cheek yoke reads as an oversized rectangular frame rather than a credible industrial C-hook suspension, roof lighting is hot/patchy, and the deposit view is overbright/sparse. Promotion is forbidden.
- Preserve the strengthened initial-datum and rigid-follow gates. Next pass should replace—not merely repaint—the rejected primitive v032 yoke/lance dressing with a purpose-built dimensioned lifting asset, retain bore engagement and the 59 cm physical offset, and use a structurally clear fixed camera.

# PR-004 purpose-built C-hook v033 checkpoint (2026-08-04, latest)

- Authored reusable Blender/FBX source under `SourceAssets/IndustrialKit/BridgeCrane/CHook/Candidate_v033/`. Independent clean-scene FBX import passes. Final source/Unreal dimensions are 2.421 x 0.558 x 2.017 m / 242.1 x 55.8 x 201.7 cm; explicit UVs removed the initial Unreal tangent warnings.
- `/Game/LineBoss/Maps/LB_PressShop_PR004CraneCHookCandidate_v033` derives from unpromoted v031. The old placeholder 40 t hook is hidden and removed from motion discovery. The single purpose-built hook retains native Z=820, yaw 90 degrees onto the world-Y coil bore axis, a 59 cm vertical bore-arm offset and a 150 cm body-to-load Y offset so the forged body stays outside the 1.50 m coil face while the 1.88 m padded arm traverses the bore.
- The first source version imported at 1.46 cm due legacy FBX unit interpretation and was rejected; import now has a mandatory 235–248 x 50–62 x 195–208 cm bounds gate. Camera review then exposed the original 0.94 m arm as too short; the corrected 2.421 m asset was rebuilt and independently re-audited before Unreal reimport.
- Fresh `press_shop_pr004_crane_runtime_v033.json` passes the complete transfer from the mandatory 820 cm initial datum with 0 cm native drift and ~0.0000305 cm observer error after accounting for the authored 150 cm horizontal offset. Navigation and collision audits also pass.
- Fresh consistent images are in `Saved/ValidationScreenshots/PressShopIntegration/v033_pr004_crane_runtime/`. `press_shop_pr004_crane_visual_gate_v033.json` records **C-HOOK SUBASSEMBLY DIRECTION PASS / FULL MAP VISUAL HOLD / NOT PROMOTED**. The side view proves the forged C silhouette and the front view proves the yellow nose through the bore. Full-map promotion remains blocked by uneven hall lighting, 30 t foreground dominance, sparse/underlit deposit presentation, final package material/label polish and missing native 30 t support authority.
- User fleet decision: use several cranes with distinct jobs. Keep the 40 t crane as the live master-coil handler; keep one 30 t front-end support/maintenance crane parked so it does not duplicate the task or dominate the view; add separate die-change/major-maintenance cranes later only in press-train bays that require them.

# PR-004 crane hierarchy/material v034 checkpoint (2026-08-04, latest)

- Built isolated `/Game/LineBoss/Maps/LB_PressShop_PR004CraneManagementCandidate_v034` from unpromoted v033. Accepted v006 and rejected v007-v010 statuses are unchanged; v034 is **NOT PROMOTED**.
- The 30 t moving assembly (52 actors) is now parked at the west/north support end at bridge X=-9100 and trolley Y=-4700 cm, with its hook stowed at Z=1010 cm. Fixed runways and columns remain at their measured datums. Its Cairnwell identity explicitly says SUPPORT. The 40 t crane remains the only live master-coil handler and retains hook Z=820 plus the proven [0,150,-59] cm hook-to-load relation.
- All 15 packaged presentations use a lighter woven-grey layered wrap; 14 Cairnwell plates were reduced to 620 x 280 mm and the native PR-004 plate was similarly restrained. Three low-power floor spots improve store/PR-004/support visibility without changing collision/navigation.
- Fresh runtime, navigation and collision gates pass: `press_shop_pr004_crane_runtime_v034.json`, `press_shop_pr004_navigation_runtime_v034.json`, `press_shop_pr004_collision_navigation_v034.json`. CS-10 deposits exactly, native load/attachment drift is 0, and navigation remains valid/non-partial at 1396.95 cm.
- Fresh images are in `Saved/ValidationScreenshots/PressShopIntegration/v034_pr004_crane_runtime/`. The deposit/operator composition, package separation and crane hierarchy improve, but `press_shop_pr004_crane_visual_gate_v034.json` records **VISUAL HOLD / NOT PROMOTED**: two columns obstruct the management view, ceiling pools remain clipped, carried-load face treatment and HMI readability need another pass, and native 30 t support authority remains open.
- Continue with isolated v035 from v034: move the management camera inside the south column line, rebalance ceiling/floor energy, and refine package/HMI readability without changing the proven 40 t runtime geometry.

# PR-004 crane/package/HMI finish v035 checkpoint (2026-08-04, latest)

- Built isolated `/Game/LineBoss/Maps/LB_PressShop_PR004CraneFinishCandidate_v035` from unpromoted v034. v006 remains the accepted integration baseline; v007-v010 remain rejected; v035 is **NOT PROMOTED**.
- Reduced broad factory fills from 440/620 to 320/450 while retaining v034 floor-directed spots. The selected south-interior clear camera has no structural column between the viewer and the working 40 t crane; the 30 t support crane remains recessed and stowed.
- Corrected the package identity system rather than stacking another plate: both imported fixed label slots are blank controlled paper, obsolete baked COIL ID/HEAT values are gone, and live Cairnwell/Moorcross text sits on the existing 420 x 250 mm physical main label. The final 85 cm world-X alignment keeps the three CS-10 attachment actors rigidly owned by the moving load.
- Fresh final runtime passes with exact CS-10 deposit, all phases, mandatory initial/final Z=820 and zero native load/attachment error. Fresh navigation remains valid/non-partial at 1396.95 cm and collision audit has zero failures.
- Selected evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v035_pr004_crane_runtime/`: `...management_south_interior_clear...`, purpose-built hook, hook side, deposit operator oblique and readable HMI. The HMI visibly shows Cairnwell/Moorcross, PR-004, `COIL LOADED`, `MCX-U-CS10-0001` and its actual blocked-action state.
- `Saved/Audits/press_shop_pr004_crane_visual_gate_v035.json` records **DIRECTION PASS / RELEASE POLISH AND 30 T AUTHORITY OPEN / NOT PROMOTED**. Reuse v031/v033/v034/v035 subassemblies. Remaining blockers are live heat/lot/barcode data for the second label panel, close wrap fibre/wrinkle/scuff polish, final luminaire/reflection design, distinct native 30 t support dispatch and combined PR-004 campaign/fault/save plus PR-005 handoff proof.

# PR-004 30 t support-crane authority and hook v036-v038 (2026-08-04, latest)

- Added reusable native `ALBSupportCraneController`; it is separate from `ALBBridgeCraneController` and has no coil source, PR-004 deposit or material-ownership API. CR-40-01 remains the sole master-coil authority. `ULBPressShopSaveGame` is now format v3 and includes `FLBSupportCraneSaveState`.
- CR-30-01 requires power, clear route/personnel, an active maintenance permit, a reserved support zone and explicit 40 t swept-zone separation. Motion fail-stops on any lost proof. Moving saves restore in `RestoreInterlockStop`; only Parked and OnStation restore as stable states.
- Native UE 5.8 build and `Saved/Automation/SupportCrane_v001/index.json` pass. v038 reaches (-7600,-4700,760), returns exactly to park (-9100,-4700,1010), and produces 0 cm drift in 117 observed 40 t actors plus 0 cm master-coil drift.
- v036 proved the authority but retained a contradictory C-hook. v037 introduced a dimensioned general-purpose 30 t hook block. v038 adds a guarded sheave face and moves the service datum clear of coil inventory. Reusable asset: `/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane/SupportHook/Candidate_v038/SM_LB_Crane_SupportHookBlock_30T_Candidate_v038` (117.07 x 69.50 x 161.09 cm).
- Full v038 regressions pass: `press_shop_pr004_support_crane_runtime_v038.json`, `press_shop_pr004_crane_runtime_v038.json`, `press_shop_pr004_navigation_runtime_v038.json` and `press_shop_pr004_collision_navigation_v038.json`. The 40 t regression still deposits exact `MCX-U-CS10-0001` with zero native load/attachment error; navigation remains valid/non-partial at 1396.95 cm.
- Fresh support evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v038_pr004_support_crane_runtime/`. `Saved/Audits/press_shop_pr004_support_crane_visual_gate_v038.json` records **SUPPORT AUTHORITY AND GENERAL HOOK DIRECTION PASS / VISUAL HOLD / NOT PROMOTED**.
- Retain the controller, guarded hook and clear service envelope. Before promotion, make the Cairnwell CR-30-01 SUPPORT bridge identity readable, bring the inherited upper hoist casing up to the lower-block finish, add restrained hook wear and prove the secondary crane remains subordinate in the final 40 t management view. Live heat/lot/barcode, wrap finish, factory luminaires and combined PR-004 campaign/save/PR-005 handoff remain open. Accepted v006 and rejected v007-v010 statuses are unchanged.

# PR-004 live coil traceability v039 (2026-08-04, latest)

- Current isolated candidate is `/Game/LineBoss/Maps/LB_PressShop_PR004TraceabilityCandidate_v039`, derived from retained v038. Accepted v006 remains the integration baseline; rejected v007-v010 remain rejected; **v039 is not promoted**.
- `ALBPR004Station` stable save is v4 and persists `HeatId`, `SupplierLotId` and `TraceabilityBarcode`. The 40 t transfer deposits exact CS-10 values `HT-CW26-08417`, `LOT-MCXU-260804-A`, `503184064100010`; deterministic non-empty fallbacks exist for other loaded coils.
- Four native tests pass in `Saved/Automation/PR004_Traceability_v039/index.json`. UE 5.8 editor target compilation and source/HMI controller contracts pass.
- All fourteen external packages have live secondary trace backing/text/barcode actors; PR-004 has three matching native components. The CS-10 ownership set is six actors. A first live run correctly failed when new text actors remained Static; after correction to Movable, the final audit passes with zero native load/attachment drift.
- The heat-panel datum is taken from CAD source: 240 x 150 mm at imported X=-27 cm, face Y=+75.3 cm, Z=-36 cm. Two estimated placements that created or exposed a third white label were visually rejected and replaced. Fresh carried/deposited images show one correctly overlaid secondary panel.
- Final technical regressions pass in `press_shop_pr004_crane_runtime_v039.json`, `press_shop_pr004_support_crane_runtime_v039.json`, `press_shop_pr004_navigation_runtime_v039.json` and `press_shop_pr004_collision_navigation_v039.json`; navigation is valid/non-partial at 1396.953125 cm.
- Fresh evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v039_pr004_crane_runtime/`. `Saved/Audits/press_shop_pr004_traceability_visual_gate_v039.json` is **TRACEABILITY DIRECTION PASS / PACKAGE AND FACTORY RELEASE VISUAL HOLD / NOT PROMOTED**. Continue small-type/barcode polish, wrap fibre/wrinkle/scuff finish, luminaires/reflections, 30 t fleet polish and combined PR-004 campaign/save plus PR-005 handoff proof.

# PR-004 package surface and local task light v040 (2026-08-04, latest)

- Current isolated visual direction is `/Game/LineBoss/Maps/LB_PressShop_PR004WrapFinishCandidate_v040`, derived from unpromoted v039. v006 remains accepted; v007-v010 remain rejected; **v040 is not promoted**.
- Only package material slots 2/3/4/6 and one non-colliding package task light changed. Geometry, 1499.8 x 1900 x 1900 mm bounds, labels, six-actor CS-10 ownership and crane datums are unchanged.
- The final retained balance uses woven silver-grey wrap, softer blue-grey overlap/patch materials and dry brown compressed-fibre pads. A first dark pass, an overbright material/light pass and a pale carried-state pass were visually rejected before the balanced result.
- Fresh technical gates pass: `press_shop_pr004_crane_runtime_v040.json`, `press_shop_pr004_support_crane_runtime_v040.json`, `press_shop_pr004_navigation_runtime_v040.json`, `press_shop_pr004_collision_navigation_v040.json`. Primary six-actor ownership and support isolation report zero native drift; navigation remains valid/non-partial at 1396.953125 cm.
- Fresh close/carried/management images are in `Saved/ValidationScreenshots/PressShopIntegration/v040_pr004_crane_runtime/`. `Saved/Audits/press_shop_pr004_wrap_finish_visual_gate_v040.json` records **PACKAGE SURFACE AND LOCAL TASK LIGHT DIRECTION PASS / AUTHORED WRINKLE AND FACTORY LIGHTING HOLD / NOT PROMOTED**.
- Retain v040 material/light direction. Next add restrained authored shallow wrinkles, handling scuffs and edge compression; then rebalance inventory/store luminaires and roof reflections without losing the active 40 t / subordinate 30 t hierarchy.

# PR-004 directed factory luminaire candidate v041 (2026-08-04, latest)

- Current isolated visual candidate is `/Game/LineBoss/Maps/LB_PressShop_PR004LuminaireCandidate_v041`, derived from unpromoted v040. Accepted v006 remains protected; rejected v007-v010 remain rejected; **v041 is not promoted**.
- v041 reduces the fifteen former omnidirectional factory-fill point sources to 100-intensity ambient support and adds fifteen downward, non-shadow-casting factory task sources. General sources use 950 intensity; active PR-004/store sources use 1300. Geometry, package ownership, crane authority and navigation are unchanged.
- Fresh technical gates pass: `press_shop_pr004_crane_runtime_v041.json`, `press_shop_pr004_support_crane_runtime_v041.json`, `press_shop_pr004_navigation_runtime_v041.json`, and `press_shop_pr004_collision_navigation_v041.json`. Navigation remains valid/non-partial at 1396.953125 cm.
- Fresh management, package-close and carried-package images are in `Saved/ValidationScreenshots/PressShopIntegration/v041_pr004_crane_runtime/`. `Saved/Audits/press_shop_pr004_luminaire_visual_gate_v041.json` records **DIRECTED FACTORY LUMINAIRE DIRECTION PASS / PACKAGE CARRY AND RELEASE LIGHTING HOLD / NOT PROMOTED**.
- Retain the directed-light grid as the next lighting foundation. Remaining visual holds are the pale carried wrap against the dark upper hall, final wall/reflection exposure without restoring v040 roof bloom, authored shallow wrinkle/scuff/edge-compression detail, and trace typography/barcode polish. Then complete the 30 t upper-hoist/identity finish and combined PR-004 campaign/save plus PR-005 handoff proof.

# Native PR-004 to PR-005 traceable material flow v001 (2026-08-04, latest)

- The UE 5.8 C++ toolchain is operational. `LineBossCarFactoryEditor Win64 Development` builds with VS 2022 14.44 and Windows SDK 10.0.22621.0; older missing-toolchain notes are historical.
- New `ALBPressShopMaterialFlowController` performs a transactional handoff: PR-004 remains owner until PR-005 accepts the same coil. Coil ID `MCX-U-CS10-0001`, heat `HT-CW26-08417`, supplier lot `LOT-MCXU-260804-A`, barcode `503184064100010`, and 1500 mm width are carried into PR-005.
- PR-005 save state is now version 2 and the Press Shop root is format 4. Traceability survives capture/restore; legacy PR-005 v1 saves remain accepted with empty migrated trace fields.
- Focused automation at `Saved/Automation/PR004_PR005_Handoff_v001/index.json` passes 1/1. Full `LineBoss.PressShop` native regression at `Saved/Automation/PressShop_NativeRegression_v001/index.json` passes 6/6 with zero warnings/failures. Audit: `Saved/Audits/press_shop_pr004_pr005_material_flow_v001.json`.
- Status is **NATIVE TRACEABLE HANDOFF AND IN-MEMORY SAVE ROUNDTRIP PASS / MAP RUNTIME AND DISK-SLOT GATES OPEN / NOT PROMOTED**. Next bind the controller and native PR-005 station in an isolated full-map derivative, prove visible PIE ownership transition and disk-slot restore, then inspect fresh fixed PR-004/PR-005 handoff cameras.

# Full-map PR-004 to PR-005 handoff candidate v042 (2026-08-04, latest)

- Current isolated map is `/Game/LineBoss/Maps/LB_PressShop_PR004PR005HandoffCandidate_v042`, derived from unpromoted v041. Accepted v006 remains protected and rejected v007-v010 remain rejected; **v042 is not promoted**.
- v041 already contained all 59 modular PR-005 geometry actors but no native PR-005 authority. v042 adds one native `ALBPR005Station`, one transactional material-flow controller, binds 15 payoff/mandrel/coil-car/strip/crop moving actors to native movers, and makes the payoff-coil presentation appear only after PR-005 accepts the traceable coil.
- `Saved/Audits/press_shop_pr004_pr005_handoff_runtime_v042.json` passes with exact coil/heat/lot/barcode continuity and visible PR-005 payoff. Fresh v042 primary crane, support crane, navigation and collision/navigation gates all pass; navigation remains valid/non-partial at 1396.953125 cm.
- The first south-side camera pair was visually rejected because structural columns obscured the payoff. Revised opposite-aisle evidence clearly shows the loaded bare coil and PR-004→PR-005 relationship in `Saved/ValidationScreenshots/PressShopIntegration/v042_pr004_pr005_handoff_runtime/`.
- `Saved/Audits/press_shop_pr004_pr005_visual_gate_v042.json` records **TRACEABLE HANDOFF AND LOADED PAYOFF DIRECTION PASS / PR-005 HMI, MATERIAL AND RELEASE POLISH HOLD / NOT PROMOTED**. Remaining v042 holds are full-map live Cairnwell HMI binding, authored coil-car/loading motion, PR-005 factory material/reflection finish, operational aisle dressing/workers/logistics, and fresh fixed-camera reinspection after those changes.
- Native regression v002 passes 6/6 and now includes actual `SaveGameToMemory`/`LoadGameFromMemory` serialization of Press Shop format 4. Only the persistent disk-slot/fresh-process save gate remains open for this handoff state.
- The persistent save gate is now closed. Fresh Unreal writer report `Saved/Automation/PR004_PR005_DiskWriter_v001/index.json` writes the exact transferred format-4 state; a separate fresh reader report `Saved/Automation/PR004_PR005_DiskReader_v001/index.json` verifies PR-004 released ownership plus PR-005 coil/heat/lot/barcode, then deletes only `LB_AUTOMATION_PR004_PR005_HANDOFF_V001`. Full native regression v003 passes 7/7 with zero warnings/failures and leaves no automation save slot behind.

# PR-005 live Cairnwell HMI candidate v043 (2026-08-04, latest)

- Current isolated map is `/Game/LineBoss/Maps/LB_PressShop_PR005LiveHMICandidate_v043`, derived from unpromoted v042. Accepted v006 remains protected; rejected v007-v010 remain rejected; **v043 is not promoted**.
- `ALBPR005Station` now hosts the native `ULBPR005HMIWidget` and a deterministic live TextRender presentation on the exact authored 340 x 255 mm display surface. The Press Shop -90 degree station transform is applied correctly. The screen shows Cairnwell/Moorcross branding, real station state, exact coil ID, selected recipe/width, permissive count and guarded action; there is no in-world Line Boss wording.
- A first camera/mount attempt was visually rejected because the guard obscured the view and the unrotated coordinates missed the physical screen. Corrected fresh evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v043_pr005_live_hmi_runtime/`; the close live-HMI direction passes and the wider shot proves the transferred coil in the guarded payoff cell.
- Final v043 gates pass: UE 5.8 editor build; 40 t transfer; 30 t support dispatch/return; valid non-partial 1396.953125 cm navigation; collision/navigation; exact traceable PR-004-to-PR-005 handoff with 15 mover bindings; and `Saved/Automation/PressShop_NativeRegression_v004/index.json` at 7/7.
- Visual decision: `Saved/Audits/press_shop_pr005_live_hmi_visual_gate_v043.json` is **LIVE CAIRNWELL HMI DIRECTION PASS / PR-005 CELL MATERIAL, MOTION AND RELEASE POLISH HOLD / NOT PROMOTED**. Next author visible coil-car/loading motion, replace harsh PR-005 materials/reflections, complete local lighting/floor/aisle logistics/workers, then repeat Pro-reference screenshot inspection.
- Native coil-car motion is now implemented on the same unpromoted v043 checkpoint. A five-second approach/lift begins at [-220,0,-38] cm, reaches the authored mandrel datum, and only then sets the commissioning `bCoilCarPositioned` proof. Save restore restarts an incomplete owned-coil presentation safely.
- Fresh motion evidence shows a distinct inbound coil and the live HMI at `COIL CAR LOADING 20%`. `Saved/Automation/PressShop_NativeRegression_v006/index.json` passes 7/7 with explicit start/intermediate/settled assertions; all v043 crane, support, navigation, collision and handoff gates were rerun and pass.
- Motion decision: `Saved/Audits/press_shop_pr005_coil_car_motion_visual_gate_v043.json` is **COIL-CAR RUNTIME MOTION DIRECTION PASS / LOADING APERTURE, MATERIAL AND RELEASE POLISH HOLD / NOT PROMOTED**. The next pass must clarify the guarded loading aperture/rail relationship and replace the harsh mirror-like coil and black/yellow material balance before adding workers/logistics.

# PR-005 layered material candidate v044 (2026-08-04, latest)

- Current isolated map is `/Game/LineBoss/Maps/LB_PressShop_PR005MaterialCandidate_v044`, derived from unpromoted v043. Accepted v006 remains protected; rejected v007-v010 remain rejected; **v044 is not promoted**.
- 59 PR-005 actors receive 116 candidate overrides. The licensed Surface Forge Metal Paint Chips set is wrapped through a duplicated reusable industrial-paint master and used only on restrained dark machine paint. The first Surface Forge safety-yellow pass rendered the approved barrier nearly black and was visually rejected; safety-coded yellow now uses a controlled coated material and guard mesh uses distinct galvanised steel.
- Fresh settled, loading-motion and live-HMI captures are under `Saved/ValidationScreenshots/PressShopIntegration/v044_pr005_runtime/`. The corrected safety hierarchy and less mirror-like steel direction pass, while the coil still lacks convincing wound-layer/edge detail and dark machinery needs more tonal separation.
- Fresh v044 40 t crane, 30 t support, valid non-partial 1396.953125 cm navigation, collision/navigation and exact traceable handoff gates pass. Native regression v006 remains 7/7.
- Visual decision: `Saved/Audits/press_shop_pr005_material_visual_gate_v044.json` is **SAFETY COLOUR AND STEEL BALANCE DIRECTION PASS / WOUND DETAIL, DARK MACHINE AND RELEASE DRESSING HOLD / NOT PROMOTED**. Next add authored wound-layer/edge treatment and PR-005 local task/reflection lighting, then clarify loading rails/aperture and add floor/aisle/logistics/workers.

# PR-005 authored coil-finish candidate v045 (2026-08-04, latest)

- Current isolated map is `/Game/LineBoss/Maps/LB_PressShop_PR005CoilFinishCandidate_v045`, derived from unpromoted v044. Accepted v006 remains protected; rejected v007-v010 remain rejected; **v045 is not promoted**.
- Source inspection proved the existing 151.2 x 184.0 x 185.4 cm, 32,188-triangle payoff coil already contains 28 concentric face-winding objects, two outer edge bands, one lap and two bore collars. v045 preserves that mesh and restores three exact semantic finishes: brushed shell, wound edges and bore shadow. Surface Forge is not used on the bare coil.
- The first high-specular v045 edge pass was visually rejected for point-highlight glitter. The final pass uses a rougher, lower-specular winding finish plus two restrained PR-005-local task sources. No equipment coordinates, collision or navigation geometry changed.
- Fresh PIE evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v045_pr005_runtime/`: loaded cell, loading motion, live Cairnwell HMI, honest exterior close view through approved guarding and an internal material-inspection view.
- Fresh v045 gates pass: 40 t primary transfer; 30 t support dispatch/return; valid non-partial 1396.953125 cm navigation; collision/navigation; exact traceable PR-004-to-PR-005 handoff with barcode `503184064100010` and 15 native mover bindings. Native source did not change; `Saved/Automation/PressShop_NativeRegression_v006/index.json` remains 7/7.
- Visual audit `Saved/Audits/press_shop_pr005_coil_finish_visual_gate_v045.json` is **AUTHORED WOUND COIL AND LOCAL LIGHTING DIRECTION PASS / CELL SCALE, DRESSING AND RELEASE POLISH HOLD / NOT PROMOTED**. Next expand the visual read of the full 11,500 mm PR-005 line/loading aperture/rails, improve dark-machine panel separation and add floor wear, route markings, logistics and workers before another Pro-reference gate.

# PR-005 semantic floor-route candidate v046 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005FloorRoutesCandidate_v046` is an isolated v045 derivative and remains unpromoted. Accepted v006 and rejected v007-v010 remain protected.
- Audit found five authored floor slots had inherited generic concrete/dark-machine appearances. v046 binds exact matte service blue, maintenance red, material-flow cyan, label white and protected-walkway green while retaining the existing safety-yellow slot. No machinery coordinates, collision or navigation geometry changed.
- Fresh whole-line and floor-route PIE views are under `Saved/ValidationScreenshots/PressShopIntegration/v046_pr005_runtime/`. The whole-line camera usefully proves the outgoing PR-005 threader/strip approach toward PR-006, but the coloured authored floor features remain too small/occluded for a release-quality player hierarchy.
- All v046 gate receipts pass: primary crane, support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact traceable handoff. However, three successful gate processes and one capture returned Windows `0xC0000005` after the PASS receipt and clean Unreal shutdown log, with no new CrashReporter bundle. This is an explicit clean-process-exit hold.
- `Saved/Audits/press_shop_pr005_floor_routes_visual_gate_v046.json` records **WHOLE-LINE CAMERA DIRECTION PASS / FLOOR-ROUTE PLAYER READABILITY AND CLEAN PROCESS EXIT HOLD / NOT PROMOTED**. Next use dimensioned non-colliding surface geometry for the 1,500 mm walkway, maintenance boundary and flow arrows, strengthen outgoing-line supports/continuity, and repeat gates until process exits are clean.

# PR-005 dimensioned route candidate v047 (2026-08-04, latest)

- `/Game/LineBoss/Maps/LB_PressShop_PR005DimensionedRoutesCandidate_v047` is an isolated v046 derivative. It is **visually rejected and not promoted**; accepted v006 and rejected v007-v010 remain unchanged. v045 remains the strongest preserved PR-005 visual checkpoint.
- v047 adds an audited 11,500 x 1,500 mm protected walkway, two yellow edges, ten red maintenance-boundary dashes and a cyan material-flow arrow. All 16 surfaces are `NoCollision`, cannot affect navigation and do not move equipment.
- The first pass was rejected because the surfaces sat below the top of the authored floor mesh. They were raised, rebuilt and re-audited; exact bounds and material paths are recorded in `Saved/Audits/press_shop_pr005_v047_route_bounds.json`.
- Fresh whole-line, angled-route and top-route captures are under `Saved/ValidationScreenshots/PressShopIntegration/v047_pr005_runtime/`. Despite correct bounds, the intended floor hierarchy still does not read coherently in fixed player views. This is a visual reject.
- Fresh v047 primary crane, support crane, valid non-partial 1396.953125 cm navigation, collision/navigation and exact traceable handoff receipts pass. Primary/support/navigation and screenshot sessions exited cleanly. The handoff session returned Windows `0xC0000005` after writing its PASS receipt and clean shutdown log; no new CrashReporter bundle exists.
- `Saved/Audits/press_shop_pr005_dimensioned_routes_visual_gate_v047.json` records **DIMENSION, COLLISION AND RUNTIME TECHNICAL PASS / FIXED-CAMERA VISUAL REJECT / NOT PROMOTED**. Next re-author the full floor composition as a cohesive Blender/CAD decal/mesh package aligned to an intentional player camera, then resolve outgoing threader/strip support readability before workers/logistics.
# 2026-08-04 continuation checkpoint — PR-005 CAD floor route v048

- Work remained exclusively in the canonical non-OneDrive UE 5.8 repository. Accepted PR-004 v006 is untouched; rejected v007-v010 and visually rejected PR-005 v046/v047 remain unpromoted.
- Current retained PR-005 floor-integration direction is `/Game/LineBoss/Maps/LB_PressShop_PR005CADFloorCandidate_v048`, derived directly from v045. Reusable dimensioned source is `SourceAssets/PR005/FloorRoutes/Candidate_v048/`.
- v048 has an exact 11.5 x 1.5 m station-local protected walkway with separate yellow, red, cyan and white semantics. Final runtime gates pass for both cranes, navigation/collision and exact traceable PR-004→PR-005 handoff; screenshots and decision are in the v048 runtime folder and `Saved/Audits/press_shop_pr005_cad_floor_visual_gate_v048.json`.
- v048 is a direction pass only and is not promoted. Next isolate a derivative to design the intersecting pale factory cross-aisle junction and finish the authored hydraulic service carrier/cover containment before workers/logistics and the next release gate.

# 2026-08-04 continuation checkpoint — PR-005 cross-aisle junction v049

- Current retained floor-integration direction is the unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR005FloorJunctionCandidate_v049`, with source in `SourceAssets/PR005/FloorRoutes/Candidate_v049/`.
- The 1800 x 1260 mm white/yellow crossing makes the inherited factory cross-aisle junction intentional. Three fresh runtime views pass direction review; final paint wear, global cross-aisle material authority, hydraulic-service containment, workers/logistics and lighting remain open.
- Both crane authorities, navigation/collision and exact traceable PR-004→PR-005 handoff pass after the v049 change. See `Saved/Audits/press_shop_pr005_floor_junction_visual_gate_v049.json`. Do not promote v049; next isolate hydraulic carrier/cover work.

# 2026-08-04 continuation checkpoint — PR-005 service-routing materials v050

- Current hydraulic material direction is the unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR005ServiceRoutingCandidate_v050`. Seven exact authored hydraulic slots now separate pressure/return IDs, unions, hoses, grip/tread and galvanised carrier.
- Fresh v050 close/elevated/whole-line images and all five runtime gates pass direction review. Decision is in `Saved/Audits/press_shop_pr005_service_routing_visual_gate_v050.json`; no promotion.
- Next create a station-local, removable tread-cover module over only the long horizontal twin-hose run. Keep both flexible end loops and capped unions visible/accessible, preserve v050 materials and repeat runtime/fixed-camera gates.

# 2026-08-04 continuation checkpoint — PR-005 service covers v051

- Current retained PR-005 containment direction is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR005ServiceCoversCandidate_v051`; reusable source is `SourceAssets/PR005/HydraulicRouting/Candidate_v051/`.
- Five solid removable covers protect 3480 mm of straight hose run while flexible end loops/unions remain exposed for service. The first conveyor-like rib version was rejected; the corrected one-pad-per-panel source is retained.
- v051 has real BlockAll collision and navigation contribution. Both cranes, complete 1396.953125 cm non-partial route, collision/navigation and exact traceable handoff pass. See `Saved/Audits/press_shop_pr005_service_covers_visual_gate_v051.json` and the v051 runtime screenshots. Do not promote.
- Next add small HYDRAULIC SERVICES / NO STEP identity and restrained cover/floor wear, then workers/logistics and final lighting without moving proven geometry.

# 2026-08-04 continuation checkpoint — PR-005 service identity/wear v052

- Current retained service-detail direction is the unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR005ServiceIdentityCandidate_v052`, with reusable source in `SourceAssets/PR005/HydraulicRouting/Candidate_v052/`.
- Fixed-camera review rejected invisible top-only text, a back-facing plate and mirrored lettering. The corrected player-side plate is readable as `HYD SERVICE / NO STEP`; eight sparse edge-contact marks add restrained use. There is no in-world Line Boss branding.
- v052 preserves the five cover dimensions, flexible-end access, `BlockAll` collision, navigation contribution and all equipment datums. Both cranes, complete 1396.953125 cm non-partial navigation, collision/navigation and exact traceable handoff pass; barcode `503184064100010` and 15 mover bindings remain exact.
- See `Saved/Audits/press_shop_pr005_service_identity_visual_gate_v052.json` and `Saved/ValidationScreenshots/PressShopIntegration/v052_pr005_runtime/`. This is a direction pass only; do not promote.
- Next add workers/logistics context without altering proven geometry, then finish lighting and repeat fresh Pro-reference inspection before any promotion decision.

# 2026-08-04 continuation checkpoint — PR-005 stationary logistics v053

- Current retained candidate is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR005LogisticsCandidate_v053`, derived from retained v052. Accepted PR-004 v006 remains protected.
- v053 contains only route-safe stationary dressing: one licensed return stillage, one controlled-blue pallet and three controlled safety-yellow service crates. Forklift and placeholder mannequin are deliberately excluded after failing the required quality boundary.
- The initial obstructed camera iteration was rejected and replaced. Fresh fixed views are under `Saved/ValidationScreenshots/PressShopIntegration/v053_pr005_runtime/`.
- All v053 technical/runtime gates pass; navigation is valid/non-partial at exactly `1396.953125 cm`. See `Saved/Audits/press_shop_pr005_logistics_visual_gate_v053.json`.
- Status remains **NOT PROMOTED**. Next resolve a genuinely release-quality worker solution and final integrated lighting/Pro-reference review before advancing to PR-006.

# 2026-08-04 continuation checkpoint — PR-006 leveller v054

- Retained machine direction, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR006LevellerCandidate_v054`.
- Source: `SourceAssets/PR006/PrecisionCassetteLeveller/Candidate_v001/`; 67 local-pivot semantic source modules and placement manifest, 65 Unreal machine modules, three native identity rows.
- The 1500 mm-strip machine is at authoritative datum `(-1700, -2000, 0)` with 19 work rolls, removable cassette structure, four gap-control points and three drives.
- First dark Unreal views and mirrored imported lettering were rejected and corrected. Close views pass machine direction; wide integration fails because the required PR-007 washer/lube unit is not yet between PR-005 and PR-006.
- All inherited gates pass and navigation remains `1396.953125 cm`, valid and non-partial. PR-006 itself has not passed runtime, guarding, HMI, fault or save-state gates.
- See `Saved/Audits/press_shop_pr006_leveller_visual_gate_v054.json`. Next build PR-007 in the physical gap, then revalidate connected strip continuity. Do not promote v054.

# 2026-08-04 continuation checkpoint — PR-007 washer/lube v055

- Current retained connected-line candidate, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR007WasherLubeCandidate_v055`.
- Reusable source is `SourceAssets/PR007/WasherLubeUnit/Candidate_v001/`: 78 semantic local-pivot modules for a 1500 mm strip, with four spray headers, 20 nozzles, two tanks, pumps/duplex filters, lift hoods, mist extraction and service access at datum `(-2700, -2000, 0)`.
- Fresh operator/service/connected-line images in `Saved/ValidationScreenshots/PressShopIntegration/v055_pr005_runtime/` pass the modular direction review and prove the correct PR-005 to PR-007 to PR-006 physical sequence.
- All five inherited v055 gates pass. Navigation remains valid, non-partial and exactly `1396.953125 cm`; exact PR-004-to-PR-005 identity continuity is unchanged.
- `Saved/Audits/press_shop_pr007_washer_lube_visual_gate_v055.json` records **DIRECTION PASS / NOT PROMOTED**. Explicit strip bridging, approved open-mesh guarding, live HMI, pump/lift-hood runtime, fluid faults and save state remain mandatory before PR-007 promotion.

# 2026-08-04 continuation checkpoint — PR-007 connected strip/guard/HMI v056

- Current retained candidate, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR007StripGuardHMICandidate_v056`.
- Reusable source `SourceAssets/PR007/StripBridges/Candidate_v001/` closes the audited 512.5 cm upstream and 257.5 cm downstream breaks with exact 150 cm strip modules and four roller supports. Six approved open-mesh panels plus ten posts protect only the exposed transition hazards.
- The first full shared HMI cabinet was visually rejected. A compact pedestal touchscreen is retained instead; it presents Cairnwell/Moorcross PR-007 state cleanly but is not yet runtime-bound.
- Fresh corrected fixed views are in `Saved/ValidationScreenshots/PressShopIntegration/v056_pr005_runtime/`. All inherited v056 gates pass, including valid/non-partial `1396.953125 cm` navigation and exact PR-004-to-PR-005 continuity.
- See `Saved/Audits/press_shop_pr007_strip_guard_hmi_visual_gate_v056.json`. Status is **DIRECTION PASS / NOT PROMOTED**. Native pump/hood permissives, fluid faults and persisted PR-007 state are the next mandatory work.
# 2026-08-04 continuation checkpoint — PR-007 native runtime v057

- Current retained runtime direction, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR007RuntimeCandidate_v057`, isolated from v056. Accepted PR-004 v006 remains untouched; rejected v007-v010 remain rejected.
- Native `ALBPR007Station` now owns Priming/Running/Stopping/Fault state, guard and strip-threaded permissives, wash/lube levels, filter differential, mist extraction, controlled stop, safe fault reset, production travel and running hours. Press Shop save format advances to v5 with versioned `FLBPR007SaveState`; moving restores safely to Ready.
- Seven authored modules are bound to native local pivots: wash hood, both pump motors and four lower process rollers. The compact Cairnwell/Moorcross touchscreen is runtime-bound and shows live Running or Fault state; it remains a simple touchscreen rather than a redundant full console.
- Focused native automation `LineBoss.PressShop.PR007.RuntimeAndSave` passes. Map PIE audit `Saved/Audits/press_shop_pr007_runtime_v057.json` passes Priming→Running, fluid consumption, strip travel, hood closure, live HMI, controlled stop, restart, `GUARD_OPEN` trip, fault HMI and safe reset with all seven mover bindings exact.
- All five inherited v057 gates pass: primary crane, support crane, exact traceable PR-004→PR-005 handoff, collision/navigation and a valid non-partial navigation path of exactly `1396.953125 cm`.
- Fresh fixed evidence is in `Saved/ValidationScreenshots/PressShopIntegration/v057_pr005_runtime/`; the readable close screen shows `RUNNING | WASH 82% | LUBE 76%`. See `Saved/Audits/press_shop_pr007_runtime_visual_gate_v057.json`.
- Decision: **NATIVE RUNTIME AND LIVE HMI DIRECTION PASS / RELEASE MACHINE DETAIL, PROCESS EFFECTS AND CLEAN EDITOR EXIT HOLD / NOT PROMOTED**. The simplified washer/lube casing, process visualization, final material wear and occasional post-audit Unreal shutdown `0xC0000005` remain open. Continue full Press Shop work without claiming v057 release-quality.

# 2026-08-04 continuation checkpoint — PR-008 servo blanking v058

- Current unpromoted integration direction is `/Game/LineBoss/Maps/LB_PressShop_PR008ServoBlankingCandidate_v058`; accepted PR-004 v006 is protected and rejected v007-v010 remain rejected.
- `SourceAssets/PR008/ServoBlankingLine/Candidate_v001/` supplies 79 dimensioned semantic modules at datum `(-500, -2000, 0)`. The corrected Unreal material hierarchy uses grey housings/cabinets, charcoal structure, safety yellow for moving/hazard parts and blue only for actual powered drives.
- Three fresh fixed cameras in `Saved/ValidationScreenshots/PressShopIntegration/v058_pr005_runtime/` pass modular/material direction only. This is not release quality and has not yet been judged against the incoming authoritative Pro PR-008 design pack.
- Exact bounds prove a 305 cm unsupported PR-006-to-PR-008 strip gap, zero lateral offset and a 2.5 cm height change. Receipt: `Saved/Audits/press_shop_pr006_pr008_strip_continuity_v058.json`. Build a supported 1500 mm transition in an isolated derivative without stretching either machine.
- All inherited v058 technical/runtime gates pass: both crane authorities, valid non-partial `1396.953125 cm` navigation, collision/navigation and exact traceable PR-004-to-PR-005 handoff.
- Decision audit: `Saved/Audits/press_shop_pr008_servo_blanking_visual_gate_v058.json`. Status is **DIRECTION PASS / PRO REFERENCE, GUARDING, LIVE HMI, NATIVE RUNTIME, SAVE/FAULT AND STRIP CONTINUITY HOLD / NOT PROMOTED**.
- Next: retain v058 as evidence, use the requested Pro PR-008-to-PR-010/four-train pack as visual authority when received, and continue an isolated PR-008 derivative with the measured strip bridge and release-detail framework.

# 2026-08-04 continuation checkpoint — PR-008 transition/guard v059

- Current retained transition direction, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008TransitionGuardCandidate_v059`. Source is `SourceAssets/PR008/StripTransition/Candidate_v001/`.
- A Blender-authored 1500 mm strip transition closes the measured 305 cm PR-006-to-PR-008 break across a 25 mm fall. Three roller stands support it; four approved open-mesh panels plus six posts protect the exposed rollers.
- Exact Unreal bounds pass both joints with `-0.007369995 cm` gap (minute overlap) and `0.000007629 cm` lateral error. Receipt: `Saved/Audits/press_shop_pr008_transition_continuity_v059.json`.
- All inherited technical/runtime gates pass, including unchanged valid/non-partial `1396.953125 cm` navigation. Fresh v059 fixed cameras pass the transition direction review.
- Two capture sessions repeated the known post-output Windows `0xC0000005`; valid screenshots exist, but clean repeated capture exit remains open.
- Decision audit: `Saved/Audits/press_shop_pr008_transition_guard_visual_gate_v059.json`. Status is **DIRECTION PASS / NOT PROMOTED**. Retain the bridge source; next add native PR-008 process authority while final machine geometry, full guarding/access and visual promotion await the authoritative Pro pack.

# 2026-08-04 continuation checkpoint — PR-008 native runtime v060

- Current retained native checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008RuntimeCandidate_v060`. v059 transition source remains reusable; accepted PR-004 v006 and rejected v007-v010 are unchanged.
- `ALBPR008Station` now owns Threading/Running/Stopping/Fault sequencing, safety/process permissives, strip travel, 1450 mm blank indexing/counting, scrap accumulation, controlled stop/reset and safe save restore. Press Shop save format is v6 with `FLBPR008SaveState PR008`.
- UE 5.8 compile succeeds. Focused `LineBoss.PressShop.PR008.RuntimeAndSave` automation is 1/1 green. Twelve exact map modules bind to seven native movers.
- `Saved/Audits/press_shop_pr008_runtime_v060.json` passes real PIE Running, first blank, scrap, live HMI, stop/restart, blocked-outfeed fault/HMI and safe reset. The close fixed image reads `RUNNING | BLANKS 1 | 1450 mm` with Cairnwell/Moorcross branding and no Line Boss in-world wording.
- All inherited v060 crane/handoff/collision/navigation gates pass; navigation remains valid, non-partial and exactly `1396.953125 cm`. All final v060 capture processes exit normally.
- Visual decision: `Saved/Audits/press_shop_pr008_runtime_visual_gate_v060.json` is **RUNTIME/HMI/CONTINUITY DIRECTION PASS / NOT PROMOTED**. The blockout machine is not release art. Reuse this controller and HMI binding when the authoritative Pro PR-008 design arrives, then finish full guards/access, materials, process effects and promotion screenshots.
# 2026-08-04 continuation checkpoint — PR-006 native runtime v061

- Retain `/Game/LineBoss/Maps/LB_PressShop_PR006RuntimeCandidate_v061` as an unpromoted native calibration/runtime checkpoint. It owns 28 exact mover bindings, a 1.15 mm gap recipe, strip travel/load, live HMI, stop/restart, cassette-unlocked fault/reset and save format v7.
- Automation and PIE pass; all inherited crane/handoff/navigation/collision gates pass. Fresh HMI/process/connected evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v061_pr005_runtime/` and decision audit is `Saved/Audits/press_shop_pr006_runtime_visual_gate_v061.json`.
- The close screen reads `RUNNING | GAP 1.15 mm | LOAD 58%`. This is a direction pass only; guard access, process detail, full-line finish and clean repeated screenshot exits remain open.

# 2026-08-04 continuation checkpoint — Pro remaining-machinery pack authority

- Authoritative pack is preserved and staged at `SourceAssets/ReferencePacks/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0/`. ZIP SHA-256 is `7021A2E5DE71F89306E1AA6CB96D2F6018870404E01F4F83FF27D5F6B2BC399A`; 28/28 manifest files verify and no unsafe archive path exists.
- Authority order is owner/fixed datums, `authority_and_assumptions.json`, CSV/JSON numeric schedules, engineering spec, then visuals. Numbers override pictures; EST dimensions need blockout validation.
- PR-008 uses datum `(-500,-2000,0)` cm and exact planning envelope `10400 x 5560 x 4490 mm`. Assemble Pro local modules with station yaw `-90 degrees`: local `+Y` flow maps to world `+X`, local `+X` maps to world `-Y`.
- v060 remains useful native runtime/HMI/continuity evidence, but its visual layout is superseded because it used the wrong source flow axis. Preserve it; rebuild in a new isolated candidate and do not promote either.
- Native rebind later requires telescope Y travel, edge-guide travel, service-door/scrap-flap movers and the complete Pro fault vocabulary. Press-train global datums remain TBC and must not be invented.
- In-world branding is Cairnwell Automotive / Moorcross Works only. `Line Boss` on sheet titles is not in-world branding.
- Full receipt: `Saved/Audits/cairnwell_press_shop_remaining_machinery_pack_intake_v001.json`. Immediate next action is the exact ten-module PR-008 Pro envelope blockout, Unreal measurement gate and fresh operator/elevated/connected reference comparison.

# 2026-08-04 continuation checkpoint — PR-008 Pro envelope v062

- Current PR-008 spatial authority is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008ProEnvelopeCandidate_v062`; source is `SourceAssets/PR008/ServoBlankingLine/ProEnvelope_v001/`.
- Ten Pro module cages, the separate fixed planning cage and strip datum are assembled at datum `(-500,-2000,0)` cm with yaw `-90 degrees`. Unreal measurement is `1040.000000 x 556.000000 x 449.000153 cm`; HMI centre is `(-185,-2252,110)` cm.
- 114 old PR-008 visual actors are preserved but hidden only in v062. PR-004–PR-007 and native PR-008/PR-006 authority remain intact. All envelope meshes are navigation-neutral `NoCollision`.
- Fresh fixed operator/elevated/connected views pass the Pro spatial contract but not art quality. One hall column (`LB_PRESS_Column_0_-2250`) intrudes into the outer planning envelope.
- PR-006 to Pro PR-008 has a 305 cm gap and 25.5 cm fall. Supersede the old v059 25 mm-fall bridge with a new supported entry-loop transition; do not redesign PR-006 or stretch either envelope.
- v062 inherited gates pass: both cranes, exact handoff, complete `1396.953125 cm` navigation and collision/navigation. Decision: `Saved/Audits/press_shop_pr008_pro_envelope_visual_gate_v062.json` — spatial contract pass, engineering blockout only, not promoted.
- Next build the corrected Pro entry-loop transition and coordinate the guard/service-aisle line around the measured column. Then replace cages with detailed modular PR-008 machinery and rebind/extend native authority.

# 2026-08-04 continuation checkpoint — PR-008 Pro entry loop v063

- Current connected interface is unpromoted `/Game/LineBoss/Maps/LB_PressShop_PR008ProEntryLoopCandidate_v063`; source is `SourceAssets/PR008/StripTransition/ProEntryLoop_v002/`.
- It resolves the measured PR-006-to-Pro-PR-008 contract: 3050 mm gap, 255 mm fall, 4.779 degree slope, 1500 mm strip, three roller stands, four approved open-mesh panels and six posts.
- Actual Unreal bounds pass both joints with `-0.074981689 cm` overlap and only `0.000007629 cm` lateral error. Receipt: `Saved/Audits/press_shop_pr008_pro_entry_loop_continuity_v063.json`.
- Fresh operator/elevated/connected views and inherited gates pass direction review. Decision: `Saved/Audits/press_shop_pr008_pro_entry_loop_visual_gate_v063.json` — not promoted.
- The interface is now spatially resolved without rebuilding PR-006. Next replace the ten Pro cages with detailed PR-008 machinery, expand/rebind native authority, and coordinate final gates/light curtains around the hall-column intrusion.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 01 v064

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module01Candidate_v064`, derived from v063 and replacing only Pro cage 01.
- `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` contains 20 semantic FBXs. Exact Unreal union bounds remain inside the fixed Module 01 envelope after correcting the initial E-stop overhang.
- Fresh inspection/elevated/connected evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v064_pr005_runtime/`. The original operator view is rejected as guard-obscured diagnostic evidence; use the added inspection view for the visual decision.
- The close inspection read passes process hierarchy and native Cairnwell/Moorcross PR-008 identity. It does not pass release quality: layered wear, fasteners, bearings, anchors, service details, native binding for six roll/sleeve movers and final guarding remain open.
- All inherited v064 technical/runtime gates pass, including valid non-partial `1396.953125 cm` navigation. Decision: `Saved/Audits/press_shop_pr008_module01_visual_gate_v064.json` — direction pass only, not promoted.
- Standing owner decision: earlier machines predate the final Cairnwell/Moorcross branding. Apply branding/material identity as a reusable layer; do not rebuild sound geometry/runtime merely to add branding. Rebuild only where authoritative dimensions, function or fresh Pro-reference inspection identifies a real conflict. Never place Line Boss branding in-world.
- Next build detailed Pro Module 02 edge tracking inside its exact cage, continuing one module at a time before native rebind and full guard/service-aisle coordination.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 02 v065

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module02Candidate_v065`, derived from v064 and replacing only Pro cage 02.
- Fourteen semantic FBXs add the edge-tracking frame, support rolls, rails/ball screw, sensors, drive, limit hardware and services. Two guide carriages use physical guide-centre pivots and the authoritative local-X `+/-150 mm`, `40 mm/s`, centred-safe contract.
- Blender first rejected a 20 mm service overhang. Unreal subsequently exposed a stricter applied-bevel/FBX bounds overhang. The hardware and service-assembly origin were corrected; final Unreal containment passes the fixed `2200 x 650 x 1450 mm` cage.
- All inherited v065 gates pass, including valid non-partial `1396.953125 cm` navigation. Fresh evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v065_pr005_runtime/`.
- The drive camera and earlier inspection framings are rejected as guard-obscured or wrong-subject diagnostics. The final elevated three-quarter inspection passes the functional edge-tracking direction. Native guide movement/fault/save binding, readable Module 02 identity, layered wear, fasteners/bearings/anchors and final guarding remain open.
- Decision: `Saved/Audits/press_shop_pr008_module02_visual_gate_v065.json` — direction pass only, not promoted. Continue exact Pro Module 03 servo-feed rolls.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 03 v066

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module03Candidate_v066`, derived from v065 and replacing only Pro cage 03.
- Nineteen semantic FBXs provide the servo-feed frame, support rolls, top/bottom driven rolls and replaceable sleeves, bearing/gap control, paired guarded servo drives, encoders, pinch shielding, service hardware, E-stop and identity.
- Initial source containment rejected a 30 mm side-drive and about 10 mm upstream plate/E-stop infringement. The geometry was corrected inward. Blender and Unreal now pass the fixed `2600 x 1450 x 1950 mm` cage.
- Four roll/sleeve actors carry the authoritative local-X continuous `12 rpm`, stop/brake-safe contract. They are not yet rebound to native PR-008 authority.
- All inherited v066 gates pass, including valid non-partial `1396.953125 cm` navigation. Fresh fixed evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v066_pr005_runtime/`.
- Visual decision: dedicated servo-feed geometry, drive hierarchy and process sequence pass direction review. Native motion/fault/save binding, readable integrated identity, layered wear, fasteners/services/anchors, dominant drive-cover reassessment and final guarding remain open.
- Decision audit: `Saved/Audits/press_shop_pr008_module03_visual_gate_v066.json` — direction pass only, not promoted. Continue exact Pro Module 04 telescopic strip support with authoritative local-Y `0-1200 mm`, retracted-safe movement.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 04 v067

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module04Candidate_v067`, derived from v066 and replacing only Pro cage 04.
- Thirteen semantic FBXs provide the support bed/guides, three nested stages, rack/pinion servo drive, cable carrier, redundant home/end/position sensing, edge protection, service hardware, E-stop and identity.
- Initial source containment rejected a 20 mm nested tip-stage and 5 mm motor infringement. Unreal then caught an FBX joined-origin reflection that put the drive 950 mm outside the permitted world bound and pushed services through the downstream face. Origins were recentered on geometry; final Blender and Unreal bounds pass the fixed `2400 x 2000 x 1300 mm` safe/retracted cage.
- Three moving stages share the authoritative local-Y `0-1200 mm`, `60 mm/s`, retracted-safe command with one-third, two-thirds and full-travel ratios. They remain unbound to native PR-008 authority.
- All inherited v067 gates pass, including valid non-partial `1396.953125 cm` navigation. Fresh fixed evidence is under `Saved/ValidationScreenshots/PressShopIntegration/v067_pr005_runtime/`.
- The safe/retracted mechanical/process direction passes. Live extension/return, obstruction and position faults, persisted restore, readable identity, underside visibility, layered wear, fasteners/rack detail/anchors and final guarding remain open.
- Decision audit: `Saved/Audits/press_shop_pr008_module04_visual_gate_v067.json` — direction pass only, not promoted. Continue exact Pro Module 05 pre-punch press.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 05 v068

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module05Candidate_v068`, derived from v067 and replacing only Pro cage 05.
- Reusable source in `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` adds 15 semantic FBXs for the four-column pre-punch frame, bed/crown, lower cassette, moving slide/tool, hydraulics, guides/sensors, slug drawer, scrap flap, two service doors, pinch shielding, services, identity and E-stop.
- The first source gate rejected a 30 mm lift-eye height infringement and a 10 mm upstream E-stop-button infringement. The lift eyes were lowered and the button was corrected to face outward on the operator-side corner rather than toward Module 04. Unreal then exposed FBX reflection around off-centre joined origins on the service doors and upper service bundle; export origins were recentered without changing the approved dimensions.
- Blender and Unreal now pass the exact `2850 x 1850 x 3500 mm` Module 05 envelope. Unreal receipt is `Saved/Audits/press_shop_pr008_module05_candidate_v068.json`: 15 semantic actors and 4 movable actors.
- Authored motion contracts are slide local-Z down `0-220 mm` at `120 mm/s`, two service doors `0-110 degrees` manual/closed-safe, and scrap flap `0-70 degrees` at `15 degrees/s`/closed-safe. Native PR-008 rebind remains open.
- All five inherited v068 gates pass: both cranes, exact traceable PR-004-to-PR-005 handoff, collision/navigation and valid non-partial navigation of exactly `1396.953125 cm`.
- Four fresh fixed Unreal views are under `Saved/ValidationScreenshots/PressShopIntegration/v068_pr005_runtime/`. They pass pre-punch geometry, process hierarchy, motion separation and E-stop direction only. They do not match the Pro hero density closely enough for release: readable identity, layered wear/services/fasteners, live slide/tool/scrap evidence, final interlocked guarding/light curtains and native safe restore remain open. White planning-cage lines are diagnostic and must be hidden before promotion.
- Decision audit: `Saved/Audits/press_shop_pr008_module05_visual_gate_v068.json` — direction pass only, not promoted. Continue exact Pro Module 06 cut-to-length shear.

# 2026-08-04 owner decision — fully automated Press Shop and robot-only maintenance

- The Press Shop is a fully automated factory. Do not add worker NPCs, pedestrian population simulation or release-worker art as completion requirements.
- Machine faults remain important management gameplay, but the player does not manually repair equipment. The loop is HMI diagnosis and downtime review → dispatch available LB-MR01 → certified route and automated machine-isolation proof → diagnosis/light service or modular exchange → robot verification → player-authorised restart.
- LB-CR01 owns routine cleaning missions. LB-MR01 owns inspection, diagnosis, lubrication, sensor cleaning, parts delivery, approved fastener service, leak classification and approved module exchange using its existing eight-tool runtime authority.
- Heavy repairs are abstracted through robot-assisted module exchange plus parts, time, cost and off-line depot service. No visible technician or manual repair animation is required.
- Remove historical worker/pedestrian holds from forward promotion criteria. Replace them with robot availability, certified routes, tool/part inventory, battery, isolation/exclusion authority, repair duration, production loss and fresh robot/machine runtime evidence.
- Safety is not removed: guarding, light curtains, exclusion zones, automated zero-energy isolation, controlled stop/reset, crane separation and certified routes remain mandatory.
- Machine-readable authority: `SourceAssets/Robots/LB_MR01_MaintenanceRobot/Data/AUTOMATED_PRESS_SHOP_MAINTENANCE_AUTHORITY_v001.json`. Code wording now records PR-004 automated inspection evidence and robot-proved isolation rather than worker preparation or human-applied LOTO.

## Control-room-only player authority

- Owner decision: the player remains in the factory control room and performs the complete game loop remotely. Factory-floor walking, a floor-level player avatar and direct manual machine repair are not required.
- Production schedules, recipes, machine start/stop/isolate/reset, crane/material commands, fault diagnosis, maintenance/cleaning dispatch, parts and consumables, campaign restoration and restart approval are all control-room HMI functions.
- Every release station needs authored fixed CCTV views. Selectable inspection drones provide movable visual, thermal and diagnostic feeds when a fixed camera cannot reveal the fault; drones inspect only and do not replace MR01 repair tools.
- Do not render every feed at full rate. Use cached/low-rate thumbnails for inactive feeds and full-rate quality only for the selected camera or drone. Drone routes must respect cranes, machine exclusions and temporary no-fly zones.
- Existing world-click prototypes remain useful authority tests, but their release control path becomes the corresponding remote HMI/camera command. This applies to PR-004 `Unpackage`, which remains a simple automated state change rather than an operator animation.

## Autonomous support-robot charging checkpoint (2026-08-04)

- `ALBSupportRobot` now owns a reusable certified automatic-charging route. At or below its configured idle reserve threshold it enters `Returning`, follows the certified docking route, docks using the route destination dock ID, charges to 100 percent and returns to `Docked`/available without player micromanagement.
- Critical-reserve handling attempts the certified automatic return before declaring a battery fault. `bAutomaticChargeReturnActive` prevents the dock/return loop from immediately redispatching itself.
- UE 5.8 native editor compilation passed after the implementation and again after the focused test/getter additions.
- Focused automation `LineBoss.SupportRobots.Common.AutomaticCharging` is 1/1 green. Evidence is `Saved/Automation/SupportRobot_AutomaticCharging_v001/` and `Saved/Logs/SupportRobot_AutomaticCharging_v001.log`; it proves 25 percent reserve -> autonomous certified return -> destination dock ID -> increasing charge -> 100 percent -> `Docked`/available.
- This common authority is reusable by both LB-CR01 and LB-MR01. It does not close either robot's visual promotion gate and does not weaken certified-route, dock, charger, collision or screenshot requirements.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 06 v069

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module06Candidate_v069`, derived from v068 and replacing only Pro cage 06. Accepted PR-004 v006 and rejected PR-004 v007-v010 are unchanged.
- Reusable source in `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/` provides 16 semantic FBXs for the enclosed guillotine frame, lower knife cassette, moving blade beam, twin servo-hydraulic drive, hold-down array, infeed/outfeed support, guides/sensing, trim drawer, service/access panels, light curtain, services/lifting hardware, identity and outward operator-side E-stop.
- Blender source and Unreal import both pass the unchanged `2850 x 1200 x 3000 mm` Pro Module 06 cage. Unreal measured world bounds are min `(-314.750002,-2139.999985,3.0)` cm and max `(-197.000008,-1857.5,237.499985)` cm. Receipt: `Saved/Audits/press_shop_pr008_module06_candidate_v069.json`.
- The separately authored blade beam retains the authoritative local-Z down `0-180 mm` at `300 mm/s`, top-safe contract. Native PR-008 motion/fault/save binding remains open.
- UE 5.8 editor build succeeds. Both crane runtime gates, exact PR-004-to-PR-005 handoff, collision/navigation and valid non-partial `1396.953125 cm` navigation pass. The combined collision audit was correctly rerun after its fresh navigation dependency.
- Four fresh 1920x1080 fixed Unreal views are under `Saved/ValidationScreenshots/PressShopIntegration/v069_pr005_runtime/`. They prove shear identity by form, process sequence, E-stop direction and connected-strip placement only.
- Pro Sheet 01 comparison holds promotion for mechanical/service density, layered condition materials, readable Cairnwell/Moorcross identity, live cut/hold-down/blank/scrap evidence, native fault/save restore, full interlocked open-mesh guarding/light curtains and removal of visible white planning cages. Inspection/drive views are diagnostic crops, not release hero views.
- Decision audit: `Saved/Audits/press_shop_pr008_module06_visual_gate_v069.json` — direction pass only, not promoted. Continue exact Pro Module 07 discharge rollers.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 07 v070

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module07Candidate_v070`, derived from v069 and replacing only Pro cage 07. Accepted PR-004 v006 and rejected PR-004 v007-v010 are unchanged.
- New dimensioned source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module07_discharge_v001.py` generates 19 semantic FBXs, a Blender file, manifest, audit and three source renders. It includes the frame, seven individually pivoted rollers, bearing blocks, guarded common drive, guides, blank/skew sensing, representative cut blank, approved open-mesh sides, outfeed light curtain, service routing, attached identity and outward operator-side E-stop.
- The first source gate rejected E-stop, drive, frame and light-curtain infringements. These components were corrected inward; the fixed cage was not enlarged. Final Blender bounds are min `(-1.315,3.1,0.3)` m and max `(1.3,4.8,1.485)` m inside the exact `2650 x 1750 x 1200 mm` Pro envelope.
- Unreal import contains 19 semantic actors and seven movable rollers. Measured world bounds min `(-189.999969,-2130.000009,29.999989)` cm and max `(-19.999985,-1868.5,148.500011)` cm pass the unchanged cage. Receipt: `Saved/Audits/press_shop_pr008_module07_candidate_v070.json`.
- Each roller retains the authoritative local-X continuous `0-60 m/min`, stop/brake-safe contract. Native roll speed, blank travel, blocked-outfeed fault and save restore remain open.
- UE 5.8 editor build succeeds. Both cranes, exact PR-004-to-PR-005 handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass in dependency order.
- Four fresh 1920x1080 Unreal views are under `Saved/ValidationScreenshots/PressShopIntegration/v070_pr005_runtime/`. Pro Sheet 01 comparison passes discharge mechanism, open-mesh, E-stop, identity attachment and process order only.
- Promotion remains held for live roller/blank evidence, a measured PR-008-to-PR-009 interface, native fault/save binding, service/fastener/anchor density, layered condition materials, complete interlocked guarding and clean camera compositions without future cages or white planning lines.
- Decision audit: `Saved/Audits/press_shop_pr008_module07_visual_gate_v070.json` — direction pass only, not promoted. Continue exact Pro Modules 08-10 utilities/HMI, then native PR-008 rebind and the real PR-009 handoff.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 08 v071

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module08Candidate_v071`, derived from v070 and replacing only Pro cage 08. Accepted PR-004 v006 and rejected PR-004 v007-v010 remain unchanged.
- New source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module08_hpu_v001.py` implements the v062 base-on-floor interpretation for the exact `1100 x 900 x 1850 mm` HPU envelope. Eleven semantic FBXs provide a retaining bund/skid, reservoir, duty/standby pump set, filters, cooler, accumulator, manifold, pressure/temperature/level/leak instrumentation, hard lines, local isolator and attached identity.
- Blender initially rejected 5 mm bund-lip and 2.5 mm identity infringements; both were moved inward. Unreal then exposed FBX-origin reflections on the off-centre reservoir/drain and pipe bundle; geometry-centred export origins corrected them without changing approved dimensions.
- Final Blender bounds min `(-2.6,3.6025,0.01)` m and max `(-1.5,4.495,1.79)` m pass. Unreal bounds min `(-139.750002,-1850,0.999994)` cm and max `(-50.499989,-1739.999989,179.000006)` cm pass; receipt is `Saved/Audits/press_shop_pr008_module08_candidate_v071.json`.
- UE 5.8 editor build succeeds. Both cranes, exact PR-004-to-PR-005 handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass in dependency order.
- Four fresh 1920x1080 Unreal images are under `Saved/ValidationScreenshots/PressShopIntegration/v071_pr005_runtime/`. The original drive camera was rejected as shear-obscured; a downstream/operator-side replacement clearly proves the HPU and is the authoritative drive view.
- Pro Sheet 01 comparison passes base-on-floor placement, bund/pump/filter/accumulator/manifold/instrument direction and maintenance readability only. Native pressure/temperature/level/filter/leak states, alarms, MR01 dispatch, save restore, pressure/return machine connections, layered hydraulic wear and clean captures without planning lines remain promotion holds.
- The `200 bar / 120 L/min` schedule is retained as EST concept authority only, never certified procurement data. Decision: `Saved/Audits/press_shop_pr008_module08_visual_gate_v071.json` — direction pass only, not promoted. Continue exact Module 09 electrical/drive cabinets.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 09 v072

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module09Candidate_v072`, derived from v071 and replacing only Pro cage 09. Accepted PR-004 v006 and rejected PR-004 v007-v010 are unchanged.
- Source `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module09_cabinets_v001.py` generates 11 semantic FBXs for the plinth, separate incoming-power/servo-drive/controls-and-UPS shells, doors/hardware, controls, cooling, rear cable entry, beacon, sensors and label plates.
- Source corrections retained the exact `1250 x 650 x 2200 mm` base-on-floor envelope. Unreal caught off-centre FBX reflections; bounds-centred origins corrected all static cabinet exports without altering geometry. Unreal bounds min `(-127.500005,-2266.0,-0.000001)` cm and max `(-62.749985,-2145.0,219.000010)` cm pass.
- Dedicated `M_CA_MW_PR008_LightGrey_v001` preserves the authored electrical-enclosure finish. UE 5.8 build, both cranes, exact handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v072_pr005_runtime/`. Cabinet section/coating/placement direction passes only. Visible engineering/planning frames, obstructed views, weak identity/service labels, clean/flat materials, missing native electrical states/faults/MR01/save and missing real connections hold promotion.
- Decision: `Saved/Audits/press_shop_pr008_module09_visual_gate_v072.json` — direction pass only, not promoted. Continue exact Module 10 compact HMI, then native PR-008 rebind and measured PR-009 interface.

# 2026-08-04 Moorcross main control-room reference intake

- Eight owner-supplied Pro sheets are preserved and hashed under `SourceAssets/ReferencePacks/CAIRNWELL_MOORCROSS_MAIN_CONTROL_ROOM_PRO_REFERENCE_v1.0/`; see `MANIFEST.json` and `Saved/Audits/cairnwell_control_room_pro_reference_intake_v001.json`.
- Sheet 03 fixed `14400 x 7800 mm` dimensions outrank Sheet 01 `14000 x 7500 mm` and Sheet 02 `18600 x 11400 mm` recommended alternatives.
- The set confirms the seated control-room-only player, selected-live/cached-inactive CCTV, inspection-only drone, autonomous MR01/CR01, alarm hierarchy and save-state authority. No Line Boss wording is permitted in-world.
- A parallel chat may create source assets only in `C:\Users\greg_\Projects\LineBoss_ControlRoom_Staging`; it must not open or modify this canonical Unreal repository. Integration follows PR-008 physical completion.

# 2026-08-04 continuation checkpoint — PR-008 detailed Module 10 v073

- Current retained detailed checkpoint, not promoted: `/Game/LineBoss/Maps/LB_PressShop_PR008Module10Candidate_v073`, derived from v072 and replacing only exact Pro cage 10. This completes the scheduled physical source/import pass for PR-008 Modules 01-10 without changing accepted PR-004 v006 or rejected v007-v010.
- `SourceAssets/PR008/ServoBlankingLine/Detailed_v001/build_pr008_module10_hmi_v001.py` generates 10 semantic FBXs for the anchored base, sealed pedestal, neck, 15-17-inch display housing, separate touch surface, local control deck, controls, outward operator-side E-stop, rear services and Cairnwell/Moorcross label plates.
- The first Blender gate rejected base, deck, E-stop and rear-handle infringements; geometry was corrected inward. Blender bounds min `(2.22,2.93,0.461)` m/max `(2.82,3.37,1.7395)` m and Unreal bounds min `(-207.000004,-2282.0,46.099999)` cm/max `(-163.000004,-2222.000006,173.950006)` cm pass the exact `600 x 460 x 1280 mm` envelope.
- Separate interaction contracts are retained for `PR008_HMI_PRIMARY_TOUCH`, `PR008_HMI_LOCAL_CONTROLS` and `PR008_ESTOP`. These are source/import authority only, not proof of live UI or safe runtime control.
- Fresh UE 5.8 build, both cranes, exact handoff, valid non-partial `1396.953125 cm` navigation and combined collision/navigation pass. Four fresh Unreal images are under `Saved/ValidationScreenshots/PressShopIntegration/v073_pr005_runtime/`.
- Pro Sheet 01 comparison passes compact-HMI form, operator orientation, touch/control/E-stop readability and equipment-family direction. Live UI/native state, measured operator/service clearance, readable identity, layered condition, remote-control-room routing, safe reset/isolation, fault/save proof and clean cage-free captures hold promotion.
- Decision: `Saved/Audits/press_shop_pr008_module10_visual_gate_v073.json` — physical direction checkpoint only, not promoted. Begin native PR-008 process/HMI/fault/save rebind and measure the actual PR-008-to-PR-009 interface.

# 2026-08-04 continuation checkpoint — PR-008 native runtime v074

- Current native checkpoint, **not promoted**: `/Game/LineBoss/Maps/LB_PressShop_PR008NativeRuntimeCandidate_v074`, isolated from v073. Accepted PR-004 v006 remains protected and rejected PR-004 v007-v010 remain rejected.
- `ALBPR008Station` now owns the detailed strip-wait/loop/feed/pre-punch/cut/discharge sequence, expanded Pro fault set, latched E-stop/alarm acknowledgement, trusted remote authority `CW.MW.CONTROL_ROOM`, automated isolation/zero-energy proof/release and save-state version 2. Moving saves restore safely to Ready with restart required. Old roll animation was corrected to Unreal local-X Roll.
- Detailed actors are bound to one native authority: 27 semantic bindings, 14 attached movers, three queryable HMI/control/E-stop surfaces and live status text. Focused automation `LineBoss.PressShop.PR008.RuntimeAndSave` is 1/1 green at `Saved/Automation/PR008_Runtime_v002/`; UE 5.8 editor compilation passes.
- PIE audit `Saved/Audits/press_shop_pr008_native_runtime_v074.json` proves authored feed/loop/discharge rotation, edge-guide travel, three-stage telescope, pre-punch slide, scrap flap, shear travel, strip/blank production, E-stop acknowledgement, zero-energy evidence and safe release. Both crane gates, exact PR-004-to-PR-005 handoff, collision/navigation and valid non-partial `1396.953125 cm` navigation also pass on v074.
- Interface audit `Saved/Audits/press_shop_pr008_pr009_interface_v074.json` measures discharge end world X `-19.999985 cm`, only `2.499985 cm` from the Pro target, with `0 cm` primary process centreline error. No PR-009 receiver actors exist yet, so a physical handoff gap cannot be approved.
- Four fresh 1920x1080 captures are in `Saved/ValidationScreenshots/PressShopIntegration/v074_pr005_runtime/`. Manual Pro-reference inspection is recorded with hashes in `Saved/Audits/press_shop_pr008_visual_review_v074.json` as **TECHNICAL/RUNTIME PASS / VISUAL RELEASE GATE FAIL / NOT PROMOTED**.
- Visual blockers: visible white planning cage, obstructing inherited grey slabs/columns, flat/clean materials, weak floor routing/foundations/wear, harsh lighting, HMI/pedestal overlap and a blocked PR-008-to-PR-009 sightline. Next duplicate v074 to isolated v075, remove only confirmed PR-008 placeholders, resolve HMI clearance/cameras and improve layered materials, floor zoning and lighting before fresh gates and screenshot inspection.

# 2026-08-04 continuation checkpoint — PR-008 visual cleanup v075

- Current visual-cleanup checkpoint, **not promoted**: `/Game/LineBoss/Maps/LB_PressShop_PR008VisualCleanupCandidate_v075`, isolated from v074. v074/v073, accepted PR-004 v006 and rejected PR-004 v007-v010 remain unchanged.
- Read-only inventory `Saved/Audits/press_shop_pr008_visual_obstructions_v074.json` distinguished engineering artefacts from real structure. v075 suppresses only the fixed white planning cage, strip datum, three engineering labels and two obsolete v073 HMI captions. The real hall column `LB_PRESS_Column_0_-2250` remains present.
- v075 adds a replacement process strip, 1120 x 610 cm dark machine pad, 1120 x 220 cm remote service aisle, 8 cm safety boundary and four cleaner fixed cameras. All floor dressing is `NoCollision` and navigation-neutral. Build receipt: `Saved/Audits/press_shop_pr008_visual_cleanup_candidate_v075.json`.
- Fresh v075 gates pass: native PR-008 motion/HMI/safety/isolation, primary crane, support crane, traceable PR-004-to-PR-005 handoff, collision and runtime navigation. The path remains valid/non-partial at `1396.953125 cm`.
- Interface measurement is unchanged: `Saved/Audits/press_shop_pr008_pr009_interface_v075.json` records discharge X `-19.999985 cm`, `2.499985 cm` target error and `0 cm` primary centreline error; PR-009 is still absent.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v075_pr005_runtime/`. Hashes and manual Pro comparison are in `Saved/Audits/press_shop_pr008_visual_review_v075.json`.
- Visual decision: **ENGINEERING CLEANUP / FLOOR ZONING / CAMERA DIRECTION PASS; MATERIAL / IDENTITY / ENVIRONMENT / PR-009 HANDOFF HOLD; NOT PROMOTED**. The cage, duplicate captions and blocked camera are fixed, but the line remains too clean/plastic, the strip reads too dark/belt-like, identity plates are weak, floor foundations/wear are incomplete, hall depth is sparse and the real PR-009 receiver is missing. Next isolated candidate is v076 with dedicated bright strip steel, layered machine/cabinet materials, legible identity and authored foundation/floor detail while retaining the v075 cameras.

# 2026-08-04 continuation checkpoint - PR-008 layered v076 rejection and smooth v077 retention

- `/Game/LineBoss/Maps/LB_PressShop_PR008LayeredMaterialCandidate_v076` passed its technical/runtime gates but is **rejected and not promoted**. Its high-frequency procedural colour/roughness breakup made the machinery read as coarse sand-textured paint and materially regressed from v075 and the Pro reference. Decision evidence: `Saved/Audits/press_shop_pr008_visual_review_v076.json`. Do not use v076 as a parent.
- Current retained direction, still **not promoted**, is `/Game/LineBoss/Maps/LB_PressShop_PR008SmoothLayerCandidate_v077`, branched directly from v075. It applies 229 controlled smooth material overrides, preserves functional material distinctions, keeps the real hall column and open-mesh guards, and adds a mounted Cairnwell Automotive / Moorcross Works / PR-008 identity plate. No Line Boss wording appears in-world.
- Fresh UE 5.8 editor compilation succeeds. Native PR-008 process/HMI/safety/isolation, both cranes, exact PR-004-to-PR-005 handoff, collision/navigation and valid non-partial `1396.953125 cm` navigation all pass. The measured discharge remains `2.499985 cm` from target with `0 cm` centreline error; PR-009 remains absent.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v077_pr005_runtime/`. Manual original-resolution comparison against Pro Sheet 01 confirms smooth coated-material and identity/HMI direction improvement, but holds release for weak reflection/lighting context, a nearly black discharge blank at some angles, sparse hall depth, simplified enclosure/cabinet/mechanical density and the absent PR-009 receiver.
- `Saved/Audits/press_shop_pr008_visual_review_v077.json` records **SMOOTH MATERIAL / IDENTITY / CAMERA DIRECTION PASS; REFLECTION / ENVIRONMENT / MECHANICAL DENSITY / PR-009 HANDOFF HOLD; RETAINED; NOT PROMOTED**.
- Control-room-only construction rule: optimize silhouette, motion, state and identity for fixed management CCTV first; retain close drone-inspection geometry, service access, collision, robot routes, crane clearances and safety exclusions. Local HMIs are secondary service/status panels. Floor-player walk-up interaction and pedestrian navigation are not release requirements.
- Next candidate must branch from v077, preserve its smooth hierarchy, improve local reflections/industrial lighting/hall context and Pro-level enclosure/mechanical depth, then repeat all gates and fixed-camera review. Do not approve downstream completion until the real PR-009 receiver is staged and measured.

# 2026-08-04 PR-008 reflection-environment v078 rejection

- `/Game/LineBoss/Maps/LB_PressShop_PR008ReflectionEnvironmentCandidate_v078` added three physical overhead luminaires, two camera fills and one local reflection capture from retained v077. All inherited technical gates and the fresh UE 5.8 build pass.
- Four fresh 1920x1080 images under `Saved/ValidationScreenshots/PressShopIntegration/v078_pr005_runtime/` are severely overexposed. Green/charcoal/yellow/steel distinctions clip toward white, the HMI and identity lose legibility, fixture/column glare dominates and the interface view no longer communicates the process.
- `Saved/Audits/press_shop_pr008_visual_review_v078.json` records **TECHNICAL PASS / SEVERE OVEREXPOSURE AND READABILITY FAIL / REJECTED / NOT PROMOTED**. Never parent from v078; retained v077 remains the parent. Any next lighting candidate must reduce photometric intensity by an order of magnitude and pass an early single process-camera exposure check before the full gate suite.
- External staging audit: `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging` contains a valid hash-matched planning handoff with parseable JSON and 25 inventory rows, but zero Blender, FBX or Unreal assets. It is ready for isolated PR-009 source blockout only, not canonical import.

# 2026-08-04 continuation checkpoint - PR-008 calibrated lighting v079

- Current retained direction, **not promoted**: `/Game/LineBoss/Maps/LB_PressShop_PR008CalibratedLightingCandidate_v079`, branched directly from retained v077. Rejected v078 was not used as a parent.
- v079 keeps v077 smooth materials and uses three 550-intensity physical overhead luminaires, 90/75 camera fills and a restrained local reflection capture. An early process-camera exposure gate passed before the full validation suite ran.
- Fresh UE 5.8 editor build, native PR-008 runtime/HMI/safety/isolation, both cranes, exact PR-004-to-PR-005 handoff, valid non-partial `1396.953125 cm` navigation, collision/navigation and PR-008/PR-009 datum inspection all pass.
- Four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v079_pr005_runtime/`. Compared with v077/v078 and Pro Sheet 01, the strip and blank read as metal, close-view depth improves, safety/material colours survive and HMI/E-stop remain legible.
- Release still holds for sparse hall context, slightly hot floor/column highlights, validation-looking shadow/noise, insufficient Pro-level enclosure/cabinet/service density, small long-camera identity and absent PR-009 receiver.
- `Saved/Audits/press_shop_pr008_visual_review_v079.json` records **CALIBRATED LIGHTING / WORKED-STEEL READABILITY PASS; HALL CONTEXT / MECHANICAL DENSITY / IDENTITY DISTANCE / PR-009 HOLD; RETAINED; NOT PROMOTED**. Continue from v079, not v078.

# 2026-08-04 PR-008 installed-hall v080 early rejection

- `/Game/LineBoss/Maps/LB_PressShop_PR008InstalledHallCandidate_v080` tested a rear panel wall, service spine, cable tray, large cell header and foundation anchors from v079. The early process-camera gate failed before technical gates were run.
- The wall appears as a cropped floating slab in the upper-right composition, service runs look unsupported/dangling, and the large identity is clipped. The backdrop does not create credible hall depth or close the Pro mechanical-density gap. Foundation anchor plates are the only clearly useful direction.
- `Saved/Audits/press_shop_pr008_visual_review_v080.json` records **EARLY CAMERA FAIL / COMPOSITION REGRESSION / REJECTED / FULL GATES NOT RUN / NOT PROMOTED**. Retain v079. Any future architecture must be placed from measured camera frusta and real service clearances, with supported trays/drops and an early camera check.

# 2026-08-04 PR-008 measured-anchor v081 rejection and external-tab v082 checkpoint

- `/Game/LineBoss/Maps/LB_PressShop_PR008AnchoredInstallationCandidate_v081` used exact measured v079 base bounds for 24 four-corner anchor assemblies. The mandatory early motion camera showed that the inset plates were almost entirely hidden beneath the machine footprints. `Saved/Audits/press_shop_pr008_visual_review_v081.json` records **MEASURED DIRECTION PLAUSIBLE / VISUAL EVIDENCE INSUFFICIENT / NOT RETAINED / FULL GATES NOT RUN / NOT PROMOTED**. Do not use v081 as a retained parent.
- Retained incremental direction is `/Game/LineBoss/Maps/LB_PressShop_PR008ExternalAnchorTabsCandidate_v082`, branched directly from retained v079. It places measured 120 x 120 mm external plates with 35 mm studs immediately outside six verified major base footprints, producing visible base-connected tabs without moving machinery or changing the established process composition.
- Fresh UE 5.8 compilation, native PR-008 process/HMI/safety/isolation, primary and support cranes, exact PR-004-to-PR-005 handoff, collision, valid non-partial runtime navigation and PR-008-to-PR-009 datum inspection all pass. The tab layer is deliberately `NoCollision` and navigation-neutral while its eventual authored physical-collision treatment remains open.
- Four fresh 1920x1080 Unreal captures are under `Saved/ValidationScreenshots/PressShopIntegration/v082_pr005_runtime/`. Original-resolution inspection confirms a modest installation-grounding improvement while preserving v079 lighting, worked-steel readability, material hierarchy and HMI/process presentation.
- `Saved/Audits/press_shop_pr008_visual_review_v082.json` records **MEASURED EXTERNAL ANCHOR-TAB GROUNDING PASS / HALL CONTEXT, MECHANICAL DENSITY, DISTANT IDENTITY AND PR-009 HOLD / RETAINED / NOT PROMOTED**. Generic plates/studs should become authored base geometry before release; the Pro hall/service-density gap remains substantial.
- Read-only staging inspection now confirms real PR-009 source deliverables in `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging`: one Blender source, 15 candidate FBXs, validation/interface/export manifests and 12 source renders. Source validation passes without promotion, but the proposed receiver begins at world X `220 cm`, leaving a measured `2399.99985 mm` unsupported gap from PR-008 discharge. No canonical Unreal import/runtime/collision/navigation/live-transfer proof exists yet.
- Next: intake and hash the completed PR-009 source package into the canonical repository, resolve the unsupported PR-008-to-PR-009 transfer span by authority-backed geometry/layout rather than silently moving fixed datums, then import into an isolated v083 candidate and repeat every compile/import/runtime/collision/navigation/interface and fixed-camera gate.

# 2026-08-04 PR-009 intake in progress and supported transfer source v001

- The external PR-009 task is still writing `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging`. An initial canonical copy correctly failed the independent hash gate when the Blender file/renders changed during intake; a refreshed snapshot subsequently matched, but it remains explicitly unpromoted and must be refreshed once more after the external task declares final completion.
- Current snapshot and independent receipt: `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v001/` and `Saved/Audits/press_shop_pr009_source_intake_v001.json`. The root `09_HANDOFF_MANIFEST.json` is stale because it predates the binary build; newer `PR009_Audits` receipts and the independent canonical manifest supersede only its old binary-count statement.
- A separate dimensioned interface source now exists at `SourceAssets/PR009/AutomatedBlankStacker/Interface_v001/`. It spans the measured `2400 mm` gap without moving either fixed station datum, uses a `900 mm` roller axis/`990 mm` roller top, and contains 17 individually pivoted rollers, six supported legs, bearings, guarded drive, guides, sensors, service routing, isolation hardware and approved open-mesh sides.
- Blender 5.2 source validation and 25 deterministic FBX exports pass. Three fresh 1600x900 source renders were inspected. `Saved/Audits/press_shop_pr008_pr009_supported_transfer_source_v001.json` records **SOURCE DIMENSION / PIVOT / OPEN-MESH / INSTALLATION DIRECTION PASS; UNREAL INTERFACE / RUNTIME / COLLISION / VISUAL HOLD; NOT PROMOTED**.
- `Scripts/import_build_press_shop_pr009_physical_integration_v083.py` is prepared and syntax-checked, but it has intentionally not been run while the external package remains mutable. It will duplicate retained v082 into isolated `/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083`, import the final source snapshot and supported bridge, then enforce measured bounds before any downstream gates.
- Native PR-009 authority now compiles in `LBPR009Station.h/.cpp`. It owns remote receiving, vision/centring, gantry stacking, separator placement, carrier release, traceability, machine interlocks/faults, controlled stop, isolation/zero-energy proof and safe save restore. Press Shop save format is now version 8 with `FLBPR009SaveState`.

# 2026-08-04 PR-009 v002 canonical intake and v083 visual hold

- The external task remains restricted to PR-009 and has been explicitly told not to begin PR-010. Canonical integration never writes to `C:\Users\greg_\Projects\LineBoss_PR009_PR010_Staging`.
- A hash-matched v002 snapshot at v083 integration time is preserved under `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002/`. `Scripts/intake_pr009_candidate_v002.py` independently verified 83 selected files byte-for-byte against staging, including the production Blender source, 19 FBXs and 16 source renders. Receipt: `Saved/Audits/press_shop_pr009_source_intake_v002.json` — **POINT-IN-TIME HASH/MANIFEST PASS; UNREAL GATES REQUIRED; NOT PROMOTED**. The external task resumed writing after v083 and added FBX reimport evidence, so a final refresh/hash pass remains mandatory after it declares completion.
- Isolated integration map `/Game/LineBoss/Maps/LB_PressShop_PR009PhysicalIntegrationCandidate_v083` is derived from retained v082. It imports all 19 v002 groups, places 16 full-detail presentation groups, imports but does not place LOD1/LOD2, imports but does not bind UCX evidence, installs the separate 25-part supported transfer and spawns one native `ALBPR009Station` using trusted authority `CW.MW.CONTROL_ROOM`.
- Physical bounds pass: PR-009 min `(222.499969,-2259,0)` cm/max `(980,-1741.75,326)` cm remains inside the EST envelope, and the supported transfer spans the measured interface. Receipt: `Saved/Audits/press_shop_pr009_physical_integration_v083.json`. Six combined SK presentation groups still require native decomposition/motion bindings; collision and runtime navigation remain unproved.
- Four fresh 1920x1080 Unreal captures are under `Saved/ValidationScreenshots/PressShopIntegration/v083_pr005_runtime/`. Original-resolution inspection against authoritative Pro `SHEET_02_PR009_ENGINEERING_REFERENCE_4K.png` fails the visual promotion gate: correct footprint/process/silhouette, but insufficient enclosure depth and machine mass, flat over-bright materials, weak service/mechanical density, crowded CCTV composition and low-contrast identity. One interface capture wrote valid evidence before a post-capture Unreal process fault, so stable recapture also remains required.
- `Saved/Audits/press_shop_pr009_visual_review_v083.json` records **FRESH FIXED-CAMERA EVIDENCE COMPLETE / PRO SHEET 02 VISUAL GATE FAIL / INTEGRATION BASELINE RETAINED / NOT PROMOTED**. Do not run the full release gate suite or promote v083. Continue in a new isolated PR-009 candidate from v083 with layered industrial materials, stronger enclosure/gantry/lift/output depth, supported service detail and revised fixed cameras; then recapture early before motion decomposition, collision/navigation and full runtime gates.
- Unreal decomposition pilots exposed the actual motion-import contract. `transform_vertex_to_absolute=False` produces 42 gantry parts at 1/100 expected scale and cannot reconstruct the assembly; receipt `Saved/Audits/press_shop_pr009_gantry_decomposition_pilot_v001.json` is a deliberate fail. Absolute-transform uncombined import produces all 42 parts and exactly reproduces the expected assembled world bounds; receipt `Saved/Audits/press_shop_pr009_gantry_absolute_import_pilot_v002.json` passes. However, current assets arrive as generic `Cube_###`, so semantic binding is unsafe. The parallel PR-009 task has been instructed to preserve semantic mesh-data names, document exact Unreal scale/axis settings and emit deterministic per-object transform/pivot/parent manifests for all six SK groups before final handoff. PR-010 remains prohibited.
- Native `ALBPR009Station` now exposes 26 modular motion contracts plus its station root: nine independent infeed-roll pivots, nine output-roll pivots, gantry bridge/cross-slide/Z, lift table, two side joggers, end jogger and separator picker. Runtime presentation covers receiving rolls, centring joggers, stack gantry/Z/lift movement, separator placement and release rolls while preserving process/fault/isolation/save authority. UE 5.8 compilation succeeds and focused `LineBoss.PressShop.PR009.RuntimeAndSave` passes 1/1 with zero warnings/errors at `Saved/Automation/PR009_Runtime_v002/`. Receipt: `Saved/Audits/press_shop_pr009_native_runtime_presentation_v002.json` — **NATIVE RUNTIME / SAVE / PRESENTATION CONTRACT PASS; FINAL SEMANTIC ASSET BINDING AND VISUAL GATES REQUIRED; NOT PROMOTED**.
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

# 2026-08-04 continuation checkpoint - PR-009 calibrated v086 technical pass, visual and collision hold

- Current retained PR-009 baseline, still **not promoted**: `/Game/LineBoss/Maps/LB_PressShop_PR009LayeredPresentationCandidate_v086`, isolated from v085. It retains the corrected 158-part semantic modular assembly and 237 authored material-role assignments, darkens the presentation calibration, reduces local light/reflection contribution, and moves Cairnwell Automotive / Moorcross Works identity to the measured near guard face. No Line Boss wording appears in-world.
- Four fresh 1920x1080 fixed-camera Unreal captures are under `Saved/ValidationScreenshots/PressShopIntegration/v086_pr009_layered/`. Original-resolution inspection against authoritative Pro Sheet 02 and the corrected v002 source render confirms improved depth, readable blank steel/rollers, restrained safety yellow, visible amber light curtains and near-face identity placement.
- `Saved/Audits/press_shop_pr009_visual_review_v086.json` records **CALIBRATED MATERIAL / NEAR-GUARD IDENTITY / BLANK-STEEL / LIGHT-CURTAIN DIRECTION PASS; TYPOGRAPHY / MECHANICAL DENSITY / ENVIRONMENT / RELEASE COLLISION HOLD; RETAINED; NOT PROMOTED**. Remaining visual blockers are small/soft identity at CCTV distance, sparse cabinets/hoses/sensors/service hardware, a clean bright hall/floor, a technical rather than cinematic interface view and an elevated view that still reads as a modular assembly.
- v086 has one PR-008 station, one PR-009 station and one shared transactional material-flow controller. Full in-map validation is consolidated at `Saved/Audits/PR009_InMap_v086/PR009_IN_MAP_TECHNICAL_VERIFICATION.json`: all eight technical gates pass, both focused automations are 1/1 green, all native process movers animate in PIE, safe save/load restores stopped/Ready with restart required, remote authority/isolation/zero-energy evidence passes, and two non-partial `1040 cm` perimeter navigation routes avoid the protected process volume.
- Promotion remains blocked by authored release collision: ten combined PR-009 static groups still use temporary complex-as-simple collision with no simple elements, so `release_collision_ready=false`. The 158 modular visual actors remain intentionally `NoCollision`; interface assets retain simple collision where intended. Create an isolated v087 collision successor from v086, author simple/convex/UCX collision only for meaningful physical/service/safety envelopes, prove full motion without self-blocking and rerun every technical and fresh fixed-camera gate. PR-010 and robot polish remain on hold.
- `Saved/Audits/press_shop_pr009_visual_successor_plan_v086.json` records a key camera finding before further geometry work: every current v086 camera is on the north/near side, while the authored HMI and electrical cabinet are measured on the south service face at approximately Y `-2240.5` and `-2208 cm`. The accepted collision successor should first receive an early-gated south-west service/hero camera that proves these existing modules, then improve larger CCTV-legible identity and installed grounding; add geometry only when existing semantic actors are proven insufficient.

# 2026-08-04 PR-009 v087 authored-collision checkpoint and measured successor decision

- Isolated `/Game/LineBoss/Maps/LB_PressShop_PR009ReleaseCollisionCandidate_v087` replaces complex-as-simple on all ten combined PR-009 station groups with authored simple box collision. Its inventory is 98 simple boxes: 58 on the ten combined groups, 14 on substantial fixed chassis actors and 26 query-only sensing envelopes on selected movers. There are zero convex primitives and zero complex-as-simple assets in release scope; 118 minor modular visuals remain deliberately `NoCollision`.
- Fixed chassis/substantial envelopes use blocking query-and-physics collision and navigation relevance where appropriate. Selected movers use query-only overlap sensing and do not become physical or navigation blockers. All 20 authored guard primitives, BaseFrame/fixed chassis traces and the physical/query-only distinction are directly proved.
- UE 5.8 compile, both focused PR-009 automations, transactional rollback/no-phantom ownership, native PIE motion, safe stopped restore, trusted authority, isolation/zero-energy proof, two non-partial `1040 cm` perimeter routes, protected-space exclusion and validation-window integrity pass. All 207 normalized v086/v087 visual actor payloads match exactly, and four fresh 1920x1080 images are under `Saved/ValidationScreenshots/PressShopIntegration/v087_pr009_release_collision/`.
- v087 is **not release-ready and not promoted**. A physical full-size `1800 x 2600 mm` blank sweep hits the current trace portal around world `(426,-1870,105.5)` cm because its `2600 mm` opening has zero side clearance. The complete source-authoritative `2800 mm` gantry contract also overlaps the trace beam and both posts; these three contacts are not approved. Authoritative report: `Saved/Audits/PR009_InMap_v087/PR009_RELEASE_COLLISION_VERIFICATION_REPORT.md`; consolidated status is `FAIL_RELEASE_COLLISION_BLOCKED_BY_MAX_BLANK_TRACE_PORTAL_AND_FULL_GANTRY_PORTAL_OVERLAPS__NOT_PROMOTED`.
- The next isolated successor must preserve the full `2800 mm` gantry travel. Move the complete portal visual and collision toward the output from source-Y centre `1.865 m` to `3.15 m` (verified Unreal world-X delta `-128.5 cm`), and widen its clear opening from `2.6 m` to `2.8 m`. This provides `0.165 m` clearance to the governing mover, `0.445 m` to the guarded-cell end and `0.1 m` per side around the maximum blank.
- Author the change as a separate dimensioned derived Blender/FBX/manifest package; preserve immutable Candidate_v002 and do not leave non-identity actor scale in the release asset. Plan: `Saved/Audits/PR009_InMap_v087/trace_portal_clearance_successor_plan.json`. Rerun import/bounds, full-contract sweeps, collision, compile, automations, PIE, save, authority, navigation, integrity and fresh fixed-camera Pro review. PR-010 and both robots remain on hold.

# 2026-08-04 PR-009 Pro-axis correction, v088 rejection and v089 technical acceptance

- **This section supersedes the v087 portal-clearance conclusion immediately above.** Re-reading authoritative Pro Sheet 02 and `PRESS_SHOP_REMAINING_MACHINERY_ENGINEERING_SPEC_v1.0.md` proved local `+X` is across strip/lane and local `+Y` is material flow. The `2600 x 1800 mm` maximum blank is therefore tested as `2600 mm` along flow by `1800 mm` across, which maps through station yaw `-90` to world half extents `(130,90,0.8) cm`.
- M02's `0..2800 mm` entry is total travel within the `3100 mm` module envelope, not an additional `+2800 mm` from the authored midpoint at local Y `-0.3 m`. Correct endpoint offsets are `-1.4..+1.4 m`. With these authoritative interpretations, unchanged v087 clears the original trace portal and its analytical 26-mover full-contract audit has zero unapproved overlaps.
- The dimensionally valid derived portal package at `SourceAssets/PR009/AutomatedBlankStacker/TracePortalClearance_v001/` and map `/Game/LineBoss/Maps/LB_PressShop_PR009TracePortalClearanceCandidate_v088` were built only while testing the earlier interpretation. v088 is now **rejected / not promoted / never a parent** because the design change is unnecessary. Candidate_v002 and v087 remained unchanged. Authority receipt: `Saved/Audits/PR009_InMap_v089/axis_authority_correction.json`.
- Corrected physical tracing exposed the real issue: `SM_CA_MW_PR008_PR009_TransferGuides_01` had one generated collision envelope spanning both physical guide rails and filling the intended open channel. Isolated `/Game/LineBoss/Maps/LB_PressShop_PR009TransferGuideCollisionCandidate_v089`, parented directly from v087, preserves identical guide vertices, triangles, bounds and materials while replacing that envelope with two authored side boxes. Clear channel is `2181.4 mm`, providing `190.7 mm` clearance per side for the Pro `1800 mm` across-strip blank.
- v089 passes: UE 5.8 native build; both focused automations 1/1 with zero warnings/failures; static collision with 98 station primitives plus the two guide boxes and zero complex-as-simple; runtime motion/save/authority/isolation; physical guard/chassis/interface traces; full blank sweep; all 26 full-contract mover sweeps with zero unapproved overlaps; and two non-partial `1040 cm` navigation routes with no protected-space points.
- Four fresh v089 images are under `Saved/ValidationScreenshots/PressShopIntegration/v089_pr009_transfer_guide_collision/`. `Saved/Audits/press_shop_pr009_visual_review_v089.json` records **RELEASE COLLISION / RUNTIME / SAVE / AUTHORITY / NAVIGATION PASS; TYPOGRAPHY / SERVICE-SIDE CAMERA / ENVIRONMENT / PRESENTATION HOLD; RETAINED; NOT PROMOTED**. The next isolated successor must keep v089 geometry/collision, first add the measured south-west service/hero camera to show the existing HMI and electrical cabinet, then improve CCTV-legible Cairnwell/Moorcross identity and installed presentation before any PR-009 promotion. PR-010 and robot polish remain on hold.

# 2026-08-04 PR-009 south service camera and measured fascia identity v090-v092

- `/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraCandidate_v090` is an isolated v089 derivative with a fixed south-west service camera at `(0,-2820,400)` cm targeting `(550,-2020,130)` cm. Fresh evidence proves the existing local HMI, electrical/service cabinet, guarded transfer, gantry and blank stack from the remote-operations service side. v089 geometry, collision and authority remain unchanged.
- v091 attempted to reuse the north guard identity plate's reverse face. Measured probing and the fresh capture proved that plate remains about `5.2 m` behind the south service controls and is partly obscured. `/Game/LineBoss/Maps/LB_PressShop_PR009ServiceIdentityCandidate_v091` is **rejected / not promoted / not a parent**.
- `/Game/LineBoss/Maps/LB_PressShop_PR009ServiceFasciaIdentityCandidate_v092`, parented directly from v090, places Cairnwell Automotive / Moorcross Works / PR-009 Automated Blank Stacker text `0.85 cm` outside the measured south face of the existing authored PR-009 interaction fascia at world Y `-2258.75 cm`. It adds no plate and changes no process geometry, collision or navigation. Line Boss remains absent in-world.
- Fresh v091/v092 comparison evidence and hashes are recorded in `Saved/Audits/press_shop_pr009_service_identity_visual_gate_v092.json`. v092 is **SERVICE-FASCIA IDENTITY DIRECTION PASS / INSTALLED PRESENTATION AND FULL RELEASE GATES HOLD / RETAINED / NOT PROMOTED**. Guard mesh/rail interference, installed cable/ground/anchor detail, hall/floor condition, a complete four-camera suite and all repeated technical gates remain open. PR-010 and robot polish remain on hold.

# 2026-08-04 enclosed automated-machine direction

- The user selected connected enclosed automated machine cells as the normal production presentation: material enters a controlled opening, the named operation occurs inside and the correct intermediate or finished part exits toward the next station. Detailed authority is `Docs/MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md`.
- This is a reusable casing/state system, not permission to replace simulation with opaque boxes. Existing validated rollers, gantries, lifts, dies, transfers, sensors, buffers and traceability remain animated inside; inspection glazing, internal CCTV/drone views and isolated maintenance-open states expose them deliberately.
- PR-009 is the first enclosure pilot because v089 already proves its machinery, collision, transactional flow, authority, save and navigation. Preserve v089 and retained v092 service identity. Keep PR-009 infeed/outfeed and the south HMI/electrical cabinet accessible, use approved open mesh only at real transfer/access hazards, and do not start PR-010 until the reusable PR-009 shell passes fresh Unreal visual and runtime gates.
- User authority for the four press trains is management-game simulation depth: make each train look and sound operational without reproducing every internal working part or physically deforming sheet. One truthful saved gameplay cycle drives blank arrival, guarded feed, visible ram/die stroke, synchronized layered spatial audio, formed-panel mesh/state replacement, downstream transfer, HMI, throughput, energy, wear and faults. Detailed rule: `Docs/MACHINE_ENCLOSURE_DESIGN_AUTHORITY.md`.

# 2026-08-04 PR-009 enclosed-cell v095 accepted baseline

- The PR-009 enclosure pilot has passed its required candidate and accepted-map gates. The stable accepted map is `/Game/LineBoss/Maps/LB_PressShop_PR009Accepted_v095`; its gated source candidate remains `/Game/LineBoss/Maps/LB_PressShop_PR009EnclosureReleaseCandidate_v095`. Preserve protected technical parent v089. v094 remains an unpromoted first pilot; rejected v091 and v093 must not become parents.
- Seven reusable identity-scale enclosure modules provide the structural shell, layered panels/roof, inspection glazing, interlocked service door and hardware, utilities and roof equipment. Normal production remains closed and interlocked; validated conveyors, gantry, lift, stack and carrier mechanisms remain visible through deliberate glazing/process views. Infeed/outfeed portals, south-side HMI/electrical access and approved open-mesh transfer guarding remain available.
- Native `ALBPR009Station` owns the service-door hinge. The door restores from saved `bGuardsClosed`, interpolates between 0 and 105 degrees at 90 degrees/s and is bound by semantic role rather than actor order. The shell has ten authored simple structure boxes and one authored simple door box; the old guard collision is disabled. The full Pro `2600 x 1800 mm` blank and all 26 configured mover contracts clear with zero unapproved overlaps.
- Final candidate verification is `Saved/Audits/PR009_InMap_v095/PR009_ENCLOSURE_RELEASE_VERIFICATION.json`: native build passed; both focused automations passed 1/1 with zero warnings/errors; static identity/collision/authority, runtime motion/transaction/save/isolation, physical shell/door/portal, two non-partial `1040 cm` navigation routes and full-contract sweep gates passed. Matching integrity snapshots prove 7 protected maps, 126 PR-009/enclosure source files, 1772 robot files and the held PR-010 scope did not change during the final gate run.
- Seven fresh images are under `Saved/ValidationScreenshots/PressShopIntegration/v095_pr009_enclosure/`. They were manually inspected against Pro Sheet 02, the PR-009 v002 source render and enclosure v002 hero. The enclosed silhouette, controlled portals, external service equipment, Cairnwell Automotive / Moorcross Works / PR-009 identity and deliberate internal visibility pass at management-camera distance. Line Boss does not appear in-world.
- Promotion used two clean Unreal sessions to avoid an editor world-lifetime conflict. Receipt: `Saved/Audits/PR009_Accepted_v095/promotion_receipt.json`, status `PASS__PR009_V095_ACCEPTED_BASELINE_CREATED`, with 2231 actors, seven enclosure modules, one PR-009 authority, one flow controller and zero candidate-not-promoted tags. Direct static, runtime/save/authority, physical and navigation validators also passed on the accepted map under `Saved/Audits/PR009_Accepted_v095/`.
- This is acceptance of the PR-009 enclosed-cell baseline, not a claim that the full Press Shop is release-complete. Shared hall exposure, roof/service-grey response, floor ageing and installed environmental dressing remain later factory-wide polish. The reusable enclosure direction may now proceed to PR-010, preserving PR-009 v095 and applying station-specific dimensions/interfaces rather than cloning its exact shell. Both support robots remain deferred; preserve MR-01 v021 as an unpromoted structural/runtime/collision/save checkpoint with its visual gate open.

# 2026-08-04 PR-009 v095 acceptance revoked by cross-station axis audit (supersedes the acceptance above)

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
- Exact-map static authority/branding passes with one native station, eight carriers, nine stacks, eight open guards and 52 accounted hidden collision proxies. UE 5.8 native build passes. PR-010, PR-009, PR-008 and traceable PR008-to-PR009 automations each pass 1/1. Runtime stores nine stacks including quality hold, dispatches one, proves trusted/untrusted authority and safe-save restoration, exercises all five presentation motions across more than 2,200 frames, and reports zero new temporal overlaps. All three non-partial protected navigation routes pass.
- Map-bound HMI PIE proof is explicit: the exact v102 map changes the visible fields to `REMOTE RESERVATION WAIT` and `3 / 8 STACK POSITIONS`. Consolidated evidence is `Saved/Audits/PR010_ReleaseArt_v102/PR010_V102_RELEASE_VERIFICATION.json`.
- Four fresh images are under `Saved/ValidationScreenshots/PressShopIntegration/v102_pr010_release_art/`. Direct Sheet 03 review passes the enclosed automated silhouette, upper service deck, repeated drives/routes, detailed lane identity and unobstructed HMI direction, but v102 is **retained and not promoted**: close views still need installed conduit/hose/hatch/fastener density, calmer roof/stack highlights, CCTV-readable stack IDs and shared hall/floor finishing. Visual authority is `Saved/Audits/PR010_ReleaseArt_v102/pr010_visual_review_v102.json`.
- No Pro redesign is required. Next create isolated v103 from v102, preserve every technical contract, add dimensioned installed-service detail and calibrated materials/identity, then repeat all exact-map technical and fresh fixed-camera gates. Press Train A-D datums remain TBC and must not be invented.

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

- Existing Pro Sheets 04/05 remain sufficient; no new exterior redesign is required and production placement remains `TBC_NOT_INVENTED`.
- v036's exact material reassignment passed technically but did not create a decisive camera-distance improvement. v037's first cue placement faced blank module backs toward camera and is rejected. Both remain unpromoted evidence.
- Reusable source `SourceAssets/PressTrains/Shared/StageExteriorCues_v001/` now supplies distinct S03 forming-pressure, S04 trim-scrap, S05 pierce-slug and S06 restrike-quality modules. Its source audit passes dimensions, hashes, material separation and authority.
- Retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038`. Static audit `press_train_a_stage_cue_facing_static_v038.json` passes 121 presentation meshes, 173 scoped actors, four unique cues, seven facades, five cameras, unchanged bounds and zero failures.
- All five fresh images are in `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v038/`; `press_train_a_visual_review_v038.json` retains the visibly differentiated enclosed-machine direction but keeps the release-art gate open.
- Next improve shared crown/frame mass, physical identity/HMI legibility, S01/S07 material-flow presentation and die-change-side mechanics before beginning runtime gates. Do not promote v036-v038.

# Train A identity experiments v039-v045 rejected; v038 still retained (2026-08-05, latest)

- v039 failed safely on a semantic-tag resolver. v040 corrected it but proved inherited plate/text face alignment unreliable. v041-v043 explicit plate/TextRender variants passed static counts but remained faint, mirrored or incomplete in fresh overview/draw evidence.
- `RaisedIdentityPlates_v001` then produced seven dimensioned 73 x 1200 x 400 mm fabricated plate sources with separated accent, fastener and raised-letter materials; its source audit passes. v044 imported them and passed the corrected 128-presentation/173-scope static gate; v045 tested the reverse face.
- Fresh draw evidence for v044-v045 shows plate bodies and fasteners but not readable font-mesh faces. Reject v039-v045 and do not promote them. Retained parent remains `/Game/LineBoss/Maps/LB_PressTrainAStageCueFacingCandidate_v038`.
- Next build S01-S07 identities from explicit segmented box geometry, inspect draw/overview first, then continue crown/frame mass, S01/S07 material flow and die-change-side evidence.

# Press Train A v047 retained segmented-identity parent; release-art hold (2026-08-05, latest)

- No new Pro exterior redesign is required. Sheets 04/05 remain sufficient and global Train A-D datums/rotations remain `TBC_NOT_INVENTED`.
- Reusable source `SourceAssets/PressTrains/Shared/SegmentedIdentityPlates_v002/` contains seven explicit raised cuboid-segment S01-S07 identity assemblies. It uses no TextRender, font mesh, decal or texture dependency. Source audit `Saved/Audits/PressTrains/press_train_segmented_identity_plates_source_audit_v002.json` passes seven 98 x 1180 x 390 mm assets, dimensions, hashes, materials and authority.
- v046 proved the segmented identities readable but left S07 behind the wider unload/inspection facade. v047 moves only that S07 assembly to `X=-485 cm`, clearing the endpoint face while retaining the exact 173-actor scope, established train envelope and all five cameras.
- Current retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainAS07IdentityClearanceCandidate_v047`. Exact static evidence `Saved/Audits/PressTrains/press_train_a_s07_identity_clearance_static_v047.json` passes 128 presentation meshes, seven stages/facades, four stage-specific cues, five cameras, unchanged `15000.005 x 56000.001 x 11350 mm` bounds and zero failures.
- All five fresh exact-map 1920x1080 captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v047/`. Original-resolution Pro comparison is `Saved/Audits/PressTrains/press_train_a_visual_review_v047.json`; it retains the physical identity direction but keeps a release-art hold. Do not promote v039-v047.
- Next improve shared press crown/frame mass and camera-visible S01 blank feed/S07 panel discharge, then strengthen opposite-side die-cart/dock/tow/clamp/connector/cable-chain evidence. Runtime/HMI/motion/audio/flow/fault/save/collision/navigation/crane-clearance gates remain deferred until those visual holds pass.

# Press Train A v051 retained crown/endpoint refinement; release-art hold (2026-08-05, latest)

- Reusable `CrownEndpointPresentation_v002` source supplies a deep fabricated S02-S06 crown assembly with recessed shared drive evidence plus S01 visible blank-feed and S07 visible formed-panel discharge assets. Source audit `Saved/Audits/PressTrains/press_train_crown_endpoint_presentation_source_audit_v002.json` passes three dimensioned assets, hashes, local bounds, materials and TBC authority.
- v048 was hidden behind the facades; v049 projected the new hardware too far toward camera; v050 reduced the offset and brightness but retained an oversized repeated drive guard. Those are preserved unpromoted calibration history.
- Current retained unpromoted parent is `/Game/LineBoss/Maps/LB_PressTrainACrownEndpointRefinementCandidate_v051`. It replaces the seven presentation actors in place with recessed v002 geometry. Exact static audit `Saved/Audits/PressTrains/press_train_a_crown_endpoint_refinement_static_v051.json` passes 135 presentation meshes, 180 scoped actors, five verified v002 crown bindings, both endpoint bindings, five cameras and unchanged `15000.005 x 56000.001 x 11350 mm` bounds.
- Five fresh exact-map captures are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_v051/`. Direct Pro review `Saved/Audits/PressTrains/press_train_a_visual_review_v051.json` retains the crown/endpoint direction but keeps a release-art hold. Do not promote v048-v051.
- Next improve opposite-side service lighting and author camera-readable die-cart/dock clamps, tow points, connectors and cable-chain engagement. S01 blank-stack/S07 panel contents still need stronger camera-distance material-state proof. The v002 import also has three non-fatal missing-smoothing-group warnings that must be removed in a clean later import gate before promotion.

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

- User correctly rejected the v005/v006 positive-pitch appearance. Preserve all earlier candidates and continue from unpromoted source `SourceAssets/ControlRoom/MainControlRoom_v006` and playable Unreal map `/Game/LineBoss/Maps/LB_MainControlRoom_OperatorAimCandidate_v008`.
- All console monitor faces, frames, authored UI surfaces, terminal screens and mothballed masks now use `-12` degree Blender X pitch, aiming down toward the seated 1.12 m operator eye while retaining the Pro Sheet 05 10-15 degree tilt magnitude.
- Import audit: `Saved/Audits/ControlRoom/main_control_room_operator_aim_import_build_v008.json`. Fresh actual game-mode image: `Saved/ValidationScreenshots/ControlRoom/v008_operator_aim/main_control_room_v008_runtime_seated.png`. Visual review: `Saved/Audits/ControlRoom/main_control_room_operator_aim_visual_review_v008.json`.
- The physical orientation sub-gate passes, but v008 remains **not promoted**. Continue with the compiled authority-backed PR-004 console actor, seated interaction, a real selected CCTV/render-target feed, then collision/save/performance and final fixed-camera Pro gates.

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

- User-supplied real tandem stamping references establish the S07 robot direction: compact press-adjacent arm, slim cast/rectangular links, enclosed circular joints, short pedestal, visible wrist/tooling and restrained cabling.
- v014 is visually rejected and must never be promoted. Its technical gates pass, and a fresh static audit proves all nine robot actors match the v009 source transforms and hierarchy; the failure is geometry/proportion readability, not a broken attachment chain.
- Rejection: `Saved/Audits/PressTrains/press_train_a_robot_visual_rejection_v014.json`.
- Static hierarchy evidence: `Saved/Audits/PressTrains/press_train_a_robot_hierarchy_static_v014.json`.
- Source-only v010 now provides continuous overlapping joints without changing pivots, roles, hierarchy, actor count, envelope or the validated whole-train transfer architecture. It is not imported, integrated or promoted; fresh Unreal visual gates remain mandatory.
# 2026-08-06 — Robot family pack intake and connected Train A v016

- User-supplied Cairnwell robot-family sheets are accepted as **visual direction only** for six distinct variants: press handling, body weld, paint, PR-004 depackaging, low-profile coil AGV and pallet/forklift logistics AGV. Performance, safety, certification and unverified dimensional values shown on the generated sheets remain TBC.
- v015 is rejected and is not a parent: the legacy Blender-FBX-Unreal conversion mirrored directional mesh-local Y while actor world Y remained correct, separating the S07 robot even at rest.
- v016 is a fresh direct v013 child using the same validated v011 source plus a robot-only local-Y preflip in staging. Fresh rest and peak-motion Unreal captures show a connected arm and attached vacuum tooling.
- `/Game/LineBoss/Maps/LB_PressTrainARobotAxisCorrectedCandidate_v016` SHA-256 `AC4AE375AC4A014586A4DA4AF62EF009504B790BD675D65B9D6B066773BC2183`; static and live PIE pass, robot motion reaches 34.68 degrees, exact automation passes 1/1 and full Press Shop passes 15/15.
- **Retain v016 only as the connected robot axis-integration parent.** Family-quality casing, material response, joint proportions and tooling detail remain visually open; do not promote. Intake: `Saved/Audits/PressTrains/press_train_a_robot_family_design_pack_intake_v016.json`.

# 2026-08-06 — Train A S07 Cairnwell robot-family successor v017 retained

- The owner supplied three Cairnwell industrial robot-family design sheets covering distinct press-handling, body-weld, paint, PR-004 depackaging, coil-AGV and pallet/forklift-AGV variants. They are visual authority only; their payload, reach, speed, safety, certification and other unverified engineering figures remain TBC and were not adopted.
- Source-only `AssemblyStudy_v012` is a direct cosmetic successor to v011. It keeps all 336 Train A actors, the exact 15,000 x 56,000 x 10,750 mm assembly bounds, all 9 S07 runtime actors and every pivot/role/hierarchy edge. It changes the press robot to charcoal cast housings, restrained orange joint accents, service detailing, cable routing and a steel multi-cup vacuum crossbar.
- Retained isolated Unreal successor: `/Game/LineBoss/Maps/LB_PressTrainARobotFamilyCandidate_v017`, SHA-256 `E647EB62C3552CF39EFFE83687C2A3AA058C0323F2DD53DACFD5FD0738B02E42`. It is a fresh direct v013 map child and uses the validated robot-local-Y staging correction.
- Fresh source, static, PIE and fixed-camera evidence passes. Peak robot articulation is 34.56 degrees with one visible workpiece; controlled stop, fault recovery, isolation, HMI and save pass. Exact Train A automation is 1/1 and full Press Shop automation is 15/15.
- **Retain v017 as the current Train A S07 press-handling robot visual successor. Do not promote the whole Train A area.** Release collision/swept volume, navigation/service clearances, sound, broader cause-and-effect and whole-area release comparison remain open. Decision: `Saved/Audits/PressTrains/press_train_a_robot_family_visual_decision_v017.json`.

# 2026-08-06 — Train A physical gameplay successor v024 retained

- `/Game/LineBoss/Maps/LB_PressTrainAPhysicalGameplayCandidate_v024` is a fresh direct child of protected v017, SHA-256 `2AEE55ABF7AFB975CD0D9558AB84846F45B626F0455F24D9AE857EA803651584`. Failed/partial v018-v023 are preserved and are never parents.
- v024 removes all seven inherited station-wide proxy boxes and uses the source-derived collision plan: 61 fixed blockers, 65 QueryOnly movers and 489 simple boxes. Visual geometry, materials, lighting and native motion authority are unchanged.
- Static and live PIE gates pass. The 34 x 88 cm standing-player capsule has floor support and a clear operator aisle; runtime navigation produces a valid complete 3,800 cm path; the maintenance approach is clear; the guarded entry blocks; all movers remain non-blocking; one full cycle completes with zero unexpected robot/blocker overlaps.
- The original Train A motion/safety/save validator passes on v024 with 34.34-degree robot motion and exactly one visible workpiece. Exact Train A automation passes 1/1 and all `LineBoss.PressShop` regressions pass 15/15. Fresh unload evidence: `Saved/ValidationScreenshots/PressShopIntegration/press_train_a_motion_v024/press_train_a_motion_v024_s07_unload.png`.
- **Retain v024 as the unpromoted Train A physical-gameplay successor.** State-driven sound, authoritative installed Train A-D datums, cumulative whole-hall integration and release-art comparison remain open; unverified robot engineering values remain TBC. Decision: `Saved/Audits/PressTrains/press_train_a_physical_gameplay_decision_v024.json`.

# 2026-08-06 — Train A state-driven spatial audio successor v027 retained

- `/Game/LineBoss/Maps/LB_PressTrainAAudioRuntimeCandidate_v027`, SHA-256 `00225848C15668BE523F181FD81A8C1FB472675A724B72847B9E206A7C99848F`, is a fresh direct child of retained v024. Failed partial v025 is never a parent; v026 is superseded by the cleaner sound revision.
- Original `Audio_v002` provides eight 48 kHz mono PCM sources with zero clipped samples. Native Train A authority drives six spatial emitters for hydraulic power, transfer servo, robot servo, warning alarm, press cues and safety/transition cues.
- Live PIE proves cause/effect for destack, press stroke, robot unload, controlled stop, guarded-access fault/alarm and distinct emergency stop. Motion, HMI, safety, isolation and save remain green.
- Exact physical inheritance proves 366 actors, zero additions/removals and zero collision/navigation/transform changes from v024. Exact Train A automation passes 1/1; full `LineBoss.PressShop` passes 15/15.
- **Retain v027 as the unpromoted Train A physical-gameplay/audio successor.** The robot no longer needs a separate task. Subjective whole-hall mix, installed Train A-D datums and cumulative release-art integration remain open. Decision: `Saved/Audits/PressTrains/press_train_a_audio_runtime_decision_v027.json`.

# 2026-08-06 — isolated Press Trains B-D shared-runtime variants v001 retained on visual hold

- Native `ALBPressTrainAStation` is now the shared Train A-D runtime class. `ConfigureTrainVariant` accepts only `TRAIN_A` through `TRAIN_D`, exposes distinct display/part-family/accent identity, uses PTB/PTC/PTD output-panel namespaces and rejects cross-train save restoration. Train A behavior remains unchanged; exact native automation passes.
- Fresh direct v027 isolated successors preserve the 366-actor runtime/physical/audio contract and deliberately keep world placement `TBC_NOT_INVENTED`: Train B `/Game/LineBoss/Maps/LB_PressTrainBIsolatedVariantCandidate_v001` (`EA511F15D2E70C0FD84560CF8DD8B6909512ED2F051EC1B8230BEAD29BBAA30E`), Train C `/Game/LineBoss/Maps/LB_PressTrainCIsolatedVariantCandidate_v001` (`1F7282069883B84ECB537A666CE860902BA6B41F316752B4EE17775BA92423F6`) and Train D `/Game/LineBoss/Maps/LB_PressTrainDIsolatedVariantCandidate_v001` (`300ABFE9E5C9B259A68F366AAD2E2B235FA777244921003F9F5CDD1FCFD62982`).
- B uses green deep-draw/heavy-scrap cues, C uses orange closure/flexible-gripper identity and D uses purple smaller-die/high-variety cues. Each live PIE validator passes motion, one-workpiece flow, beacons/HMI, controlled stop, access fault/recovery, isolation and save. All 15 `LineBoss.PressShop` regressions pass in `Saved/Automation/PressTrainSharedVariantAuthority_v001_FullPressShop/`.
- Nine fresh PIE fixed-camera frames are under `Saved/ValidationScreenshots/PressShopIntegration/press_train_{b,c,d}_variant_v001/`. Direct Sheet 06-08 review retains all three maps as isolated technical/directional parents only: B and D tooling direction reads, while C's orange identity and mixed-model gripper difference are not yet legible enough; the inherited black isolation surround is not an installed release comparison.
- **RETAIN B-D V001 AS UNPROMOTED ISOLATED TECHNICAL/DIRECTIONAL PARENTS; VISUAL RELEASE HOLD; DO NOT PLACE OR PROMOTE.** Protected Train A v027 and cumulative v213 hashes remain unchanged. Decision: `Saved/Audits/PressTrains/press_train_bcd_isolated_variant_runtime_visual_decision_v001.json`. Next improve Train C identity/gripper readability and capture B/C operator-side tooling evidence without inventing installation datums.

# 2026-08-06 — B/C visual-successor v002-v004 disposition

- B/C v002 passed build and PIE, but its material-slot and C gripper-detail changes remained effectively indistinguishable from v001 in fixed hero/operator-side views. Preserve both maps as visually rejected; never parent or promote them.
- B v003 stopped correctly because its new stage plates retained a blocking collision profile. Preserve that failed partial; C v003 was never created; never parent from v003.
- Fresh B/C v004 maps were rebuilt directly from v001 with 21 visual-only actors each, explicit `NoCollision`, 387 total actors and zero inherited transform changes. Both passed live cycling, motion, controlled stop, access-fault recovery, isolation and save authority.
- Fixed-camera review still fails: the isolated scene is over-bright, the plates wash out or read too small, and B/C family identity remains insufficiently distinct. **VISUALLY REJECT B/C V004; DO NOT PROMOTE OR PARENT FROM IT.** B/C v001 remain the isolated technical/directional parents.
- Consolidated decision: `Saved/Audits/PressTrains/press_train_bc_visual_successor_lineage_decision_v004.json`. Any successor must be a fresh v001 child and correct source-scale materials/exposure rather than add unreadable signage. Installed datums remain `TBC_NOT_INVENTED`.

# 2026-08-06 — standing-player floor-spawn runtime correction

- A standalone v213 owner free-roam launch exposed a real native defect: when no `PlayerStart` supplied a transform, `ALBControlRoomPawn` spawned with its 88 cm half-height capsule centred at world `Z=0`, embedding the operator in the floor and making the correct `WASD` bindings appear dead.
- `ALBControlRoomPawn::BeginPlay` now resolves a standing spawn against the first static surface below it before locking the permitted walking area, placing the capsule centre at floor impact plus capsule half-height plus 2 cm. A half-height fallback is used when no surface is found; seated behavior is unchanged.
- Native Editor Development rebuild succeeded. A fresh standalone v213 session using `LBControlRoomGameMode` logged the resolved seat at `Z=95` and camera at `Z=175`; the process remained responsive. Protected v213 stayed byte-identical at `1790B48ABF75762A474C6F3FDB91B2ABD3AD9088B5430D08DC1905154CDF6554`.
- Runtime/build evidence: `Saved/Audits/ControlRoom/standing_player_floor_spawn_runtime_fix_v001.json`. Focused control-room automation and a fresh collision/navigation walking test remain required after the owner's live free-roam session ends.

# 2026-08-06 — unrestricted owner inspection mode v001

- The bounded standing control-room pawn and built-in `DefaultPawn` do not reproduce Unreal Editor free flight: the former is intentionally room-bounded and the latter retains a blocking collision sphere. A dedicated native inspection path now exists: `ALBFreeRoamGameMode` plus `ALBFreeRoamPawn`.
- The pawn is an unbounded `ASpectatorPawn`, explicitly `NoCollision`, starts no lower than `Z=500 cm`, uses Unreal's native `WASD`/mouse/vertical-flight bindings and is tuned to 6,000 cm/s maximum speed. It is deliberately inspection-only and does not replace the standing-player production/control authority.
- Editor Development build passed. Fresh standalone v213 runtime logged `FreeRoam spectator start=X=0 Y=0 Z=500 collision=NoCollision`; the live process is responsive. Protected v213 remains byte-identical.
- Evidence: `Saved/Audits/ControlRoom/unrestricted_free_roam_runtime_v001.json`. Add/run a focused defaults/input automation test after the owner inspection session ends.

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

- Fresh direct v255 child `/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v260`, SHA-256 `4A7DC500CE8B23CFEA06EC81B4CC88BE8DF4574B2C6F99856703C55B71383B8F`, installs two independent MR01 maintenance robots, two independent CR01 cleaning robots and four charging/service docks. Protected v255 remains byte-identical at `38884454F39F649B9767517ECE6A68B7029B1D27219FD5FBA81483FF2DC71A23`.
- All four robots dock straight in rear-first; none docks sideways. Native charging-contact error remains exactly `0.0 cm`. The imported dock presentation required a visual-only `180°` yaw correction so its open portal and Cairnwell identity face the service aisle; robot roots, charging contacts, collision proxies and runtime authority did not move.
- Exact v260 gates pass: 16 intended fleet blockers, zero unexpected overlaps, playable-management Start/Pause/Stop and train isolation, two PR009 nonpartial routes, three PR010 nonpartial routes, `LineBoss.PressShop` 16/16 and `LineBoss.SupportRobots` 3/3 with zero warnings.
- Five exact-map live captures under `Saved/ValidationScreenshots/SupportRobots/PressShopFleet_v260/` prove four unique docked/charging authorities, readable open-front MR01/CR01 berths and a contextual low-oblique support-zone overview. Workshop dividers make the per-berth views authoritative for robot readability.
- **RETAIN V260 AS THE UNPROMOTED CUMULATIVE PRESS SHOP SUPPORT-FLEET PARENT.** v254 and v256-v259 are rejected/superseded visual or collision evidence and must never be parents. Dispatch-route gameplay, dock moving-service sweeps, final hall lighting/material comparison and subjective audio remain open. Decision: `Saved/Audits/SupportRobots/press_shop_support_fleet_visual_runtime_decision_v260.json`.
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
# 2026-08-07 - Latest active builder/storage checkpoint v454

- Player-built Press Shop storage is now functional authority, not decorative paint. New `ALBPressShopStorageZone` supports deterministic identity, type, capacity/occupancy, ingress/egress and bounded store/withdraw operations.
- `ALBPressShopBuildAuthority` validates authored storage bays, permitted storage types, protected-area clearance and AGV/forklift logistics-spine reach.
- Focused Unreal automation `LineBoss.PressShop.Builder.StorageAuthority` passes 1/1 with zero warnings/errors at `Saved/Automation/StorageAuthority_v454/index.json`.
- Research/technology and vehicle-sales/dealership gameplay are explicitly out of current scope. Near-term gameplay remains factory layout, material supply, automation, quality, faults, maintenance and throughput; finished output ends at an outbound buffer.
- No retained map was modified or promoted. Next: management storage placement UI and preview, authored v438 storage/logistics authority, save DTO binding, visual floor/signage and AGV dispatch integration.
## 2026-08-07 — automatic inter-machine transport authority (v457)

- Added authored process-port components and a strict world connection authority for player-built machinery.
- A newly placed machine can automatically connect each required input to the nearest compatible predecessor only when direction, exact next process stage, material class, transport kind and authored maximum range agree.
- Generated links use a deterministic direct/dogleg spline and retain functional transferred-unit state. Partial multi-input creation rolls back if any required predecessor is unavailable.
- UE 5.8 editor target compiled successfully.
- `Saved/Automation/FactoryAutoTransport_v457/index.json`: `LineBoss.FactoryBuilder.Transport.AutomaticNextStageConnection` passed 1/1 with zero warnings/errors.
- This is functional routing authority, not final release visuals. Procedural roller/belt meshes, supports, collision/navigation, save/load, placement integration and the complete lorry-to-finished-panel runtime chain remain open.
## 2026-08-07 — visible transport and parallel-capacity successor (v458)

- Automatic transport links now build visible modular rails, rollers/belt deck and floor supports from the validated spline route using instanced meshes with blocking collision.
- Process ports now have authored `MaximumConnections`. Normal station ports remain one-to-one; distributor/buffer outputs may explicitly feed parallel next-stage machines.
- Exact next-stage, material, transport, range and duplicate-link gates remain fail-closed. This supports player responses to bottlenecks without allowing process-stage skipping.
- UE 5.8 editor target compiled successfully.
- `Saved/Automation/FactoryAutoTransportVisualParallel_v458/index.json`: 1/1 passed, zero warnings/errors. The test covers dogleg generation, visible rail/roller/support instances, functional unit transfer and one authored source feeding two parallel machines.
- Open: replace Engine primitive visuals with Cairnwell release modules/materials; builder catalogue for individual machines/buffers; save/restore of placed machines and links; route junction presentation; collision/navigation and in-game visual gate.
## 2026-08-07 — player-facing automatic replenishment buffers (v460)

- Functional player-built storage zones now support automatic pull replenishment using player-facing terms only: reorder level, replenishment batch, outstanding loads, requested units, starved and blocked.
- Do not expose the manufacturing-method term in UI/help; the user explicitly requested `Automatic Replenishment` wording.
- Consumption at/below the configured reorder level raises bounded replenishment demand; received units close the outstanding demand. Full/empty buffer state is queryable for management UI and dispatch authority.
- UE 5.8 editor target compiled successfully.
- `Saved/Automation/BuilderReplenishmentTransport_v460/index.json`: storage/replenishment plus automatic transport tests passed 2/2, zero warnings/errors.
## 2026-08-07 — persisted builder topology and dragged coil storage (v468)

- Automatic transport links now capture/restore by stable source/target process-port IDs, including parallel topology and transferred-unit count, through the main campaign save root.
- Restore reuses existing link actors where possible to avoid runtime allocation hitches. Focused v462 and campaign v464 tests passed without warnings.
- Player storage zones now capture/restore identity, transform, footprint, type, capacity, occupancy and complete Automatic Replenishment state. The main campaign controller captures/restores player storage through the single map build authority.
- Coil-storage placement changed from a fixed click footprint to click-drag / hold-X sizing. The HUD previews generated columns, rows and capacity before release/confirmation.
- Coil stand count uses the accepted PR-003 authored pitch: 220 cm along a row and 600 cm between row centrelines. Arbitrary capacity entry is rejected when an authored layout can be calculated.
- UE 5.8 target compiled successfully. `DraggedStorageLayout_v467` passed storage + whole-campaign tests 2/2; `DraggedStorageHUD_v468` passed controller/HUD workflow 1/1. All had zero warnings/errors.
- No retained production map was modified or promoted. In-game visual/input capture of drag placement remains required before promotion.

## 2026-08-07 — generated multi-material storage modules v471

- The dragged storage footprint now persists its generated rows, columns, authored unit pitch and clearance rather than only a numerical capacity. Bare-coil areas construct one permanent saddle per valid slot and show cylindrical coils only for occupied slots.
- The same authority generates type-appropriate module positions for prepared blanks, finished-panel stillages, scrap, maintenance parts and quarantine material. Parts use pallet/rack positions; inventory visibility follows occupancy while empty positions remain readable.
- Storage-state version 2 retains exact generated layout data and accepts version 1 for migration. UE5.8 build passes; `DraggedMultiMaterialStorage_v471` proves storage authority and whole-shop campaign save round trips 2/2 without warnings. This remains technical/runtime evidence pending authored map bays, production meshes/materials and live visual/navigation review.

## 2026-08-07 — storage process-graph integration v472

- Every functional player-built storage zone now exposes stable identity-derived ingress and egress process ports. The ports carry the storage material, transport kind and ordered process stage, so buffers participate in the same strict automatic connection authority as machines.
- Bare-coil storage proves the first real chain edge: a stage-zero inbound dock automatically generates one AGV handoff into the zone's stage-one ingress. Egress supports authored branching to parallel next-stage equipment.
- UE5.8 build succeeds. `StorageProcessGraph_v472` passes storage authority, automatic next-stage transport and whole-shop campaign persistence 3/3 without warnings. Individual machine catalog/placement and live map visual/navigation evidence remain open.

## 2026-08-07 - Car Manufacture read-only structural study and ordered-machine compile

- Inspected only the installed game's exposed package structure and metadata for architectural inspiration. No proprietary game assembly was decompiled and no code, meshes, textures or other assets were extracted or copied.
- The visible structure supports a data-driven approach: separate blueprint/item/factory-entity addressable bundles, a dedicated blueprint-preview scene, runtime preview generation, A* and navigation packages, reactive UI support, dependency injection and structured serialization. These observations are architectural indicators only, not proof of exact internal implementation.
- Apply the useful patterns in an original Cairnwell system: data assets for the build catalogue, generated catalogue thumbnails, a context-filtered next-valid-machine menu, grid/clearance preview, explicit automatic links, AGV path validation and modular save records. Retain variable management-camera zoom and separate full 3D standing/free-roam presentation.
- Added and compiled the preliminary `ALBFactoryBuildMachine` actor for ordered machine types and authored process ports. It is technical scaffolding only. Its generic Press Train entry must not become a parallel train authority; final placement must bind the existing press-train identity/station system.
- UE 5.8 editor target compiled successfully after the new actor was added. No retained production map or visual lineage was modified or promoted.

## 2026-08-07 - ordered machine catalogue and native press integration v475

- Added an Unreal world-subsystem catalogue that exposes only process-valid machine types. The initial sequence is inbound delivery, bare-coil storage, depackaging, decoiler, prepared-blank storage, native press train, inspection, finished-panel storage and outbound dock. Duplicate capacity remains possible after the required predecessor exists; the single inbound authority cannot be duplicated.
- Generic surrounding machines receive deterministic identities and persist exact type/transform records. Campaign restore now recreates generic machines and storage before restoring transport topology, so saved port identities exist when links are validated.
- `PressTrain` placement delegates to the existing `ULBPressTrainIdentitySubsystem` and `ALBPressTrainAStation`; it does not spawn the generic technical shell. The native train now exposes stable blank-input and formed-panel-output process ports derived from `TRAIN_A`-`TRAIN_D` identities.
- Player-placed storage attempts its valid incoming automatic connection immediately while retained authored maps may still pre-place unconnected buffers.
- UE 5.8 build passes. `OrderedMachineCatalogue_v473` passed 1/1; `OrderedBuilderRegression_v474` passed ordered catalogue/persistence, transport and storage 3/3; `OrderedBuilderCampaign_v475` passed whole-shop campaign round trip 1/1. No warnings/errors were reported and no retained map or visual lineage was promoted.
- This is functional builder/save authority, not release visual completion. Machine-specific placement envelopes, catalogue HUD integration, complete physical material transfer and fresh map screenshots remain open.

## 2026-08-07 - traceable player-built production chain v477

- Generic player-built machines now retain identified input, output and completed-unit queues through save/restore. Depackaging preserves coil identity, the decoiler emits deterministic blank identities, inspection preserves the native press panel identity and outbound records the exact shipped panel.
- Player storage save state is version 3 and may retain exact unit IDs alongside legacy anonymous quantity. Version 1 and 2 storage states remain accepted for migration. Duplicate/missing IDs and identified counts exceeding occupancy fail closed.
- Added transactional player-built flow authority. Every handoff verifies an existing compatible transport link and rolls source/target state back on failure. Prepared blanks enter the existing native train reservation API, and finished train panels use its existing request/confirm handoff API.
- `PlayerBuiltEndToEndFlow_v476` passed 1/1: identified inbound coil -> coil storage -> depackaging -> decoiler -> identified blank buffer -> native seven-stage train cycle -> identified panel -> inspection -> finished storage -> outbound shipment. This is functional runtime proof, not yet proof of lorry/crane animation or retained-map presentation.
- `TraceableBuilderPersistence_v477` passed storage authority, ordered-machine persistence and whole-shop campaign round trip 3/3 after a successful UE5.8 build. No retained map or visual lineage was promoted.
# Inbound modular source and isolated Unreal review v487-v492 (2026-08-07)

- Seven missing Pro-pack modules were authored under `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v001`: lorry cab, four-coil trailer, dock guides/restraint, controls/signals, receiving saddle, AGV handoff guides and identity scanner. The combined Blender source, seven FBXs, manifest and fixed source render are preserved; all dimensions remain visual/TBC.
- Isolated Unreal import `/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v001` passes plausible centimetre bounds and body-setup gates in `Saved/Audits/PressShopIntegration/inbound_modular_import_v487.json`. The first 100x attempt was correctly rejected before an audit or map save; Blender FBX unit metadata plus Unreal scene-unit conversion requires import scale 1.0.
- The pale/default-material v489 image is rejected. Ten controlled native PBR materials are now bound by exact authored slot identity; `inbound_candidate_materials_v491.json` passes. Fresh isolated review `/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryReview_v492` proves the four coils, dock sequence, retained Coil AGV and retained powered C-hook/bridge direction in `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v492/inbound_overview.png`.
- Decision `inbound_modular_visual_decision_v492.json`: retain v492 only as source/integration direction. Cab/trailer detail, installed crane structure, hook finish, doors/fencing/restraint/signage and all fresh-v438 runtime/save/collision/navigation gates remain open. Exact v438 was never loaded for write and remains unchanged.
## 2026-08-07 — Inbound coil delivery reference and v494 gate

- Four Pro sheets now define the visual sequence: reverse-in four-coil curtain-sided lorry, protected dock, crane/C-hook unload, fixed receiving saddle, then coil AGV handoff to PR-003. Values without verified engineering sources remain TBC.
- Modular v002 import v493 passed technical intake, but isolated Unreal review v494 failed the release visual gate and must not be promoted or used to replace retained v438.
- Preserve `/Game/LineBoss/IndustrialKit/InboundCoilDelivery/Candidate_v002` as source evidence. Next successor must improve cab visibility, trailer/door readability, AGV identity and crane/C-hook silhouette before any v438 integration child is created.
## 2026-08-07 — Inbound v003 retained source, v497 unpromoted

- `Modular_v003` corrects the closed-door error from v494 and gives a coherent coupled tractor/four-coil trailer, raised entrance shutter, separate receiving saddle and lateral AGV handoff.
- Unreal import v496 passed technical intake. Isolated review v497 is improved but still below release visual quality; do not promote it and do not integrate it into retained v438 yet.
- Next work: camera/context successor plus stronger tractor and crane/C-hook readability, followed by another fixed-camera Pro comparison. Retained v438 was not modified.
## 2026-08-07 — Inbound context v501 and external vehicle check

- Installed-context attempts v498 and v500 failed due wall/roof/camera occlusion. v499 failed during map duplication with UE world-memory-leak protection and must not be a parent.
- Clean-context v501 is the best current screenshot but remains a placeholder and is not promoted. The remaining visible blocker is primarily the procedural cab/trailer and crane-detail fidelity, not module count or sequence.
- A small CC0 OpenGameArt vehicle pack was downloaded with provenance and inspected, then rejected for game integration because its American conventional low-poly semi is less faithful than the existing European cab-over placeholder.
- Next: dedicated higher-detail European cab-over tractor source module or a demonstrably better licensed asset, followed by isolated Unreal import and fixed-camera comparison. Do not touch retained v438 until that visual gate passes.

## 2026-08-07 — Inbound cab orientation v503

- v502 proved that positional Rotator `(0, 180, 0)` uses the wrong axis and tips the cab over; reject v502 and do not parent from it.
- v503 uses positional Rotator `(0, 0, 180)`, correctly yawing the current European cab-over so its detailed front is visible and upright. Preserve `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v503/inbound_orientation_test.png` as the orientation result.
- v503 remains unpromoted. The crane is overexposed, the backdrop is too black and the receiving saddle plus AGV handoff are not yet clear enough against the Pro sheets.
- The four-sheet reference sequence is authoritative visually: exactly four trailer coils, protected C-hook unload, fixed receiving saddle and Coil AGV transfer to PR-003. Engineering data remains TBC.
- Retained builder authority v438 remains untouched. The next isolated successor should retain the v503 yaw, rebalance exposure and improve crane/saddle/AGV composition before any fresh direct child of v438 is considered.

## 2026-08-07 — Inbound v504-v505 visual decision

- Fresh v504 and v505 fixed-camera reviews remain rejected and unpromoted. v504 improves orientation/exposure but the crane dominates; v505 confirms exactly four visible trailer coils but crops the cab and reveals that the current crane guarding occludes the receiving saddle/AGV sequence.
- Do not spend another successor on camera-only changes. Build an additive source/layout successor with clearer crane, fixed-saddle and Coil AGV silhouettes and more believable spacing, then repeat isolated Unreal technical and visual gates.
- Decision: `Saved/Audits/PressShopIntegration/inbound_presentation_decision_v505.json`. Retained v438 was not modified.

## 2026-08-08 — Inbound source successor Modular_v004

- Additive source `SourceAssets/Candidate/PressShop/InboundCoilDelivery/Modular_v004` is built from v003. It opens the crane entry presentation, adds a readable rubber-lined receiving V-saddle with stops/locators, gives the AGV handoff its own datum/guides and increases separation so the sequence no longer collapses into one guarded cluster.
- Blender 5.2 successfully produced the blend, nine FBXs, manifest and overview render. All values remain TBC and this is source-only—not an Unreal or visual promotion.
- Next: import v004 into a new isolated Unreal candidate folder, run bounds/body/material gates, then review it with retained crane/C-hook and Coil AGV assets. Do not modify v438 unless that fresh combined view passes.

## 2026-08-08 — Inbound v506-v507 gate

- Candidate_v004 Unreal intake passed all nine scale/bounds/body/material gates in `inbound_modular_import_v506.json`; FBX smoothing-group warnings remain source-pipeline cleanup, not a promotion.
- Fresh combined review v507 proves the improved receiving V-saddle, correct cab and exact four coils, but fails visually because the Coil AGV/handoff is not readable and the crane/context remains below Pro fidelity.
- Preserve source Modular_v004, isolated Unreal Candidate_v004 and rejected v507 evidence. Do not integrate into v438. Next improvement must make the actual Coil AGV/handoff and crane/C-hook presentation release-readable, not merely move the camera.

## 2026-08-08 — Inbound operational-readability review v508

- Fresh isolated v508 adds the retained master coil to the Coil AGV and preserves the powered C-hook's authored material separation, correct upright cab yaw, exact four trailer coils and Modular_v004 saddle/handoff geometry.
- Visual decision: **rejected for promotion**. The trailer obscures the loaded AGV, the crane remains too schematic, and the trailer coils render as dark drums rather than wrapped steel. The fixed view does not yet communicate trailer → C-hook → fixed saddle → Coil AGV clearly enough.
- Evidence: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v508/inbound_operational_readability.png`; decision: `Saved/Audits/PressShopIntegration/inbound_operational_readability_decision_v508.json`.
- Next successor must move the loaded AGV into an unobstructed foreground handoff lane, correct coil material readability and improve the installed crane/C-hook silhouette. Retained builder authority v438 remains untouched.

## 2026-08-08 — Inbound readability reviews v509-v511

- v509 applies the retained pale protective-wrap material to coil surfaces; v510 moves the loaded Coil AGV laterally; v511 adds an AGV-side process view. All are fresh isolated maps and leave v438 untouched.
- v511 finally proves an unobstructed layout containing the exact four-coil trailer, fixed receiving saddle and visibly loaded Coil AGV. Preserve this as layout evidence only.
- None is promoted: dark machinery remains crushed by review lighting and the bridge crane/powered C-hook assembly is still too schematic for the Pro visual standard. See `inbound_operational_readability_decision_v509_v511.json`.
- Next work is a visually finished installed-cell successor using the proven v511 layout, proper factory lighting and higher-fidelity crane/C-hook modules—not further camera churn.

## 2026-08-08 — Inbound installed-cell reviews v512-v513

- v512 corrects the crushed-black exposure and presents the loaded Coil AGV plus four-coil trailer clearly. Retain its lighting/layout direction only; the powered C-hook load and bridge structure remain insufficient in the wide view.
- v513 tested retained generic runway beams and end trucks. Reject it: the pieces float at the attempted transforms and a rear wall occludes the cell. This proves the inbound cell needs a purpose-built installed crane/support source module rather than direct generic-kit recombination.
- Retain Powered C-hook Candidate_v035 and Coil AGV Candidate_v001—their dedicated source validations remain strong. Do not rebuild those accepted assets.
- Audit: `Saved/Audits/PressShopIntegration/inbound_installed_cell_decision_v512_v513.json`. v438 remains untouched.

## 2026-08-08 — Inbound installed crane source v001

- Built additive Blender source at `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/Candidate_v001` from the supplied four-sheet inbound reference pack; all dimensions/performance remain TBC.
- Two Unreal-ready FBXs are separated by motion responsibility: static runway/support frame and moving double-girder bridge. Trolley, hoist, powered C-hook v035 and master coil remain retained modules rather than rebuilt parts.
- The initial joined-object origin error was corrected and the fixed source render regenerated. Do not promote yet; next run is isolated Unreal intake plus fixed-camera process validation. Retained builder authority v438 is unchanged.

## 2026-08-08 — Inbound installed crane Unreal reviews v514-v518

- v514 technical intake passed scale/bounds/material/body setup for the new static runway and moving bridge. v517 proves the installed geometry and controlled materials; v518 proves internal bay clearance.
- Neither passes the final visual gate: v517 obscures the powered C-hook transfer and v518 hides the exact four-coil lorry. Retain v517 as structure evidence, reject v518 presentation, and do not integrate either into v438.
- Decision: `Saved/Audits/PressShopIntegration/inbound_installed_crane_decision_v514_v518.json`. Next successor needs a wider factory-context view showing lorry, carried coil, receiving saddle and loaded Coil AGV together. All engineering values remain TBC.

## 2026-08-08 — Inbound linear-layout evidence v519-v521

- Camera-only v519 confirmed the inherited layout was the obstruction. v520 establishes the Pro-aligned linear equipment sequence and v521 verifies that the exact four trailer coils, carried load position, fixed saddle and loaded AGV can coexist visibly.
- Retain v520 transforms as layout evidence only. Do not promote the isolated-stage renders; they lack real hall context and clear floor/material-flow communication.
- Next gate: install those transforms in a fresh hall-context validation child and capture both a process overview and crane hero. Decision: `Saved/Audits/PressShopIntegration/inbound_linear_layout_decision_v519_v521.json`. v438 remains untouched.

## 2026-08-08 — Inbound installed-hall validation v522-v523

- Fresh isolated v522/v523 rebuild from retained v520/v521 process geometry; immutable builder authority v438 remains byte-identical at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- v522 is visually rejected and must not be a parent: its roof is too low and review lighting clips the floor/coils to white.
- v523 fixes roof height, exposure and camera framing. It proves exactly four trailer coils, coherent installed runway/moving bridge, a powered C-hook carrying a separate coil, distinct fixed receiving saddle and a visible loaded Coil AGV inside a lit hall.
- Retain v523 only as hall-context/process-readability evidence. It is not release art or a production integration parent because the cab is cropped, enclosure/safety presentation is sparse and lorry/dock/control detail remains below the four owner-supplied Pro sheets.
- Decision: `Saved/Audits/PressShopIntegration/inbound_hall_context_decision_v522_v523.json`. Fresh views: `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v523/`. All engineering values remain TBC; no runtime, collision, navigation, save or authority gate is claimed.
- Next inbound gate is a release-intent fresh direct child of v438 only after the lorry/dock/enclosure/signage modules meet the Pro visual bar, followed by the full technical and fixed-camera gate set.

## 2026-08-08 — Coherent four-coil lorry intake / v527-v528 decision

- Added `InboundCoilDelivery/LorryAssembly_v001`, baking the verified Modular_v005 cab and open four-coil trailer into one parked-delivery presentation mesh while preserving all modular source parts. Source proof is clear and isolated Unreal intake passes 270 x 1468.75 x 381 cm bounds, nine material slots and body setup; engineering values remain TBC.
- Reject v527 because separate imported cab/trailer origins visibly detach the tractor. Reject v528 because the coherent lorry fixes that defect and keeps exactly four visible coils, but overlaps the protected crane enclosure and blocks the powered C-hook operating envelope.
- Retain the coherent lorry asset and linear-flow evidence only. Next successor must place the complete docked lorry wholly upstream, preserve a visibly empty crane envelope, then place the fixed receiving saddle and separate AGV handoff downstream. Decision: `Saved/Audits/PressShopIntegration/inbound_coherent_lorry_decision_v527_v528.json`.
- Immutable builder authority v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Inbound owner-sequence layout retention v529-v532

- v529 improved spacing but left the tractor inside the protected crane envelope. v530 established the first clean physical separation. v531's opposite-aisle evidence is rejected because the temporary far wall blocks the camera.
- Retain isolated v532 as layout/camera evidence only. Its cutaway view keeps structural beams/columns and clearly proves left-to-right: coherent four-coil lorry → protected bridge crane/powered C-hook → fixed receiving saddle → separate loaded Coil AGV handoff.
- Do not promote v532 as release art. The temporary black hall, basic lighting/materials, sparse dock detail and lorry smoothing metadata remain below the owner Pro pack. A fresh direct-v438 integration child and all runtime/collision/navigation/save/authority gates remain open.
- Decision: `Saved/Audits/PressShopIntegration/inbound_owner_sequence_retention_v529_v532.json`. Immutable v438 remains unchanged.

## 2026-08-08 — Inbound lorry smoothing cleanup v533

- Rebuilt the retained coherent four-coil lorry FBX with explicit face smoothing metadata and reimported it into the existing isolated candidate asset. Unreal reported zero warnings and zero errors.
- Technical intake is unchanged: 270 x 1468.75 x 381 cm, nine material slots, body setup present, exactly four restrained coils. New FBX SHA-256 is `743dfe1359c0134cac48448e26e2b7d616e76124e6508d3ac747508db7591607`.
- Fresh v532 fixed-camera evidence was recaptured after the reimport and still proves the retained sequence. This closes only the lorry smoothing warning; release hall/PBR/signage/runtime gates remain open and nothing is promoted.
- Audit: `Saved/Audits/PressShopIntegration/inbound_lorry_assembly_import_v533.json`. Immutable v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Inbound installed-context reviews v534-v535

- v534/v535 preserve the retained v532 process transforms and add a light industrial wall, dark lower service band, window strip, sealed-grey floor language, hall columns, high-bay lighting and aisle-facing inbound/PR-003 identity signs.
- Reject v534 as final evidence because equipment remained underlit and signs faced incorrectly. v535 corrects sign orientation, exposure and aisle fill; retain its lighting/backdrop direction only.
- v535 is still not release art: the backdrop uses validation blocks rather than final dock architecture and detailed PBR assets. Direct-v438 integration and runtime/collision/navigation/save/authority gates remain open.
- Decision: `Saved/Audits/PressShopIntegration/inbound_release_context_decision_v534_v535.json`. Immutable v438 remains unchanged.

## 2026-08-08 — Inbound signage/control refinement v549-v551

- The four owner-supplied Pro sheets confirm the visual sequence: coherent cab-over lorry with exactly four restrained coils → protected powered C-hook crane cell → fixed receiving saddle → separate low-profile Coil AGV handoff to PR-003. All engineering values remain TBC.
- v550 added useful process identities and an aisle-side dock-control assembly but its long floor stripes dominated the composition and implied verified clearances. Do not retain v550 as the visual parent.
- Retain isolated v551 as the strongest current inbound visual candidate. It removes those stripes, lowers/enlarges the three process signs, preserves bright cylindrical trailer coils and keeps the lorry, crane cell, saddle and AGV visually distinct in fresh fixed-camera evidence.
- v551 is not promoted or integrated. Runtime, collision, navigation, save and authority gates remain open. Audit: `Saved/Audits/PressShopIntegration/inbound_signage_controls_decision_v549_v551.json`. Immutable v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Inbound close-detail diagnostic v552

- v552 is a camera-only child of v551 adding fixed dock-detail and saddle/AGV-handoff views; no process geometry changed. All four captures passed.
- The detail evidence confirms separate dock guide/restraint, control/signal, scanner, receiving-saddle and AGV-handoff modules. The saddle, powered C-hook and loaded AGV relationship reads correctly.
- Do not use v552 as a new visual parent: close range proves the dock/restraint hardware and validation hall materials remain below release fidelity. Keep v551 as the strongest visual parent and rebuild/refine those modules before integration.
- Audit: `Saved/Audits/PressShopIntegration/inbound_detail_camera_decision_v552.json`. v438 remains byte-identical.

## 2026-08-08 — Blender dock architecture v002 / installed review v553-v554

- Rebuilt the inbound dock from the retained Blender generator as additive `DockArchitecture_v002`, preserving v001 and adding leveller/hinge detail, tubular wheel guides and anchors, dock bumpers, clearer powered restraint hardware, scanner/traffic/control housings and mesh pedestrian guarding. Source contains 133 modules; all values remain TBC.
- Isolated Unreal intake v553 passed: 1240 x 657 x 655 cm bounds, eight material slots and body setup. Installed direct-v551 child v554 built and all four fixed-camera captures passed.
- v554 improves dock mechanical readability without disturbing the four-coil lorry → protected C-hook cell → fixed saddle → separate Coil AGV sequence. Close-range materials/model density still fall below release quality, so retain the source and isolated asset only; keep v551 as visual parent and do not integrate/promote v554.
- Audit: `Saved/Audits/PressShopIntegration/inbound_dock_architecture_decision_v553_v554.json`. Immutable v438 remains unchanged.

## 2026-08-08 — Inbound dock PBR audit/binding v555-v557

- v555 confirmed eight clean imported dock material slots. v556 duplicates v002 geometry into isolated DockArchitectureCandidate_v003 and binds every slot to the controlled inbound PBR material library; bounds and body setup are preserved.
- Fresh installed v557 overview, crane, dock-detail and handoff-detail captures pass. Painted steel, brushed steel, rubber, sensor glass and safety colours separate more clearly while exactly four bright trailer coils and the full lorry → C-hook → saddle → Coil AGV sequence remain intact.
- Retain v557 as the strongest isolated inbound visual candidate, superseding v551 for future isolated visual work only. It is still below release quality at close range and is not promoted/integrated; runtime, collision, navigation, save and authority gates remain open.
- Decision: `Saved/Audits/PressShopIntegration/inbound_dock_pbr_decision_v555_v557.json`. v438 remains byte-identical.

## 2026-08-08 — Inbound lorry identity refinement v558

- Built v558 directly from retained v557. A slim green identity rail and `CAIRNWELL AUTOMOTIVE | INBOUND COILS` TextRender improve lorry ownership/readability without covering the open trailer or any of its exactly four bright coils.
- All four fixed-camera captures passed in `Saved/ValidationScreenshots/PressShopIntegration/inbound_coil_delivery_v558`. Retain v558 as the strongest isolated visual candidate only.
- Do not promote or merge v558. Release-grade close geometry/surfaces plus runtime, collision, navigation, save and authority gates remain open. Audit: `Saved/Audits/PressShopIntegration/inbound_lorry_identity_decision_v558.json`. Immutable v438 remains unchanged.

## 2026-08-08 — Detailed inbound lorry successor v559-v561

- `LorryAssembly_v002` is a source-only additive reconstruction of v001 with stronger cab-over, running-gear and open-trailer detail; the exact four-coil load and coherent single origin are preserved. v559 import passes at 295 x 1743.75 x 381 cm with 17 material slots and body setup.
- v560 binds every slot to controlled inbound PBR assets, retaining the approved bright-wrap material only on the original coil-steel slot. Fresh v561 overview/crane/dock/handoff captures pass and show exactly four bright coils with no process-order regression.
- Retain v561 as the strongest isolated inbound visual candidate only. Protected crane/dock release refinement and every runtime/technical gate remain open. Audit: `Saved/Audits/PressShopIntegration/inbound_detailed_lorry_decision_v559_v561.json`. Immutable v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 — Protected enclosure/crane PBR decisions v562-v567

- v563 remaps the five audited enclosure slots to controlled Cairnwell PBR materials. Fresh v564 captures materially improve the protected-cell read and preserve the detailed lorry, four bright coils, powered C-hook, saddle and separate Coil AGV. Retain v564 as the strongest isolated visual parent.
- v566 creates controlled-PBR runway/moving-bridge duplicates after the v565 slot audit. v567 captures pass but show no meaningful visual gain over v564, so retain the assets only and do not advance the visual parent.
- No promotion or v438 integration is authorized. Audit: `Saved/Audits/PressShopIntegration/inbound_enclosure_crane_pbr_decision_v562_v567.json`. Immutable v438 remains unchanged.
## 2026-08-08 - Direct-v438 inbound integration v568-v571

- v568 is rejected placement evidence: placing the retained inbound cell upstream without changing the shell crossed the inherited west wall at x = -11000 cm. Unreal's first same-process duplicate/load attempt hit the known world-GC safeguard and left no map; the successful candidate used the safe two-process prepare/build pattern. Protected v438 remained byte-identical throughout.
- Fresh direct-v438 child `/Game/LineBoss/Developer/Validation/LB_PressShop_InboundIntegrationCandidate_v570` deliberately enlarges the west receiving bay by 5000 cm, extends the sealed floor and north/south walls, moves the west wall/liner outward, and installs the retained detailed four-coil lorry, dock, protected crane/C-hook, receiving saddle and AGV handoff guides upstream of PR-003.
- v570 does not spawn another AGV, lift deck or loose/in-transfer coil. Exact-map v571 passes one retained Coil AGV, one lift deck, one in-transfer coil, one Coil AGV controller, one build authority and thirteen additive inbound presentation modules. Audit: `Saved/Audits/PressShopIntegration/inbound_exact_authority_v571.json`.
- Retain v570 as the strongest direct-map layout/authority candidate, not promotion. Fresh views prove the expanded bay fits and connects to PR-003, but lighting, dock/lorry composition, navigation/collision/PIE, inbound runtime/save binding and final Pro comparison remain open. v438 stays immutable at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

## 2026-08-08 - Functional inbound authority, navigation and release-view successor v575-v601

- v575/v576 are rejected partial build attempts only: v575 failed on an unavailable Unreal-Python root-component helper and v576 correctly refused an undersized 6x2 storage footprint. They did not overwrite v570 or protected v438.
- Native persistence support was added to `LBFactoryTransportLink` and `LBInboundDeliveryController`; the project builds successfully. Fresh v577 installs hidden persistent gameplay authorities behind the retained Pro-quality presentation: `INBOUND-001`, `SZ-COIL-PR003` (BareCoils, capacity 12, 6x2), one dock-to-store transport link and one inbound controller reusing the existing single Coil AGV controller. Reload audit v578 and native campaign round-trip automation pass.
- Exact-map functional PIE v579 proves one identified coil dispatches, reaches PR-003 storage, increments occupancy/delivery count to one and leaves the Coil AGV ready for reload. Values used for gameplay tuning remain TBC rather than claimed engineering data.
- v581 added west receiving-bay nav; v585 found a 10.5 m coverage gap. Fresh v586 closes that gap by overlapping retained PR-004 coverage. Segregated-nav v591 proves serviceable paths on both sides of the protected handoff while correctly keeping the direct safety-fence crossing blocked. Exact v586 whole-nav v592, aisle/collision v593, one-coil cycle v594 and authority/hash v595 all pass.
- v596 is visually rejected: its first lighting pass clipped the floor/coils and its overview camera sat above the roof. Do not use it as a presentation parent.
- Retain unpromoted `/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v597` as the strongest current inbound/whole-shop candidate. It is a clean v586 successor with restrained industrial west-bay lighting and fixed interior evidence cameras. Fresh renders are in `Saved/ValidationScreenshots/PressShopIntegration/inbound_release_v597/`.
- Exact v597 regression evidence passes: authority/hash v601, whole-shop six-route nav v598, all expanded aisles/service lanes v599 and one identified coil delivery v600. Protected v438 remains byte-identical at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. v597 remains candidate-not-promoted; continue release-art refinement and final integrated gameplay work from v597, never from v596 or older presentation-only maps.

## 2026-08-08 - playable ordered machine catalogue v602-v603

- Closed the gap between the existing ordered-machine authority and the management-camera HUD. The Factory Build page now queries `ULBFactoryMachineBuilderSubsystem::GetAvailableMachineTypes()` live and displays only machine packages whose required predecessor/buffer exists.
- `ALBManagementPawn::StartMachinePlacement` now gives inbound delivery, depackaging, decoiler/feeder, complete press train, inspection and outbound dock packages the same 1 m grid placement workflow. Generic packages receive obstruction checks; press trains retain their protected identity/envelope validation.
- Confirmation now routes every machine, including press trains, through `PlaceMachine`, preserving automatic identity and automatic AGV/roller/panel-transfer connection creation. Storage remains player-drawn and auto-capacity-filled.
- Native Editor build PASS. `Saved/Logs/FactoryBuilder_v602.log`: all five `LineBoss.FactoryBuilder` tests PASS. `Saved/Logs/ManagementBuilder_v603.log`: management controller workflow PASS.
- No map or presentation candidate was edited. Continue visual/integrated work from unpromoted v597; protected v438 remains immutable.

## 2026-08-08 - strict process/storage progression v604-v606

- Closed a progression bypass discovered after v603: a prematurely authored downstream buffer can no longer unlock a machine without the complete upstream chain. Depackaging now requires inbound plus bare-coil storage; a press train requires decoiling plus prepared blanks; outbound requires inspection plus finished-panel storage.
- Added a live context-filtered storage catalogue. Before inbound, no storage choice is offered. Bare coils/maintenance/quarantine unlock after inbound; prepared blanks after decoiling; scrap after a press train; finished-panel stillages after inspection. Already unlocked buffer types remain available so players can add capacity at visible bottlenecks.
- The controller/mouse Factory Build action count and selections now derive from both live catalogues. Regression explicitly proves an early finished-panel buffer cannot skip inspection.
- Native Editor build PASS. `Saved/Logs/FactoryBuilderProgression_v604.log` passes 5/5; `Saved/Logs/ManagementProgression_v605.log` passes 1/1; `Saved/Logs/LineBossFullProgression_v606.log` passes all 34/34 with zero failures and zero automation errors.
- Code/tests/docs only: v597 remains the strongest unpromoted integrated candidate; protected v438 was not edited.

## 2026-08-08 - generic machine floor datum v607

- Corrected the management preview/commit datum for generic player-built machines: their protected envelope centre now sits one half-height above the traced floor, so the machine base is floor-seated instead of half buried. Grid lines remain on the slab. Native press trains preserve their established floor-origin convention.
- Editor build PASS and full `LineBoss` regression passes 34/34 with zero failures/errors in `Saved/Logs/LineBossPlacementDatum_v607.log`.
- Protected v438 re-hashed unchanged at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`; no map was saved.
## External reference acquisition rule (user-directed, 2026-08-08)

- If an asset cannot reach the required visual or operational fidelity from retained references, search online before modelling for official manufacturer drawings, body-builder information, CAD/data sheets, manuals, and clear photographic references.
- Prefer primary manufacturer sources. Retain downloaded reference files and record their source/provenance and licence constraints.
- Do not import restricted, confidential, trademark-dependent, or ambiguously licensed geometry into the shipping game. Reconstruct a brand-neutral Cairnwell asset from permitted references where required.
- Treat dimensions and performance data as TBC unless verified by authoritative project information.
## 2026-08-08 — inbound trailer coil identity and Production Line reference

- User correction: every coil carried by the inbound lorry must use the exact retained wrapped packaged-coil presentation already used in PR-003 storage, not a dark/simple substitute. Isolated map `/Game/LineBoss/Developer/Validation/LB_PressShop_InboundWrappedTrailerCandidate_v616` now carries exactly four independent instances of `/Game/LineBoss/IndustrialKit/MaterialHandling/MasterCoil/Candidate_v005/SM_LB_MasterCoil_Candidate_v005`; the simplified imported trailer coils are excluded. The lorry is authored at an approach point and reverses to the dock. Candidate is not promoted pending fresh visual/PIE gates.
- Native `ALBInboundDeliveryController` now supports stable tag discovery at BeginPlay so the modular lorry, four coils, crane, C-hook and saddle can rebind after map reopen/save restore. Compile passed. Existing two inbound delivery automation tests passed before the tag-discovery addition; rerun plus exact-map visual sequence validation remains required.
- A UE 5.8 Save Map workflow briefly touched v597; hash preservation stopped the candidate. The touched package was preserved at `Saved/Audits/PressShopIntegration/forensic_touched_v597_before_restore_20260808.umap`, and v597 was semantically restored from the clean pre-edit v616 snapshot before the successful isolated edit. Do not treat byte hash alone as authority; rerun exact v597 semantic audit before further parenting.
- The installed game `Production Line` may be inspected read-only for exposed data/UI/mod/save structure and gameplay principles only. Never decompile its executable or copy proprietary code/assets. Useful independent ideas: zoomable isometric management view, ordered placement, visible buffers/alerts, auto-routing and compact scheduling. Cairnwell remains original, Unreal-native, realistic, robot/AGV-led, with separate buildings. Research and sales gameplay remain out of scope for now.
# 2026-08-09 continuation checkpoint - new inbound assets / AGV plan

- Active objective: rebuild the Press Shop from the loaded lorry through unloading, wrapped-coil storage and preparation into the retained wider Press Trains A-D, using old maps only as positional reference; validate in Blender before Unreal; correct AGV routes; review cleaning/maintenance robots afterward; conserve Meshy credits.
- Retain the existing powered C-hook. Rebuild it only if installed scale/alignment validation fails.
- Approved-texture split stand candidate: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/MeshyAdjustableCoilStand_v20260809_v004/Cairnwell_AdjustableCoilStand_SpatialTexturedSplit_v004.blend`; direct Blender render: `Saved/ValidationScreenshots/PressShopIntegration/coil_stand_spatial_split_v004_direct.png`.
- Revised four-coil lorry candidate with eight approved stand instances: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryLoadedWrappedCoils_v20260809_v004/Cairnwell_Lorry_Loaded_WrappedCoils_ApprovedStands_v004.blend`. Latest fit is 92.5% stand X/Y, pair centres +/-0.46 m, approximately 0.70 m stand height and 0.35 m coil base offset over deck. Review under its `Review` folder; final owner acceptance and Unreal intake remain open.
- Matching 12-position/24-stand wrapped storage candidate: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/WrappedCoilStorage12_v20260809_v001/Cairnwell_WrappedCoilStorage_12Position_v001.blend`. Latest fit is 92.5% stand X/Y, pair centres +/-0.46 m, approximately 0.61 m stand height and 0.10 m coil base offset. Review under its `Review` folder; final owner acceptance and Unreal intake remain open.
- Pro AGV map `C:/Users/greg_/Downloads/ChatGPT Image Aug 9, 2026, 08_45_47 AM.png` is Rev A evidence only. Correct 20 storage icons to 12, place four actual charging bays, add four Train A-D S01 handoff bays and update the sheet date before using it as the planning reference. Coordinates remain provisional until exact-map validation.
- Do not promote `C:/Users/greg_/Downloads/ChatGPT Image Aug 9, 2026, 09_01_40 AM.png`: it has the correct player-built notice/date but only nine coil icons, five chargers (duplicate CS2) placed over support rooms and no explicit S01 handoff A-D bays. The next sheet must visibly pass 12 coils/4 chargers/4 handoffs before reference acceptance.
- No Meshy credits were used for these changes. Protected builder-authority v438 must remain untouched.
- Powered C-hook Candidate_v035 now has a fresh Blender fit check against repaired wrapped coil v003. With the powered 90-degree alignment applied, its padded arm passes through the coil centre eye and supports the inner bore. Evidence is under `Saved/ValidationScreenshots/PressShopIntegration/retained_chook_wrapped_coil_v035_v003/`. Retain the hook; do not regenerate it unless installed clearance later fails.
- Owner requirement: players build the Press Shop themselves, following the two reviewed factory-game precedents. Treat every revised plan as a valid example/reference layout only. Inbound modules, coil storage/stands, AGV routes/waits/chargers, process cells and press trains must be modular catalogue placements with preview, clearance validation, progression and automatic connection/persistence; do not bake a finished factory into the release map. Fixed shell/structure/fire/road constraints remain authored.
- Owner rejected Coil AGV Candidate_v001 as final visual art. Retain it only for functional/envelope reference. Next paid model is one proper unloaded modular coil AGV from four consistent Pro orthographic images via Meshy multi-view. Keep the wrapped coil separate; require chassis, lifting cradle/deck, wheels/bogies, bumpers and sensors/lights to remain separable. Validate textured and segmented `.blend` sources in Blender before Unreal intake.
- Credit-free code progress: player-placeable AGV infrastructure is now a separate persistent catalogue covering chargers, wait points, route waypoints and exact S01 handoffs A-D. Chargers are limited/named `CS-01` through `CS-04`; duplicate Train A-D handoffs and a fifth charger are rejected. The whole set saves/restores through the campaign controller. This changes no map and uses placeholder presentation until approved Blender art is available.
- Verification: Editor build PASS; focused AGV-infrastructure automation PASS (`Saved/Logs/FactoryBuilder_AGVInfrastructure_20260809.log`); full FactoryBuilder 7/7 PASS (`Saved/Logs/FactoryBuilder_AGVInfrastructureRegression_20260809.log`); campaign round-trip PASS (`Saved/Logs/FactoryBuilder_AGVInfrastructureCampaign_20260809.log`). Protected v438 SHA-256 remains `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- The first Meshy coil-AGV pair is now fully audited and rejected, not merely “needs cleanup.” Textured bounds are ~1.900 x 1.900 x 0.788 m and segmented bounds ~2.000 x 2.000 x 0.829 m, proving the four near-identical Pro faces produced a square vehicle instead of the required 3.61 x 2.22 x 1.18 m carrier. Both sources exceed 1.56 million polygons; segmented has no materials; the four-way cradle and melted corner modules are structurally wrong. Preserve originals/evidence, do not spend repair/retopo credits. Use `.../MeshyCoilAGV_v20260809_v001/CORRECTED_PRO_ORTHOGRAPHIC_PROMPT.md`, validate the corrected long side/end ratios first, then make only one replacement generation.
- New-assets-only sequence authority is `SourceAssets/Candidate/PressShop/PRESS_SHOP_CLEAN_REBUILD_INTAKE_v20260809.json`. It is an asset gate, not a fixed map plan. Ready/retained items and all missing PR001-PR010 visuals are explicit, as are forbidden old visuals.
- The earlier Meshy six-axis suction robot pair is now correctly filed at `SourceAssets/Candidate/PressTrains/Shared/MeshyUnloadRobot_v20260809_v001/` for S07 unload, not PR004. Direct Blender audit proves a good overall arm/tool silhouette and 24 spatial parts including major arm sections, tool group and eight individual cups. Density remains about 2 million polygons and exact pivots/material transfer are open, but this is suitable for credit-free cleanup and possible PR004 arm-core reuse with separate tooling. Do not buy another robot generation.
- Owner added a whole-shop presentation requirement: repaint the complete visible floor and every walkway; inherited unpainted/mismatched/patchwork floor materials are rejected. Authority: `SourceAssets/Candidate/PressShop/FloorPaint_v20260809_v001/PRESS_SHOP_FLOOR_PAINT_SPEC_v001.json`; preview blend/render: `.../Cairnwell_PressShop_FloorPaint_Preview_v001.blend` and `Saved/ValidationScreenshots/PressShopIntegration/press_shop_floor_paint_preview_v001.png`.
- Paint language: sealed industrial-grey slab; green pedestrian/service walkways with yellow edges; white crossings/yellow thresholds; blue AGV lanes and pull-off bays; cyan flow arrows; red dashed maintenance borders; yellow/charcoal exclusion hatch; red/white fire keep-clear. Fixed safety paint belongs to the shell, while AGV/equipment-zone markings must follow saved player placements. The preview is validated as a semantic sample; clean Unreal application waits for final equipment positions and the accepted AGV envelope. Protected v438 remains untouched.
- Credit-free S07 cleanup is now at `SourceAssets/Candidate/PressTrains/Shared/MeshyUnloadRobot_v20260809_v001/Cleaned_v001/Cairnwell_S07_UnloadRobot_Cleaned_v001.blend`. It reduces the preserved segmented source from 2,042,191 to 466,514 polygons including review geometry, names the assemblies, applies readable candidate materials and repairs the exploded end effector by seating all eight retained cups on a new two-rail panel gripper. Evidence: `Saved/ValidationScreenshots/PressShopIntegration/meshy_s07_unload_robot_cleaned_v001.png` and `.../Cleaned_v001/cleaned_inspection.json`. Six joint markers remain provisional; motion, runtime-only export, collision/reach/swept envelope and installed S07 orientation must pass before Unreal promotion. No Meshy credits used.
- S07 runtime-only package now exists at `.../Runtime_v001/Cairnwell_S07_UnloadRobot_RuntimeCandidate_v001.blend` with 29 visual meshes, 466,513 polygons, ~2.000 x 0.848 x 1.610 m visual bounds, seven isolated conservative collision-review proxies and no studio floor/camera/lights. Exact pivots, posed sweep, reach, LOD and installed orientation remain open; see `runtime_manifest.json`.
- Player-built AGV infrastructure now carries saved dynamic floor paint rather than plain route semantics only. Every charger, wait point, route point and S01 handoff creates an approved-blue `#2167A5`, 1 cm-thick surface with no collision or navigation effect, sized inside its placement envelope and restored from the saved player layout. Editor build PASS; all seven FactoryBuilder tests PASS in `Saved/Logs/FactoryBuilder_DynamicFloorPaint_20260809.log`. This does not paint or modify protected v438.
- Support-fleet review is locked in `SourceAssets/Candidate/PressShop/SUPPORT_FLEET_CLEAN_REBUILD_REVIEW_v20260809.json`. Retain exactly two standalone CR01 v022/v023 cleaning robots and two standalone MR01 v022 maintenance robots plus four independent docks; use old maps only for positional reference and discard inherited transforms/presentation. CR01 source/pivots/sockets/collision/LODs pass. MR01 v022 supersedes the old white-wheel v021 map view and retains straight-reverse dock, compact arm, eight tools, lift, save, collision and route authority. Reintegrate these into the clean painted map and rerun visual/sweep/four-unit route gates before promotion. Do not spend Meshy credits on either robot unless the fresh owner comparison rejects a specific unrepairable component.
- Do not resume from v723 or v770. `Saved/Audits/PressShopIntegration/clean_rebuild_visual_rejection_v20260809.json` supersedes the earlier screenshot capture-pass receipts: v723 is visually rejected for squashed/glossy-melted trains, inconsistent temporary/legacy-looking modules, unpainted floor and wrong S07 presentation; v770 is rejected as an incomplete isolated inbound gantry on an empty slab with v723 trains in the distance. Preserve both as evidence only; never parent the clean rebuild from them.
- Fresh clean shell v003 now exists at `/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v003`: exact 220 x 120 m shell, fully sealed-grey floor, all fixed perimeter walkways green/yellow and six red/white fire keep-clear pads, with no inherited legacy equipment. Balanced-light captures are under `Saved/ValidationScreenshots/PressShopIntegration/clean_shell_v20260809_v003/`. This is a clean presentation/building base only; equipment-linked/internal paint remains dynamic with player placements. v438 remains protected and byte-identical.
- S07 rig pose gate now has hard evidence and fails: `.../MeshyUnloadRobot_v20260809_v001/Rigged_v002/Cairnwell_S07_UnloadRobot_RigValidation_v002.blend` separates at the wrist/tool and upper joint shells under a conservative pose. Manifest status is `FAIL_POSED_JOINT_CONTINUITY__STATIC_VISUAL_ONLY`; screenshot is `Saved/ValidationScreenshots/PressShopIntegration/meshy_s07_rig_validation_v002.png`. Retain static visual/eight-cup tooling, repair joint interfaces and pivots credit-free, and do not install or animate it yet.
- Clean inbound/store progress: approved Blender lorry v006 and adjustable stand v005 now have explicit Unreal exports and packed PBR texture extraction. Fresh shell child `/Game/LineBoss/Maps/LB_PressShop_CleanInboundStorageFit_v20260809_v005` contains exactly 1 lorry, 4 trailer coils/8 stands and 12 PR003 coils/24 stands, all separate. Fit successor seats floor stands at Z=0, store coil centres at 112 cm and trailer coil centres at 200 cm. Counts/contact pass, but the lorry atlas remains too dark/grey in Unreal compared with its green Blender authority, so colour readability stays open and neither v004 nor v005 is promotable. No Meshy credits used; v438 unchanged.
- Fresh actor-by-actor reconstruction proved the isolated v694/v696 A-D train family is structurally placeable but visually unacceptable. `/Game/LineBoss/Maps/LB_PressShop_CleanInboundRetainedTrains_v20260809_v011` has 728 installed-scope actors and correct left-to-right direction without inheriting a rejected whole-shop map, but screenshots show the same oversized grey block bodies/old top geometry the owner rejected. Treat v011 as diagnostic-only and never parent from it. Audit: `Saved/Audits/PressShopIntegration/clean_retained_trains_visual_rejection_v20260809_v011.json`. The next train build must replace the main press bodies with approved new-quality sources before internal walkway paint is laid.
- Greg's accepted S03 Walker GLB is now preserved and optimized credit-free at `SourceAssets/Candidate/PressTrains/Shared/UserApprovedS03Walker_v20260809_v001/Runtime_v001/`. The runtime source is 359,999 triangles (down 81.87%) and its Blender hero retains the accepted clean tall geometry/texture. Use it as the static S02-S06 outer body, with dies/ram/transfer/console/guards separate. Never use `MeshyStaticPressShell_v642`/v639: direct render proves the melted, deeper, squashed model. Audit: `Saved/Audits/PressTrains/approved_walker_vs_melted_shell_decision_v20260809.json`.
- New modular-train checkpoint: Blender v005 at `.../NewApprovedAssembly_v20260809_v005/` validates the corrected front-facing seven-stage layout and adds separate S02-S06 plaques. Four textured GLB authorities are under `RuntimeTexturedModules_v015/`. Clean Unreal child `/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsPaint_v20260809_v015` installs A-D and paints internal green/yellow walkways, equipment footprints, blue AGV routes/handoffs, white crossings, red crane exclusion and storage boundaries. v012 (100x scale) and v013 (grey/sideways FBX) are rejected diagnostics. v015 has correct scale/orientation but final material/lighting readability is still open, so do not promote yet. S07 remains static-only. Zero Meshy credits; protected v438 unchanged.
- Support-fleet successor v017 is the current clean-map continuation: exactly 2 CR01, 2 MR01 and 4 independent v026 docks are seated in compact painted south berths, robot bottoms are corrected to Z=0 within 0.25 cm, and bounds pass clearance between the south AGV trunk and Train A safety edge. Evidence: `.../clean_approved_trains_fleet_lit_v20260809_v017/support_fleet_south_floor_contact.png`. v016 is rejected for Blueprint-origin floor penetration; v018 is rejected for blown-out local press lighting. Resume from v017. Runtime tool/brush/door/drawer/dock sweeps and train material readability remain open. No Meshy credits; v438 unchanged.
## Latest floor-paint checkpoint (2026-08-09)

Use `/Game/LineBoss/Maps/LB_PressShop_CleanApprovedTrainsFleetPaint_v20260809_v032`. It is a proven template child of v019 with one clean 139-actor floor scheme and the inherited partial/doubled route pass removed. Exact inspection and fresh v033 screenshots prove the paint is saved, grounded and continuous across unloading, storage, preparation, trains A-D, AGV circulation, robot docks and perimeter escape walkways. v023/v026/v029 are rejected diagnostics only. Protected v438 remains unchanged; no Meshy credits were used.

## Latest inbound-fit checkpoint (2026-08-09)

Continue from `/Game/LineBoss/Maps/LB_PressShop_CleanInboundFlowFit_v20260809_v035` for inbound visual work. It inherits the clean full-floor paint and corrects the four trailer coils to 400 cm pitch at Z=220 cm, with independent paired chocks widened to +/-60 cm. Exact audit `Saved/Audits/PressShopIntegration/clean_inbound_trailer_fit_v20260809_v035.json` passes trailer envelope and support contact. Use only the valid v037 lorry views under `Saved/ValidationScreenshots/PressShopIntegration/clean_inbound_fit_v20260809_v037/`; v036 lorry views are invalid outside-wall captures. The 12-position store remains grounded and modular. No Meshy credits were used; protected v438 is unchanged.

## Latest clean navigation checkpoint (2026-08-09)

Use `/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049` for the next clean-map runtime/visual successor. All 155 floor-paint actors are now `NoCollision`, while the structural slab retains collision. One full-shop nav volume plus native `LBPressShopNavigationBootstrap` replaces the failed v020 Python-config attempt. Live PIE `Saved/Audits/PressShopIntegration/clean_runtime_navigation_pie_v20260809_v050.json` passes four robot exits and all six painted AGV corridor families. MR01-02 and its complete independent berth moved to x=-1250 cm to clear the Train A obstruction; the other three units are unchanged. v051 is placement-only visual evidence because it is too dark for material approval. PR005 v002 remains source-only legacy-style evidence and must not enter the clean map. No Meshy credits were used; protected v438 is unchanged.

## Latest clean support-fleet runtime checkpoint (2026-08-09)

Continue from `/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetRuntimeFloorFix_v20260809_v059`. Four explicit saved unit identities, installed-transform clean routes, exact structural-floor authority and assigned-visual-dock collision handling are now active. PIE v060 passes sequential commission/dispatch/standby/return for both CR01 and both MR01 units, with every unit returning to its own dock within 5.15 cm. All four SupportRobots tests and the whole-shop campaign round-trip pass in v061/v062 logs. Legacy controller coordinates remain the default for old maps; clean-layout mode is opt-in. Final lit robot material review remains open. No Meshy credits were used and v438 is unchanged.

## Whole-floor paint requirement (2026-08-09)

The user confirmed that the entire press-shop floor and every walkway must be visibly painted. v059 inherits v032's complete scheme (sealed-concrete slab; continuous green walkways; yellow edges/safety zones; blue AGV lanes; crossings; crane exclusions; inbound, storage, preparation, trains A-D and robot-dock access). Preserve all 155 paint actors as `NoCollision`; only the structural slab is floor collision/nav authority. Extend/regenerate paint whenever the player-built layout moves or widens so no default-floor gaps remain. A fresh lit capture of v059 is still required for colour approval; v051 is placement evidence only.

That lit gate now passes in `Saved/ValidationScreenshots/PressShopIntegration/clean_lit_floor_walkways_v20260809_v064/`, with audit `Saved/Audits/PressShopIntegration/clean_lit_floor_walkways_capture_v20260809_v064.json`. v063 was rejected as overexposed. v064 used transient review lighting only, so v059 was not changed. AGV lane width and preparation footprints remain provisional pending the missing accepted AGV and PR001/PR002/PR004/PR005 assets.

## Latest support-fleet visual checkpoint (2026-08-09)

Continue from `/Game/LineBoss/Maps/LB_PressShop_CleanInboundSupportFleetDockContactFix_v20260809_v069`. Close lit review found the four standalone static dock faces 122.5-124 cm behind the parked robots. v069 moves only those four visual docks forward 100 cm, leaving robot/runtime roots, native service targets, paint and routes unchanged; the final visual gaps are 22.5-24 cm. PIE v070 passes all four commission/dispatch/return cycles with correct dock IDs and 5.03-5.15 cm return errors. Lit v071 passes grounding, textures, berth separation and dock alignment. v065 was rejected as overexposed and v066's MR01-01 angle was occluded; use v067 plus alternate v068 for close material evidence and v071 for final alignment. No Meshy credits used; protected v438 remains unchanged.

## Clean rebuild completion audit v072 (2026-08-09)

Read `Saved/Audits/PressShopIntegration/PRESS_SHOP_CLEAN_REBUILD_COMPLETION_AUDIT_v20260809_v072.md` before claiming completion. The clean lineage, loaded-lorry fit, storage, wider train reference rows, whole-floor paint/navigation and support fleet are proved. The objective is still incomplete because the accepted elongated coil AGV, PR001/PR002, PR004 tooling package, PR005-PR010 preparation packages, final moving press assemblies and installed cleaned S07 runtime replacement are missing or unproved. Promotion remains forbidden; do not substitute legacy PR visuals or the rejected square AGV. The intake JSON was refreshed with current evidence and protected v438 still hashes to `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.

S07 update: current clean continuation is now `/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791`, a fresh v069 child. Blender v787 short unique names fixed Unreal's earlier arm-name collapse; v788 intake proves six textured meshes and the separate steel tool material. v791 removes exactly four static S07 placeholders and installs four grounded six-part `Base -> Turn -> Lower -> Upper -> Wrist -> Tool` hierarchies. Fresh lit v792 shows every vacuum frame and all cups connected; transient v795 proves every descendant follows a 20-degree turntable rotation and restores with zero error. Evidence: `Saved/Audits/PressShopIntegration/s07_connected_vacuum_tool_intake_v20260809_v788.json`, `clean_connected_s07_placement_v20260809_v791.json`, `clean_connected_s07_hierarchy_motion_v20260809_v795.json`, and `Saved/ValidationScreenshots/PressShopIntegration/clean_connected_s07_v20260809_v792/`. v789/v790 are incomplete script-error children; never use them. Remaining S07 work is final gameplay controller/joint-range/collision certification. No Meshy credits used; protected v438 remains unchanged.

Coil AGV update: v796 proves the user's textured file is a single 1.57M-triangle mesh, while the split file has 40 parts / 1.61M triangles but no materials. Credit-free v797 grounds, decimates and elongates the split assembly to 2.8 x 1.7 x 0.9 m, but its attempted atlas transfer is visually rejected because the split source lacks usable UV/material binding. v798 keeps all 40 parts and uses clean factory paint instead (green body, dark bumpers, steel cradle, yellow corner protection). Review candidate: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v798/`; render under `Review/`; audit `Saved/Audits/PressShopIntegration/coil_agv_segmented_factory_paint_v798.json`. Await owner approval before Unreal import and final part-role/lift classification. Zero Meshy credits.

AGV lift successor v799 classifies six central cradle/deck meshes under `AGV_COIL_LIFT_ROOT` and leaves 34 chassis/corner meshes fixed. Neutral and transient +180 mm raised renders prove the cradle moves as one assembly; the saved master remains neutral. Use workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v799/` and audit `Saved/Audits/PressShopIntegration/coil_agv_lift_classification_v799.json`. Owner visual approval, wrapped-coil contact fit, collision proxies and Unreal route-envelope validation remain open. No Meshy credits used.

Loaded AGV fit: v800 is rejected because its inherited payload transform buried the coil into the chassis (bottom 69.7 mm). v801 corrects the approved 1.65 x 1.15 x 1.65 m wrapped coil to bottom Z=560 mm, axis across vehicle width, with 574 mm longitudinal and 269 mm lateral containment per side. It is parented to the payload root beneath the classified lift. Use workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v801/` and audit `Saved/Audits/PressShopIntegration/coil_agv_loaded_contact_corrected_v801.json`. Await owner visual approval before Unreal import; collision and route-envelope gates remain open. Zero Meshy credits.

AGV runtime-prep v802 adds separate chassis/lift/payload collision proxies and fixes the route envelope from the actual elongated vehicle: minimum 2.3 m straight lane, 3.4 x 2.3 m charger/handoff bay and 1.938 m swept turn radius using 300 mm safety margin. The +180 mm lift leaves 160 mm proxy clearance. Candidate: workspace `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v802/`; audit `Saved/Audits/PressShopIntegration/coil_agv_runtime_collision_envelope_v802.json`. Unreal import still waits for owner appearance approval. No Meshy credits used.

Floor/authority continuation v803: use `/Game/LineBoss/Maps/LB_PressShop_CleanConnectedS07_v20260809_v791` as the only clean continuation; never parent from rejected/incomplete v073, v789 or v790. Full floor and walkway paint is complete. `Saved/Audits/PressShopIntegration/clean_agv_paint_envelope_v20260809_v803.json` proves 4.2-5.2 m painted AGV surfaces versus the provisional v802 2.3 m loaded-AGV straight-lane requirement. Do not import v802 until owner appearance approval; afterward, add and validate 3.4 x 2.3 m charger/handoff bays and 1.938 m swept turns in a fresh v791 child.

Verified reference authority: `SourceAssets/Reference/PressShop/RemainingMachineryPack_v1.0/CAIRNWELL_PRESS_SHOP_REMAINING_MACHINERY_PACK_v1.0`; ZIP SHA256 `7021A2E5DE71F89306E1AA6CB96D2F6018870404E01F4F83FF27D5F6B2BC399A`; 28/28 manifest entries pass. Use numeric engineering data only until visuals receive owner approval. No Meshy credits used.

PR008 v804: new credit-free Blender engineering blockout at `SourceAssets/Candidate/PressShop/PR008/EngineeringBlockout_v20260809_v804/Cairnwell_PR008_EngineeringBlockout_v804.blend`. It proves the 10-module schedule, fixed `10400 x 5560 x 4490 mm` planning envelope, world datum `(-500,-2000,0) cm`, local +Y flow and 13 separate moving objects across all eight motion groups. Review renders and JSON audit are beside the blend. This is deliberately not final art and must not enter Unreal before owner appearance approval. Zero Meshy credits.

PR001/PR002 v805: authority audit `Saved/Audits/PressShopIntegration/pr001_pr002_new_asset_authority_v805.json`. PR001 may use owner Pro Sheet 03 presentation/sequence (verified SHA256 `9FF84A3F0260E4920274F3619010C36B68982880649506E7F3EEA06AD1B602BF`) but every dimension remains TBC; Modular_v001-v005 is positional/component-name reference only. PR002 has no approved new appearance or dimensions; legacy actors define function only. Generation/split/Blender briefs are under `SourceAssets/Candidate/PressShop/PR001` and `PR002`. Do not import either station until new models pass Blender and owner approval. Zero Meshy credits.

PR004 v806: reuse only the cleaned arm body/joint presentation from `MeshyUnloadRobot_v20260809_v001/Runtime_v001`; remove the S07 vacuum panel tool for this role. `SourceAssets/PR004/FilmDewrapSpindle_v005` supplies sequence/pivot/state metadata only, never final geometry or materials. New 31-part generation and Blender-gate brief: `SourceAssets/Candidate/PressShop/PR004/PR004_NEW_CELL_GENERATION_BRIEF_v806.md`; audit `Saved/Audits/PressShopIntegration/pr004_retained_core_and_new_tooling_authority_v806.json`. Wrapped exact-ID coil enters; the same ID leaves bare to PR005. No Unreal import and zero Meshy credits.

AGV approval pack v807: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/UserCoilAGV_v20260809_v807_ApprovalPack/Review` contains unloaded hero plus loaded hero/side/top/front Blender views with UCX helpers hidden. They visibly confirm the approved wrapped coil is centred and supported by the cradle, not floating. The v802 master and route authority are unchanged. Audit is alongside the renders as `coil_agv_owner_approval_pack_v807.json`. Still wait for explicit owner appearance approval before Unreal import. Zero Meshy credits.

Loaded lorry approval pack v808: `SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryLoadedWrappedCoils_v20260809_v808_ApprovalPack/Review` contains hero, side, rear, top and close trailer/stand Blender views. They visibly show four evenly spaced seated wrapped coils and eight separate stands, including rear orientation; the Cairnwell factory-green cab is readable. The v004 master and Unreal map were unchanged. Audit `loaded_lorry_owner_approval_pack_v808.json` is beside the renders. Owner appearance approval remains open. Zero Meshy credits.

PR001 engineering candidate v809: `SourceAssets/Candidate/PressShop/PR001/EngineeringCandidate_v20260809_v809/Cairnwell_PR001_EngineeringCandidate_v809.blend` is a credit-free 19-part modular receiving saddle and identity-scanner candidate. It uses the approved repaired coil geometry at the 1.65 x 1.15 x 1.65 m gameplay envelope. Blender QA rejected the first wall-like scanner and replaced it with an open arch; six current renders and `pr001_engineering_candidate_audit_v809.json` pass. It remains provisional and must not enter Unreal until owner appearance/scale approval. Protected v438 remains byte-identical. Zero Meshy credits.

PR002 engineering candidate v810: `SourceAssets/Candidate/PressShop/PR002/EngineeringCandidate_v20260809_v810/Cairnwell_PR002_EngineeringCandidate_v810.blend` has all 20 mandatory modular parts, four visible load paths and a separate approved packaged coil. First-render QA caught and corrected displaced parented parts. Six rerenders pass; measured coil bottom 0.704455 m lies within the rubber-pad 0.544217-0.895783 m contact range. No approved PR002 appearance exists, so owner approval/final dimensions and Unreal intake remain open. Zero Meshy credits.

PR004 engineering layout v811: `SourceAssets/Candidate/PressShop/PR004/EngineeringCandidate_v20260809_v811/Cairnwell_PR004_EngineeringCandidate_v811.blend` contains all 31 mandated cell modules and six clean review views. Thirteen retained arm-core meshes are collection-instanced; every S07 vacuum-tool mesh is excluded. The visible flow covers wrapped input cradle, new wrist tooling, winding/dancer, compaction/bale handling and bare output saddle. Treat it as generation/layout authority only pending final art, exact pivots/reach, owner approval and Unreal intake. Zero Meshy credits.

PR005 generation-reference pack v812: `SourceAssets/Candidate/PressShop/PR005/OwnerApprovalPack_v20260809_v812/Review` contains bright hero/front/rear/left/right/top renders of unchanged Candidate_v002. Nine of nine modular exports and manifest hashes pass, with source validation PASS and exact shell/ports retained. The blocky legacy appearance is still forbidden as final clean-map art; use this only to guide a proportionally consistent Pro/Meshy replacement unless the owner explicitly approves it. Zero credits and no Unreal import.

PR002 owner Pro pack v813: five supplied views are archived at `SourceAssets/Reference/PressShop/PR002/ProPack_v20260809_v813` with fixed front/rear/left/right/hero names and hashes. They are now appearance authority; v810 remains engineering/contact authority. `PR002_MESHY_JOB_v813.md` excludes the coil/floor/bollards and preserves the 20-part split. Meshy was not started because signed-in Edge is not connected to Codex browser control; connect it in Settings -> Computer use. Zero credits used.

PR004 missing-equipment pack v814: `SourceAssets/Candidate/PressShop/PR004/MissingEquipmentProMeshyPack_v20260809_v814` provides bright hashed hero/front/rear/left/right/top views with the retained arm, coil and temporary film/bale states hidden. The job prompt requests only the missing cradle/tooling/spindle/dancer/compactor/output/guard/control art, preventing fused reusable assets. Generation, Blender pivot/reach validation, owner approval and Unreal intake remain open. Zero credits used.

PR006 generation reference v815: `SourceAssets/Candidate/PressShop/PR006/GenerationReference_v20260809_v815` combines the 67-module dimensioned source and six verified release-detail modules. Six hashed views preserve the 7.50 x 4.52 x 2.97 m envelope, 1.5 m strip, 9 lower/10 upper rolls, four gap cylinders and three drives. Old appearance remains reference-only; constrained Pro/Meshy final art, Blender validation, owner approval and Unreal intake are open. Zero credits used.

PR007 generation reference v816: `SourceAssets/Candidate/PressShop/PR007/GenerationReference_v20260809_v816` combines the dimensioned 78-module washer/lube source with six verified release-detail modules. Six hashed views preserve the 7.35 x 5.44 x 4.03 m envelope, 1.5 m strip, four headers, twenty nozzles and two tanks; the ten strip-bridge modules stay separate. Old appearance is reference-only; final art, Blender validation, owner approval and Unreal intake remain open. Zero credits used.

PR008 Pro-design gate v818: the authoritative detailed Sheet 01 was found and hash-verified (`75F8F0445CE578C2176A4BCF3165DCB16836AAA7F765091D095966443E99C0C2`). The v817 six-view Blender box blockout is rejected as Meshy appearance input and remains envelope evidence only. Give Pro `SourceAssets/Candidate/PressShop/PR008/ProDesignPack_v20260809_v818/PR008_PRO_DESIGN_JOB_v818.md` plus Sheet 01 and request five separate consistent views. Preserve the fixed 10.40 x 5.56 x 4.49 m envelope, 1.50 m strip, ten modules and eight moving groups. No Meshy or Unreal work yet; credits used: 0.

PR009 Pro-design gate v819: Sheet 02 was visually inspected and hash-verified (`3D37D19DCBE4BDB5D30D6FA58F7E4C60D2654BAEB36057E6DBF46BB4FFC43008`). Candidate_v002 is dimensions/pivots/interfaces/splits only, never clean-map appearance. Give Pro `SourceAssets/Candidate/PressShop/PR009/ProDesignPack_v20260809_v819/PR009_PRO_DESIGN_JOB_v819.md` plus Sheet 02 for five separate matching views. Preserve the 7.60 x 5.20 x 4.25 m guarded target, 2.60 x 1.80 m blank, 1.40 m stack, ten modules and eight movers. No Meshy or Unreal work; credits used: 0.

PR010 Pro-design gate v820: Sheet 03 was visually inspected and hash-verified (`E69BF1B26342393840B41FBF3BDBB24B4D35DD9E3B25EDB5AD7C1A89348062B3`). ReleaseArt_v103 is engineering/gameplay/split evidence only, never final clean-map appearance. Give Pro `SourceAssets/Candidate/PressShop/PR010/ProDesignPack_v20260809_v820/PR010_PRO_DESIGN_JOB_v820.md` plus Sheet 03 for five separate matching views. Preserve exactly four lanes at 3.00 m pitch, two carrier positions per lane, the 14.00 x 8.40 x 3.60 m footprint, ten modules and six movers. No Meshy or Unreal work; credits used: 0.

Press Trains shared missing-kit gate v821: Sheets 04-08 are visually inspected and hash-fixed in `SourceAssets/Candidate/PressTrains/Shared/ProDesignPack_v20260809_v821/PRESS_TRAINS_SHARED_AUTHORITY_MANIFEST_v821.json`. Reuse the owner-approved S03 Walker body for every S02-S06 press; do not generate complete A-D trains or duplicated bodies. Give Pro `PRESS_TRAINS_SHARED_MISSING_KIT_PRO_JOB_v821.md` for four separate five-view jobs covering S01, shared transfer, shared die/tooling and S07 surroundings without the retained robot. Each train stays 56 x 15 x 11.5 m, seven stages at 7.5 m pitch, lengthwise S01-to-S07. Final art and Unreal integration are open; credits used: 0.

Route/logistics gate v822: `Saved/Audits/PressShopIntegration/press_shop_player_built_route_and_handoff_contract_v20260809_v822.json` fixes the elongated coil AGV to PR003-PR005 coil duties only. Never reuse it for PR010 flat-stack-to-S01 delivery; a separate stack-carrier AGV/forklift envelope is missing. Existing blue paint widths and centred rounded turns fit the coil AGV, but hard 90-degree corners are forbidden and the clean map still has zero charger/handoff bay actors. Add bays only after AGV owner approval in a fresh v791 child, then repeat CR01/MR01 crossing reservation and dock-separation gates. No map or Meshy changes.

Blank-stack AGV gate v823: PR010 proves the separate 2400 x 1900 x 180 mm carrier and 2200 x 1700 x 500 mm stack. `SourceAssets/Candidate/PressShop/BlankStackAGV/ProDesignPack_v20260809_v823/BLANK_STACK_AGV_PRO_JOB_v823.md` requests a distinct low-profile five-view vehicle with separate lift/rollers/locators and no baked payload. Provisional target 3200 x 2200 x 420 mm gives a 2241.649 mm swept radius: outer 5200 mm route only, never the 4200 mm storage loop until final Blender/runtime validation. No credits or Unreal work yet.

Blank-stack AGV Blender v824: zero-credit engineering candidate `SourceAssets/Candidate/PressShop/BlankStackAGV/EngineeringCandidate_v20260809_v824/Cairnwell_BlankStackAGV_EngineeringCandidate_v824.blend`, SHA256 `D3C9C0D398E11890DF53FBA9361E38D03AAF322EB9FACEABFC2F5E761742BD7A`. Exact 3200 x 2200 mm plan bounds, four drives, separate 100 mm lift, eight rollers, four locators and exact carrier/stack contact/containment pass. Seven views inspected; first E-stop width overrun corrected and rerendered. Owner appearance, collision/runtime sweep and Unreal remain open; outer route only. Credits used: 0.

Blank-stack AGV runtime-prep v825: successor `SourceAssets/Candidate/PressShop/BlankStackAGV/RuntimePrep_v20260809_v825/Cairnwell_BlankStackAGV_RuntimePrep_v825.blend`, SHA256 `22B597D90474DD52729553A898B38A2009CC05EC1395D6D7D1BC7027A7B084E6`. Three separate hidden collision proxies cover chassis, moving deck and loaded payload. Separate carrier/stack references follow the payload root: +100 mm transient lift moved 28 descendants within `3.58e-8 m`, then restored neutral with zero error; saved master is lowered. Owner appearance and Unreal sweep open; outer route only. Credits used: 0.

Support-fleet/dual-AGV gate v826: `Saved/Audits/PressShopIntegration/support_fleet_vs_dual_agv_route_decision_v20260809_v826.json` retains 2x CR01, 2x MR01, all four docks and the passed runtime; never spend Meshy credits regenerating them. Robot egress runs north away from the south blue lane. North/east/west outer AGV segments are provisionally usable. Hold the south segment beside dock X -1250 to +250 cm for the 2.20 m-wide blank-stack AGV because current evidence records only the dock face, not exact rear collision depth. In a fresh v791 child, trace both loaded AGV envelopes against exact dock collision, then repeat crossing reservation, priority stop and four robot return cycles before certifying it. No map changes; zero credits.

PR002 consistency hold v827: the five latest uploads hash exactly to archived ProPack v813, but the left-side view contradicts the others by replacing the two blue upright-mounted scanners with a central suspended mechanism. Do not use v813 in Meshy. Audit: `Saved/Audits/PressShopIntegration/pr002_propack_consistency_review_v20260809_v827.json`; correction prompt: `SourceAssets/Candidate/PressShop/PR002/ProPackCorrection_v20260809_v827/PR002_PRO_CORRECTION_PROMPT_v827.md`. v810 remains engineering/contact authority. Zero credits and no Unreal import.

Inbound crane Blender review v828: five fresh lit views are in `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/ReviewPack_v20260809_v828/Review`; audit beside them as `inbound_installed_crane_blender_review_v828.json`. Static runway, moving bridge, trolley and retained powered C-hook remain separate, and the close view confirms the hook enters the coil bore and supports it on its padded lower arm. Do not spend Meshy credits remaking it. Owner structure appearance, final structural data, Y/X/Z Blender sweep and Unreal loaded runtime remain open. Source and maps unchanged.

Inbound crane runtime-prep v829: `SourceAssets/IndustrialKit/BridgeCrane/InboundInstalledCrane/RuntimePrep_v20260809_v829/CA_MW_InboundInstalledCrane_RuntimePrep_v829.blend`, SHA256 `70BC0F905FDFFEC92A385217BEFE43E4DAF3280226108E98A854394455348BCD`. Separate zero-neutral bridge-Y, trolley-X and loaded-hoist-Z roots pass 27 extreme combinations. Measured provisional limits are Y -6/+6 m, X -2.8/+2.3 m and Z -1.45/+0.5 m; minimum loaded floor clearance 0.30 m, hook top maximum 5.74 m under the 5.93 m bridge underside, neutral restore error zero. First invalid hierarchy was rejected before retention. Final engineering and Unreal runtime remain open; source/maps unchanged; zero credits.

Inbound crane placement v830: `Saved/Audits/PressShopIntegration/inbound_crane_clean_placement_contract_v20260809_v830.json` fixes a provisional clean root (-9120,-2500,0) cm yaw 0 from v829 reach and clean v035 lorry evidence. All four trailer coils map to bridge -6/-2/+2/+6 m at trolley +1.2 m. PR001 maps to (-9400,-2500,0) cm at yaw 90 and trolley -2.8 m; yaw 90 is required to turn PR001 local-Y bore into world-X for the C-hook/trailer coil axis. Rotated PR001 and lorry retain 1.80 m plan gap. PR003 is AGV-only and outside crane reach. Exact column/dock collision and loaded runtime remain open in a fresh v791 child; maps unchanged, zero credits.

Inbound combined handoff v831 supersedes every v830 coordinate. Source `SourceAssets/Candidate/PressShop/InboundHandoffComposite_v20260809_v831/Cairnwell_Inbound_Lorry_Crane_PR001_Handoff_v831.blend`, SHA256 `CB1170BCB41665A123EEE9DA7AEEC03697BBF5973214FEBB2FA77279216D4A09`, combines the actual accepted lorry/four coils, v829 crane and PR001. Correct contract: crane (-9120,-2722,0) cm yaw 0, lorry (-9000,-2500,0) yaw -90, PR001 (-9400,-2500,0) yaw -90. Four pickups use bridge +6/+2/-2/-6 m and trolley +1.2 m, maximum error 5.875 mm; PR001 uses bridge +1.5 m/trolley -2.8 m, error 4.527 mm. PR001-lorry gap is 1.625 m. Authority audit: `Saved/Audits/PressShopIntegration/inbound_handoff_blender_placement_contract_v20260809_v831.json`. Exact shell/dock collision and Unreal runtime remain open; protected map unchanged and zero credits.

Inbound overlap/route v832-v833: a headless read-only v791 actor-bounds audit found no fixed shell, dock or column blocker inside the corrected v831 crane/lorry/PR001 volumes. Existing colliders are only the retained lorry/four coils/eight stands and expected floor contact. The current west AGV surface, its blue edge and the west-inner yellow walkway edge cross the validated PR001/crane volume, so `Saved/Audits/PressShopIntegration/inbound_v831_static_overlap_decision_v20260809_v833.json` holds that segment for rerouting around the guarded inbound cell. Do not certify or reuse the current west strip. Exact primitive/runtime testing remains open; protected v438 unchanged and zero credits.

Support robots v834: retain MR01 v022 unchanged; its newer visuals, modular maintenance arm/tools, corrected materials and runtime/dock contract pass. CR01 v022 remains the functional/runtime fallback but its block-built body reads older than MR01/new machinery. Do not delete it or spend credits blindly. `SourceAssets/Candidate/PressShop/SupportRobots/CR01_VisualReplacement_v20260809_v834/CR01_PRO_AND_MESHY_JOB_v834.md` fixes its 1520 x 980 x 1120 mm envelope, cleaning modules, rear dock datum and separated movers for five Pro views followed by at most one owner-approved Meshy generation. Audit: `Saved/Audits/PressShopIntegration/support_robot_visual_parity_decision_v20260809_v834.json`. Zero credits/maps unchanged.

Inbound AGV bypass v835: the invalid X -9500 west strip is replaced at reservation level by a 5.20 m-wide corridor centred X -7450 cm, Y -4450 to +4450 cm, connecting the outer north/south routes. Edges X -7710/-7190 leave 9.275 m from the corrected crane and 8.950 m from the nearest PR003 support. Final PR002 guarding must remain west of X -7860 to preserve 1.50 m lane clearance or the route must be recalculated. Authority: `Saved/Audits/PressShopIntegration/inbound_agv_bypass_reservation_v20260809_v835.json`. No actors installed; rounded spline, bays and exact runtime remain open. Zero credits/map changes.

Current generation queue v836: use `Saved/Audits/PressShopIntegration/press_shop_current_generation_queue_v20260809_v836.json`, not stale top-level summary wording. Correct PR002 views first; optional CR01 replacement only after owner rejection; then PR004 missing equipment, PR005, PR007/PR006, PR008-PR010 and shared press-train missing kit. Pro consistency precedes Meshy every time. Generate shared train kit once and instance across A-D; retain the S03 Walker body and current S07 geometry. Preserve an untouched textured master plus a separate segmented blend. Zero credits/maps changed.

PR005 v837: new controlled job `SourceAssets/Candidate/PressShop/PR005/ProDesignPack_v20260809_v837/PR005_PRO_DESIGN_AND_MESHY_JOB_v837.md` closes the prior prompt gap. It fixes the 5763 x 10360 x 3550 mm shell, exact inlet/outlet/scrap/HMI datums, 1500 mm strip path and nine separated modules. Five unchanged Pro views must pass before Meshy; Candidate_v002 remains interface/pivot authority only. Audit `Saved/Audits/PressShopIntegration/pr005_pro_job_readiness_v20260809_v837.json`. Zero credits/maps changed.

PR004/PR006/PR007 v838: their existing jobs now explicitly demand five separate unchanged Pro views and forbid combined sheets. PR004 excludes the retained robot/coil/state geometry; PR006 preserves 9+10 rolls, four cylinders and three motors; PR007 preserves four headers, twenty nozzles and two tanks and excludes retained strip bridges. Each must keep an untouched textured master and a separate texture-verified segmented blend. Audit `Saved/Audits/PressShopIntegration/pr004_pr006_pr007_separate_view_prompt_gate_v20260809_v838.json`. Zero credits/maps changed.

PR002 scanner v839: user supplied textured and segmented Blender files. Workspace intake `SourceAssets/Candidate/PressShop/PR002/UserScanner_v20260809_v839` contains untouched copies, inspections and four true orthographic renders. Textured master is visually usable but one mesh and includes the wrapped coil; segmented source has 16 parts but zero materials/textures. Conditional accept: modularize and preserve/transfer textures in Blender, separate the coil as a gameplay payload, scale to PR002, then render before Unreal. Do not spend more Meshy credits on PR002 yet. Audit beside the files as `PR002_SCANNER_INTAKE_AUDIT_v839.json`.

PR002 scanner v842: v841 automatic textured coil cut was rejected because the empty render left suspended white fragments. Use workspace `SourceAssets/Candidate/PressShop/PR002/UserScanner_v20260809_v839/PR002_CoilScanner_ModularPainted_v842.blend` SHA256 `8118C7358D6F5DDE4CECE87074526B97A27E775D5CD18F441C7EE91A8E5FA0A7`. It has 16 named/painted modules and separate wrapped-coil plus label payload; loaded and empty Blender renders pass with intact cradle and no floating coil remnants. Still reduce ~1.94M polygons, scale, add pivots/collisions and test in Unreal. Zero Meshy credits.

## 2026-08-10 — engine/pipeline audit and clean promotion gate

- Engine decision: retain Unreal Engine 5.8. The isolated untouched high-resolution S03 Walker renders correctly, while the former merged/reworked v015 shell is visibly faceted. The failure is revision/asset/conversion authority, not general Meshy incompatibility with Unreal.
- Adopt a hybrid asset package: untouched textured `VisualMaster`, lightweight major-part `MotionProxy`, independent simple `CollisionProxy`, and stable data-driven `GameplayActor`. Never force a two-million-polygon 105-part split with no UVs to serve all four roles.
- Project inventory exposed the core process risk: 526 map packages, 2,989 scripts, 152 candidate `.blend` files and 88 candidate `.glb` files. Freeze old maps as evidence; promote only manifest entries into the one clean rebuild map.
- Durable audit: `Docs/PRESS_SHOP_ENGINE_AND_PIPELINE_AUDIT_2026-08-10.md`. Working asset authority: `SourceAssets/Candidate/PressShop/PRESS_SHOP_APPROVED_ASSET_MANIFEST_v20260810.json`.
- Installed games were inspected read-only only. Car Manufacture and Captain of Industry are Unity titles; Production Line exposes separate simulation configuration and lightweight sprite/animation data. Transferable rule: keep simulation/layout separate from rendering and instance repeated visuals. No proprietary code/assets were copied or decompiled.
- Godot and Unity are capable alternatives but do not repair missing UVs, malformed geometry, bad pivots or heavyweight animation hierarchies, and migration would discard the existing tested Unreal player placement, routing, progression and save systems.
- Immediate build order: finish one accepted placeable Train A, prove placement/connect/save in the clean shell, instance B-D, then populate inbound/storage/prep/AGVs, dynamic walkways/routes, and support robots. No Meshy credits were used for this audit.

## Latest playable-game checkpoint — PlayerBuildable_v972 (2026-08-10)

The first corrected player-buildable Windows vertical slice is now packaged at `Builds/PlayerBuildable_v972/Windows/LineBossCarFactory.exe`. BuildCookRun and a hidden packaged boot smoke both exited 0, loading clean map `/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913` with `LBGameMode`.

Gameplay authority is now the console-free player builder, not the old control room. The contiguous flow is inbound -> PR002 -> wrapped-coil storage -> depack/ID -> decoiler/threader -> prepared blanks -> Press Train A-D -> inspection -> finished buffer -> outbound. The full-detail untouched Coil AGV and controlled R2 wrapped-coil runtime asset are bound. Presses are floor-seated and oriented from audited through-throat geometry rather than the contradictory Pro elevation; six cup transfers share the 202.221 cm internal panel datum. Each line is one placeable/saveable/removable 89-module actor, and only four live trains A-D are allowed.

Console-free bootstrap and regressions pass: 3/3 runtime, 5/5 material flow, plus AGV presentation, ordered catalogue, train identity persistence and builder boot/confirm. Unsafe and restart-required trains remain blocked. Protected v438 is unchanged at `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`. Missing final art is intentionally represented by gameplay placeholders; replace visuals later without reopening the proven flow. Use keyboard/mouse because gamepad placement confirm is not yet wired. Meshy credits used: **0**.

## Latest future-vehicle checkpoint — M1 Moorcross v974-v975 (2026-08-10)

The first product vehicle is now defined as a believable model-year-2042 Cairnwell M1 Moorcross five-door electric hatchback. The durable concept board and under-800-character Meshy web prompt/checklist are in `SourceAssets/Candidate/Vehicles/M1_Moorcross/DesignAuthority_v975/`.

One 20-credit API geometry preview was completed and then rejected—no refine or texture followed. Blender measured it at roughly 4.38 x 2.0095 x 1.5506 m when length-correct, versus the 4.38 x 1.82 x 1.45 m target, and five neutral renders confirmed a swollen contemporary crossover silhouette. Preserve it only as rejection evidence under `MeshyTextPreview_v974`; use the owner's 40 web retries to select good raw geometry before downloading original, split and textured masters separately. Meshy balance recorded after the preview: 6765.

## Latest PR004 art checkpoint — modular Meshy retry pack v976 (2026-08-10)

Do not generate the whole PR004 cell as one fused model. The Blender-audited engineering authority is now divided into five owner web-retry jobs: cradle, film winding/transfer, compactor, output saddle and wrist depack tool. Exact prompts, envelopes and exclusions are in `SourceAssets/Candidate/PressShop/PR004/MeshyWebRetryPack_v20260810_v976/PR004_MESHY_WEB_RETRY_PACK_v976.md`. Retain the existing six-axis arm and coil/state assets; build guards, scanners, HMI and bin as reusable deterministic modules. No credits or maps changed; every winner still needs Blender approval before split, texture and Unreal.

## Latest authority checkpoint — runtime-reconciled manifest/queue v977 (2026-08-10)

Use `SourceAssets/Candidate/PressShop/PRESS_SHOP_APPROVED_ASSET_MANIFEST_v20260810.json` and `Saved/Audits/PressShopIntegration/press_shop_current_generation_queue_v20260810_v977.json`. They now reflect v973: inbound, PR002, storage, Coil AGV, S01/S02-S06/S07, CR01/MR01 and their docks are integrated and must not be regenerated. PR004 modular geometry is next; PR005 and later cells remain gated by consistent owner-approved views. This reconciliation changed no map/code/assets and spent no credits.

## Latest AGV route checkpoint — continuous inbound authority v978 (2026-08-10)

Inbound no longer authorizes movement merely because two route tiles exist somewhere. `LBCoilAGVController` now proves continuous painted coverage of wait-to-turn and turn-to-live-PR002-input legs. The focused runtime test rejects two distant tiles, accepts the correctly rotated connected route and completes the identity-preserving unload. Editor build, ConsoleFreeRuntime 3/3 and MaterialFlow 5/5 pass. Evidence: `Saved/Audits/PressShopIntegration/inbound_player_agv_continuous_route_authority_v20260810_v978.json`. Zero credits/map changes.

Playable v978 is packaged at `Builds/PlayerBuildable_v978/Windows/LineBossCarFactory.exe`. BuildCookRun passed; hidden packaged smoke exited 0 and loaded clean v913 with `LBGameMode`.

## Latest inbound placement checkpoint — measured package v979 (2026-08-10)

The player-placed inbound lorry no longer floats 225 cm above the floor and no longer protects only its trailer-sized body. Imported runtime bounds now reserve the complete lorry/crane/saddle package with a measured offset envelope: visible X -602.5..362.5 cm, Y -944.5..825 cm, Z 0..797 cm, plus 25 cm lateral placement clearance. Placement collision, debug box and floor grid use the same rotated offset envelope, so routes and machines cannot be placed through the crane structure. Audit: `Saved/Audits/PressShopIntegration/inbound_player_package_protected_placement_v20260810_v979.json`. Editor build, ordered catalogue, management and ConsoleFreeRuntime tests pass; protected v438 hash is unchanged; zero Meshy credits used.

Current executable is `Builds/PlayerBuildable_v979/Windows/LineBossCarFactory.exe`; BuildCookRun succeeded and packaged smoke loaded clean v913 with `LBGameMode`.

## Latest controller checkpoint — contextual placement confirm v980 (2026-08-10)

Cross/A now confirms the open catalogue or whichever player placement preview is active (machine, storage or infrastructure). The former packaged-build caveat that gamepad could select but not place is removed in source. Editor build and Management 2/2 pass. Audit: `Saved/Audits/PressShopIntegration/contextual_gamepad_placement_confirm_v20260810_v980.json`; zero Meshy credits used.

Current executable: `Builds/PlayerBuildable_v980/Windows/LineBossCarFactory.exe`. BuildCookRun and clean-v913/LBGameMode packaged smoke pass; protected v438 is unchanged.

## Latest physical-unload checkpoint — C-hook bore and saddle datum v981 (2026-08-10)

The player-built inbound sequence no longer snaps the wrapped coil's bottom pivot onto the hook pivot. It uses Powered C-hook v035's retained visual interface (load centre 150 cm from the body and 59 cm below the hook datum), the wrapped-coil mesh-origin bore centre, and the measured receiving-saddle top. Live automation proves bore engagement and final saddle seating within 1 cm; MaterialFlow passes 5/5. Audit: `Saved/Audits/PressShopIntegration/player_inbound_chook_bore_and_saddle_datum_v20260810_v981.json`. Engineering certification remains TBC; protected v438 is unchanged; zero Meshy credits used.

## 2026-08-10 — current playable checkpoint v982

Use `Builds/PlayerBuildable_v982/Windows/LineBossCarFactory.exe`. Inbound save schema v4 now persists the complete moving crane pose plus lorry and active coil, while schemas 1-3 stay readable. Editor build, MaterialFlow 5/5, BuildCookRun and packaged clean-v913 smoke all pass. Audit: `Saved/Audits/PressShopIntegration/player_inbound_mid_unload_save_v20260810_v982.json`. Zero Meshy credits used.

## 2026-08-10 — current playable checkpoint v983

Use `Builds/PlayerBuildable_v983/Windows/LineBossCarFactory.exe`. Controller centre-screen placement now covers routes/walkways/crossings and all floor infrastructure; press handoffs allocate A-D; infrastructure can no longer misroute the inbound coil AGV away from PR002. Exact clean service-bank positions and separate docks for CR01-01/02 and MR01-01/02 are asserted and commissioned. Build, packaging, smoke and 20 focused tests pass. Audit: `Saved/Audits/PressShopIntegration/player_infrastructure_train_handoffs_and_support_fleet_v20260810_v983.json`. Zero Meshy credits used.
## 2026-08-10 — v984 process-readable placeholder checkpoint

- `PlayerBuildable_v984` replaces block-only pending-art machines with tested modular placeholders: PR004 open gantry/V-cradle/robot, PR005 correctly oriented reel/mandrel/roller line, panel inspection portal/bed, and AGV-accessible outbound stillage dock.
- No approved visual master or protected old map was touched. All existing process ports and player-built order remain authoritative. Final owner-approved art can replace these modules without changing gameplay/save identity.
- Editor build, catalogue, material flow, Press Trains A-D, support robots, console-free boot, approved AGV, BuildCookRun and packaged smoke all pass. Evidence: `Saved/Audits/PressShopIntegration/player_process_readable_placeholders_v20260810_v984.json`.
- No Meshy credits used.

## 2026-08-10 — v985 complete coil-preparation checkpoint

- Use `Builds/PlayerBuildable_v985/Windows/LineBossCarFactory.exe`. The ordered catalogue's save-compatible coil-prep item now covers PR005 through PR010 in one 35-module player-placeable package with six progress steps; duplicates provide parallel bottleneck capacity.
- Editor build, ordered catalogue, material flow 5/5, packaging and clean-v913/LBGameMode smoke pass. Protected v438 remains SHA-256 `5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8`.
- C plastic-film compactor: visual candidate only, audit `plastic_film_compactor_intake_v20260810_v985.json`. A powered cradle attempt is rejected as a spindle unwinder; wait for corrected front/rear/left/right Pro views before another Meshy generation.

## 2026-08-10 — v986 branch/merge and support-fleet checkpoint

- Use `Builds/PlayerBuildable_v986/Windows/LineBossCarFactory.exe`. Automatic routes now support real fan-out/fan-in and late-added parallel capacity. A real actor test proves one blank buffer feeds Press Trains A-D and all four trains merge into the common inspection cell.
- Storage primitives use controlled Cairnwell materials without overriding approved coil/stand art. The accepted two CR01/two MR01 service bank and four independent docks remain at their proven clean transforms and pass commissioning/runtime tests.
- Valid tests: Transport 2/2, MaterialFlow 5/5, ordered catalogue 1/1, ConsoleFreeRuntime 3/3, AGV infrastructure 1/1, PressTrains 4/4 and SupportRobots 4/4. BuildCookRun and packaged clean-v913 smoke pass. Protected v438 hash is unchanged.
- Pro sheet review: A powered cradle, B film winder, C compactor and D output saddle are concept-approved but must be supplied to Meshy as separate consistent orthographic sheets; E wrist tool needs simplification first. Audit: `player_branch_merge_storage_support_checkpoint_v20260810_v986.json`. Zero Meshy credits used by Codex.

## 2026-08-10 — PR004 runtime art and autonomous coil-handler checkpoint v997-v999

- PR004 A-E and the reusable adjustable V-block saddle are consolidated in `SourceAssets/Candidate/PressShop/PR004_FilmDepack/Assembly_v20260810/Cairnwell_PR004_CompleteCell_v996.blend`. Runtime exports/imports pass at 1,218,739 and 244,711 triangles respectively; gameplay coil loads remain separate. Audits: `pr004_complete_runtime_export_v997.json` and `pr004_unreal_import_v997.json`.
- The overhead crane is retired from normal player-built inbound production. Legacy crane-named component slots remain only for old-save compatibility; the visible unload authority is a driverless 30 t bore-ram coil-handler.
- Owner Meshy masters are preserved under `SourceAssets/Candidate/PressShop/Inbound/CoilHandlerAGV_v20260810/Original`. The split is not render authority because its mast/body remains fused and its ram is absent. Hybrid authority is `Hybrid_v999/Cairnwell_AGV_CHF01_Hybrid_v999.blend`: detailed textured fixed chassis/mast plus an independent carriage/backrest/ram lift mesh.
- Unreal runtime meshes are `/Game/LineBoss/Runtime/PressShop/CoilHandlerAGV_v999/SM_Cairnwell_AGV_CHF01_StaticBody_v999` and `SM_Cairnwell_AGV_CHF01_LiftAssembly_v999`. Blender review set: `Saved/ValidationScreenshots/PressShopIntegration/coil_handler_agv_hybrid_v999`. Import/build audits pass; FactoryBuilder 12/12 tests pass after binding. Meshy credits used for the repair: 0.
- Inbound save schema v5 persists the moving handler chassis as well as the existing lift followers. The protected player-placement envelope now covers the lorry, staged handler, four coils and receiving saddle. Extra independently placeable handler capacity is still a gameplay follow-up; do not claim multiple simultaneous handlers yet.
- Current executable: `Builds/PlayerBuildable_v1000/Windows/LineBossCarFactory.exe`. BuildCookRun and hidden packaged smoke pass; clean v913 loads with `LBGameMode`. Durable checkpoint: `Saved/Audits/PressShopIntegration/autonomous_coil_handler_pr004_playable_v1000.json`.

## 2026-08-10 — Press Shop completion gate v1001

- Full current `LineBoss` automation passes 45/45. This includes ordered player construction, automatic fan-out/fan-in, continuous inbound AGV routing, autonomous four-coil unload, storage, PR004-PR010 handoffs, wider Press Trains A-D, inspection/outbound material flow, save/load, CR01, MR01, charging and guarded service docks.
- Completion is for the player-buildable Press Shop using the user-authorised pending-art placeholders where no final approved model exists. Those placeholders have real ports, buffers, branching and save identity; they are not old-map production actors.
- Final requirement matrix: `Saved/Audits/PressShopIntegration/press_shop_completion_audit_v1001.json`. Project, cooked content and package are outside OneDrive. Old v438 remains reference-only and byte-identical.

## 2026-08-10 — corrected inbound orientation and builder UX v1005

- Current executable: `Builds/PlayerBuildable_v1005/Windows/LineBossCarFactory.exe`, SHA-256 `6B66F6CAA95B46C49281728304102FDD7B963F2F73EDBB126800EC328A6DFDA1`.
- All four trailer coils are yawed +90 degrees so their bore axes run across the lorry and align with the side-entry autonomous coil-handler ram. The two long transverse support rails per coil were already correct and were retained.
- Placing PR002 now creates the initial AGV wait point, turn point and continuous route automatically, configures the live AGV, persists the generated route, and adds a parallel automatic service walkway. Painted route/walkway actors no longer create invisible collision walls.
- The clean builder HUD is now a mouse-driven bottom build bar with Machines, Storage, Logistics and Safety categories and large click-to-place cards. Automatic routes/walkways are hidden from the normal manual catalogue.
- Full `LineBoss` automation passes 46/46; BuildCookRun v1005 succeeds. A fully obstacle-aware live reroute/rejection pass remains the next routing task: current automatic route is generated on PR002 placement but does not yet recompute around later machinery.
- Agreed future company customisation: saved factory name/logo plus primary, secondary and safety colours. Meshy baked materials require one-time paint masks; after conversion a shared material parameter set must recolour all compatible assets without duplicate meshes or further Meshy spend.
