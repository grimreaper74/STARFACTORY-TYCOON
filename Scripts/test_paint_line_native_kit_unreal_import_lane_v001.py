"""Offline structural tests for the guarded Paint native-kit Unreal lane."""

from __future__ import annotations

import ast
import hashlib
import json
import re
import unittest
from pathlib import Path


ROOT = Path(r"C:\Users\greg_\Projects\LineBossCarFactory_Unreal 5.8")
SCRIPTS = ROOT / "Scripts"
SOURCE = ROOT / "SourceAssets/Candidate/PaintShop/PaintLineNativeKit_v001"
FILES = {
    "freezer": SCRIPTS / "freeze_paint_line_native_kit_unreal_import_baseline_v001.py",
    "runtime": SCRIPTS / "paint_line_native_kit_unreal_runtime_v001.py",
    "importer": SCRIPTS / "import_paint_line_native_kit_v001.py",
    "validator": SCRIPTS / "validate_paint_line_native_kit_v001.py",
    "runner": SCRIPTS / "run_paint_line_native_kit_unreal_import_lane_v001.ps1",
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


class PaintNativeImportLaneStaticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.text = {key: path.read_text(encoding="utf-8-sig") for key, path in FILES.items()}
        cls.manifest = json.loads((SOURCE / "MANIFEST_v001.json").read_text(encoding="utf-8-sig"))
        cls.freeze = json.loads((SOURCE / "Audit/FROZEN_v001.json").read_text(encoding="utf-8-sig"))
        cls.geometry = json.loads((SOURCE / "Audit/geometry_inventory_v001.json").read_text(encoding="utf-8-sig"))
        cls.roundtrip = json.loads((SOURCE / "Audit/roundtrip_validation_v001.json").read_text(encoding="utf-8-sig"))

    def test_python_scripts_parse_offline(self):
        for key in ("freezer", "runtime", "importer", "validator"):
            with self.subTest(key=key):
                ast.parse(self.text[key], filename=str(FILES[key]))

    def test_frozen_source_contract_is_exact(self):
        self.assertEqual(self.manifest["asset_count"], 7)
        self.assertEqual(self.manifest["lod_count_per_asset"], 3)
        self.assertEqual(self.freeze["lod_record_count"], 21)
        self.assertEqual(self.roundtrip["validated_count"], 42)
        self.assertEqual(self.roundtrip["failures"], [])
        self.assertEqual(len(self.geometry["inventory"]), 21)
        self.assertEqual(len([path for path in SOURCE.rglob("*") if path.is_file()]), 60)
        for row in self.geometry["inventory"]:
            self.assertEqual(row["uv_layers"], 1)
            self.assertTrue(row["floor_centered"])
            self.assertFalse(row["spray_robots"])
            self.assertFalse(row["modeled_process_internals"])

    def test_strict_lod_chains_and_portal_roles(self):
        wanted_portals = {"CuringOvenTunnel", "PretreatmentWashTunnel", "FlashOffTunnel", "PaintQualityLightTunnel"}
        by_asset = {}
        for row in self.geometry["inventory"]:
            by_asset.setdefault(row["asset"], []).append(row)
        self.assertEqual(set(by_asset), {row["id"] for row in self.manifest["assets"]})
        for key, rows in by_asset.items():
            rows.sort(key=lambda item: item["lod"])
            chain = [row["triangles"] for row in rows]
            self.assertGreater(chain[0], chain[1])
            self.assertGreater(chain[1], chain[2])
            self.assertTrue(all(bool(row["open_end_portals"]) == (key in wanted_portals) for row in rows))

    def test_fresh_only_and_no_destructive_api_contract(self):
        combined = "\n".join(self.text.values()).lower()
        self.assertIn('replace_existing": false', self.text["importer"].lower())
        self.assertIn("target namespace already exists; overwrite/reimport forbidden", self.text["importer"])
        self.assertIn("lane refuses every pre-existing v001 result", self.text["importer"])
        for forbidden in ("delete_asset(", "delete_directory(", "reimport_asset(", "save_current_level(", "load_map("):
            self.assertNotIn(forbidden, combined)
        self.assertIn("NOT_PERFORMED__PARTIAL_ARTIFACTS_PRESERVED_FOR_EXPLICIT_REVIEW", self.text["importer"])

    def test_ue58_custom_lod_cvar_has_finally_restore(self):
        importer = self.text["importer"]
        self.assertIn('INTERCHANGE_FBX_CVAR + " 0"', importer)
        self.assertRegex(importer, r"finally:\s+evidence\[\"restore_attempted_in_finally\"\] = True")
        self.assertIn('f"{lane.INTERCHANGE_FBX_CVAR} {previous}"', importer)
        self.assertIn('len(evidence["custom_lods_imported"]) != 14', importer)

    def test_collision_and_black_box_contract_are_explicit(self):
        freezer = self.text["freezer"]
        for key in ("CuringOvenTunnel", "PretreatmentWashTunnel", "FlashOffTunnel",
                    "PaintQualityLightTunnel", "BodySkidCarrier"):
            self.assertIn(key, freezer)
        self.assertIn("COMPLEX_AS_SIMPLE", freezer)
        self.assertIn("preserves both open longitudinal X portals", freezer)
        self.assertIn("preserves the skid's open rail and wheel channels", freezer)
        self.assertIn("no_spray_robots", freezer)
        self.assertIn("no_windows", freezer)
        self.assertIn("no_side_vehicle_doors", freezer)

    def test_independent_validator_is_read_only_and_hash_exact(self):
        validator = self.text["validator"]
        self.assertIn("import_pid == os.getpid()", validator)
        self.assertIn("target_after != target_before", validator)
        self.assertIn("full_hash=True", validator)
        self.assertIn('"asset_or_level_saves": []', validator)
        self.assertIn('"imports_reimports_deletes": []', validator)
        self.assertIn("spray_booth_namespace_and_pass_receipts_unchanged", validator)

    def test_runner_is_powershell_51_safe_and_one_shot(self):
        runner = self.text["runner"]
        self.assertIn("Set-StrictMode -Version Latest", runner)
        self.assertIn("$null = $Process.Handle", runner)
        self.assertIn("$Process.WaitForExit()", runner)
        self.assertIn("Assert-NoPriorResults", runner)
        self.assertIn("Assert-NoProcesses", runner)
        self.assertIn("-WindowStyle Hidden", runner)
        self.assertIn("$Importer.Replace('\\','/')", runner)
        self.assertIn("$Validator.Replace('\\','/')", runner)
        self.assertIn("[\\x00-\\x1F\\\\]", runner)
        self.assertNotIn("pwsh", runner.lower())
        self.assertEqual(runner.count("Invoke-GuardedProcess $Editor"), 2)

    def test_hash_pins_are_all_pending_or_all_frozen(self):
        runtime_match = re.search(r'EXPECTED_BASELINE_SHA256 = "([A-Z0-9_]+)"', self.text["runtime"])
        self.assertIsNotNone(runtime_match)
        pins = re.findall(r"= '([^']+)'", self.text["runner"])
        pending = [value for value in pins if value.startswith("__PAINT_")]
        self.assertIn(len(pending), (0, 5))
        if not pending:
            self.assertRegex(runtime_match.group(1), r"^[A-F0-9]{64}$")
            baseline = SCRIPTS / "paint_line_native_kit_unreal_import_baseline_v001.json"
            self.assertTrue(baseline.is_file())
            self.assertEqual(runtime_match.group(1), sha256(baseline))


if __name__ == "__main__":
    unittest.main(verbosity=2)
