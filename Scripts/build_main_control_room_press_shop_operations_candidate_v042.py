"""Install the native Press Shop operations terminal into an isolated v041 successor."""

import json
from datetime import datetime, timezone
from pathlib import Path

import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_MainControlRoom_PR004CCTVDormantCandidate_v041"
MAP = "/Game/LineBoss/Maps/LB_MainControlRoom_PressShopOperationsCandidate_v042"
OUT = ROOT / "Saved/Audits/ControlRoom/main_control_room_press_shop_operations_build_v042.json"

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors_api = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if library.does_asset_exist(MAP):
    raise RuntimeError(f"refusing to overwrite {MAP}")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError(f"could not derive {MAP} from {BASE}")

failures = []
console_class = unreal.load_class(None, "/Script/LineBossCarFactory.LBControlRoomOperationsConsole")
if console_class is None:
    raise RuntimeError("compiled operations-console class is unavailable")

location = unreal.Vector(182.805, -90.047, 147.337)
rotation = unreal.Rotator(-12.0, 98.786, 0.0)
console = actors_api.spawn_actor_from_class(console_class, location, rotation)
if console is None:
    raise RuntimeError("could not spawn operations console")
console.set_actor_label("LB_MCR_V042_PRESS_SHOP_OPERATIONS_CONSOLE")
console.tags = [
    unreal.Name("LB.ControlRoom.v042"),
    unreal.Name("LB.ControlRoom.PressShopOperations"),
    unreal.Name("LB.Authority.PlanningOnly"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
]

screen_material = library.load_asset(
    "/Game/LineBoss/Candidates/ControlRoom/MainControlRoom_v002/Materials/M_CA_ScreenDark_R_v002")
screen_back = console.get_editor_property("screen_back")
if screen_material is None or screen_back is None:
    failures.append("screen material or native screen-back component unavailable")
else:
    screen_back.set_material(0, screen_material)

camera_specs = {
    "StandingOperations": (
        unreal.Vector(0.0, 42.0, 168.0),
        unreal.Vector(182.805, -90.047, 148.0),
        72.0,
    ),
    "OperationsScreenClose": (
        unreal.Vector(82.0, -18.0, 158.0),
        unreal.Vector(182.805, -90.047, 148.0),
        52.0,
    ),
}
for name, (camera_location, target, fov) in camera_specs.items():
    camera = actors_api.spawn_actor_from_class(unreal.CameraActor, camera_location, unreal.Rotator())
    if camera is None:
        failures.append(f"could not spawn {name} camera")
        continue
    camera.set_actor_label(f"LB_MCR_V042_CAM_{name}")
    camera.set_actor_rotation(unreal.MathLibrary.find_look_at_rotation(camera_location, target), False)
    camera.camera_component.set_editor_property("field_of_view", fov)
    camera.tags = [
        unreal.Name("LB.ControlRoom.v042"),
        unreal.Name(f"LB.ControlRoom.Camera.{name}"),
        unreal.Name("LB.Asset.CandidateNotPromoted"),
    ]

actors = actors_api.get_all_level_actors()
operations = [a for a in actors if a.get_class().get_name() == "LBControlRoomOperationsConsole"]
starts = [a for a in actors if a.get_class().get_name() == "PlayerStart"]
pr004_consoles = [a for a in actors if a.get_class().get_name() == "LBControlRoomPR004Console"]
cctv_feeds = [a for a in actors if a.get_class().get_name() == "LBControlRoomCCTVFeed"]
if len(operations) != 1: failures.append(f"expected one operations console, found {len(operations)}")
if len(starts) != 1: failures.append(f"expected one standing-first PlayerStart, found {len(starts)}")
if len(pr004_consoles) != 1: failures.append(f"expected one preserved PR-004 console, found {len(pr004_consoles)}")
if len(cctv_feeds) != 1: failures.append(f"expected one preserved CCTV feed, found {len(cctv_feeds)}")

levels.save_current_level()
payload = {
    "$schema": "cairnwell/audit/main-control-room-press-shop-operations-build-v042/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__ISOLATED_PRESS_SHOP_OPERATIONS_VERTICAL_SLICE_BUILT__RUNTIME_VISUAL_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__CONTROL_ROOM_OPERATIONS_BUILD__NOT_PROMOTED",
    "source_map": BASE,
    "map": MAP,
    "operations_console_count": len(operations),
    "standing_first_player_start_count": len(starts),
    "preserved_pr004_console_count": len(pr004_consoles),
    "preserved_dormant_cctv_count": len(cctv_feeds),
    "screen_location_cm": [location.x, location.y, location.z],
    "screen_rotation_deg": [rotation.pitch, rotation.yaw, rotation.roll],
    "authority_policy": {
        "planning_state": "native and saveable",
        "machine_execution": "existing PR-005 authority only",
        "recipe_catalogue": "explicit runtime hold until authoritative integration",
        "coil_inventory": "explicit runtime hold until authoritative integration",
        "panel_counts": "external authoritative event endpoint; no presentation-time fabrication",
    },
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2), encoding="utf-8")
if failures:
    raise RuntimeError("; ".join(failures))
print(json.dumps({"status": payload["status"], "map": MAP, "audit": str(OUT)}, indent=2))
