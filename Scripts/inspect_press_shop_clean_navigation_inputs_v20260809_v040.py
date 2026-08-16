"""Read-only actor/collision inventory for failed clean-map nav build."""
from pathlib import Path
import json
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNav_v20260809_v038"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_navigation_inputs_v20260809_v040.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError("load failed")
rows = []
for actor in actors.get_all_level_actors():
    label = actor.get_actor_label()
    if not any(key in label.lower() for key in ("floor", "slab", "shell", "nav", "walk")):
        continue
    row = {"label": label, "class": actor.get_class().get_name(), "location_cm": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z]}
    if isinstance(actor, unreal.StaticMeshActor):
        comp = actor.static_mesh_component
        row["collision_enabled"] = str(comp.get_collision_enabled())
        row["collision_profile"] = str(comp.get_collision_profile_name())
        mesh = comp.static_mesh
        row["mesh"] = mesh.get_path_name() if mesh else None
        origin, extent = actor.get_actor_bounds(False)
        row["bounds_origin_cm"] = [origin.x, origin.y, origin.z]
        row["bounds_size_cm"] = [extent.x*2, extent.y*2, extent.z*2]
    rows.append(row)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"map": MAP, "actors": rows}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_NAV_INPUTS_V040_WRITTEN")
