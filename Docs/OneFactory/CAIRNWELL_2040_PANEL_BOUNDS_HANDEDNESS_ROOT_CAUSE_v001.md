# Cairnwell 2040 panel bounds — handedness root cause

Snapshot: **2026-08-16**. This supersedes the diagnosis implied by Recovery
v002. The panel meshes are correct. The expectation they were measured against
was wrong.

## What Recovery v002 actually reported

The preserved fail-closed run
`Recovery_v002/20260815T193624Z-b1de90e0` stopped at the first failing field of
the first panel:

```
DOOR_FRONT_LEFT:LOD0 fitted bounds/shared-origin drift: minimum_cm
```

That message names the field but records no measured value, so it cannot
distinguish a bad asset from a bad expectation. A read-only diagnostic pass was
run instead of a further contract iteration, measuring all 11 panels and 33
authored LODs in one editor process.

## Measured result

| Panels | LODs | Result |
|---|---|---|
| Hood, roof, tailgate | 9 | Within tolerance (worst 2.4e-5 cm) |
| 4 doors, 2 fenders, 2 quarter panels | 24 | Y minimum/maximum drift of 166–180 cm |

`dimensions_cm` matched on **every** panel, and X and Z matched on every panel.
Only the Y interval differed, and only by sign:

```
DOOR_FRONT_LEFT LOD0
  measured Y : [ +87.911621, +91.999527 ]
  expected Y : [ -91.999531, -87.911636 ]   negated, endpoints swapped
```

The nine passing LODs are exactly the three centreline panels. Their Y bounds
are symmetric about the car datum, so a sign flip is invisible in them. The
eight left/right panels are offset in Y and expose it. Identical extents plus an
inverted Y interval is a coordinate-handedness signature, not damaged geometry.

## Root cause

[`prepare_cairnwell_2040_panel_modules_v001_contract.py`](../../Scripts/prepare_cairnwell_2040_panel_modules_v001_contract.py)
wrote the raw exporter-space bounds straight into the field named
`expected_unreal_bounds`:

```python
"expected_unreal_bounds": {
    "minimum_cm": minimum,   # bounds_min_cm, exporter space
    "maximum_cm": maximum,   # bounds_max_cm, exporter space
```

The panel exports are authored in a right-handed scene. Unreal imports them with
`convert_scene` enabled, which converts to Unreal's left-handed Z-up space by
negating Y. No conversion was applied, so the contract expected exporter-space
numbers from an Unreal-space measurement.

Because negating an interval reverses it, the Unreal Y minimum derives from the
exporter Y maximum and vice versa. Extent is unchanged, which is why
`dimensions_cm` always agreed and masked the defect.

## Fix

`unreal_space_bounds()` now performs the conversion at the point the expectation
is authored. Re-deriving all 33 expectations from the recorded exporter bounds
and comparing against the measured Unreal values gives a worst-case delta of
**0.000027 cm** against a 0.25 cm tolerance, with zero failures.

The frozen baseline and contract still carry the old exporter-space numbers and
must be regenerated before the panel lane can pass.

## Open question, deliberately not closed here

As imported, `DOOR_FRONT_LEFT` occupies **+Y**, which is Unreal's right-hand
side. Whether the left/right pairs are genuinely mirrored, or whether the naming
follows the source convention and the assembly transforms already account for
it, is a content question. It is not what failed the lane and must not be folded
into this fix. It should be settled before panels are fitted to a body.

## Process finding

The fail-fast bounds assertion records the field that drifted but never the
value, so each diagnosis costs a full editor launch and returns one bit. The
same blind assertion is duplicated in six lane modules:

- `cairnwell_2040_panel_modules_v001.py`
- `cairnwell_2040_runtime_v001.py`
- `assembly_line_native_kit_unreal_runtime_v001.py`
- `import_body_shop_robot_native_v001.py`
- `import_body_shop_support_kit_native_v001.py`
- and the paint-line equivalent

Any lane built on this pattern will reproduce both the phantom failure and the
expensive blind iteration. Reporting actual, expected and delta for every
checked LOD before failing is the durable fix.
