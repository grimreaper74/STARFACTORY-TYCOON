"""Read-only diagnostic for the v438 build-bay coordinate mismatch."""
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_builder_authority_diagnostic_v444.json"

unreal.EditorLoadingAndSavingUtils.load_map(MAP)
api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
authority = next(a for a in api.get_all_level_actors() if a.get_class().get_name() == "LBPressShopBuildAuthority")

payload = {
    "map": MAP,
    "map_saved": False,
    "bays": [],
    "spines": [],
    "rotation_probes": {},
}
for bay in authority.get_editor_property("build_bays"):
    payload["bays"].append({
        "id": str(bay.get_editor_property("bay_id")),
        "centre": str(bay.get_editor_property("centre")),
        "half_extent": str(bay.get_editor_property("half_extent")),
    })
for spine in authority.get_editor_property("utility_spines"):
    payload["spines"].append({
        "id": str(spine.get_editor_property("spine_id")),
        "start": str(spine.get_editor_property("start")),
        "end": str(spine.get_editor_property("end")),
        "reach": spine.get_editor_property("maximum_connection_distance_cm"),
    })

for yaw in (0.0, 90.0, -90.0, 180.0):
    transform = unreal.Transform(
        location=unreal.Vector(3850.0, -4300.0, 0.0),
        rotation=unreal.Rotator(0.0, yaw, 0.0),
        scale=unreal.Vector(1.0, 1.0, 1.0))
    payload["rotation_probes"][str(yaw)] = {
        "rotation": str(transform.rotation.rotator()),
        "description": str(authority.describe_train_transform(transform)),
    }

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
unreal.SystemLibrary.quit_editor()
