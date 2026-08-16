"""Fresh direct-v269 one-dock technical child with superseded proxy blockers removed."""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

source = Path(__file__).with_name("build_press_shop_mr01_modular_dock_comparison_v270.py")
code = source.read_text(encoding="utf-8").replace("v270", "v272").replace("V270", "V272")
exec(compile(code, str(source) + "::v272", "exec"), globals(), globals())

actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
proxy_labels = [
    "LB-DOCK-MR01-01_Collision_WestSide",
    "LB-DOCK-MR01-01_Collision_EastSide",
    "LB-DOCK-MR01-01_Collision_Rear",
]
removed = []
for label in proxy_labels:
    actor = next((a for a in actors.get_all_level_actors() if a.get_actor_label() == label), None)
    if actor is None or not actors.destroy_actor(actor):
        raise RuntimeError(f"failed to remove superseded proxy {label}")
    removed.append(label)
if not levels.save_current_level():
    raise RuntimeError("failed to save v272 after proxy removal")

project = Path(unreal.Paths.project_dir()).resolve()
map_file = project / "Content/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v272.umap"
digest = hashlib.sha256(map_file.read_bytes()).hexdigest().upper()
audit = Path(unreal.Paths.project_saved_dir()).resolve() / "Audits/SupportRobots/press_shop_mr01_modular_dock_technical_build_v272.json"
audit.parent.mkdir(parents=True, exist_ok=True)
audit.write_text(json.dumps({
    "$schema": "cairnwell/audit/press-shop-mr01-modular-dock-technical-build-v272/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__FRESH_DIRECT_V269_SINGLE_NATIVE_DOCK__SUPERSEDED_PROXY_BLOCKERS_REMOVED__GATES_OPEN__NOT_PROMOTED",
    "map": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v272",
    "map_sha256": digest,
    "parent": "/Game/LineBoss/Maps/LB_PressShop_PlayableManagementCandidate_v269",
    "native_dock": "LB-DOCK-MR01-01",
    "removed_proxy_blockers": removed,
    "retained_control": "LB-DOCK-MR01-02",
    "promotion_authorized": False
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_MR01_MODULAR_DOCK_TECHNICAL_V272_PASS")
