"""A/B-test the one remaining pivot-safe native legacy import setting.

RuntimePrep v002 has neutral FBX nodes for every mesh.  This wrapper reuses
the guarded v001 scratch harness unchanged except for one intentional native
import difference: ``transform_vertex_to_absolute=True``.  The preflight
asserts that a node transform cannot carry mover parking offsets before the
test begins.  It writes to a wholly separate scratch namespace/receipt.
"""

from __future__ import annotations

import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
SOURCE_HARNESS = HERE / "validate_material_flow_pack_v002_legacy_fbx_factory_scratch_v001.py"
SOURCE_STATS = (HERE.parent / "ArtSource/Claude_PressShop_MaterialFlowPack_RuntimePrep_v002/"
                "runtime_prep_stats_v002.json")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError("MATERIAL_FLOW_V002_ABSOLUTE_PIVOT_PROBE_PRECHECK_FAIL: " + message)


def neutral_node_preflight() -> None:
    require(SOURCE_STATS.is_file(), "v002 stats missing")
    stats = json.loads(SOURCE_STATS.read_text(encoding="utf-8"))
    verification = stats.get("raw_fbx_verification", {})
    node_count = 0
    for fbx, report in verification.items():
        for name, node in report.get("nodes", {}).items():
            node_count += 1
            require(all(abs(float(value)) <= 1e-6 for value in node.get("Lcl Translation", ())),
                    "non-neutral translation {}:{}".format(fbx, name))
            require(all(abs(float(value)) <= 1e-6 for value in node.get("Lcl Rotation", ())),
                    "non-neutral rotation {}:{}".format(fbx, name))
            require(all(abs(float(value) - 1.0) <= 1e-6 for value in node.get("Lcl Scaling", ())),
                    "non-neutral scale {}:{}".format(fbx, name))
            require(all(abs(float(value)) <= 1e-6 for value in node.get("GeometricTranslation", ())),
                    "non-neutral geometric translation {}:{}".format(fbx, name))
            require(all(abs(float(value) - 1.0) <= 1e-6 for value in node.get("GeometricScaling", ())),
                    "non-neutral geometric scale {}:{}".format(fbx, name))
    require(node_count == 10, "expected ten neutral v002 mesh nodes, got {}".format(node_count))


def replace_exact(code: str, old: str, new: str, expected_count: int) -> str:
    count = code.count(old)
    require(count == expected_count, "harness drift for {!r}: got {}, expected {}".format(old, count, expected_count))
    return code.replace(old, new)


neutral_node_preflight()
require(SOURCE_HARNESS.is_file(), "source harness missing")
code = SOURCE_HARNESS.read_text(encoding="utf-8")

# Isolate all scratch content/receipts and give the test a self-describing
# label.  No v001 harness artifact is edited or overwritten.
code = replace_exact(
    code,
    "MaterialFlowPack_v002_LegacyFbxFactory_v001",
    "MaterialFlowPack_v002_LegacyAbsolutePivotProbe_v001",
    1,
)
code = replace_exact(
    code,
    "legacy_fbx_factory_scratch_v001.json",
    "legacy_fbx_factory_absolute_pivot_probe_v001.json",
    1,
)
code = replace_exact(
    code,
    "legacy_fbx_factory_scratch_v001_failure.json",
    "legacy_fbx_factory_absolute_pivot_probe_v001_failure.json",
    1,
)
code = code.replace(
    "material-flow-runtimeprep-v002/legacy-fbx-factory-scratch/v1",
    "material-flow-runtimeprep-v002/legacy-fbx-factory-absolute-pivot-probe/v1",
)
code = code.replace(
    "MATERIAL_FLOW_V002_LEGACY_FBX_FACTORY_SCRATCH",
    "MATERIAL_FLOW_V002_LEGACY_FBX_FACTORY_ABSOLUTE_PIVOT_PROBE",
)

# First make every false occurrence true: import options, persisted native
# import-data expectation and evidence will then agree.  Restore the source
# handoff's *declared* recipe to false only in its source-contract check;
# v002 itself remains unmodified and the receipt will make the tested native
# override explicit.
code = code.replace('"transform_vertex_to_absolute": False,', '"transform_vertex_to_absolute": True,')
code = replace_exact(
    code,
    '"Convert Scene Unit": True,\n        "transform_vertex_to_absolute": True,\n        "bake_pivot_in_vertex": False,',
    '"Convert Scene Unit": True,\n        "transform_vertex_to_absolute": False,\n        "bake_pivot_in_vertex": False,',
    1,
)

# The original text says it is the approved false-transform source recipe;
# this test is deliberately a candidate override and cannot authorize
# production integration by itself.
code = code.replace(
    '"native_importer": "Unreal 5.8 legacy FbxFactory",',
    '"native_importer": "Unreal 5.8 legacy FbxFactory (absolute-pivot candidate)",',
)
code = code.replace(
    '"promotion_authorized": False,',
    '"promotion_authorized": False,\n        "source_recipe_override_under_test": "transform_vertex_to_absolute=True; permitted only because all ten v002 FBX nodes are proven neutral",',
)

exec(compile(code, str(SOURCE_HARNESS) + "::absolute-pivot-probe-v001", "exec"), globals(), globals())
