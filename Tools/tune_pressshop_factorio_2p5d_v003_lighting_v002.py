"""Bring the 2.5D proof down from the deliberately over-bright light probe."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_v003/Maps/LB_PressShop_Factorio2p5D_v003"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_factorio_2p5d_v003_lighting_tune_v002.json"
PROTECTED = PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap"
V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap"


def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


before = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load 2.5D candidate")
lights = sorted((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label().startswith("2.5D | flat key fixture ")), key=lambda actor: actor.get_actor_label())
if len(lights) != 6:
    raise RuntimeError("expected six prior 2.5D fixtures, found %d" % len(lights))
for index, actor in enumerate(lights, start=1):
    component = actor.get_component_by_class(unreal.RectLightComponent)
    component.set_editor_property("intensity", 5000.0 if index <= 3 else 2200.0)
post = next((actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == "2.5D | fixed high-key exposure"), None)
if not isinstance(post, unreal.PostProcessVolume):
    raise RuntimeError("high-key post-process volume missing")
settings = post.get_editor_property("settings")
settings.override_auto_exposure_bias = True
settings.auto_exposure_bias = 0.25
post.set_editor_property("settings", settings)
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("could not save 2.5D lighting tune")
after = {"v438": sha256(PROTECTED), "v002": sha256(V002)}
if before != after:
    raise RuntimeError("protected map changed during 2.5D lighting tune")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__2P5D_LIGHTING_TUNED_FOR_DETAIL_READABILITY",
    "map": MAP,
    "front_fixture_lumens": 5000.0,
    "rear_fixture_lumens": 2200.0,
    "fixed_exposure_bias": 0.25,
    "protected_hashes_before": before,
    "protected_hashes_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FACTORIO_2P5D_LIGHTING_TUNE_V002_PASS")
