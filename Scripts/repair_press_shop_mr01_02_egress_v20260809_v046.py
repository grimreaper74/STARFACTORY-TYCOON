"""Shift the complete MR01-02 berth east to clear its unique nav obstruction."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
SOURCE = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavPaintFix_v20260809_v043"
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_mr01_02_egress_repair_v20260809_v049.json"
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

labels = {
    "LB_CLEAN_Robot_MR01_02", "LB_CLEAN_Dock_MR01_02",
    "LB_PAINT_DockBay_MR01_02", "LB_PAINT_DockEdge_MR01_02_-180",
    "LB_PAINT_DockEdge_MR01_02_180", "LB_PAINT_DockStop_MR01_02"
}
moved = []
for actor in actors.get_all_level_actors():
    if actor.get_actor_label() in labels:
        old = actor.get_actor_location()
        actor.set_actor_location(unreal.Vector(old.x - 2000.0, old.y, old.z), False, False)
        new = actor.get_actor_location()
        moved.append({"label": actor.get_actor_label(), "before_cm": [old.x,old.y,old.z], "after_cm": [new.x,new.y,new.z]})
if {row["label"] for row in moved} != labels:
    raise RuntimeError({"expected": sorted(labels), "moved": sorted(row["label"] for row in moved)})
world = unreal.EditorLevelLibrary.get_editor_world()
unreal.SystemLibrary.execute_console_command(world, "RebuildNavigation")
if not levels.save_current_level():
    raise RuntimeError("save failed")
after = sha(PROTECTED)
if after != before:
    raise RuntimeError("protected map changed")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanInboundRuntimeNavFleetFix_v20260809_v049.umap"
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "PASS_BUILD__MR01_02_COMPLETE_BERTH_SHIFTED_WEST_2000CM_TO_CLEAR_TRAIN_A_OBSTRUCTION__PIE_REPEAT_REQUIRED__NOT_PROMOTED",
    "generated_utc": datetime.now(timezone.utc).isoformat(), "source": SOURCE, "map": MAP,
    "map_sha256": sha(map_file), "moved": moved, "meshy_credits_used": 0,
    "protected_v438_before": before, "protected_v438_after": after
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_MR01_02_EGRESS_V049_PASS")
