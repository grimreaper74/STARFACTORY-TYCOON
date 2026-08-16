"""Compare visible donor static actors with their v286 copies."""
import json
import os
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
VERSION = os.environ.get("LB_COPY_FIDELITY_VERSION", "v286").lower()
TARGET = f"/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_{VERSION}"
DONORS = {
    "PR006": "/Game/LineBoss/Maps/LB_PressShop_PR006ReleaseArtCandidate_v208",
    "PR007": "/Game/LineBoss/Maps/LB_PressShop_PR007ReleaseArtCandidate_v209",
    "PR008": "/Game/LineBoss/Maps/LB_PressShop_PR008AuthoredAnchorCandidate_v210",
}
OUT = ROOT / f"Saved/Audits/PressShopIntegration/press_shop_pr006_pr008_donor_copy_fidelity_{VERSION}.json"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def state(actor):
    component = actor.static_mesh_component
    origin, extent = actor.get_actor_bounds(False)
    return {
        "location": [actor.get_actor_location().x, actor.get_actor_location().y, actor.get_actor_location().z],
        "rotation": [actor.get_actor_rotation().pitch, actor.get_actor_rotation().yaw, actor.get_actor_rotation().roll],
        "scale": [actor.get_actor_scale3d().x, actor.get_actor_scale3d().y, actor.get_actor_scale3d().z],
        "bounds_origin": [origin.x, origin.y, origin.z],
        "bounds_extent": [extent.x, extent.y, extent.z],
        "mesh": component.static_mesh.get_path_name() if component.static_mesh else None,
        "materials": [component.get_material(i).get_path_name() if component.get_material(i) else None for i in range(component.get_num_materials())],
    }


if not levels.load_level(TARGET):
    raise RuntimeError(TARGET)
target = {a.get_actor_label(): state(a) for a in actors_api.get_all_level_actors() if isinstance(a, unreal.StaticMeshActor)}
families = {}
for family, donor in DONORS.items():
    if not levels.load_level(donor):
        raise RuntimeError(donor)
    mismatches = []
    checked = 0
    for actor in actors_api.get_all_level_actors():
        if not isinstance(actor, unreal.StaticMeshActor):
            continue
        tags = [str(tag) for tag in actor.tags]
        component = actor.static_mesh_component
        if f"LB.Station.{family}" not in tags or actor.is_hidden_ed() or not bool(component.get_editor_property("visible")):
            continue
        label = actor.get_actor_label()
        if label not in target:
            mismatches.append({"label": label, "reason": "missing"})
            continue
        checked += 1
        source_state = state(actor)
        target_state = target[label]
        differences = {}
        for key in ("location", "rotation", "scale", "bounds_origin", "bounds_extent"):
            delta = [abs(float(a) - float(b)) for a, b in zip(source_state[key], target_state[key])]
            if max(delta) > 0.01:
                differences[key] = {"donor": source_state[key], "target": target_state[key], "max_delta": max(delta)}
        for key in ("mesh", "materials"):
            if source_state[key] != target_state[key]:
                differences[key] = {"donor": source_state[key], "target": target_state[key]}
        if differences:
            mismatches.append({"label": label, "differences": differences})
    families[family] = {"checked": checked, "mismatch_count": len(mismatches), "mismatches": mismatches}
payload = {"target": TARGET, "donors": DONORS, "families": families}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps({family: {"checked": row["checked"], "mismatches": row["mismatch_count"]} for family, row in families.items()}, indent=2))
unreal.SystemLibrary.quit_editor()
