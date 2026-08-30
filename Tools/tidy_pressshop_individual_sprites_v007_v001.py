"""Hide legacy placeholder tenders and cube beacons in the v007 presentation map."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007/Maps/LB_PressShop_Factorio2p5D_IndividualSprites_v007"
SOURCE_V006 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v006_TopdownSprite" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v006_TopdownSprite.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_IndividualSprites_v007" / "Maps" / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap"
PROTECTED_MAPS = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_individual_sprites_v007_presentation_tidy.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def hide(actor):
    if isinstance(actor, unreal.StaticMeshActor):
        actor.static_mesh_component.set_visibility(False, True)
        actor.static_mesh_component.set_editor_property("cast_shadow", False)
    actor.set_actor_hidden_in_game(True)


if not TARGET_FILE.is_file() or not SOURCE_V006.is_file():
    raise RuntimeError("PRESSSHOP_V007_TIDY_FAIL: candidate or source map missing")
for path, expected in PROTECTED_MAPS.items():
    if not path.is_file() or digest(path) != expected:
        raise RuntimeError("PRESSSHOP_V007_TIDY_FAIL: protected map changed")
before = {"v006_source": digest(SOURCE_V006)}
before.update({str(path): digest(path) for path in PROTECTED_MAPS})
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("PRESSSHOP_V007_TIDY_FAIL: could not load v007")
hidden = []
for actor in unreal.EditorLevelLibrary.get_all_level_actors():
    label = actor.get_actor_label()
    if label.startswith("2.5D full | robotic tender ") or label.startswith("2.5D full | status beacon "):
        hide(actor)
        hidden.append(label)
if len(hidden) != 12:
    raise RuntimeError("PRESSSHOP_V007_TIDY_FAIL: expected 12 legacy placeholders, hid {}".format(len(hidden)))
if not unreal.EditorLevelLibrary.save_current_level():
    raise RuntimeError("PRESSSHOP_V007_TIDY_FAIL: could not save v007")
after = {"v006_source": digest(SOURCE_V006)}
after.update({str(path): digest(path) for path in PROTECTED_MAPS})
if before != after:
    raise RuntimeError("PRESSSHOP_V007_TIDY_FAIL: source or protected evidence changed")
record = {"status": "PASS__V007_LEGACY_PLACEHOLDERS_HIDDEN_NOT_DELETED", "map": MAP, "hidden_labels": sorted(hidden), "replacement": "individual detailed machine cards and four overhead-transfer robot cards", "source_and_protected_unchanged_before_after": True, "target_sha256": digest(TARGET_FILE)}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_V007_PRESENTATION_TIDY_PASS=" + json.dumps(record, sort_keys=True))
