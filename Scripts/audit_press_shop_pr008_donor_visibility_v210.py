"""Audit PR008 donor visibility states to separate current and superseded meshes."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressShopIntegration/press_shop_pr008_donor_visibility_v210.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
rows = []
for actor in actors_api.get_all_level_actors():
    if not isinstance(actor, unreal.StaticMeshActor):
        continue
    tags = [str(tag) for tag in actor.tags]
    if "LB.Station.PR008" not in tags:
        continue
    component = actor.static_mesh_component
    origin, extent = actor.get_actor_bounds(False)
    rows.append({
        "label": actor.get_actor_label(),
        "mesh": component.static_mesh.get_path_name() if component.static_mesh else None,
        "hidden_editor": bool(actor.is_hidden_ed()),
        "component_visible": bool(component.get_editor_property("visible")),
        "hidden_in_game": bool(component.get_editor_property("hidden_in_game")),
        "extent": [extent.x, extent.y, extent.z],
        "location": [origin.x, origin.y, origin.z],
        "tags": tags,
    })
groups = {}
for row in rows:
    key = f"ed_hidden={row['hidden_editor']}__visible={row['component_visible']}__game_hidden={row['hidden_in_game']}"
    groups.setdefault(key, []).append(row)
payload = {"map": MAP, "count": len(rows), "groups": groups}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({key: len(value) for key, value in groups.items()}, indent=2))
unreal.SystemLibrary.quit_editor()
