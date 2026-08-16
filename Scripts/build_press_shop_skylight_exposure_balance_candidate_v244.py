"""Balance inherited skylight fill and fixed exposure in an isolated v242 child."""

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242"
MAP = "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v244"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_skylight_exposure_balance_build_v244.json"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v242.umap"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v244.umap"

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
sky = next((actor for actor in actors_api.get_all_level_actors()
            if actor.get_actor_label() == "LB_PRESS_V023_FrontEndSkyLight"), None)
exposure = next((actor for actor in actors_api.get_all_level_actors()
                 if actor.get_actor_label() == "LB_INT_FRONT_FrontEndFixedExposure"), None)
sky_before = None
exposure_before = None
if isinstance(sky, unreal.SkyLight):
    component = sky.get_component_by_class(unreal.SkyLightComponent)
    sky_before = float(component.get_editor_property("intensity"))
    component.set_editor_properties({"intensity": 1.35, "cast_shadows": False})
    sky.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in sky.tags] + [
            "LB.VisualCorrection.SkylightExposureBalance.v244",
            "LB.Lighting.PreviewOnly.NoLuxAuthority",
            "LB.Asset.CandidateNotPromoted",
        ])]
else:
    failures.append("retained skylight missing")

if isinstance(exposure, unreal.PostProcessVolume):
    settings = exposure.get_editor_property("settings")
    exposure_before = float(settings.get_editor_property("auto_exposure_bias"))
    settings.set_editor_properties({
        "override_auto_exposure_bias": True,
        "auto_exposure_bias": 0.25,
    })
    exposure.set_editor_property("settings", settings)
    exposure.tags = [unreal.Name(value) for value in dict.fromkeys(
        [str(value) for value in exposure.tags] + [
            "LB.VisualCorrection.SkylightExposureBalance.v244",
            "LB.Asset.CandidateNotPromoted",
        ])]
else:
    failures.append("retained fixed exposure volume missing")

if sky_before is not None and abs(sky_before - 0.72) > 0.001:
    failures.append(f"unexpected inherited skylight intensity {sky_before}")
if exposure_before is not None and abs(exposure_before - 0.75) > 0.001:
    failures.append(f"unexpected inherited exposure bias {exposure_before}")
if not levels.save_current_level():
    failures.append("could not save v244")
parent_hash_after = sha256(BASE_FILE)
if parent_hash_after != parent_hash_before:
    failures.append("protected v242 parent changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-skylight-exposure-balance-build-v244/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__SKYLIGHT_FILL_INCREASED_AND_EXPOSURE_REDUCED__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__NOT_PROMOTED",
    "base": BASE,
    "map": MAP,
    "parent_hash_before": parent_hash_before,
    "parent_hash_after": parent_hash_after,
    "map_hash": sha256(MAP_FILE) if MAP_FILE.exists() else None,
    "skylight_intensity_before": sky_before,
    "skylight_intensity_after": 1.35,
    "exposure_bias_before": exposure_before,
    "exposure_bias_after": 0.25,
    "contract": {
        "purpose": "preview balance only; no lux or engineering authority",
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
