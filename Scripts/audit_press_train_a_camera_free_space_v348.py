"""Read-only camera transform and planned-point containment audit for v343."""
import json
from pathlib import Path
import unreal

MAP = "/Game/LineBoss/Maps/LB_PressShop_TrainAReleaseIntegrationCandidate_v343"
OUT = Path(unreal.Paths.project_saved_dir()) / "Audits/PressTrains/press_train_a_camera_free_space_v348.json"
if OUT.exists():
    raise RuntimeError(f"Refusing to overwrite {OUT}")
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if not levels.load_level(MAP):
    raise RuntimeError(MAP)
actors = actors_api.get_all_level_actors()
cameras = []
for actor in actors:
    if isinstance(actor, unreal.CameraActor) and ("TrainA" in actor.get_actor_label() or "PTA" in actor.get_actor_label()):
        cameras.append({
            "label": actor.get_actor_label(),
            "location_cm": list(actor.get_actor_location().to_tuple()),
            "rotation_deg": list(actor.get_actor_rotation().to_tuple()),
            "fov": actor.camera_component.get_editor_property("field_of_view"),
        })
points = {
    "v345_south": [3850.0, -7500.0, 760.0],
    "v347_south": [3850.0, -6400.0, 760.0],
    "between_a_south_edge_and_wall_1": [3850.0, -5600.0, 600.0],
    "between_a_south_edge_and_wall_2": [3850.0, -5300.0, 600.0],
    "west_end": [700.0, -4300.0, 700.0],
    "east_end": [7000.0, -4300.0, 700.0],
}
containment = {}
for key, coords in points.items():
    hits = []
    x, y, z = coords
    for actor in actors:
        origin, extent = actor.get_actor_bounds(False)
        if extent.x <= 0 or extent.y <= 0 or extent.z <= 0:
            continue
        if (abs(x - origin.x) <= extent.x and abs(y - origin.y) <= extent.y and abs(z - origin.z) <= extent.z):
            hits.append({"label": actor.get_actor_label(), "class": actor.get_class().get_name(),
                         "origin": list(origin.to_tuple()), "extent": list(extent.to_tuple())})
    containment[key] = hits
payload = {"map": MAP, "status": "READ_ONLY__NO_MAP_CHANGE", "cameras": cameras,
           "planned_point_containment": containment, "promotion_authorized": False}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"LB_CAMERA_FREE_SPACE_V348_PASS {OUT}")
unreal.SystemLibrary.quit_editor()
