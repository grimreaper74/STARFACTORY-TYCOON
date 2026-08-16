"""Add broad movable upward area fill directly to retained visual parent v242."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v247"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_broad_roof_bounce_build_v247.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v247.umap"

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
for bay_id, x_value in enumerate((2600.0, 5600.0, 8600.0), 1):
    light = actors_api.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(x_value, -1700.0, 900.0), unreal.Rotator(90.0, 0.0, 0.0))
    if light is None:
        failures.append(f"could not spawn broad roof fill bay {bay_id}")
        continue
    label = f"LB_WHOLE_V247_BROAD_ROOF_BOUNCE_{bay_id:02d}"
    light.set_actor_label(label)
    component = light.rect_light_component
    component.set_mobility(unreal.ComponentMobility.MOVABLE)
    component.set_editor_properties({
        "intensity": 4.0,
        "attenuation_radius": 2600.0,
        "source_width": 2600.0,
        "source_height": 6200.0,
        "light_color": unreal.Color(190, 204, 216, 255),
        "cast_shadows": False,
    })
    light.tags = [
        unreal.Name("LB.Lighting.IndustrialLED.BroadRoofBounce"),
        unreal.Name("LB.Lighting.PreviewOnly.NoLuxAuthority"),
        unreal.Name("LB.VisualCorrection.RoofReadability.v247"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]
    added.append({
        "label": label,
        "location_cm": [x_value, -1700.0, 900.0],
        "rotation_deg": [90.0, 0.0, 0.0],
        "intensity_preview_only": 4.0,
        "attenuation_radius_cm": 2600.0,
        "source_width_cm": 2600.0,
        "source_height_cm": 6200.0,
        "mobility": "MOVABLE",
    })

if len(added) != 3:
    failures.append(f"expected three broad roof-bounce lights, added {len(added)}")
if not levels.save_current_level():
    failures.append("could not save v247")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v242 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-broad-roof-bounce-build-v247/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__THREE_BROAD_MOVABLE_ROOF_BOUNCE_LIGHTS_ADDED_DIRECTLY_FROM_V242__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "added_lights": added,
    "rejected_maps_not_in_ancestry": ["v243", "v244", "v245", "v246"],
    "contract": {
        "purpose": "preview-only broad roof bounce; no lux authority",
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
