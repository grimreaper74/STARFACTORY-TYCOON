"""Add one full-shop nav volume and the native runtime bootstrap to clean inbound v035."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundFlowFit_v20260809_v035"
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNav_v20260809_v038"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_runtime_navigation_build_v20260809_v038.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest().upper()
before = sha(PROTECTED)
lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if before != EXPECTED or lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("fresh/protected invariant")
if not levels.new_level_from_template(MAP, SOURCE):
    raise RuntimeError("could not create clean navigation child")

for actor in list(actors.get_all_level_actors()):
    if isinstance(actor, unreal.NavMeshBoundsVolume) or actor.get_class().get_name() == "LBPressShopNavigationBootstrap":
        actors.destroy_actor(actor)

nav = actors.spawn_actor_from_class(unreal.NavMeshBoundsVolume, unreal.Vector(0, 0, 500), unreal.Rotator())
nav.set_actor_label("LB_CLEAN_NavBounds_FullPressShop_v038")
nav.set_actor_scale3d(unreal.Vector(110, 60, 5))
nav.tags = [unreal.Name("LB.CleanRebuild.v20260809.v038"), unreal.Name("LB.Navigation.FullPressShop"), unreal.Name("LB.Asset.NewAuthored")]

bootstrap = actors.spawn_actor_from_class(unreal.LBPressShopNavigationBootstrap, unreal.Vector(0, -5200, 20), unreal.Rotator())
bootstrap.set_actor_label("LB_CLEAN_NavigationBootstrap_v038")
bootstrap.tags = [unreal.Name("LB.CleanRebuild.v20260809.v038"), unreal.Name("LB.Navigation.RuntimeAuthority"), unreal.Name("LB.Asset.NewAuthored")]

world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
if not levels.save_current_level():
    raise RuntimeError("save failed")
after = sha(PROTECTED)
if after != before:
    raise RuntimeError("protected map changed")
origin, extent = nav.get_actor_bounds(False)
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNav_v20260809_v038.umap"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_BUILD__FULL_SHOP_NAV_BOUNDS_AND_NATIVE_RUNTIME_BOOTSTRAP__PIE_REQUIRED__NOT_PROMOTED",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE,
    "map": MAP,
    "map_sha256": sha(map_file),
    "nav_bounds_origin_cm": [origin.x, origin.y, origin.z],
    "nav_bounds_size_cm": [extent.x * 2, extent.y * 2, extent.z * 2],
    "bootstrap_class": bootstrap.get_class().get_name(),
    "meshy_credits_used": 0,
    "protected_v438_before": before,
    "protected_v438_after": after
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_RUNTIME_NAV_V038_PASS")
