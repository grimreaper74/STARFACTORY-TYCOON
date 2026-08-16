"""Make all clean paint presentation-only and rebuild full-shop dynamic nav in a fresh child."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNav_v20260809_v038"
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavPaintFix_v20260809_v043"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_paint_collision_nav_repair_v20260809_v043.json"
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
    raise RuntimeError("map child failed")

fixed = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label().startswith("LB_PAINT_") and isinstance(actor, unreal.StaticMeshActor):
        comp = actor.static_mesh_component
        comp.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        comp.set_collision_profile_name("NoCollision")
        fixed.append(actor.get_actor_label())

recasts = [a for a in actors.get_all_level_actors() if isinstance(a, unreal.RecastNavMesh)]
for recast in recasts:
    recast.set_editor_property("runtime_generation", unreal.RuntimeGenerationType.DYNAMIC)
    recast.set_editor_property("can_be_main_nav_data", True)
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
if not levels.save_current_level():
    raise RuntimeError("save failed")
after = sha(PROTECTED)
if after != before:
    raise RuntimeError("protected map changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavPaintFix_v20260809_v043.umap"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_REPAIR__ALL_PAINT_NO_COLLISION__DYNAMIC_RECAST_REQUESTED__PIE_REPEAT_REQUIRED__NOT_PROMOTED",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "source": SOURCE, "map": MAP, "map_sha256": sha(map_file),
    "paint_actor_count": len(fixed), "paint_actors": fixed,
    "recast_count": len(recasts), "meshy_credits_used": 0,
    "protected_v438_before": before, "protected_v438_after": after
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_PAINT_COLLISION_NAV_V043_PASS")
