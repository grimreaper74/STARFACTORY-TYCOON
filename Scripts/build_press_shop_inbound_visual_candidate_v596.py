"""Add controlled west-bay lighting and fixed evidence cameras to tested v586.

No process transform, gameplay authority, navigation actor, or protected source
map is changed.  The lighting follows the supplied Pro inbound-cell sheets while
all engineering values remain explicitly TBC.
"""
from pathlib import Path
import hashlib
import json
import unreal

MAP = "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundReleaseCandidate_v596"
ROOT = Path(unreal.Paths.project_dir())
SOURCE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED_SOURCE_HASH = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
OUT = ROOT / "Saved/Audits/PressShopIntegration/inbound_release_visual_build_v596.json"

levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest().upper() != EXPECTED_SOURCE_HASH:
    raise RuntimeError("Protected v438 hash mismatch before visual build")
if not levels.load_level(MAP):
    raise RuntimeError(f"Could not load {MAP}")

tags = [
    unreal.Name("LB.Asset.Candidate.v596"),
    unreal.Name("LB.Asset.CandidateNotPromoted"),
    unreal.Name("LB.Inbound.ProPack.20260808"),
    unreal.Name("LB.Engineering.Values.TBC"),
    unreal.Name("LB.Lighting.WestReceivingBay.v596"),
]

# Two rows of broad, shadow-free industrial luminaires illuminate the lorry,
# crane, saddle and handoff without changing the darker identity of the hall.
light_rows = []
for row, y in enumerate((-2850.0, 50.0), 1):
    for col, x in enumerate((-14800.0, -13200.0, -11600.0, -10000.0, -8400.0, -6800.0), 1):
        light = actors.spawn_actor_from_class(
            unreal.RectLight, unreal.Vector(x, y, 1525.0), unreal.Rotator(0.0, -90.0, 0.0))
        light.set_actor_label(f"LB_INBOUND_V596_HighBay_R{row}_C{col:02d}")
        light.rect_light_component.set_editor_properties({
            "intensity": 4200.0,
            "attenuation_radius": 2350.0,
            "source_width": 1050.0,
            "source_height": 110.0,
            "cast_shadows": False,
            "light_color": unreal.Color(225, 238, 255, 255),
        })
        light.tags = tags
        light_rows.append(light.get_actor_label())

# Soft task lights make the receiving saddle and AGV handoff legible.
for name, loc, intensity, radius in (
    ("ReceivingSaddle", (-11250.0, -2000.0, 780.0), 1700.0, 1500.0),
    ("AGVHandoff", (-10650.0, -2000.0, 720.0), 1500.0, 1400.0),
):
    light = actors.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(*loc), unreal.Rotator(0.0, -90.0, 0.0))
    light.set_actor_label(f"LB_INBOUND_V596_TaskLight_{name}")
    light.rect_light_component.set_editor_properties({
        "intensity": intensity,
        "attenuation_radius": radius,
        "source_width": 650.0,
        "source_height": 80.0,
        "cast_shadows": False,
        "light_color": unreal.Color(238, 244, 255, 255),
    })
    light.tags = tags
    light_rows.append(light.get_actor_label())

cameras = []
for label, loc, target, fov in (
    ("LB_CAM_InboundRelease_Process_v596", (-15600.0, 1950.0, 1425.0), (-12200.0, -2000.0, 300.0), 53.0),
    ("LB_CAM_InboundRelease_Handoff_v596", (-10150.0, 1150.0, 1050.0), (-11500.0, -2000.0, 255.0), 49.0),
    ("LB_CAM_InboundRelease_WholeShop_v596", (-15000.0, 5200.0, 3600.0), (-1500.0, -1200.0, 250.0), 58.0),
):
    camera = actors.spawn_actor_from_class(unreal.CameraActor, unreal.Vector(*loc), unreal.Rotator())
    camera.set_actor_label(label)
    camera.set_actor_rotation(
        unreal.MathLibrary.find_look_at_rotation(camera.get_actor_location(), unreal.Vector(*target)), False)
    camera.camera_component.set_editor_properties({
        "field_of_view": fov,
        "aspect_ratio": 16.0 / 9.0,
        "constrain_aspect_ratio": True,
    })
    camera.tags = tags + [unreal.Name("LB.Camera.FixedEvidence")]
    cameras.append(label)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level():
    raise RuntimeError("Failed saving v596")
after_hash = hashlib.sha256(SOURCE_FILE.read_bytes()).hexdigest().upper()
if after_hash != EXPECTED_SOURCE_HASH:
    raise RuntimeError("Protected v438 changed during visual build")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "status": "BUILT__FIXED_CAMERA_VISUAL_GATE_REQUIRED__NOT_PROMOTED",
    "source_candidate": "/Game/LineBoss/Developer/Validation/LB_PressShop_InboundNavConnectedCandidate_v586",
    "candidate_map": MAP,
    "protected_v438_sha256": after_hash,
    "high_bay_and_task_light_count": len(light_rows),
    "lights": light_rows,
    "fixed_evidence_cameras": cameras,
    "process_or_authority_transforms_changed": False,
    "engineering_values": "TBC",
    "promotion_authorized": False,
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_INBOUND_RELEASE_VISUAL_BUILD_V596_PASS")
