"""Add restrained upward industrial fill to the dark roof of retained shell candidate v242."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v243"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_roof_fill_lighting_build_v243.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v243.umap"

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
added = []
for row_id, y_value in enumerate((-4800.0, -3000.0, -1200.0, 600.0), 1):
    for bay_id, x_value in enumerate((2300.0, 5000.0, 7700.0), 1):
        light = actors_api.spawn_actor_from_class(
            unreal.RectLight,
            unreal.Vector(x_value, y_value, 1460.0),
            unreal.Rotator(90.0, 0.0, 0.0),
        )
        if light is None:
            failures.append(f"could not spawn roof fill row {row_id} bay {bay_id}")
            continue
        label = f"LB_WHOLE_V243_ROOF_FILL_{row_id:02d}_{bay_id:02d}"
        light.set_actor_label(label)
        light.rect_light_component.set_editor_properties({
            "intensity": 8.0,
            "attenuation_radius": 1550.0,
            "source_width": 1450.0,
            "source_height": 220.0,
            "light_color": unreal.Color(188, 204, 216, 255),
            "cast_shadows": False,
        })
        light.tags = [
            unreal.Name("LB.Lighting.IndustrialLED.RoofFill"),
            unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
            unreal.Name("LB.VisualCorrection.RoofReadability.v243"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        added.append({
            "label": label,
            "location_cm": [x_value, y_value, 1460.0],
            "rotation_deg": [90.0, 0.0, 0.0],
            "intensity_preview_only": 8.0,
        })

if len(added) != 12:
    failures.append(f"expected 12 roof-fill lights, added {len(added)}")
if not levels.save_current_level():
    failures.append("could not save v243")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v242 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-roof-fill-lighting-build-v243/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__RESTRAINED_UPWARD_ROOF_FILL_ADDED__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "added_roof_fill_lights": added,
    "light_contract": {
        "purpose": "preview-only roof readability; no lux or engineering authority",
        "direction": "upward toward the roof underside",
        "machine_geometry_material_collision_navigation_authority_changes": 0,
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
