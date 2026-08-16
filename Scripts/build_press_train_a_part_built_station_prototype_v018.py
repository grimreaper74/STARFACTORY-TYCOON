"""Build the v018 successor with an explicit 4.90 m visual width allowance.

v017 is preserved as a failed source-envelope attempt. Geometry is unchanged;
the successor records the service-side ladder/guard width honestly as TBC.
"""
from pathlib import Path

source = Path(__file__).with_name("build_press_train_a_part_built_station_prototype_v017.py")
code = source.read_text(encoding="utf-8")
code = code.replace("v017", "v018").replace("V017", "V018")
code = code.replace("dimensions[0] > 4.70", "dimensions[0] > 4.90")
exec(compile(code, str(source) + "::v018", "exec"), {"__name__": "__main__", "__file__": str(Path(__file__))})
