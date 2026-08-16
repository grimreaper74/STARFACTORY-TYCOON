"""Install the purpose-built dock architecture into the retained inbound cell."""
from pathlib import Path
import json
import unreal

root = Path(__file__).parent
source = (root / "build_inbound_installed_cell_v535.py").read_text(encoding="utf-8")
source = source.replace("v535", "v537").replace("V535", "V537").replace("V035_", "V037_")
exec(compile(source, str(root / "build_inbound_installed_cell_v535.py"), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
project = Path(unreal.Paths.project_dir())
dock = library.load_asset("/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v001/SM_CA_MW_Inbound_DockArchitecture_v001")
if not isinstance(dock, unreal.StaticMesh):
    raise RuntimeError("Missing imported inbound dock architecture v001")

# Remove only the temporary backdrop blocks behind the lorry. Structural hall
# columns, lights and the downstream PR-003 context remain for scale.
for actor in list(actors.get_all_level_actors()):
    label = actor.get_actor_label()
    if label.startswith("LB_INBOUND_V037_BackWall_") or label.startswith("LB_INBOUND_V037_WindowBand") or label.startswith("LB_INBOUND_V037_WallMullion_") or label.startswith("LB_INBOUND_V037_DockIdentitySign") or label.startswith("LB_INBOUND_V037_DockSignText"):
        actors.destroy_actor(actor)

a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(-3200, 0, 0), unreal.Rotator(0, 0, -90))
a.set_actor_label("LB_INBOUND_V037_PurposeBuiltDockArchitecture")
a.static_mesh_component.set_static_mesh(dock)
a.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
a.static_mesh_component.set_editor_property("can_ever_affect_navigation", True)
a.tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"),
          unreal.Name("LB.Engineering.Values.TBC"), unreal.Name("LB.Inbound.ProPack.20260807")]

overview = next(x for x in actors.get_all_level_actors() if x.get_actor_label() == "LB_CAM_InboundHall_ProcessOverview_v537")
overview.set_actor_location(unreal.Vector(-650, 6900, 2250), False, False)
overview.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(overview.get_actor_location(), unreal.Vector(-750, -50, 320)), False)
overview.camera_component.set_editor_property("field_of_view", 51.0)
hero = next(x for x in actors.get_all_level_actors() if x.get_actor_label() == "LB_CAM_InboundHall_CraneHero_v537")
hero.set_actor_location(unreal.Vector(1500, 4350, 1700), False, False)
hero.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(hero.get_actor_location(), unreal.Vector(-350, -50, 360)), False)
hero.camera_component.set_editor_property("field_of_view", 56.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v537 installed dock review")
audit = project / "Saved/Audits/PressShopIntegration/inbound_dock_install_build_v537.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "status": "PASS__ISOLATED_DOCK_INSTALLED__VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "map": "/Game/LineBoss/Developer/Validation/LB_InboundCoilDeliveryInstalledCell_v537",
    "dock_asset": "/Game/LineBoss/IndustrialKit/InboundCoilDelivery/DockArchitectureCandidate_v001/SM_CA_MW_Inbound_DockArchitecture_v001",
    "retained_process_layout": "v532", "lighting_direction": "v535",
    "engineering_values": "TBC", "builder_authority_v438_modified": False,
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_DOCK_INSTALL_V537_BUILD_PASS")
