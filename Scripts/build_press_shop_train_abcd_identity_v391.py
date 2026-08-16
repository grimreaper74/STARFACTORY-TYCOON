"""Fresh v386 child adding distinct, visual-only A-D line identity at both ends."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import unreal

ROOT = Path(unreal.Paths.project_dir())
BASE = "/Game/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386"
BASE_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_TrainBalancedLightingCandidate_v386.umap"
BASE_SHA = "057F2D9F382EB34DAC7E8727E3E58FEA4194C99E16F339F016116533B8377038"
MAP = "/Game/LineBoss/Maps/LB_PressShop_MountedTrainIdentityCandidate_v393"
MAP_FILE = ROOT / "Content/LineBoss/Maps/LB_PressShop_MountedTrainIdentityCandidate_v393.umap"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_mounted_train_identity_build_v393.json"
ROWS = {"A": -4300.0, "B": -2100.0, "C": 100.0, "D": 2300.0}

def sha(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()

library = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
if sha(BASE_FILE) != BASE_SHA:
    raise RuntimeError("protected v386 base drift")
if library.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("refusing to overwrite preserved v391")
if not levels.new_level_from_template(MAP, BASE):
    raise RuntimeError("fresh v386 child failed")

board_mesh = library.load_asset("/Engine/BasicShapes/Cube.Cube")
board_material = library.load_asset("/Game/LineBoss/Stations/Press/PR009/Presentation_v086/Materials/M_CA_MW_PR009_LayeredFoundryCharcoal_v086")
if not isinstance(board_mesh, unreal.StaticMesh) or not isinstance(board_material, unreal.MaterialInterface):
    raise RuntimeError("retained sign substrate missing")

added = []
boards = []
for train, y_value in ROWS.items():
    for end, board_x, text_x, yaw in (("WEST", 1075.0, 1068.0, 0.0), ("EAST", 6825.0, 6832.0, 180.0)):
        board_label = f"LB_V393_IDENTITY_BOARD_PRESS_TRAIN_{train}_{end}"
        board = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(board_x, y_value, 900.0), unreal.Rotator())
        if board is None:
            raise RuntimeError(f"could not spawn {board_label}")
        board.set_actor_label(board_label)
        board.static_mesh_component.set_static_mesh(board_mesh)
        board.set_actor_scale3d(unreal.Vector(0.05, 2.4, 0.72))
        board.static_mesh_component.set_material(0, board_material)
        board.static_mesh_component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        board.static_mesh_component.set_editor_property("generate_overlap_events", False)
        board.static_mesh_component.set_editor_property("can_ever_affect_navigation", False)
        board.tags = [unreal.Name("LB.Identity.PhysicalPresentationBoard"), unreal.Name("LB.Collision.NoCollision.VisualOnly"), unreal.Name("LB.Navigation.None"), unreal.Name("LB.Asset.Candidate.v393"), unreal.Name("LB.Asset.CandidateNotPromoted")]
        boards.append(board_label)
        label = f"LB_V393_IDENTITY_PRESS_TRAIN_{train}_{end}"
        actor = actors.spawn_actor_from_class(unreal.TextRenderActor, unreal.Vector(text_x, y_value, 900.0), unreal.Rotator(yaw=yaw))
        if actor is None:
            raise RuntimeError(f"could not spawn {label}")
        actor.set_actor_label(label)
        component = actor.text_render
        component.set_text(f"PRESS TRAIN {train}\nS01 - S07")
        component.set_world_size(34.0)
        component.set_text_render_color(unreal.Color(224, 236, 228, 255))
        component.set_horizontal_alignment(unreal.HorizTextAligment.EHTA_CENTER)
        component.set_vertical_alignment(unreal.VerticalTextAligment.EVRTA_TEXT_CENTER)
        component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
        component.set_editor_property("generate_overlap_events", False)
        component.set_editor_property("can_ever_affect_navigation", False)
        actor.tags = [
            unreal.Name(f"LB.PressTrain.Identity.Train{train}"),
            unreal.Name("LB.Identity.VisualOnly.NoRuntimeAuthority"),
            unreal.Name("LB.Collision.NoCollision.VisualOnly"),
            unreal.Name("LB.Navigation.None"),
            unreal.Name("LB.Asset.Candidate.v393"),
            unreal.Name("LB.Asset.CandidateNotPromoted"),
        ]
        added.append({"label": label, "train": train, "end": end, "text": f"PRESS TRAIN {train} / S01-S07", "location_cm": [text_x, y_value, 900.0]})

train_counts = {key: sum(1 for actor in actors.get_all_level_actors() if f"LB.PressTrain.Installed.TRAIN_{key}" in {str(tag) for tag in actor.tags}) for key in "ABCD"}
failures = []
if len(added) != 8:
    failures.append(f"expected eight identities, added {len(added)}")
if len(boards) != 8:
    failures.append(f"expected eight mounted boards, added {len(boards)}")
if train_counts != {"A": 338, "B": 338, "C": 338, "D": 338}:
    failures.append(f"train actor contract changed: {train_counts}")
if not levels.save_current_level():
    failures.append("could not save v391")
if sha(BASE_FILE) != BASE_SHA:
    failures.append("protected v386 changed")

payload = {
    "$schema": "cairnwell/audit/press-shop-mounted-train-identity-build-v393/v1",
    "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__DISTINCT_A_D_MOUNTED_IDENTITY_CANDIDATE__FRESH_VISUAL_AND_RUNTIME_GATES_REQUIRED__NOT_PROMOTED" if not failures else "FAIL__V393_NOT_A_PARENT",
    "base": BASE,
    "base_sha256": BASE_SHA,
    "map": MAP,
    "map_sha256": sha(MAP_FILE) if MAP_FILE.exists() else None,
    "added_visual_only_identity": added,
    "added_visual_only_mounting_boards": boards,
    "train_actor_counts": train_counts,
    "unchanged_contracts": ["materials", "lighting", "geometry", "transforms", "collision", "navigation", "runtime authority", "production state", "save authority"],
    "promotion_authorized": False,
    "failures": failures,
}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
print(json.dumps(payload, indent=2))
if failures:
    raise RuntimeError("; ".join(failures))
unreal.SystemLibrary.quit_editor()
