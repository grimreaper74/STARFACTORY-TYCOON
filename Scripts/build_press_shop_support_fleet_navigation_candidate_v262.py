"""Build widened support-fleet nav coverage directly from protected v260."""

from pathlib import Path

source = Path(__file__).with_name("build_press_shop_support_fleet_navigation_candidate_v261.py")
code = source.read_text(encoding="utf-8").replace("v261", "v262").replace("V261", "V262")
code = code.replace("unreal.Vector(-3350.0, 4650.0, 350.0)", "unreal.Vector(-3350.0, 4000.0, 350.0)")
code = code.replace("unreal.Vector(38.0, 8.0, 3.5)", "unreal.Vector(38.0, 20.0, 3.5)")
code = code.replace(
    "Covers only the retained north support berths, their straight aprons and the\n+# common service aisle.",
    "Covers the retained north support berths, straight aprons and the unobstructed\n+# southern service cross-aisle needed to route around inherited workshop dividers.",
)
exec(compile(code, str(source) + "::v262-widened-direct-v260", "exec"), globals(), globals())
