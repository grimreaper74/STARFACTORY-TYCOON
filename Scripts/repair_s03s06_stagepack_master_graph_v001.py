"""Repair the native StagePack v003 PBR master's unconnected mask inputs.

The original import built valid nodes but addressed ComponentMask's unnamed
input as ``Input``.  UE 5.8 silently left those four connections unset and
compiled the master to the default material.  This narrowly reconnects the
existing graph, verifies every source/output, saves only the existing native
master asset, and records an audit receipt under Saved.
"""

import json
from pathlib import Path
import traceback

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
MASTER_PATH = (
    "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/SharedTrainModules_v003/"
    "Materials/M_CA_MW_PT_StagePack_PBR_Master_v001."
    "M_CA_MW_PT_StagePack_PBR_Master_v001"
)
RECEIPT = (ROOT / "Saved/Audits/OneFactory/Press/S03S06StagePackRuntimePrep_v001/"
           "stagepack_master_graph_repair_v001.json")
MEL = unreal.MaterialEditingLibrary


def node_y(node):
    return int(node.get_editor_property("material_expression_editor_y"))


def named_texture(expressions, name):
    matches = [node for node in expressions
               if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D)
               and str(node.get_editor_property("parameter_name")) == name]
    if len(matches) != 1:
        raise RuntimeError(f"Expected exactly one texture parameter {name}; found {len(matches)}")
    return matches[0]


def input_connection(material, node):
    sources = list(MEL.get_inputs_for_material_expression(material, node))
    if len(sources) != 1:
        raise RuntimeError(f"Expected one ComponentMask input, found {len(sources)}")
    source = sources[0]
    return {
        "source": str(source.get_name()) if source else None,
        "output": (str(MEL.get_input_node_output_name_for_material_expression(node, source))
                   if source else None),
    }, source


def main():
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    master = unreal.load_asset(MASTER_PATH)
    if not master or not isinstance(master, unreal.Material):
        raise RuntimeError("StagePack native PBR master does not resolve")
    expressions = list(MEL.get_material_expressions(master))
    orm = named_texture(expressions, "ORMMap")
    raw_mask = named_texture(expressions, "WearMaskMap")
    masks = [node for node in expressions
             if isinstance(node, unreal.MaterialExpressionComponentMask)]
    expected_masks = {320: orm, 400: orm, 480: orm, 600: raw_mask}
    by_y = {node_y(node): node for node in masks}
    if len(masks) != 4 or set(by_y) != set(expected_masks):
        raise RuntimeError(
            "Unexpected StagePack ComponentMask graph; expected four masks at "
            f"{sorted(expected_masks)}, found {sorted(by_y)}")
    before = {}
    for y, node in sorted(by_y.items()):
        before[str(y)], _ = input_connection(master, node)
    repaired = []
    for y, node in sorted(by_y.items()):
        expected_source = expected_masks[y]
        _, actual_source = input_connection(master, node)
        if actual_source != expected_source:
            # ComponentMask's input is unnamed in UE 5.8.  Do not target the
            # display-only "Input" label used by older wrappers.
            MEL.disconnect_material_expressions(node, "")
            if not MEL.connect_material_expressions(expected_source, "RGB", node, ""):
                raise RuntimeError(f"Could not reconnect ComponentMask at graph y={y}")
            repaired.append(y)
    after = {}
    for y, node in sorted(by_y.items()):
        connection, actual_source = input_connection(master, node)
        expected_source = expected_masks[y]
        if actual_source != expected_source or connection["output"] != "RGB":
            raise RuntimeError(f"ComponentMask verification failed at graph y={y}: {connection}")
        after[str(y)] = connection
    MEL.recompile_material(master)
    if not unreal.EditorAssetLibrary.save_loaded_asset(master, only_if_is_dirty=False):
        raise RuntimeError("Could not save repaired StagePack PBR master")
    result = {
        "$schema": "lineboss/repair/onefactory/press/stagepack-master-graph/v1",
        "status": "PASS__STAGEPACK_MASTER_COMPONENTMASKS_CONNECTED",
        "master": MASTER_PATH,
        "connections_before": before,
        "connections_after": after,
        "repaired_mask_graph_y": repaired,
        "content_writes": [MASTER_PATH],
        "map_loaded_or_saved": [],
        "write_scope": [str(RECEIPT)],
    }
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log("STAGEPACK_MASTER_GRAPH_REPAIR_PASS")
    unreal.SystemLibrary.quit_editor()


try:
    main()
except Exception as exc:
    failure = {
        "$schema": "lineboss/repair/onefactory/press/stagepack-master-graph/v1",
        "status": "FAIL__STAGEPACK_MASTER_GRAPH_REPAIR",
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "content_writes": [],
        "map_loaded_or_saved": [],
        "write_scope": [str(RECEIPT)],
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log_error("STAGEPACK_MASTER_GRAPH_REPAIR_FAIL " + str(exc))
    unreal.SystemLibrary.quit_editor()
