"""Correct v026's Blender 5.2 render-engine identifier without overwriting it."""
from pathlib import Path

base=Path(__file__).with_name("build_press_train_a_dedicated_end_cells_source_v026.py")
code=base.read_text(encoding="utf-8")
code=code.replace("DedicatedEndCells_v026", "DedicatedEndCells_v027")
code=code.replace("DEDICATED_END_CELLS_MANIFEST_v026", "DEDICATED_END_CELLS_MANIFEST_v027")
code=code.replace("DEDICATED_END_CELLS_VALIDATION_v026", "DEDICATED_END_CELLS_VALIDATION_v027")
code=code.replace("_v026", "_v027").replace("-v026", "-v027")
code=code.replace('scene.render.engine="BLENDER_EEVEE_NEXT"', 'scene.render.engine="BLENDER_EEVEE"')
exec(compile(code,str(base)+"::v027","exec"),globals(),globals())
