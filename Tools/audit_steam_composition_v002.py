"""Read-only layout census for the roofless Press Shop Steam candidate."""

import json
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
TARGET = "/Game/LineBoss/Candidates/PressShop/SquareMeshyPressTrain_v001/Maps/LB_PressShop_SteamComposition_v002"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "steam_composition_v002_layout_census.json"


def vector(value):
    return [round(float(value.x), 2), round(float(value.y), 2), round(float(value.z), 2)]


if not unreal.EditorAssetLibrary.does_asset_exist(TARGET):
    raise RuntimeError("STEAM_COMPOSITION_V002_CENSUS_FAIL: candidate map is missing")
if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET):
    raise RuntimeError("STEAM_COMPOSITION_V002_CENSUS_FAIL: cannot load candidate map")

actors = unreal.EditorLevelLibrary.get_all_level_actors()
rows = []
for actor in actors:
    label = actor.get_actor_label()
    centre, extent = actor.get_actor_bounds(False)
    meshes = []
    for component in actor.get_components_by_class(unreal.StaticMeshComponent):
        mesh = component.get_editor_property("static_mesh")
        if mesh:
            meshes.append(mesh.get_path_name())
    rows.append({
        "label": label,
        "class": actor.get_class().get_name(),
        "location_cm": vector(actor.get_actor_location()),
        "bounds_centre_cm": vector(centre),
        "bounds_extent_cm": vector(extent),
        "mesh_paths": sorted(set(meshes)),
    })

rows.sort(key=lambda row: row["label"].lower())
terms = ("roof", "ceiling", "liner", "wall", "crane", "lorry", "truck", "coil", "agv", "camera", "light")
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps({
    "status": "PASS__READ_ONLY_STEAM_COMPOSITION_V002_CENSUS",
    "target": TARGET,
    "actor_count": len(rows),
    "actors": rows,
    "named_candidates": [row for row in rows if any(term in row["label"].lower() for term in terms)],
    "honest_status": "read-only layout evidence; candidate map not changed",
}, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("STEAM_COMPOSITION_V002_CENSUS=" + str(REPORT))
