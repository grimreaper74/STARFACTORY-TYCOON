# Line Boss - full goal list from the measured audits (2026-08-17)

Every item was measured against the owner's gameplay mockup with file:line
evidence by a 37-agent analysis. Each 'absent' and 'blocker' claim was then
adversarially re-checked; 16 were overturned and are excluded here.
`state` is what the code actually does today, not what it should do.

Milestone ordering and rationale: `GAME_STANDARD_ROADMAP_2026-08-17.md`.
Press level-instance analysis: `SITE_AUTHORED_IN_EDITOR_2026-08-17.md`.

## BLOCKER (13)

| Area | State | Goal | Effort |
|---|---|---|---|
| camera | partial | player camera after commissioning (view target) | small |
| density | partial | assembly shop content (24 stations) | large |
| density | partial | packed floor — rendered instance density per department | large |
| density | partial | paint shop content (8 stations) | large |
| density | absent | reference map for weld, paint and assembly | large |
| hud | partial | Default launch state hides the production flow | small |
| hud | partial | HUD persistence — the whole shell is gated behind a toggle | medium |
| hud | present | HUD technology (Canvas vs UMG) — architectural verdict | small |
| hud | partial | cash / issued / sim-rate top strip (dead implementation) | small |
| hud | partial | persistent top bar (whole HUD shell) | medium |
| loop | absent | machine prices / cash cost of building | medium |
| loop | partial | time controls (pause / play / fast-forward) | medium |
| other | partial | map lighting authority (one RectLight) vs a daylit shop | large |

## HIGH (32)

| Area | State | Goal | Effort |
|---|---|---|---|
| camera | partial | Home / whole-factory and process framing helpers | medium |
| camera | partial | camera controls are dead at spawn (build panel opens itself) | small |
| camera | absent | camera pitch / tilt control | small |
| camera | partial | key collisions between the OneFactory controller and the management pawn | small |
| camera | partial | zoom range cannot frame a shop, let alone the site | small |
| density | partial | Factory Environment Collection (869-asset Fab pack) — largest untapped raw material | medium |
| density | partial | aisle/row spacing — empty floor between rows | medium |
| density | partial | coil racking, stillage racks and conveyor runs across all four shops | medium |
| density | partial | green painted floor zones per cell and walkway | medium |
| density | absent | mezzanines and gantries | medium |
| density | absent | multiple parallel press cells in organised rows | large |
| density | absent | shop content is spawned at runtime, not authored as actors in the editor | large |
| hud | partial | Nav icon row (factory, orders, chart, awards, settings) | medium |
| hud | partial | Per-card status label with count ("Waiting: 2") | medium |
| hud | absent | Per-card throughput figure ("18.0/hr") | medium |
| hud | absent | Right detail panel — buffer "Blank buffer: 8" with layers icon | medium |
| hud | partial | Right detail panel — throughput "14.2 panels/hr" with gauge icon | medium |
| hud | absent | Speed multiplier readout "1x" | small |
| hud | partial | Transport controls: pause / play / fast-forward | medium |
| hud | partial | Two conflicting production-flow rows draw at once (OneFactory mode) | medium |
| hud | absent | UI icon and font asset library | medium |
| hud | partial | World-space alert toast with warning triangle | medium |
| hud | absent | alert toast over the world | small |
| hud | absent | placement feedback surface | medium |
| loop | partial | income per vehicle | medium |
| loop | absent | operating costs / running expenses | medium |
| loop | absent | orders as contracts (offers, deadlines, penalties) | large |
| loop | partial | progression / research unlocks | large |
| other | partial | clerestory daylight band | medium |
| other | present | frozen exact-count contracts as the cost driver for any density increase | medium |
| other | present | press native-only provenance allowlist forbids the authored shop content | medium |
| other | partial | the playable light rig only exists as a transient runtime spawn | medium |

## MEDIUM (27)

| Area | State | Goal | Effort |
|---|---|---|---|
| camera | partial | authored management overview camera in the map is unreferenced | small |
| camera | partial | click-a-flow-card-to-fly-there | medium |
| camera | present | management camera pawn (pan / rotate / zoom) | small |
| camera | absent | mouse-driven camera (drag-pan, edge pan, drag-orbit) | medium |
| camera | partial | opening frame is not a shop overview | small |
| camera | partial | player-facing framing targets the whole 610 m route, not one shop | small |
| camera | partial | roof cutaway mechanism | medium |
| camera | partial | two incompatible lens languages (48 deg pawn vs 78 deg dev camera) | small |
| density | partial | IndustrialKit dressing props not placed in the route | small |
| density | partial | engine-primitive content still carrying visual load | medium |
| density | present | press station content is one baked aggregate mesh, and it is hidden at runtime | large |
| density | partial | reference manifest is lossy and press-anchored | medium |
| density | partial | service cabinets and HMI/control furniture outside press | medium |
| hud | absent | "1x" speed readout | small |
| hud | partial | Alert bell with count "2 alerts" | medium |
| hud | partial | Cash readout "£2.50m" | small |
| hud | partial | Company mark + "CAIRNWELL AUTOMOTIVE" | small |
| hud | partial | Green flow arrows between cards | medium |
| hud | partial | Non-16:9 layout — whole shell letterboxes | medium |
| hud | partial | Primary green CTA "Place next machine" with chevron | small |
| hud | partial | Top-bar typography scale and chip styling | small |
| hud | partial | Vehicle model badge pill "CAIRNWELL 2040" | small |
| hud | partial | top-bar nav icon row and hamburger | medium |
| loop | present | automatic systems on placement (auto-connect, walkways, AGV route) | small |
| loop | partial | save / load | medium |
| other | present | authored asset library — what raw material actually exists | small |
| other | partial | the whole presentation path runs through a class documented as developer-only | medium |

## LOW (20)

| Area | State | Goal | Effort |
|---|---|---|---|
| camera | partial | camera feel: no pan bounds, no pan/orbit smoothing | small |
| hud | present | "Production flow" panel with horizontal card chain | small |
| hud | absent | Hamburger menu button | small |
| hud | absent | Localisation of the UMG shell | medium |
| hud | present | Order counter "0 / 16 issued" | small |
| hud | present | Per-card coloured status dot | small |
| hud | present | Per-card rendered 3D machine thumbnail | small |
| hud | absent | Render-target / live thumbnail capture capability | large |
| hud | present | Right detail panel — title | small |
| hud | present | Selected-card green outline | small |
| hud | present | flow-card 3D thumbnails | small |
| hud | partial | vehicle model badge pill | small |
| loop | present | "Place next machine" build flow | small |
| loop | present | alert system and queue | small |
| loop | present | cash model / ledger | small |
| loop | present | order counter "0 / 16 issued" | small |
| loop | present | per-station Running / Waiting / Blocked state | small |
| other | present | Overlapping Canvas placement card drawn by the pawn | small |
| other | absent | awards / trophy progression | large |
| other | present | maintenance and quality simulation | small |


---

# Detail

## 1. [blocker / camera] player camera after commissioning (view target)

**State today: partial.** A management camera DOES exist (see next row), but it stops being what the player looks through. ALBOneFactoryPlayerController::EnsureSitePresentation ends by calling ULBOneFactoryDevFactory::FrameProductionLine(this, "All"), which spawns a transient ACameraActor tagged LB.OneFactory.DevCamera and calls Controller->SetViewTargetWithBlend(Camera, 0.0f). That is the ONLY SetViewTarget* call in the whole module (verified by grep), and nothing ever hands the view back to the pawn. Engine-side, APlayerController::AutoManageActiveCameraTarget only runs on possess/restart (PlayerController.cpp:863, :921), never per tick, so the dev camera stays the view target for the rest of the session. Consequence: after the player presses B to commission the factory - the normal and only way to get a factory - WASD pan, Q/E rotate, mouse-wheel zoom and Home all still drive ALBManagementPawn, but the screen never moves. The same happens after F9 load (LoadFactory -> EnsureSitePresentation). This is the single thing standing between the current build and a steerable mockup-grade view: the pose the dev camera picks is roughly right (34 deg down-pitch, solved fit), it just cannot be moved.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:224; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:401; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:762; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:774; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:795

## 2. [blocker / density] assembly shop content (24 stations)

**State today: partial.** Assembly renders exactly 95 instances across 10 batches for 24 stations — literally 3 props per station (one skillet carrier, one per-operation machine, one status cube) plus 23 route cubes. BuildExpectedPresentationItems adds nothing else. The dev dressing adds a further ~2-3 props per station by semantic stage (robot, bench, parts cart, lift platform, wheel racks, alignment bed, EOL arch) plus one control cabinet and side guarding from the common branch. No racking rows, no overhead conveyor, no mezzanine, no service cabinets, no aisle definition. Eight authored AssemblyLineNativeKit_v001 meshes exist and all eight are already used, so the kit itself is exhausted — new density here needs either more authored assembly modules or the Fab pack.

Evidence: Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActor.cpp:11; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActor.cpp:613; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActor.cpp:658; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:645; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActorTests.cpp:28

## 3. [blocker / density] packed floor — rendered instance density per department

**State today: partial.** Press alone is at reference density; the other three bays are near-empty. Rendered instances vs bay floor area: press 2,804 instances over 41,600 m2 (0.067/m2, delivered by the manifest actor, not by the station route); body/weld 597 over 18,000 m2 (0.033/m2); paint 119 over 22,000 m2 (0.0054/m2); assembly 95 over 33,600 m2 (0.0028/m2). Assembly is 24x sparser than press, paint 12x. Station-footprint occupancy of each bay: press 6,412/41,600 m2 = 15%, weld 9,792/18,000 = 54%, paint 819/22,000 = 3.7%, assembly 14,256/33,600 = 42%. The mockup's "floor is PACKED" is only true of the press bay, and only because a dev manifest actor instances the reference map on top of the route.

Evidence: Source/LineBossCarFactory/LBOneFactoryTypes.cpp:154; Source/LineBossCarFactory/LBOneFactoryDevRestoredShopActor.cpp:84; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActor.cpp:16; Source/LineBossCarFactory/LBOneFactoryPaintStarterPresentationActor.cpp:14; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActor.cpp:12; Docs/OneFactory/SESSION_HANDOVER_2026-08-17.md:11

## 4. [blocker / density] paint shop content (8 stations)

**State today: partial.** Paint renders 119 instances across 22 batches in a 220 x 100 m bay — 3.7% floor occupancy, the sparsest department. All eight stations sit on one straight line at Y=-8500 spanning X 0 to 11800 cm (118 m of a 220 m bay), leaving over 100 m of empty floor at one end and the full 100 m bay depth almost untouched. The dev dressing deliberately places nothing in Paint (to avoid z-fighting the frozen presentation), so 119 instances is the whole shop. The authored PaintLineNativeKit_v001 plus ED line kit is already fully bound; the unused remainder is 6 superseded blockout modules and 2 access stairs.

Evidence: Source/LineBossCarFactory/LBOneFactoryPaintStarterPresentationActor.cpp:12; Source/LineBossCarFactory/LBOneFactoryPaintStarterLayout.cpp:62; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:627; Source/LineBossCarFactory/LBOneFactoryTypes.cpp:160

## 5. [blocker / density] reference map for weld, paint and assembly

**State today: absent.** Press has a 4,092-actor density authority at /Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001 (11.3 MB .umap) and a 2,804-entry mesh manifest derived from it. Nothing equivalent exists for the other three. The only candidates found across all of Content: LB_BodyShop_Prototype_v001.umap (666 KB, Experimental), LB_PaintShop_Prototype_v001.umap (74 KB, Experimental), and LB_WeldRobotRuntime_v001_VisualGate.umap (58 KB, a single-robot gate). There is no assembly map at all. Content/LineBoss/Maps holds ~420 maps, every one of which is a press-shop, press-train, control-room or PR004 candidate. So there is no authored target to measure weld/paint/assembly density against — the press bar cannot be transplanted, it has to be authored.

Evidence: Content/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001.umap; Content/LineBoss/BodyShop/Experimental/v001/Maps/LB_BodyShop_Prototype_v001.umap; Content/LineBoss/PaintShop/Experimental/v001/Maps/LB_PaintShop_Prototype_v001.umap; Content/LineBoss/Developer/Validation/WeldShop/WeldRobotRuntime_v001/LB_WeldRobotRuntime_v001_VisualGate.umap

## 6. [blocker / hud] Default launch state hides the production flow

**State today: partial.** The mockup's default frame is the production-flow view. On a clean (console-free) map the pawn calls HUD->OpenFactoryBuild() during its one-shot Tick bootstrap, which sets ManagementPage = FactoryBuild. SetManagementContext() then collapses FlowTrayBorder and shows ContextBorder instead, so the player launches into the five-card Build context panel with no flow tray, no detail panel and no thumbnails visible. Returning to the flow tray requires the Overview page, and there is no on-screen control for it (see the nav-icon-row entry) — only the `[` / `]` page-cycle keys.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1038; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:993; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:907; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2212

## 7. [blocker / hud] HUD persistence — the whole shell is gated behind a toggle

**State today: partial.** The mockup's HUD is always on screen. Here the entire UMG shell is collapsed unless bManagementVisible is true: SyncModernOverviewWidget() sets ESlateVisibility::Collapsed whenever IsModernManagementActive() is false, and bManagementVisible defaults to false. Pressing M (LB_ToggleManagement) hides the top bar, cash, alerts, flow tray and detail panel in one go, leaving no HUD at all under LBGameMode. Additionally ActivateProductionFlowPrimaryAction() deliberately sets bManagementVisible = false when a placement starts, so using the mockup's own CTA dismisses the whole HUD. The fix is to split the shell into a persistent chrome layer (top bar + flow tray + detail) and an optional modal layer, rather than one all-or-nothing visibility flag.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1474; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1241; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.h:236; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2782; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1142; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultInput.ini:12

## 8. [blocker / hud] HUD technology (Canvas vs UMG) — architectural verdict

**State today: present.** The mockup is achievable: the live HUD is UMG/Slate, not Canvas. ALBControlRoomHUD::DrawHUD() draws nothing on Canvas — it calls only EnsureMandatoryFactorySetup() and SyncModernOverviewWidget(). Every legacy Canvas surface is excluded from the build behind four `#if 0` blocks (HandlePersistentHUDClick 827-854; DrawPersistentFactoryHUD 858-1159; DrawProductionFlowHUD 2787-3116; DrawFactoryBuildHUD + DrawFactoryBrandEditor + DrawManagementHUD 3347-4032), with the in-source comment 'Retired Canvas implementation. The active HUD is UMG-only'. Those functions are also absent from the header (only DrawHUD is declared), so they are unreachable dead code. The live shell is ULBManagementRootWidget, a UUserWidget whose Slate tree is built entirely in C++ via WidgetTree->ConstructWidget (no Widget Blueprints exist anywhere in Content — `find Content -iname "WBP*"` returns nothing), added via AddToPlayerScreen(50). The one exception is ALBOneFactoryProductionHUD, which still Canvas-draws a flow strip and toasts over the top. Conclusion: build all mockup work in the UMG shell; do not extend the Canvas path.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:4034; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:827; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:856; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2787; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:3347; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1203

## 9. [blocker / hud] cash / issued / sim-rate top strip (dead implementation)

**State today: partial.** ALBControlRoomHUD::DrawPersistentFactoryHUD (lines 859-1160) already draws almost exactly the mockup's top bar: a CASH readout via FormatMoneyPence, 'ISSUED n / n' with a progress bar, 'RP n | SIM n.nx', a 'HEALTH n ASSETS' counter, and a world-space alert marker from TopAlert->MarkerWorldLocation. It is never called. ALBControlRoomHUD::DrawHUD only calls EnsureMandatoryFactorySetup and SyncModernOverviewWidget, so no Canvas layer is drawn at all. HandlePersistentHUDClick and GetPersistentHUDHeight are likewise orphaned. This is ~300 lines of finished, on-target work that is simply unreachable — either call it or port its content into the UMG strip.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:859; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:986; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1048; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:4034

## 10. [blocker / hud] persistent top bar (whole HUD shell)

**State today: partial.** The mockup's HUD is a permanent fixture. The implementation makes it a modal overlay: ALBControlRoomHUD::bManagementVisible defaults to false, and SyncModernOverviewWidget collapses ManagementRootWidget whenever IsModernManagementActive() is false. A fresh game therefore shows NO HUD at all until the player presses M (LB_ToggleManagement). Worse, the shell actively hides itself when the player acts: bManagementVisible = false on placement start and on actor selection, so the top bar disappears exactly when the player is building. Needs the top strip + flow tray split from the modal page system so they render unconditionally.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.h:236; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1228; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1241; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1476; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2756; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2781

## 11. [blocker / loop] machine prices / cash cost of building

**State today: absent.** The economy has no sink. Grepping CostPence and PricePence across all 318 source files returns hits only inside LBFactoryManagementSubsystem and its tests — there is no price catalogue for any machine type. ULBFactoryMachineBuilderSubsystem::PlaceMachine (line 1778) never consults cash and never calls TryPurchaseCapitalAsset; CanPlaceMachine (line 882) gates purely on process-chain prerequisites ('PLACE THE INBOUND DELIVERY CELL FIRST'), never on affordability. TryPurchaseCapitalAsset and TryChargeOperatingCost have zero non-test callers, so cash only ever goes up. Without prices, the mockup's £2.50m readout is decoration and the whole build flow has no economic decision in it.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:1778; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:882; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.cpp:176; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.cpp:203

## 12. [blocker / loop] time controls (pause / play / fast-forward)

**State today: partial.** Two independent defects make the buttons inert on the shipping map. (1) Wrong-world gate: HandleModernSimulationRateRequested returns early unless Operations->IsOneFactoryOperationsWorld(), which requires an ALBOneFactoryBootstrap actor with a valid shell plus a runtime coordinator. The default map is LB_PressShop_RebuildFromLorry_v20260810_v913 under ALBGameMode, so pressing pause/play/2X does nothing at all. (2) Readout disconnect: the snapshot's EffectiveSimulationRate reads AWorldSettings::GetEffectiveTimeDilation(), but SetSimulationRate writes Coordinator->RuntimeTimeScale and Production->SetLinePaused and never touches world dilation — so even where the buttons work the displayed rate stays 1.0x forever. The setter itself is well built (clamped 0-4x, ledger snapshot and rollback on failure).

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1617; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryOperationsSubsystem.cpp:109; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryOperationsSubsystem.cpp:529; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryRuntimeCoordinator.cpp:801; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:203; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultEngine.ini:3

## 13. [blocker / other] map lighting authority (one RectLight) vs a daylit shop

**State today: partial.** The shipped map's entire lighting authority is one movable RectLight at (0,0,6500) pitched straight down, tagged LB.OneFactory.Lighting.Authority.5000K.v001, plus one unbound PostProcessVolume tagged LB.OneFactory.Lighting.FixedExposure.v001 that pins AutoExposureBias/Method/Min/Max. The measured result is roughly half the intended exposure: the project's own frozen diagnosis records mean luma 0.164 with 52.85% black clipping on the empty whole-factory overview and 0.174 / 49.43% on the populated Press overview, against a reference envelope of 0.35-0.48 mean luma and at most 1.0% clipping, from one 800,000 lm fixture with a 60000x29000 cm face and 45000 cm attenuation. The replacement 32-fixture grid contract (48000 lm each, 5000 K, plus a 0.30 DirectionalLight and 0.20 SkyLight) is frozen but explicitly 'not executed', and Content/LineBoss/Factory/OneFactory/v002 does not exist on disk. After the press lit pass the floor band still reads 37.4/255 against an audit target of 40, with 39.2% dark fraction.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap:1; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Docs/OneFactory/ONE_FACTORY_VISUAL_NAVIGATION_V002.md:36; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Docs/OneFactory/ONE_FACTORY_VISUAL_NAVIGATION_V002.md:53; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Docs/OneFactory/ONE_FACTORY_VISUAL_NAVIGATION_V002.md:60; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Docs/OneFactory/ONE_FACTORY_VISUAL_NAVIGATION_V002.md:3; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Docs/OneFactory/PRESS_SHOP_RELEASE_AUDIT_2026-08-16.md:60

## 14. [high / camera] Home / whole-factory and process framing helpers

**State today: partial.** The pawn has a well-developed framing system - BuildFactoryOverviewFramingContract (yaw -50, pitch -32, distance = LongAxis*1.04 + ShortAxis*0.12 + Z*0.45, plus an explicit bias so the HUD tray does not cover the visual centre) and BuildProcessOverviewFramingContract (crops to the 65.69% of a 720p canvas left above the tray). It is dead on the OneFactory map. FocusBuiltFactoryInternal only accumulates actors tagged LB.FactoryBuilder.Machine or LB.FactoryBuilder.StorageZone; those tags are applied only by the legacy press-shop path (ALBFactoryBuildMachine, ULBFactoryMachineBuilderSubsystem, ALBPressShopStorageZone). Every OneFactory presentation actor tags itself LB.OneFactory.*Starter / LB.Environment.VisualOnly / LB.NotProcessWIP instead, so FramedActorCount is 0 and both FocusBuiltFactory() and FocusWholeBuiltFactory() return false. That makes Home fall through to FocusInitialBuildBay and then to a hardcoded (0,0,0) yaw -65 / zoom 9000 pose, and makes the HUD's FACTORY nav button (its documented 'two-state camera control') a no-op.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1569; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1581; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1448; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1414; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:685; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryBuildMachine.cpp:1019

## 15. [high / camera] camera controls are dead at spawn (build panel opens itself)

**State today: partial.** On the OneFactory map the pawn opens the legacy build catalogue on itself during BeginPlay and again as a one-shot in Tick, because the map contains no ALBControlRoomOperationsConsole. ALBControlRoomHUD::OpenFactoryBuild sets bManagementVisible = true. ALBManagementPawn::IsManagementOpen() then returns true, which makes MoveForward/MoveRight/Rotate store 0.0 and makes Tick return before AddActorWorldOffset/AddActorWorldRotation ever run. So the player's first frames have pan and orbit disabled; only zoom survives, because ZoomInput is consumed above the early-out. The player must press V or M to get camera control back, which nothing tells them.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:983; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1027; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1084; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1292; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2212

## 16. [high / camera] camera pitch / tilt control

**State today: absent.** The mockup's defining framing choice is the high near-isometric down-angle, and the player has no way to set it. The spring-arm pitch is hard-assigned to FRotator(-35, 0, 0) in five separate places (constructor, ResetCamera, FocusInitialBuildBay, SetAutomationCamera, FocusWorldTarget) and to the framing contract's -32 deg in FocusBuiltFactoryInternal. There is no pitch axis on the management pawn at all: SetupPlayerInputComponent binds only LB_MoveForward, LB_MoveRight, LB_Rotate (yaw) and LB_Zoom. DefaultInput.ini defines LB_ControlRoomLookPitch (Up/Down, right stick Y) but that axis is bound only by ALBControlRoomPawn, which is not on the OneFactory path. Also, no orthographic option exists anywhere in the module (grep for Orthographic / ProjectionMode / OrthoWidth returns zero hits), so 'near-isometric' can only be approached by narrowing FOV, not by projection.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:938; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1419; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1442; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1637; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1967; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1134

## 17. [high / camera] key collisions between the OneFactory controller and the management pawn

**State today: partial.** ALBOneFactoryPlayerController::SetupInputComponent uses raw InputComponent->BindKey for B, N, SpaceBar, 1, 2, 3, Q, R, F5, F9. FInputKeyBinding defaults bConsumeInput = true, and APlayerController::BuildInputStack pushes the pawn's InputComponent first and the controller's last, while UPlayerInput::EvaluateInputDelegates walks the stack from the top down (PlayerInput.cpp:1500-1516) - so the controller's bindings are evaluated first and consume the key (bConsumed set at PlayerInput.cpp:1804, honoured for axes at :1232). Net effect on camera and placement: pressing Q both passes the oldest quality hold AND is the camera's rotate-left key (DefaultInput.ini LB_Rotate, scale -1), so a camera nudge silently makes a quality decision; pressing R both reworks the oldest hold and has its LB_PlacementRotate action masked, so a placement ghost cannot be rotated; pressing B commissions the factory and fully masks the pawn's LB_BuildPressTrain action. None of these overlaps is intentional in either file.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:68; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:80; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultInput.ini:43; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultInput.ini:27; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1148

## 18. [high / camera] zoom range cannot frame a shop, let alone the site

**State today: partial.** GetMaximumManagementZoomDistance() is 30000 cm, with a comment explaining it was sized to fit the 189 m ED line. The Moorcross site is far larger: the map's interface datums put coil receiving at X -30500 and vehicle dispatch at X +30500 with the service spine at Y -14500, i.e. 610 m x 290 m, and the four bay datums alone span X -14500..+16500 by Y -8500..+8500 (310 m x 170 m). At the pawn's 48 deg FOV, fitting even the 310 m bay span needs about 35,000 cm and the ~562 m envelope the dev envelope reports needs about 63,000 cm - both beyond the cap. So the pawn physically cannot produce the mockup's 'entire shop reads in a single frame', and can never show the whole site. Minimum zoom is 1000 cm normally and is forced up to 6500 cm during any placement.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.h:228; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.h:231; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1048; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:406

## 19. [high / density] Factory Environment Collection (869-asset Fab pack) — largest untapped raw material

**State today: partial.** Content/Meshes holds 785 SM_ static meshes; native code references exactly 21 of them, 11 of those via the dev dressing kit table. The 764 unused meshes are precisely the mockup's missing vocabulary: SM_IndustrialPlatform / SM_HeavyPlatform / SM_PlatformGrill / SM_PlatformRailing / SM_PlatformPillar / SM_FloorStairs (mezzanines), SM_HeavyArch / SM_LampArch (gantries), SM_StorageShelvesBottom/Middle/Top and SM_StorageShelves_group (stillage racking), the full modular SM_Pipe_round_* and SM_Pipe_square_* sets plus SM_ElectricalPanel / SM_ElectricalSupply_Switchboard / SM_ElectricalSupply_JunctionBox / SM_CableBox (service cabinets and runs), SM_LargeWindow / SM_LargeWindowFramed (the clerestory band), SM_PaintBoxWall/Ceiling/Floor/Lamp (a paint booth kit), SM_Pallet / SM_PalletCart / SM_PlasticBin / SM_Barrel, SM_ForkLift, SM_FloorDrainage, SM_ConcretePillar, SM_RoofFrame. This is the cheapest available density and it is 97% unused.

Evidence: Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:39; Content/Meshes

## 20. [high / density] aisle/row spacing — empty floor between rows

**State today: partial.** Weld and assembly are laid out as two parallel rows, which matches the mockup's "organised rows", but the row separation is implausibly large and reads as void from an isometric camera. Weld positions 1-9 sit at Y=-11300 and 10-18 at Y=-5700: 56 m apart with 1700 x 3200 cm cells and nothing between them. Assembly positions 1-12 at Y=5500, 13-24 at Y=11500: 60 m apart. Press is a single serpentine with no parallel row at all. Nothing occupies the mid-bay strip — no cross-conveyors, no stillage rows, no mezzanine, no marked walkway.

Evidence: Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterLayout.cpp:231; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterLayout.cpp:426; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterLayout.cpp:143; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterLayout.cpp:277

## 21. [high / density] coil racking, stillage racks and conveyor runs across all four shops

**State today: partial.** Coil racking exists only in the press bay, and only as reference-manifest instances (15 SM_LB_CoilSaddle, 15 SM_LB_MasterCoil, plus the press presentation's baked 6-coil store). Stillage racks appear as 2 authored panel-stillage meshes gated to 8 of 18 weld positions and 3 baked stillages at press dispatch. Conveyor runs are the Fab pack's SM_AssemblyLine01 laid station-to-station by the dev dressing (skipped entirely in Press), plus flat green route cubes in each presentation. The mockup's continuous conveyor spine, banked coil racking and rows of stillage racks between cells do not exist. SM_StorageShelvesBottom01 is the only racking mesh wired up, out of the four-piece SM_StorageShelves family in the pack.

Evidence: Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:46; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:762; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActor.cpp:974; Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:216; Content/LineBoss/Reference/RestoredShop/shop_manifest.json

## 22. [high / density] green painted floor zones per cell and walkway

**State today: partial.** A complete floor-paint system exists and is unused by the One Factory route. ULBFactoryFloorMarkingComponent provides AddFilledRectangle, AddRectangleOutline, AddDiagonalHatching and AddDashedLine over 8 semantics with fixed hex colours, including StorageFill 2D7D55 (green) and ServiceEnvelope F2C94C. Its only consumers are legacy/other-mode classes — LBFactoryBuildMachine, LBPressShopStorageZone, LBBodyWeldLineActor, LBECoatLineActor, LBFactoryAGVInfrastructure — none of which the One Factory path spawns. None of the four LBOneFactory*StarterPresentationActor classes include the header. What actually renders as floor paint today: 24 yellow 12 cm bay/spine boundary strips and one whole-bay tinted slab per department in the map shell, plus green route stripes (2F8A5F, 1.2 m wide) laid station-to-station by the dev dressing actor. So: green route lines yes, green per-cell zone pads with delineated walkways no.

Evidence: Source/LineBossCarFactory/LBFactoryFloorMarkingComponent.h:19; Source/LineBossCarFactory/LBFactoryFloorMarkingComponent.cpp:26; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:863; Scripts/create_one_factory_shell_v001.py:286; Scripts/create_one_factory_shell_v001.py:307; Source/LineBossCarFactory/LBPressShopStorageZone.cpp:350

## 23. [high / density] mezzanines and gantries

**State today: absent.** No mezzanine exists anywhere in the One Factory route. Overhead structure is limited to: the press presentation's baked high gantry rails and three crane bridges (inside the aggregate mesh, hidden at runtime), the reference manifest's 42 SM_LB_Crane_BridgeGirder_4500 and 20 SM_LB_Crane_Column_14300 in the press bay only, and the shell's open roof frame at Z=3000. Weld, paint and assembly have no overhead structure at all. The Fab pack's SM_IndustrialPlatform, SM_HeavyPlatform, SM_PlatformGrill, SM_PlatformRailing, SM_PlatformPillar, SM_FloorStairs, SM_Ladder and SM_HeavyArch are all present and all unused.

Evidence: Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:457; Content/LineBoss/Reference/RestoredShop/shop_manifest.json; Scripts/create_one_factory_shell_v001.py:262; Content/Meshes

## 24. [high / density] multiple parallel press cells in organised rows

**State today: absent.** The mockup shows several parallel press cells. The route commissions exactly one ConfigurablePressTrain station (7 press stages in a single 25 x 80 m north-south line) out of 7 press stations, and ValidateStarterLayout hard-rejects any layout that is not exactly 7 stations and 6 routes. The reference map does contain four trains (identity signs A/B/C/D in the manifest) and the handover records all four standing on the 2200 cm row grid — but those arrive as manifest instances with no station, no simulation and no HUD entry. There is no data path to commission a second press train.

Evidence: Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.cpp:273; Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.cpp:311; Content/LineBoss/Reference/RestoredShop/shop_manifest.json; Docs/OneFactory/SESSION_HANDOVER_2026-08-17.md:23

## 25. [high / density] shop content is spawned at runtime, not authored as actors in the editor

**State today: absent.** LB_MoorcrossWorks_OneFactory_v001.umap contains only the shell: floor slabs, per-department floor slabs, columns, cutaway walls, open roof frame, a 100 cm grid, 24 safety-line strips, lighting authority, nav bounds, player start, management camera, six datum TargetPoints, the bootstrap and one press build authority. No station, no machine, no presentation actor is saved in it. All 57 stations, all four presentations, the envelope walls, the dressing and the 2,804 manifest instances are spawned by ULBOneFactoryPlayerBuilderSubsystem and ALBOneFactoryPlayerController::EnsureSitePresentation on commission, and the GameMode explicitly asserts "ONEFACTORY GAME MODE MUST REMAIN SHELL-ONLY". This directly contradicts the owner's standing direction to author environment content as real actors placed and saved in the editor, and it means density cannot be art-directed by eye — only by editing C++ tables.

Evidence: Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap; Source/LineBossCarFactory/LBOneFactoryGameMode.cpp:84; Source/LineBossCarFactory/LBOneFactoryPlayerBuilderSubsystem.cpp:1401; Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:121

## 26. [high / hud] Nav icon row (factory, orders, chart, awards, settings)

**State today: partial.** Four text-label buttons exist — BUILD (74px), PRODUCTION (104px), ANALYTICS (94px), SETTINGS (86px) — all focusable, all delegate-wired, all with tooltips, and all covered by an automation test. But: (1) labels are 10pt text, not icons — the widget contains exactly one ConstructWidget<UImage> in the whole file (the stage thumbnail), and Content/LineBoss/UI contains nothing but the twelve production-flow textures, so there is no icon library to draw from at all; (2) there is no FACTORY/overview button even though OnFactoryDestinationClicked() exists and FACTORY is the first canonical destination ID — so the flow tray has no on-screen route back; (3) there is no trophy/awards destination, and no awards system exists anywhere (grep for achievement|award|trophy across Source returns zero files); (4) an in-source comment states the strip is 'intentionally bounded' to three pages plus Settings, so ASSETS/MAINTENANCE/RESEARCH keep routing IDs but have no button.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:499; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:470; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1269; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:56; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:703; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidgetTests.cpp:230

## 27. [high / hud] Per-card status label with count ("Waiting: 2")

**State today: partial.** A live state label exists beside the dot, colour-matched, fed from FLBFactoryUIProductionStageSnapshot::State — real strings such as 'READY', 'FULL', 'AWAITING BLANKS', 'CYCLING', defaulting to 'NOT INSTALLED'. The mockup's counted form is not achievable from the current projection: the stage snapshot carries only bInstalled/bRunning/bWaiting/bFaulted booleans and no integer. The counts do exist upstream — the subsystem formats '%d / %d blanks' and '%d / %d stillages' from Zone->GetOccupancy()/GetCapacity() — but only into the Detail string, which the card never shows (it goes to the tooltip and the detail panel description). Adding an int32 WaitingCount/Occupancy to FLBFactoryUIProductionStageSnapshot and rendering it on the card is the clean fix.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:740; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:991; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:150; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:461

## 28. [high / hud] Per-card throughput figure ("18.0/hr")

**State today: absent.** No throughput appears on any UMG card. FLBFactoryUIProductionStageSnapshot has no throughput member at all, and RefreshStageCard sets only state text, dot, image, art-status and border. The only throughput in the shell is one factory-wide figure in the detail panel. The maths already exists in the retired-looking Canvas HUD, which derives a per-group bottleneck rate as 3600/SlowestCycleSeconds from the authored NominalCycleSeconds of the configured route and draws it as '{0}/hr' on each group — so the correct approach is to lift that per-stage bottleneck calculation into the UI-state projection and render it on each card, then delete the Canvas strip.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:150; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:982; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:191; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:407

## 29. [high / hud] Right detail panel — buffer "Blank buffer: 8" with layers icon

**State today: absent.** There is no upstream-buffer readout. The detail panel's third and fourth rows are an order readout ('ORDER OUTPUT   %d / %d' or 'NO ACTIVE PRODUCTION ORDER') and a green UProgressBar of order completion — useful, but not the mockup's buffer figure. Occupancy data exists ('%d / %d blanks' from Zone->GetOccupancy()/GetCapacity()) but only surfaces as the Blank buffer stage's own description when that stage is itself selected; there is no cross-stage lookup that says 'the machine you selected is fed by Blank buffer, which holds 8'. Requires the buffer count on the stage snapshot plus an upstream-stage relation in RefreshDetailPanel.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:834; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1106; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:461

## 30. [high / hud] Right detail panel — throughput "14.2 panels/hr" with gauge icon

**State today: partial.** A throughput line exists but it is the wrong scope and has no icon. DetailThroughputLabel renders 'FACTORY GOOD OUTPUT   %.1f units/hr' from Management.ThroughputGoodUnitsPerHour — one factory-wide figure that does not change with the selected stage, so selecting Transfer press cannot show that machine's own rate. It is honestly gated: collapsed entirely unless HasTruthfulThroughput() (>0), on the stated principle that zero is indistinguishable from no sample, and that policy is unit-tested. Needs a per-stage throughput source (see the per-card throughput entry) plus a gauge icon.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:826; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1094; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:209; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidgetTests.cpp:113

## 31. [high / hud] Speed multiplier readout "1x"

**State today: absent.** No widget displays the current simulation rate. The data is available — FLBFactoryUIStateSnapshot::EffectiveSimulationRate is populated every refresh from WorldSettings->GetEffectiveTimeDilation() — and the retired Canvas strip did draw 'SIM %.1fx', but grepping EffectiveSimulationRate in LBManagementRootWidget.cpp returns nothing. The player therefore has no confirmation of what speed the line is running at. Cheap to add: one UTextBlock in the top strip bound to LastSnapshot.EffectiveSimulationRate in RefreshPresentation.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:168; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:201; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:992; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:940

## 32. [high / hud] Transport controls: pause / play / fast-forward

**State today: partial.** Three real focusable UButtons exist (Simulation_PAUSE 62px, Simulation_PLAY 54px, Simulation_FAST_FORWARD 50px), each delegate-wired to RequestSimulationRate(0.0 / 1.0 / 2.0) and routed through HandleModernSimulationRateRequested to ULBOneFactoryOperationsSubsystem::SetSimulationRate, which accepts 0-4x. An automation test asserts all three are visible, focusable and bound. Gaps: labels are the text 'PAUSE' / 'PLAY' / '2X' rather than transport glyphs (no icon assets); nothing indicates which rate is currently active (RefreshPresentation never touches SimulationRateButtons); and the handler returns early unless Operations->IsOneFactoryOperationsWorld(), so in the default LBGameMode press-shop map the buttons are visible but inert.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:554; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:580; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1282; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1611; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryOperationsSubsystem.cpp:529; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidgetTests.cpp:250

## 33. [high / hud] Two conflicting production-flow rows draw at once (OneFactory mode)

**State today: partial.** Under ALBOneFactoryGameMode (HUDClass = ALBOneFactoryProductionHUD) the Canvas flow strip and the UMG flow tray both render. The Canvas strip occupies the bottom 132*Scale px; the UMG tray is 344 design-px tall sitting 40 px off the bottom — so they overlap in the bottom ~92 px band, and the Canvas alert toasts are positioned at Height-132-14-34, i.e. inside the UMG tray. They also disagree on the model: the Canvas HUD shows seven coarse groups (Coil intake, Press, Panel stillages, Body weld, Paint, Assembly, Dispatch) while the UMG shell shows the mockup's six (Coil intake, Blank buffer, Transfer press, Panel stillages, Body weld, ED coat). One of the two must be retired; the Canvas one is the weaker but currently carries the only per-stage throughput maths.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryGameMode.cpp:72; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:271; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:317; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:55; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:609; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:47

## 34. [high / hud] UI icon and font asset library

**State today: absent.** This is the root cause behind most of the individual icon gaps and should be treated as one work item. Content/LineBoss/UI contains only the twelve production-flow thumbnails (v002 + v003) — no icon set, no glyph atlas. A recursive search for icon/font assets across all of Content finds only two unrelated press-station HMI meshes and zero font assets. All text uses FCoreStyle::GetDefaultFontStyle (engine Roboto), so there is no brand typeface either. Delivering the mockup's top bar needs a small authored icon set (hamburger, factory, clipboard, chart, trophy, gear, cash, bell, warning triangle, gauge, layers, chevron, transport glyphs) imported as UI textures.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:63; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:703

## 35. [high / hud] World-space alert toast with warning triangle

**State today: partial.** Nothing in the UMG shell draws a toast. The only toast is Canvas-drawn in the OneFactory HUD: up to three stacked 470x34 panels with a 3px yellow left stripe, text truncated to 78 characters, placed bottom-right immediately above the Canvas strip — i.e. screen-space, inside the region the UMG tray occupies, with no warning-triangle icon and no world anchoring. The alert text itself is truthful and generated from real coordinator reasons ('{Group} finished its cycle at {Station} and cannot move on'), which is close to the mockup's 'Panel stillages waiting for transfer press'. Notably, a complete world-projected implementation already exists but is compiled out: inside the `#if 0` block, DrawPersistentFactoryHUD projects TopAlert->MarkerWorldLocation to screen, draws a severity-coloured diamond, a leader line and a titled callout card that flips above/below. That is the code to port into UMG (a positioned canvas-slot widget driven by ProjectWorldLocationToScreen), plus a triangle icon.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:431; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:246; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1045; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:858; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:33

## 36. [high / hud] alert toast over the world

**State today: absent.** The mockup floats a warning-triangle toast ('Panel stillages waiting for transfer press.') over the 3D view. ULBManagementRootWidget has no toast widget at all — grepping 'toast' in the widget returns nothing; alerts appear only as a right-aligned 'n alerts' count in the top strip. A working toast renderer does exist in ALBOneFactoryProductionHUD::DrawAlertToast (newest-first, max three, yellow severity stripe) but that HUD is installed only by ALBOneFactoryGameMode, which no map or config references, so it never ships. All the data the toast needs (Title, Detail, Severity) is already on FLBFactoryUIAlertSnapshot.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:431; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryGameMode.cpp:72; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:27; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:601

## 37. [high / hud] placement feedback surface

**State today: absent.** Every placement path returns a rich OutReason string — prerequisites ('PLACE THE PREPARED-BLANK BUFFER FIRST'), refusals ('THE FOUR AUTHORED PRESS TRAINS A-D ARE ALREADY INSTALLED'), and successes listing automatic links and walkway tile counts. None of it reaches the player in the modern shell, and because bManagementVisible is cleared when placement starts the shell is not even on screen to show it. The player gets a ghost with no explanation of why it is red or what was built for them.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:1981; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:947; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2781

## 38. [high / loop] income per vehicle

**State today: partial.** Revenue is wired end-to-end but is a pressed-panel contract, not a vehicle sale. ULBFactoryManagementRuntimeSubsystem verifies each panel's lineage (correct order, model, panel type, Good disposition, delivered stillage, accepted by a weld line) before paying DefaultPanelRevenuePence = 25000 (£250) per panel and granting 5 research points. The code comments this explicitly: 'This is deliberately a pressed-panel delivery contract. It does not claim that a vehicle, weld body or painted body exists.' The mockup implies a finished CAIRNWELL 2040 is sold. Needs a vehicle-completion revenue event at end-of-line inspection / dispatch.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementRuntimeSubsystem.cpp:677; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementRuntimeSubsystem.cpp:683; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementRuntimeSubsystem.h:74

## 39. [high / loop] operating costs / running expenses

**State today: absent.** TryChargeOperatingCost exists with a full ledger category (ELBManagementLedgerCategory::OperatingCost) and OperatingSpendPence in the snapshot, but nothing ever calls it. No wages, energy, consumables, coil purchase cost or maintenance spend is charged during play (TryCompleteMaintenanceService is also uncalled outside tests). Combined with the missing machine prices, cash is monotonically increasing, so there is no pressure and no fail state.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.cpp:203; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:440; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:478

## 40. [high / loop] orders as contracts (offers, deadlines, penalties)

**State today: absent.** What exists is a self-issued work order: the player picks a model and panel type from hardcoded arrays (PreProductionVehicleModels, FuturePanelTypes) and a quantity 1-1000, then queues it. There is no contract offer list to choose from, no due date, no deadline pressure, no penalty for late or rejected delivery, no reputation, and no reason to prefer one order over another. The mockup's '0 / 16 issued' implies an externally-set target. QueuePanelBatch is the sole entry point.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:3289; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:3296; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBPlayerBuiltPressFlowController.h:199

## 41. [high / loop] progression / research unlocks

**State today: partial.** The clearest stub in the codebase: a complete API with zero consumers. TryUnlockResearch, TryPurchaseMachineUpgrade, HasResearchUnlock and GetMachineUpgradeLevel are implemented with idempotency, point accounting and a RequiredUnlockId prerequisite check, and GrantResearchPoints genuinely fires at 5 points per fulfilled order — but grepping all non-test .cpp files shows the only caller of HasResearchUnlock is TryPurchaseMachineUpgrade inside the same file. Nothing in the game unlocks or upgrades anything. The Research management page returns 0 actions, so there is no UI to spend points, and CanPlaceMachine never consults research, so no machine or capability is gated behind progression. Research points accumulate forever and can never be spent.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.cpp:256; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.cpp:283; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.cpp:293; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1917; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementRuntimeSubsystem.cpp:688; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:882

## 42. [high / other] clerestory daylight band

**State today: partial.** Geometry for the mockup's clerestory exists but emits and admits no light. ALBOneFactoryDevEnvelopeActor builds a 420 cm 'glazing band' as scaled /Engine/BasicShapes/Cube instances on /Engine/BasicShapes/BasicShapeMaterial tinted E8F0FA at roughness 0.2 - opaque, non-emissive, non-translucent - running unbroken over walls and portals just under the eaves. There is nothing behind it: the map contains 25 actors in total and not one DirectionalLight, SkyLight, SkyAtmosphere or fog actor, so no daylight source exists to come through a window even if the band were glazed. This also sits against the standing preference to author environment content as real assets in the editor rather than as runtime engine primitives.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:36; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:198; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:329; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:15; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap:1

## 43. [high / other] frozen exact-count contracts as the cost driver for any density increase

**State today: present.** Every department presentation validates its item list against a hard-coded total, per-batch counts and per-role counts, and rejects the layout if any differ — press 268 logical items with per-role and per-batch tables, weld 597, paint 119, assembly 95 — and the automation tests assert the same literals. Adding a single prop anywhere therefore requires editing the builder, the total constant, the per-batch table, the per-role table and the tests in one commit. The handover records this happening three times for weld alone (469 to 489 to 597). This is why density has grown by re-freezing rather than by iterating, and it is the main reason paint and assembly have stayed at 119 and 95.

Evidence: Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:1169; Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:1231; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActor.cpp:1156; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActor.cpp:706; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActorTests.cpp:30; Docs/OneFactory/SESSION_HANDOVER_2026-08-17.md:28

## 44. [high / other] press native-only provenance allowlist forbids the authored shop content

**State today: present.** MakeNativeOnlyProfile restricts press presentation assets to /Script/LineBossCarFactory., /Engine/BasicShapes/, /Engine/EngineMaterials/ and /Game/LineBoss/Factory/OneFactory/v001/Native/Press/, and lists /Candidates/, /Runtime/PressShop/ and /Stations/Press/ as ForbiddenSourceTokens. ValidateNativeReference and ValidateNativePresentationReferences enforce it, and ValidateStarterPair re-checks it on every commission. That means the press presentation is structurally barred from referencing the authored press-shop kits, the IndustrialKit or the Fab pack — which is why the density that exists arrives through two side channels instead (a baked aggregate inside the allowed root, and a dev manifest actor outside the contract). Raising press density in-contract requires either widening this allowlist or continuing to bake.

Evidence: Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.cpp:474; Source/LineBossCarFactory/LBOneFactoryPressStarterLayout.cpp:487; Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:1084

## 45. [high / other] the playable light rig only exists as a transient runtime spawn

**State today: partial.** The lighting that actually makes the shop readable is not in the map - it is bolted on by ULBOneFactoryDevFactory::EnsureDevLighting, which the player controller calls once during EnsureSitePresentation with intensity 9.0. It spawns a movable DirectionalLight at -48 deg pitch / 35 deg yaw at 5000 K, then a per-department point-light grid (about one lamp per 18 m bay, clamped 2-12 per axis, at Z 1400, intensity 68000, attenuation max(SizeX,SizeY)/5 + 3000, with only every other row and column casting shadows), then a SkyLight at Z 8000 with SLS_CapturedScene and an immediate RecaptureSky(). All of it is tagged LB.OneFactory.DevLighting, guarded so it builds at most once, and never saved - so the map on disk stays dark and every session re-derives its lighting from the live route. The runtime RecaptureSky is the exact call LBGameMode warns against: 'forcing a recapture after the shell runtime pass can trigger a D3D12 device loss before the first playable frame on affected PCs.'

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:210; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:436; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:462; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:527; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:576; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBGameMode.cpp:544

## 46. [medium / camera] authored management overview camera in the map is unreferenced

**State today: partial.** The map already contains the mockup's viewpoint as an authored actor and no code uses it. CameraActor_0, labelled LB_OF_ManagementCamera_Overview_v001 and tagged LB.OneFactory.ManagementView.Overview.v001, sits at (0, -43000, 36000) with quaternion (-0.2415, 0.2415, 0.6646, 0.6646) - yaw 90, pitch -39.9 - i.e. 360 m up, 560 m out, looking down into the site at 40 degrees. Grepping the whole module for ManagementView returns only ALBControlRoomPawn::EnterManagementView, which is unrelated (it spawns a management pawn in the legacy control-room maps). The same is true of the map's two authored cutaway batches, LB_OF_ENV_HISM_CutawayWalls_v001 and LB_OF_ENV_HISM_OpenRoofFrame_v001, both tagged LB.OneFactory.Environment.ManagementCutaway: no source file mentions that tag, so the authored cutaway intent drives nothing.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap:1; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomPawn.cpp:252

## 47. [medium / camera] click-a-flow-card-to-fly-there

**State today: partial.** The mockup's selected 'Transfer press' card implies selecting a card moves the camera, and that wiring exists but is aimed at the wrong actors. ULBFactoryUIStateSubsystem already publishes exactly the mockup's six stages (COIL_INTAKE, BLANK_BUFFER, TRANSFER_PRESS, PANEL_STILLAGES, BODY_WELD, ED_COAT), and ALBControlRoomHUD calls ManagementPawn->SelectFactoryActor(Stage.TargetActor, /*bFocus*/ true) when a card is confirmed, which routes through FocusFactoryActor -> FocusWorldTarget -> a smoothed RInterpTo/VInterpTo transition at speed 5.5. But Stage.TargetActor is only ever set from ALBFactoryBuildMachine / ALBPressShopStorageZone / ALBPressTrainAStation iterators, none of which exist on the OneFactory map, so bInstalled stays false and the click starts a legacy placement flow instead of flying the camera. JumpToTopFactoryAlert() (which would serve the mockup's alert toast) has the same dependency.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:218; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:295; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2753; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1910; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1972; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1991

## 48. [medium / camera] management camera pawn (pan / rotate / zoom)

**State today: present.** A real overhead management camera exists and is the map's default pawn - this is NOT a missing feature. ALBOneFactoryGameMode sets DefaultPawnClass = ALBManagementPawn. The pawn is a scene-root Pivot + USpringArmComponent (TargetArmLength 11000 cm, relative rotation -35 deg pitch, bDoCollisionTest false) + UCameraComponent (FieldOfView 48). Input is fully bound: LB_MoveForward/LB_MoveRight (W/A/S/D and left stick) pan the pivot at 2600 cm/s in yaw-only space, LB_Rotate (Q/E) orbits at 48 deg/s, LB_Zoom (mouse wheel, gamepad triggers) drives DesiredZoomDistance which FInterpTo's the arm at speed 10, LB_CameraReset (Home / gamepad B) resets. So pan, yaw-orbit and zoom all exist and are wired through Config/DefaultInput.ini. What it lacks is listed in the rows below (no pitch, capped zoom, no mouse camera, dead framing helpers, and it is not the view target after commissioning).

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryGameMode.cpp:71; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:930; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:943; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1131; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1046; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1091

## 49. [medium / camera] mouse-driven camera (drag-pan, edge pan, drag-orbit)

**State today: absent.** A management game of this kind is normally driven with the mouse. Nothing here is: the only camera inputs are keyboard/gamepad (W/A/S/D, Q/E, wheel, Home). LB_PrimaryClick (left mouse) is bound to InteractUnderCursor / EndPointerInteraction, which is placement confirm, storage drag-size, HUD hit testing, widget-interaction press and world selection - there is no free mouse button left for camera drag, and no edge-of-screen pan or middle-drag orbit exists. Zoom is also cursor-agnostic: it changes TargetArmLength only, so the view does not zoom toward whatever the mouse is over.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultInput.ini:36; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultInput.ini:3; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1139; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1187; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1056

## 50. [medium / camera] opening frame is not a shop overview

**State today: partial.** The map's PlayerStart (LB_OF_PlayerStart_Management_v001) sits at (-28000, -13500, 200) with identity rotation, i.e. yaw 0, and the game mode restarts the pawn there. With the constructor's 11000 cm arm at -35 deg and 48 deg FOV that puts the camera about 65 m up at the far south-west corner of the site, looking axis-aligned along +X across roughly 100 m of floor, while the four bays run from X -14500 to +16500. No focus call runs at spawn - the pawn constructor's -45 yaw (its only three-quarter hint) is overwritten by the PlayerStart rotation, and the first real framing the player gets is the dev camera on the B press. The dev factory header records the same symptom: 'a player standing at the Management start 280 m away sees almost nothing.'

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:954; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:935; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.h:120; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content/LineBoss/Factory/OneFactory/v001/Maps/LB_MoorcrossWorks_OneFactory_v001.umap:1

## 51. [medium / camera] player-facing framing targets the whole 610 m route, not one shop

**State today: partial.** The mockup frames ONE shop. The only framing the player can trigger is FrameProductionLine(this, TEXT("All")), which accumulates all 57 configured station transforms across all four departments and solves a distance from the footprint diagonal - so the player always gets the whole-campus shot with each shop a small cluster. Per-department framing exists and works well (Press, Body, Paint, Assembly, plus a WIP mode that frames the first live unit at 1500 cm, plus the Dept@scale~pitch close-up syntax), but it is reachable only from the console command LB.OneFactory.View or from the LB.OneFactory.Tour capture actor - no player input, HUD button or nav icon calls it with a department.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:224; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:628; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:704; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:1324

## 52. [medium / camera] roof cutaway mechanism

**State today: partial.** The cutaway is real, player-facing and correctly engineered, but removes less than the mockup implies. ULBOneFactoryDevFactory::SetRoofHidden is called from the shipped player path (EnsureSitePresentation, hidden=true above 900 cm) and again automatically from FrameProductionLine, which toggles it on camera eye height (Eye.Z > 900) so a floor-level close-up puts the roof back. State is per-UWorld (so PIE/editor/reloaded worlds cannot corrupt each other), exactly reversible via the stored component set, exposed through IsRoofHidden, and re-applied by the envelope after a rebuild; LB.OneFactory.Roof [hidden] [aboveCm] is the manual console form. Limits: it only hides UStaticMeshComponents whose ENTIRE bounds sit above AboveZCm, and it explicitly exempts four actor families (WIPPresentation, DevEnvelope, DevStationDressing, DevRestoredShop). In practice the only things removed are the four flat cube roof decks the envelope spawns as untagged StaticMeshActors and the map's LB_OF_ENV_HISM_OpenRoofFrame_v001 batch. The envelope's 2200 cm full-height walls start at Z 0 and are therefore never hidden, so a high-angle camera still looks at the back faces of near walls; and because the test is per-component, any mixed instance batch spanning floor-to-roof cannot be partially cut.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:196; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:755; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:821; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:862; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:888; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:348

## 53. [medium / camera] two incompatible lens languages (48 deg pawn vs 78 deg dev camera)

**State today: partial.** FrameProductionLine hardcodes ManagementFovDegrees = 78.0, uses it both to solve the fit distance and to set the spawned lens, and defaults the pitch to 34 deg (overridable per shot with the Dept@scale~pitch syntax). The management pawn uses FieldOfView 48. 78 degrees is a wide-angle look with strong perspective divergence across a 300 m hall - the opposite of the mockup's near-isometric, near-parallel read - and it means the pose the player is handed after pressing B does not match the pose the pawn would produce if control were restored. The dev lens also pins AutoExposureBias to -0.50 with PostProcessBlendWeight 1.0, so the camera itself carries a grade the pawn's camera does not.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:711; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:782; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.cpp:610; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:943

## 54. [medium / density] IndustrialKit dressing props not placed in the route

**State today: partial.** Content/LineBoss/IndustrialKit holds 105 authored static meshes; 28 are referenced, 77 are not. Most of the 77 are superseded versions (InboundCoilDelivery Candidate_v001..v005 of the same 7-8 modules, five MasterCoil revisions), so the genuine unused-but-current set is small: the Barrier_v002 family (SM_LB_GuardPanel_1000x2400_v002, SM_LB_GuardPanel_1400x2400_v002, SM_LB_GuardInterlockBox_v002, SM_LB_InterlockedGate_1400x2400_v002, SM_LB_InterlockedSlidingGate_2400x2400_v002) and SM_LB_Crane_CHook_v001. Separately, the PressShop/FrontEndDressing family (E-stop pedestal, floor trench grate, inspection mast, packaging prep bench, recovery bin, safety bollard, service cabinet) reaches the press bay only through the reference manifest — nothing places it in weld, paint or assembly, where the mockup wants exactly those service cabinets and bollards.

Evidence: Content/LineBoss/IndustrialKit/Safety/Barrier_v002; Content/LineBoss/IndustrialKit/PressShop/FrontEndDressing; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:39

## 55. [medium / density] engine-primitive content still carrying visual load

**State today: partial.** 418 of the 2,804 reference manifest entries are /Engine/BasicShapes (327 Cube, 63 Cylinder, 28 Plane) — 15% of press-bay geometry is untextured primitives. Beyond that: the assembly presentation's status cubes and route cubes, the weld presentation's last 3 of 29 batches (FloorRouteCube, RobotRoleCube, StatusCube), the paint presentation's cube batches, the dev envelope's entire walls/dado/ceiling/clerestory built from scaled cubes with hex-tinted BasicShapeMaterial, and the dressing's department aprons and green route stripes. The clerestory band the mockup calls for is currently a scaled cube tinted E8F0FA, with SM_LargeWindowFramed sitting unused in the pack.

Evidence: Content/LineBoss/Reference/RestoredShop/shop_manifest.json; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActor.cpp:105; Source/LineBossCarFactory/LBOneFactoryAssemblyStarterPresentationActor.cpp:31; Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:33; Source/LineBossCarFactory/LBOneFactoryDevEnvelopeActor.cpp:118

## 56. [medium / density] press station content is one baked aggregate mesh, and it is hidden at runtime

**State today: present.** The press presentation no longer instances anything: it stages a single 14 MB static mesh (SM_OneFactoryDetailedPressPresentation_v001, 306 material slots over 13 owned PBR materials) into one of two double-buffered components, and asserts ExpectedVisualBatchCount 1 / ExpectedRenderedAggregateCount 1. The 268 cube/cylinder "logical items" the BuildInboundReceiving/BuildCoilStore/BuildPressTrain functions still generate are contract records for selection and validation only, not geometry. On top of that, EnsureSitePresentation hides the whole press presentation actor at runtime, so what the player actually sees in the press bay is the 2,804-instance manifest plus the dev dressing. Any attempt to raise press density inside the presentation contract means re-exporting that 14 MB aggregate, not adding instances.

Evidence: Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:11; Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:919; Source/LineBossCarFactory/LBOneFactoryPressStarterPresentationActor.cpp:1145; Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:202; Content/LineBoss/Factory/OneFactory/v001/Native/Press/DetailedPresentation_v001/SM_OneFactoryDetailedPressPresentation_v001.uasset

## 57. [medium / density] reference manifest is lossy and press-anchored

**State today: partial.** The manifest captured 2,804 of the reference map's 4,092 actors (68%) — mesh transforms and material overrides only, no lights, no volumes, no non-mesh actors. The loader synthesises point lights for the 28 SM_Lamp01 entries as a workaround. It also anchors the entire payload to the single OF_PRESS_TRAIN_001 station transform with a fixed +90 degree yaw and a hard-coded (9.25, 2367.5, 0) datum offset, and returns failure if that station is absent — so the manifest can only ever dress the press bay, and it silently skips any mesh path that fails to load (MissingMeshes is counted but not fatal).

Evidence: Content/LineBoss/Reference/RestoredShop/shop_manifest.json; Source/LineBossCarFactory/LBOneFactoryDevRestoredShopActor.cpp:64; Source/LineBossCarFactory/LBOneFactoryDevRestoredShopActor.cpp:110; Source/LineBossCarFactory/LBOneFactoryDevRestoredShopActor.cpp:244; Source/LineBossCarFactory/LBOneFactoryDevRestoredShopActor.cpp:171

## 58. [medium / density] service cabinets and HMI/control furniture outside press

**State today: partial.** Weld does this reasonably: an HMI pedestal at every one of 18 stations, guard panel at every station, guard gate on odd positions, electrical cabinet at 7 positions, utility pedestal at 15, extraction pedestal at 12, from the authored BodyShopSupportKitNative_v002. Paint and assembly get only the dev dressing's common branch — one SM_AssemblyLineControl01 cabinet plus a fence run per station — and press is skipped by that branch entirely on the grounds that the detailed train carries its own. So the weld pattern is the working template and it has not been applied to paint or assembly.

Evidence: Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActor.cpp:943; Source/LineBossCarFactory/LBOneFactoryBodyWeldStarterPresentationActor.cpp:955; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:703; Source/LineBossCarFactory/LBOneFactoryDevStationDressingActor.cpp:716

## 59. [medium / hud] "1x" speed readout

**State today: absent.** The mockup shows a speed multiplier readout beside the transport controls. The top strip builds three text buttons labelled PAUSE / PLAY / 2X into SimulationRateButtons but constructs no TextBlock for the current rate — there is no member equivalent to CashLabel/OrderLabel/AlertLabel for simulation speed. The value is available on the snapshot as EffectiveSimulationRate (and the dead Canvas path already formatted it as 'SIM %.1fx'), so this is purely a missing widget plus the rate-source fix above.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:583; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:314; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:999

## 60. [medium / hud] Alert bell with count "2 alerts"

**State today: partial.** The count and its pluralisation are correct and live: AlertLabel renders '%d alert(s)' from LastSnapshot.Alerts.Num() in amber, falling back to 'No alerts' in muted grey, right-justified in a 186x52 block. Missing the bell icon (no icon assets), missing any chip/pill treatment, and the label is a passive UTextBlock — not a button, so there is no click-to-jump-to-alert. Severity is not reflected either: the colour is amber for any non-empty list, even though FLBFactoryUIAlertSnapshot carries Information/Warning/Critical.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:597; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:963; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:27

## 61. [medium / hud] Cash readout "£2.50m"

**State today: partial.** The value and format are exactly right: FormatMoney() converts pence and emits '£%.2fm' above a million, '£%.1fk' above a thousand, else '£%.0f' — so a £2.5m balance renders literally as '£2.50m'. Wired live to LastSnapshot.Management.CashBalancePence in a 108x52 block. Missing only the coin/cash icon the mockup places beside it (no icon assets exist), and there is no styling as a chip.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:130; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:540; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:960; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:88

## 62. [medium / hud] Company mark + "CAIRNWELL AUTOMOTIVE"

**State today: partial.** A text wordmark exists — "CAIRNWELL" at size 18 bold with "AUTOMOTIVE SYSTEMS" at size 8 in green beneath it, inside a 246x52 brand block, tooltip 'Cairnwell Automotive'. No logo mark: BrandLogoImage is declared as a UPROPERTY but is never constructed anywhere (zero ConstructWidget<UImage> calls for it), and an in-source comment says the supplied print logo was deliberately dropped as 'an unreadable smudge on a dark operations shell'. The logo texture does exist on disk and GetBrandLogoPath() still resolves it. Separately, FactoryNameLabel is declared and read in RefreshPresentation() (guarded by `if (FactoryNameLabel && ...)`) but is never constructed either — so the player's own factory name from ULBFactoryBrandSubsystem never reaches the top bar; the strip is hardcoded English text.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:448; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:459; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:296; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:293; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:942; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:191

## 63. [medium / hud] Green flow arrows between cards

**State today: partial.** Connectors exist and are state-driven, but they are flat lines, not arrows: a 24x2 px SizeBox holding a UBorder with a 1px-radius rounded brush, vertically centred between cards. The colour logic is good and unit-tested — Green when both adjacent stages are installed (ShouldHighlightStageConnector), Red when either is faulted, Stroke grey when the link is only planned — with an explanatory tooltip on each ('CONNECTED' / 'PLANNED - BOTH STAGES ARE NOT YET INSTALLED'). What is missing is the arrowhead and any sense of direction or flow animation; at 2px they will barely register at the mockup's framing.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:761; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1037; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:202

## 64. [medium / hud] Non-16:9 layout — whole shell letterboxes

**State today: partial.** The shell is one 1920x1080 SizeBox inside a UScaleBox set to ScaleToFit / StretchDirection::Both, anchored full-screen. That gives exact, tested 2/3 and 1.0 scales at 720p and 1080p and keeps every hit target in proportion, but on any aspect other than 16:9 the entire HUD is uniformly letterboxed rather than the top bar and bottom tray spanning the viewport edges — so on ultrawide the bars will float with dead margins. UpdateResponsiveLayout() is effectively a no-op (body is comments only). Fix by keeping the ScaleBox for the flow tray/detail content but anchoring the top strip and tray backgrounds to the real viewport.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:325; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1201; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:141

## 65. [medium / hud] Primary green CTA "Place next machine" with chevron

**State today: partial.** A real primary action button exists in the right position with the right treatment: 310x52, GreenDark fill with a Green outline hovering to full Green, always enabled, with a state-dependent tooltip, and explicit up/down focus navigation linking it to the selected card. It is fully wired: OnClicked -> ActivateSelectedStage -> OnStageActionRequested -> HandleModernProductionStageAction -> ActivateProductionFlowPrimaryAction, which either focuses the live actor or starts machine/storage placement through the existing builder subsystem. Divergences from the mockup: the label is 'BUILD THIS STAGE' (or 'FOCUS LIVE ASSET' when installed) rather than 'Place next machine', and there is no chevron glyph. Also note it sets bManagementVisible = false on success, dismissing the HUD.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:845; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1121; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1169; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:1579; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2729

## 66. [medium / hud] Top-bar typography scale and chip styling

**State today: partial.** The top strip is currently under-scaled against the mockup: destination labels are 10pt and simulation-rate labels 9pt inside a 1920x1080 design canvas, and the navigation buttons use a deliberately invisible resting style (fully transparent normal brush, revealed only on hover/focus), so at the mockup's framing the nav row will read as faint small text rather than a row of legible controls. The order (14pt), cash (16pt) and alert (14pt) blocks are plain text in fixed SizeBoxes with no pill/chip backgrounds. Purely a styling pass over BuildTopCommandStrip.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:490; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:571; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:95; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:534

## 67. [medium / hud] Vehicle model badge pill "CAIRNWELL 2040"

**State today: partial.** The model name is shown, but not as a separate badge pill: it is concatenated into a single OrderLabel text block with the issued counter — default literal 'CAIRNWELL 2040   0 / 0 issued', live form '%s   %d / %d issued' with underscores replaced by spaces from Order.VehicleModelId. Two consequences: there is no pill background/border, and when there is no active order the whole block collapses to 'NO ACTIVE ORDER', so the model identity disappears entirely. The canonical model ID CAIRNWELL_2040 exists in gameplay (LBBodyWeldLineActor.h:88), so the data is real.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:530; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:949; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBBodyWeldLineActor.h:88

## 68. [medium / hud] top-bar nav icon row and hamburger

**State today: partial.** The mockup shows a hamburger plus five nav icons (factory, orders, chart, awards, settings). The shell declares seven canonical destinations — FACTORY, BUILD, ORDERS, ASSETS, MAINTENANCE, RESEARCH, ANALYTICS (ManagementDestinationCount = 7) — but builds only four buttons, and as 10pt text labels rather than icons: BUILD, PRODUCTION, ANALYTICS, SETTINGS. So FACTORY, ASSETS, MAINTENANCE and RESEARCH have no clickable entry in the modern strip and are reachable only by keyboard page-cycling (LB_ManagementNextPage). There is no hamburger and no trophy/awards destination anywhere.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:56; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:499; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:141; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1143

## 69. [medium / loop] automatic systems on placement (auto-connect, walkways, AGV route)

**State today: present.** Substantial player-facing automation that the UI currently never mentions — worth surfacing as a feature. On every PlaceMachine: ULBFactoryConnectionSubsystem::AutoConnectNewMachine wires the new machine to the nearest compatible upstream port with deterministic distance-then-PortId tie-breaking (weld and ED lines get bespoke nearest-handoff logic); CreateAutomaticServiceWalkways lays pedestrian tiles along each new link offset 300 cm to clear the 230 cm AGV lane and 180 cm conveyor; and placing a CoilWeighInspectionCell triggers CreateAutomaticInboundAGVRoute, which builds a readable single-corner Manhattan route from the inbound dock in 500 cm tiles, splitting a collinear run at its midpoint so the AGV never gets a zero-length leg, tagging each tile LB.FactoryBuilder.AutomaticAGVRoute and MarkAutomaticallyGenerated. Placement is transactional — FailPlacement unwinds links, ports and the actor. The success string already reports 'PLACED x WITH n AUTOMATIC LINK(S); ...; n SERVICE WALKWAY TILES' but nothing displays it.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:1948; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:1971; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:2050; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:2095; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryMachineBuilderSubsystem.cpp:1845; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryConnectionSubsystem.cpp:138

## 70. [medium / loop] save / load

**State today: partial.** The mechanism is real and complete. FLBPressShopSaveState persists the full FLBFactoryManagementSaveState (cash, ledger, research, upgrades, quality, maintenance, analytics) alongside PlayerBuiltMachines, PlayerBuiltBodyWeldLines, PlayerBuiltECoatLines, PlayerBuiltAGVInfrastructure, PlayerStorageZones and the inbound coil AGV, with per-set validation on restore; ALBPressShopCampaignController::SaveCampaignToSlot / LoadCampaignFromSlot drive it and the Analytics page exposes both as player actions. What is missing is lifecycle: no autosave, no save-on-quit, no named slots or save-browser UI, and no new-game/continue front end — one hardcoded CampaignSlotName. Note ULBOneFactorySaveGame deliberately excludes management state ('no inheritance or migration path to campaign saves'), so the OneFactory map cannot persist an economy.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBPressShopSaveGame.h:69; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBPressShopSaveGame.h:118; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBPressShopCampaignController.cpp:1733; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:3257; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactorySaveGame.h:56

## 71. [medium / other] authored asset library — what raw material actually exists

**State today: present.** 8,957 SM_ uassets under Content/LineBoss plus 785 in the Fab pack. Kit-by-kit usage: WeldShop 30 of 36 used (the 6 unused are the superseded BodyShopUnderbodySlice robot); PaintShop 29 of 35 used (6 unused are v001 blockout modules and access stairs); AssemblyShop 8 of 8 used; IndustrialKit 28 of 105 used, remainder mostly superseded versions; Fab pack 21 of 785 used. The bulk of the 8,957 is per-part GLB fragment libraries — 3,150 under Shared/SupportRobots/LB_CR01, 2,297 under Candidates/PressTrains/TrainA, 1,372 under Robots/Maintenance/MR01, 354 under Stations/Press/PR004 — component parts of assembled machines, not placeable props. The honest conclusion: the authored department kits are essentially exhausted, and the real reserve of placeable density is the 764 unused Fab pack meshes.

Evidence: Content/LineBoss; Content/Meshes; Content/LineBoss/Candidates/AssemblyShop/AssemblyLineNativeKit_v001; Content/LineBoss/Candidates/PaintShop/PaintLineNativeKit_v001; Content/LineBoss/Candidates/WeldShop/BodyShopSupportKitNative_v002

## 72. [medium / other] the whole presentation path runs through a class documented as developer-only

**State today: partial.** ULBOneFactoryDevFactory's own header describes it as 'Developer-only orchestration' whose purpose is to exercise a loop 'only ever exercised by synthetic-world automation'. It is a plain UBlueprintFunctionLibrary with no UE_BUILD_SHIPPING guard, and the shipped ALBOneFactoryPlayerController drives four of its functions from a single keypress: BuildAndCommissionWholeFactory, SetRoofHidden, EnsureDevLighting and FrameProductionLine. So in a packaged Shipping build the player's camera, roof cutaway and lighting are all provided by dev tooling, and the presentation has no owner that survives being told 'this is developer-only'. Consolidating the roof rule, the light rig and the framing solver into player-facing systems (or into saved map content) is the structural change behind several rows above.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryDevFactoryCommands.h:49; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:100; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:196; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:210; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryPlayerController.cpp:224

## 73. [low / camera] camera feel: no pan bounds, no pan/orbit smoothing

**State today: partial.** Zoom is smoothed (FInterpTo at speed 10) and explicit focus moves are smoothed (VInterpTo/RInterpTo at 5.5), but player-driven pan and orbit are raw: Tick applies AddActorWorldOffset at 2600 cm/s and AddActorWorldRotation at 48 deg/s directly, with no acceleration, no spring-arm camera lag (bEnableCameraLag is never set anywhere in the module) and no clamp to the site. Because the pivot is unbounded, holding W walks the camera off the 610 m site into empty space with nothing to look at and no way back except Home - which, per the framing row above, resolves to a hardcoded (0,0,0) pose on this map.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1091; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1056; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1975; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:939

## 74. [low / hud] "Production flow" panel with horizontal card chain

**State today: present.** Structurally complete and matching the mockup. A 344-px-tall rounded tray anchored to the bottom with 32px side margins and a 40px bottom margin, titled 'Production flow' at 24pt bold, containing a horizontal StageRow of six 210x258 cards interleaved with five connectors, then a divider and the detail column. The six stages are exactly the mockup's chain — COIL_INTAKE, BLANK_BUFFER, TRANSFER_PRESS, PANEL_STILLAGES, BODY_WELD, ED_COAT with display names 'Coil intake', 'Blank buffer', 'Transfer press', 'Panel stillages', 'Body weld', 'ED coat' — and an automation test locks that contract. Each card is a real UButton with DownAndUp click/press methods and a per-stage accessibility tooltip.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:607; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:655; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:47; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidgetTests.cpp:49; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1030

## 75. [low / hud] Hamburger menu button

**State today: absent.** No hamburger control of any kind. A case-insensitive grep for 'hamburger' or 'menu icon' across all .cpp/.h in Source returns nothing, and BuildTopCommandStrip constructs only the brand block, four text destination buttons, order/cash blocks, a spacer, three rate buttons and the alert label.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:427

## 76. [low / hud] Localisation of the UMG shell

**State today: absent.** Worth recording because it will be cheaper to fix now than later. Every string in the UMG shell is a raw FString::Printf or TEXT() literal with no LOCTEXT namespace — brand wordmark, nav labels, 'Production flow', stage names, 'NOT INSTALLED', 'ART IMPORT PENDING', 'BUILD THIS STAGE', 'No alerts', money formatting with a hardcoded £. By contrast the Canvas HUD it replaced was properly wrapped in LOCTEXT with plural forms. The project's own status doc already flags 'Current HUD strings are hard-coded English'.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:109; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:130; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBOneFactoryProductionHUD.cpp:40; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Docs/ReleaseGate/CURRENT_GAMEPLAY_STATUS.md:74

## 77. [low / hud] Order counter "0 / 16 issued"

**State today: present.** Live and truthful, in the exact mockup wording. RefreshPresentation() formats '%d / %d issued' from LastSnapshot.Order.IssuedQuantity and RequestedQuantity, which are projections of the real order authority (FLBFactoryUIOrderSnapshot). Only shortfall is that it shares one text block with the model badge rather than being its own chip, and it vanishes with 'NO ACTIVE ORDER' when no order is live.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:954; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:21

## 78. [low / hud] Per-card coloured status dot

**State today: present.** Implemented as a 10x10 UBorder with a 5px-radius rounded brush in a fixed SizeBox, leading the state row with 7px right padding and centre vertical alignment. Its colour is recomputed each refresh through the same precedence as the label — Red if faulted, Amber if waiting, Green if running, OffWhite if installed, Muted otherwise. Deliberately Collapsed unless the stage is installed, gated by the pure, unit-tested predicate ShouldShowStageStatusDot(). Set HitTestInvisible so it never steals the card's click.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:727; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:996; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:196; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:986

## 79. [low / hud] Per-card rendered 3D machine thumbnail

**State today: present.** This — usually the hardest HUD item — is already done, as baked renders rather than live capture. Each card holds a UImage with a 186x118 desired size, sourced from a strict soft path /Game/LineBoss/UI/ProductionFlow/v003/T_LB_UI_PF_<Key>_v003. All six .uasset files exist on disk, are 384x240, and an automation test loads each one and asserts its imported size. They are genuine 3D renders of the authored machines, not icons: the provenance table classifies them as textured Meshy/Blender presentation renders of the coil handler, destack feed, transfer-press train, stillage stack, weld fixture and ED tanks, hash-locked to the source .blend authorities. A verified render strip confirms the visual quality is good, with the caveat that the ED coat card is a three-panel montage rather than one assembled line, and the Body weld card shows a fixture plus skid plus underbody, explicitly not a complete cell. Remaining limitation: they are static PNGs, so they cannot reflect the player's chosen livery, upgrades or actual placed configuration.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:703; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:175; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1005; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidgetTests.cpp:283; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/SourceAssets/Candidate/UI/ProductionFlowThumbnails_v003/TRUTHFULNESS_TABLE.md:5; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Saved/Audits/UIUX/ProductionFlowThumbnails_v003/validation_v003.json:1

## 80. [low / hud] Render-target / live thumbnail capture capability

**State today: absent.** There is no UI thumbnail-capture path. The only USceneCaptureComponent2D in the entire project is ALBControlRoomCCTVFeed, which renders the world to a UTextureRenderTarget2D and applies it to an in-world UStaticMeshComponent display surface via a MID — it is factory CCTV geometry, not a UI brush source. ALBControlRoomHUD::ShowCCTVFeed()/Feed still accept a render target, but the code that composited it was in the retired `#if 0` Canvas block, so nothing draws it now. So if live per-machine thumbnails (reflecting livery/upgrades) are ever wanted, that capture-to-Slate-brush pipeline must be built from scratch; the current static v003 textures are the practical answer and are good enough.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomCCTVFeed.h:59; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomCCTVFeed.h:37; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.h:101; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:858

## 81. [low / hud] Right detail panel — title

**State today: present.** A 354x258 detail column sits at the right end of the flow tray behind a 1px divider, headed by DetailTitleLabel at 22pt bold in brand green, set from the selected stage's DisplayName and recoloured by state, with a 'STAGE %02d / 06  |  <STATE>' subhead and a wrapped description line beneath. Note this is the right-hand column of the bottom tray rather than a full-height right-side panel; whether that diverges from the mockup depends on reading of the image, but it is the same visual role and position.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:782; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:810; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1082

## 82. [low / hud] Selected-card green outline

**State today: present.** Matches the mockup, including its default selection. The selected card's border brush is rebuilt with a 2px Green outline over a GreenDark fill at 30% opacity (unselected: 1px Stroke over transparent). SelectedStageIndex defaults to 2 — Transfer press — exactly the mockup's selected card, and the HUD's own SelectedProductionFlowStage also defaults to 2 and is pushed into the widget on activation. Selection is driven by pointer clicks, by keyboard/gamepad left/right (arrows, A/D, D-pad, left stick) with keyboard focus following, and is deliberately separate from activation so clicking a card never starts placement.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1019; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:363; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.h:248; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:1142; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:276; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:152

## 83. [low / hud] flow-card 3D thumbnails

**State today: present.** Fully satisfied. All six rendered thumbnails exist on disk at the strict v003 path the widget resolves — T_LB_UI_PF_{CoilIntake,BlankBuffer,TransferPress,PanelStillages,BodyWeld,EDCoat}_v003 under Content/LineBoss/UI/ProductionFlow/v003 — matching the mockup's six cards one-for-one, with a v002 set retained. GetStageThumbnailPath builds the soft reference, ResolveThumbnail loads it, HasCompleteThumbnailSet verifies the set and ReloadStageThumbnails re-checks after an art import. The Cairnwell brand logo for the top-left mark also resolves.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:175; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:191; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:306; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Content/LineBoss/UI/ProductionFlow/v003/T_LB_UI_PF_TransferPress_v003.uasset

## 84. [low / hud] vehicle model badge pill

**State today: partial.** The mockup has a distinct pill for the vehicle model ('CAIRNWELL 2040') separate from the order counter. The implementation merges both into one 236x52 centred TextBlock ('%s   %d / %d issued'), so there is no separately styleable badge and the model name vanishes entirely when no order is active. Cosmetic split of one label into two.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:531; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:954

## 85. [low / loop] "Place next machine" build flow

**State today: present.** Fully end-to-end and one of the strongest parts of the build. ActivateProductionFlowPrimaryAction takes the selected flow card, and if the stage is already installed it selects and focuses that actor; otherwise ResolveProductionStagePlacement maps the stage to a machine or storage type, checks CanPlaceMachine, and starts a real ghost placement on the pawn. ALBManagementPawn drives a cursor-traced preview with live validity feedback, rotate and cancel, then ConfirmPressTrainPlacement calls Builder->PlaceMachine. Input is bound to real actions: B = LB_BuildPressTrain, R = LB_PlacementRotate, Escape/gamepad = LB_PlacementCancel, all present in DefaultInput.ini. This is a genuine build mode, not a console command.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:2729; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:2174; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:2265; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1148; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Config/DefaultInput.ini:24

## 86. [low / loop] alert system and queue

**State today: present.** A real prioritised queue, not a stub. ULBFactoryUIStateSubsystem::RefreshSnapshot raises alerts from live machine state — Fault becomes Critical 'MACHINE FAULT', Blocked becomes Warning 'OUTPUT BLOCKED', Starved becomes Information 'AWAITING MATERIAL' (only while an order is active, so an idle factory does not nag) — each carrying the machine's own GetOperatingReason text, a world marker location, a weak actor pointer and a ProcessOrder. The queue is then sorted by severity, then upstream process order, then entity id, so the top alert is the most upstream root cause. GetTopAlert feeds a camera jump via ALBManagementPawn::FocusWorldTarget, and the count binds to the top bar as 'n alerts'.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:319; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:695; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:181; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:963; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:2007

## 87. [low / loop] cash model / ledger

**State today: present.** Genuinely strong and needs no rework. ULBFactoryManagementSubsystem is a deterministic, idempotent, event-sourced authority storing all money as int64 pence with a categorised ledger (CapitalPurchase, OperatingCost, OrderRevenue, MaintenanceService, MachineUpgrade), capital-asset register, quality and maintenance records, per-asset analytics time buckets and full OEE/availability/performance KPI derivation. It has no Tick and never invents failures. DefaultStartingCashPence = 250000000 = £2.50m, matching the mockup readout exactly, and ALBGameMode::BeginPlay initialises the campaign once. FormatMoney already renders '£2.50m'.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:423; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:430; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBGameMode.cpp:394; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:130

## 88. [low / loop] order counter "0 / 16 issued"

**State today: present.** Real and already in the mockup's exact wording. FLBVehiclePanelBatch carries OrderId, VehicleModelId, PanelTypeId, RequestedQuantity and DispatchedQuantity; ULBFactoryUIStateSubsystem projects the first incomplete batch into Order.IssuedQuantity / RequestedQuantity, and ULBManagementRootWidget renders '%s   %d / %d issued'. The default label string is literally 'CAIRNWELL 2040   0 / 0 issued'. The player can create an order in-game through the Production page (cycle model, cycle panel type, decrement, increment, queue).

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBPlayerBuiltPressFlowController.h:95; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:252; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:954; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBControlRoomHUD.cpp:3289

## 89. [low / loop] per-station Running / Waiting / Blocked state

**State today: present.** The simulation exposes exactly what the mockup's status dots need. ELBFactoryMachineOperatingState distinguishes Processing, Starved, Blocked and Fault per machine, each with a GetOperatingReason string. ULBFactoryUIStateSubsystem aggregates these into RunningCount, WaitingCount and FaultCount and stamps per-stage bRunning / bWaiting / bFaulted plus a Detail string such as '%d coils queued' onto each of the six canonical flow stages. ULBManagementRootWidget already drives coloured status dots from this and deliberately hides the dot for a not-yet-installed stage (ShouldShowStageStatusDot).

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:301; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:309; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:150; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.h:221

## 90. [low / other] Overlapping Canvas placement card drawn by the pawn

**State today: present.** Flagging a third HUD surface so it is not missed when consolidating: ALBManagementPawn registers itself as a post-rendered actor and Canvas-draws a placement card in PostRenderFor. That is a fourth drawing path alongside the UMG shell, the OneFactory Canvas strip and the Canvas toasts. Any consolidation of the HUD onto UMG needs to account for it.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:1014; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementPawn.cpp:996

## 91. [low / other] awards / trophy progression

**State today: absent.** The mockup's nav row includes a trophy/awards icon. There is no achievement, award, milestone or objective-completion system in the source at all — no destination id, no page enum entry, no data. The only adjacent concept is FLBFactoryUIOrderSnapshot::Objective, a single free-text string defaulting to 'BUILD THE FIRST PROCESS CELL' and reassigned to 'SCHEDULE THE NEXT PRODUCTION BATCH' when no order is active, which is a one-line hint rather than tracked progression.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.h:16; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryUIStateSubsystem.cpp:683; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBManagementRootWidget.cpp:56

## 92. [low / other] maintenance and quality simulation

**State today: present.** Unrequested by the mockup but already running, and it is what the alert system feeds on. ULBFactoryManagementRuntimeSubsystem ticks a bounded fixed-step bridge (max ten samples per frame so a load hitch cannot manufacture hours of wear), registering maintainable assets, mirroring faults, reconciling press quality counts and staging per-asset analytics buckets into the management authority. FLBManagementMaintenanceRecord tracks deterministic WearFraction, operating seconds since service and a 250-operating-hour service interval, and explicitly never invents a random fault. Quality records carry produced/inspected/passed/rejected/reworked/scrapped, feeding the OEE KPIs. This is the substrate a real management game needs and it already exists.

Evidence: C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementRuntimeSubsystem.cpp:714; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:147; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:172; C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8/Source/LineBossCarFactory/LBFactoryManagementSubsystem.h:236

