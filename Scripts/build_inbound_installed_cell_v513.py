"""Fresh v513 adds retained runway/end-carriage modules and a crane-side process view."""
from pathlib import Path
import unreal

source = (Path(__file__).parent / "build_inbound_installed_cell_v512.py").read_text(encoding="utf-8")
source = source.replace("InstalledCell_v512", "InstalledCell_v513")
source = source.replace("LB_INBOUND_V012_", "LB_INBOUND_V013_")
source = source.replace("V512", "V513")
source = source.replace("unreal.Vector(2550, -2350, 1280)", "unreal.Vector(2350, 2650, 1380)")
source = source.replace("unreal.Vector(120, 300, 210)", "unreal.Vector(100, 250, 220)")
exec(compile(source, str(Path(__file__)), "exec"), globals(), globals())

library = unreal.EditorAssetLibrary
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
base = "/Game/LineBoss/IndustrialKit/MaterialHandling/BridgeCrane"

def crane_part(label, asset_name, location, rotation=(0, 0, 0), scale=(1, 1, 1)):
    mesh = library.load_asset(f"{base}/{asset_name}")
    if not isinstance(mesh, unreal.StaticMesh):
        raise RuntimeError(f"Missing crane part {asset_name}")
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator(*rotation))
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    actor.static_mesh_component.set_static_mesh(mesh)
    actor.tags = [unreal.Name("LB.Asset.ValidationOnly"), unreal.Name("LB.Asset.CandidateNotPromoted"), unreal.Name("LB.Crane.40T.TBC")]
    return actor

# Readable longitudinal runway rails and bridge end carriages around the retained bridge girder.
crane_part("LB_INBOUND_V013_RunwayWest", "SM_LB_Crane_RunwayBeam_3000_v001", (-720, 760, 610), rotation=(0, 0, 90), scale=(1.25, 1, 1))
crane_part("LB_INBOUND_V013_RunwayEast", "SM_LB_Crane_RunwayBeam_3000_v001", (720, 760, 610), rotation=(0, 0, 90), scale=(1.25, 1, 1))
crane_part("LB_INBOUND_V013_EndTruckWest", "SM_LB_Crane_EndTruck_v001", (-660, 540, 625), rotation=(0, 0, 90))
crane_part("LB_INBOUND_V013_EndTruckEast", "SM_LB_Crane_EndTruck_v001", (660, 540, 625), rotation=(0, 0, 90))

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving isolated v513 installed cell")
unreal.log("LINE_BOSS_INBOUND_INSTALLED_CELL_V513_BUILD_PASS")
