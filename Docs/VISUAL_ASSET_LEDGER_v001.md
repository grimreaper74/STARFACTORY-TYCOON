# Line Boss visual asset ledger

This ledger records visual authority separately from functional authority.  A listed source or
derivative is never a runtime promotion unless its runtime status explicitly says so.

| Player-visible family | Engineering / source authority | Best visual source or derivative | Runtime status | Current blocker | Evidence |
| --- | --- | --- | --- | --- | --- |
| Inbound lorry, coils, crane, saddle and handler | `SourceAssets/Candidate/PressShop/InboundCoilDelivery/LorryLoadedWrappedCoils_v20260809_v004` | Owner review pack `.../v808_ApprovalPack`; 16.5 x 2.55 x 4.0 m four-coil assembly | Runtime-ready components exist; player-built binding is functional | Player overview material/camera validation still required | `.../v808_ApprovalPack/Review/01_Lorry_Loaded_Hero_v808.png` |
| PR005 decoiler/threader | Immutable engineering: `SourceAssets/Candidate/PressShop/PR005/OwnerApprovalPack_v20260809_v812/PR005_ExteriorEnclosure_OwnerReview_v812.blend` | `SourceAssets/Candidate/PressShop/PR005/ArtSkin_v013_BrightIndustrialCell/PR005_CairnwellBrightIndustrialSkin_v013.blend` | Candidate-only source derivative; no Unreal import | Review approval, Unreal split/import, collision/LOD/Nanite/socket/save/cook/overview checks | `.../ArtSkin_v013_BrightIndustrialCell/Renders/05_PR005_v013_OverviewThreeQuarter.png` |
| PR006 feed/straightening | Existing engineering/generation reference `SourceAssets/Candidate/PressShop/PR006/GenerationReference_v20260809_v815` | No new Cairnwell derivative yet | Proxy/candidate | Player-visible family not yet refit | Existing reference pack |
| PR007 blank buffer | Existing engineering/generation reference `SourceAssets/Candidate/PressShop/PR007/GenerationReference_v20260809_v816` | No new Cairnwell derivative yet | Proxy/candidate | Player-visible family not yet refit | Existing reference pack |
| PR008 transfer/process line | `SourceAssets/Candidate/PressShop/PR008/EngineeringBlockout_v20260809_v804` | `.../PR008/ProDesignPack_v20260809_v818` is design evidence only | Proxy/candidate | Do not promote blockout/design reference as final art | Existing review pack |
| PR009 blank stacker | `SourceAssets/PR009/AutomatedBlankStacker/Candidate_v002` canonical source | Candidate import only | Candidate-only | Runtime/source handoff and final visual gates are incomplete | `Saved/Audits/press_shop_pr009_source_intake_v002.json` |
| PR010 buffer/transfer | v098/v099 detailed runtime authority, visual release held | Pro design pack v820 / engineering source v103 (not direct promotion) | Runtime technical candidate; visual proxy | Final art authority and presentation pass | `Saved/Audits/PR010_CollisionNavigation/PR010_V099_RELEASE_VERIFICATION.json` |
| Conveyors, stillages, panel handling | Current factory-builder engineering authority | No family-level final art derivative yet | Mixed runtime/proxy | Needs a shared visual kit/binding audit after PR005–PR010 | Existing player-builder route meshes |
| Body Weld | `SourceAssets/Candidate/WeldShop/BodyWeldRuntimeArt_v001/Freeze/FROZEN_v001.json` | Imported `/Game/LineBoss/Candidates/WeldShop/BodyWeldLine/Runtime_v001` fixture/skid/underbody | Unreal-import validated; runtime binding pending | Full cell, robot, lighting and overview validation | `Saved/Audits/WeldShop/BodyWeldRuntimeArt_v001/promotion_receipt_v001.json` |
| ED coat | Existing source/technical runtime authority | Rail-free module derivative v002 | Deferred by current work order | Complete press and Body Weld first | `Saved/Audits/PaintShop/EDLine/ed_line_no_rail_unreal_validation_v002.json` |
| Finished vehicle / drive-off | Existing visual reference only | `FinishedVehicleVisual_Intake_v001` | Deferred and runtime blocked | Press/Body Weld complete first; then derive a separately validated runtime vehicle | `.../FinishedVehicleVisual_Intake_v001/Audit/FINISHED_VEHICLE_VISUAL_AUDIT_v001.md` |

## PR005 v013 derivative scope

- v013 is created from v012 as a new Blender file; v012 and the v812 engineering source are
  untouched.
- The fixed PR005 envelope remains 5.763 x 10.360 x 3.550 m.
- The derivative preserves exposed headstock/mandrel, pinch-roll/threader and strip zones.  Its
  visual additions are separately removable roof cassettes, exterior access doors, vents,
  handles, latches, service trunking, cables, HMI, stack light and non-functional panel details.
- No collision, pivot, gameplay, map, v913 or Unreal content was modified by this source pass.
