"""Read-only UE 5.8 Python API probe for deterministic simple collision authoring."""
import json
from pathlib import Path
import unreal

out = Path(unreal.Paths.project_saved_dir()) / "Audits/PR009_InMap_v087/collision_api_probe.json"
row = {"kbox_available": hasattr(unreal, "KBoxElem"), "errors": []}
try:
    box = unreal.KBoxElem()
    for name, value in {
        "center": unreal.Vector(1.0, 2.0, 3.0),
        "rotation": unreal.Rotator(),
        "x": 10.0, "y": 20.0, "z": 30.0,
    }.items():
        box.set_editor_property(name, value)
    row["box"] = {name: str(box.get_editor_property(name)) for name in ("center", "rotation", "x", "y", "z")}
except Exception as exc:
    row["errors"].append(f"KBoxElem: {exc}")
try:
    agg = unreal.KAggregateGeom()
    agg.set_editor_property("box_elems", [box])
    row["aggregate_box_count"] = len(agg.get_editor_property("box_elems"))
except Exception as exc:
    row["errors"].append(f"KAggregateGeom: {exc}")
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(row, indent=2), encoding="utf-8")
unreal.log(f"PR009_V087_COLLISION_API_PROBE output={out}")
unreal.SystemLibrary.quit_editor()
