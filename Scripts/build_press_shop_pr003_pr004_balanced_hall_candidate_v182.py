"""Build v182 directly from retained v180: wall lift only, roof untouched."""

from pathlib import Path


source = Path(__file__).with_name("build_press_shop_pr003_pr004_balanced_hall_candidate_v181.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v181", "v182").replace("V181", "V182")
code = code.replace(
    '"M_CA_MW_HallUpperServicePanel_v182", (0.29, 0.32, 0.34), 0.78)',
    '"M_CA_MW_HallUpperServicePanel_v182", (0.20, 0.22, 0.24), 0.82)')
code = code.replace(
    'elif label.startswith("LB_PR004_V028_RoofLiner_"):\n        role = "upper_panel"\n        roof_count += 1',
    'elif label.startswith("LB_PR004_V028_RoofLiner_"):\n        continue')
code = code.replace('"intensity": 22.0,', '"intensity": 12.0,')
code = code.replace('if len(changed) != 51:', 'if len(changed) != 31:')
code = code.replace(
    'failures.append(f"expected 31 wall/structure plus 20 roof bindings, changed {len(changed)}")',
    'failures.append(f"expected 31 wall/structure bindings, changed {len(changed)}")')
code = code.replace('if roof_count != 20:', 'if roof_count != 0:')
code = code.replace(
    'failures.append(f"expected 20 roof liners, found {roof_count}")',
    'failures.append(f"expected roof liners unchanged, changed {roof_count}")')
code = code.replace(
    "BALANCED_LIGHT_GREY_HALL_SURFACES_AND_BROAD_WALL_WASH_BUILT",
    "RESTRAINED_WALL_LIFT_WITH_ROOF_AND_COIL_EXPOSURE_UNCHANGED")
exec(compile(code, str(source), "exec"), {"__name__": "__main__", "__file__": str(source)})
