"""Add CCTV-legible south-facing identity to the existing PR-009 guard panel."""

import json
from datetime import datetime, timezone
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
PARENT_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceCameraCandidate_v090"
TARGET_MAP = "/Game/LineBoss/Maps/LB_PressShop_PR009ServiceIdentityCandidate_v091"
OUT = ROOT / "Saved/Audits/PR009_InMap_v091/service_identity_build.json"
PREFIX = "LB_PR009_V091_SERVICE_IDENTITY_"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)

if not lib.does_asset_exist(TARGET_MAP):
    if not lib.duplicate_asset(PARENT_MAP, TARGET_MAP):
        raise RuntimeError(PARENT_MAP)
    if not lib.save_asset(TARGET_MAP, only_if_is_dirty=False):
        raise RuntimeError(TARGET_MAP)
    unreal.log("PR009_V091_MAP_DUPLICATED__RERUN_FOR_SERVICE_IDENTITY")
    unreal.SystemLibrary.quit_editor()
    raise SystemExit
if not levels.load_level(TARGET_MAP):
    raise RuntimeError(TARGET_MAP)

for actor in actors_api.get_all_level_actors():
    if "V090" in actor.get_actor_label():
        actor.set_actor_label(actor.get_actor_label().replace("V090", "V091"))
    actor.tags = [unreal.Name(str(tag).replace("v090", "v091")) for tag in actor.tags]
for actor in list(actors_api.get_all_level_actors()):
    if actor.get_actor_label().startswith(PREFIX):
        actors_api.destroy_actor(actor)

def text(label, value, location, world_size, colour):
    actor = actors_api.spawn_actor_from_class(
        unreal.TextRenderActor, unreal.Vector(*location), unreal.Rotator(yaw=-90.0))
    actor.set_actor_label(PREFIX + label)
    actor.tags = [
        unreal.Name("LB.Asset.Candidate.v091"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
        unreal.Name("LB.Identity.CairnwellMoorcross"),
        unreal.Name("LB.Identity.ServiceSide.CCTVLegible"),
        unreal.Name("LB.Navigation.Neutral"),
    ]
    component = actor.text_render
    component.set_text(value)
    component.set_world_size(world_size)
    component.set_text_render_color(colour)
    component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
    component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("can_ever_affect_navigation", False)
    return actor

# Existing panel centre is (600,-1738.5,165), size 210x3x58 cm.  The south
# face is near y=-1740; place text just outside it to avoid z-fighting.
identity = [
    text("Corporation", "CAIRNWELL AUTOMOTIVE", (600.0, -1741.2, 180.0), 8.2, unreal.Color(70,220,165,255)),
    text("Site", "MOORCROSS WORKS", (600.0, -1741.2, 165.0), 7.0, unreal.Color(228,235,230,255)),
    text("Station", "PR-009  AUTOMATED BLANK STACKER", (600.0, -1741.2, 150.0), 5.4, unreal.Color(242,195,0,255)),
]
flows = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPressShopMaterialFlowController)]
pr008 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR008Station)]
pr009 = [actor for actor in actors_api.get_all_level_actors() if isinstance(actor, unreal.LBPR009Station)]
if len(flows) != 1 or len(pr008) != 1 or len(pr009) != 1:
    raise RuntimeError(f"Authority cardinality changed: flow={len(flows)} PR008={len(pr008)} PR009={len(pr009)}")
flows[0].bind_blank_stations(pr008[0], pr009[0])
if not levels.save_current_level():
    raise RuntimeError(TARGET_MAP)

payload = {
    "$schema": "cairnwell/audit/pr009-service-identity-build-v091/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "V091_TWO_SIDED_CCTV_LEGIBLE_CAIRNWELL_MOORCROSS_IDENTITY_BUILT__EARLY_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "parent_map": PARENT_MAP,
    "target_map": TARGET_MAP,
    "identity": [{"label": actor.get_actor_label(), "text": str(actor.text_render.text), "location_cm": [actor.get_actor_location().x,actor.get_actor_location().y,actor.get_actor_location().z], "world_size": actor.text_render.world_size} for actor in identity],
    "line_boss_in_world": False,
    "existing_panel_reused": True,
    "new_plate_added": False,
    "collision_changed": False,
    "navigation_changed": False,
    "process_geometry_changed": False,
    "parent_v090_modified": False,
    "pr010_started": False,
    "robots_modified": False,
    "promotion_authorized": False,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
unreal.log(f"PR009_V091_SERVICE_IDENTITY_BUILD_PASS output={OUT}")
unreal.SystemLibrary.quit_editor()
