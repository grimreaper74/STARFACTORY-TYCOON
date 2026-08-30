"""Configure only the isolated 2126 full-hall map after the duplication pass."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
MAP_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_FullHall_v001" / "Maps" / "LB_PressShop_2126_FullHall_v001.umap"
BASELINE_SHA256 = "3f972aa8788c1e7b062f349c3e3e6236431520b75c167dc75223eb059809de06"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_FullFactoryRestored_v001.umap"
SOURCE_SHA256 = "d3f8652aa45e7c2fcee5af1971f6aa78a3f027e60e361b039d14dad5806c74a5"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "configure_fullhall_v001_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map missing or changed: {}".format(path))
if digest(SOURCE_FILE) != SOURCE_SHA256:
    raise RuntimeError("restored foundation changed")
if digest(MAP_FILE) != BASELINE_SHA256:
    raise RuntimeError("full-hall candidate does not match duplication receipt")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated full-hall candidate")

actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
hidden_roof_liners = []
for actor in actors:
    label = actor.get_actor_label()
    if "roofliner" in label.lower() or "roof liner" in label.lower():
        actor.set_actor_hidden_in_game(True)
        try:
            actor.set_is_temporarily_hidden_in_editor(True)
        except Exception:
            pass
        hidden_roof_liners.append(label)

existing_camera = next((a for a in actors if a.get_actor_label() == "CAM | 2126 full hall fixed game view"), None)
if existing_camera is not None:
    raise RuntimeError("fixed 2126 camera already exists")
camera = unreal.EditorLevelLibrary.spawn_actor_from_class(
    unreal.CameraActor,
    unreal.Vector(-8025.0, -13160.0, 25980.0),
    unreal.Rotator(-60.0, 57.63, 0.0),
)
camera.set_actor_label("CAM | 2126 full hall fixed game view")
camera.camera_component.projection_mode = unreal.CameraProjectionMode.ORTHOGRAPHIC
camera.camera_component.ortho_width = 26000.0
camera.camera_component.constrain_aspect_ratio = True
camera.camera_component.aspect_ratio = 16.0 / 9.0

marker = unreal.EditorLevelLibrary.spawn_actor_from_class(unreal.TargetPoint, unreal.Vector(0.0, -500.0, 0.0), unreal.Rotator())
marker.set_actor_label("IF | 2126 full hall camera target")

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save configured full-hall candidate")
after = {str(path): digest(path) for path in PROTECTED}
if after != before or digest(SOURCE_FILE) != SOURCE_SHA256:
    raise RuntimeError("a protected or foundation map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__FULLHALL_CONFIGURED",
    "candidate_map": MAP,
    "candidate_sha256": digest(MAP_FILE),
    "foundation_sha256": SOURCE_SHA256,
    "actor_count": len(unreal.EditorLevelLibrary.get_all_level_actors()),
    "roof_liner_actor_count_hidden": len(hidden_roof_liners),
    "roof_liner_examples": hidden_roof_liners[:40],
    "fixed_camera": {"label": camera.get_actor_label(), "location_cm": [-8025.0, -13160.0, 25980.0], "rotation": [-60.0, 57.63, 0.0], "orthographic_width_cm": 26000.0},
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2126_FULLHALL_CONFIGURE_PASS {}".format(RECEIPT))
unreal.SystemLibrary.quit_editor()
