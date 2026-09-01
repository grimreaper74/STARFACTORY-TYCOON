"""Palette-grade the concept batch, v002 (2026-09-01).

Supersedes v001, whose node graph wired SILENTLY WRONG: none of the
connect calls were checked, a broken BaseColor chain compiles to
black, and the frame stayed exactly as dark as before - the failure
mode this repo exists to refuse. v002:

  - checks EVERY connect call and fails closed with the pin names
  - drops the saturation-accent branch entirely; the simplest graph
    that can work ships first (two-tone by luminance, lifted), and
    accents come back in a v003 only after a frame proves this one
  - reuses the v001 material instances (same parameter names) - only
    the master is rebuilt, under the same asset name so the MIs pick
    it up without reassignment.
"""
import json
import os
import unreal

RECEIPT_NAME = "concept_material_grade_v002.json"
PROPS_ROOT = "/Game/Spacecraft/Props"
MASTER_NAME = "M_LB_ConceptGraded_v001"

GRAPHITE = (0.069, 0.077, 0.084)
HOUSING_PALE = (0.68, 0.65, 0.60)


class GradeError(Exception):
    pass


def must_connect(result, what):
    if not result:
        raise GradeError("CONNECT FAILED: %s" % what)


def rebuild_master():
    lib = unreal.MaterialEditingLibrary
    master_path = "%s/%s" % (PROPS_ROOT, MASTER_NAME)
    mat = unreal.load_asset(master_path)
    if mat is None:
        raise GradeError("master missing at %s" % master_path)
    lib.delete_all_material_expressions(mat)

    def node(cls, x, y):
        made = lib.create_material_expression(mat, cls, x, y)
        if made is None:
            raise GradeError("create failed: %s" % cls.get_name())
        return made

    tex = node(unreal.MaterialExpressionTextureSampleParameter2D,
               -1000, 0)
    tex.set_editor_property("parameter_name", "BaseTex")

    desat = node(unreal.MaterialExpressionDesaturation, -700, 0)
    must_connect(lib.connect_material_expressions(tex, "RGB", desat, ""),
                 "tex.RGB -> desat")

    lift = node(unreal.MaterialExpressionMultiply, -520, 0)
    lift.set_editor_property("const_b", 1.7)
    must_connect(lib.connect_material_expressions(desat, "", lift, "A"),
                 "desat -> lift.A")

    clamp = node(unreal.MaterialExpressionClamp, -380, 0)
    must_connect(lib.connect_material_expressions(clamp_input(lift), "",
                                                  clamp, ""),
                 "lift -> clamp")

    graphite = node(unreal.MaterialExpressionConstant3Vector, -520, 160)
    graphite.set_editor_property(
        "constant", unreal.LinearColor(*GRAPHITE, 1.0))
    pale = node(unreal.MaterialExpressionConstant3Vector, -520, 300)
    pale.set_editor_property(
        "constant", unreal.LinearColor(*HOUSING_PALE, 1.0))

    two_tone = node(unreal.MaterialExpressionLinearInterpolate, -180, 40)
    must_connect(lib.connect_material_expressions(
        graphite, "", two_tone, "A"), "graphite -> lerp.A")
    must_connect(lib.connect_material_expressions(
        pale, "", two_tone, "B"), "pale -> lerp.B")
    must_connect(lib.connect_material_expressions(
        clamp, "", two_tone, "Alpha"), "clamp -> lerp.Alpha")

    must_connect(lib.connect_material_property(
        two_tone, "", unreal.MaterialProperty.MP_BASE_COLOR),
        "lerp -> BaseColor")

    rough = node(unreal.MaterialExpressionScalarParameter, -180, 300)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.55)
    must_connect(lib.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS),
        "rough -> Roughness")

    lib.recompile_material(mat)
    unreal.EditorAssetLibrary.save_loaded_asset(mat)
    return mat


def clamp_input(node_obj):
    return node_obj


def main():
    project = unreal.SystemLibrary.get_project_directory()
    audit_dir = os.path.join(project, "Saved", "Audits", "Spacecraft")
    os.makedirs(audit_dir, exist_ok=True)
    receipt_path = os.path.join(audit_dir, RECEIPT_NAME)
    if os.path.exists(receipt_path):
        unreal.log_error("RECEIPT EXISTS: %s - author v003." %
                         receipt_path)
        return
    try:
        rebuild_master()
        status = "PASS__MASTER_REBUILT"
        unreal.log("MATERIAL GRADE v002: %s" % status)
    except GradeError as err:
        status = "FAIL_CLOSED__%s" % err
        unreal.log_error(str(err))
    with open(receipt_path, "w", encoding="utf-8") as handle:
        json.dump({"$schema": "lineboss/audit/concept-material-grade/v1",
                   "status": status}, handle, indent=2)


main()
