"""Create a fresh whole-shop v231 child correcting current PR003 coil readability."""

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v231"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_coil_readability_build_v231.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v230.umap"
LIGHT_LABELS = {
    "LB_ENV_V140_CoilTaskRect_01", "LB_ENV_V140_CoilTaskRect_02",
    "LB_ENV_V141_CoilNorthTaskRect_01", "LB_ENV_V141_CoilNorthTaskRect_02",
}
TARGET_INTENSITY = 110.0

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite preserved candidate {MAP}")
parent_hash_before = sha256(BASE_FILE)
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

failures = []
changed_lights = []
for actor in actors_api.get_all_level_actors():
    label = actor.get_actor_label()
    if label not in LIGHT_LABELS:
        continue
    component = actor.get_component_by_class(unreal.RectLightComponent)
    before = float(component.get_editor_property("intensity"))
    if abs(before - 62.0) > 0.01:
        failures.append(f"unexpected inherited intensity {label}={before}")
    component.set_editor_property("intensity", TARGET_INTENSITY)
    prior_tags = [str(value) for value in actor.tags]
    actor.tags = [unreal.Name(value) for value in dict.fromkeys(prior_tags + [
        "LB.Integration.WholeShop.v231", "LB.VisualCorrection.CoilReadability.v231",
        "LB.Lighting.PreviewOnly.NoLuxAuthority", "LB.Asset.CandidateNotPromoted",
    ])]
    changed_lights.append({"label": label, "before": before, "after": TARGET_INTENSITY})

slot_pattern = re.compile(r"LB\.PR003\.Layout\.Slot\.CS-(0[1-9]|1[0-2])")
coil_rows = []
for actor in actors_api.get_all_level_actors():
    tags = [str(value) for value in actor.tags]
    slot_tags = [tag for tag in tags if slot_pattern.fullmatch(tag)]
    if not slot_tags:
        continue
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh is None or "SM_LB_MasterCoil_Candidate_v005" not in mesh.get_path_name():
            continue
        location = actor.get_actor_location()
        coil_rows.append({
            "actor": actor.get_actor_label(),
            "slot": slot_tags[0].rsplit(".", 1)[-1],
            "location_cm": [location.x, location.y, location.z],
            "pale_silver_slot": component.get_material(2).get_path_name() if component.get_material(2) else None,
        })

if len(changed_lights) != 4:
    failures.append(f"expected four inherited task lights, found {len(changed_lights)}")
if len(coil_rows) != 12:
    failures.append(f"expected exactly twelve PR003 stored coils, found {len(coil_rows)}")
if sorted(row["slot"] for row in coil_rows) != [f"CS-{index:02d}" for index in range(1, 13)]:
    failures.append("PR003 slot identities are not exactly CS-01 through CS-12")
if any("MI_CA_MW_PaleSilverPolyWrap_v118" not in (row["pale_silver_slot"] or "") for row in coil_rows):
    failures.append("one or more PR003 coils lost the retained pale-silver wrap slot")

if not levels.save_current_level():
    failures.append("could not save v231")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v230 parent changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v231.umap"
payload = {
    "$schema": "cairnwell/audit/press-shop-coil-readability-build-v231/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FOUR_EXISTING_COIL_TASK_LIGHTS_RECALIBRATED__FRESH_VISUAL_GATE_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(map_file) if map_file.exists() else None,
    "changed_lights": sorted(changed_lights, key=lambda row: row["label"]),
    "stored_coil_count": len(coil_rows),
    "stored_coils": sorted(coil_rows, key=lambda row: row["slot"]),
    "coil_material_or_transform_changes": 0,
    "fixture_geometry_changes": 0,
    "authority_machine_collision_navigation_changes": 0,
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
