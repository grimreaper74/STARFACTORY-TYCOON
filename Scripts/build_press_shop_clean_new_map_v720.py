"""Create the clean Press Shop rebuild from an empty level; no legacy actors or assets are copied."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, unreal

ROOT = Path(unreal.Paths.project_dir())
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanMeshyBuild_v720"
OUT = ROOT / "Saved/Audits/PressShopIntegration/press_shop_clean_new_map_build_v720.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
assets = unreal.EditorAssetLibrary
cube = unreal.load_asset("/Engine/BasicShapes/Cube.Cube")
if OUT.exists() or assets.does_asset_exist(MAP):
    raise RuntimeError("Refusing overwrite of clean v720 map")
if hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper() != EXPECTED:
    raise RuntimeError("Protected v438 hash mismatch before clean build")
if not levels.new_level(MAP):
    raise RuntimeError("Could not create empty clean Press Shop map")

created = []
def mesh_actor(label, location, scale, tags):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    a.set_actor_label(label)
    a.tags = [unreal.Name(t) for t in tags + ["LB.PressShop.CleanNewBuild.v720", "LB.Asset.NewAuthored"]]
    c = a.static_mesh_component
    c.set_static_mesh(cube)
    c.set_world_scale3d(unreal.Vector(*scale))
    c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS)
    c.set_editor_property("can_ever_affect_navigation", True)
    created.append(a)
    return a

# New simple hall shell: 100 cm cube scale basis. Floor top is Z=0.
mesh_actor("LB_NEW_Floor_Main", (4000, -1000, -25), (140, 120, 0.5), ["LB.Environment.Floor"])
mesh_actor("LB_NEW_Wall_North", (4000, 5000, 700), (140, 0.5, 14), ["LB.Environment.Wall"])
mesh_actor("LB_NEW_Wall_South", (4000, -7000, 700), (140, 0.5, 14), ["LB.Environment.Wall"])
mesh_actor("LB_NEW_Wall_West", (-3000, -1000, 700), (0.5, 120, 14), ["LB.Environment.Wall"])
mesh_actor("LB_NEW_Wall_East", (11000, -1000, 700), (0.5, 120, 14), ["LB.Environment.Wall"])
for x in range(-3000, 11001, 2000):
    for y in (-7000, 5000):
        mesh_actor(f"LB_NEW_Column_{x}_{y}", (x, y, 650), (0.35, 0.35, 13), ["LB.Environment.Column"])
for x in range(-3000, 11001, 2000):
    mesh_actor(f"LB_NEW_RoofBeam_{x}", (x, -1000, 1300), (0.30, 120, 0.30), ["LB.Environment.RoofStructure"])

datums = {"TRAIN_A": (1600, -4300, 0), "TRAIN_B": (1600, -2100, 0), "TRAIN_C": (1600, 100, 0), "TRAIN_D": (1600, 2300, 0)}
for train, (x, y, z) in datums.items():
    marker = mesh_actor(f"LB_NEW_Datum_{train}", (x, y, 2), (1.5, 0.05, 0.04), [f"LB.PressTrain.Datum.{train}", "LB.Presentation.DatumMarker"])
    marker.set_actor_rotation(unreal.Rotator(0, -90, 0), False)

sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 1000), unreal.Rotator(-55, -35, 0))
sun.set_actor_label("LB_NEW_Light_Directional")
sun.tags = [unreal.Name("LB.PressShop.CleanNewBuild.v720"), unreal.Name("LB.Asset.NewAuthored")]
sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 4.0)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 1100), unreal.Rotator())
sky.set_actor_label("LB_NEW_Light_Sky")
sky.tags = [unreal.Name("LB.PressShop.CleanNewBuild.v720"), unreal.Name("LB.Asset.NewAuthored")]
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 1.0)
for x in (-1000, 2000, 5000, 8000):
    for y in (-5200, -3000, -800, 1400, 3600):
        light = actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x, y, 1150), unreal.Rotator(-90, 0, 0))
        light.set_actor_label(f"LB_NEW_Light_{x}_{y}")
        light.tags = [unreal.Name("LB.PressShop.CleanNewBuild.v720"), unreal.Name("LB.Asset.NewAuthored")]
        c = light.get_component_by_class(unreal.RectLightComponent)
        c.set_editor_property("intensity", 16000.0); c.set_editor_property("source_width", 900.0); c.set_editor_property("source_height", 180.0)

if not levels.save_current_level():
    raise RuntimeError("Could not save clean v720 map")
all_actors = actors.get_all_level_actors()
legacy = []
for a in all_actors:
    comp = a.get_component_by_class(unreal.StaticMeshComponent)
    if comp and comp.static_mesh:
        p = comp.static_mesh.get_path_name()
        if not p.startswith("/Engine/BasicShapes/"):
            legacy.append({"actor": a.get_actor_label(), "mesh": p})
after = hashlib.sha256(PROTECTED.read_bytes()).hexdigest().upper()
if legacy or after != EXPECTED:
    raise RuntimeError(f"Clean-map invariant failed: legacy={len(legacy)} protected={after}")
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({
    "revision": "v720", "generated_utc": datetime.now(timezone.utc).isoformat(),
    "status": "PASS__EMPTY_LEVEL_ORIGIN__NEW_AUTHORED_SHELL_ONLY__NO_LEGACY_ASSET_REFERENCES__FOUR_WIDENED_DATUMS",
    "map": MAP, "actor_count": len(all_actors), "new_authored_actor_count": len(all_actors),
    "legacy_asset_reference_count": len(legacy), "train_datums_cm": datums,
    "protected_v438_hash_before": EXPECTED, "protected_v438_hash_after": after,
    "meshy_credits_used": 0
}, indent=2), encoding="utf-8")
unreal.log("LINE_BOSS_PRESS_SHOP_CLEAN_NEW_MAP_V720_PASS")
