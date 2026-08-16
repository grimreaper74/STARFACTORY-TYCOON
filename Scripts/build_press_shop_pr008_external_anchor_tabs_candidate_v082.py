"""Build visible external anchor tabs from measured v079 base footprints."""
from pathlib import Path

base = Path(__file__).with_name("build_press_shop_pr008_anchored_installation_candidate_v081.py")
code = base.read_text(encoding="utf-8")
code = code.replace("AnchoredInstallationCandidate_v081", "ExternalAnchorTabsCandidate_v082")
code = code.replace("AnchoredInstallation_v081", "ExternalAnchorTabs_v082")
code = code.replace("anchored_installation_candidate_v081", "external_anchor_tabs_candidate_v082")
code = code.replace("V081", "V082").replace("v081", "v082")
code = code.replace("min_x + inset_x, min_y + inset_y", "min_x - 4.0, min_y - 4.0")
code = code.replace("min_x + inset_x, max_y - inset_y", "min_x - 4.0, max_y + 4.0")
code = code.replace("max_x - inset_x, min_y + inset_y", "max_x + 4.0, min_y - 4.0")
code = code.replace("max_x - inset_x, max_y - inset_y", "max_x + 4.0, max_y + 4.0")
code = code.replace("(0.10, 0.10, 0.008)", "(0.12, 0.12, 0.008)")
code = code.replace('"plate_dimensions_cm": [10.0, 10.0, 0.8]', '"plate_dimensions_cm": [12.0, 12.0, 0.8]')
code = code.replace(
    "MEASURED_MAJOR_BASE_FOOTPRINT_ANCHORS_BUILT_FROM_RETAINED_V079",
    "MEASURED_EXTERNAL_BASE_ANCHOR_TABS_BUILT_FROM_RETAINED_V079")
exec(compile(code, str(base) + "::v082-external-anchor-adapter", "exec"), globals(), globals())
