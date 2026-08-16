"""Bind v052 cleaner semantics to isolated shared/support materials."""

from pathlib import Path

import unreal


root = Path(unreal.Paths.project_dir())
base_path = root / "Scripts/bind_lb_cr01_v042_shared_materials_candidate_v002.py"
code = base_path.read_text(encoding="utf-8")

replacements = {
    "quarantined CR01 v042": "quarantined CR01 v052",
    "/Candidate_v042/Blueprints/BP_LB_CR01_CleaningAMR_v042": "/Candidate_v052/Blueprints/BP_LB_CR01_CleaningAMR_v052",
    "/Candidate_v042/Materials": "/Candidate_v052/Materials",
    "lb_cr01_v042_shared_material_bindings_v002.json": "lb_cr01_v052_shared_material_bindings_v002.json",
    "existing v042 material candidate": "existing v052 material candidate",
    "/Candidate_v042/Meshes/": "/Candidate_v052/Meshes/",
    "Unmapped CR01 v042": "Unmapped CR01 v052",
    "lb-cr01-v042-shared-material-bindings-v002": "lb-cr01-v052-shared-material-bindings-v002",
    "CR01_V042_SHARED": "CR01_V052_SHARED",
    'if "BodyCharcoal" in slot_name or "FrameAnthracite" in slot_name:': 'if any(token in slot_name for token in ("BodyCharcoal", "FrameAnthracite", "GraphitePowdercoat", "ServiceCharcoal")):',
    'if "CairnwellGreen" in slot_name:': 'if "CairnwellGreen" in slot_name or "RuggedGreen" in slot_name:',
    'if "RubberBlack" in slot_name or "RenewedRubber" in slot_name:': 'if any(token in slot_name for token in ("RubberBlack", "RenewedRubber", "WearRubber", "GasketBlack", "HydraulicBlack", "BrushHubWearBlack")):',
    'if "SensorGlass" in slot_name:': 'if any(token in slot_name for token in ("SensorGlass", "SensorLens", "WorkLamp", "AmberMarker", "StopMarker")):',
    '    exact = {': '''    if any(token in slot_name for token in ("DenseRollerBristle", "ProductionBristle", "RadialBristleCluster")):
        return support["M_LB_CR01_Bristle"], "isolated_candidate_bristle"
    if any(token in slot_name for token in ("BrushedServiceSteel", "CarrierSteel", "WearSteel", "FilterMedia")):
        return support["M_LB_CR01_BrushedSteel_v013"], "isolated_candidate_service_metal"
    if "HopperPolymer" in slot_name:
        return shared_paint[f"ServiceGrey_{condition}"], "shared_paint_hopper_polymer"
    exact = {''',
}

for old, new in replacements.items():
    if old not in code:
        raise RuntimeError(f"v052 material adapter base drift: missing replacement token {old!r}")
    code = code.replace(old, new)

exec(compile(code, str(base_path) + "::v052-adapter", "exec"), globals(), globals())
