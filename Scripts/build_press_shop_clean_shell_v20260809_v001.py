"""Build a genuinely empty 220 m x 120 m Press Shop shell with new paint assets.

No legacy map is opened or duplicated. This is fixed shell/presentation authority
only; production equipment remains player-built or belongs in a separate review child.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import unreal

ROOT = Path(unreal.Paths.project_dir()).resolve()
MAP = "/Game/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v001"
MAT_DIR = "/Game/LineBoss/Candidates/PressShop/CleanRebuild_v20260809_v001/Materials"
OUT = ROOT / "Saved/Audits/PressShopIntegration/clean_shell_build_v20260809_v001.json"
PROTECTED = ROOT / "Content/LineBoss/Maps/LB_PressShop_BuilderAuthorityCandidate_v438.umap"
EXPECTED = "5029C9D827D9A1D72C12F27EE757C9BC1E47FEBD5006CE6D7BA319AAD2E7FEC8"

lib = unreal.EditorAssetLibrary
levels = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
actors = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary

def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest().upper()
before = sha(PROTECTED)
if before != EXPECTED:
    raise RuntimeError(f"Protected map hash mismatch: {before}")
if lib.does_asset_exist(MAP) or OUT.exists():
    raise RuntimeError("Fresh clean-shell output already exists; refusing overwrite")

def new_material(name, colour, roughness, metallic=0.0):
    path = f"{MAT_DIR}/{name}"
    if lib.does_asset_exist(path):
        raise RuntimeError(f"Fresh material invariant failed: {path}")
    m = tools.create_asset(name, MAT_DIR, unreal.Material, unreal.MaterialFactoryNew())
    base = mel.create_material_expression(m, unreal.MaterialExpressionConstant3Vector, -420, 0)
    base.set_editor_property("constant", unreal.LinearColor(*colour, 1.0))
    rough = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -420, 140)
    rough.set_editor_property("r", roughness)
    metal = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -420, 250)
    metal.set_editor_property("r", metallic)
    mel.connect_material_property(base, "", unreal.MaterialProperty.MP_BASE_COLOR)
    mel.connect_material_property(rough, "", unreal.MaterialProperty.MP_ROUGHNESS)
    mel.connect_material_property(metal, "", unreal.MaterialProperty.MP_METALLIC)
    mel.recompile_material(m)
    lib.save_loaded_asset(m)
    return m

materials = {
    "floor": new_material("M_LB_CleanShell_SealedEpoxyGrey_v001", (0.1329, 0.1470, 0.1559), 0.72),
    "wall": new_material("M_LB_CleanShell_WarmWhite_v001", (0.8879, 0.8796, 0.8148), 0.78),
    "steel": new_material("M_LB_CleanShell_FoundryCharcoal_v001", (0.0144, 0.0176, 0.0202), 0.48, 0.35),
    "walk": new_material("M_LB_CleanShell_WalkwayGreen_v001", (0.0138, 0.0704, 0.0578), 0.66),
    "yellow": new_material("M_LB_CleanShell_SafetyYellow_v001", (0.8879, 0.5420, 0.0), 0.55),
    "red": new_material("M_LB_CleanShell_SignalRed_v001", (0.5711, 0.0356, 0.0262), 0.58),
    "white": new_material("M_LB_CleanShell_MarkingWhite_v001", (0.8963, 0.8796, 0.8148), 0.60),
}

if not levels.new_level(MAP):
    raise RuntimeError("Could not create new empty level")
cube = lib.load_asset("/Engine/BasicShapes/Cube.Cube")
if not isinstance(cube, unreal.StaticMesh): raise RuntimeError("Engine cube missing")

created = []
def box(label, location, dims_cm, material, tags, collision=True, nav=True):
    a = actors.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(*location), unreal.Rotator())
    a.set_actor_label(label)
    a.tags = [unreal.Name(t) for t in ["LB.CleanShell.v20260809.v001", "LB.Asset.NewAuthored"] + tags]
    c = a.static_mesh_component
    c.set_static_mesh(cube)
    c.set_world_scale3d(unreal.Vector(dims_cm[0]/100.0, dims_cm[1]/100.0, dims_cm[2]/100.0))
    c.set_material(0, material)
    c.set_collision_enabled(unreal.CollisionEnabled.QUERY_AND_PHYSICS if collision else unreal.CollisionEnabled.NO_COLLISION)
    c.set_editor_property("can_ever_affect_navigation", nav)
    c.set_cast_shadow(collision)
    created.append(a)
    return a

# Exact overall authority: 22000 x 12000 cm, floor top at Z=0, 1650 cm clear wall height.
box("LB_CLEAN_Floor_220m_x_120m", (0,0,-25), (22000,12000,50), materials["floor"], ["LB.Environment.Floor"])
box("LB_CLEAN_Wall_North", (0,6000,825), (22000,40,1650), materials["wall"], ["LB.Environment.Wall"])
box("LB_CLEAN_Wall_South", (0,-6000,825), (22000,40,1650), materials["wall"], ["LB.Environment.Wall"])
box("LB_CLEAN_Wall_West", (-11000,0,825), (40,12000,1650), materials["wall"], ["LB.Environment.Wall"])
box("LB_CLEAN_Wall_East", (11000,0,825), (40,12000,1650), materials["wall"], ["LB.Environment.Wall"])

# Perimeter structural rhythm only. Interior grid remains uncommitted until equipment clearance validation.
for x in range(-11000, 11001, 2000):
    for y in (-5950, 5950):
        box(f"LB_CLEAN_PerimeterColumn_{x}_{y}", (x,y,825), (55,55,1650), materials["steel"], ["LB.Environment.Structure"])
for x in range(-11000, 11001, 2000):
    box(f"LB_CLEAN_RoofBeam_{x}", (x,0,1625), (45,11900,45), materials["steel"], ["LB.Environment.RoofStructure"])

# Fixed protected perimeter service walkway: 150 cm clear, yellow 10 cm boundary.
z_paint = 1.0
box("LB_CLEAN_Walkway_South", (0,-5200,z_paint), (21600,150,2), materials["walk"], ["LB.FloorPaint.FixedWalkway"], False, False)
box("LB_CLEAN_Walkway_North", (0,5200,z_paint), (21600,150,2), materials["walk"], ["LB.FloorPaint.FixedWalkway"], False, False)
box("LB_CLEAN_Walkway_West", (-10200,0,z_paint), (150,8900,2), materials["walk"], ["LB.FloorPaint.FixedWalkway"], False, False)
box("LB_CLEAN_Walkway_East", (10200,0,z_paint), (150,8900,2), materials["walk"], ["LB.FloorPaint.FixedWalkway"], False, False)
for label, loc, dims in [
    ("SouthInner",(0,-4425,1.6),(21600,10,2)), ("NorthInner",(0,4425,1.6),(21600,10,2)),
    ("WestInner",(-9425,0,1.6),(10,8900,2)), ("EastInner",(9425,0,1.6),(10,8900,2))]:
    box(f"LB_CLEAN_WalkwayYellow_{label}", loc, dims, materials["yellow"], ["LB.FloorPaint.FixedSafetyEdge"], False, False)

# Six fixed fire keep-clear pads; doors/egress hardware remain a later shell-detail gate.
fire_pads = [(-9000,-5200),(0,-5200),(9000,-5200),(-9000,5200),(0,5200),(9000,5200)]
for i,(x,y) in enumerate(fire_pads,1):
    box(f"LB_CLEAN_FireKeepClear_{i:02d}_Red", (x,y,2.0), (300,150,2), materials["red"], ["LB.FloorPaint.FireKeepClear"], False, False)
    box(f"LB_CLEAN_FireKeepClear_{i:02d}_White", (x,y,2.6), (180,80,2), materials["white"], ["LB.FloorPaint.FireKeepClear"], False, False)

# Positional-reference datums only: invisible at runtime and not production actors.
datums = {
    "TRAIN_A": (2000,-3300,0), "TRAIN_B": (2000,-1100,0),
    "TRAIN_C": (2000,1100,0), "TRAIN_D": (2000,3300,0),
    "INBOUND_REVIEW": (-7500,0,0), "SUPPORT_REVIEW": (0,-5000,0)
}
for name, loc in datums.items():
    a = box(f"LB_CLEAN_DATUM_{name}", (loc[0],loc[1],3), (300,10,2), materials["white"], [f"LB.ReferenceDatum.{name}"], False, False)
    a.set_is_temporarily_hidden_in_editor(True)
    a.set_actor_hidden_in_game(True)

# Neutral lighting for future visual review, no machine lighting copied.
sun = actors.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0,0,1500), unreal.Rotator(-55,-25,0))
sun.set_actor_label("LB_CLEAN_Light_Directional"); sun.tags=[unreal.Name("LB.CleanShell.v20260809.v001")]
sun.get_component_by_class(unreal.DirectionalLightComponent).set_editor_property("intensity", 3.0)
sky = actors.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0,0,1500), unreal.Rotator())
sky.set_actor_label("LB_CLEAN_Light_Sky"); sky.tags=[unreal.Name("LB.CleanShell.v20260809.v001")]
sky.get_component_by_class(unreal.SkyLightComponent).set_editor_property("intensity", 0.75)
for x in range(-9000, 9001, 3000):
    for y in (-3600,0,3600):
        l=actors.spawn_actor_from_class(unreal.RectLight, unreal.Vector(x,y,1450), unreal.Rotator(-90,0,0))
        l.set_actor_label(f"LB_CLEAN_Light_{x}_{y}"); l.tags=[unreal.Name("LB.CleanShell.v20260809.v001")]
        c=l.get_component_by_class(unreal.RectLightComponent); c.set_editor_property("intensity",12000.0); c.set_editor_property("source_width",800.0); c.set_editor_property("source_height",160.0)

unreal.AutomationUtilsBlueprintLibrary.finish_all_asset_compilation()
if not levels.save_current_level(): raise RuntimeError("Could not save clean shell")
after = sha(PROTECTED)
if after != before: raise RuntimeError("Protected v438 changed")

all_actors = actors.get_all_level_actors()
production = [a.get_actor_label() for a in all_actors if any(str(t).startswith(("LB.PressTrain", "LB.Inbound.Module", "LB.SupportRobot")) for t in a.tags)]
if production: raise RuntimeError(f"Production actor leak: {production}")
map_file = ROOT / "Content/LineBoss/Maps/LB_PressShop_CleanShell_v20260809_v001.umap"
payload = {
    "$schema":"cairnwell/audit/press-shop-clean-shell-v20260809-v001/v1",
    "generated_utc":datetime.now(timezone.utc).isoformat(),
    "status":"PASS__FRESH_EMPTY_220M_X_120M_SHELL__NEW_MATERIALS_AND_FIXED_PAINT_ONLY__NO_PRODUCTION_ACTORS__NOT_PROMOTED",
    "map":MAP, "map_sha256":sha(map_file), "dimensions_cm":[22000,12000,1650],
    "actor_count":len(all_actors), "production_actor_count":0, "reference_datums_cm":datums,
    "materials":[f"{MAT_DIR}/{m.get_name()}" for m in materials.values()],
    "fixed_paint":{"sealed_floor":1,"green_walkways":4,"yellow_edges":4,"fire_keep_clear_pads":6},
    "interior_structural_grid_status":"UNCOMMITTED_PENDING_EQUIPMENT_CLEARANCE",
    "protected_v438_before":before,"protected_v438_after":after,"meshy_credits_used":0,"promotion_authorized":False
}
OUT.parent.mkdir(parents=True,exist_ok=True); OUT.write_text(json.dumps(payload,indent=2),encoding="utf-8")
unreal.log("LINE_BOSS_CLEAN_SHELL_V20260809_V001_PASS")
