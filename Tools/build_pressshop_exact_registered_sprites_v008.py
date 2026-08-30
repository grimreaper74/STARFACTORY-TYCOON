"""Build an isolated Press Shop map with physical full-canvas machine sprites.

The selected beauty pack preserves each dimensioned orthographic render's complete
camera canvas and already bakes the assembly yaw seen by the locked
game camera. This builder duplicates unopened v007 first, projects every hidden
proxy's eight transformed local-bound corners into camera screen right/up, and
applies one uniform physical scale from the source orthographic height. Alpha
bounds are machine-source QA only and never drive machine scale or offset.
"""

import hashlib
import json
import math
import struct
import zlib
from pathlib import Path

import unreal


PROJECT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SOURCE_MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007/Maps/LB_PressShop_Factorio2p5D_IndividualSprites_v007"
TARGET_MAP = "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_ExactSprites_v008/Maps/LB_PressShop_Factorio2p5D_ExactSprites_v008"
SOURCE_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_IndividualSprites_v007" / "Maps" / "LB_PressShop_Factorio2p5D_IndividualSprites_v007.umap"
SOURCE_FILE_SHA256 = "0e1bc9ddbf753a790955375eba8d0b274eb7d48cb336a84a82df431f85aa9624"
TARGET_FILE = PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShopFactorio2p5D_ExactSprites_v008" / "Maps" / "LB_PressShop_Factorio2p5D_ExactSprites_v008.umap"
REPORT = PROJECT / "Saved" / "Audits" / "PressShopIntegration" / "pressshop_exact_registered_sprites_v008_build.json"
MACHINE_SOURCE_ART = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "PressShop_ExactRegisteredSprites_v002"
MACHINE_MANIFEST = MACHINE_SOURCE_ART / "exact_registered_sprite_manifest_v002.json"
MACHINE_MANIFEST_SHA256 = "e93dcbbc04c15fb9fcfe02ae691098b6201d3906fadffc6e460ac53bbe1c49fc"
LEGACY_SOURCE_ART = PROJECT / "SourceAssets" / "Candidate" / "PressShop" / "PressShop2D_Sprites_v001"
FINAL_ASSET_ROOT = "/Game/LineBoss/Candidates/PressShop/PressShop2DSprites_ExactRegisteredBeauty_v002"
FINAL_TEXTURE_ROOT = FINAL_ASSET_ROOT + "/Textures"
FINAL_MATERIAL_ROOT = FINAL_ASSET_ROOT + "/Materials"
CAMERA_LABEL = "CAM | 2.5D full Press Shop overview"
WORLD_PROCESS_FLOW = unreal.Vector(1.0, 0.0, 0.0)
PLANE_ASSET = "/Engine/BasicShapes/Plane.Plane"
MATERIAL_CLIP_VALUE = 0.08
ALPHA_THRESHOLD_BYTE = 21
CARD_DEPTH_CM = 40.0
CAMERA_ANGLE_TOLERANCE_DEG = 0.05
CAMERA_LOCATION_TOLERANCE_CM = 0.05
CAMERA_ORTHO_WIDTH_TOLERANCE_CM = 0.05
BASIS_ANGLE_TOLERANCE_DEG = 0.05
BASIS_DOT_MIN = math.cos(math.radians(BASIS_ANGLE_TOLERANCE_DEG))
BASIS_NUMERIC_TOLERANCE = 0.00001
MAX_PIXEL_SCALE_DISTORTION = 0.02
MAX_PHYSICAL_SCALE_ERROR = 0.02
DISTORTION_NUMERIC_TOLERANCE = 0.000000001
MIN_GEOMETRIC_TOLERANCE_CM = 0.05
RELATIVE_GEOMETRIC_TOLERANCE = 0.00001
MANIFEST_NUMERIC_TOLERANCE = 0.000001
ACCEPTED_MANIFEST_STATUS_PREFIX = "PASS_EXACT_REGISTERED_"
MACHINE_REGISTRATION_MODE = "FULL_CANVAS_PHYSICAL"
MACHINE_ORIENTATION_MODE = "LOCKED_CAMERA_SCREEN_BAKED"
LEGACY_REGISTRATION_MODE = "LEGACY_ALPHA_ENVELOPE"

PROTECTED_MAPS = {
    PROJECT / "Content" / "LineBoss" / "Maps" / "LB_PressShop_BuilderAuthorityCandidate_v438.umap": "5029c9d827d9a1d72c12f27ee757c9bc1e47febd5006ce6d7ba319aad2e7fec8",
    PROJECT / "Content" / "LineBoss" / "Candidates" / "PressShop" / "PressShop2126_v002" / "Maps" / "LB_PressShop_2126_Steam_v002.umap": "cc09cf46d33e8a562d97f5a3bc35a5b42c9582d8e4650cf315694ebf340e4aa0",
}

EXPECTED_MACHINE_LABELS = {
    "S01": ("2.5D full | 01 | coil-free autonomous feeder", "2.5D sprite art | S01 straightener / servo feeder"),
    "S02": ("2.5D full | 02 | draw / form portal press", "2.5D sprite art | S02 draw-form portal press"),
    "S03": ("2.5D full | 03 | trim press", "2.5D sprite art | S03 trim press"),
    "S04": ("2.5D full | 04 | pierce press", "2.5D sprite art | S04 pierce press"),
    "S05": ("2.5D full | 05 | flange / hem press", "2.5D sprite art | S05 flange / hem press"),
    "S06": ("2.5D full | 06 | vision / outfeed press", "2.5D sprite art | S06 vision / reject press"),
}

CONVEYOR_SPEC = {
    "kind": "transfer_conveyor",
    "registration_mode": LEGACY_REGISTRATION_MODE,
    "source_root": LEGACY_SOURCE_ART,
    "source": "T_LB_PS_TransferConveyor_Topdown_v001.png",
    "canvas_px": (2172, 724),
    "alpha_bbox_px": (48, 45, 2124, 664),
    "edge_alpha_max": 1,
}


def fail(message):
    raise RuntimeError("PRESSSHOP_EXACT_SPRITES_V008_BUILD_FAIL: " + message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest().lower()


def numeric_tuple(value, size, context):
    if not isinstance(value, (list, tuple)) or len(value) != size:
        fail("{} must contain exactly {} values".format(context, size))
    try:
        result = tuple(float(item) for item in value)
    except (TypeError, ValueError):
        fail("{} contains a non-numeric value".format(context))
    if not all(math.isfinite(item) for item in result):
        fail("{} contains a non-finite value".format(context))
    return result


def require_close(actual, expected, context, tolerance=MANIFEST_NUMERIC_TOLERANCE):
    if len(actual) != len(expected) or any(abs(a - b) > tolerance for a, b in zip(actual, expected)):
        fail("{} changed: {} != {}".format(context, actual, expected))


def load_machine_manifest():
    if not MACHINE_MANIFEST.is_file():
        fail("final sprite manifest is missing: {}".format(MACHINE_MANIFEST))
    actual_manifest_hash = digest(MACHINE_MANIFEST)
    if actual_manifest_hash != MACHINE_MANIFEST_SHA256:
        fail("final sprite manifest hash changed: {}".format(actual_manifest_hash))
    try:
        manifest = json.loads(MACHINE_MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        fail("could not parse final sprite manifest: {}".format(error))
    status = manifest.get("status") if isinstance(manifest, dict) else None
    if not isinstance(status, str) or not status.startswith(ACCEPTED_MANIFEST_STATUS_PREFIX):
        fail("final sprite manifest status is not accepted")
    if manifest.get("alpha_threshold") != ALPHA_THRESHOLD_BYTE:
        fail("manifest alpha threshold does not match the material clip contract")
    camera_contract = manifest.get("camera_contract")
    if not isinstance(camera_contract, dict) or camera_contract.get("projection") != "orthographic":
        fail("manifest camera projection is not orthographic")
    camera_rotation = numeric_tuple(
        (camera_contract.get("pitch_deg"), camera_contract.get("yaw_deg"), camera_contract.get("roll_deg")),
        3,
        "manifest camera rotation",
    )
    if camera_rotation[0] < -90.0 or camera_rotation[0] > 90.0:
        fail("manifest camera pitch is outside Unreal Rotator range")
    target_map_location_raw = camera_contract.get("target_map_location_cm")
    target_map_ortho_width_raw = camera_contract.get("target_map_ortho_width_cm")
    if (target_map_location_raw is None) != (target_map_ortho_width_raw is None):
        fail("manifest target-map camera location and orthographic width must be supplied together")
    if target_map_location_raw is None:
        target_map_location_cm = None
        target_map_ortho_width_cm = None
    else:
        target_map_location_cm = numeric_tuple(
            target_map_location_raw,
            3,
            "manifest target-map camera location",
        )
        try:
            target_map_ortho_width_cm = float(target_map_ortho_width_raw)
        except (TypeError, ValueError):
            fail("manifest target-map orthographic width is non-numeric")
        if not math.isfinite(target_map_ortho_width_cm) or target_map_ortho_width_cm <= 0.0:
            fail("manifest target-map orthographic width is invalid")
    expected_forward = (
        math.cos(math.radians(camera_rotation[0])) * math.cos(math.radians(camera_rotation[1])),
        math.cos(math.radians(camera_rotation[0])) * math.sin(math.radians(camera_rotation[1])),
        math.sin(math.radians(camera_rotation[0])),
    )
    rows = manifest.get("stations")
    if not isinstance(rows, list) or len(rows) != len(EXPECTED_MACHINE_LABELS):
        fail("manifest must contain exactly the six S01-S06 machine rows")
    by_station = {}
    for row in rows:
        if not isinstance(row, dict):
            fail("manifest station row is not an object")
        station = row.get("station")
        if station not in EXPECTED_MACHINE_LABELS or station in by_station:
            fail("manifest contains an unexpected or duplicate station: {}".format(station))
        proxy_label, sprite_label = EXPECTED_MACHINE_LABELS[station]
        if row.get("proxy_label") != proxy_label or row.get("sprite_label") != sprite_label:
            fail("manifest actor labels changed for {}".format(station))
        source_name = row.get("output_png")
        if (
            not isinstance(source_name, str)
            or Path(source_name).name != source_name
            or Path(source_name).suffix.lower() != ".png"
            or station not in source_name
        ):
            fail("manifest source filename changed for {}".format(station))
        source_sha256 = str(row.get("final_png_sha256", "")).lower()
        if source_sha256 != str(row.get("output_sha256", "")).lower():
            fail("manifest final/output hashes disagree for {}".format(station))
        if len(source_sha256) != 64 or any(character not in "0123456789abcdef" for character in source_sha256):
            fail("manifest final PNG hash is invalid for {}".format(station))
        canvas_raw = numeric_tuple(row.get("canvas_px"), 2, "{} canvas".format(station))
        canvas_px = tuple(int(value) for value in canvas_raw)
        if canvas_raw != canvas_px or canvas_px != (2048, 2048):
            fail("{} final canvas must be exactly 2048x2048".format(station))
        bbox_raw = numeric_tuple(
            row.get("alpha_bbox_px_at_21_png_top_left"),
            4,
            "{} alpha bbox".format(station),
        )
        bbox_px = tuple(int(value) for value in bbox_raw)
        if bbox_raw != bbox_px:
            fail("{} alpha bbox must contain integer pixel edges".format(station))
        source_ortho_height_cm = float(row.get("source_ortho_height_cm", 0.0))
        if not math.isfinite(source_ortho_height_cm) or source_ortho_height_cm <= 0.0:
            fail("{} source orthographic height is invalid".format(station))
        ortho_scale_m = float(row.get("ortho_scale_m", 0.0))
        if abs(source_ortho_height_cm - ortho_scale_m * 100.0) > MANIFEST_NUMERIC_TOLERANCE:
            fail("{} metre/centimetre orthographic scales disagree".format(station))
        projected_size_cm = numeric_tuple(
            row.get("source_projected_obb_size_cm"),
            2,
            "{} source projected OBB".format(station),
        )
        if min(projected_size_cm) <= 0.0:
            fail("{} source projected OBB is degenerate".format(station))
        centre_px = numeric_tuple(
            row.get("source_projected_obb_center_px"),
            2,
            "{} source projected centre".format(station),
        )
        require_close(
            centre_px,
            (canvas_px[0] * 0.5, canvas_px[1] * 0.5),
            "{} source projected centre".format(station),
        )
        expected_canvas_cm = (
            source_ortho_height_cm * canvas_px[0] / float(canvas_px[1]),
            source_ortho_height_cm,
        )
        full_canvas_cm = numeric_tuple(row.get("full_canvas_size_cm"), 2, "{} full canvas".format(station))
        require_close(full_canvas_cm, expected_canvas_cm, "{} full canvas physical size".format(station))
        if projected_size_cm[0] > full_canvas_cm[0] or projected_size_cm[1] > full_canvas_cm[1]:
            fail("{} source projected OBB does not fit inside its full canvas".format(station))
        require_close(
            numeric_tuple(
                (row.get("camera_pitch_deg"), row.get("camera_yaw_deg"), row.get("camera_roll_deg")),
                3,
                "{} camera rotation".format(station),
            ),
            camera_rotation,
            "{} camera rotation".format(station),
        )
        require_close(
            numeric_tuple(row.get("camera_forward"), 3, "{} camera forward".format(station)),
            expected_forward,
            "{} camera forward".format(station),
        )
        if row.get("registration_mode") != MACHINE_REGISTRATION_MODE:
            fail("{} is not a full-canvas physical registration".format(station))
        if row.get("orientation_mode") != MACHINE_ORIENTATION_MODE:
            fail("{} is not locked-camera-screen baked".format(station))
        if row.get("png_u_basis") != "camera_screen_right" or row.get("png_v_down_basis") != "-camera_screen_up":
            fail("{} PNG camera-screen basis changed".format(station))
        if row.get("assembly_yaw_baked") is not True:
            fail("{} assembly yaw is not declared baked".format(station))
        if row.get("outer_envelope_exact_to_dimensioned_source") is not True or row.get("non_uniform_stretch") is not False:
            fail("{} final beauty registration contract failed".format(station))
        require_close(
            numeric_tuple(row.get("process_world_axis"), 3, "{} process world axis".format(station)),
            (1.0, 0.0, 0.0),
            "{} process world axis".format(station),
        )
        require_close(
            numeric_tuple(row.get("proxy_process_axis_local"), 3, "{} proxy process axis".format(station)),
            (1.0, 0.0, 0.0),
            "{} proxy process axis".format(station),
        )
        expected_texture = row.get("texture_asset")
        expected_material = row.get("material_asset")
        if (
            not isinstance(expected_texture, str)
            or not expected_texture.startswith(FINAL_TEXTURE_ROOT + "/")
            or "." in expected_texture.rsplit("/", 1)[-1]
            or station not in expected_texture.rsplit("/", 1)[-1]
            or not isinstance(expected_material, str)
            or not expected_material.startswith(FINAL_MATERIAL_ROOT + "/")
            or "." in expected_material.rsplit("/", 1)[-1]
            or station not in expected_material.rsplit("/", 1)[-1]
        ):
            fail("{} final Unreal asset lane changed".format(station))
        try:
            assembly_yaw_deg_baked = float(row.get("assembly_yaw_deg"))
        except (TypeError, ValueError):
            fail("{} assembly yaw is non-numeric".format(station))
        if not math.isfinite(assembly_yaw_deg_baked):
            fail("{} assembly yaw is non-finite".format(station))
        by_station[station] = {
            "kind": "machine",
            "station": station,
            "proxy": proxy_label,
            "sprite": sprite_label,
            "source_root": MACHINE_SOURCE_ART,
            "source": source_name,
            "source_sha256": source_sha256,
            "canvas_px": canvas_px,
            "alpha_bbox_px": bbox_px,
            "edge_alpha_max": int(row.get("canvas_edge_alpha_max", -1)),
            "source_ortho_height_cm": source_ortho_height_cm,
            "source_projected_obb_size_cm": projected_size_cm,
            "source_projected_obb_center_px": centre_px,
            "full_canvas_size_cm": full_canvas_cm,
            "registration_mode": MACHINE_REGISTRATION_MODE,
            "orientation_mode": MACHINE_ORIENTATION_MODE,
            "assembly_yaw_deg_baked": assembly_yaw_deg_baked,
            "texture_asset": expected_texture,
            "material_asset": expected_material,
        }
    if set(by_station) != set(EXPECTED_MACHINE_LABELS):
        fail("manifest station set changed")
    return manifest, actual_manifest_hash, {
        "rotation": camera_rotation,
        "target_map_location_cm": target_map_location_cm,
        "target_map_ortho_width_cm": target_map_ortho_width_cm,
    }, tuple(
        by_station[station] for station in sorted(by_station)
    )


def dot(a, b):
    return a.x * b.x + a.y * b.y + a.z * b.z


def cross(a, b):
    return unreal.Vector(
        a.y * b.z - a.z * b.y,
        a.z * b.x - a.x * b.z,
        a.x * b.y - a.y * b.x,
    )


def add(a, b):
    return unreal.Vector(a.x + b.x, a.y + b.y, a.z + b.z)


def subtract(a, b):
    return unreal.Vector(a.x - b.x, a.y - b.y, a.z - b.z)


def scaled(vector, scalar):
    return unreal.Vector(vector.x * scalar, vector.y * scalar, vector.z * scalar)


def length(vector):
    return math.sqrt(dot(vector, vector))


def unit(vector):
    size = length(vector)
    if size < 0.000001:
        fail("cannot normalize zero-length vector")
    return unreal.Vector(vector.x / size, vector.y / size, vector.z / size)


def projected(vector, normal):
    return unit(unreal.Vector(
        vector.x - normal.x * dot(vector, normal),
        vector.y - normal.y * dot(vector, normal),
        vector.z - normal.z * dot(vector, normal),
    ))


def find_one(actors, label):
    matches = [actor for actor in actors if actor.get_actor_label() == label]
    if len(matches) != 1:
        fail("expected exactly one actor {!r}; found {}".format(label, len(matches)))
    return matches[0]


def validate_basis(basis_x, basis_y, basis_z, context):
    lengths = (length(basis_x), length(basis_y), length(basis_z))
    if max(abs(value - 1.0) for value in lengths) > BASIS_NUMERIC_TOLERANCE:
        fail("{} basis is not unit length: {}".format(context, lengths))
    orthogonality = (
        abs(dot(basis_x, basis_y)),
        abs(dot(basis_x, basis_z)),
        abs(dot(basis_y, basis_z)),
    )
    if max(orthogonality) > BASIS_NUMERIC_TOLERANCE:
        fail("{} basis is not orthogonal: {}".format(context, orthogonality))
    handedness = dot(unit(cross(basis_x, basis_y)), basis_z)
    if handedness < BASIS_DOT_MIN:
        fail("{} basis is not right handed: {}".format(context, handedness))


def validate_camera(camera, expected_contract):
    if not isinstance(camera, unreal.CameraActor):
        fail("locked overview actor is not a CameraActor")
    rotation = camera.get_actor_rotation()
    expected_rotation = expected_contract["rotation"]
    actual = (rotation.pitch, rotation.yaw, rotation.roll)
    if any(abs(value - expected) > CAMERA_ANGLE_TOLERANCE_DEG for value, expected in zip(actual, expected_rotation)):
        fail("locked camera rotation changed: {}".format(rotation))
    component = camera.get_component_by_class(unreal.CameraComponent)
    if component is None:
        fail("locked overview camera has no CameraComponent")
    if component.get_editor_property("projection_mode") != unreal.CameraProjectionMode.ORTHOGRAPHIC:
        fail("locked overview camera is not orthographic")
    expected_location = expected_contract["target_map_location_cm"]
    expected_ortho_width = expected_contract["target_map_ortho_width_cm"]
    if expected_location is not None:
        location = camera.get_actor_location()
        location_error = max(
            abs(location.x - expected_location[0]),
            abs(location.y - expected_location[1]),
            abs(location.z - expected_location[2]),
        )
        if location_error > CAMERA_LOCATION_TOLERANCE_CM:
            fail("locked target-map camera location changed: {}".format(location))
        actual_ortho_width = float(component.get_editor_property("ortho_width"))
        if abs(actual_ortho_width - expected_ortho_width) > CAMERA_ORTHO_WIDTH_TOLERANCE_CM:
            fail("locked target-map camera orthographic width changed: {}".format(actual_ortho_width))
    camera_x = unit(unreal.MathLibrary.get_forward_vector(rotation))
    camera_y = unit(unreal.MathLibrary.get_right_vector(rotation))
    camera_z = unit(unreal.MathLibrary.get_up_vector(rotation))
    validate_basis(camera_x, camera_y, camera_z, "camera")
    return rotation, camera_x, camera_y, camera_z


def configure_target_camera(camera, expected_contract):
    if not isinstance(camera, unreal.CameraActor):
        fail("locked overview actor is not a CameraActor")
    expected_rotation = expected_contract["rotation"]
    inherited_rotation = camera.get_actor_rotation()
    inherited_rotation_values = (
        inherited_rotation.pitch,
        inherited_rotation.yaw,
        inherited_rotation.roll,
    )
    has_target_map_framing = expected_contract["target_map_location_cm"] is not None
    if (
        not has_target_map_framing
        and any(
            abs(value - expected) > CAMERA_ANGLE_TOLERANCE_DEG
            for value, expected in zip(inherited_rotation_values, expected_rotation)
        )
    ):
        fail(
            "manifest changes the inherited camera basis but omits "
            "camera_contract.target_map_location_cm and target_map_ortho_width_cm"
        )
    component = camera.get_component_by_class(unreal.CameraComponent)
    if component is None:
        fail("locked overview camera has no CameraComponent")
    if component.get_editor_property("projection_mode") != unreal.CameraProjectionMode.ORTHOGRAPHIC:
        fail("inherited overview camera is not orthographic")
    if has_target_map_framing:
        location = expected_contract["target_map_location_cm"]
        camera.set_actor_location(unreal.Vector(location[0], location[1], location[2]), False, False)
        component.set_editor_property(
            "ortho_width",
            expected_contract["target_map_ortho_width_cm"],
        )
    desired = unreal.Rotator(
        pitch=expected_rotation[0],
        yaw=expected_rotation[1],
        roll=expected_rotation[2],
    )
    if not camera.set_actor_rotation(desired, False):
        fail("could not apply manifest camera rotation in duplicated v008")
    return validate_camera(camera, expected_contract)


def paeth_predictor(left, up, upper_left):
    estimate = left + up - upper_left
    distance_left = abs(estimate - left)
    distance_up = abs(estimate - up)
    distance_upper_left = abs(estimate - upper_left)
    if distance_left <= distance_up and distance_left <= distance_upper_left:
        return left
    if distance_up <= distance_upper_left:
        return up
    return upper_left


def read_png_alpha_bbox(path, threshold):
    """Return canvas, half-open alpha bbox, and maximum canvas-edge alpha."""
    data = path.read_bytes()
    if data[:8] != b"\x89PNG\r\n\x1a\n":
        fail("source is not a PNG: {}".format(path))
    offset = 8
    width = height = None
    compressed = bytearray()
    saw_end = False
    while offset < len(data):
        if offset + 12 > len(data):
            fail("truncated PNG chunk in {}".format(path))
        chunk_size = struct.unpack(">I", data[offset:offset + 4])[0]
        chunk_type = data[offset + 4:offset + 8]
        chunk_start = offset + 8
        chunk_end = chunk_start + chunk_size
        crc_end = chunk_end + 4
        if crc_end > len(data):
            fail("truncated PNG payload in {}".format(path))
        payload = data[chunk_start:chunk_end]
        expected_crc = struct.unpack(">I", data[chunk_end:crc_end])[0]
        actual_crc = zlib.crc32(chunk_type + payload) & 0xFFFFFFFF
        if actual_crc != expected_crc:
            fail("PNG CRC mismatch in {}".format(path))
        if chunk_type == b"IHDR":
            if len(payload) != 13:
                fail("invalid PNG IHDR in {}".format(path))
            width, height, bit_depth, colour_type, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            if (bit_depth, colour_type, compression, filtering, interlace) != (8, 6, 0, 0, 0):
                fail("source PNG must be non-interlaced 8-bit RGBA: {}".format(path))
        elif chunk_type == b"IDAT":
            compressed.extend(payload)
        elif chunk_type == b"IEND":
            saw_end = True
            break
        offset = crc_end
    if not saw_end or width is None or height is None or not compressed:
        fail("incomplete PNG structure: {}".format(path))
    try:
        raw = zlib.decompress(bytes(compressed))
    except zlib.error as error:
        fail("could not decompress {}: {}".format(path, error))
    bytes_per_pixel = 4
    stride = width * bytes_per_pixel
    expected_size = height * (stride + 1)
    if len(raw) != expected_size:
        fail("unexpected decompressed PNG size for {}: {} != {}".format(path, len(raw), expected_size))
    previous = bytearray(stride)
    left = top = None
    right = bottom = None
    edge_alpha_max = 0
    cursor = 0
    for y in range(height):
        filter_type = raw[cursor]
        cursor += 1
        scanline = bytearray(raw[cursor:cursor + stride])
        cursor += stride
        if filter_type not in (0, 1, 2, 3, 4):
            fail("unsupported PNG filter {} in {}".format(filter_type, path))
        for index in range(stride):
            raw_value = scanline[index]
            prior_x = scanline[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            prior_y = previous[index]
            prior_xy = previous[index - bytes_per_pixel] if index >= bytes_per_pixel else 0
            if filter_type == 1:
                predictor = prior_x
            elif filter_type == 2:
                predictor = prior_y
            elif filter_type == 3:
                predictor = (prior_x + prior_y) // 2
            elif filter_type == 4:
                predictor = paeth_predictor(prior_x, prior_y, prior_xy)
            else:
                predictor = 0
            scanline[index] = (raw_value + predictor) & 0xFF
        for x in range(width):
            alpha = scanline[x * bytes_per_pixel + 3]
            if x in (0, width - 1) or y in (0, height - 1):
                edge_alpha_max = max(edge_alpha_max, alpha)
            if alpha >= threshold:
                left = x if left is None else min(left, x)
                top = y if top is None else min(top, y)
                right = x + 1 if right is None else max(right, x + 1)
                bottom = y + 1 if bottom is None else max(bottom, y + 1)
        previous = scanline
    if left is None:
        fail("source PNG has no alpha at threshold {}: {}".format(threshold, path))
    return (width, height), (left, top, right, bottom), edge_alpha_max


def validated_alpha_spec(spec):
    source_root = spec.get("source_root")
    if not isinstance(source_root, Path):
        fail("source root is missing for {}".format(spec.get("source")))
    path = source_root / spec["source"]
    if not path.is_file():
        fail("source PNG is missing: {}".format(path))
    canvas_px, bbox_px, edge_alpha_max = read_png_alpha_bbox(path, ALPHA_THRESHOLD_BYTE)
    if tuple(spec["canvas_px"]) != canvas_px:
        fail("source canvas changed for {}: {} != {}".format(path.name, canvas_px, spec["canvas_px"]))
    if tuple(spec["alpha_bbox_px"]) != bbox_px:
        fail("alpha >= {} bbox changed for {}: {} != {}".format(ALPHA_THRESHOLD_BYTE, path.name, bbox_px, spec["alpha_bbox_px"]))
    left, top, right, bottom = bbox_px
    if left <= 0 or top <= 0 or right >= canvas_px[0] or bottom >= canvas_px[1]:
        fail("visible alpha touches the source canvas edge: {}".format(path))
    if edge_alpha_max != int(spec.get("edge_alpha_max", 0)):
        fail("canvas-edge alpha changed for {}: {}".format(path.name, edge_alpha_max))
    source_hash = digest(path)
    expected_hash = spec.get("source_sha256")
    if expected_hash is not None and source_hash != expected_hash:
        fail("source PNG hash changed for {}: {}".format(path.name, source_hash))
    return {
        "path": path,
        "sha256": source_hash,
        "canvas_px": canvas_px,
        "bbox_px": bbox_px,
        "edge_alpha_max": edge_alpha_max,
    }


def transformed_mesh_bounds(actor):
    if not isinstance(actor, unreal.StaticMeshActor):
        fail("proxy is not a StaticMeshActor: {}".format(actor.get_actor_label()))
    component = actor.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    if not isinstance(mesh, unreal.StaticMesh):
        fail("proxy has no StaticMesh: {}".format(actor.get_actor_label()))
    local_box = mesh.get_bounding_box()
    transform = component.get_world_transform()
    corners = []
    for x in (local_box.min.x, local_box.max.x):
        for y in (local_box.min.y, local_box.max.y):
            for z in (local_box.min.z, local_box.max.z):
                corners.append(transform.transform_location(unreal.Vector(x, y, z)))
    if len(corners) != 8:
        fail("could not produce eight transformed mesh-bound corners")
    local_origin_world = transform.transform_location(unreal.Vector(0.0, 0.0, 0.0))
    local_flow_world = transform.transform_location(unreal.Vector(1.0, 0.0, 0.0))
    flow_world = unit(subtract(local_flow_world, local_origin_world))
    return component, mesh, local_box, corners, flow_world


def projected_obb(corners, basis_x, basis_y, basis_z):
    x_values = [dot(point, basis_x) for point in corners]
    y_values = [dot(point, basis_y) for point in corners]
    z_values = [dot(point, basis_z) for point in corners]
    return {
        "min_x": min(x_values),
        "max_x": max(x_values),
        "min_y": min(y_values),
        "max_y": max(y_values),
        "min_z": min(z_values),
        "max_z": max(z_values),
    }


def basis_point(basis_x, x, basis_y, y, basis_z, z):
    return add(add(scaled(basis_x, x), scaled(basis_y, y)), scaled(basis_z, z))


def legacy_alpha_registration(canvas_px, bbox_px, target_width_cm, target_height_cm, plane_box):
    """Retain the accepted v007 conveyor envelope contract only."""
    image_width, image_height = canvas_px
    left, top, right, bottom = bbox_px
    alpha_width = right - left
    alpha_height = bottom - top
    if min(image_width, image_height, alpha_width, alpha_height) <= 0:
        fail("invalid image/alpha dimensions")
    fraction_x = alpha_width / float(image_width)
    fraction_y = alpha_height / float(image_height)
    plane_width = plane_box.max.x - plane_box.min.x
    plane_height = plane_box.max.y - plane_box.min.y
    plane_depth = plane_box.max.z - plane_box.min.z
    if min(plane_width, plane_height) <= 0.0 or plane_depth > 0.001:
        fail("registration plane must be a non-degenerate XY plane: {}".format(plane_box))
    scale_x = target_width_cm / (plane_width * fraction_x)
    scale_y = target_height_cm / (plane_height * fraction_y)
    canvas_width_cm = plane_width * scale_x
    canvas_height_cm = plane_height * scale_y
    pixel_scale_x = canvas_width_cm / image_width
    pixel_scale_y = canvas_height_cm / image_height
    distortion = max(pixel_scale_x, pixel_scale_y) / min(pixel_scale_x, pixel_scale_y) - 1.0
    if distortion > MAX_PIXEL_SCALE_DISTORTION + DISTORTION_NUMERIC_TOLERANCE:
        fail("exact bounds fit would distort square source pixels by {:.4%} (limit {:.2%})".format(distortion, MAX_PIXEL_SCALE_DISTORTION))

    # Registration assumes the accepted BasicShapes/Plane UV contract: source
    # U follows local +X; PNG row zero is local +Y, so increasing image V is
    # local -Y. Querying the mesh box also removes the old hard-coded 100 cm
    # size and centred-pivot assumption.
    centre_u = (left + right) * 0.5 / image_width
    centre_v = (top + bottom) * 0.5 / image_height
    alpha_centre_local_x = plane_box.min.x + centre_u * plane_width
    alpha_centre_local_y = plane_box.max.y - centre_v * plane_height
    alpha_centre_local_z = (plane_box.min.z + plane_box.max.z) * 0.5
    return {
        "mode": LEGACY_REGISTRATION_MODE,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "canvas_width_cm": canvas_width_cm,
        "canvas_height_cm": canvas_height_cm,
        "alpha_centre_local_x_cm": alpha_centre_local_x,
        "alpha_centre_local_y_cm": alpha_centre_local_y,
        "alpha_centre_local_z_cm": alpha_centre_local_z,
        "alpha_fraction": (fraction_x, fraction_y),
        "pixel_scale_cm": (pixel_scale_x, pixel_scale_y),
        "pixel_scale_distortion": distortion,
    }


def full_canvas_physical_registration(spec, target_width_cm, target_height_cm, plane_box):
    """Uniformly map the dimensioned camera canvas; never fit or stretch alpha."""
    image_width, image_height = spec["canvas_px"]
    centre_x_px, centre_y_px = spec["source_projected_obb_center_px"]
    source_obb_width_cm, source_obb_height_cm = spec["source_projected_obb_size_cm"]
    source_canvas_width_cm, source_canvas_height_cm = spec["full_canvas_size_cm"]
    plane_width = plane_box.max.x - plane_box.min.x
    plane_height = plane_box.max.y - plane_box.min.y
    plane_depth = plane_box.max.z - plane_box.min.z
    if min(plane_width, plane_height, source_obb_width_cm, source_obb_height_cm) <= 0.0 or plane_depth > 0.001:
        fail("full-canvas registration has invalid source or plane dimensions")
    fit_x = target_width_cm / source_obb_width_cm
    fit_y = target_height_cm / source_obb_height_cm
    physical_scale_error = (
        max(fit_x, 1.0 / fit_x) - 1.0,
        max(fit_y, 1.0 / fit_y) - 1.0,
    )
    if max(physical_scale_error) > MAX_PHYSICAL_SCALE_ERROR + DISTORTION_NUMERIC_TOLERANCE:
        fail(
            "dimensioned source OBB differs from the proxy physical size by {} "
            "(limit {:.2%})".format(physical_scale_error, MAX_PHYSICAL_SCALE_ERROR)
        )
    fit_distortion = max(fit_x, fit_y) / min(fit_x, fit_y) - 1.0
    if fit_distortion > MAX_PIXEL_SCALE_DISTORTION + DISTORTION_NUMERIC_TOLERANCE:
        fail(
            "dimensioned source OBB would require {:.4%} non-uniform scale (limit {:.2%})".format(
                fit_distortion,
                MAX_PIXEL_SCALE_DISTORTION,
            )
        )
    # This is a physical-centimetre registration, not a proxy refit. Preserve
    # the manifest camera's cm-per-pixel exactly; proxy bounds are validation
    # authority and cannot silently introduce even uniform source rescaling.
    uniform_fit = 1.0
    canvas_width_cm = source_canvas_width_cm * uniform_fit
    canvas_height_cm = source_canvas_height_cm * uniform_fit
    scale_x = canvas_width_cm / plane_width
    scale_y = canvas_height_cm / plane_height
    pixel_scale_x = canvas_width_cm / image_width
    pixel_scale_y = canvas_height_cm / image_height
    pixel_distortion = max(pixel_scale_x, pixel_scale_y) / min(pixel_scale_x, pixel_scale_y) - 1.0
    if pixel_distortion > BASIS_NUMERIC_TOLERANCE:
        fail("full-canvas physical mapping does not preserve square pixels")
    mapped_obb_size_cm = (source_obb_width_cm * uniform_fit, source_obb_height_cm * uniform_fit)
    fit_residual = (
        abs(mapped_obb_size_cm[0] / target_width_cm - 1.0),
        abs(mapped_obb_size_cm[1] / target_height_cm - 1.0),
    )
    if max(fit_residual) > MAX_PIXEL_SCALE_DISTORTION + DISTORTION_NUMERIC_TOLERANCE:
        fail("uniform full-canvas fit exceeds the proxy-dimension residual gate")
    centre_u = centre_x_px / float(image_width)
    centre_v = centre_y_px / float(image_height)
    anchor_local_x = plane_box.min.x + centre_u * plane_width
    anchor_local_y = plane_box.max.y - centre_v * plane_height
    anchor_local_z = (plane_box.min.z + plane_box.max.z) * 0.5
    return {
        "mode": MACHINE_REGISTRATION_MODE,
        "scale_x": scale_x,
        "scale_y": scale_y,
        "uniform_fit": uniform_fit,
        "source_fit_xy": (fit_x, fit_y),
        "physical_scale_error": physical_scale_error,
        "source_fit_distortion": fit_distortion,
        "fit_residual": fit_residual,
        "canvas_width_cm": canvas_width_cm,
        "canvas_height_cm": canvas_height_cm,
        "anchor_local_x_cm": anchor_local_x,
        "anchor_local_y_cm": anchor_local_y,
        "anchor_local_z_cm": anchor_local_z,
        "source_obb_size_cm": (source_obb_width_cm, source_obb_height_cm),
        "mapped_obb_size_cm": mapped_obb_size_cm,
        "pixel_scale_cm": (pixel_scale_x, pixel_scale_y),
        "pixel_scale_distortion": pixel_distortion,
    }


def asset_package_path(asset):
    return asset.get_path_name().split(".", 1)[0]


def validate_native_material(material, context, expected_path=None):
    if not isinstance(material, unreal.Material):
        fail("{} does not use a direct native Material".format(context))
    if expected_path is not None and asset_package_path(material) != expected_path:
        fail("{} material path changed: {}".format(context, material.get_path_name()))
    clip_value = float(material.get_editor_property("opacity_mask_clip_value"))
    if abs(clip_value - MATERIAL_CLIP_VALUE) > 0.000001:
        fail("{} opacity-mask threshold does not match alpha byte {}".format(context, ALPHA_THRESHOLD_BYTE))
    if material.get_editor_property("blend_mode") != unreal.BlendMode.BLEND_MASKED:
        fail("{} material is not masked".format(context))
    if material.get_editor_property("shading_model") != unreal.MaterialShadingModel.MSM_UNLIT:
        fail("{} material is not unlit".format(context))
    if not material.get_editor_property("two_sided"):
        fail("{} material is not two-sided".format(context))


def validate_sprite_plane(sprite, plane_mesh, expected_material_path=None):
    if not isinstance(sprite, unreal.StaticMeshActor):
        fail("sprite is not a StaticMeshActor: {}".format(sprite.get_actor_label()))
    if sprite.get_attach_parent_actor() is not None:
        fail("exact sprite must not be attached: {}".format(sprite.get_actor_label()))
    component = sprite.static_mesh_component
    mesh = component.get_editor_property("static_mesh")
    if not isinstance(mesh, unreal.StaticMesh) or mesh.get_path_name() != plane_mesh.get_path_name():
        fail("sprite does not use the validated registration plane: {}".format(sprite.get_actor_label()))
    relative_location = component.get_editor_property("relative_location")
    relative_rotation = component.get_editor_property("relative_rotation")
    relative_scale = component.get_editor_property("relative_scale3d")
    if length(relative_location) > BASIS_NUMERIC_TOLERANCE:
        fail("sprite component has a relative-location offset: {}".format(sprite.get_actor_label()))
    if max(abs(relative_rotation.pitch), abs(relative_rotation.yaw), abs(relative_rotation.roll)) > CAMERA_ANGLE_TOLERANCE_DEG:
        fail("sprite component has a relative rotation: {}".format(sprite.get_actor_label()))
    if max(abs(relative_scale.x - 1.0), abs(relative_scale.y - 1.0), abs(relative_scale.z - 1.0)) > BASIS_NUMERIC_TOLERANCE:
        fail("sprite component has a relative scale: {}".format(sprite.get_actor_label()))
    material = component.get_material(0)
    validate_native_material(material, "sprite {}".format(sprite.get_actor_label()), expected_material_path)
    return component, material


def validate_final_asset_lane_absent(machine_specs):
    existing_assets = list(
        unreal.EditorAssetLibrary.list_assets(
            FINAL_ASSET_ROOT,
            recursive=True,
            include_folder=False,
        )
        or []
    )
    if existing_assets:
        fail("final asset lane is not empty: {}".format(existing_assets))
    for spec in machine_specs:
        for field in ("texture_asset", "material_asset"):
            path = spec[field]
            if unreal.EditorAssetLibrary.does_asset_exist(path) or unreal.load_asset(path) is not None:
                fail("final destination already exists; refusing stale reuse: {}".format(path))


def import_final_machine_assets(machine_specs):
    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    material_editing = unreal.MaterialEditingLibrary
    if not hasattr(material_editing, "delete_all_material_expressions"):
        fail("MaterialEditingLibrary cannot clear material expressions in this Unreal build")
    imported = {}
    for spec in machine_specs:
        station = spec["station"]
        source = spec["source_root"] / spec["source"]
        texture_path = spec["texture_asset"]
        texture_name = texture_path.rsplit("/", 1)[-1]
        task = unreal.AssetImportTask()
        task.set_editor_properties({
            "filename": str(source),
            "destination_path": FINAL_TEXTURE_ROOT,
            "destination_name": texture_name,
            # Force the legacy texture factory. Interchange is allowed to
            # ignore AssetImportTask.destination_name, which would otherwise
            # import the CA_* source stem instead of the declared T_* asset.
            "factory": unreal.TextureFactory(),
            "automated": True,
            "replace_existing": False,
            # Save only after path/type/settings validation below.
            "save": False,
        })
        asset_tools.import_asset_tasks([task])
        imported_objects = list(task.get_objects() or [])
        imported_paths = list(task.get_editor_property("imported_object_paths") or [])
        if len(imported_objects) != 1 or not isinstance(imported_objects[0], unreal.Texture2D):
            fail(
                "expected one imported Texture2D for {}, got objects={} paths={}".format(
                    station,
                    imported_objects,
                    imported_paths,
                )
            )
        texture = imported_objects[0]
        imported_package = asset_package_path(texture)
        if imported_package != texture_path:
            if imported_package.rsplit("/", 1)[0] != FINAL_TEXTURE_ROOT:
                fail("{} imported outside the isolated texture lane: {}".format(station, imported_package))
            if unreal.EditorAssetLibrary.does_asset_exist(texture_path):
                fail("{} declared texture path unexpectedly exists before rename".format(station))
            if not unreal.EditorAssetLibrary.rename_asset(imported_package, texture_path):
                fail(
                    "could not normalize {} imported texture path {} to {}".format(
                        station,
                        imported_package,
                        texture_path,
                    )
                )
            texture = unreal.load_asset(texture_path)
        if not isinstance(texture, unreal.Texture2D) or asset_package_path(texture) != texture_path:
            fail("{} final PNG did not import to the declared Texture2D path".format(station))
        texture.set_editor_properties({
            "srgb": True,
            "compression_settings": unreal.TextureCompressionSettings.TC_DEFAULT,
            "never_stream": True,
        })
        if not unreal.EditorAssetLibrary.save_loaded_asset(texture, only_if_is_dirty=False):
            fail("could not save imported final texture for {}".format(station))

        material_path = spec["material_asset"]
        material_name = material_path.rsplit("/", 1)[-1]
        material = asset_tools.create_asset(
            material_name,
            FINAL_MATERIAL_ROOT,
            unreal.Material,
            unreal.MaterialFactoryNew(),
        )
        if not isinstance(material, unreal.Material) or asset_package_path(material) != material_path:
            fail("could not create declared final material for {}".format(station))
        material_editing.delete_all_material_expressions(material)
        material.set_editor_properties({
            "blend_mode": unreal.BlendMode.BLEND_MASKED,
            "shading_model": unreal.MaterialShadingModel.MSM_UNLIT,
            "two_sided": True,
            "opacity_mask_clip_value": MATERIAL_CLIP_VALUE,
        })
        sample = material_editing.create_material_expression(
            material,
            unreal.MaterialExpressionTextureSample,
            -420,
            0,
        )
        sample.set_editor_properties({
            "texture": texture,
            "sampler_type": unreal.MaterialSamplerType.SAMPLERTYPE_COLOR,
        })
        if not material_editing.connect_material_property(sample, "RGB", unreal.MaterialProperty.MP_EMISSIVE_COLOR):
            fail("could not connect final {} RGB to emissive".format(station))
        if not material_editing.connect_material_property(sample, "A", unreal.MaterialProperty.MP_OPACITY_MASK):
            fail("could not connect final {} alpha to opacity mask".format(station))
        compiler_errors = list(material_editing.recompile_material(material) or [])
        if compiler_errors:
            fail("final {} material compile failed: {}".format(station, compiler_errors))
        if not unreal.EditorAssetLibrary.save_loaded_asset(material, only_if_is_dirty=False):
            fail("could not save final material for {}".format(station))
        validate_native_material(material, "final {} material".format(station), material_path)
        imported[station] = {
            "texture": texture,
            "material": material,
            "texture_path": texture.get_path_name(),
            "material_path": material.get_path_name(),
        }
    if not unreal.EditorAssetLibrary.save_directory(
        FINAL_ASSET_ROOT,
        only_if_is_dirty=False,
        recursive=True,
    ):
        fail("could not save the isolated final asset lane")
    return imported


def mapped_alpha_corner(location, rotation, actor_scale, plane_box, canvas_px, pixel_x, pixel_y):
    image_width, image_height = canvas_px
    plane_width = plane_box.max.x - plane_box.min.x
    plane_height = plane_box.max.y - plane_box.min.y
    local_x = plane_box.min.x + plane_width * (pixel_x / float(image_width))
    local_y = plane_box.max.y - plane_height * (pixel_y / float(image_height))
    local_z = (plane_box.min.z + plane_box.max.z) * 0.5
    basis_x = unreal.MathLibrary.get_forward_vector(rotation)
    basis_y = unreal.MathLibrary.get_right_vector(rotation)
    basis_z = unreal.MathLibrary.get_up_vector(rotation)
    return add(
        location,
        basis_point(
            basis_x,
            local_x * actor_scale.x,
            basis_y,
            local_y * actor_scale.y,
            basis_z,
            local_z * actor_scale.z,
        ),
    )


def validate_mapped_alpha(plan, location, rotation, actor_scale):
    left, top, right, bottom = plan["alpha"]["bbox_px"]
    corners = [
        mapped_alpha_corner(location, rotation, actor_scale, plan["plane_box"], plan["alpha"]["canvas_px"], x, y)
        for x in (left, right)
        for y in (top, bottom)
    ]
    projected_corners = projected_obb(corners, plan["basis_x"], plan["basis_y"], plan["basis_z"])
    target = plan["projected_bounds"]
    edge_errors = {
        "min_x": abs(projected_corners["min_x"] - target["min_x"]),
        "max_x": abs(projected_corners["max_x"] - target["max_x"]),
        "min_y": abs(projected_corners["min_y"] - target["min_y"]),
        "max_y": abs(projected_corners["max_y"] - target["max_y"]),
    }
    depth_errors = (
        abs(projected_corners["min_z"] - plan["target_depth"]),
        abs(projected_corners["max_z"] - plan["target_depth"]),
    )
    tolerance = max(
        MIN_GEOMETRIC_TOLERANCE_CM,
        RELATIVE_GEOMETRIC_TOLERANCE * max(plan["target_width_cm"], plan["target_height_cm"]),
    )
    if max(tuple(edge_errors.values()) + depth_errors) > tolerance:
        fail("mapped alpha does not reproduce transformed proxy bounds for {}: edges={} depth={} tolerance={}".format(plan["sprite_label"], edge_errors, depth_errors, tolerance))
    return edge_errors, depth_errors, tolerance


def validate_full_canvas_mapping(plan, location, rotation, actor_scale):
    spec = plan["spec"]
    centre_x_px, centre_y_px = spec["source_projected_obb_center_px"]
    anchor_world = mapped_alpha_corner(
        location,
        rotation,
        actor_scale,
        plan["plane_box"],
        plan["alpha"]["canvas_px"],
        centre_x_px,
        centre_y_px,
    )
    target = plan["projected_bounds"]
    expected_centre = (
        (target["min_x"] + target["max_x"]) * 0.5,
        (target["min_y"] + target["max_y"]) * 0.5,
        plan["target_depth"],
    )
    actual_centre = (
        dot(anchor_world, plan["basis_x"]),
        dot(anchor_world, plan["basis_y"]),
        dot(anchor_world, plan["basis_z"]),
    )
    anchor_errors = tuple(abs(actual - expected) for actual, expected in zip(actual_centre, expected_centre))
    plane_width = plan["plane_box"].max.x - plan["plane_box"].min.x
    plane_height = plan["plane_box"].max.y - plan["plane_box"].min.y
    actual_canvas_size = (plane_width * actor_scale.x, plane_height * actor_scale.y)
    expected_canvas_size = (
        plan["registration"]["canvas_width_cm"],
        plan["registration"]["canvas_height_cm"],
    )
    canvas_errors = tuple(abs(actual - expected) for actual, expected in zip(actual_canvas_size, expected_canvas_size))
    actual_pixel_scale = (
        actual_canvas_size[0] / plan["alpha"]["canvas_px"][0],
        actual_canvas_size[1] / plan["alpha"]["canvas_px"][1],
    )
    pixel_distortion = max(actual_pixel_scale) / min(actual_pixel_scale) - 1.0
    if pixel_distortion > BASIS_NUMERIC_TOLERANCE:
        fail("applied full-canvas plane no longer preserves square pixels: {}".format(plan["sprite_label"]))
    tolerance = max(
        MIN_GEOMETRIC_TOLERANCE_CM,
        RELATIVE_GEOMETRIC_TOLERANCE * max(plan["target_width_cm"], plan["target_height_cm"]),
    )
    if max(anchor_errors + canvas_errors) > tolerance:
        fail(
            "full-canvas anchor/scale mapping drifted for {}: anchor={} canvas={} tolerance={}".format(
                plan["sprite_label"],
                anchor_errors,
                canvas_errors,
                tolerance,
            )
        )
    if max(plan["registration"]["fit_residual"]) > MAX_PIXEL_SCALE_DISTORTION + DISTORTION_NUMERIC_TOLERANCE:
        fail("full-canvas source OBB no longer fits proxy within the 2 percent gate")
    return {
        "anchor_error_cm": anchor_errors,
        "canvas_error_cm": canvas_errors,
        "pixel_scale_cm": actual_pixel_scale,
        "pixel_scale_distortion": pixel_distortion,
        "tolerance_cm": tolerance,
    }


def build_pair_plan(actors, request, camera_forward, camera_right, camera_up, plane_mesh, plane_box, alpha_sources):
    spec = request["spec"]
    proxy = find_one(actors, request["proxy_label"])
    sprite = find_one(actors, request["sprite_label"])
    sprite_component, material = validate_sprite_plane(sprite, plane_mesh)
    proxy_component, proxy_mesh, proxy_local_box, proxy_corners, proxy_flow = transformed_mesh_bounds(proxy)

    registration_mode = spec["registration_mode"]
    if registration_mode == MACHINE_REGISTRATION_MODE:
        assembly_yaw_radians = math.radians(spec["assembly_yaw_deg_baked"])
        expected_proxy_flow = unreal.Vector(
            math.cos(assembly_yaw_radians),
            math.sin(assembly_yaw_radians),
            0.0,
        )
        if dot(proxy_flow, expected_proxy_flow) < BASIS_DOT_MIN:
            fail(
                "machine proxy local +X does not match its manifest assembly yaw: {}".format(
                    request["proxy_label"]
                )
            )
        # The final PNGs already contain each assembly yaw as seen by the
        # locked camera. Their U/V axes are screen right/up; rotating by proxy
        # flow here would apply assembly orientation a second time.
        desired_x = camera_right
    elif registration_mode == LEGACY_REGISTRATION_MODE:
        if dot(proxy_flow, unit(WORLD_PROCESS_FLOW)) < BASIS_DOT_MIN:
            fail("legacy conveyor local +X no longer follows world process flow: {}".format(request["proxy_label"]))
        desired_x = projected(proxy_flow, camera_forward)
    else:
        fail("unsupported registration mode for {}: {}".format(request["sprite_label"], registration_mode))
    card_rotation = unreal.MathLibrary.make_rot_from_zx(camera_forward, desired_x)
    card_x = unit(unreal.MathLibrary.get_forward_vector(card_rotation))
    card_y = unit(unreal.MathLibrary.get_right_vector(card_rotation))
    card_z = unit(unreal.MathLibrary.get_up_vector(card_rotation))
    validate_basis(card_x, card_y, card_z, "sprite {}".format(request["sprite_label"]))
    if dot(card_x, desired_x) < BASIS_DOT_MIN:
        fail("sprite local +X does not follow its declared image basis: {}".format(request["sprite_label"]))
    if dot(card_z, camera_forward) < BASIS_DOT_MIN:
        fail("sprite local +Z does not use the accepted camera-forward back-face convention: {}".format(request["sprite_label"]))
    if registration_mode == MACHINE_REGISTRATION_MODE and dot(card_y, camera_up) < BASIS_DOT_MIN:
        fail("full-canvas sprite local +Y does not follow locked camera screen-up: {}".format(request["sprite_label"]))

    bounds = projected_obb(proxy_corners, card_x, card_y, card_z)
    target_width_cm = bounds["max_x"] - bounds["min_x"]
    target_height_cm = bounds["max_y"] - bounds["min_y"]
    if min(target_width_cm, target_height_cm) <= 0.001:
        fail("proxy has a degenerate projected OBB: {}".format(request["proxy_label"]))
    alpha_key = str(spec["source_root"] / spec["source"])
    alpha = alpha_sources[alpha_key]
    if registration_mode == MACHINE_REGISTRATION_MODE:
        registration = full_canvas_physical_registration(spec, target_width_cm, target_height_cm, plane_box)
        anchor_local = (
            registration["anchor_local_x_cm"],
            registration["anchor_local_y_cm"],
            registration["anchor_local_z_cm"],
        )
    else:
        registration = legacy_alpha_registration(
            alpha["canvas_px"],
            alpha["bbox_px"],
            target_width_cm,
            target_height_cm,
            plane_box,
        )
        anchor_local = (
            registration["alpha_centre_local_x_cm"],
            registration["alpha_centre_local_y_cm"],
            registration["alpha_centre_local_z_cm"],
        )
    target_depth = bounds["min_z"] - CARD_DEPTH_CM
    target_centre = basis_point(
        card_x,
        (bounds["min_x"] + bounds["max_x"]) * 0.5,
        card_y,
        (bounds["min_y"] + bounds["max_y"]) * 0.5,
        card_z,
        target_depth,
    )
    anchor_offset = basis_point(
        card_x,
        anchor_local[0] * registration["scale_x"],
        card_y,
        anchor_local[1] * registration["scale_y"],
        card_z,
        anchor_local[2],
    )
    location = subtract(target_centre, anchor_offset)
    actor_scale = unreal.Vector(registration["scale_x"], registration["scale_y"], 1.0)
    plan = {
        "kind": request["kind"],
        "station": request["station"],
        "spec": spec,
        "registration_mode": registration_mode,
        "proxy_label": request["proxy_label"],
        "sprite_label": request["sprite_label"],
        "proxy": proxy,
        "proxy_component": proxy_component,
        "proxy_mesh": proxy_mesh,
        "proxy_actor_location": proxy.get_actor_location(),
        "proxy_actor_rotation": proxy.get_actor_rotation(),
        "proxy_actor_scale": proxy.get_actor_scale3d(),
        "proxy_collision_enabled": proxy_component.get_collision_enabled(),
        "proxy_local_box": proxy_local_box,
        "proxy_corners": proxy_corners,
        "proxy_flow": proxy_flow,
        "sprite": sprite,
        "sprite_component": sprite_component,
        "inherited_material": material,
        "material": material,
        "alpha": alpha,
        "plane_box": plane_box,
        "basis_x": card_x,
        "basis_y": card_y,
        "basis_z": card_z,
        "rotation": card_rotation,
        "location": location,
        "actor_scale": actor_scale,
        "projected_bounds": bounds,
        "target_width_cm": target_width_cm,
        "target_height_cm": target_height_cm,
        "target_depth": target_depth,
        "registration": registration,
    }
    if registration_mode == MACHINE_REGISTRATION_MODE:
        validate_full_canvas_mapping(plan, location, card_rotation, actor_scale)
    else:
        validate_mapped_alpha(plan, location, card_rotation, actor_scale)
    return plan


def apply_pair_plan(plan):
    sprite = plan["sprite"]
    component = plan["sprite_component"]
    if plan["registration_mode"] == MACHINE_REGISTRATION_MODE:
        final_material = plan.get("final_material")
        if not isinstance(final_material, unreal.Material):
            fail("final machine material was not supplied for {}".format(plan["sprite_label"]))
        component.set_material(0, final_material)
        validate_native_material(
            component.get_material(0),
            "applied sprite {}".format(plan["sprite_label"]),
            plan["spec"]["material_asset"],
        )
        plan["material"] = final_material
    # Actor.set_actor_location returns HitResult-or-None in Unreal Python, not
    # a success boolean; with sweep disabled, None is a normal successful
    # return. The exact read-back and mapping checks below are authoritative.
    sprite.set_actor_location(plan["location"], False, False)
    if not sprite.set_actor_rotation(plan["rotation"], False):
        fail("could not set exact sprite rotation: {}".format(plan["sprite_label"]))
    sprite.set_actor_scale3d(plan["actor_scale"])
    component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
    component.set_editor_property("cast_shadow", False)
    tags = [
        unreal.Name("LB.Sprite.ExactRegistered.v008"),
        unreal.Name("LB.Sprite.Camera.ManifestDriven"),
        unreal.Name("LB.Sprite.AlphaThreshold.Byte21"),
    ]
    if plan["registration_mode"] == MACHINE_REGISTRATION_MODE:
        tags.extend([
            unreal.Name("LB.Sprite.Registration.FullCanvasPhysical"),
            unreal.Name("LB.Sprite.Orientation.LockedCameraScreenBaked"),
            unreal.Name("LB.Sprite.AssemblyYaw.AlreadyBaked"),
        ])
    else:
        tags.append(unreal.Name("LB.Sprite.ProcessAxis.ProxyLocalPlusX"))
    sprite.tags = tags

    proxy = plan["proxy"]
    plan["proxy_component"].set_visibility(False, True)
    plan["proxy_component"].set_editor_property("cast_shadow", False)
    proxy.set_actor_hidden_in_game(True)
    proxy_location = proxy.get_actor_location()
    proxy_rotation = proxy.get_actor_rotation()
    proxy_scale = proxy.get_actor_scale3d()
    expected_proxy_location = plan["proxy_actor_location"]
    expected_proxy_rotation = plan["proxy_actor_rotation"]
    expected_proxy_scale = plan["proxy_actor_scale"]
    proxy_transform_error = max(
        abs(proxy_location.x - expected_proxy_location.x),
        abs(proxy_location.y - expected_proxy_location.y),
        abs(proxy_location.z - expected_proxy_location.z),
        abs(proxy_rotation.pitch - expected_proxy_rotation.pitch),
        abs(proxy_rotation.yaw - expected_proxy_rotation.yaw),
        abs(proxy_rotation.roll - expected_proxy_rotation.roll),
        abs(proxy_scale.x - expected_proxy_scale.x),
        abs(proxy_scale.y - expected_proxy_scale.y),
        abs(proxy_scale.z - expected_proxy_scale.z),
    )
    if proxy_transform_error > BASIS_NUMERIC_TOLERANCE:
        fail("hidden proxy placement changed: {}".format(plan["proxy_label"]))
    if plan["proxy_component"].get_collision_enabled() != plan["proxy_collision_enabled"]:
        fail("hidden proxy collision authority changed: {}".format(plan["proxy_label"]))
    current_proxy_mesh = plan["proxy_component"].get_editor_property("static_mesh")
    if (
        not isinstance(current_proxy_mesh, unreal.StaticMesh)
        or current_proxy_mesh.get_path_name() != plan["proxy_mesh"].get_path_name()
    ):
        fail("hidden proxy mesh authority changed: {}".format(plan["proxy_label"]))

    actual_location = sprite.get_actor_location()
    actual_rotation = sprite.get_actor_rotation()
    actual_scale = sprite.get_actor_scale3d()
    actual_x = unit(unreal.MathLibrary.get_forward_vector(actual_rotation))
    actual_y = unit(unreal.MathLibrary.get_right_vector(actual_rotation))
    actual_z = unit(unreal.MathLibrary.get_up_vector(actual_rotation))
    validate_basis(actual_x, actual_y, actual_z, "applied sprite {}".format(plan["sprite_label"]))
    if dot(actual_x, plan["basis_x"]) < BASIS_DOT_MIN or dot(actual_z, plan["basis_z"]) < BASIS_DOT_MIN:
        fail("applied sprite basis drifted: {}".format(plan["sprite_label"]))
    expected_scale = plan["actor_scale"]
    scale_error = max(
        abs(actual_scale.x - expected_scale.x) / max(abs(expected_scale.x), 1.0),
        abs(actual_scale.y - expected_scale.y) / max(abs(expected_scale.y), 1.0),
        abs(actual_scale.z - expected_scale.z),
    )
    if scale_error > BASIS_NUMERIC_TOLERANCE:
        fail("applied sprite scale drifted: {}".format(plan["sprite_label"]))
    if plan["registration_mode"] == MACHINE_REGISTRATION_MODE:
        mapping_validation = validate_full_canvas_mapping(plan, actual_location, actual_rotation, actual_scale)
    else:
        edge_errors, depth_errors, tolerance = validate_mapped_alpha(plan, actual_location, actual_rotation, actual_scale)
        mapping_validation = {
            "edge_error_cm": edge_errors,
            "depth_error_cm": depth_errors,
            "tolerance_cm": tolerance,
        }
    record = {
        "kind": plan["kind"],
        "station": plan["station"],
        "registration_mode": plan["registration_mode"],
        "proxy": plan["proxy_label"],
        "proxy_mesh": plan["proxy_mesh"].get_path_name(),
        "proxy_local_bounds_cm": {
            "min": [round(plan["proxy_local_box"].min.x, 6), round(plan["proxy_local_box"].min.y, 6), round(plan["proxy_local_box"].min.z, 6)],
            "max": [round(plan["proxy_local_box"].max.x, 6), round(plan["proxy_local_box"].max.y, 6), round(plan["proxy_local_box"].max.z, 6)],
        },
        "proxy_transformed_bound_corner_count": len(plan["proxy_corners"]),
        "proxy_world_flow_axis": [round(plan["proxy_flow"].x, 9), round(plan["proxy_flow"].y, 9), round(plan["proxy_flow"].z, 9)],
        "proxy_projected_bounds_cm": {key: round(value, 6) for key, value in plan["projected_bounds"].items()},
        "sprite": plan["sprite_label"],
        "material": plan["material"].get_path_name(),
        "inherited_v007_material": plan["inherited_material"].get_path_name(),
        "source_png": str(plan["alpha"]["path"]),
        "source_sha256": plan["alpha"]["sha256"],
        "alpha_threshold_byte": ALPHA_THRESHOLD_BYTE,
        "canvas_px": list(plan["alpha"]["canvas_px"]),
        "alpha_bbox_px_exclusive": list(plan["alpha"]["bbox_px"]),
        "target_proxy_projected_size_cm": [round(plan["target_width_cm"], 6), round(plan["target_height_cm"], 6)],
        "plane_canvas_size_cm": [round(plan["registration"]["canvas_width_cm"], 6), round(plan["registration"]["canvas_height_cm"], 6)],
        "source_pixel_scale_cm": [round(value, 9) for value in plan["registration"]["pixel_scale_cm"]],
        "source_pixel_scale_distortion": round(plan["registration"]["pixel_scale_distortion"], 9),
        "plane_location_cm": [round(actual_location.x, 6), round(actual_location.y, 6), round(actual_location.z, 6)],
        "plane_rotation_deg": [round(actual_rotation.pitch, 6), round(actual_rotation.yaw, 6), round(actual_rotation.roll, 6)],
        "plane_actor_scale": [round(actual_scale.x, 9), round(actual_scale.y, 9), round(actual_scale.z, 9)],
        "depth_bias_cm": CARD_DEPTH_CM,
        "collision_authority": "hidden proxy retained",
        "proxy_collision_enabled": str(plan["proxy_collision_enabled"]),
        "proxy_transform_unchanged": True,
    }
    if plan["registration_mode"] == MACHINE_REGISTRATION_MODE:
        record.update({
            "orientation_mode": MACHINE_ORIENTATION_MODE,
            "assembly_yaw_deg_baked": plan["spec"]["assembly_yaw_deg_baked"],
            "source_ortho_height_cm": plan["spec"]["source_ortho_height_cm"],
            "source_projected_obb_center_px": list(plan["spec"]["source_projected_obb_center_px"]),
            "source_projected_obb_size_cm": list(plan["registration"]["source_obb_size_cm"]),
            "mapped_source_obb_size_cm": list(plan["registration"]["mapped_obb_size_cm"]),
            "uniform_physical_fit": plan["registration"]["uniform_fit"],
            "source_fit_xy": list(plan["registration"]["source_fit_xy"]),
            "source_fit_distortion": plan["registration"]["source_fit_distortion"],
            "absolute_physical_scale_error": list(plan["registration"]["physical_scale_error"]),
            "source_fit_residual": list(plan["registration"]["fit_residual"]),
            "full_canvas_anchor_error_cm": [round(value, 9) for value in mapping_validation["anchor_error_cm"]],
            "full_canvas_error_cm": [round(value, 9) for value in mapping_validation["canvas_error_cm"]],
            "registration_tolerance_cm": round(mapping_validation["tolerance_cm"], 9),
            "texture": plan["final_texture"].get_path_name(),
        })
    else:
        record.update({
            "registration_edge_error_cm": {
                key: round(value, 9) for key, value in mapping_validation["edge_error_cm"].items()
            },
            "registration_depth_error_cm": [round(value, 9) for value in mapping_validation["depth_error_cm"]],
            "registration_tolerance_cm": round(mapping_validation["tolerance_cm"], 9),
        })
    return record


manifest, manifest_sha256, manifest_camera_contract, machine_specs = load_machine_manifest()

if not SOURCE_FILE.is_file():
    fail("v007 source map is missing")
if digest(SOURCE_FILE) != SOURCE_FILE_SHA256:
    fail("accepted v007 source map hash changed")
if TARGET_FILE.exists() or unreal.EditorAssetLibrary.does_asset_exist(TARGET_MAP):
    fail("v008 target already exists; refusing to overwrite")
for path, expected in PROTECTED_MAPS.items():
    if not path.is_file() or digest(path) != expected:
        fail("protected map missing or changed: {}".format(path))

before = {"v007": digest(SOURCE_FILE)}
before.update({str(path): digest(path) for path in PROTECTED_MAPS})

requests = [
    {
        "spec": item,
        "proxy_label": item["proxy"],
        "sprite_label": item["sprite"],
        "station": item["station"],
        "kind": item["kind"],
    }
    for item in machine_specs
]
for index in range(1, 7):
    requests.append({
        "spec": CONVEYOR_SPEC,
        "proxy_label": "2.5D full | transfer conveyor {:02d}".format(index),
        "sprite_label": "2.5D sprite art | transfer conveyor {:02d}".format(index),
        "station": "handoff-{:02d}".format(index),
        "kind": "transfer_conveyor",
    })

# Parse immutable source bytes before any Unreal asset or map mutation. The
# manifest hash locks RGB identity; alpha boxes remain machine-source QA only.
alpha_sources = {}
for request in requests:
    spec = request["spec"]
    source_key = str(spec["source_root"] / spec["source"])
    if source_key not in alpha_sources:
        alpha_sources[source_key] = validated_alpha_spec(spec)

plane_mesh = unreal.load_asset(PLANE_ASSET)
if not isinstance(plane_mesh, unreal.StaticMesh):
    fail("registration plane asset is missing")
plane_box = plane_mesh.get_bounding_box()
plane_size = (
    plane_box.max.x - plane_box.min.x,
    plane_box.max.y - plane_box.min.y,
    plane_box.max.z - plane_box.min.z,
)
if min(plane_size[0], plane_size[1]) <= 0.0 or plane_size[2] > 0.001:
    fail("registration plane bounds are invalid: {}".format(plane_box))

# Duplicate the unopened source package first. Loading v007 before duplication
# caused the prior isolation/save failure; there is deliberately no save-as
# fallback and the source world is never explicitly loaded by this builder.
asset_registry = unreal.AssetRegistryHelpers.get_asset_registry()
asset_registry.scan_paths_synchronous(
    [
        "/Game/LineBoss/Candidates/PressShop/PressShopFactorio2p5D_IndividualSprites_v007",
        FINAL_ASSET_ROOT,
    ],
    force_rescan=True,
    ignore_deny_list_scan_filters=False,
)
if not unreal.EditorAssetLibrary.does_asset_exist(SOURCE_MAP):
    fail("asset registry cannot resolve the unopened v007 source map")
editor_subsystem = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem)
if editor_subsystem is None:
    fail("UnrealEditorSubsystem is unavailable")
current_world = editor_subsystem.get_editor_world()
current_world_package = asset_package_path(current_world) if current_world is not None else None
if current_world_package in (SOURCE_MAP, TARGET_MAP):
    fail(
        "source/target world is already open; switch to an unrelated clean map "
        "before duplicating the hash-locked v007 package: {}".format(current_world_package)
    )
dirty_map_packages = list(unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages() or [])
dirty_map_package_paths = sorted(package.get_path_name() for package in dirty_map_packages)
if dirty_map_package_paths:
    fail(
        "dirty editor map packages would be discarded by load_map without prompting; "
        "save or switch to a clean unrelated map first: {}".format(dirty_map_package_paths)
    )
source_asset_data = list(
    asset_registry.get_assets_by_package_name(
        unreal.Name(SOURCE_MAP),
        include_only_on_disk_assets=False,
    )
    or []
)
if len(source_asset_data) != 1:
    fail("expected exactly one v007 World asset record; found {}".format(len(source_asset_data)))
if source_asset_data[0].is_asset_loaded():
    fail("v007 World package is already loaded; refusing an in-memory duplicate")
validate_final_asset_lane_absent(machine_specs)
if not unreal.EditorAssetLibrary.duplicate_asset(SOURCE_MAP, TARGET_MAP):
    fail("could not duplicate unopened v007 source package to isolated v008")
if not unreal.EditorLoadingAndSavingUtils.load_map(TARGET_MAP):
    fail("could not load the duplicated v008 map")

# Configure the camera and preflight all geometry/scale/material-source inputs
# only in the duplicated target. Sprite/proxy edits and imports follow this
# complete preflight.
target_actors = unreal.EditorLevelLibrary.get_all_level_actors()
target_camera = find_one(target_actors, CAMERA_LABEL)
target_camera_rotation, target_camera_forward, target_camera_right, target_camera_up = configure_target_camera(
    target_camera,
    manifest_camera_contract,
)
target_camera_location = target_camera.get_actor_location()
target_camera_component = target_camera.get_component_by_class(unreal.CameraComponent)
if target_camera_component is None:
    fail("configured target camera lost its CameraComponent")
target_camera_ortho_width = float(target_camera_component.get_editor_property("ortho_width"))
target_plans = [
    build_pair_plan(
        target_actors,
        request,
        target_camera_forward,
        target_camera_right,
        target_camera_up,
        plane_mesh,
        plane_box,
        alpha_sources,
    )
    for request in requests
]
machine_plans = [plan for plan in target_plans if plan["registration_mode"] == MACHINE_REGISTRATION_MODE]
if {plan["station"] for plan in machine_plans} != set(EXPECTED_MACHINE_LABELS):
    fail("duplicated target did not preflight exactly S01-S06")

final_assets = import_final_machine_assets(machine_specs)
for plan in machine_plans:
    assets = final_assets.get(plan["station"])
    if assets is None:
        fail("no imported final asset pair for {}".format(plan["station"]))
    plan["final_texture"] = assets["texture"]
    plan["final_material"] = assets["material"]

records = [apply_pair_plan(plan) for plan in target_plans]

if not unreal.EditorLevelLibrary.save_current_level():
    fail("could not save v008")
if not unreal.EditorAssetLibrary.save_asset(TARGET_MAP, only_if_is_dirty=False):
    fail("could not explicitly save the v008 map asset")

after = {"v007": digest(SOURCE_FILE)}
after.update({str(path): digest(path) for path in PROTECTED_MAPS})
if before != after:
    fail("v007 or a protected authority map changed during the build")
if not TARGET_FILE.is_file():
    fail("v008 map file was not written")

record = {
    "status": "PASS__MANIFEST_FULL_CANVAS_PHYSICAL_MACHINE_SPRITES_V008",
    "map": TARGET_MAP,
    "source_map": SOURCE_MAP,
    "source_map_explicitly_loaded": False,
    "preduplicate_editor_world": current_world_package,
    "preduplicate_editor_world_dirty": False,
    "preduplicate_dirty_map_packages": dirty_map_package_paths,
    "preduplicate_source_asset_loaded": False,
    "isolation_method": "duplicate unopened v007 package before loading v008; no save-as fallback",
    "source_duplicate_load_semantics": "verified unloaded before duplicate_asset; duplicate_asset may load the clean source UObject internally, but v007 is never the editor world",
    "camera_actor": CAMERA_LABEL,
    "camera_rotation_deg": [target_camera_rotation.pitch, target_camera_rotation.yaw, target_camera_rotation.roll],
    "camera_location_cm": [target_camera_location.x, target_camera_location.y, target_camera_location.z],
    "camera_ortho_width_cm": target_camera_ortho_width,
    "camera_projection": "orthographic",
    "camera_target_map_location_cm": (
        list(manifest_camera_contract["target_map_location_cm"])
        if manifest_camera_contract["target_map_location_cm"] is not None
        else None
    ),
    "camera_target_map_ortho_width_cm": manifest_camera_contract["target_map_ortho_width_cm"],
    "camera_framing_source": (
        "manifest"
        if manifest_camera_contract["target_map_location_cm"] is not None
        else "matching inherited v007 transform"
    ),
    "camera_angle_tolerance_deg": CAMERA_ANGLE_TOLERANCE_DEG,
    "basis_angle_tolerance_deg": BASIS_ANGLE_TOLERANCE_DEG,
    "world_process_axis": [1.0, 0.0, 0.0],
    "registration_plane": plane_mesh.get_path_name(),
    "registration_plane_local_bounds_cm": {
        "min": [plane_box.min.x, plane_box.min.y, plane_box.min.z],
        "max": [plane_box.max.x, plane_box.max.y, plane_box.max.z],
        "size": list(plane_size),
    },
    "machine_manifest": str(MACHINE_MANIFEST),
    "machine_manifest_sha256": manifest_sha256,
    "machine_manifest_status": manifest["status"],
    "final_asset_root": FINAL_ASSET_ROOT,
    "imported_machine_assets": {
        station: {
            "texture": assets["texture_path"],
            "material": assets["material_path"],
        }
        for station, assets in sorted(final_assets.items())
    },
    "alpha_threshold_byte": ALPHA_THRESHOLD_BYTE,
    "max_uniform_source_to_proxy_fit_distortion": MAX_PIXEL_SCALE_DISTORTION,
    "max_absolute_physical_scale_error": MAX_PHYSICAL_SCALE_ERROR,
    "depth_bias_cm": CARD_DEPTH_CM,
    "registration_truth": "eight transformed corners of each hidden StaticMesh proxy local render bounds",
    "machine_registration_method": "exact FULL_CANVAS_PHYSICAL centimetre scale from manifest source ortho height (no proxy uniform refit); manifest projected centre to target projected centre; camera screen-right/up plane; baked assembly yaw is not reapplied; alpha bbox is QA only",
    "legacy_conveyor_registration_method": "v007 alpha-envelope contract retained only for legacy conveyor cards",
    "source_pngs": {
        name: {
            "path": str(value["path"]),
            "sha256": value["sha256"],
            "canvas_px": list(value["canvas_px"]),
            "alpha_bbox_px_exclusive": list(value["bbox_px"]),
            "canvas_edge_alpha_max": value["edge_alpha_max"],
        }
        for name, value in sorted(alpha_sources.items())
    },
    "records": records,
    "source_and_protected_hashes_unchanged": after,
    "target_sha256": digest(TARGET_FILE),
}
REPORT.parent.mkdir(parents=True, exist_ok=True)
REPORT.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n", encoding="utf-8")
unreal.log("PRESSSHOP_EXACT_SPRITES_V008_BUILD_PASS=" + json.dumps(record, sort_keys=True))
