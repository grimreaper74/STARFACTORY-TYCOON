"""Create the reusable unlit live-CCTV display material without overwriting assets."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal


ROOT = Path(unreal.Paths.project_dir())
DEST = "/Game/LineBoss/Candidates/ControlRoom/CCTV"
ASSET = f"{DEST}/M_CairnwellCCTVFeed"
OUT = ROOT / "Saved/Audits/ControlRoom/control_room_cctv_feed_material_build_v001.json"
library = unreal.EditorAssetLibrary
failures = []

if library.does_asset_exist(ASSET):
    raise RuntimeError(f"refusing to overwrite {ASSET}")

factory = unreal.MaterialFactoryNew()
material = unreal.AssetToolsHelpers.get_asset_tools().create_asset(
    "M_CairnwellCCTVFeed", DEST, unreal.Material, factory)
if not isinstance(material, unreal.Material):
    raise RuntimeError("failed to create CCTV material")

material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_OPAQUE)
material.set_editor_property("two_sided", True)
material.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)

sample = unreal.MaterialEditingLibrary.create_material_expression(
    material, unreal.MaterialExpressionTextureSampleParameter2D, -420, 0)
sample.set_editor_property("parameter_name", "CCTVTexture")
unreal.MaterialEditingLibrary.connect_material_property(
    sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR)
unreal.MaterialEditingLibrary.recompile_material(material)
library.save_loaded_asset(material, only_if_is_dirty=False)

payload = {
    "$schema": "cairnwell/audit/control-room-cctv-feed-material-build-v001/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__REUSABLE_UNLIT_LIVE_CCTV_MATERIAL__RUNTIME_FEED_GATE_REQUIRED__NOT_PROMOTED",
    "asset": ASSET,
    "texture_parameter": "CCTVTexture",
    "usage": "ALBControlRoomCCTVFeed selected live SceneCapture render target",
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
print(json.dumps(payload, indent=2))
