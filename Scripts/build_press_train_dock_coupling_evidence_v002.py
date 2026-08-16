"""Build a lower-profile dock/manifold successor for Train A die carts."""

from pathlib import Path


base = Path(__file__).with_name("build_press_train_dock_coupling_evidence_v001.py")
code = base.read_text(encoding="utf-8").replace("v001", "v002").replace("V001", "V002")
start = code.index("# Two visible hydraulic lock bridges")
end = code.index('bpy.ops.object.select_all(action="DESELECT")', start)
geometry = r'''
# Low-profile engaged dock hardware. The assembly stays below the die-cart deck
# and reads as locks/manifold/cable routing rather than as another vehicle.
for y in (-1250, 1250):
    box(parts, f"DockSill_{y}", (920, 260, 180), (-2380, y, 220),
        "CA_MW_FoundryCharcoal", 24)
    box(parts, f"ClampHousing_{y}", (380, 520, 430), (-2820, y, 390),
        "CA_MW_FoundryCharcoal", 34)
    cylinder(parts, f"HydraulicLockPin_{y}", 160, 650, (-2600, y, 430),
             "CA_MW_SafetyYellow", axis="X", vertices=24)
    cylinder(parts, f"LockSleeve_{y}", 235, 270, (-2380, y, 430),
             "CA_MW_WorkedSteel", axis="X", vertices=24)
    box(parts, f"ClampProofFlag_{y}", (75, 300, 190), (-2960, y, 720),
        "CA_MW_StateGreen", 10)

# Recessed multi-service manifold with three keyed connector faces.
box(parts, "ManifoldBackplate", (720, 1080, 520), (-2580, 0, 480),
    "CA_MW_FoundryCharcoal", 45)
box(parts, "ManifoldGuard", (820, 1180, 95), (-2580, 0, 800),
    "CA_MW_SafetyYellow", 18)
for y, material in ((-300, "CA_MW_TrainAAccent"), (0, "CA_MW_StateGreen"),
                    (300, "CA_MW_WorkedSteel")):
    cylinder(parts, f"MatedConnector_{y}", 170, 520, (-2720, y, 500),
             material, axis="X", vertices=24)
box(parts, "PermissiveWitness", (80, 420, 180), (-2970, 0, 650),
    "CA_MW_StateGreen", 12)

# Short articulated chain from the moving cart anchor into the dock manifold.
chain_points = [
    (-1850, -720, 150), (-2020, -720, 90), (-2200, -720, 55),
    (-2380, -720, 55), (-2560, -720, 100), (-2740, -720, 185),
]
for index, (x, y, z) in enumerate(chain_points):
    box(parts, f"CableChainLink_{index:02d}", (220, 310, 125), (x, y, z),
        "CA_MW_DarkRubber", 15, rotation_z=0 if index % 2 == 0 else 4)
    cylinder(parts, f"CableChainPin_{index:02d}", 78, 340, (x, y, z),
             "CA_MW_WorkedSteel", axis="Y", vertices=16)
box(parts, "CartCableAnchor", (280, 480, 320), (-1780, -720, 250),
    "CA_MW_CairnwellGreen", 30)
box(parts, "DockCableAnchor", (280, 480, 330), (-2840, -720, 280),
    "CA_MW_CairnwellGreen", 30)

# Compact tow capture below deck height.
torus(parts, "DockTowCapture", 400, 95, (-2820, 720, 260),
      "CA_MW_SafetyYellow", rotation=(90, 0, 0))
cylinder(parts, "TowCapturePin", 150, 460, (-2600, 720, 260),
         "CA_MW_WorkedSteel", axis="X", vertices=24)
box(parts, "TowCaptureBracket", (420, 480, 360), (-2870, 720, 280),
    "CA_MW_FoundryCharcoal", 38)

'''
code = code[:start] + geometry + code[end:]
code = code.replace(
    '"planning_envelope_mm": [1800, 3700, 1800]',
    '"planning_envelope_mm": [1500, 3200, 1000]',
)
code = code.replace(
    '"notes": "Camera-readable engaged-state evidence only; runtime separation and interlock ownership remain mandatory before promotion."',
    '"notes": "Low-profile engaged dock/manifold evidence below cart deck; runtime separation and interlock ownership remain mandatory before promotion."',
)
exec(compile(code, str(base) + "::v002", "exec"), globals(), globals())
