"""Add restrained movable high-bay roof fill directly to retained visual parent v242."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v246"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_balanced_high_bay_build_v246.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v246.umap"

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

added = []
failures = []
for row_id, y_value in enumerate((-4300.0, -1700.0, 900.0), 1):
    for bay_id, x_value in enumerate((1500.0, 3500.0, 5500.0, 7500.0, 9500.0), 1):
        light = actors_api.spawn_actor_from_class(
            unreal.PointLight, unreal.Vector(x_value, y_value, 1810.0), unreal.Rotator())
        if light is None:
            failures.append(f"could not spawn row {row_id} bay {bay_id}")
            continue
        label = f"LB_WHOLE_V246_BALANCED_HIGH_BAY_{row_id:02d}_{bay_id:02d}"
        light.set_actor_label(label)
        component = light.point_light_component
        component.set_mobility(unreal.ComponentMobility.MOVABLE)
        component.set_editor_properties({
            "intensity": 220.0,
            "attenuation_radius": 1150.0,
            "source_radius": 35.0,
            "light_color": unreal.Color(198, 210, 220, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name("LB.Lighting.IndustrialLED.HighBayBounce"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
            unreal.Name("LB.VisualCorrection.RoofReadability.v246"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        added.append({
            "label": label,
            "location_cm": [x_value, y_value, 1810.0],
            "intensity_preview_only": 220.0,
            "attenuation_radius_cm": 1150.0,
            "source_radius_cm": 35.0,
            "mobility": "MOVABLE",
        })

if len(added) != 15:
    failures.append(f"expected 15 balanced high-bay lights, added {len(added)}")
if not levels.save_current_level():
    failures.append("could not save v246")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v242 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-balanced-high-bay-build-v246/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RESTRAINED_MOVABLE_HIGH_BAY_FILL_ADDED_DIRECTLY_FROM_V242__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "added_lights": added,
    "rejected_maps_not_in_ancestry": ["v243", "v244", "v245"],
    "contract": {
        "purpose": "preview-only balanced roof readability; no lux authority",
        "geometry_machine_material_collision_navigation_authority_changes": 0
    },
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
