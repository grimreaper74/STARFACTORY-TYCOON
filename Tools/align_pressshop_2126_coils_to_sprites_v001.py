"""Align separate 3D coil actors to authored cradle/mandrel points on fixed-camera sprite cards."""
import hashlib
import json
from pathlib import Path
import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
MAP = "/Game/LineBoss/Candidates/PressShop/PressShop2126_FullHall_v001/Maps/LB_PressShop_2126_FullHall_v001"
RECEIPT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "align_coils_to_sprites_v001_receipt.json"
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError(f"protected map missing or changed: {path}")
if not unreal.EditorLoadingAndSavingUtils.load_map(MAP):
    raise RuntimeError("could not load isolated 2126 candidate")

actors = {actor.get_actor_label(): actor for actor in unreal.EditorLevelLibrary.get_all_level_actors()}
alignments = [
    {
        "card": "2126 COIL | autonomous verification and de-banding cell",
        "coil": "2126 COIL | verification cell active load",
        "local_plane_point": (-13.54, -9.57, 0.0),
        "z_cm": 175.0,
        "role": "verification cradle A",
    },
    {
        "card": "2126 COIL | magnetic three-position buffer shuttle",
        "coil": "2126 COIL | magnetic buffer load A",
        "local_plane_point": (-16.15, -8.59, 0.0),
        "z_cm": 175.0,
        "role": "buffer cradle A",
    },
    {
        "card": "2126 COIL | magnetic three-position buffer shuttle",
        "coil": "2126 COIL | magnetic buffer load C",
        "local_plane_point": (20.31, 20.70, 0.0),
        "z_cm": 175.0,
        "role": "buffer cradle C",
    },
    {
        "card": "2126 FRONT END | autonomous decoiler straightener and servo feed",
        "coil": "2126 FRONT END | active feed coil",
        "local_plane_point": (-33.07, -22.75, 0.0),
        "z_cm": 175.0,
        "role": "front-end decoiler mandrel",
    },
]

records = []
for spec in alignments:
    card = actors.get(spec["card"])
    coil = actors.get(spec["coil"])
    if not isinstance(card, unreal.StaticMeshActor) or not isinstance(coil, unreal.StaticMeshActor):
        raise RuntimeError(f"missing alignment actor(s): {spec}")
    local = unreal.Vector(*spec["local_plane_point"])
    projected = card.get_actor_transform().transform_location(local)
    target = unreal.Vector(projected.x, projected.y, spec["z_cm"])
    before_location = coil.get_actor_location()
    if not coil.set_actor_location(target, False, False):
        raise RuntimeError(f"failed to align coil: {spec['coil']}")
    records.append({
        "role": spec["role"],
        "card": spec["card"],
        "coil": spec["coil"],
        "local_plane_point": list(spec["local_plane_point"]),
        "before_location_cm": [round(before_location.x, 2), round(before_location.y, 2), round(before_location.z, 2)],
        "after_location_cm": [round(target.x, 2), round(target.y, 2), round(target.z, 2)],
    })

if not unreal.EditorLoadingAndSavingUtils.save_current_level():
    raise RuntimeError("failed to save coil alignment")
unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("a protected map changed")

RECEIPT.parent.mkdir(parents=True, exist_ok=True)
RECEIPT.write_text(json.dumps({
    "status": "PASS__SEPARATE_COILS_ALIGNED_TO_SPRITE_CONTROL_POINTS",
    "candidate_map": MAP,
    "alignments": records,
    "protected_sha256_before": before,
    "protected_sha256_after": after,
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log(f"PRESSSHOP_2126_COIL_ALIGNMENT_PASS count={len(records)} receipt={RECEIPT}")
unreal.SystemLibrary.quit_editor()
