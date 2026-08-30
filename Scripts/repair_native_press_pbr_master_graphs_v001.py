"""Repair UE 5.8 sampler/mask wiring in the two imported native press masters.

Both original import generators used ``Input`` for ComponentMask's unnamed UE
5.8 pin, and used Linear Color samplers for textures imported as TC_MASKS.
This repairs only those existing master graphs and makes no change to source
textures, instances, meshes, maps, or placements.
"""

import json
from pathlib import Path
import traceback

import unreal


ROOT = Path(r"C:/Users/greg_/Projects/LineBossCarFactory_Unreal 5.8")
RECEIPT = ROOT / "Saved/Audits/OneFactory/Press/native_pbr_master_graphs_repair_v001.json"
MEL = unreal.MaterialEditingLibrary

MASTERS = (
    {
        "label": "S02DeepDraw_v003",
        "path": (
            "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
            "DetailedPresentation_v001/S02DeepDraw_v003/Materials/"
            "M_CA_S02DeepDraw_PBR_Master_v003.M_CA_S02DeepDraw_PBR_Master_v003"),
        "samplers": {
            "BaseColorMap": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
            "NormalMap": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
            "ORMMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
            "WearMaskMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
            "ModuleAOMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        },
        "masks": {430: "ORMMap", 500: "ORMMap", 560: "ORMMap",
                  630: "WearMaskMap", 830: "ModuleAOMap"},
    },
    {
        "label": "S03S06StagePack_v003",
        "path": (
            "/Game/LineBoss/Factory/OneFactory/v001/Native/Press/"
            "SharedTrainModules_v003/Materials/"
            "M_CA_MW_PT_StagePack_PBR_Master_v001."
            "M_CA_MW_PT_StagePack_PBR_Master_v001"),
        "samplers": {
            "BaseColorMap": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
            "NormalMap": unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL,
            "ORMMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
            "WearMaskMap": unreal.MaterialSamplerType.SAMPLERTYPE_MASKS,
        },
        "masks": {320: "ORMMap", 400: "ORMMap", 480: "ORMMap",
                  600: "WearMaskMap"},
    },
)


def parameter_name(node):
    return str(node.get_editor_property("parameter_name"))


def input_state(material, node):
    sources = list(MEL.get_inputs_for_material_expression(material, node))
    if len(sources) != 1:
        raise RuntimeError(f"Expected one ComponentMask input, found {len(sources)}")
    source = sources[0]
    return source, {
        "source_parameter": (parameter_name(source)
                             if source and isinstance(
                                 source, unreal.MaterialExpressionTextureSampleParameter2D)
                             else None),
        "output": (str(MEL.get_input_node_output_name_for_material_expression(node, source))
                   if source else None),
    }


def repair_master(spec):
    material = unreal.load_asset(spec["path"])
    if not material or not isinstance(material, unreal.Material):
        raise RuntimeError(f"{spec['label']} master does not resolve")
    expressions = list(MEL.get_material_expressions(material))
    samples = {parameter_name(node): node for node in expressions
               if isinstance(node, unreal.MaterialExpressionTextureSampleParameter2D)}
    if set(samples) != set(spec["samplers"]):
        raise RuntimeError(
            f"{spec['label']} texture parameter graph drifted: {sorted(samples)}")
    sampler_before = {}
    sampler_after = {}
    sampler_changed = []
    for parameter, expected in spec["samplers"].items():
        node = samples[parameter]
        before = node.get_editor_property("sampler_type")
        sampler_before[parameter] = str(before)
        if before != expected:
            node.set_editor_property("sampler_type", expected)
            sampler_changed.append(parameter)
        actual = node.get_editor_property("sampler_type")
        if actual != expected:
            raise RuntimeError(f"{spec['label']} could not set sampler for {parameter}")
        sampler_after[parameter] = str(actual)

    mask_nodes = [node for node in expressions
                  if isinstance(node, unreal.MaterialExpressionComponentMask)]
    by_y = {int(node.get_editor_property("material_expression_editor_y")): node
            for node in mask_nodes}
    if len(mask_nodes) != len(spec["masks"]) or set(by_y) != set(spec["masks"]):
        raise RuntimeError(
            f"{spec['label']} ComponentMask graph drifted: {sorted(by_y)}")
    masks_before = {}
    masks_after = {}
    masks_changed = []
    for y, expected_parameter in sorted(spec["masks"].items()):
        node = by_y[y]
        source, before = input_state(material, node)
        masks_before[str(y)] = before
        expected_source = samples[expected_parameter]
        if source != expected_source:
            if source and not MEL.disconnect_material_expressions(node, ""):
                raise RuntimeError(f"{spec['label']} could not disconnect mask y={y}")
            if not MEL.connect_material_expressions(expected_source, "RGB", node, ""):
                raise RuntimeError(f"{spec['label']} could not connect mask y={y}")
            masks_changed.append(y)
        source, after = input_state(material, node)
        if source != expected_source or after["output"] != "RGB":
            raise RuntimeError(f"{spec['label']} mask verification failed at y={y}: {after}")
        masks_after[str(y)] = after
    MEL.recompile_material(material)
    if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
        raise RuntimeError(f"Could not save repaired {spec['label']} master")
    return {
        "path": spec["path"],
        "samplers_before": sampler_before,
        "samplers_after": sampler_after,
        "samplers_changed": sampler_changed,
        "masks_before": masks_before,
        "masks_after": masks_after,
        "masks_changed": masks_changed,
    }


def main():
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    results = {spec["label"]: repair_master(spec) for spec in MASTERS}
    result = {
        "$schema": "lineboss/repair/onefactory/press/native-pbr-master-graphs/v1",
        "status": "PASS__NATIVE_PRESS_MASTER_GRAPHS_REPAIRED",
        "masters": results,
        "content_writes": [spec["path"] for spec in MASTERS],
        "map_loaded_or_saved": [],
        "write_scope": [str(RECEIPT)],
    }
    RECEIPT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log("NATIVE_PRESS_MASTER_GRAPH_REPAIR_PASS")
    unreal.SystemLibrary.quit_editor()


try:
    main()
except Exception as exc:
    failure = {
        "$schema": "lineboss/repair/onefactory/press/native-pbr-master-graphs/v1",
        "status": "FAIL__NATIVE_PRESS_MASTER_GRAPH_REPAIR",
        "error": str(exc),
        "traceback": traceback.format_exc(),
        "content_writes": [],
        "map_loaded_or_saved": [],
        "write_scope": [str(RECEIPT)],
    }
    RECEIPT.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT.write_text(json.dumps(failure, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    unreal.log_error("NATIVE_PRESS_MASTER_GRAPH_REPAIR_FAIL " + str(exc))
    unreal.SystemLibrary.quit_editor()
