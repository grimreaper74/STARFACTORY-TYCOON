"""Build v183 directly from retained v180: wall materials only, no added light."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr003_pr004_balanced_hall_candidate_v181.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v181", "v183").replace("V181", "V183")
code = code.replace(
    '"M_CA_MW_HallUpperServicePanel_v183", (0.29, 0.32, 0.34), 0.78)',
    '"M_CA_MW_HallUpperServicePanel_v183", (0.20, 0.22, 0.24), 0.82)')
code = code.replace(
    'elif label.startswith("LB_PR004_V028_RoofLiner_"):\n        role = "upper_panel"\n        roof_count += 1',
    'elif label.startswith("LB_PR004_V028_RoofLiner_"):\n        continue')
code = code.replace(
    'for index, x in enumerate((-10000.0, -8000.0, -6000.0, -4000.0), start=1):',
    'for index, x in enumerate((), start=1):')
code = code.replace('if len(changed) != 51:', 'if len(changed) != 31:')
code = code.replace(
    'failures.append(f"expected 31 wall/structure plus 20 roof bindings, changed {len(changed)}")',
    'failures.append(f"expected 31 wall/structure bindings, changed {len(changed)}")')
code = code.replace('if roof_count != 20:', 'if roof_count != 0:')
code = code.replace(
    'failures.append(f"expected 20 roof liners, found {roof_count}")',
    'failures.append(f"expected roof liners unchanged, changed {roof_count}")')
code = code.replace('if len(wall_wash) != 4 or len(cameras) != 3:', 'if len(wall_wash) != 0 or len(cameras) != 3:')
code = code.replace(
    "BALANCED_LIGHT_GREY_HALL_SURFACES_AND_BROAD_WALL_WASH_BUILT",
    "WALL_MATERIAL_HIERARCHY_BUILT_WITH_LIGHT_RIG_UNCHANGED")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
