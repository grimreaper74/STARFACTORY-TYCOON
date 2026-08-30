"""Read-only audit of candidate Press Shop foundation maps. Never saves a map."""
import hashlib
import json
from collections import Counter
from pathlib import Path

import unreal

PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
OUT = PROJECT / "Saved" / "Audits" / "PressShop2126" / "fullhall_foundation_audit_v001.json"
MAPS = [
    "/Game/LineBoss/Maps/LB_PressShop_FullFactoryRestored_v001",
    "/Game/LineBoss/Maps/LB_PressShop_RebuildFromLorry_v20260810_v913",
    "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007/Maps/LB_PressShop_Factorio2p5D_IndividualSprites_v007",
]
PROTECTED = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def asset_path(actor):
    try:
        comp = actor.static_mesh_component
        mesh = comp.static_mesh if comp else None
        return mesh.get_path_name() if mesh else ""
    except Exception:
        return ""


def bounds_for(actors):
    points = []
    for actor in actors:
        try:
            origin, extent = actor.get_actor_bounds(False, False)
            if extent.x + extent.y + extent.z <= 1.0:
                continue
            points.append((origin, extent))
        except Exception:
            pass
    if not points:
        return None
    lo = [min(getattr(o, axis) - getattr(e, axis) for o, e in points) for axis in ("x", "y", "z")]
    hi = [max(getattr(o, axis) + getattr(e, axis) for o, e in points) for axis in ("x", "y", "z")]
    return {"min_cm": [round(v, 2) for v in lo], "max_cm": [round(v, 2) for v in hi], "size_cm": [round(hi[i] - lo[i], 2) for i in range(3)]}


before = {str(path): digest(path) for path in PROTECTED}
for path, expected in PROTECTED.items():
    if before[str(path)] != expected:
        raise RuntimeError("protected map changed before audit: {}".format(path))

report = {"status": "PASS", "maps": [], "protected_sha256_before": before}
for map_path in MAPS:
    if not unreal.EditorLoadingAndSavingUtils.load_map(map_path):
        report["maps"].append({"map": map_path, "status": "LOAD_FAILED"})
        continue
    actors = list(unreal.EditorLevelLibrary.get_all_level_actors())
    classes = Counter(actor.get_class().get_name() for actor in actors)
    meshes = Counter(filter(None, (asset_path(actor) for actor in actors)))
    labels = [actor.get_actor_label() for actor in actors]
    cameras = []
    for actor in actors:
        if isinstance(actor, unreal.CameraActor):
            loc = actor.get_actor_location()
            rot = actor.get_actor_rotation()
            cameras.append({
                "label": actor.get_actor_label(),
                "location_cm": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)],
                "rotation": [round(rot.pitch, 2), round(rot.yaw, 2), round(rot.roll, 2)],
            })
    keywords = {}
    for key in ("lorry", "truck", "agv", "coil", "press", "train", "pallet", "stillage", "conveyor", "robot", "camera", "light"):
        matches = [label for label in labels if key in label.lower()]
        keywords[key] = {"count": len(matches), "examples": matches[:30]}
    report["maps"].append({
        "map": map_path,
        "status": "LOADED",
        "actor_count": len(actors),
        "bounds": bounds_for(actors),
        "class_counts": dict(classes.most_common(30)),
        "camera_actors": cameras,
        "keyword_labels": keywords,
        "top_static_mesh_assets": [{"asset": asset, "instances": count} for asset, count in meshes.most_common(80)],
    })

after = {str(path): digest(path) for path in PROTECTED}
if after != before:
    raise RuntimeError("protected map changed during read-only audit")
report["protected_sha256_after"] = after
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_FULLHALL_FOUNDATION_AUDIT_PASS {}".format(OUT))
unreal.SystemLibrary.quit_editor()
