"""Swap the v003 S02 plane to the locked steep-overhead visible-art master."""
import hashlib
import json
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_Full_v003_OverheadSprites/Maps/LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites"
SOURCE_V002 = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v002_SpriteArt" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v002_SpriteArt.umap"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_Full_v003_OverheadSprites" / "Maps" / "LB_PressShop_Factorio2p5D_Full_v003_OverheadSprites.umap"
MATERIAL = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_v002/Materials/M_LB_PS_S02_DrawForm_SpriteMasterOverhead_Keyed_Unlit_v002"
SPRITE_LABEL = "2.5D sprite art | S02 draw-form portal press"
PROTECTED = {
    "v438": PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap",
    "steam_v002": PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap",
}
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_2d_s02_overhead_master_mount_v002.json"

def fail(message):
    raise RuntimeError("PRESSSHOP_2D_S02_OVERHEAD_MASTER_MOUNT_FAIL: " + message)

def sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()

if not TARGET_FILE.is_file() or not SOURCE_V002.is_file() or any(not path.is_file() for path in PROTECTED.values()):
    fail("candidate, source proof or protected evidence is missing")
material = unreal.load_asset(MATERIAL)
if not isinstance(material, unreal.Material):
    fail("locked overhead master material is missing")
before = {"source_v002": sha256(SOURCE_V002)}
before.update({name: sha256(path) for name, path in PROTECTED.items()})
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    fail("could not load v003 overhead sprite candidate")
matches = [actor for actor in unreal.EditorLevelLibrary.get_all_level_actors() if actor.get_actor_label() == SPRITE_LABEL]
if len(matches) != 1 or not isinstance(matches[0], unreal.StaticMeshActor):
    fail("expected one existing S02 sprite plane, found {}".format(len(matches)))
sprite = matches[0]
component = sprite.static_mesh_component
component.set_material(0, material)
component.set_world_scale3d(unreal.Vector(11.0, 11.0, 1.0))
component.set_editor_property("cast_shadow", False)
component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save v003 overhead sprite candidate")
after = {"source_v002": sha256(SOURCE_V002)}
after.update({name: sha256(path) for name, path in PROTECTED.items()})
if before != after:
    fail("source proof or protected evidence changed during overhead master mount")
report = {
    "status": "PASS__LOCKED_STEEP_OVERHEAD_S02_MASTER_MOUNTED_IN_V003",
    "map": MAP, "sprite_actor": SPRITE_LABEL,
    "material": material.get_path_name(),
    "sprite_plane_cm": {"width": 1100.0, "height": 1100.0},
    "camera_rule": "steep overhead master; every future visible-art sprite must match its fixed angle",
    "source_proof_and_protected_before": before,
    "source_proof_and_protected_after": after,
    "candidate_map_sha256": sha256(TARGET_FILE),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_2D_S02_OVERHEAD_MASTER_MOUNT_PASS=" + json.dumps(report, sort_keys=True))

