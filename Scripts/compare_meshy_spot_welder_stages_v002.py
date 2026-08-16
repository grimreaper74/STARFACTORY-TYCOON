"""Read-only normalized surface correspondence audit for Meshy robot stages."""

from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree


def parse_args() -> tuple[Path, Path, Path]:
    values = sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
    if len(values) != 3:
        raise RuntimeError(
            "usage: -- <textured.blend> <segmented.blend> <output.json>"
        )
    return tuple(Path(value).resolve() for value in values)  # type: ignore[return-value]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def bounds(objects: list[bpy.types.Object]) -> tuple[Vector, Vector]:
    points = [
        obj.matrix_world @ Vector(corner)
        for obj in objects
        for corner in obj.bound_box
    ]
    low = Vector(tuple(min(point[index] for point in points) for index in range(3)))
    high = Vector(tuple(max(point[index] for point in points) for index in range(3)))
    return low, high


def percentile(sorted_values: list[float], fraction: float) -> float:
    if not sorted_values:
        return math.nan
    position = (len(sorted_values) - 1) * fraction
    lower = int(math.floor(position))
    upper = int(math.ceil(position))
    if lower == upper:
        return sorted_values[lower]
    weight = position - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


def stats(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "count": len(ordered),
        "min_m": round(ordered[0], 8) if ordered else None,
        "p50_m": round(percentile(ordered, 0.50), 8) if ordered else None,
        "p90_m": round(percentile(ordered, 0.90), 8) if ordered else None,
        "p95_m": round(percentile(ordered, 0.95), 8) if ordered else None,
        "p99_m": round(percentile(ordered, 0.99), 8) if ordered else None,
        "max_m": round(ordered[-1], 8) if ordered else None,
        "mean_m": round(sum(ordered) / len(ordered), 8) if ordered else None,
    }


def bvh_for_object(obj: bpy.types.Object, scale: float = 1.0,
                   translation: Vector | None = None) -> BVHTree:
    translation = translation or Vector((0.0, 0.0, 0.0))
    vertices = [
        tuple((obj.matrix_world @ vertex.co) * scale + translation)
        for vertex in obj.data.vertices
    ]
    polygons = [tuple(polygon.vertices) for polygon in obj.data.polygons]
    return BVHTree.FromPolygons(vertices, polygons, all_triangles=False)


def main() -> None:
    textured_path, segmented_path, output_path = parse_args()
    before = {
        str(path): {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in (textured_path, segmented_path)
    }
    bpy.ops.wm.open_mainfile(filepath=str(textured_path), load_ui=False)
    source_meshes = [
        obj for obj in bpy.context.scene.objects if obj.type == "MESH"
    ]
    if len(source_meshes) != 1:
        raise RuntimeError(f"Expected one textured mesh, found {len(source_meshes)}")
    source = source_meshes[0]
    source_low, source_high = bounds([source])

    with bpy.data.libraries.load(str(segmented_path), link=False) as (
        data_from,
        data_to,
    ):
        data_to.objects = list(data_from.objects)
    segmented = sorted(
        (obj for obj in data_to.objects if obj and obj.type == "MESH"),
        key=lambda obj: obj.name,
    )
    for obj in segmented:
        bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.update()
    segmented_low, segmented_high = bounds(segmented)

    source_dimensions = source_high - source_low
    segmented_dimensions = segmented_high - segmented_low
    scale = source_dimensions.dot(segmented_dimensions) / segmented_dimensions.dot(
        segmented_dimensions
    )
    source_center = (source_low + source_high) * 0.5
    segmented_center = (segmented_low + segmented_high) * 0.5
    translation = source_center - segmented_center * scale
    fitted_dimensions = segmented_dimensions * scale
    residual = fitted_dimensions - source_dimensions

    source_bvh = bvh_for_object(source)
    segmented_total_vertices = sum(len(obj.data.vertices) for obj in segmented)
    target_segmented_samples = 24000
    segmented_stride = max(1, segmented_total_vertices // target_segmented_samples)
    global_index = 0
    part_to_source: dict[str, list[float]] = {obj.name: [] for obj in segmented}
    all_part_distances: list[float] = []
    for obj in segmented:
        for vertex in obj.data.vertices:
            take = global_index % segmented_stride == 0
            global_index += 1
            if not take:
                continue
            point = (obj.matrix_world @ vertex.co) * scale + translation
            nearest = source_bvh.find_nearest(point)
            if nearest[0] is None:
                continue
            distance = float(nearest[3])
            part_to_source[obj.name].append(distance)
            all_part_distances.append(distance)

    source_vertices = [source.matrix_world @ vertex.co for vertex in source.data.vertices]
    target_source_samples = 8000
    source_stride = max(1, len(source_vertices) // target_source_samples)
    sampled_source = source_vertices[::source_stride]
    best = [math.inf] * len(sampled_source)
    second = [math.inf] * len(sampled_source)
    labels: list[str | None] = [None] * len(sampled_source)
    for part in segmented:
        tree = bvh_for_object(part, scale, translation)
        for index, point in enumerate(sampled_source):
            nearest = tree.find_nearest(point)
            if nearest[0] is None:
                continue
            distance = float(nearest[3])
            if distance < best[index]:
                second[index] = best[index]
                best[index] = distance
                labels[index] = part.name
            elif distance < second[index]:
                second[index] = distance
        del tree

    classification_counts: dict[str, int] = {}
    for label in labels:
        if label is not None:
            classification_counts[label] = classification_counts.get(label, 0) + 1
    finite_best = [value for value in best if math.isfinite(value)]
    margins = [
        second[index] - best[index]
        for index in range(len(best))
        if math.isfinite(best[index]) and math.isfinite(second[index])
    ]
    ambiguity_threshold_m = 0.002
    ambiguous = sum(1 for margin in margins if margin < ambiguity_threshold_m)

    after = {
        str(path): {"bytes": path.stat().st_size, "sha256": sha256(path)}
        for path in (textured_path, segmented_path)
    }
    payload = {
        "$schema": "lineboss/audit/meshy-spot-welder-stage-comparison-v002/v1",
        "textured_source": str(textured_path),
        "segmented_source": str(segmented_path),
        "sources_before": before,
        "sources_after": after,
        "sources_unchanged": before == after,
        "uniform_alignment": {
            "scale": round(float(scale), 10),
            "translation": [round(float(value), 10) for value in translation],
            "textured_envelope_dimensions_m": [
                round(float(value), 9) for value in source_dimensions
            ],
            "segmented_envelope_dimensions_source_units": [
                round(float(value), 9) for value in segmented_dimensions
            ],
            "fitted_segmented_dimensions_m": [
                round(float(value), 9) for value in fitted_dimensions
            ],
            "envelope_fit_residual_m": [
                round(float(value), 9) for value in residual
            ],
            "max_absolute_envelope_residual_m": round(
                max(abs(float(value)) for value in residual), 9
            ),
        },
        "segmented_to_textured_surface_distance": stats(all_part_distances),
        "per_part_to_textured_surface_distance": {
            name: stats(values) for name, values in part_to_source.items()
        },
        "textured_to_segmented_surface_distance": stats(finite_best),
        "nearest_part_classification": {
            "sample_count": len(sampled_source),
            "counts": classification_counts,
            "second_nearest_margin": stats(margins),
            "ambiguity_threshold_m": ambiguity_threshold_m,
            "ambiguous_sample_count": ambiguous,
            "ambiguous_sample_fraction": round(ambiguous / len(margins), 8)
            if margins
            else None,
        },
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("LINE_BOSS_MESHY_SPOT_WELDER_STAGE_COMPARISON_V002_PASS", output_path)


if __name__ == "__main__":
    main()
