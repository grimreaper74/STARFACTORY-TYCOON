"""Apply candidate-only flat, readable lighting to the 2.5D press-cell proof."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_v003/Maps/LB_PressShop_Factorio2p5D_v003"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_v003_flat_lighting.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"
TAG = unreal.Name("LB.PressShop.Factorio2p5D.v003.FlatLighting")


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


if not PROTECTED.is_file() or not V002.is_file():
    raise RuntimeError("required protected maps are missing")
before = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load 2.5D candidate")
if any(TAG in actor.tags for actor in unreal.EditorLevelLibrary.get_all_level_actors()):
    raise RuntimeError("flat lighting has already been applied; refusing duplicate pass")

# The 2.5D proof intentionally uses broad, high-key illumination.  This is a
# presentation choice for a fixed gameplay view, not a claim that the prior
# open-air 3D B_stylized calibration is wrong.  Rect lights have no mesh, so
# they create no roof, cables, ceiling grid, or added visual clutter.
fixtures = (
    ((-1550.0, -1200.0, 2200.0), 10000.0),
    ((-450.0, -1200.0, 2200.0), 10000.0),
    ((650.0, -1200.0, 2200.0), 10000.0),
    ((-1300.0, 1000.0, 1900.0), 4500.0),
    ((0.0, 1000.0, 1900.0), 4500.0),
    ((1300.0, 1000.0, 1900.0), 4500.0),
)
placed = []
for index, (position, intensity) in enumerate(fixtures, start=1):
    actor = unreal.EditorLevelLibrary.spawn_actor_from_class(
        unreal.RectLight, unreal.Vector(*position), unreal.Rotator(pitch=-90.0, yaw=0.0, roll=0.0))
    if actor is None:
        raise RuntimeError("could not create flat-light fixture %d" % index)
    actor.set_actor_label("2.5D | flat key fixture %02d" % index)
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("mobility", unreal.ComponentMobility.MOVABLE)
    component.set_editor_property("intensity", intensity)
    component.set_editor_property("attenuation_radius", 4500.0)
    component.set_editor_property("source_width", 430.0)
    component.set_editor_property("source_height", 120.0)
    component.set_editor_property("use_temperature", True)
    component.set_editor_property("temperature", 5300.0)
    actor.tags = [TAG, unreal.Name("LB.Visual.2P5D"), unreal.Name("LB.NoRoofGeometry")]
    placed.append({"location_cm": list(position), "lumens": intensity})

post = next((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == "2.5D | fixed B_stylized exposure"), None)
if not isinstance(post, unreal.PostProcessVolume):
    raise RuntimeError("base 2.5D post-process volume missing")
post.set_actor_label("2.5D | fixed high-key exposure")
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = 1.25
post.set_editor_property("settings", settings)
post.tags = list(post.tags) + [TAG, unreal.Name("LB.Visual.2P5D")]

if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("could not save 2.5D flat-lighting candidate")
after = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
if before != after:
    raise RuntimeError("protected map changed during 2.5D lighting pass")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__2P5D_FLAT_HIGH_KEY_LIGHTING_APPLIED",
    "map": MAP,
    "fixtures": placed,
    "fixed_exposure_bias": 1.25,
    "roof_mesh_created": False,
    "protected_hashes_before": before,
    "protected_hashes_after": after,
    "honest_status": "candidate-only presentation lighting; screenshot review still required",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FACTORIO_2P5D_FLAT_LIGHTING_PASS")
