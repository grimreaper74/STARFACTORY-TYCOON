"""Disable Nanite on the full-detail textured wrapped coil used by the Coil AGV."""
import unreal
import json
from pathlib import Path

ASSET = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v004/Inbound/SM_CA_MW_WrappedCoil_Repaired_v003.SM_CA_MW_WrappedCoil_Repaired_v003"
mesh = unreal.EditorAssetLibrary.load_asset(ASSET)
if not isinstance(mesh, unreal.StaticMesh):
    raise RuntimeError(f"Missing wrapped coil: {ASSET}")
settings = mesh.get_editor_property("nanite_settings")
was_enabled = bool(settings.enabled)
settings.enabled = False
mesh.set_editor_property("nanite_settings", settings)
mesh.modify()
saved = unreal.EditorAssetLibrary.save_loaded_asset(mesh, only_if_is_dirty=False)
result = {"mesh": ASSET, "was_enabled": was_enabled, "nanite_enabled": bool(mesh.get_editor_property("nanite_settings").enabled), "saved": bool(saved)}
out = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8\Saved\Audits\PressTrains\wrapped_coil_nanite_disabled_v933.json")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
if not saved or result["nanite_enabled"]:
    raise RuntimeError(f"Wrapped coil Nanite repair failed: {out}")
unreal.log(f"LINE_BOSS_WRAPPED_COIL_NANITE_DISABLED_V933_PASS {out}")
