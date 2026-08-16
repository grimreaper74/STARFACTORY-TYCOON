"""Place two non-promoted LB-CR01 candidates and modular charging docks."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_SupportRobotsCandidate_v005"
ASSET_DIR = "/Game/LineBoss/Shared/SupportRobots/LB_CR01/Candidate_v004"
AUDIT = Path(unreal.Paths.project_saved_dir()) / "Audits/press_shop_lb_cr01_v004_placement_v005.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels.load_level(MAP)

mesh_paths = []
for path in unreal.EditorAssetLibrary.list_assets(ASSET_DIR, recursive=False, include_folder=False):
    if isinstance(unreal.load_asset(path), unreal.StaticMesh):
        mesh_paths.append(path)
if len(mesh_paths) != 89:
    raise RuntimeError(f"Expected reviewed 89-mesh LB-CR01 v004 import, found {len(mesh_paths)}")

placements = (
    ("WEST", unreal.Vector(-9800, -5200, 0), 0.0),
    ("EAST", unreal.Vector(9200, -5200, 0), 180.0),
)
created = []
for unit, location, yaw in placements:
    rotation = unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw)
    for path in mesh_paths:
        mesh = unreal.load_asset(path)
        actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, rotation)
        actor.set_actor_label(f"LB_CR01_{unit}_{mesh.get_name()}")
        component = actor.get_editor_property("static_mesh_component")
        component.set_static_mesh(mesh)
        mover = any(token in mesh.get_name().upper() for token in ("WHEEL", "BRUSH", "SCRUB", "SQUEEGEE"))
        component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE if mover else unreal.ComponentMobility.STATIC)
        actor.set_editor_property("tags", [unreal.Name("LB.SupportRobot.LB-CR01"), unreal.Name("LB.State.Mothballed"), unreal.Name(f"LB.Unit.{unit}")])
        created.append(actor.get_actor_label())

cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
charcoal = unreal.load_asset("/Game/LineBoss/Materials/M_LB_ShellCharcoal.M_LB_ShellCharcoal")
yellow = unreal.load_asset("/Game/LineBoss/Materials/M_LB_SafetyYellow.M_LB_SafetyYellow")
steel = unreal.load_asset("/Game/LineBoss/Materials/M_LB_StructureSteel.M_LB_StructureSteel")

def dock_part(label, location, scale, material, yaw=0.0):
    actor = actors.spawn_actor_from_class(unreal.StaticMeshActor, location, unreal.Rotator(roll=0.0, pitch=0.0, yaw=yaw))
    actor.set_actor_label(label)
    component = actor.get_editor_property("static_mesh_component")
    component.set_static_mesh(cube)
    component.set_material(0, material)
    actor.set_actor_scale3d(scale)
    actor.set_editor_property("tags", [unreal.Name("LB.SupportRobot.Dock.CR01"), unreal.Name("LB.State.Mothballed")])
    created.append(label)

for unit, robot_loc, yaw in placements:
    sign = -1.0 if yaw == 0.0 else 1.0
    x = robot_loc.x + sign * 125.0
    y = robot_loc.y
    dock_part(f"LB_CR01_DOCK_{unit}_Base", unreal.Vector(x, y, 5), unreal.Vector(0.22, 0.75, 0.10), charcoal, yaw)
    dock_part(f"LB_CR01_DOCK_{unit}_Back", unreal.Vector(x + sign * 18, y, 70), unreal.Vector(0.08, 0.70, 1.30), charcoal, yaw)
    dock_part(f"LB_CR01_DOCK_{unit}_Contact", unreal.Vector(x - sign * 22, y, 42), unreal.Vector(0.035, 0.28, 0.22), steel, yaw)
    dock_part(f"LB_CR01_DOCK_{unit}_Header", unreal.Vector(x + sign * 2, y, 145), unreal.Vector(0.18, 0.72, 0.12), yellow, yaw)
    for side in (-1, 1):
        dock_part(f"LB_CR01_DOCK_{unit}_Bollard_{side:+d}", unreal.Vector(x - sign * 30, y + side * 62, 42), unreal.Vector(0.14, 0.14, 0.84), yellow, yaw)

if not levels.save_current_level():
    raise RuntimeError("Could not save Press Shop v005 support-robot placement")
AUDIT.parent.mkdir(parents=True, exist_ok=True)
AUDIT.write_text(json.dumps({"status": "CANDIDATE_NOT_PROMOTED", "map": MAP, "robot_source": ASSET_DIR, "units": [p[0] for p in placements], "robot_meshes_per_unit": len(mesh_paths), "created_actor_count": len(created)}, indent=2), encoding="utf-8")
unreal.log(f"LINE_BOSS_PRESS_V005_LBCR01_PLACE_PASS actors={len(created)}")
