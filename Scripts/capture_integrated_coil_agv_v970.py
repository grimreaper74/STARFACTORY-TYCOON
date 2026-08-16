"""Low-glare industrial-lighting proof of the controlled wrapped-coil AGV."""
from pathlib import Path
import unreal

root = Path(unreal.Paths.project_dir()).resolve()
source = root / "Scripts/capture_integrated_coil_agv_v967.py"
if not source.is_file():
    raise RuntimeError(f"Missing v967 capture authority: {source}")
code = source.read_text(encoding="utf-8")
for old, new in (
    ("PlayerBuildable_v967", "PlayerBuildable_v970"),
    ("integrated_coil_agv_v967.json", "integrated_coil_agv_v970.json"),
    ("LB_TRANSIENT_PlayerBuilt_CoilAGV_v967", "LB_TRANSIENT_PlayerBuilt_CoilAGV_v970"),
    ("PASS_INTEGRATED_UNTOUCHED_COIL_AGV", "PASS_LOW_GLARE_UNTOUCHED_AGV_CONTROLLED_COIL"),
    ("LINE_BOSS_INTEGRATED_COIL_AGV_V967_PASS", "LINE_BOSS_INTEGRATED_COIL_AGV_V970_PASS"),
    ("LINE_BOSS_INTEGRATED_COIL_AGV_V967_FAIL", "LINE_BOSS_INTEGRATED_COIL_AGV_V970_FAIL"),
    ('"cubemap": sky_cube, "intensity": 0.42', '"cubemap": sky_cube, "intensity": 0.12'),
    ('{"intensity": 0.9, "cast_shadows": True}', '{"intensity": 0.35, "cast_shadows": True}'),
    ("((-260, -220, 220), 650.0, 700.0),", "((-260, -220, 220), 180.0, 700.0),"),
    ("((230, 210, 210), 500.0, 650.0)", "((230, 210, 210), 140.0, 650.0)"),
):
    code = code.replace(old, new)
code = code.replace(
    "floor.static_mesh_component.set_static_mesh(cube)",
    "floor.static_mesh_component.set_static_mesh(cube)\n"
    "floor_material = unreal.EditorAssetLibrary.load_asset("
    "'/Game/LineBoss/Materials/M_LB_FactoryConcrete.M_LB_FactoryConcrete')\n"
    "if floor_material:\n"
    "    floor.static_mesh_component.set_material(0, floor_material)")
exec(compile(code, str(source), "exec"), globals(), globals())
